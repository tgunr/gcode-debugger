#!/usr/bin/env python3
"""
Test script to verify GUI MDI functionality
"""

import sys
import os
import time
import tkinter as tk

# Add the current directory to Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

from gui.main_window import MainWindow

def test_gui_mdi():
    """Test GUI MDI functionality"""
    print("Testing GUI MDI functionality...")
    
    # Create the main window
    app = MainWindow()
    
    # Wait a moment for initialization
    app.root.after(2000, lambda: test_mdi_command(app))
    
    # Start the GUI
    app.run()

def test_mdi_command(app):
    """Test sending an MDI command through the GUI"""
    print("Testing MDI command through GUI...")
    
    # Test sending a command
    test_command = "G0 Z-100"
    print(f"Sending command: {test_command}")
    
    if app.send_gcode_command(test_command):
        print("✓ Command sent successfully through GUI!")
    else:
        print("✗ Failed to send command through GUI")
    
    # Close the application after test
    app.root.after(3000, app.exit_application)

if __name__ == "__main__":
    test_gui_mdi()