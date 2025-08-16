#!/usr/bin/env python3
"""
Test script to isolate the editor highlighting issue.
"""

import sys
import os
import tkinter as tk
sys.path.insert(0, os.path.dirname(__file__))

from core.gcode_parser import GCodeParser
from gui.code_editor import CodeEditor

def test_editor_highlighting():
    """Test the editor highlighting functionality."""
    print("="*60)
    print("Testing Code Editor highlighting")
    print("="*60)
    
    # Create a simple Tkinter window
    root = tk.Tk()
    root.title("Editor Highlighting Test")
    root.geometry("800x600")
    
    # Create the code editor
    editor = CodeEditor(root)
    editor.pack(fill=tk.BOTH, expand=True)
    
    # Load the test file
    parser = GCodeParser()
    test_file = "test_debug.gcode"
    
    print(f"\n1. Loading file: {test_file}")
    if parser.load_file(test_file):
        print("   File loaded successfully")
        
        # Load into editor
        editor.load_gcode(parser)
        print("   File loaded into editor")
        
        # Print parser info
        print(f"   Total lines: {len(parser.lines)}")
        executable_lines = parser.get_executable_lines()
        print(f"   Executable lines: {len(executable_lines)}")
        
        # Test highlighting different lines
        test_lines = [2, 3, 4, 5, 6]  # First few executable lines
        
        def test_highlight_sequence():
            """Test highlighting sequence."""
            if not test_lines:
                print("\n   All highlighting tests completed")
                root.after(2000, root.quit)  # Close after 2 seconds
                return
                
            line_num = test_lines.pop(0)
            print(f"\n   Testing highlight for line {line_num}")
            editor.highlight_current_line(line_num)
            
            # Schedule next test
            root.after(1500, test_highlight_sequence)  # Wait 1.5 seconds between tests
        
        # Start the highlighting test sequence after a short delay
        root.after(1000, test_highlight_sequence)
        
        # Add a button to manually test highlighting
        button_frame = tk.Frame(root)
        button_frame.pack(side=tk.BOTTOM, fill=tk.X, padx=5, pady=5)
        
        def manual_highlight():
            line_num = int(entry.get()) if entry.get().isdigit() else 2
            print(f"Manual highlight test for line {line_num}")
            editor.highlight_current_line(line_num)
        
        tk.Label(button_frame, text="Line to highlight:").pack(side=tk.LEFT)
        entry = tk.Entry(button_frame, width=5)
        entry.pack(side=tk.LEFT, padx=5)
        entry.insert(0, "2")
        
        tk.Button(button_frame, text="Highlight", command=manual_highlight).pack(side=tk.LEFT, padx=5)
        tk.Button(button_frame, text="Close", command=root.quit).pack(side=tk.RIGHT, padx=5)
        
        print("\n   Starting GUI test...")
        print("   Watch the editor for line highlighting")
        print("   You can also manually test by entering a line number and clicking 'Highlight'")
        
        # Start the GUI
        root.mainloop()
        
    else:
        print("   Failed to load file")
        root.destroy()

if __name__ == "__main__":
    test_editor_highlighting()