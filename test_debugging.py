#!/usr/bin/env python3
"""
Test script to isolate the debugging line highlighting issue.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from core.gcode_parser import GCodeParser
from core.debugger import GCodeDebugger
from core.communication import BBCtrlCommunicator

def test_debugging_flow():
    """Test the debugging flow without GUI."""
    print("="*60)
    print("Testing G-code debugging flow")
    print("="*60)
    
    # Create a mock communicator (we won't actually connect)
    class MockCommunicator:
        def __init__(self):
            self.last_state = {}
            
        def send_gcode(self, command):
            print(f"MOCK: Would send G-code: {command}")
            return True
            
        def pause(self):
            print("MOCK: Would pause")
            
        def stop(self):
            print("MOCK: Would stop")
            
        def emergency_stop(self):
            print("MOCK: Would emergency stop")
            return True
    
    # Create debugger with mock communicator
    communicator = MockCommunicator()
    debugger = GCodeDebugger(communicator)
    
    # Set up callbacks to trace what happens
    def on_line_changed(line_number):
        print(f"CALLBACK: Line changed to {line_number}")
        
    def on_state_changed(state):
        print(f"CALLBACK: State changed to {state}")
        
    def on_error(error):
        print(f"CALLBACK: Error - {error}")
    
    debugger.set_callbacks(
        line_changed=on_line_changed,
        state_changed=on_state_changed,
        error=on_error
    )
    
    # Load the test file
    test_file = "test_debug.gcode"
    print(f"\n1. Loading file: {test_file}")
    if debugger.load_file(test_file):
        print("   File loaded successfully")
        
        # Print parser info
        parser = debugger.parser
        print(f"   Total lines: {len(parser.lines)}")
        executable_lines = parser.get_executable_lines()
        print(f"   Executable lines: {len(executable_lines)}")
        
        print("\n   All lines:")
        for i, line in enumerate(parser.lines):
            print(f"   Line {line.line_number}: {line.original} (executable: {line.is_executable})")
            
        print("\n   Executable lines only:")
        for i, line in enumerate(executable_lines):
            print(f"   Index {i}: Line {line.line_number}: {line.original}")
        
        # Test initial state
        print(f"\n2. Initial debugger state:")
        print(f"   current_line_index: {debugger.current_line_index}")
        current_line = debugger.get_current_line()
        print(f"   current_line: {current_line.line_number if current_line else None}")
        print(f"   current_line_number: {debugger.get_current_line_number()}")
        
        # Test stepping
        print(f"\n3. Testing step operations:")
        for step in range(5):  # Test first 5 steps
            print(f"\n   Step {step + 1}:")
            print(f"   Before step - index: {debugger.current_line_index}, line: {debugger.get_current_line_number()}")
            
            if debugger.step_over():
                print(f"   After step - index: {debugger.current_line_index}, line: {debugger.get_current_line_number()}")
            else:
                print("   Step failed or reached end")
                break
                
    else:
        print("   Failed to load file")

if __name__ == "__main__":
    test_debugging_flow()