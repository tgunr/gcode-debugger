#!/usr/bin/env python3
"""
MSG and DEBUG command handler for G-code Debugger

Since the Buildbotics controller doesn't send MSG/DEBUG output back via WebSocket,
this module provides local handling and display of these commands.
"""

import re
from typing import Optional, Callable

class MsgDebugHandler:
    """Handles MSG and DEBUG commands locally since controller doesn't return output."""
    
    def __init__(self, output_callback: Optional[Callable[[str, str], None]] = None):
        """
        Initialize the MSG/DEBUG handler.
        
        Args:
            output_callback: Function to call with (message_type, content) when MSG/DEBUG found
        """
        self.output_callback = output_callback
        
        # Regex patterns for MSG and DEBUG commands
        self.msg_pattern = re.compile(r'\(MSG,\s*([^)]+)\)', re.IGNORECASE)
        self.debug_pattern = re.compile(r'\(DEBUG,\s*([^)]+)\)', re.IGNORECASE)
    
    def process_command(self, command: str) -> bool:
        """
        Process a G-code command and check for MSG/DEBUG.
        
        Args:
            command: The G-code command to process
            
        Returns:
            True if MSG or DEBUG command was found and processed
        """
        command = command.strip()
        found_msg_debug = False
        
        # Check for MSG commands
        msg_matches = self.msg_pattern.findall(command)
        for msg_content in msg_matches:
            self._handle_msg(msg_content.strip())
            found_msg_debug = True
        
        # Check for DEBUG commands  
        debug_matches = self.debug_pattern.findall(command)
        for debug_content in debug_matches:
            self._handle_debug(debug_content.strip())
            found_msg_debug = True
            
        return found_msg_debug
    
    def _handle_msg(self, content: str):
        """Handle MSG command output."""
        message = f"MSG: {content}"
        if self.output_callback:
            self.output_callback("MSG", content)
        else:
            print(f"[MSG] {content}")
    
    def _handle_debug(self, content: str):
        """Handle DEBUG command output."""
        # For DEBUG commands, we can try to evaluate expressions
        processed_content = self._process_debug_content(content)
        message = f"DEBUG: {processed_content}"
        if self.output_callback:
            self.output_callback("DEBUG", processed_content)
        else:
            print(f"[DEBUG] {processed_content}")
    
    def _process_debug_content(self, content: str) -> str:
        """
        Process DEBUG content to show variable values where possible.
        
        This is a basic implementation - in a full system, this would
        interface with the G-code interpreter's variable system.
        """
        # Look for variable references like #1001, #<_x>, etc.
        var_pattern = re.compile(r'#(\d+|<[^>]+>)')
        
        def replace_var(match):
            var_ref = match.group(0)
            # In a real implementation, this would look up the actual variable value
            # For now, we'll just indicate it's a variable reference
            return f"{var_ref}[VAR]"
        
        processed = var_pattern.sub(replace_var, content)
        return processed

    def set_output_callback(self, callback: Callable[[str, str], None]):
        """Set the output callback function."""
        self.output_callback = callback


# Example usage and testing
if __name__ == "__main__":
    def test_output(msg_type, content):
        print(f"[{msg_type}] {content}")
    
    handler = MsgDebugHandler(test_output)
    
    # Test various MSG and DEBUG formats
    test_commands = [
        "(MSG, Hello World!)",
        "(DEBUG, X position = #5221)",
        "G1 X10 (MSG, Moving to X10)",
        "(DEBUG, Current tool = #5400)",
        "M3 S1000 (MSG, Spindle starting)",
        "(msg, lowercase test)",
        "(DEBUG, Variable test #1001 = #<_x>)",
    ]
    
    print("Testing MSG/DEBUG handler:")
    for cmd in test_commands:
        print(f"\nCommand: {cmd}")
        if handler.process_command(cmd):
            print("  -> MSG/DEBUG found and processed")
        else:
            print("  -> No MSG/DEBUG found")