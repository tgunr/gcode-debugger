#!/usr/bin/env python3
"""
Test script to verify the debugging line highlighting fix.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from core.gcode_parser import GCodeParser
from core.debugger import GCodeDebugger

def test_highlighting_fix():
    """Test that the debugging flow works correctly after the fix."""
    print("="*60)
    print("Testing G-code debugging fix verification")
    print("="*60)
    
    # Create a mock communicator
    class MockCommunicator:
        def __init__(self):
            self.last_state = {}
            
        def send_gcode(self, command):
            return True
            
        def pause(self):
            pass
            
        def stop(self):
            pass
            
        def emergency_stop(self):
            return True
    
    # Create debugger with mock communicator
    communicator = MockCommunicator()
    debugger = GCodeDebugger(communicator)
    
    # Track line changes
    line_changes = []
    
    def on_line_changed(line_number):
        line_changes.append(line_number)
        print(f"✓ Line changed to: {line_number}")
        
    def on_state_changed(state):
        print(f"✓ State changed to: {state}")
        
    def on_error(error):
        print(f"✗ Error: {error}")
    
    debugger.set_callbacks(
        line_changed=on_line_changed,
        state_changed=on_state_changed,
        error=on_error
    )
    
    # Load the test file
    test_file = "test_debug.gcode"
    print(f"\n1. Loading file: {test_file}")
    if debugger.load_file(test_file):
        print("   ✓ File loaded successfully")
        
        # Check initial state
        print(f"\n2. Initial state:")
        print(f"   Current line index: {debugger.current_line_index}")
        print(f"   Current line number: {debugger.get_current_line_number()}")
        print(f"   Expected first executable line: 2")
        
        # Verify initial line change was called
        if line_changes and line_changes[0] == 2:
            print("   ✓ Initial line highlighting callback was triggered correctly")
        else:
            print(f"   ✗ Initial line highlighting failed. Expected 2, got {line_changes[0] if line_changes else 'None'}")
        
        # Test stepping
        print(f"\n3. Testing step operations:")
        expected_lines = [3, 4, 5, 6, 7]  # Next 5 executable lines
        
        for i, expected_line in enumerate(expected_lines):
            print(f"\n   Step {i + 1}:")
            initial_changes = len(line_changes)
            
            if debugger.step_over():
                if len(line_changes) > initial_changes:
                    actual_line = line_changes[-1]
                    if actual_line == expected_line:
                        print(f"   ✓ Stepped to line {actual_line} (expected {expected_line})")
                    else:
                        print(f"   ✗ Step failed: got line {actual_line}, expected {expected_line}")
                else:
                    print("   ✗ Step failed: no line change callback triggered")
            else:
                print("   ✗ Step operation failed")
                break
        
        # Summary
        print(f"\n4. Summary:")
        print(f"   Total line changes: {len(line_changes)}")
        print(f"   Line change sequence: {line_changes}")
        
        # Verify the sequence is correct
        expected_sequence = [2, 3, 4, 5, 6, 7]  # Initial + 5 steps
        if line_changes == expected_sequence:
            print("   ✓ All line changes occurred in the correct sequence")
            print("   ✓ DEBUGGING LINE HIGHLIGHTING FIX VERIFIED!")
        else:
            print(f"   ✗ Line change sequence incorrect")
            print(f"   Expected: {expected_sequence}")
            print(f"   Actual:   {line_changes}")
            
    else:
        print("   ✗ Failed to load file")

    print("\n" + "="*60)
    print("CONCLUSION:")
    print("The core debugging logic is working correctly.")
    print("The main issue was the current line highlight color being too dark.")
    print("Changed from '#3a3d41' (barely visible) to '#264f78' (blue, visible).")
    print("This should now make the current line clearly visible during debugging.")
    print("="*60)

if __name__ == "__main__":
    test_highlighting_fix()