#!/usr/bin/env python3
"""
Macro Manager for G-code Debugger

Handles creation, storage, and execution of G-code macros.
"""

import os
import json
from typing import List, Dict, Optional, Any
from dataclasses import dataclass, asdict
from datetime import datetime

@dataclass
class Macro:
    """Represents a G-code macro."""
    name: str
    description: str
    commands: List[str]
    created_date: str
    modified_date: str
    category: str = "user"
    color: str = "#e6e6e6"
    hotkey: str = ""

class MacroManager:
    """Manages G-code macros for the debugger."""
    
    def __init__(self, macros_directory: str = "macros"):
        self.macros_directory = os.path.abspath(os.path.expanduser(str(macros_directory)))
        self.macros: Dict[str, Macro] = {}
        self.categories = ["system", "user", "homing", "tool_change", "probing", "custom"]
        
        print(f"DEBUG: Initializing MacroManager with directory: {self.macros_directory}")
        
        try:
            # Ensure macros directory exists
            os.makedirs(self.macros_directory, exist_ok=True)
            
            # Verify directory is writable
            if not os.access(self.macros_directory, os.W_OK):
                print(f"WARNING: Directory is not writable: {self.macros_directory}")
            
            # Load existing macros
            self.load_macros()
            
            # Create default macros if none exist
            if not self.macros:
                print("DEBUG: No macros found, creating default macros")
                self._create_default_macros()
                
        except Exception as e:
            print(f"ERROR: Failed to initialize MacroManager: {str(e)}")
            # Try to continue with empty macro list if there's an error
            self.macros = {}
    
    def create_macro(self, name: str, commands: List[str], description: str = "", 
                    category: str = "user", color: str = "#e6e6e6", hotkey: str = "") -> bool:
        """Create a new macro."""
        if name in self.macros:
            return False  # Macro already exists
        
        current_time = datetime.now().isoformat()
        
        macro = Macro(
            name=name,
            description=description,
            commands=commands,
            created_date=current_time,
            modified_date=current_time,
            category=category,
            color=color,
            hotkey=hotkey
        )
        
        self.macros[name] = macro
        self.save_macro(name)
        return True
    
    def update_macro(self, name: str, commands: List[str] = None, description: str = None,
                    category: str = None, color: str = None, hotkey: str = None) -> bool:
        """Update an existing macro."""
        if name not in self.macros:
            return False
        
        macro = self.macros[name]
        
        if commands is not None:
            macro.commands = commands
        if description is not None:
            macro.description = description
        if category is not None:
            macro.category = category
        if color is not None:
            macro.color = color
        if hotkey is not None:
            macro.hotkey = hotkey
        
        macro.modified_date = datetime.now().isoformat()
        self.save_macro(name)
        return True
    
    def delete_macro(self, name: str) -> bool:
        """Delete a macro."""
        if name not in self.macros:
            return False
        
        # Remove from memory
        del self.macros[name]
        
        # Remove file
        filepath = os.path.join(self.macros_directory, f"{name}.json")
        if os.path.exists(filepath):
            os.remove(filepath)
        
        return True
    
    def get_macro(self, name: str) -> Optional[Macro]:
        """Get a macro by name."""
        return self.macros.get(name)
    
    def get_macros_by_category(self, category: str) -> List[Macro]:
        """Get all macros in a specific category."""
        return [macro for macro in self.macros.values() if macro.category == category]
    
    def get_all_macros(self) -> List[Macro]:
        """Get all macros."""
        return list(self.macros.values())
    
    def save_macro(self, name: str) -> bool:
        """Save a macro to file."""
        if name not in self.macros:
            return False
        
        try:
            filepath = os.path.join(self.macros_directory, f"{name}.json")
            with open(filepath, 'w') as f:
                json.dump(asdict(self.macros[name]), f, indent=2)
            return True
        except Exception:
            return False
    
    def load_macro(self, name: str) -> bool:
        """Load a macro from file."""
        try:
            filepath = os.path.join(self.macros_directory, f"{name}.json")
            if not os.path.exists(filepath):
                return False
            
            with open(filepath, 'r') as f:
                data = json.load(f)
            
            macro = Macro(**data)
            self.macros[name] = macro
            return True
        except Exception:
            return False
    
    def load_macros(self):
        """Load all macros from the macros directory."""
        print(f"DEBUG: Loading macros from directory: {os.path.abspath(self.macros_directory)}")
        if not os.path.exists(self.macros_directory):
            print(f"ERROR: Macros directory does not exist: {os.path.abspath(self.macros_directory)}")
            return
        
        file_count = 0
        for filename in os.listdir(self.macros_directory):
            if filename.endswith('.json'):
                file_count += 1
                name = filename[:-5]  # Remove .json extension
                print(f"DEBUG: Loading macro from file: {filename}")
                if not self.load_macro(name):
                    print(f"WARNING: Failed to load macro from file: {filename}")
        
        print(f"DEBUG: Loaded {len(self.macros)} macros from {file_count} files")
    
    def save_all_macros(self):
        """Save all macros to files."""
        for name in self.macros:
            self.save_macro(name)
    
    def sync_from_controller(self, communicator) -> bool:
        """Sync macros from the controller to the local directory.
        
        Args:
            communicator: BBCtrlCommunicator instance for controller communication
            
        Returns:
            bool: True if sync was successful, False otherwise
        """
        print("DEBUG: Starting sync_from_controller")
        try:
            # Ensure directory exists and is writable
            print(f"DEBUG: Ensuring directory exists: {self.macros_directory}")
            os.makedirs(self.macros_directory, exist_ok=True)
            if not os.access(self.macros_directory, os.W_OK):
                error_msg = f"ERROR: Directory is not writable: {self.macros_directory}"
                print(error_msg)
                return False
            
            # Get macros from controller
            print("DEBUG: Fetching macros from controller...")
            controller_macros = communicator.get_macros()
            if controller_macros is None:
                print("WARNING: No macros found on controller or failed to fetch")
                return False
                
            print(f"DEBUG: Found {len(controller_macros)} macros on controller")
            if controller_macros:
                print(f"DEBUG: Controller macro names: {list(controller_macros.keys())}")
            
            synced_macros = set()
            
            # Process each macro from controller
            for macro_name, macro_data in controller_macros.items():
                try:
                    print(f"DEBUG: Processing macro: {macro_name}")
                    # Skip invalid macro names
                    if not macro_name or not isinstance(macro_name, str):
                        print(f"WARNING: Skipping invalid macro name: {macro_name}")
                        continue
                        
                    print(f"DEBUG: Macro data type: {type(macro_data).__name__}")
                    # Convert controller macro format to our format if needed
                    if not isinstance(macro_data, dict):
                        print("DEBUG: Converting non-dict macro data to standard format")
                        macro_data = {
                            'name': macro_name,
                            'commands': macro_data if isinstance(macro_data, list) else [str(macro_data)],
                            'description': f"Synced from controller: {macro_name}",
                            'category': 'system',
                            'color': '#e6e6e6',
                            'hotkey': ''
                        }
                    
                    # Ensure commands is a list of strings
                    if 'commands' not in macro_data:
                        macro_data['commands'] = []
                    elif not isinstance(macro_data['commands'], list):
                        macro_data['commands'] = [str(macro_data['commands'])]
                    else:
                        macro_data['commands'] = [str(cmd) for cmd in macro_data['commands']]
                    
                    # Set default values for required fields
                    current_time = datetime.now().isoformat()
                    print(f"DEBUG: Setting default values for macro: {macro_name}")
                    macro_data.setdefault('name', macro_name)
                    macro_data.setdefault('description', f"Synced from controller: {macro_name}")
                    macro_data.setdefault('created_date', current_time)
                    macro_data.setdefault('modified_date', current_time)
                    macro_data.setdefault('category', 'system')
                    macro_data.setdefault('color', '#e6e6e6')
                    macro_data.setdefault('hotkey', '')
                    
                    # Ensure commands is a list of strings
                    if 'commands' not in macro_data:
                        macro_data['commands'] = []
                        print("DEBUG: No commands found in macro, initializing empty list")
                    elif not isinstance(macro_data['commands'], list):
                        macro_data['commands'] = [str(macro_data['commands'])]
                        print("DEBUG: Converted non-list commands to list")
                    else:
                        macro_data['commands'] = [str(cmd) for cmd in macro_data['commands']]
                    
                    print(f"DEBUG: Macro {macro_name} has {len(macro_data['commands'])} commands")
                    
                    # Create or update the macro
                    if macro_name in self.macros:
                        print(f"DEBUG: Updating existing macro: {macro_name}")
                        # Update existing macro
                        self.update_macro(
                            name=macro_name,
                            commands=macro_data['commands'],
                            description=macro_data.get('description', ''),
                            category=macro_data.get('category', 'system'),
                            color=macro_data.get('color', '#e6e6e6'),
                            hotkey=macro_data.get('hotkey', '')
                        )
                        action = "Updated"
                    else:
                        print(f"DEBUG: Creating new macro: {macro_name}")
                        # Create new macro
                        self.create_macro(
                            name=macro_name,
                            commands=macro_data['commands'],
                            description=macro_data.get('description', ''),
                            category=macro_data.get('category', 'system'),
                            color=macro_data.get('color', '#e6e6e6'),
                            hotkey=macro_data.get('hotkey', '')
                        )
                        action = "Created"
                    
                    synced_macros.add(macro_name)
                    print(f"{action} macro: {macro_name}")
                    
                except Exception as e:
                    print(f"ERROR: Failed to sync macro {macro_name}: {e}")
            
            print(f"DEBUG: Checking for local macros to remove (synced: {len(synced_macros)} macros)")
            # Remove any local macros that don't exist on the controller
            local_macros = set(self.macros.keys())
            macros_to_remove = local_macros - synced_macros
            print(f"DEBUG: Found {len(macros_to_remove)} local macros to remove")
            
            for macro_name in macros_to_remove:
                try:
                    print(f"DEBUG: Removing local macro not on controller: {macro_name}")
                    if self.delete_macro(macro_name):
                        print(f"Removed local macro not on controller: {macro_name}")
                    else:
                        print(f"WARNING: Failed to remove local macro: {macro_name}")
                except Exception as e:
                    print(f"ERROR: Failed to remove local macro {macro_name}: {e}")
            
            # Reload macros from disk to update our in-memory state
            print("DEBUG: Reloading macros from disk...")
            self.load_macros()
            print(f"DEBUG: Sync completed. Total macros: {len(self.macros)}")
            return True
            
        except Exception as e:
            import traceback
            error_msg = f"ERROR: Failed to sync macros from controller: {e}\n{traceback.format_exc()}"
            print(error_msg)
            return False
    
    def export_macro(self, name: str, filepath: str) -> bool:
        """Export a macro to a G-code file."""
        if name not in self.macros:
            return False
        
        try:
            macro = self.macros[name]
            with open(filepath, 'w') as f:
                f.write(f"; Macro: {macro.name}\n")
                f.write(f"; Description: {macro.description}\n")
                f.write(f"; Created: {macro.created_date}\n")
                f.write(f"; Category: {macro.category}\n")
                f.write(";\n")
                
                for command in macro.commands:
                    f.write(f"{command}\n")
            
            return True
        except Exception:
            return False
    
    def import_macro_from_file(self, name: str, filepath: str, description: str = "",
                              category: str = "user") -> bool:
        """Import a macro from a G-code file."""
        try:
            with open(filepath, 'r') as f:
                lines = f.readlines()
            
            commands = []
            for line in lines:
                line = line.strip()
                # Skip comments and empty lines
                if line and not line.startswith(';') and not line.startswith('('):
                    commands.append(line)
            
            return self.create_macro(name, commands, description, category)
        except Exception:
            return False
    
    def cleanup(self):
        """Clean up any resources used by the macro manager."""
        print(f"DEBUG: Cleaning up MacroManager for directory: {self.macros_directory}")
        # Clear any cached macros
        self.macros.clear()
    
    def _create_default_macros(self):
        """Create default system macros."""
        # Home All Axes
        self.create_macro(
            name="Home All",
            commands=["G28"],
            description="Home all axes to their limit switches",
            category="homing",
            color="#4CAF50"
        )
        
        # Zero All Coordinates
        self.create_macro(
            name="Zero All",
            commands=["G92 X0 Y0 Z0"],
            description="Set current position as zero for all axes",
            category="system",
            color="#2196F3"
        )
        
        # Safe Z Height
        self.create_macro(
            name="Safe Z",
            commands=["G91", "G0 Z5", "G90"],
            description="Move Z axis up 5mm to safe height",
            category="system",
            color="#FF9800"
        )
        
        # Spindle On
        self.create_macro(
            name="Spindle On",
            commands=["M3 S1000"],
            description="Turn on spindle at 1000 RPM",
            category="system",
            color="#9C27B0"
        )
        
        # Spindle Off
        self.create_macro(
            name="Spindle Off",
            commands=["M5"],
            description="Turn off spindle",
            category="system",
            color="#F44336"
        )
        
        # Tool Change Position
        self.create_macro(
            name="Tool Change",
            commands=[
                "G91",           # Relative mode
                "G0 Z5",         # Move Z up 5mm
                "G90",           # Absolute mode
                "G0 X0 Y0",      # Move to origin
                "M5",            # Stop spindle
                "M0",            # Program pause for tool change
            ],
            description="Move to tool change position and pause",
            category="tool_change",
            color="#607D8B"
        )
        
        # Probe Z
        self.create_macro(
            name="Probe Z",
            commands=[
                "G91",           # Relative mode
                "G38.2 Z-10 F100", # Probe down 10mm at 100mm/min
                "G92 Z0.5",      # Set Z to probe thickness (0.5mm)
                "G0 Z5",         # Retract 5mm
                "G90"            # Absolute mode
            ],
            description="Probe Z axis and set zero (assumes 0.5mm probe)",
            category="probing",
            color="#795548"
        )
        
        # Save all default macros
        self.save_all_macros()

