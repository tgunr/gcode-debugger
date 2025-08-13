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

def sync_macros_on_startup(controller_url: str, macros_path: str) -> None:
    """Sync macros on application startup."""
    try:
        # Create communicator instance
        communicator = BBCtrlCommunicator(host=controller_url)
        
        # Attempt to connect
        if communicator.connect_websocket():
            print("Successfully connected to controller for sync")
            
            # Create macro manager with specified path
            macro_manager = MacroManager(macros_directory=macros_path)
            
            # Perform sync
            if macro_manager.sync_from_controller(communicator):
                print("Macro synchronization completed successfully")
            else:
                print("Macro synchronization failed")
            
            # Clean up
            communicator.close()
        else:
            print("Failed to connect to controller for sync")
            
    except Exception as e:
        print(f"Error during startup macro sync: {str(e)}")
        
def load_preferences() -> dict:
    """Load application preferences from configuration."""
    config = get_config()
    return {
        "controller_url": config.get("connection.host", "localhost"),
        "macros_path": config.get("paths.external_macros", "macros")
    }

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

def main():
    """Main application entry point."""
    import argparse
    parser = argparse.ArgumentParser(description="G-Code Debugger for Buildbotics Controller")
    parser.add_argument('--host', type=str, help='The hostname or IP address of the Buildbotics controller.')
    args = parser.parse_args()

    print("G-Code Debugger v1.0.0")
    print("For Buildbotics Controller")
    print("-" * 30)
    
    # Check dependencies
    if not check_dependencies():
        sys.exit(1)
    
    try:
        print("\nCreating MainWindow instance...")
        # Create the main application window
        app = MainWindow(host=args.host)
        print("MainWindow created successfully")
        print("MainWindow root window ID:", app.root.winfo_id())
        
        # Make sure the window is visible
        app.root.deiconify()
        app.root.lift()
        app.root.focus_force()
        
        # Handle application close
        def on_closing():
            if messagebox.askokcancel("Quit", "Do you want to quit the G-Code Debugger?"):
                app.exit_application()
        
        app.root.protocol("WM_DELETE_WINDOW", on_closing)
        
        # Force an update of all pending GUI operations
        app.root.update()
        
        print("Starting main event loop...")
        app.run()
        print("Main event loop ended")
        
    except KeyboardInterrupt:
        print("\nApplication interrupted by user.")
        sys.exit(0)
    except Exception as e:
        print(f"Fatal error: {e}")
        import traceback
        traceback.print_exc()
        
        # Show error dialog
        messagebox.showerror(
            "Fatal Error", 
            f"The application encountered a fatal error:\n\n{e}\n\nCheck the console for details."
        )
        
        sys.exit(1)
    finally:
        # Make sure to clean up properly
        if 'app' in locals():
            app.exit_application()

if __name__ == "__main__":
    preferences = load_preferences()
    sync_macros_on_startup(preferences["controller_url"], preferences["macros_path"])
    main()