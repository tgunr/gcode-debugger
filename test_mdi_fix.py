#!/usr/bin/env python3
"""
Test script to verify the MDI fix with JSON-RPC format
"""

import sys
import os
import time

# Add the current directory to Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

from core.communication import BBCtrlCommunicator

def test_mdi_fix():
    """Test MDI with the fixed JSON-RPC format"""
    print("Testing MDI fix with JSON-RPC format...")
    
    # Create communicator
    comm = BBCtrlCommunicator()
    
    # Test callbacks
    def on_message(msg):
        print(f"Message: {msg}")
    
    def on_error(err):
        print(f"Error: {err}")
    
    def on_state(state):
        print(f"State update received")
    
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
        
        # Test 1: MSG command to verify communication
        print("\n=== Test 1: MSG Command ===")
        msg_command = "(MSG, MDI Fix Test - JSON-RPC Format)"
        print(f"Sending: {msg_command}")
        if comm.send_mdi_command(msg_command):
            print("✓ MSG command sent successfully!")
        else:
            print("✗ Failed to send MSG command")
        
        time.sleep(1)
        
        # Test 2: Get current position
        print("\n=== Test 2: Current Position ===")
        state = comm.get_state()
        if state:
            current_z = state.get('zp', 'unknown')
            print(f"Current Z position: {current_z}")
            
            # Test 3: Move to a more noticeable position
            print("\n=== Test 3: Noticeable Movement ===")
            if current_z != 'unknown':
                # Move 10mm up from current position for a more noticeable movement
                new_z = float(current_z) + 10
                move_command = f"G0 Z{new_z}"
                print(f"Sending: {move_command}")
                if comm.send_mdi_command(move_command):
                    print("✓ Movement command sent successfully!")
                    print(f"Machine should move from Z{current_z} to Z{new_z}")
                else:
                    print("✗ Failed to send movement command")
            else:
                print("Could not determine current position for movement test")
        else:
            print("Could not get machine state")
        
        time.sleep(2)
        
    else:
        print("✗ Failed to connect")
    
    # Close connection
    comm.close()
    print("\n=== Test completed ===")
    print("Check if the machine moved and if messages appeared on the controller display.")

if __name__ == "__main__":
    test_mdi_fix()