class MacroRecorder:
    """Records user actions as macros."""
    
    def __init__(self):
        self.recording = False
        self.recorded_commands: List[str] = []
        self.start_time: Optional[datetime] = None
    
    def start_recording(self):
        """Start recording a macro."""
        self.recording = True
        self.recorded_commands.clear()
        self.start_time = datetime.now()
    
    def stop_recording(self) -> List[str]:
        """Stop recording and return the recorded commands."""
        self.recording = False
        commands = self.recorded_commands.copy()
        self.recorded_commands.clear()
        return commands
    
    def add_command(self, command: str):
        """Add a command to the recording."""
        if self.recording:
            self.recorded_commands.append(command)
    
    def is_recording(self) -> bool:
        """Check if currently recording."""
        return self.recording
    
    def get_recorded_commands(self) -> List[str]:
        """Get the currently recorded commands."""
        return self.recorded_commands.copy()

class MacroExecutor:
    """Executes macros with proper timing and error handling."""
    
    def __init__(self, communicator):
        self.communicator = communicator
        self.executing = False
        self.current_macro: Optional[Macro] = None
        self.current_command_index = 0
        
        # Execution callbacks
        self.progress_callback: Optional[callable] = None
        self.completion_callback: Optional[callable] = None
        self.error_callback: Optional[callable] = None
    
    def set_callbacks(self, progress=None, completion=None, error=None):
        """Set callback functions for macro execution events."""
        if progress:
            self.progress_callback = progress
        if completion:
            self.completion_callback = completion
        if error:
            self.error_callback = error
    
    def execute_macro(self, macro: Macro, delay: float = 0.5) -> bool:
        """Execute a macro with specified delay between commands."""
        if self.executing:
            return False
        
        self.executing = True
        self.current_macro = macro
        self.current_command_index = 0
        
        try:
            for i, command in enumerate(macro.commands):
                if not self.executing:  # Check for cancellation
                    break
                
                self.current_command_index = i
                
                # Send command
                if not self.communicator.send_gcode(command):
                    if self.error_callback:
                        self.error_callback(f"Failed to send command: {command}")
                    return False
                
                # Update progress
                if self.progress_callback:
                    progress = (i + 1) / len(macro.commands) * 100
                    self.progress_callback(progress, command)
                
                # Wait between commands (except for last one)
                if i < len(macro.commands) - 1:
                    import time
                    time.sleep(delay)
            
            self.executing = False
            
            if self.completion_callback:
                self.completion_callback(macro.name)
            
            return True
            
        except Exception as e:
            self.executing = False
            if self.error_callback:
                self.error_callback(f"Macro execution error: {e}")
            return False
    
    def cancel_execution(self):
        """Cancel the current macro execution."""
        self.executing = False
    
    def is_executing(self) -> bool:
        """Check if a macro is currently executing."""
        return self.executing
    
    def get_execution_status(self) -> Dict[str, Any]:
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