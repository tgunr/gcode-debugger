#!/usr/bin/env python3
"""
Tkinter Diagnostic Tool

This script helps diagnose Tkinter and display issues.
"""

import sys
import os
import platform
import tkinter as tk
from tkinter import ttk

def check_environment():
    """Check Python and system environment."""
    print("\n" + "="*80)
    print("ENVIRONMENT INFORMATION")
    print("="*80)
    print(f"Python: {sys.version}")
    print(f"Platform: {platform.platform()}")
    print(f"System: {platform.system()}" 
          f" {platform.release()} ({platform.version()})")
    print(f"Machine: {platform.machine()}")
    print(f"Processor: {platform.processor()}")
    
    # Check if running in a virtual environment
    print(f"\nVirtual Environment:")
    print(f"  sys.prefix: {sys.prefix}")
    print(f"  sys.base_prefix: {sys.base_prefix}")
    print(f"  Virtual Env: {hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.prefix != sys.base_prefix)}")
    
    # Check display environment
    print("\nDisplay Environment:")
    print(f"  DISPLAY: {os.environ.get('DISPLAY', 'Not set')}")
    print(f"  XAUTHORITY: {os.environ.get('XAUTHORITY', 'Not set')}")
    print(f"  XDG_SESSION_TYPE: {os.environ.get('XDG_SESSION_TYPE', 'Not set')}")
    print(f"  WAYLAND_DISPLAY: {os.environ.get('WAYLAND_DISPLAY', 'Not set')}")
    print(f"  XDG_CURRENT_DESKTOP: {os.environ.get('XDG_CURRENT_DESKTOP', 'Not set')}")

def check_tkinter():
    """Check Tkinter installation and display backend."""
    print("\n" + "="*80)
    print("TKINTER INFORMATION")
    print("="*80)
    
    # Basic Tkinter info
    print(f"Tkinter version: {tk.TkVersion}")
    print(f"Tcl/Tk version: {tk.Tcl().eval('info patchlevel')}")
    
    # Try to create a basic window
    print("\nTesting basic Tkinter window...")
    try:
        root = tk.Tk()
        root.withdraw()  # Don't show the window yet
        
        # Get window manager info
        print(f"Window manager: {root.tk.call('tk', 'windowingsystem')}")
        print(f"Tk window ID: {root.winfo_id()}")
        
        # Check screen info
        print(f"Screen dimensions: {root.winfo_screenwidth()}x{root.winfo_screenheight()}")
        print(f"Screen DPI: {root.winfo_fpixels('1i')}")
        
        # Try to display a simple window
        test_window = tk.Toplevel(root)
        test_window.title("Tkinter Test Window")
        
        # Add some widgets
        label = ttk.Label(test_window, text="Tkinter is working!")
        label.pack(padx=20, pady=20)
        
        button = ttk.Button(test_window, text="Close", command=test_window.destroy)
        button.pack(pady=(0, 20))
        
        # Force window to be visible
        test_window.update_idletasks()
        test_window.deiconify()
        test_window.lift()
        test_window.focus_force()
        
        print("Test window should be visible now")
        print("Close the test window to continue...")
        
        # Wait for the window to be closed
        test_window.wait_window()
        print("Test window closed")
        
        root.destroy()
        return True
        
    except Exception as e:
        print(f"ERROR creating Tkinter window: {e}")
        import traceback
        traceback.print_exc()
        return False

def check_imports():
    """Check if required modules can be imported."""
    print("\n" + "="*80)
    print("MODULE IMPORTS")
    print("="*80)
    
    modules = [
        'PIL',
        'PIL.Image',
        'PIL.ImageTk',
        'websocket',
        'requests',
        'numpy',
        'matplotlib',
        'ttkthemes',
        'pygments',
        'pyperclip'
    ]
    
    for module in modules:
        try:
            __import__(module.split('.')[0])
            print(f"✓ {module}")
        except ImportError:
            print(f"✗ {module} (Not found)")
        except Exception as e:
            print(f"✗ {module} (Error: {str(e)})")

def main():
    """Run all diagnostic checks."""
    print("Tkinter Diagnostic Tool")
    print("======================")
    
    check_environment()
    
    if not check_tkinter():
        print("\n" + "!"*80)
        print("WARNING: Basic Tkinter test failed!")
        print("The application may not work correctly.")
        print("!"*80 + "\n")
    
    check_imports()
    
    print("\nDiagnostics complete!")

if __name__ == "__main__":
    main()
