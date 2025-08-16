#!/usr/bin/env python3
"""
Test script to verify MDI functionality with JSON-RPC format
"""

import sys
import os
import json
import time

# Add the current directory to Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

from core.communication import BBCtrlCommunicator

def test_mdi_command():
    """Test sending an MDI command"""
    print("Testing MDI command with JSON-RPC format...")
    
    # Create communicator
    comm = BBCtrlCommunicator()
    
    # Test callbacks
    def on_message(msg):
        print(f"Message: {msg}")
    
    def on_error(err):
        print(f"Error: {err}")
    
    def on_state(state):
        print(f"State update: {state}")
    
    comm.set_callbacks(
        message_callback=on_message,
        error_callback=on_error,
        state_callback=on_state
    )
    
    # Try to connect
    print("Attempting to connect to WebSocket...")
    if comm.connect_websocket():
        print("Connected successfully!")
        
        # Test sending a simple message command
        test_command = "(MSG, MDI Test - JSON-RPC Format)"
        print(f"Sending test command: {test_command}")
        
        if comm.send_gcode(test_command):
            print("Command sent successfully!")
            print("Check the controller console for the message.")
        else:
            print("Failed to send command")
        
        # Wait a bit for response
        time.sleep(2)
        
        # Test a simple G-code command
        gcode_command = "G90"  # Set absolute positioning
        print(f"Sending G-code: {gcode_command}")
        
        if comm.send_gcode(gcode_command):
            print("G-code sent successfully!")
        else:
            print("Failed to send G-code")
        
        time.sleep(1)
        
    else:
        print("Failed to connect to WebSocket")
        print("Make sure the Buildbotics controller is running and accessible")
    
    # Cleanup
    comm.close()
    print("Test completed")

if __name__ == "__main__":
    test_mdi_command()