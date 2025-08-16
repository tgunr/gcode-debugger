#!/usr/bin/env python3
"""
Test script to verify GUI MDI functionality
"""

import sys
import os
import time
import tkinter as tk

# --------------------------------------------------------------------------- #
# Guard: Skip GUI tests gracefully when Tk cannot be initialized (headless CI)
# --------------------------------------------------------------------------- #
def _can_init_tk() -> bool:
    """Return True if a Tk root window can be created (i.e., a display is available)."""
    try:
        root = tk.Tk()
        root.withdraw()
        root.destroy()
        return True
    except Exception:
        return False


# When running in environments without a display (e.g., GitHub Actions),
# attempting to create the first Tk() instance segfaults.  Probe availability
# early and skip the whole module if Tk cannot start.
if not _can_init_tk():  # pragma: no cover
    import pytest

    pytest.skip(
        "Tkinter GUI not available (likely headless CI); skipping GUI tests.",
        allow_module_level=True,
    )

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