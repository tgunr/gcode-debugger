#!/usr/bin/env python3
"""
Communication module for G-code Debugger

Based on the proven send_gcode_direct.py approach for WebSocket communication
with the Buildbotics controller.
"""

import json
import logging
import random
import requests
import socket
import ssl
import sys
import threading
import time
import websocket
import websocket._exceptions as ws_exceptions
from queue import Queue, Empty
from typing import Dict, Any, Optional, Callable, Union, List
from urllib.parse import urlparse, urlunparse

# Import local modules
from .msg_debug_handler import MsgDebugHandler

class BBCtrlCommunicator:
    def __init__(self, host='bbctrl.polymicro.net', port=80, callback_scheduler=None):
        # Connection settings
        self.host = host
        self.port = port

        # Determine scheme based on port
        if self.port == 443:
            http_scheme = 'https'
            ws_scheme = 'wss'
        else:
            http_scheme = 'http'
            ws_scheme = 'ws'

        # Set up base URL for REST API calls
        self.base_url = f'{http_scheme}://{self.host}' if self.port in [80, 443] else f'{http_scheme}://{self.host}:{self.port}'
        
        # Set up WebSocket URL
        self.ws_url = f'{ws_scheme}://{self.host}/websocket' if self.port in [80, 443] else f'{ws_scheme}://{self.host}:{self.port}/websocket'
        
        # Thread safety
        self._lock = threading.RLock()
        self._stop_event = threading.Event()
        self._main_thread_id = threading.get_ident()
        
        # Connection state
        self.connected = False
        self._reconnect_attempts = 0
        self._stopping = False
        self._reconnect_timer = None
        self.keepalive_thread = None
        self.ws_thread = None
        self.ws = None
        self.last_message_time = time.time()
        self.connection_attempts = 0
        self.last_connection_attempt = 0
        self._max_reconnect_attempts = 10  # Maximum number of reconnection attempts
        self._reconnect_delay = 1  # Initial delay in seconds
        self._max_reconnect_delay = 60  # Maximum delay in seconds
        self._connection_lock = threading.Lock()

        # Callbacks
        self.state_callback = None
        self.message_callback = None
        self.error_callback = None
        self._callback_scheduler = callback_scheduler

        # State tracking
        self.last_state = {}
        self.message_counter = 1
        
        # MSG/DEBUG handler for local processing
        self.msg_debug_handler = MsgDebugHandler(self._handle_msg_debug_output)

    """Handles WebSocket and HTTP communication with Buildbotics controller."""
    # (Removed duplicate __init__ method)
        
    def set_callbacks(self, state_callback=None, message_callback=None, error_callback=None):
        """Set callback functions for various events."""
        if state_callback:
            self.state_callback = state_callback
        if message_callback:
            self.message_callback = message_callback
        if error_callback:
            self.error_callback = error_callback

    def _call_callback(self, callback, *args):
        """Safely call a callback function with the provided arguments.
        
        This method ensures thread safety when calling callbacks and provides
        comprehensive error handling and logging.
        
        Args:
            callback: The callback function to call
            *args: Arguments to pass to the callback
        """
        try:
            # Get current thread info for debugging
            current_thread = threading.current_thread()
            thread_name = getattr(current_thread, 'name', 'unnamed')
            thread_id = getattr(current_thread, 'ident', 'unknown')
            
            # Basic validation
            if callback is None:
                print(f"WARNING: Attempted to call None callback from thread {thread_name} ({thread_id})")
                return
                
            if not callable(callback):
                print(f"WARNING: Callback is not callable: {callback} (type: {type(callback).__name__})")
                return
            
            # Safely get callback name for logging
            callback_name = 'anonymous'
            try:
                if hasattr(callback, '__name__') and callback.__name__:
                    callback_name = callback.__name__
                elif hasattr(callback, '__class__') and hasattr(callback, '__call__'):
                    callback_name = callback.__class__.__name__
            except Exception as e:
                print(f"WARNING: Could not determine callback name: {e}")
            
            args_str = ', '.join(repr(arg) for arg in args)
            print(f"DEBUG: _call_callback for {callback_name}({args_str}) from thread {thread_name} ({thread_id})")
            
            # Check if we need to schedule this on the main thread
            if self._callback_scheduler:
                try:
                    print(f"DEBUG: Scheduling callback {callback_name} on main thread")
                    self._callback_scheduler(callback, *args)
                except Exception as e:
                    error_msg = f"Error scheduling callback {callback_name}: {str(e)}"
                    print(f"CRITICAL: {error_msg}")
                    import traceback
                    traceback.print_exc()
            else:
                try:
                    print(f"DEBUG: Directly invoking {callback_name}")
                    # Add a small delay to prevent thread congestion
                    time.sleep(0.001)
                    callback(*args)
                    print(f"DEBUG: Successfully completed {callback_name}")
                except Exception as e:
                    error_msg = f"Error in callback {callback_name}: {str(e)}"
                    print(f"ERROR: {error_msg}")
                    import traceback
                    traceback.print_exc()
                    
                    # If we have an error callback and it's not the source of the error
                    if hasattr(self, 'error_callback') and self.error_callback and self.error_callback != callback:
                        try:
                            self.error_callback(f"Callback error: {error_msg}")
                        except Exception as err:
                            print(f"CRITICAL: Error in error callback: {err}")
        
        except Exception as e:
            error_msg = f"Critical error in _call_callback for {callback_name}: {str(e)}"
            print(f"CRITICAL: {error_msg}")
            import traceback
            traceback.print_exc()
            
            # Last resort error handling
            try:
                if hasattr(self, 'error_callback') and self.error_callback and self.error_callback != callback:
                    self.error_callback(f"Critical error: {error_msg}")
            except Exception as err:
                print(f"CRITICAL: Failed to call error handler: {err}")
                
            # Don't propagate the error to avoid crashing the WebSocket thread
    
    def _handle_msg_debug_output(self, msg_type: str, content: str):
        """Handle MSG/DEBUG output from local processing."""
        formatted_message = f"[{msg_type}] {content}"
        self._call_callback(self.message_callback, formatted_message)
    
    def connect_websocket(self):
        """Connect to the WebSocket for real-time communication."""
        thread_id = threading.get_ident()
        print(f"[DEBUG] connect_websocket called on thread {thread_id}")
        
        with self._lock:
            try:
                # Check if we're already connected or connecting
                if self.connected or (hasattr(self, 'ws_thread') and self.ws_thread and self.ws_thread.is_alive()):
                    print("[DEBUG] WebSocket already connected or connecting")
                    return True
                    
                print(f"[DEBUG] Current state - connected: {self.connected}, stopping: {getattr(self, '_stopping', False)}")
                
                # Reset stopping flag
                self._stopping = False
                
                # Close any existing connection
                self.close()
                
                print(f"[INFO] Connecting to WebSocket at {self.ws_url}")
                
                # Configure SSL options only for wss:// connections
                sslopt = {}
                if self.ws_url.startswith('wss://'):
                    sslopt = {
                        "cert_reqs": ssl.CERT_NONE,  # Disable certificate verification
                        "ssl_version": ssl.PROTOCOL_TLS
                    }
                
                # Determine scheme for Origin header
                origin_scheme = 'https' if self.ws_url.startswith('wss://') else 'http'
                
                # Build minimal headers – controller rejects unexpected Origin
                ws_headers = {
                    'Origin': f'{origin_scheme}://{self.host}'
                }

                # Create WebSocketApp instance – disable per-message deflate
                self.ws = websocket.WebSocketApp(
                    self.ws_url,
                    on_open=self._on_open,
                    on_message=self._on_message,
                    on_error=self._on_error,
                    on_close=self._on_close,
                    on_ping=self._on_ping,
                    on_pong=self._on_pong,
                    header=ws_headers,
                    subprotocols=None
                )

                # Disable permessage-deflate by monkey-patching the app options
                # (library <1.7 uses ws.options dict; newer uses kwargs in run_forever)
                self.ws.enable_permessage_deflate = False

                # Start WebSocket thread
                self.ws_thread = threading.Thread(target=self._run_websocket, name="WebSocketThread", daemon=True)
                self.ws_thread.start()
                
                print("[DEBUG] WebSocket thread started. Connection will be established asynchronously.")
                return True
                
            except Exception as e:
                error_msg = f"Error initiating WebSocket connection: {e}"
                print(f"[ERROR] {error_msg}")
                import traceback
                traceback.print_exc()
                self._call_callback(self.error_callback, error_msg)
                self.close()
                return False
                
    def _run_websocket(self):
        """Run the WebSocket client in a loop with enhanced error handling."""
        current_thread = threading.current_thread()
        thread_id = current_thread.ident
        thread_name = current_thread.name
        
        print(f"[DEBUG] WebSocket thread started: {thread_name} (ID: {thread_id})")
        
        # Connection settings
        max_consecutive_errors = 5  # Max consecutive errors before giving up
        socket_timeout = 30.0       # 30 second socket timeout for operations
        
        consecutive_errors = 0
        
        try:
            while not getattr(self, '_stopping', False):
                try:
                    # Ensure WebSocket object exists and is properly initialized
                    if not hasattr(self, 'ws') or self.ws is None:
                        print("[ERROR] WebSocket not initialized in _run_websocket")
                        consecutive_errors += 1
                        
                        if consecutive_errors >= max_consecutive_errors:
                            error_msg = "Too many WebSocket connection errors"
                            print(f"[ERROR] {error_msg}")
                            self._call_callback(self.error_callback, error_msg)
                            # Notify UI of disconnection
                            self._call_callback(self.state_callback, {'connected': False})
                            break
                            
                        # Wait before next attempt with exponential backoff
                        backoff = min(2 ** consecutive_errors, 30)  # Cap at 30s
                        print(f"[INFO] Waiting {backoff} seconds before next connection attempt...")
                        time.sleep(backoff)
                        
                        # Reinitialize WebSocket if we're retrying
                        if not getattr(self, '_stopping', False):
                            self.connect_websocket()
                        continue
                    
                    # Reset error counter on successful iteration
                    consecutive_errors = 0
                    
                    # Configure SSL options only for wss:// connections
                    sslopt = {}
                    if self.ws_url.startswith('wss://'):
                        sslopt = {
                            "cert_reqs": ssl.CERT_NONE,  # Disable certificate verification
                            "ssl_version": ssl.PROTOCOL_TLS,
                            "timeout": 10.0  # 10 second SSL handshake timeout
                        }

                    # Ensure we have a valid WebSocket object before proceeding
                    if not hasattr(self, 'ws') or self.ws is None:
                        print("[WARNING] WebSocket object became None before connection")
                        raise websocket.WebSocketConnectionClosedException("WebSocket object is None")

                    # --- Establish connection ---
                    print(f"[DEBUG] Starting WebSocket connection to {self.ws_url}")
                    print(f"[DEBUG] Thread: {thread_name} (ID: {thread_id})")

                    try:
                        print("[DEBUG] Starting WebSocket run_forever")
                        self.ws.run_forever(sslopt=sslopt)
                        print("[DEBUG] WebSocket run_forever completed")

                    except websocket.WebSocketConnectionClosedException as e:
                        print(f"[WARNING] WebSocket connection closed: {e}")
                        if not self._stopping:
                            self._call_callback(self.error_callback, f"Connection closed: {e}")

                    except Exception as e:
                        error_msg = f"Error in WebSocket run_forever: {str(e)}"
                        print(f"[ERROR] {error_msg}")
                        import traceback
                        traceback.print_exc()
                        if not self._stopping:
                            self._call_callback(self.error_callback, error_msg)

                    # If we get here, the connection was closed or the loop will iterate again
                    if not self._stopping:
                        print("[INFO] WebSocket connection closed, scheduling reconnection...")
                        self._schedule_reconnect()
                        # Continue loop to attempt reconnection
                        continue

                    
                except Exception as e:
                    error_msg = f"Unexpected error in WebSocket loop: {str(e)}"
                    print(f"[ERROR] {error_msg}")
                    import traceback
                    traceback.print_exc()
                    
                    consecutive_errors += 1
                    if consecutive_errors >= max_consecutive_errors:
                        print("[ERROR] Too many consecutive errors, giving up")
                        self._call_callback(self.error_callback, "Too many connection errors")
                        break
                        
                    # Wait before next attempt
                    time.sleep(min(2 ** consecutive_errors, 30))  # Exponential backoff with max 30s
        
        except Exception as e:
            error_msg = f"Critical error in WebSocket thread: {str(e)}"
            print(f"[CRITICAL] {error_msg}")
            import traceback
            traceback.print_exc()
            
            if not self._stopping:
                self._call_callback(self.error_callback, error_msg)
        
        finally:
            print("[DEBUG] WebSocket thread exiting")
                
    def _on_ping(self, ws, message):
        """Handle WebSocket ping frame."""
        print("[DEBUG] Received ping from server")
        try:
            # Send pong response
            if hasattr(ws, 'sock') and ws.sock:
                ws.sock.pong(message)
                print("[DEBUG] Sent pong response")
        except Exception as e:
            print(f"[ERROR] Error sending pong: {e}")
    
    def _on_pong(self, ws, message):
        """Handle WebSocket pong frame."""
        # Update last message time to prevent timeout
        self.last_message_time = time.time()
        print("[DEBUG] Received pong from server")
    
    def _request_state(self):
        """Request the current state from the controller via REST API."""
        try:
            url = f"{self.base_url}/api/state"
            print(f"[DEBUG] Requesting state from {url}")
            
            response = requests.get(url, timeout=5)
            response.raise_for_status()
            
            state = response.json()
            if state:
                self._update_state(state)
                return True
                
        except requests.exceptions.RequestException as e:
            print(f"[WARNING] Error getting state: {e}")
        except Exception as e:
            print(f"[ERROR] Unexpected error in _request_state: {e}")
            import traceback
            traceback.print_exc()
            
        return False

    def _on_open(self, ws):
        """Handle WebSocket connection opened event with detailed logging."""
        print("\n" + "="*80)
        print("DEBUG: WebSocket _on_open called")
        print("="*80)
        
        try:
            # Log basic connection info
            if hasattr(ws, 'sock') and ws.sock and hasattr(ws, 'sock') and ws.sock.sock:
                try:
                    sock_name = ws.sock.sock.getsockname()
                    print(f"[DEBUG] Local socket: {sock_name}")
                except Exception as e:
                    print(f"[WARNING] Could not get socket info: {e}")
            else:
                print("[WARNING] Could not get socket: ws.sock.sock is not available")
            
            # Update connection state
            with self._lock:
                self.connected = True
                self._reconnect_attempts = 0
                self.last_message_time = time.time()
            
            print(f"[DEBUG] WebSocket connection established. Connected: {self.connected}")
            
            # Start keepalive thread if not already running
            if not hasattr(self, 'keepalive_thread') or not self.keepalive_thread or not self.keepalive_thread.is_alive():
                self._start_keepalive()
            
            # Update UI and request initial state
            def update_ui_and_get_state():
                try:
                    if self.state_callback:
                        print("[DEBUG] Updating UI: Connected")
                        self.state_callback({'connected': True})
                    
                    print("[DEBUG] Requesting initial state...")
                    if not self._request_state():
                        print("[WARNING] Failed to get initial state")
                        if self.error_callback:
                            self._call_callback(self.error_callback, "Failed to get initial state from controller")
                except Exception as e:
                    error_msg = f"Error during UI update or initial state request: {e}"
                    print(f"[ERROR] {error_msg}")
                    if self.error_callback:
                        self._call_callback(self.error_callback, error_msg)
            
            # Schedule the UI update and state request on the main thread
            self._call_callback(update_ui_and_get_state)
            
            print("="*80 + "\n")
            
        except Exception as e:
            error_msg = f"Error in _on_open: {e}"
            print(f"[CRITICAL] {error_msg}")
            import traceback
            traceback.print_exc()
            self._call_callback(self.error_callback, error_msg)
            
    def _on_error(self, ws, error):
        """Handle WebSocket errors."""
        try:
            error_msg = str(error) if error else "Unknown error"
            if isinstance(error, OSError) and "No route to host" in error_msg:
                error_msg = "Cannot connect to host: No route to host. Please check your network connection and the controller's IP address."

            print("\n" + "="*80)
            print("DEBUG: WebSocket _on_error called")
            print("="*80)
            print(f"[ERROR] WebSocket error: {error_msg}")
            import traceback
            traceback.print_exc()

            if self.connected:
                self.connected = False
                self._call_callback(self.state_callback, {'connected': False})

            self._call_callback(self.error_callback, error_msg)

        except Exception as e:
            print(f"[CRITICAL] Error in _on_error handler: {e}")
            import traceback
            traceback.print_exc()

    def _schedule_reconnect(self):
        """Schedule a reconnection attempt with exponential backoff."""
        # Use a flag to prevent multiple reconnection attempts
        if getattr(self, '_reconnect_scheduled', False):
            return
            
        with self._lock:
            try:
                # Set the flag immediately
                self._reconnect_scheduled = True
                
                # Don't schedule if we're already stopping
                if getattr(self, '_stopping', False):
                    self._reconnect_scheduled = False
                    return
                    
                # Initialize or get the current attempt count
                if not hasattr(self, '_reconnect_attempts'):
                    self._reconnect_attempts = 0
                
                # Limit the number of reconnection attempts
                max_attempts = 5
                if self._reconnect_attempts >= max_attempts:
                    print("[WARNING] Max reconnection attempts reached")
                    self._call_callback(
                        self.error_callback,
                        "Connection lost: Max reconnection attempts reached"
                    )
                    self._reconnect_scheduled = False
                    return
                
                # Calculate delay with exponential backoff and jitter
                base_delay = min(2 ** self._reconnect_attempts, 10)  # Cap at 10 seconds
                delay = base_delay * random.uniform(0.8, 1.2)  # Add jitter
                
                print(f"[INFO] Will attempt to reconnect in {delay:.1f} seconds (attempt {self._reconnect_attempts + 1}/{max_attempts})...")
                
                def attempt_reconnect():
                    try:
                        if not getattr(self, '_stopping', False):
                            self._reconnect_attempts += 1
                            self.connect_websocket()
                    except Exception as e:
                        print(f"[ERROR] Error in reconnect attempt: {e}")
                    finally:
                        # Clear the flag when done
                        self._reconnect_scheduled = False
                
                # Cancel any existing timer
                if hasattr(self, '_reconnect_timer') and self._reconnect_timer:
                    try:
                        self._reconnect_timer.cancel()
                    except:
                        pass
                
                # Schedule the reconnection attempt
                try:
                    self._reconnect_timer = threading.Timer(delay, attempt_reconnect)
                    self._reconnect_timer.daemon = True
                    self._reconnect_timer.start()
                except Exception as e:
                    print(f"[ERROR] Failed to schedule reconnection: {e}")
                    self._reconnect_scheduled = False
                    
            except Exception as e:
                print(f"[CRITICAL] Error in _schedule_reconnect: {type(e).__name__}: {e}")
                import traceback
                traceback.print_exc()
                
                # Clear the flag on error
                self._reconnect_scheduled = False
                
                # Last resort: try to reconnect after a short delay
                if not getattr(self, '_stopping', False):
                    try:
                        threading.Timer(2.0, self.connect_websocket).start()
                    except Exception as e:
                        print(f"[CRITICAL] Failed to schedule final reconnection: {e}")
    
    def _on_close(self, ws, close_status_code, close_msg):
        """Handle WebSocket connection close."""
        print("\n" + "="*80)
        print("DEBUG: WebSocket _on_close called")
        print("="*80)
        
        try:
            # Skip if we're already stopped or in the process of stopping
            if getattr(self, '_stopping', False) or not hasattr(self, 'connected'):
                print("[DEBUG] Ignoring close - already stopping or not connected")
                # Ensure we're fully cleaned up
                with self._lock:
                    self.connected = False
                    if hasattr(self, 'ws'):
                        self.ws = None
                return
            
            # Get current thread info
            current_thread = threading.current_thread()
            print(f"[DEBUG] Close handler running on thread: {current_thread.name} (ID: {current_thread.ident})")
            print(f"[DEBUG] Main thread ID: {self._main_thread_id}")
            
            # Log WebSocket state
            print(f"[DEBUG] WebSocket object in _on_close: {ws}")
            if ws is not None:
                print(f"[DEBUG] WebSocket URL: {getattr(ws, 'url', 'N/A')}")
                print(f"[DEBUG] WebSocket sock: {getattr(ws, 'sock', 'N/A')}")
            
            # Only process if we were previously connected
            was_connected = self.connected
            
            # Log the close event with more details
            close_msg = str(close_msg) if close_msg else "No close message"
            close_status_code = close_status_code if close_status_code is not None else -1
            
            print(f"[INFO] WebSocket closed: {close_msg}")
            print(f"[DEBUG] WebSocket close status code: {close_status_code}")
            print(f"[DEBUG] Current thread: {threading.get_ident()}")
            
            # Clean up WebSocket resources
            with self._lock:
                # Only clean up if this is the current WebSocket instance
                if self.ws is ws:
                    try:
                        # Explicitly close the socket if it exists
                        if hasattr(ws, 'sock') and ws.sock is not None:
                            try:
                                ws.sock.close()
                            except Exception as e:
                                print(f"[WARNING] Error closing WebSocket socket: {e}")
                        
                        # Clear the WebSocket reference
                        self.ws = None
                        self.connected = False
                    except Exception as e:
                        print(f"[WARNING] Error cleaning up WebSocket: {e}")
                
                # Update UI state with disconnection status - ensure this runs on main thread
                def update_ui_disconnected():
                    try:
                        if hasattr(self, 'state_callback') and self.state_callback:
                            print("[DEBUG] Updating UI: Disconnected")
                            self.state_callback({'connected': False})
                        if hasattr(self, 'message_callback') and self.message_callback:
                            self.message_callback(f"WebSocket closed: {close_msg}")
                    except Exception as e:
                        print(f"[ERROR] Error in UI update: {e}")
                
                # Use _call_callback to ensure this runs on the main thread
                self._call_callback(update_ui_disconnected)
                
                # Only attempt reconnection for unexpected disconnections
                if close_status_code != 1000 and not getattr(self, '_stopping', False):  # Not a normal closure
                    print("[INFO] Connection lost unexpectedly, scheduling reconnection...")
                    try:
                        self._schedule_reconnect()
                    except Exception as e:
                        print(f"[ERROR] Failed to schedule reconnect: {e}")
                
        except Exception as e:
            print(f"[ERROR] Error in _on_close handler: {e}")
            import traceback
            traceback.print_exc()
            
            # Ensure we update the UI even if there's an error
            try:
                if hasattr(self, 'state_callback') and self.state_callback:
                    self._call_callback(self.state_callback, {'connected': False})
            except Exception as ui_error:
                print(f"[ERROR] Error updating UI after close error: {ui_error}")
            
            # Ensure we don't leave the connection in a bad state
            self.connected = False
            if hasattr(self, 'ws'):
                self.ws = None
    
    def _start_keepalive(self):
        """Start the keepalive thread that sends periodic pings to keep the connection alive."""
        if self.keepalive_thread and self.keepalive_thread.is_alive():
            return
            
        self._stop_event.clear()
        
        def keepalive_loop():
            while not self._stop_event.is_set() and self.connected:
                try:
                    # Wait at least 30 s since the last controller message before pinging
                    time_since_last_message = time.time() - self.last_message_time
                    if time_since_last_message > 30:  # 30-second inactivity threshold
                        if hasattr(self, 'ws') and self.ws and self.connected and hasattr(self.ws, 'sock') and self.ws.sock:
                            print("[DEBUG] Sending WebSocket PING frame for keep-alive")
                            try:
                                # Send a native WebSocket PING frame instead of a text message
                                self.ws.sock.ping(b'keepalive')
                                # Reset timer so we do not spam pings if no traffic
                                self.last_message_time = time.time()
                            except Exception as e:
                                print(f"[WARNING] Failed to send keepalive PING: {e}")
                                # Force a reconnect on ping failure
                                self.connected = False
                                break
                except Exception as e:
                    print(f"[ERROR] Error in keepalive thread: {e}")
                
                # Sleep for 5 seconds before next check
                self._stop_event.wait(5)
        
        self.keepalive_thread = threading.Thread(
            target=keepalive_loop,
            name="WebSocketKeepaliveThread",
            daemon=True
        )
        self.keepalive_thread.start()
    
    def _stop_keepalive(self):
        """Stop the keepalive thread."""
        self._stop_event.set()
        if self.keepalive_thread and self.keepalive_thread.is_alive():
            self.keepalive_thread.join(timeout=2.0)
    
    def _on_message(self, ws, message):
        """Handle incoming WebSocket messages."""
        if not hasattr(self, '_main_thread_id'):
            print("[ERROR] _main_thread_id not set in _on_message")
            return
            
        try:
            self.last_message_time = time.time()
            
            # Skip empty messages
            if not message or not message.strip():
                return
                
            # Log raw message for debugging
            print(f"[DEBUG] Received message: {message}")
            
            # Parse JSON message
            try:
                data = json.loads(message)
            except json.JSONDecodeError as e:
                print(f"[WARNING] Received invalid JSON: {message}")
                print(f"[WARNING] JSON decode error: {e}")
                return
                
            # Check for error logs from the server
            if isinstance(data, dict) and 'log' in data and data['log'].get('level') == 'error':
                error_msg = f"Controller error: {data['log'].get('msg', 'Unknown error')}"
                print(f"[ERROR] {error_msg}")
                self._call_callback(self.error_callback, error_msg)
                return
                
            # Update state
            self._update_state(data)
            
            # Only forward concise messages to the UI to avoid huge dumps that
            # can crash Tk.  Skip full-state dicts; just show heartbeats.
            if isinstance(data, dict):
                if data.keys() == {'heartbeat'}:
                    self._call_callback(self.message_callback,
                                        f"Heartbeat: {data['heartbeat']}")
            else:
                # Non-dict messages (e.g. log strings) – pass through.
                self._call_callback(self.message_callback, str(data))
            
        except Exception as e:
            error_msg = f"Error processing WebSocket message: {e}"
            print(f"[ERROR] {error_msg}")
            import traceback
            traceback.print_exc()
            self._call_callback(self.error_callback, error_msg)
            
            print("DEBUG: _on_message completed successfully")
                    
        except Exception as e:
            error_msg = f"Critical error in _on_message: {str(e)}"
            print(f"[CRITICAL] {error_msg}")
            print(f"CRITICAL: {error_msg}")
            import traceback
            traceback.print_exc()
            # Don't try to use callbacks here as they might be the source of the problem
    
    def _update_state(self, data):
        """Update the internal state with new data from the controller."""
        if not isinstance(data, dict):
            return
            
        # Update last_state with the new data
        self._merge_state(self.last_state, data)
        
        # Notify state change
        self._call_callback(self.state_callback, self.last_state)
    
    def _merge_state(self, original, updates):
        """Recursively merge update data into the original state."""
        for key, value in updates.items():
            if (key in original and isinstance(original[key], dict) and 
                    isinstance(value, dict)):
                self._merge_state(original[key], value)
            else:
                original[key] = value
        

    
    def get_state(self) -> Optional[Dict[str, Any]]:
        """Get current machine state via REST API."""
        try:
            response = requests.get(f'{self.base_url}/api/state', timeout=5)
            if response.status_code == 200:
                state = response.json()
                self.last_state.update(state)
                return state
        except Exception as e:
            self._call_callback(self.error_callback, f"Error getting state: {e}")
        return None
    
    def send_gcode(self, command: str) -> bool:
        """Send G-code command via WebSocket."""
        if not self.connected:
            self._call_callback(self.error_callback, "Not connected to WebSocket")
            return False
        
        # Process MSG/DEBUG commands locally before sending
        self.msg_debug_handler.process_command(command)
        
        try:
            # Add newline terminator to the command as G-code typically requires line termination
            command_with_terminator = command.rstrip() + '\n'
            self.ws.send(command_with_terminator)
            self._call_callback(self.message_callback, f"Sent: {command}")
            return True
        except Exception as e:
            self._call_callback(self.error_callback, f"Error sending command: {e}")
            return False
    
    def send_mdi_command(self, command: str) -> bool:
        """Send MDI command using the same simple method as send_gcode_direct.py."""
        # Use the exact same simple method that works in send_gcode_direct.py
        return self.send_gcode(command)
    
    def emergency_stop(self) -> bool:
        """Send emergency stop command."""
        try:
            # Try WebSocket first for immediate response
            if self.connected:
                self.ws.send('!')
            # Also try REST API for redundancy
            response = requests.put(f'{self.base_url}/api/estop', timeout=2)
            self._call_callback(self.message_callback, "Emergency stop sent")
            return True
        except Exception as e:
            self._call_callback(self.error_callback, f"Emergency stop error: {e}")
            return False
    
    def clear_estop(self) -> bool:
        """Clear emergency stop condition."""
        try:
            response = requests.put(f'{self.base_url}/api/clear', timeout=5)
            if response.status_code == 200:
                self._call_callback(self.message_callback, "Emergency stop cleared")
                return True
        except Exception as e:
            self._call_callback(self.error_callback, f"Error clearing estop: {e}")
        return False
    
    def pause(self) -> bool:
        """Pause machine execution."""
        try:
            response = requests.put(f'{self.base_url}/api/pause', timeout=5)
            return response.status_code == 200
        except Exception as e:
            self._call_callback(self.error_callback, f"Error pausing: {e}")
            return False
    
    def unpause(self) -> bool:
        """Resume machine execution."""
        try:
            response = requests.put(f'{self.base_url}/api/unpause', timeout=5)
            return response.status_code == 200
        except Exception as e:
            self._call_callback(self.error_callback, f"Error resuming: {e}")
            return False
    
    def stop(self) -> bool:
        """Stop machine execution."""
        try:
            response = requests.put(f'{self.base_url}/api/stop', timeout=5)
            return response.status_code == 200
        except Exception as e:
            self._call_callback(self.error_callback, f"Error stopping: {e}")
            return False
    
    def is_ready_for_command(self) -> bool:
        """Check if machine is ready to accept new commands."""
        state = self.last_state
        return (state.get('xx') in ['READY', 'HOLDING'] or 
                state.get('cycle') in ['idle', 'mdi'])
    
    def get_macros(self) -> Optional[Dict[str, Any]]:
        """Fetch all macros from the controller via REST API.
        
        Returns:
            Dict containing macro data if successful, None otherwise
        """
        try:
            response = requests.get(f'{self.base_url}/api/macros', timeout=10)
            if response.status_code == 200:
                return response.json()
            else:
                self._call_callback(self.error_callback, 
                                  f"Failed to fetch macros: HTTP {response.status_code}")
        except Exception as e:
            self._call_callback(self.error_callback, f"Error fetching macros: {e}")
        return None
    
    def close(self):
        """Close WebSocket connection and clean up resources."""
        with self._connection_lock:
            print("[DEBUG] Closing WebSocket connection...")
            
            # Stop any pending reconnection attempts
            if hasattr(self, '_reconnect_timer') and self._reconnect_timer:
                try:
                    self._reconnect_timer.cancel()
                except:
                    pass
                self._reconnect_timer = None
            
            # Stop the keepalive thread
            self._stop_keepalive()
            
            # Close WebSocket if it exists
            if hasattr(self, 'ws') and self.ws:
                try:
                    # Don't call close() here as it can cause deadlocks
                    # Just set the socket to None and let garbage collection handle it
                    ws = self.ws
                    self.ws = None
                    
                    # Close in a separate thread to avoid deadlocks
                    def safe_close():
                        try:
                            ws.close()
                        except:
                            pass
                    
                    closer = threading.Thread(target=safe_close, daemon=True)
                    closer.start()
                    closer.join(timeout=1.0)  # Wait up to 1 second
                    
                except Exception as e:
                    print(f"[WARNING] Error closing WebSocket: {e}")
            
            # Clean up thread
            if self.ws_thread and self.ws_thread.is_alive():
                try:
                    self.ws_thread.join(timeout=1.0)
                except:
                    pass
            
            print("[INFO] WebSocket connection closed")


class CommunicationError(Exception):
    """Custom exception for communication errors."""
    pass