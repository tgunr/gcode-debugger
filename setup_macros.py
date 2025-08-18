#!/usr/bin/env python3
"""
Script to set up the required macros directory structure.
"""
import os

def setup_macros():
    """Create the required macros directory structure."""
    # Base directories
    base_dirs = [
        'macros',
        'local_macros',
        os.path.expanduser('~/Documents/BBCtrl/Macros')
    ]
    
    # Subdirectories to create
    sub_dirs = [
        'Projects',
        'Subroutines',
        'Macros',
        '.meta'
    ]
    
    # Create base directories and subdirectories
    for base_dir in base_dirs:
        if not os.path.exists(base_dir):
            try:
                os.makedirs(base_dir)
                print(f"Created directory: {os.path.abspath(base_dir)}")
                
                # Create subdirectories
                for sub_dir in sub_dirs:
                    sub_path = os.path.join(base_dir, sub_dir)
                    os.makedirs(sub_path, exist_ok=True)
                    print(f"  - {sub_dir}")
                    
            except OSError as e:
                print(f"Error creating directory {base_dir}: {e}")
        else:
            print(f"Directory exists: {os.path.abspath(base_dir)}")
            
            # Ensure subdirectories exist
            for sub_dir in sub_dirs:
                sub_path = os.path.join(base_dir, sub_dir)
                os.makedirs(sub_path, exist_ok=True)
                if not os.path.exists(sub_path):
                    print(f"  - Created: {sub_dir}")

if __name__ == "__main__":
    print("Setting up macros directory structure...")
    setup_macros()
    print("Setup complete.")
