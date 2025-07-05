#!/usr/bin/env python3
"""
Communication module for G-code Debugger

Based on the proven send_gcode_direct.py approach for WebSocket communication
with the Buildbotics controller.
"""

import websocket
import requests
import json
import time
import threading
from typing import Callable, Optional, Dict, Any
from .msg_debug_handler import MsgDebugHandler

class BBCtrlCommunicator:
    def __init__(self, host='bbctrl.local', port=80, callback_scheduler=None):
        self.host = host
        self.port = port
        self.base_url = f'http://{host}' if port == 80 else f'http://{host}:{port}'
        
        # Use the original working WebSocket URL format (same as send_gcode_direct.py)
        self.ws_url = f'ws://{host}/websocket' if port == 80 else f'ws://{host}:{port}/websocket'

        # WebSocket connection
        self.ws = None
        self.ws_thread = None
        self.connected = False

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
        if callback:
            if self._callback_scheduler:
                self._callback_scheduler(callback, *args)
            else:
                callback(*args)
    
    def _handle_msg_debug_output(self, msg_type: str, content: str):
        """Handle MSG/DEBUG output from local processing."""
        formatted_message = f"[{msg_type}] {content}"
        self._call_callback(self.message_callback, formatted_message)
    
    def connect_websocket(self) -> bool:
        """Connect to the WebSocket for real-time communication."""
        try:
            self.ws = websocket.WebSocketApp(
                self.ws_url,
                on_open=self._on_open,
                on_message=self._on_message,
                on_error=self._on_error,
                on_close=self._on_close
            )
            # Start WebSocket in a separate thread
            self.ws_thread = threading.Thread(target=self.ws.run_forever)
            self.ws_thread.daemon = True
            self.ws_thread.start()
            # Wait for connection with timeout
            timeout = 10
            while not self.connected and timeout > 0:
                time.sleep(0.1)
                timeout -= 0.1
            return self.connected
        except Exception as e:
            self._call_callback(self.error_callback, f"WebSocket connection error: {e}")
            return False
    
    def _on_open(self, ws):
        """WebSocket connection opened."""
        self.connected = True
        self._call_callback(self.message_callback, "WebSocket connected")
    
    def _on_message(self, ws, message):
        """Handle incoming WebSocket messages (enhanced for MSG/DEBUG output)."""
        # Log ALL incoming messages for debugging
        self._call_callback(self.message_callback, f"RAW WS MESSAGE: {message}")
        
        try:
            data = json.loads(message)
            
            # Check for MSG/DEBUG command responses
            if 'result' in data or 'response' in data:
                self._call_callback(self.message_callback, f"COMMAND RESPONSE: {data}")
            
            # Check for error responses
            if 'error' in data:
                self._call_callback(self.error_callback, f"COMMAND ERROR: {data}")
            
            # Update state if received
            if 'state' in data or any(key in data for key in ['xx', 'cycle', 'line']):
                self.last_state.update(data)
                self._call_callback(self.state_callback, self.last_state)
                
        except json.JSONDecodeError:
            # Handle non-JSON messages (might be plain text responses)
            if message.strip():  # Only log non-empty messages
                self._call_callback(self.message_callback, f"NON-JSON MESSAGE: {message}")
        except Exception as e:
            self._call_callback(self.error_callback, f"Message processing error: {e}")
    
    def _on_error(self, ws, error):
        """Handle WebSocket errors."""
        self._call_callback(self.error_callback, f"WebSocket error: {error}")
    
    def _on_close(self, ws, close_status_code, close_msg):
        """WebSocket connection closed."""
        self.connected = False
        self._call_callback(self.message_callback, "WebSocket closed")
    
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
    
    def close(self):
        """Close WebSocket connection."""
        self.connected = False
        if self.ws:
            self.ws.close()
        if self.ws_thread and self.ws_thread.is_alive():
            self.ws_thread.join(timeout=1)


class CommunicationError(Exception):
    """Custom exception for communication errors."""
    pass