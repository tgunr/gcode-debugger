#!/usr/bin/env python3
"""
Test script to verify MDI functionality with REST API
"""

import sys
import os
import time

# Add the current directory to Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

from core.communication import BBCtrlCommunicator

def test_rest_mdi():
    """Test MDI using REST API"""
    print("Testing MDI with REST API...")
    
    # Create communicator
    comm = BBCtrlCommunicator()
    
    # Test callbacks
    def on_message(msg):
        print(f"Message: {msg}")
    
    def on_error(err):
        print(f"Error: {err}")
    
    comm.set_callbacks(
        message_callback=on_message,
        error_callback=on_error
    )
    
    # Connect to WebSocket first (same as debugger)
    print("Connecting to WebSocket...")
    if not comm.connect_websocket():
        print("Failed to connect to WebSocket")
        return
    
    print("Connected! Testing MDI commands...")
    
    # Test 1: Simple message command
    test_command = "(MSG, Testing REST API MDI)"
    print(f"Sending: {test_command}")
    
    if comm.send_mdi_command(test_command):
        print("✓ Message command sent successfully!")
    else:
        print("✗ Failed to send message command")
    
    time.sleep(1)
    
    # Test 2: G-code command
    gcode_command = "G90"  # Set absolute positioning
    print(f"Sending: {gcode_command}")
    
    if comm.send_mdi_command(gcode_command):
        print("✓ G-code command sent successfully!")
    else:
        print("✗ Failed to send G-code command")
    
    time.sleep(1)
    
    # Test 3: Spindle command
    spindle_command = "M3 S1000"  # Start spindle
    print(f"Sending: {spindle_command}")
    
    if comm.send_mdi_command(spindle_command):
        print("✓ Spindle command sent successfully!")
    else:
        print("✗ Failed to send spindle command")
    
    time.sleep(1)
    
    # Test 4: Stop spindle
    stop_command = "M5"  # Stop spindle
    print(f"Sending: {stop_command}")
    
    if comm.send_mdi_command(stop_command):
        print("✓ Stop command sent successfully!")
    else:
        print("✗ Failed to send stop command")
    
    print("\nREST API MDI test completed!")
    print("Check the Buildbotics controller console/display for command execution.")

if __name__ == "__main__":
    test_rest_mdi()