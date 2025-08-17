#!/usr/bin/env python3
"""
Test script to verify status display colors work correctly.
"""

import tkinter as tk
from tkinter import ttk
import time

def test_status_colors():
    """Test the status display color functionality."""
    
    # Create a simple test window
    root = tk.Tk()
    root.title("Status Color Test")
    root.geometry("400x200")
    
    # Create connection status variable and label
    connection_status = tk.StringVar()
    connection_status_label = ttk.Label(root, textvariable=connection_status, font=("Arial", 12, "bold"))
    connection_status_label.pack(pady=20)
    
    # Create status text label
    status_text_label = tk.Label(root, text="Connection Status:", font=("Arial", 10))
    status_text_label.pack(pady=5)
    
    def on_connection_status_change(*args):
        """Update label color based on current connection status."""
        status = connection_status.get().lower()
        if status == "connected":
            connection_status_label.configure(foreground="#00cc00")  # bright green
            print("Status changed to Connected - should be bright green")
        else:
            connection_status_label.configure(foreground="#ff0000")  # bright red
            print("Status changed to Not Connected - should be bright red")
    
    # Set up the trace callback
    connection_status.trace_add("write", on_connection_status_change)
    
    # Create buttons to test the color changes
    def set_connected():
        connection_status.set("Connected")
    
    def set_disconnected():
        connection_status.set("Not Connected")
    
    button_frame = tk.Frame(root)
    button_frame.pack(pady=20)
    
    connect_btn = tk.Button(button_frame, text="Set Connected", command=set_connected, bg="lightgreen")
    connect_btn.pack(side=tk.LEFT, padx=10)
    
    disconnect_btn = tk.Button(button_frame, text="Set Disconnected", command=set_disconnected, bg="lightcoral")
    disconnect_btn.pack(side=tk.LEFT, padx=10)
    
    # Set initial status
    connection_status.set("Not Connected")
    
    # Add instructions
    instructions = tk.Label(root, text="Click buttons to test color changes.\nConnected should be bright green, Not Connected should be bright red.", 
                          font=("Arial", 9), justify=tk.CENTER)
    instructions.pack(pady=10)
    
    print("Starting status color test...")
    print("Connected status should show in bright green (#00cc00)")
    print("Not Connected status should show in bright red (#ff0000)")
    
    root.mainloop()

if __name__ == "__main__":
    test_status_colors()