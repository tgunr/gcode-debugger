#!/usr/bin/env python3
"""
Test script to verify both MDI and debugger functionality
"""

import sys
import os
import time

# Add the current directory to Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

from core.communication import BBCtrlCommunicator
from core.debugger import GCodeDebugger

def test_both_modes():
    """Test both MDI and debugger functionality"""
    print("Testing both MDI and debugger modes...")
    
    # Create communicator and debugger
    comm = BBCtrlCommunicator()
    debugger = GCodeDebugger(comm)
    
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
    
    # Try to connect
    print("Attempting to connect to WebSocket...")
    if comm.connect_websocket():
        print("Connected successfully!")
        
        # Test 1: MDI command (should use JSON-RPC)
        print("\n=== Testing MDI Command ===")
        mdi_command = "(MSG, Testing MDI with JSON-RPC)"
        print(f"Sending MDI command: {mdi_command}")
        
        if comm.send_mdi_command(mdi_command):
            print("✓ MDI command sent successfully!")
        else:
            print("✗ Failed to send MDI command")
        
        time.sleep(1)
        
        # Test 2: Debugger command (should use raw format)
        print("\n=== Testing Debugger Command ===")
        debugger_command = "G90"  # Set absolute positioning
        print(f"Sending debugger command: {debugger_command}")
        
        if comm.send_gcode(debugger_command, use_json_rpc=False):
            print("✓ Debugger command sent successfully!")
        else:
            print("✗ Failed to send debugger command")
        
        time.sleep(1)
        
        # Test 3: Create a simple test file and try stepping
        print("\n=== Testing File Stepping ===")
        test_gcode = """G90
G0 X0 Y0
G0 Z5
(MSG, Test complete)"""
        
        # Write test file
        test_file = "test_step.gcode"
        with open(test_file, 'w') as f:
            f.write(test_gcode)
        
        # Load file in debugger
        if debugger.load_file(test_file):
            print("✓ Test file loaded successfully!")
            
            # Try stepping through first line
            print("Attempting to step through first line...")
            if debugger.step_over():
                print("✓ Step over successful!")
            else:
                print("✗ Step over failed")
        else:
            print("✗ Failed to load test file")
        
        # Cleanup test file
        try:
            os.remove(test_file)
        except:
            pass
        
    else:
        print("Failed to connect to WebSocket")
        print("Make sure the Buildbotics controller is running and accessible")
    
    # Cleanup
    comm.close()
    print("\nTest completed")

if __name__ == "__main__":
    test_both_modes()