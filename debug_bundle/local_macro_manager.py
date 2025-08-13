#!/usr/bin/env python3
"""
Local Macro Manager for G-code Debugger

Manages local macros stored in debugger (not on controller).
Local macros are executed by sending individual commands through the debugger.
"""

import json
import os
from typing import List, Dict, Optional
from dataclasses import dataclass, asdict
from datetime import datetime

@dataclass
class LocalMacro:
    """Represents a local G-code macro stored in debugger."""
    name: str
    description: str
    commands: List[str]
    created_date: str
    modified_date: str
    category: str = "user"
    is_local: bool = True

class LocalMacroManager:
    """Manages local macros stored in debugger (not on controller)."""
    
    def __init__(self, local_macros_directory: str = "local_macros"):
        self.local_macros_directory = local_macros_directory
        self.local_macros_file = os.path.join(local_macros_directory, "local_macros.json")
        self.local_macros: Dict[str, LocalMacro] = {}
        self.categories = ["system", "user", "homing", "tool_change", "probing", "custom", "debug"]
        
        # Ensure directory exists
        os.makedirs(self.local_macros_directory, exist_ok=True)
        
        # Load existing local macros
        self.load_local_macros()
        
        # Create default local macros if none exist
        if not self.local_macros:
            self._create_default_local_macros()
    
    def create_local_macro(self, name: str, commands: List[str], description: str = "", 
                          category: str = "user") -> bool:
        """Create a new local macro."""
        if name in self.local_macros:
            return False  # Macro already exists
        
        current_time = datetime.now().isoformat()
        
        local_macro = LocalMacro(
            name=name,
            description=description,
            commands=commands,
            created_date=current_time,
            modified_date=current_time,
            category=category,
            is_local=True
        )
        
        self.local_macros[name] = local_macro
        self.save_local_macros()
        return True
    
    def update_local_macro(self, name: str, commands: List[str] = None, 
                          description: str = None, category: str = None) -> bool:
        """Update an existing local macro."""
        if name not in self.local_macros:
            return False
        
        local_macro = self.local_macros[name]
        
        if commands is not None:
            local_macro.commands = commands
        if description is not None:
            local_macro.description = description
        if category is not None:
            local_macro.category = category
        
        local_macro.modified_date = datetime.now().isoformat()
        self.save_local_macros()
        return True
    
    def delete_local_macro(self, name: str) -> bool:
        """Delete a local macro."""
        if name not in self.local_macros:
            return False
        
        del self.local_macros[name]
        self.save_local_macros()
        return True
    
    def get_local_macro(self, name: str) -> Optional[LocalMacro]:
        """Get a local macro by name."""
        return self.local_macros.get(name)
    
    def get_local_macros_by_category(self, category: str) -> List[LocalMacro]:
        """Get all local macros in a specific category."""
        return [macro for macro in self.local_macros.values() if macro.category == category]
    
    def get_all_local_macros(self) -> List[LocalMacro]:
        """Get all local macros."""
        return list(self.local_macros.values())
    
    def save_local_macros(self) -> bool:
        """Save all local macros to file."""
        try:
            # Convert macros to dictionary format
            macros_data = {}
            for name, macro in self.local_macros.items():
                macros_data[name] = asdict(macro)
            
            # Create file structure
            file_data = {
                "version": "1.0",
                "created_date": datetime.now().isoformat(),
                "local_macros": macros_data
            }
            
            with open(self.local_macros_file, 'w') as f:
                json.dump(file_data, f, indent=2)
            return True
        except Exception as e:
            print(f"Error saving local macros: {e}")
            return False
    
    def load_local_macros(self) -> bool:
        """Load local macros from file."""
        try:
            if not os.path.exists(self.local_macros_file):
                return False
            
            with open(self.local_macros_file, 'r') as f:
                file_data = json.load(f)
            
            # Extract macros from file structure
            macros_data = file_data.get("local_macros", {})
            
            self.local_macros.clear()
            for name, macro_data in macros_data.items():
                local_macro = LocalMacro(**macro_data)
                self.local_macros[name] = local_macro
            
            return True
        except Exception as e:
            print(f"Error loading local macros: {e}")
            return False
    
    def export_local_macro(self, name: str, filepath: str) -> bool:
        """Export a local macro to a G-code file."""
        if name not in self.local_macros:
            return False
        
        try:
            local_macro = self.local_macros[name]
            with open(filepath, 'w') as f:
                f.write(f"; Local Macro: {local_macro.name}\n")
                f.write(f"; Description: {local_macro.description}\n")
                f.write(f"; Created: {local_macro.created_date}\n")
                f.write(f"; Category: {local_macro.category}\n")
                f.write(f"; Type: Local (executed by debugger)\n")
                f.write(";\n")
                
                for command in local_macro.commands:
                    f.write(f"{command}\n")
            
            return True
        except Exception as e:
            print(f"Error exporting local macro: {e}")
            return False
    
    def import_local_macro_from_file(self, name: str, filepath: str, 
                                   description: str = "", category: str = "user") -> bool:
        """Import a local macro from a G-code file."""
        try:
            with open(filepath, 'r') as f:
                lines = f.readlines()
            
            commands = []
            for line in lines:
                line = line.strip()
                # Skip comments and empty lines
                if line and not line.startswith(';') and not line.startswith('('):
                    commands.append(line)
            
            return self.create_local_macro(name, commands, description, category)
        except Exception as e:
            print(f"Error importing local macro: {e}")
            return False
    
    def _create_default_local_macros(self):
        """Create default local macros for debugging."""
        # Quick positioning macros for debugging
        self.create_local_macro(
            name="Debug Home XY",
            commands=["G28 X Y"],
            description="Home X and Y axes only (for debugging)",
            category="debug"
        )
        
        self.create_local_macro(
            name="Debug Safe Position",
            commands=[
                "G91",           # Relative mode
                "G0 Z5",         # Move Z up 5mm
                "G90",           # Absolute mode
                "G0 X0 Y0"       # Move to origin
            ],
            description="Move to safe debugging position",
            category="debug"
        )
        
        self.create_local_macro(
            name="Debug Zero Current",
            commands=["G92 X0 Y0 Z0"],
            description="Set current position as zero (debugging)",
            category="debug"
        )
        
        self.create_local_macro(
            name="Debug Small Move",
            commands=[
                "G91",           # Relative mode
                "G0 X1 Y1",      # Small move
                "G90"            # Absolute mode
            ],
            description="Small test movement for debugging",
            category="debug"
        )
        
        self.create_local_macro(
            name="Debug Spindle Test",
            commands=[
                "M3 S500",       # Spindle on at low speed
                "G4 P2",         # Wait 2 seconds
                "M5"             # Spindle off
            ],
            description="Quick spindle test (low speed)",
            category="debug"
        )
        
        # Quick setup macros
        self.create_local_macro(
            name="Quick Setup",
            commands=[
                "G21",           # Metric units
                "G90",           # Absolute positioning
                "G94",           # Feed rate per minute
                "G17"            # XY plane selection
            ],
            description="Quick machine setup for debugging",
            category="system"
        )
        
        # Save all default local macros
        self.save_local_macros()

