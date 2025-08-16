#!/usr/bin/env python3
"""
Simple Tkinter test script to verify basic GUI functionality.
"""
import tkinter as tk
from tkinter import messagebox

def main():
    print("Creating root window...")
    root = tk.Tk()
    root.title("Tkinter Test")
    root.geometry("400x300")
    
    # Add a label
    label = tk.Label(root, text="Tkinter is working!")
    label.pack(pady=20)
    
    # Add a button
    def on_click():
        messagebox.showinfo("Test", "Button clicked!")
    
    button = tk.Button(root, text="Click Me", command=on_click)
    button.pack(pady=10)
    
    # Center the window
    root.update_idletasks()
    width = root.winfo_width()
    height = root.winfo_height()
    x = (root.winfo_screenwidth() // 2) - (width // 2)
    y = (root.winfo_screenheight() // 2) - (height // 2)
    root.geometry(f'{width}x{height}+{x}+{y}')
    
    print("Starting mainloop...")
    root.mainloop()
    print("Mainloop ended")

if __name__ == "__main__":
    main()
