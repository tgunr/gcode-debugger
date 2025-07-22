#!/usr/bin/env python3
"""
Generate simple placeholder icons for the file browser.
"""
import tkinter as tk
from PIL import Image, ImageDraw, ImageTk
import os

def create_icon(name, color, size=(16, 16)):
    """Create a simple colored square icon."""
    img = Image.new('RGBA', size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    
    # Draw a rounded rectangle
    draw.rounded_rectangle(
        [1, 1, size[0]-2, size[1]-2],
        radius=2,
        fill=color,
        outline='#666666',
        width=1
    )
    
    # Save the image
    img.save(f"{name}.png", "PNG")
    print(f"Created {name}.png")

def main():
    """Generate all required icons."""
    # Create icons directory if it doesn't exist
    os.makedirs('icons', exist_ok=True)
    os.chdir('icons')
    
    # Generate icons
    create_icon('folder', '#FFD700')  # Gold color for folders
    create_icon('file', '#87CEEB')    # Light blue for regular files
    create_icon('macro', '#98FB98')   # Pale green for macro files
    
    print("Icons generated successfully!")

if __name__ == "__main__":
    main()
