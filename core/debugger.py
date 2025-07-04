#!/usr/bin/env python3
"""
G-code Debugger Engine

Manages debugging sessions, execution control, breakpoints, and state tracking.
"""

import time
from typing import List, Set, Dict, Any, Optional, Callable
from enum import Enum
from dataclasses import dataclass, field
from .gcode_parser import GCodeParser, GCodeLine
from .communication import BBCtrlCommunicator

class DebugState(Enum):
    """Debugger execution states."""
    STOPPED = "stopped"
    RUNNING = "running"
    PAUSED = "paused"
    STEPPING = "stepping"
    WAITING = "waiting"
    ERROR = "error"

@dataclass
class ExecutionFrame:
    """Represents a point in execution for state restoration."""
    line_number: int
    machine_position: Dict[str, float] = field(default_factory=dict)
    modal_state: Dict[str, Any] = field(default_factory=dict)
    timestamp: float = field(default_factory=time.time)

class GCodeDebugger:
    """Main debugger engine for G-code debugging."""
    
    def __init__(self, communicator: BBCtrlCommunicator):
        self.communicator = communicator
        self.parser = GCodeParser()
        
        # Execution state
        self.debug_state = DebugState.STOPPED
        self.current_line_index = 0  # Index in executable lines
        self.breakpoints: Set[int] = set()  # Line numbers with breakpoints
        
        # Execution history for go-back functionality
        self.execution_stack: List[ExecutionFrame] = []
        self.max_stack_size = 1000
        
        # Callbacks
        self.line_changed_callback: Optional[Callable] = None
        self.state_changed_callback: Optional[Callable] = None
        self.error_callback: Optional[Callable] = None
        
        # Safety settings
        self.confirm_dangerous_moves = True
        self.max_rapid_speed = 10000  # mm/min
        self.safe_z_height = 5.0     # mm
        
    def set_callbacks(self, line_changed=None, state_changed=None, error=None):
        """Set callback functions for debugger events."""
        if line_changed:
            self.line_changed_callback = line_changed
        if state_changed:
            self.state_changed_callback = state_changed
        if error:
            self.error_callback = error
    
    def load_file(self, filepath: str) -> bool:
        """Load a G-code file for debugging."""
        try:
            success = self.parser.load_file(filepath)
            if success:
                self.reset_session()
                self._notify_state_changed()
            return success
        except Exception as e:
            self._notify_error(f"Failed to load file: {e}")
            return False
    
    def reset_session(self):
        """Reset the debugging session to the beginning."""
        self.debug_state = DebugState.STOPPED
        self.current_line_index = 0
        self.execution_stack.clear()
        self._notify_line_changed()
        self._notify_state_changed()
    
    def set_breakpoint(self, line_number: int) -> bool:
        """Set a breakpoint at the specified line number."""
        line = self.parser.get_line_by_number(line_number)
        if line and line.is_executable:
            self.breakpoints.add(line_number)
            return True
        return False
    
    def remove_breakpoint(self, line_number: int) -> bool:
        """Remove a breakpoint from the specified line number."""
        if line_number in self.breakpoints:
            self.breakpoints.remove(line_number)
            return True
        return False
    
    def toggle_breakpoint(self, line_number: int) -> bool:
        """Toggle breakpoint at the specified line number."""
        if line_number in self.breakpoints:
            return self.remove_breakpoint(line_number)
        else:
            return self.set_breakpoint(line_number)
    
    def get_current_line(self) -> Optional[GCodeLine]:
        """Get the current line being debugged."""
        return self.parser.get_executable_line_at_index(self.current_line_index)
    
    def get_current_line_number(self) -> int:
        """Get the current line number."""
        current_line = self.get_current_line()
        return current_line.line_number if current_line else 0
    
    def step_over(self) -> bool:
        """Execute the current line and move to the next."""
        if self.debug_state in [DebugState.ERROR, DebugState.RUNNING]:
            return False
        
        current_line = self.get_current_line()
        if not current_line:
            self._notify_error("No current line to execute")
            return False
        
        # Save current state for go-back functionality
        self._save_execution_frame()
        
        # Execute the line
        if self._execute_line(current_line):
            self.current_line_index += 1
            self._notify_line_changed()
            return True
        
        return False
    
    def step_to_line(self, target_line_number: int) -> bool:
        """Execute until reaching the specified line number."""
        if self.debug_state in [DebugState.ERROR, DebugState.RUNNING]:
            return False
        
        self.debug_state = DebugState.RUNNING
        self._notify_state_changed()
        
        try:
            while True:
                current_line = self.get_current_line()
                if not current_line:
                    break
                
                # Check if we've reached the target
                if current_line.line_number >= target_line_number:
                    break
                
                # Check for breakpoints
                if current_line.line_number in self.breakpoints:
                    self.debug_state = DebugState.PAUSED
                    self._notify_state_changed()
                    return True
                
                # Execute current line
                if not self.step_over():
                    return False
                
                # Small delay to prevent overwhelming the controller
                time.sleep(0.1)
            
            self.debug_state = DebugState.PAUSED
            self._notify_state_changed()
            return True
            
        except Exception as e:
            self.debug_state = DebugState.ERROR
            self._notify_error(f"Error during step to line: {e}")
            return False
    
    def skip_line(self) -> bool:
        """Skip the current line without executing it."""
        if self.debug_state == DebugState.ERROR:
            return False
        
        current_line = self.get_current_line()
        if not current_line:
            return False
        
        self.current_line_index += 1
        self._notify_line_changed()
        return True
    
    def skip_to_line(self, target_line_number: int) -> bool:
        """Skip to the specified line without executing intermediate lines."""
        executable_lines = self.parser.get_executable_lines()
        
        # Find the target line index
        target_index = -1
        for i, line in enumerate(executable_lines):
            if line.line_number >= target_line_number:
                target_index = i
                break
        
        if target_index == -1:
            return False
        
        self.current_line_index = target_index
        self._notify_line_changed()
        return True
    
    def go_back(self) -> bool:
        """Go back to the previous execution point."""
        if not self.execution_stack:
            self._notify_error("No previous execution point available")
            return False
        
        # Get the previous frame
        previous_frame = self.execution_stack.pop()
        
        # Find the line index for the previous line
        executable_lines = self.parser.get_executable_lines()
        target_index = -1
        
        for i, line in enumerate(executable_lines):
            if line.line_number == previous_frame.line_number:
                target_index = i
                break
        
        if target_index == -1:
            self._notify_error("Cannot find previous line")
            return False
        
        # Restore position (this would need machine-specific implementation)
        if previous_frame.machine_position:
            restoration_commands = self._generate_restoration_commands(previous_frame)
            for cmd in restoration_commands:
                self.communicator.send_gcode(cmd)
                time.sleep(0.1)
        
        self.current_line_index = target_index
        self._notify_line_changed()
        return True
    
    def continue_execution(self) -> bool:
        """Continue execution from current line until breakpoint or end."""
        if self.debug_state == DebugState.ERROR:
            return False
        
        self.debug_state = DebugState.RUNNING
        self._notify_state_changed()
        
        try:
            while True:
                current_line = self.get_current_line()
                if not current_line:
                    # Reached end of program
                    self.debug_state = DebugState.STOPPED
                    self._notify_state_changed()
                    return True
                
                # Check for breakpoint
                if current_line.line_number in self.breakpoints:
                    self.debug_state = DebugState.PAUSED
                    self._notify_state_changed()
                    return True
                
                # Execute current line
                if not self.step_over():
                    return False
                
                # Small delay
                time.sleep(0.1)
                
        except Exception as e:
            self.debug_state = DebugState.ERROR
            self._notify_error(f"Error during continue: {e}")
            return False
    
    def pause_execution(self) -> bool:
        """Pause the current execution."""
        if self.debug_state == DebugState.RUNNING:
            self.debug_state = DebugState.PAUSED
            self.communicator.pause()
            self._notify_state_changed()
            return True
        return False
    
    def stop_execution(self) -> bool:
        """Stop the current execution."""
        self.debug_state = DebugState.STOPPED
        self.communicator.stop()
        self._notify_state_changed()
        return True
    
    def emergency_stop(self) -> bool:
        """Execute emergency stop."""
        self.debug_state = DebugState.ERROR
        success = self.communicator.emergency_stop()
        self._notify_state_changed()
        if success:
            self._notify_error("Emergency stop activated")
        return success
    
    def _execute_line(self, line: GCodeLine) -> bool:
        """Execute a single line of G-code."""
        if not line.is_executable:
            return False
        
        # Safety checks
        if self.confirm_dangerous_moves and self._is_dangerous_move(line.content):
            # In a real implementation, this would show a confirmation dialog
            pass
        
        # Send the command
        return self.communicator.send_gcode(line.content)
    
    def _is_dangerous_move(self, gcode: str) -> bool:
        """Check if a G-code command might be dangerous."""
        gcode_upper = gcode.upper()
        
        # Check for rapid moves to negative Z
        if 'G0' in gcode_upper and 'Z-' in gcode_upper:
            return True
        
        # Check for very high feed rates
        if 'F' in gcode_upper:
            import re
            feed_match = re.search(r'F(\d+)', gcode_upper)
            if feed_match and int(feed_match.group(1)) > self.max_rapid_speed:
                return True
        
        return False
    
    def _save_execution_frame(self):
        """Save current execution state for go-back functionality."""
        current_line = self.get_current_line()
        if not current_line:
            return
        
        # Get current machine state (simplified - real implementation would get actual positions)
        machine_state = self.communicator.last_state
        
        frame = ExecutionFrame(
            line_number=current_line.line_number,
            machine_position={
                'x': machine_state.get('posx', 0),
                'y': machine_state.get('posy', 0),
                'z': machine_state.get('posz', 0),
            },
            modal_state={
                'units': machine_state.get('imperial', False),
                'feed_mode': machine_state.get('feed_mode', 'G94'),
            }
        )
        
        self.execution_stack.append(frame)
        
        # Limit stack size
        if len(self.execution_stack) > self.max_stack_size:
            self.execution_stack.pop(0)
    
    def _generate_restoration_commands(self, frame: ExecutionFrame) -> List[str]:
        """Generate G-code commands to restore machine state."""
        commands = []
        
        # Move to safe height first
        commands.append(f"G0 Z{self.safe_z_height}")
        
        # Restore position
        if frame.machine_position:
            pos = frame.machine_position
            commands.append(f"G0 X{pos.get('x', 0)} Y{pos.get('y', 0)}")
            commands.append(f"G0 Z{pos.get('z', 0)}")
        
        return commands
    
    def _notify_line_changed(self):
        """Notify that the current line has changed."""
        if self.line_changed_callback:
            self.line_changed_callback(self.get_current_line_number())
    
    def _notify_state_changed(self):
        """Notify that the debugger state has changed."""
        if self.state_changed_callback:
            self.state_changed_callback(self.debug_state)
    
    def _notify_error(self, message: str):
        """Notify about an error."""
        if self.error_callback:
            self.error_callback(message)
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get debugging session statistics."""
        current_line = self.get_current_line()
        executable_lines = self.parser.get_executable_lines()
        
        return {
            'current_line': current_line.line_number if current_line else 0,
            'current_index': self.current_line_index,
            'total_executable': len(executable_lines),
            'progress_percent': (self.current_line_index / len(executable_lines) * 100) 
                               if executable_lines else 0,
            'breakpoints_count': len(self.breakpoints),
            'execution_stack_size': len(self.execution_stack),
            'debug_state': self.debug_state.value
        }