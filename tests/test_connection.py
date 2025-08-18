#!/usr/bin/env python3
"""
Script to test the connection to the Buildbotics controller.
"""
import sys
import os
import json
import requests
from urllib.parse import urljoin

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from core.config import config

def test_http_connection():
    """Test HTTP connection to the controller."""
    try:
        host = config.get('connection.host', '10.1.1.111')
        port = config.get('connection.port', 80)
        
        # Determine scheme based on port
        scheme = 'https' if port == 443 else 'http'
        base_url = f"{scheme}://{host}" if port in [80, 443] else f"{scheme}://{host}:{port}"
        
        print(f"Testing connection to {base_url}")
        
        # Test basic API endpoint
        response = requests.get(f"{base_url}/api/version", timeout=5)
        response.raise_for_status()
        
        print("✓ HTTP Connection Successful!")
        print(f"Controller Version: {response.text}")
        return True
        
    except requests.exceptions.RequestException as e:
        print(f"✗ HTTP Connection Failed: {e}")
        return False

def test_websocket_connection():
    """Test WebSocket connection to the controller."""
    try:
        import websocket
        import threading
        import time
        
        host = config.get('connection.host', '10.1.1.111')
        port = config.get('connection.port', 80)
        
        # Determine scheme based on port
        ws_scheme = 'wss' if port == 443 else 'ws'
        ws_url = f"{ws_scheme}://{host}/websocket" if port in [80, 443] else f"{ws_scheme}://{host}:{port}/websocket"
        
        print(f"Testing WebSocket connection to {ws_url}")
        
        def on_message(ws, message):
            print(f"WebSocket message: {message}")
            
        def on_error(ws, error):
            print(f"WebSocket error: {error}")
            
        def on_close(ws, close_status_code, close_msg):
            print("WebSocket connection closed")
            
        def on_open(ws):
            print("✓ WebSocket Connection Established!")
            ws.send(json.dumps({"subscribe": "state"}))
            
        ws = websocket.WebSocketApp(
            ws_url,
            on_open=on_open,
            on_message=on_message,
            on_error=on_error,
            on_close=on_close
        )
        
        # Run WebSocket in a separate thread
        ws_thread = threading.Thread(target=ws.run_forever, daemon=True)
        ws_thread.start()
        
        # Keep the connection open for a few seconds
        time.sleep(5)
        ws.close()
        ws_thread.join()
        
        return True
        
    except Exception as e:
        print(f"✗ WebSocket Connection Failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    print("=== Testing Connection to Buildbotics Controller ===\n")
    
    # Test HTTP connection
    print("1. Testing HTTP connection...")
    http_success = test_http_connection()
    
    # Test WebSocket connection
    print("\n2. Testing WebSocket connection...")
    ws_success = test_websocket_connection()
    
    print("\n=== Test Results ===")
    print(f"HTTP Connection: {'✓ Success' if http_success else '✗ Failed'}")
    print(f"WebSocket Connection: {'✓ Success' if ws_success else '✗ Failed'}")
    
    if not (http_success and ws_success):
        print("\nTroubleshooting Tips:")
        print("1. Verify the controller is powered on and connected to the network")
        print("2. Check if you can ping the controller's IP address")
        print("3. Verify the port number is correct (default is 80 for HTTP, 443 for HTTPS)")
        print("4. Check for any firewall rules blocking the connection")
        print("5. Ensure no other application is using the same port")

if __name__ == "__main__":
    main()
