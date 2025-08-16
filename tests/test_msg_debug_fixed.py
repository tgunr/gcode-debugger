#!/usr/bin/env python3
"""
Test script to verify MSG and DEBUG command output is now working.
This tests the enhanced communication module with local MSG/DEBUG processing.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from core.communication import BBCtrlCommunicator
import time
import threading

class EnhancedMessageTester:
    def __init__(self):
        self.communicator = BBCtrlCommunicator()
        self.messages_received = []
        self.msg_debug_outputs = []
        self.setup_callbacks()
    
    def setup_callbacks(self):
        """Setup callbacks to capture all messages."""
        self.communicator.set_callbacks(
            message_callback=self.on_message,
            error_callback=self.on_error,
            state_callback=self.on_state
        )
    
    def on_message(self, message):
        """Capture all messages."""
        print(f"[MESSAGE] {message}")
        self.messages_received.append(message)
        
        # Track MSG/DEBUG outputs specifically
        if message.startswith("[MSG]") or message.startswith("[DEBUG]"):
            self.msg_debug_outputs.append(message)
    
    def on_error(self, error):
        """Capture all errors."""
        print(f"[ERROR] {error}")
    
    def on_state(self, state):
        """Capture state updates (minimal logging)."""
        print(f"[STATE] Machine state updated")
    
    def test_enhanced_msg_debug(self):
        """Test MSG and DEBUG commands with enhanced local processing."""
        print("=== Enhanced MSG/DEBUG Command Test ===")
        print("Connecting to controller...")
        
        if not self.communicator.connect_websocket():
            print("Failed to connect to controller!")
            return False
        
        print("Connected! Testing MSG/DEBUG processing...")
        time.sleep(1)
        
        # Test various MSG commands
        print("\n--- Testing MSG Commands ---")
        test_msg_commands = [
            "(MSG, Hello from enhanced debugger!)",
            "(MSG, Current operation: Testing)",
            "G1 X10 (MSG, Moving to position X10)",
            "(msg, lowercase msg test)",
        ]
        
        for cmd in test_msg_commands:
            print(f"\nSending: {cmd}")
            self.communicator.send_gcode(cmd)
            time.sleep(0.5)
        
        # Test various DEBUG commands
        print("\n--- Testing DEBUG Commands ---")
        test_debug_commands = [
            "(DEBUG, Variable test #1001)",
            "(DEBUG, X position = #5221)",
            "(DEBUG, Current tool = #5400)",
            "(DEBUG, Expression: #<_x> + #<_y>)",
        ]
        
        for cmd in test_debug_commands:
            print(f"\nSending: {cmd}")
            self.communicator.send_gcode(cmd)
            time.sleep(0.5)
        
        # Test mixed commands
        print("\n--- Testing Mixed Commands ---")
        mixed_commands = [
            "G0 X0 Y0 (MSG, Returning to origin)",
            "M3 S1000 (DEBUG, Spindle speed = #5037)",
            "(MSG, Test complete) (DEBUG, Final check)",
        ]
        
        for cmd in mixed_commands:
            print(f"\nSending: {cmd}")
            self.communicator.send_gcode(cmd)
            time.sleep(0.5)
        
        print(f"\n=== Test Results ===")
        print(f"Total messages received: {len(self.messages_received)}")
        print(f"MSG/DEBUG outputs captured: {len(self.msg_debug_outputs)}")
        
        if self.msg_debug_outputs:
            print("\nCaptured MSG/DEBUG outputs:")
            for output in self.msg_debug_outputs:
                print(f"  {output}")
        else:
            print("\nNo MSG/DEBUG outputs captured - there may be an issue!")
        
        # Close connection
        self.communicator.close()
        return len(self.msg_debug_outputs) > 0

def main():
    """Run the enhanced MSG/DEBUG test."""
    tester = EnhancedMessageTester()
    
    try:
        success = tester.test_enhanced_msg_debug()
        if success:
            print("\n✅ Test completed successfully! MSG/DEBUG output is now working.")
        else:
            print("\n❌ Test failed - MSG/DEBUG output not captured.")
    except KeyboardInterrupt:
        print("\nTest interrupted by user")
    except Exception as e:
        print(f"\nTest failed with error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        tester.communicator.close()

if __name__ == "__main__":
    main()