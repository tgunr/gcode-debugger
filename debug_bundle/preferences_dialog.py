#!/usr/bin/env python3
"""
Preferences Dialog for G-code Debugger

Allows users to configure application settings.
"""

import os
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from typing import Dict, Any, Callable, Optional, List

class PreferencesDialog:
    """Dialog for editing application preferences."""
    
    def __init__(self, parent, config, on_save: Optional[Callable[[], None]] = None):
        """Initialize the preferences dialog.
        
        Args:
            parent: Parent window
            config: ConfigManager instance
            on_save: Optional callback to call after saving preferences
        """
        self.config = config
        self.on_save = on_save
        
        # Create dialog window
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("Preferences")
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        # Set window size and position
        self.dialog.geometry("600x500")
        self.dialog.minsize(500, 400)
        
        # Center the dialog on screen
        self.dialog.update_idletasks()
        width = self.dialog.winfo_width()
        height = self.dialog.winfo_height()
        x = (self.dialog.winfo_screenwidth() // 2) - (width // 2)
        y = (self.dialog.winfo_screenheight() // 2) - (height // 2)
        self.dialog.geometry(f"{width}x{height}+{x}+{y}")
        
        # Store values from config
        self.values = {
            'paths.external_macros': tk.StringVar(value=self.config.get('paths.external_macros', '')),
            'editor.font_family': tk.StringVar(value=self.config.get('editor.font_family', 'Courier')),
            'editor.font_size': tk.IntVar(value=self.config.get('editor.font_size', 12)),
            'editor.tab_size': tk.IntVar(value=self.config.get('editor.tab_size', 4)),
            'editor.show_line_numbers': tk.BooleanVar(value=self.config.get('editor.show_line_numbers', True)),
            'connection.host': tk.StringVar(value=self.config.get('connection.host', 'bbctrl.polymicro.net')),
            'connection.port': tk.IntVar(value=self.config.get('connection.port', 80)),
            'general.theme': tk.StringVar(value=self.config.get('general.theme', 'light')),
        }
        
        # Setup UI
        self._setup_ui()
        
        # Bind window close event
        self.dialog.protocol("WM_DELETE_WINDOW", self._on_cancel)
    
    def _setup_ui(self):
        """Setup the preferences dialog UI."""
        # Create main container with padding
        main_frame = ttk.Frame(self.dialog, padding="10 10 10 10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Create notebook for preference categories
        notebook = ttk.Notebook(main_frame)
        notebook.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Add preference tabs
        self._add_general_tab(notebook)
        self._add_editor_tab(notebook)
        self._add_connection_tab(notebook)
        self._add_paths_tab(notebook)
        
        # Add buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=(10, 0))
        
        ttk.Button(
            button_frame, 
            text="Save", 
            command=self._on_save,
            style="Accent.TButton"
        ).pack(side=tk.RIGHT, padx=5)
        
        ttk.Button(
            button_frame, 
            text="Cancel", 
            command=self._on_cancel
        ).pack(side=tk.RIGHT, padx=5)
        
        # Make buttons expand to fill space
        button_frame.columnconfigure(0, weight=1)
    
    def _add_general_tab(self, notebook):
        """Add the General preferences tab."""
        frame = ttk.Frame(notebook, padding=10)
        notebook.add(frame, text="General")
        
        row = 0
        
        # Theme selection
        ttk.Label(frame, text="Theme:").grid(row=row, column=0, sticky=tk.W, pady=2)
        theme_combo = ttk.Combobox(
            frame,
            textvariable=self.values['general.theme'],
            values=["light", "dark", "system"],
            state="readonly",
            width=20
        )
        theme_combo.grid(row=row, column=1, sticky=tk.W, pady=2, padx=5)
        row += 1
        
        # Add padding to all children
        for child in frame.winfo_children():
            child.grid_configure(padx=5, pady=2)
    
    def _add_editor_tab(self, notebook):
        """Add the Editor preferences tab."""
        frame = ttk.Frame(notebook, padding=10)
        notebook.add(frame, text="Editor")
        
        row = 0
        
        # Font family
        ttk.Label(frame, text="Font Family:").grid(row=row, column=0, sticky=tk.W, pady=2)
        font_family = ttk.Combobox(
            frame,
            textvariable=self.values['editor.font_family'],
            values=["Courier", "Consolas", "Monaco", "Menlo", "Source Code Pro", "DejaVu Sans Mono"],
            width=20
        )
        font_family.grid(row=row, column=1, sticky=tk.W, pady=2, padx=5)
        row += 1
        
        # Font size
        ttk.Label(frame, text="Font Size:").grid(row=row, column=0, sticky=tk.W, pady=2)
        ttk.Spinbox(
            frame,
            from_=8,
            to=32,
            textvariable=self.values['editor.font_size'],
            width=5
        ).grid(row=row, column=1, sticky=tk.W, pady=2, padx=5)
        row += 1
        
        # Tab size
        ttk.Label(frame, text="Tab Size:").grid(row=row, column=0, sticky=tk.W, pady=2)
        ttk.Spinbox(
            frame,
            from_=1,
            to=8,
            textvariable=self.values['editor.tab_size'],
            width=5
        ).grid(row=row, column=1, sticky=tk.W, pady=2, padx=5)
        row += 1
        
        # Show line numbers
        ttk.Checkbutton(
            frame,
            text="Show Line Numbers",
            variable=self.values['editor.show_line_numbers']
        ).grid(row=row, column=0, columnspan=2, sticky=tk.W, pady=2)
        row += 1
        
        # Add padding to all children
        for child in frame.winfo_children():
            child.grid_configure(padx=5, pady=2)
    
    def _add_connection_tab(self, notebook):
        """Add the Connection preferences tab."""
        frame = ttk.Frame(notebook, padding=10)
        notebook.add(frame, text="Connection")
        
        row = 0
        
        # Host
        ttk.Label(frame, text="Host:").grid(row=row, column=0, sticky=tk.W, pady=2)
        ttk.Entry(
            frame,
            textvariable=self.values['connection.host'],
            width=25
        ).grid(row=row, column=1, sticky=tk.W, pady=2, padx=5)
        row += 1
        
        # Port
        ttk.Label(frame, text="Port:").grid(row=row, column=0, sticky=tk.W, pady=2)
        ttk.Spinbox(
            frame,
            from_=1,
            to=65535,
            textvariable=self.values['connection.port'],
            width=8
        ).grid(row=row, column=1, sticky=tk.W, pady=2, padx=5)
        row += 1
        
        # Add padding to all children
        for child in frame.winfo_children():
            child.grid_configure(padx=5, pady=2)
    
    def _add_paths_tab(self, notebook):
        """Add the Paths preferences tab."""
        frame = ttk.Frame(notebook, padding=10)
        notebook.add(frame, text="Paths")
        
        # Configure grid weights
        frame.columnconfigure(1, weight=1)
        
        row = 0
        
        # External Macros Directory
        ttk.Label(frame, text="External Macros:").grid(row=row, column=0, sticky=tk.W, pady=5)
        
        # Create a frame for the path entry and browse button
        path_frame = ttk.Frame(frame)
        path_frame.grid(row=row, column=1, sticky=tk.EW, pady=5)
        path_frame.columnconfigure(0, weight=1)  # Make entry expand
        
        # Path entry
        entry = ttk.Entry(
            path_frame,
            textvariable=self.values['paths.external_macros']
        )
        entry.grid(row=0, column=0, sticky=tk.EW, padx=(0, 5))
        
        # Browse button
        ttk.Button(
            path_frame,
            text="Browse...",
            command=self._browse_external_macros_dir,
            width=10
        ).grid(row=0, column=1, sticky=tk.E)
        
        # Add help text
        ttk.Label(
            frame, 
            text="Location where external macros are stored",
            font=('TkDefaultFont', 9, 'italic'),
            foreground='gray50'
        ).grid(row=row+1, column=1, sticky=tk.W, pady=(0, 10))
        
        # Add padding to all direct children of the main frame
        for child in frame.winfo_children():
            child.grid_configure(padx=5, pady=2)
    
    def _browse_external_macros_dir(self):
        """Open a directory selection dialog for the external macros directory."""
        try:
            initial_dir = self.values['paths.external_macros'].get()
            
            # If the current path doesn't exist, use the user's home directory
            if not initial_dir or not os.path.exists(initial_dir):
                initial_dir = os.path.expanduser("~")
            
            # Ensure initial_dir is a directory and exists
            if not os.path.isdir(initial_dir):
                initial_dir = os.path.dirname(initial_dir) or os.path.expanduser("~")
                
            dir_path = filedialog.askdirectory(
                title="Select External Macros Directory",
                mustexist=True,
                initialdir=initial_dir
            )
            
            if dir_path:
                # Convert to absolute path and normalize
                dir_path = os.path.abspath(dir_path)
                print(f"DEBUG: Selected directory: {dir_path}")
                self.values['paths.external_macros'].set(dir_path)
                
        except Exception as e:
            print(f"ERROR: Failed to select directory: {str(e)}")
            messagebox.showerror("Error", f"Failed to select directory: {str(e)}")
    
    def _on_save(self):
        """Handle save button click."""
        try:
            # Save all values to config
            for key, var in self.values.items():
                self.config.set(key, var.get(), save=False)
            
            # Save config to file
            if self.config.save():
                messagebox.showinfo("Preferences", "Preferences saved successfully.")
                
                # Call on_save callback if provided
                if self.on_save:
                    self.on_save()
                
                # Close the dialog
                self.dialog.destroy()
            else:
                messagebox.showerror("Error", "Failed to save preferences.")
                
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save preferences: {str(e)}")
    
    def _on_cancel(self):
        """Handle cancel button click or window close."""
        self.dialog.destroy()
    
    def show(self):
        """Show the preferences dialog."""
        self.dialog.wait_window()
