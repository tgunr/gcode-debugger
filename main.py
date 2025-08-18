#!/usr/bin/env python3
print("main.py: script started")
"""
G-Code Debugger for Buildbotics Controller

Main entry point for the G-code debugging application.
"""

import sys
import os
import tkinter as tk
from tkinter import messagebox
from core.config import get_config
from core.communication import BBCtrlCommunicator
from core.macro_manager import MacroManager

# Add the current directory to Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

try:
    # Import using direct imports from current directory
    from gui.main_window import MainWindow
except ImportError as e:
    print(f"Import error: {e}")
    print("Please ensure all required dependencies are installed.")
    print("Run: pip install -r requirements.txt")
    sys.exit(1)

        

def check_dependencies():
    """Check if required dependencies are available."""
    missing = []
    
    try:
        import websocket
    except ImportError:
        missing.append("websocket-client")
    
    try:
        import requests
    except ImportError:
        missing.append("requests")
    
    if missing:
        print("Missing required dependencies:")
        for dep in missing:
            print(f"  - {dep}")
        print("\nPlease install them with:")
        print("pip install " + " ".join(missing))
        return False
    
    return True

def setup_communicator(host=None, port=None):
    """Set up and return a configured BBCtrlCommunicator instance."""
    from core.config import config
    
    # Get connection settings from config or use provided values
    host = host or config.get('connection.host', '10.1.1.111')
    port = port or config.get('connection.port', 80)
    
    print(f"Setting up communicator with host: {host}, port: {port}")
    
    # Initialize communicator
    communicator = BBCtrlCommunicator(host=host, port=port)
    
    # Set up callbacks
    def on_state_change(state):
        print(f"[STATE] {state}")
        
    def on_message(msg):
        print(f"[MESSAGE] {msg}")
        
    def on_error(error):
        print(f"[ERROR] {error}")
    
    communicator.set_callbacks(
        state_callback=on_state_change,
        message_callback=on_message,
        error_callback=on_error
    )
    
    return communicator

def main():
    """Main application entry point."""
    import argparse
    parser = argparse.ArgumentParser(description="G-Code Debugger for Buildbotics Controller")
    parser.add_argument('--host', type=str, help='The hostname or IP address of the Buildbotics controller.')
    parser.add_argument('--port', type=int, help='The port number of the Buildbotics controller.')
    args = parser.parse_args()

    print("G-Code Debugger v1.0.0")
    print("For Buildbotics Controller")
    print("-" * 30)
    
    # Check dependencies
    if not check_dependencies():
        sys.exit(1)
    
    try:
        # Create the main application window
        app = MainWindow(host=args.host)
        
        # Start the main event loop
        app.root.mainloop()
        
    except Exception as e:
        print(f"Fatal error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":    
    main()