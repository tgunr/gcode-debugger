#!/usr/bin/env python3
"""
Test script to validate MSG and DEBUG command output handling.
This will help us confirm our diagnosis of the WebSocket message processing.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from core.communication import BBCtrlCommunicator
import time
import threading

class MessageTester:
    def __init__(self):
        self.communicator = BBCtrlCommunicator()
        self.messages_received = []
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
    
    def on_error(self, error):
        """Capture all errors."""
        print(f"[ERROR] {error}")
    
    def on_state(self, state):
        """Capture state updates."""
        print(f"[STATE] {state}")
    
    def test_msg_debug_commands(self):
        """Test MSG and DEBUG commands with enhanced logging."""
        print("=== MSG/DEBUG Command Test ===")
        print("Connecting to controller...")
        
        if not self.communicator.connect_websocket():
            print("Failed to connect to controller!")
            return False
        
        print("Connected! Waiting for initial messages...")
        time.sleep(2)
        
        print("\n--- Testing MSG command ---")
        self.communicator.send_gcode("(MSG, Hello from debugger test!)")
        time.sleep(2)
        
        print("\n--- Testing DEBUG command ---")
        self.communicator.send_gcode("(DEBUG, Variable X=#1001)")
        time.sleep(2)
        
        print("\n--- Testing with JSON-RPC format ---")
        self.communicator.send_gcode("(MSG, JSON-RPC test message)", use_json_rpc=True)
        time.sleep(2)
        
        print("\n--- Testing DEBUG with JSON-RPC format ---")
        self.communicator.send_gcode("(DEBUG, JSON-RPC debug test)", use_json_rpc=True)
        time.sleep(2)
        
        print(f"\n=== Test Complete ===")
        print(f"Total messages received: {len(self.messages_received)}")
        
        # Close connection
        self.communicator.close()
        return True

def main():
    """Run the MSG/DEBUG test."""
    tester = MessageTester()
    
    try:
        success = tester.test_msg_debug_commands()
        if success:
            print("\nTest completed successfully!")
        else:
            print("\nTest failed!")
    except KeyboardInterrupt:
        print("\nTest interrupted by user")
    except Exception as e:
        print(f"\nTest failed with error: {e}")
    finally:
        tester.communicator.close()

if __name__ == "__main__":
    main()