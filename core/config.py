#!/usr/bin/env python3
"""
Configuration Manager for G-code Debugger

Handles loading and saving of application settings.
"""

import os
import json
from typing import Dict, Any, Optional
from pathlib import Path

class ConfigManager:
    """Manages application configuration settings."""
    
    def __init__(self, config_dir: Optional[str] = None):
        """Initialize the configuration manager.
        
        Args:
            config_dir: Directory to store configuration files. If None, uses a default location.
        """
        # Default configuration values
        self._defaults = {
            "general": {
                "theme": "light",
                "recent_files": [],
                "max_recent_files": 10,
            },
            "connection": {
                "host": "bbctrl.polymicro.net",
                "port": 80,
                "auto_connect": True,
                "auto_reconnect": True,
                "reconnect_interval": 5,
                "timeout": 10,
            },
            "paths": {
                "external_macros": os.path.join(os.path.expanduser("~"), "Documents", "BBCtrl", "Macros"),
                "local_macros": os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "local_macros"),
                "last_file_dir": os.path.expanduser("~"),
                "last_export_dir": os.path.expanduser("~"),
            },
            "editor": {
                "font_family": "Courier",
                "font_size": 12,
                "tab_size": 4,
                "show_line_numbers": True,
                "highlight_current_line": True,
                "auto_indent": True,
                "word_wrap": False,
                "show_whitespace": False,
            },
            "macro": {
                "default_category": "user",
                "default_color": "#e6e6e6",
                "auto_save": True,
                "confirm_delete": True,
                "categories": ["system", "user", "homing", "tool_change", "probing", "custom"],
            },
            "debugger": {
                "auto_continue_on_error": False,
                "break_on_error": True,
                "break_on_warning": False,
                "max_history": 1000,
                "show_line_numbers": True,
            },
            "ui": {
                "window_width": 1400,
                "window_height": 900,
                "window_maximized": False,
                "panel_sizes": {
                    "left_panel": 250,
                    "right_panel": 300,
                    "bottom_panel": 200,
                },
            },
        }
        
        # Determine config directory
        if config_dir is None:
            # Use platform-appropriate config directory
            if os.name == 'nt':  # Windows
                app_data = os.environ.get('APPDATA', os.path.expanduser('~'))
                self.config_dir = os.path.join(app_data, 'Buildbotics', 'GCodeDebugger')
            else:  # macOS and Linux
                config_home = os.environ.get('XDG_CONFIG_HOME', os.path.expanduser('~/.config'))
                self.config_dir = os.path.join(config_home, 'buildbotics', 'gcode-debugger')
        else:
            self.config_dir = config_dir
            
        # Ensure config directory exists
        os.makedirs(self.config_dir, exist_ok=True)
        
        # Config file path
        self.config_file = os.path.join(self.config_dir, 'config.json')
        
        # Load existing config or create default
        self.config = self._load_config()
        
        # Ensure required directories exist
        self._ensure_directories()
    
    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from file or create default if it doesn't exist."""
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r') as f:
                    loaded_config = json.load(f)
                return self._merge_configs(self._defaults, loaded_config)
            except (json.JSONDecodeError, IOError) as e:
                print(f"Error loading config file: {e}. Using default configuration.")
                return self._defaults.copy()
        else:
            return self._defaults.copy()
    
    def _merge_configs(self, default: Dict[str, Any], loaded: Dict[str, Any]) -> Dict[str, Any]:
        """Recursively merge loaded config with defaults."""
        result = default.copy()
        for key, value in loaded.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self._merge_configs(result[key], value)
            else:
                result[key] = value
        return result
    
    def _ensure_directories(self) -> None:
        """Ensure all configured directories exist."""
        # Ensure external macros directory exists
        macros_dir = self.get('paths/external_macros')
        if macros_dir and not os.path.exists(macros_dir):
            try:
                os.makedirs(macros_dir, exist_ok=True)
            except OSError as e:
                print(f"Error creating macros directory '{macros_dir}': {e}")
        
        # Ensure local macros directory exists
        local_macros_dir = self.get('paths/local_macros')
        if local_macros_dir and not os.path.exists(local_macros_dir):
            try:
                os.makedirs(local_macros_dir, exist_ok=True)
            except OSError as e:
                print(f"Error creating local macros directory '{local_macros_dir}': {e}")
    
    def save(self) -> bool:
        """Save configuration to file."""
        try:
            # Create config directory if it doesn't exist
            os.makedirs(os.path.dirname(self.config_file), exist_ok=True)
            
            with open(self.config_file, 'w') as f:
                json.dump(self.config, f, indent=4, sort_keys=True)
            return True
        except (IOError, OSError) as e:
            print(f"Error saving config file: {e}")
            return False
    
    def get(self, key_path: str, default: Any = None) -> Any:
        """Get a configuration value by dot notation path."""
        keys = key_path.split('.')
        value = self.config
        
        try:
            for key in keys:
                value = value[key]
            return value
        except (KeyError, TypeError):
            return default
    
    def set(self, key_path: str, value: Any, save: bool = True) -> bool:
        """Set a configuration value by dot notation path."""
        keys = key_path.split('.')
        config = self.config
        
        try:
            # Navigate to the parent of the target key
            for key in keys[:-1]:
                if key not in config or not isinstance(config[key], dict):
                    config[key] = {}
                config = config[key]
            
            # Set the value
            config[keys[-1]] = value
            
            # Save if requested
            if save:
                return self.save()
            return True
            
        except (KeyError, TypeError) as e:
            print(f"Error setting config value '{key_path}': {e}")
            return False
    
    def add_recent_file(self, file_path: str) -> None:
        """Add a file to the recent files list."""
        recent_files = self.get('general.recent_files', [])
        
        # Remove if already in list
        if file_path in recent_files:
            recent_files.remove(file_path)
        
        # Add to beginning of list
        recent_files.insert(0, file_path)
        
        # Trim to max length
        max_files = self.get('general.max_recent_files', 10)
        if len(recent_files) > max_files:
            recent_files = recent_files[:max_files]
        
        # Save updated list
        self.set('general.recent_files', recent_files)
    
    def get_external_macros_dir(self) -> str:
        """Get the external macros directory, ensuring it exists."""
        macros_dir = self.get('paths.external_macros')
        if not os.path.exists(macros_dir):
            try:
                os.makedirs(macros_dir, exist_ok=True)
            except OSError as e:
                print(f"Error creating external macros directory: {e}")
        return macros_dir


# Global configuration instance
config = ConfigManager()

def get_config() -> ConfigManager:
    """Get the global configuration instance."""
    return config
