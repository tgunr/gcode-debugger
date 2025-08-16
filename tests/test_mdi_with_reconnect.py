#!/usr/bin/env python3
"""
Test MDI with reconnection for each command
"""

import sys
import os
import time

# Add the current directory to Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

from core.communication import BBCtrlCommunicator

def test_mdi_with_reconnect():
    """Test MDI with reconnection for each command"""
    print("Testing MDI with reconnection for each command...")
    
    commands = [
        "(MSG, Testing MDI with reconnect)",
        "G90",  # Set absolute positioning
        "G0 Z-113",  # Move Z axis (should be visible)
    ]
    
    for i, command in enumerate(commands, 1):
        print(f"\n=== Command {i}/{len(commands)}: {command} ===")
        
        # Create fresh communicator for each command
        comm = BBCtrlCommunicator()
        
        # Set up callbacks
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
        
        # Connect
        print("Connecting...")
        if comm.connect_websocket():
            print("Connected!")
            
            # Wait a moment for connection to stabilize
            time.sleep(0.5)
            
            # Send command
            print(f"Sending: {command}")
            if comm.send_mdi_command(command):
                print("✓ Command sent successfully!")
                
                # Wait for any response
                print("Waiting for response...")
                time.sleep(2)
                
            else:
                print("✗ Failed to send command")
        else:
            print("✗ Failed to connect")
        
        # Close connection
        comm.close()
        
        # Wait between commands
        if i < len(commands):
            print("Waiting before next command...")
            time.sleep(1)
    
    print("\n=== Test completed ===")
    print("Check the Buildbotics controller display/machine for any movement or messages.")

if __name__ == "__main__":
    test_mdi_with_reconnect()