class LocalMacroExecutor:
    """Executes local macros by sending individual commands."""
    
    def __init__(self, communicator, message_callback=None):
        self.communicator = communicator
        self.message_callback = message_callback
        self.executing = False
        self.current_macro: Optional[LocalMacro] = None
        self.current_command_index = 0
        
        # Execution callbacks
        self.progress_callback: Optional[callable] = None
        self.completion_callback: Optional[callable] = None
        self.error_callback: Optional[callable] = None
    
    def set_callbacks(self, progress=None, completion=None, error=None):
        """Set callback functions for local macro execution events."""
        if progress:
            self.progress_callback = progress
        if completion:
            self.completion_callback = completion
        if error:
            self.error_callback = error
    
    def execute_local_macro(self, local_macro: LocalMacro, delay: float = 0.1) -> bool:
        """Execute a local macro by sending commands individually."""
        if self.executing:
            return False
        
        self.executing = True
        self.current_macro = local_macro
        self.current_command_index = 0
        
        if self.message_callback:
            self.message_callback(f"Executing local macro: {local_macro.name}")
        
        try:
            for i, command in enumerate(local_macro.commands):
                if not self.executing:  # Check for cancellation
                    break
                
                self.current_command_index = i
                
                # Send command through communicator
                if hasattr(self.communicator, 'send_gcode'):
                    success = self.communicator.send_gcode(command)
                else:
                    success = False
                
                if not success:
                    if self.error_callback:
                        self.error_callback(f"Failed to send command: {command}")
                    self.executing = False
                    return False
                
                # Update progress
                if self.progress_callback:
                    progress = (i + 1) / len(local_macro.commands) * 100
                    self.progress_callback(progress, command)
                
                # Small delay between commands
                if i < len(local_macro.commands) - 1:
                    import time
                    time.sleep(delay)
            
            self.executing = False
            
            if self.completion_callback:
                self.completion_callback(local_macro.name)
            
            if self.message_callback:
                self.message_callback(f"Local macro '{local_macro.name}' completed")
            
            return True
            
        except Exception as e:
            self.executing = False
            if self.error_callback:
                self.error_callback(f"Local macro execution error: {e}")
            return False
    
    def cancel_execution(self):
        """Cancel the current local macro execution."""
        self.executing = False
        if self.message_callback:
            self.message_callback("Local macro execution cancelled")
    
    def is_executing(self) -> bool:
        """Check if a local macro is currently executing."""
        return self.executing
    
    def get_execution_status(self) -> Dict[str, any]:
        """Get the current execution status."""
        if not self.executing or not self.current_macro:
            return {"executing": False}
        
        return {
            "executing": True,
            "macro_name": self.current_macro.name,
            "current_command_index": self.current_command_index,
            "total_commands": len(self.current_macro.commands),
            "progress_percent": (self.current_command_index / len(self.current_macro.commands)) * 100
        }