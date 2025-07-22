#!/usr/bin/env python3
"""
Macro Panel for G-code Debugger

Provides macro management and execution interface for both local and external macros.
"""
import os
import tkinter as tk
from tkinter import ttk, messagebox, filedialog, simpledialog
from datetime import datetime
from typing import Optional
from PIL import Image, ImageTk
import logging
import threading
import time
import requests
import queue

# Set up logging
logging.basicConfig(level=logging.WARNING)  # Set to WARNING to reduce debug output
logger = logging.getLogger(__name__)

class MacroPanel(ttk.LabelFrame):
    """Panel for both local and external macro management and execution."""
    
    def __init__(self, parent, macro_manager, local_macro_manager, comm=None):
        super().__init__(parent, text="Macros")
        self.macro_manager = macro_manager  # External macros
        self.local_macro_manager = local_macro_manager  # Local macros
        self.comm = comm  # Communication interface
        self.selected_macro = None
        self.selected_local_macro = None
        self.current_tab = "local"  # Track which tab is active
        self.path_history = []  # For navigation history
        self.current_path = "Home"  # Current directory path
        self.setup_ui()
        self._refresh_macro_lists()
    
    def setup_ui(self):
        """Setup the tabbed macro panel UI."""
        # Create notebook for tabs
        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Local macros tab
        self.local_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.local_frame, text="📝 Local Macros")
        self._setup_local_macro_tab()
        
        # Controller files tab
        self.external_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.external_frame, text="📁 Controller Files")
        self._setup_external_macro_tab()
        
        # Bind tab change event
        self.notebook.bind("<<NotebookTabChanged>>", self._on_tab_changed)
    
    def _setup_local_macro_tab(self):
        """Setup the local macros tab."""
        # Local macro list frame
        list_frame = ttk.Frame(self.local_frame)
        list_frame.pack(fill=tk.X, pady=(5, 5), padx=5)
        
        # Local macro listbox with scrollbar
        self.local_macro_listbox = tk.Listbox(
            list_frame,
            height=10,  # Increased from 3 to 10 to show more macros
            font=("Arial", 8),
            selectmode=tk.SINGLE
        )
        self.local_macro_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        local_scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL)
        local_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.local_macro_listbox.config(yscrollcommand=local_scrollbar.set)
        local_scrollbar.config(command=self.local_macro_listbox.yview)
        
        # Bind events for local macros
        self.local_macro_listbox.bind('<<ListboxSelect>>', self._on_local_macro_select)
        self.local_macro_listbox.bind('<Double-Button-1>', self._on_view_local_macro_in_editor)
        
        # Local macro buttons frame
        local_btn_frame = ttk.Frame(self.local_frame)
        local_btn_frame.pack(fill=tk.X, padx=5, pady=(0, 5))
        
        # Row 1: Main action buttons
        local_main_frame = ttk.Frame(local_btn_frame)
        local_main_frame.pack(fill=tk.X, pady=(0, 2))
        
        self.local_execute_btn = ttk.Button(
            local_main_frame,
            text="▶️ Run",
            command=self._on_execute_local_macro,
            width=8
        )
        self.local_execute_btn.pack(side=tk.LEFT, padx=(0, 2))
        
        self.local_new_btn = ttk.Button(
            local_main_frame,
            text="➕ New",
            command=self._on_new_local_macro,
            width=8
        )
        self.local_new_btn.pack(side=tk.LEFT, padx=(0, 2))
        
        # Edit button removed - double-click macro to edit in debugger
        
        self.local_delete_btn = ttk.Button(
            local_main_frame,
            text="🗑️ Del",
            command=self._on_delete_local_macro,
            width=8,
            state=tk.DISABLED
        )
        self.local_delete_btn.pack(side=tk.LEFT)
        
        # Row 2: Secondary buttons
        local_sec_frame = ttk.Frame(local_btn_frame)
        local_sec_frame.pack(fill=tk.X)
        
        self.local_stop_btn = ttk.Button(
            local_sec_frame,
            text="⏹️ Stop",
            command=self._on_stop_local_macro,
            width=8,
            state=tk.DISABLED
        )
        self.local_stop_btn.pack(side=tk.LEFT, padx=(0, 2))
        
        self.local_import_btn = ttk.Button(
            local_sec_frame,
            text="📁 Import",
            command=self._on_import_local_macro,
            width=8
        )
        self.local_import_btn.pack(side=tk.LEFT, padx=(0, 2))
        
        self.local_export_btn = ttk.Button(
            local_sec_frame,
            text="💾 Export",
            command=self._on_export_local_macro,
            width=8,
            state=tk.DISABLED
        )
        self.local_export_btn.pack(side=tk.LEFT, padx=(0, 2))
        
        self.local_refresh_btn = ttk.Button(
            local_sec_frame,
            text="🔄",
            command=self._refresh_local_macro_list,
            width=4
        )
        self.local_refresh_btn.pack(side=tk.LEFT)
    
    def _setup_external_macro_tab(self):
        """Setup the controller files tab with a tree view of the file system."""
        print("DEBUG: Setting up external macro tab...")
        
        # Controller files frame
        self.external_files_frame = ttk.LabelFrame(self.external_frame, text="Controller Files", padding=5)
        self.external_files_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Configure grid weights
        self.external_files_frame.columnconfigure(0, weight=1)
        self.external_files_frame.rowconfigure(0, weight=1)
        
        # Create a frame for the treeview and scrollbars
        tree_frame = ttk.Frame(self.external_files_frame)
        tree_frame.grid(row=0, column=0, sticky='nsew')
        
        # Configure grid weights for the container
        tree_frame.columnconfigure(0, weight=1)
        tree_frame.rowconfigure(0, weight=1)
        
        print("DEBUG: Creating treeview...")
        # Create a treeview with columns matching the controller interface
        self.tree = ttk.Treeview(
            tree_frame,
            columns=('size', 'modified'),
            selectmode='browse',
            show='tree headings',  # Show both tree and column headers
            height=15
        )
        
        # Configure the treeview style
        style = ttk.Style()
        style.configure('Treeview', rowheight=25)  # Increase row height for better touch
        style.configure('Treeview.Heading', font=('Arial', 10, 'bold'))
        
        # Add scrollbars
        vsb = ttk.Scrollbar(tree_frame, orient='vertical', command=self.tree.yview)
        hsb = ttk.Scrollbar(tree_frame, orient='horizontal', command=self.tree.xview)
        self.tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
        
        # Grid the treeview and scrollbars
        self.tree.grid(row=0, column=0, sticky='nsew')
        vsb.grid(row=0, column=1, sticky='ns')
        hsb.grid(row=1, column=0, sticky='ew')
        
        # Configure treeview columns to match controller
        self.tree.column('#0', width=350, minwidth=200, stretch=tk.YES)
        self.tree.column('size', width=100, minwidth=80, stretch=tk.NO, anchor='e')
        self.tree.column('modified', width=150, minwidth=100, stretch=tk.NO, anchor='w')
        
        print("DEBUG: Setting up column headings...")
        # Add column headings to match controller
        self.tree.heading('#0', text='Name', anchor=tk.W)
        self.tree.heading('size', text='Size', anchor=tk.CENTER)
        self.tree.heading('modified', text='Date Modified', anchor=tk.W)
        
        # Create default icons for the treeview
        self.folder_icon = self._load_icon('folder')
        self.file_icon = self._load_icon('file')
        self.macro_icon = self._load_icon('macro')
        
        # Bind events for the treeview
        self.tree.bind('<Double-1>', self._on_tree_item_double_click)
        self.tree.bind('<<TreeviewSelect>>', self._on_tree_item_select)
        self.tree.bind('<Button-3>', self._on_tree_right_click)  # Right-click for context menu
        
        # Create context menu
        self.tree_menu = tk.Menu(self.tree, tearoff=0)
        self.tree_menu.add_command(label="Open", command=self._on_open_item)
        self.tree_menu.add_command(label="Edit", command=self._on_edit_item)
        self.tree_menu.add_separator()
        self.tree_menu.add_command(label="Delete", command=self._on_delete_item)
        self.tree_menu.add_command(label="Rename", command=self._on_rename_item)
        self.tree_menu.add_separator()
        self.tree_menu.add_command(label="Refresh", command=self._refresh_external_macro_list)
        self.tree.bind('<<TreeviewSelect>>', self._on_tree_item_select)
        
        # Add a right-click context menu
        self.tree_menu = tk.Menu(self.tree, tearoff=0)
        self.tree_menu.add_command(label="Open", command=self._on_open_item)
        self.tree_menu.add_command(label="Edit", command=self._on_edit_external_macro)
        self.tree_menu.add_separator()
        self.tree_menu.add_command(label="Delete", command=self._on_delete_external_macro)
        
        # Bind right-click event
        self.tree.bind('<Button-3>', self._on_tree_right_click)
        
        # Navigation history
        self.path_history = []
        self.current_path = 'Home'
        
        # Add a frame for navigation buttons
        nav_frame = ttk.Frame(self.external_files_frame)
        nav_frame.grid(row=1, column=0, sticky='ew', pady=(5, 0))
        
        # Navigation buttons
        self.back_btn = ttk.Button(
            nav_frame,
            text='⬅ Back',
            command=self._on_nav_back,
            width=8,
            state=tk.DISABLED
        )
        self.back_btn.pack(side=tk.LEFT, padx=(0, 5))
        
        self.forward_btn = ttk.Button(
            nav_frame,
            text='Forward ➡',
            command=self._on_nav_forward,
            width=8,
            state=tk.DISABLED
        )
        self.forward_btn.pack(side=tk.LEFT, padx=(0, 5))
        
        self.up_btn = ttk.Button(
            nav_frame,
            text='⬆ Up',
            command=self._on_nav_up,
            width=6
        )
        self.up_btn.pack(side=tk.LEFT, padx=(0, 5))
        
        # Current path label
        self.path_var = tk.StringVar(value=f"Path: {self.current_path}")
        path_label = ttk.Label(nav_frame, textvariable=self.path_var)
        path_label.pack(side=tk.LEFT, padx=10)
        
        # Controller files buttons frame
        external_btn_frame = ttk.Frame(self.external_frame)
        external_btn_frame.pack(fill=tk.X, padx=5, pady=(0, 5))
        
        # Initialize all UI elements before loading directory
        self._setup_external_buttons(external_btn_frame)
        
        # Load the root directory after UI is fully initialized
        self._load_directory(self.current_path)
        
    def _setup_external_buttons(self, parent_frame):
        """Initialize all external macro buttons in the specified parent frame."""
        # Row 1: Main action buttons
        external_main_frame = ttk.Frame(parent_frame)
        external_main_frame.pack(fill=tk.X, pady=(0, 2))
        
        # Row 2: Secondary action buttons
        external_secondary_frame = ttk.Frame(parent_frame)
        external_secondary_frame.pack(fill=tk.X, pady=(2, 0))
        
        # Execute button
        self.external_execute_btn = ttk.Button(
            external_main_frame,
            text="▶️ Run",
            command=self._on_execute_external_macro,
            width=8,
            state=tk.DISABLED  # Initially disabled until a macro is selected
        )
        self.external_execute_btn.pack(side=tk.LEFT, padx=(0, 2))
        
        # Stop button
        self.external_stop_btn = ttk.Button(
            external_main_frame,
            text="⏹️ Stop",
            command=self._on_stop_external_macro,
            width=8,
            state=tk.DISABLED  # Initially disabled until execution starts
        )
        self.external_stop_btn.pack(side=tk.LEFT, padx=(0, 2))
        
        # New button
        self.external_new_btn = ttk.Button(
            external_main_frame,
            text="➕ New",
            command=self._on_new_external_macro,
            width=8
        )
        self.external_new_btn.pack(side=tk.LEFT, padx=(0, 2))
        
        # Delete button
        self.external_delete_btn = ttk.Button(
            external_main_frame,
            text="🗑️ Del",
            command=self._on_delete_external_macro,
            width=8,
            state=tk.DISABLED  # Initially disabled until a macro is selected
        )
        self.external_delete_btn.pack(side=tk.LEFT, padx=(0, 2))
        
        # Import button
        self.external_import_btn = ttk.Button(
            external_secondary_frame,
            text="📥 Import",
            command=self._on_import_external_macro,
            width=8
        )
        self.external_import_btn.pack(side=tk.LEFT, padx=(0, 2))
        
        # Export button
        self.external_export_btn = ttk.Button(
            external_secondary_frame,
            text="📤 Export",
            command=self._on_export_external_macro,
            width=8,
            state=tk.DISABLED  # Initially disabled until a macro is selected
        )
        self.external_export_btn.pack(side=tk.LEFT, padx=(0, 2))
        
        # Refresh button
        self.external_refresh_btn = ttk.Button(
            external_secondary_frame,
            text="🔄",
            command=self._refresh_external_macro_list,
            width=4
        )
        self.external_refresh_btn.pack(side=tk.LEFT)
    
    def refresh_macro_lists(self):
        """Refresh both local and external macro lists."""
        self._refresh_local_macro_list()
        self._refresh_external_macro_list()
        
        # Update button states for the current tab
        if hasattr(self, 'current_tab'):
            if self.current_tab == "local":
                self._update_local_button_states()
            else:
                self._update_external_button_states()
    
    def _on_tab_changed(self, event):
        """Handle tab change event between local and external macros."""
        try:
            selected_tab = self.notebook.index(self.notebook.select())
            
            if selected_tab == 0:  # Local macros tab
                self.current_tab = "local"
                self._refresh_local_macro_list()
            else:  # External macros tab
                self.current_tab = "external"
                self._refresh_external_macro_list()
            
            # Update button states for the active tab
            if self.current_tab == "local":
                self._update_local_button_states()
            else:
                self._update_external_button_states()
                
        except Exception as e:
            print(f"Error handling tab change: {str(e)}")
    
    def _refresh_macro_lists(self):
        """Refresh both macro list displays."""
        self._refresh_local_macro_list()
        self._refresh_external_macro_list()
    
    def _refresh_local_macro_list(self):
        """Refresh the local macro list display."""
        self.local_macro_listbox.delete(0, tk.END)
        
        local_macros = self.local_macro_manager.get_all_local_macros()
        for macro in sorted(local_macros, key=lambda m: (m.category, m.name)):
            # Color code by category
            color_prefix = self._get_category_prefix(macro.category)
            display_text = f"{color_prefix} {macro.name}"
            if macro.description:
                display_text += f" - {macro.description[:25]}"
                if len(macro.description) > 25:
                    display_text += "..."
            
            self.local_macro_listbox.insert(tk.END, display_text)
        
        self._update_local_button_states()
    
    def _refresh_external_macro_list(self):
        """Refresh the list of files and directories from the controller."""
        print(f"\n{'='*80}")
        print("DEBUG: _refresh_external_macro_list()")
        print(f"Current tab: {self.current_tab}")
        print(f"Current path: {self.current_path}")
        print(f"Has comm: {hasattr(self, 'comm')}")
        
        if hasattr(self, 'comm'):
            print(f"comm is None: {self.comm is None}")
            if self.comm is not None:
                print(f"comm.connected: {getattr(self.comm, 'connected', 'N/A')}")
        
        # Check if we have a valid current_path
        if not self.current_path:
            print("WARNING: current_path is empty, defaulting to 'Home'")
            self.current_path = 'Home'
        
        print(f"Calling _load_directory('{self.current_path}')...")
        try:
            self._load_directory(self.current_path)
        except Exception as e:
            print(f"ERROR in _load_directory: {str(e)}")
            import traceback
            traceback.print_exc()
            
            # Try to show error in UI if possible
            if hasattr(self, 'tree') and hasattr(self, '_show_error_in_ui'):
                try:
                    # Clear any existing items
                    for item in self.tree.get_children():
                        self.tree.delete(item)
                    # Show error
                    self.tree.insert('', 'end', text=f"Error: {str(e)}", values=('', ''), tags=('error',))
                except Exception as ui_error:
                    print(f"ERROR showing error in UI: {str(ui_error)}")
    
    def _load_directory(self, path: str):
        """
        Load the contents of the specified directory into the treeview.
        
        Args:
            path: The directory path to load
        """
        print(f"\n{'='*80}")
        print(f"DEBUG: _load_directory('{path}')")
        print(f"Thread: {threading.current_thread().name}")
        print(f"PID: {os.getpid()}")
        print(f"Has comm: {hasattr(self, 'comm')}")
        print(f"Has tree: {hasattr(self, 'tree')}")
        print(f"Has after: {hasattr(self, 'after')}")
        
        # Ensure path is a string and not empty
        if not isinstance(path, str) or not path.strip():
            print(f"ERROR: Invalid path provided: {path}")
            return
            
        print(f"CWD: {os.getcwd()}")
        print(f"Has comm: {hasattr(self, 'comm')}")
        
        # Store the current path
        self.current_path = path
        print(f"DEBUG: Set current_path to: {self.current_path}")
        
        # Initialize path_history if it doesn't exist
        if not hasattr(self, 'path_history'):
            self.path_history = []
            
        # Add to navigation history if it's different from the last one
        if not self.path_history or (self.path_history and self.path_history[-1] != path):
            self.path_history.append(path)
            print(f"DEBUG: Added to path_history: {path}")
            
        # Update navigation buttons if the method exists
        if hasattr(self, '_update_navigation_buttons'):
            print("DEBUG: Updating navigation buttons")
            if hasattr(self, 'after') and callable(self.after):
                self.after(0, self._update_navigation_buttons)
            else:
                self._update_navigation_buttons()
                
        # Clear the treeview first
        clear_result = self._safe_clear_treeview()
        print(f"DEBUG: _safe_clear_treeview() returned: {clear_result}")
        if not clear_result:
            error_msg = "Failed to clear treeview before loading directory"
            print(f"ERROR: {error_msg}")
            if hasattr(self, 'after') and callable(self.after):
                self.after(0, lambda: self._show_error_in_ui(None, error_msg))
            else:
                self._show_error_in_ui(None, error_msg)
            return
            
        # Add a loading indicator
        loading_id = [None]  # Use a list to allow modification in nested functions
        
        def add_loading_indicator():
            """Add a loading indicator to the treeview."""
            try:
                print("DEBUG: Adding loading indicator to treeview")
                loading_id[0] = self.tree.insert('', 'end', text='Loading...', values=('', ''), tags=('loading',))
                self.tree.see(loading_id[0])  # Ensure the loading indicator is visible
                self.tree.update()
                print(f"DEBUG: Loading indicator added with ID: {loading_id[0]}")
            except Exception as e:
                print(f"ERROR adding loading indicator: {str(e)}")
                import traceback
                traceback.print_exc()
        
        # Add loading indicator in a thread-safe way
        if threading.current_thread() is threading.main_thread():
            add_loading_indicator()
        else:
            if hasattr(self, 'after') and callable(self.after):
                print("DEBUG: Scheduling loading indicator on main thread")
                self.after(0, add_loading_indicator)
        
        # Define a helper function to safely update the UI from any thread
        def safe_update_ui(callback, *args):
            """Safely execute a UI update on the main thread"""
            try:
                if threading.current_thread() is threading.main_thread():
                    # If we're already on the main thread, execute directly
                    return callback(*args)
                elif hasattr(self, 'after') and callable(self.after):
                    # Schedule on main thread - return None for async operation
                    self.after(0, lambda: safe_update_ui(callback, *args))
                    return None
                else:
                    print("WARNING: Cannot update UI - no valid after method")
                    return None
            except Exception as e:
                print(f"ERROR in safe_update_ui: {str(e)}")
                return None
                import traceback
                traceback.print_exc()
        
        # Define a function to update the UI with an error message
        def update_ui_with_error(message):
            """Update the UI to show an error message"""
            print(f"ERROR: {message}")
            
            def _show_error():
                try:
                    # Clear the treeview
                    self._safe_clear_treeview()
                    # Show error message
                    self.tree.insert('', 'end', text=f'Error: {message}', values=('', ''), tags=('error',))
                    # Configure error tag
                    self.tree.tag_configure('error', foreground='red')
                except Exception as e:
                    print(f"ERROR in update_ui_with_error: {str(e)}")
            
            safe_update_ui(_show_error)
        
        # Define the main directory loading function
        def load_directory():
            """Load directory contents and update the UI"""
            try:
                print(f"DEBUG: Loading directory: {path}")
                
                # Check if we have a communication object
                if not hasattr(self, 'comm') or self.comm is None:
                    update_ui_with_error("No communication interface available")
                    return
                
                # Get the directory listing
                try:
                    print(f"DEBUG: Requesting directory listing for: {path}")
                    listing = self.comm.list_directory(path)
                    print(f"DEBUG: Received listing: {listing}")
                    
                    if not isinstance(listing, (list, tuple)):
                        update_ui_with_error(f"Invalid response from controller: {type(listing).__name__}")
                        return
                    
                    # Update the UI with the directory contents
                    def update_ui():
                        try:
                            # Clear the treeview
                            if not self._safe_clear_treeview():
                                print("WARNING: Failed to clear treeview before update")
                            
                            # Add parent directory reference if not at root
                            if path != 'Home':
                                parent_path = '/'.join(path.split('/')[:-1]) if '/' in path else 'Home'
                                item_id = self.tree.insert(
                                    '', 'end',
                                    text='..',
                                    values=('', ''),
                                    tags=('directory', parent_path)
                                )
                                self.tree.item(item_id, image=self.folder_icon)
                            
                            # Add each item to the treeview
                            for item in listing:
                                try:
                                    name = item.get('name', 'unnamed')
                                    is_dir = item.get('is_dir', False)
                                    size = item.get('size', 0)
                                    modified = item.get('modified', 0)
                                    full_path = item.get('path', '')
                                    
                                    # Skip hidden files and directories
                                    if name.startswith('.'):
                                        continue
                                    
                                    # Format the size
                                    size_str = self._format_size(size) if not is_dir else ''
                                    
                                    # Format the modification time
                                    modified_str = ''
                                    if modified > 0:
                                        try:
                                            modified_str = datetime.fromtimestamp(modified).strftime('%Y-%m-%d %H:%M:%S')
                                        except:
                                            modified_str = str(modified)
                                    
                                    # Insert the item
                                    item_id = self.tree.insert(
                                        '', 'end',
                                        text=name,
                                        values=(size_str, modified_str),
                                        tags=('directory' if is_dir else 'file', full_path)
                                    )
                                    
                                    # Set the appropriate icon
                                    icon = self.folder_icon if is_dir else self.file_icon
                                    self.tree.item(item_id, image=icon)
                                    
                                except Exception as e:
                                    print(f"WARNING: Failed to add item to treeview: {str(e)}")
                                    import traceback
                                    traceback.print_exc()
                            
                            # Update button states
                            if hasattr(self, '_update_external_button_states'):
                                self._update_external_button_states()
                            
                            # Update navigation buttons
                            if hasattr(self, '_update_navigation_buttons'):
                                self._update_navigation_buttons()
                            
                        except Exception as e:
                            print(f"ERROR in update_ui: {str(e)}")
                            import traceback
                            traceback.print_exc()
                            update_ui_with_error(f"Failed to update UI: {str(e)}")
                    
                    # Update the UI on the main thread
                    safe_update_ui(update_ui)
                    
                except Exception as e:
                    error_msg = f"Failed to list directory: {str(e)}"
                    print(f"ERROR: {error_msg}")
                    import traceback
                    traceback.print_exc()
                    update_ui_with_error(error_msg)
                
            except Exception as e:
                error_msg = f"Unexpected error in load_directory: {str(e)}"
                print(f"CRITICAL: {error_msg}")
                import traceback
                traceback.print_exc()
                update_ui_with_error(error_msg)
        
        # Start loading the directory in a separate thread
        print("DEBUG: Starting directory load in background thread")
        threading.Thread(target=load_directory, daemon=True).start()
        
        # Initialize loading_id at function scope so it's accessible in the finally block
        loading_id = None
        
        # Function to clear the treeview safely
        def clear_treeview():
            try:
                children = self.tree.get_children()
                print(f"Found {len(children)} items to clear")
                for item in children:
                    self.tree.delete(item)
                print("Treeview cleared")
                return True
            except Exception as e:
                print(f"ERROR clearing treeview: {str(e)}")
                import traceback
                traceback.print_exc()
                return False
        
        # Function to add loading indicator safely
        def add_loading_indicator():
            try:
                nonlocal loading_id
                loading_id = self.tree.insert('', 'end', text='Loading...', values=('', ''), tags=('loading',))
                self.tree.see(loading_id)  # Ensure the loading indicator is visible
                self.tree.update()
                print(f"Loading indicator added with ID: {loading_id}")
                return loading_id
            except Exception as e:
                print(f"ERROR adding loading indicator: {str(e)}")
                import traceback
                traceback.print_exc()
                return None
        
        try:
            # Save the current path
            try:
                self.current_path = path
                safe_update_ui(lambda: self.path_var.set(f"Path: {path}"))
                print(f"Path set to: {path}")
            except Exception as e:
                print(f"ERROR setting path: {str(e)}")
                raise  # Re-raise to be caught by outer try/except
            
            # Clear the treeview on the main thread
            print("DEBUG: Clearing treeview...")
            if not safe_update_ui(clear_treeview):
                raise RuntimeError("Failed to clear treeview")
            
            # Add loading indicator on the main thread
            print("DEBUG: Adding loading indicator...")
            loading_id = safe_update_ui(add_loading_indicator)
            if loading_id is None:
                raise RuntimeError("Failed to add loading indicator")
                
        except Exception as e:
            error_msg = f"ERROR in _load_directory: {str(e)}"
            print(error_msg)
            import traceback
            traceback.print_exc()
            
            # Update UI with error on the main thread
            safe_update_ui(
                lambda: self.tree.insert('', 'end', text=f"Error: {str(e)}", values=('', ''), tags=('error',))
            )
            return
        
        # Get directory contents in a background thread to avoid freezing the UI
        def load_directory_async():
            try:
                print(f"\n{'='*80}")
                print(f"DEBUG: load_directory_async()")
                print(f"Path: {path}")
                print(f"Thread: {threading.current_thread().name}")
                print(f"Has self.comm: {hasattr(self, 'comm')}")
                print(f"Tree widget exists: 'tree' in dir(self) and self.tree is not None")
                print(f"After flag: {hasattr(self, 'after')}")
                
                # Set a timeout for the entire operation
                timeout_seconds = 10  # 10 second timeout
                start_time = time.time()
                
                # Define a function to check if we've exceeded the timeout
                def check_timeout():
                    elapsed = time.time() - start_time
                    if elapsed > timeout_seconds:
                        error_msg = "Operation timed out. The controller may be unreachable."
                        print(f"TIMEOUT: {error_msg}")
                        update_ui_with_error(error_msg)
                        return True
                    return False
                
                # Check if we have a valid loading_id
                if loading_id is None:
                    error_msg = "No valid loading_id provided"
                    print(f"ERROR: {error_msg}")
                    update_ui_with_error(f"Failed to initialize: {error_msg}")
                    return
                
                # Make a local copy of the comm object to prevent race conditions
                try:
                    comm = getattr(self, 'comm', None)
                    if comm is None:
                        error_msg = "Controller communication interface is not available"
                        print(f"ERROR: {error_msg}")
                        update_ui_with_error(error_msg)
                        return
                        
                    # Verify controller connection
                    if not hasattr(comm, 'connected') or not comm.connected:
                        error_msg = "Not connected to controller. Please check connection and try again."
                        print(f"ERROR: {error_msg}")
                        update_ui_with_error(error_msg)
                        return
                        
                    # Check if list_directory method is available
                    if not hasattr(comm, 'list_directory') or not callable(comm.list_directory):
                        error_msg = "Controller interface does not support directory listing"
                        print(f"ERROR: {error_msg}")
                        update_ui_with_error(error_msg)
                        return
                        
                except Exception as comm_error:
                    error_msg = f"Error initializing controller communication: {str(comm_error)}"
                    print(f"ERROR: {error_msg}")
                    import traceback
                    traceback.print_exc()
                    update_ui_with_error("Failed to communicate with controller. Please check the connection.")
                    return
                    
                # Check timeout before proceeding
                if check_timeout():
                    return
                    
                # Make sure the treeview is still valid
                if not hasattr(self, 'tree') or self.tree is None:
                    error_msg = "Treeview widget is no longer available"
                    print(f"ERROR: {error_msg}")
                    update_ui_with_error(error_msg)
                    return
                    
                # At this point, we have a valid comm object and treeview
                # Now try to list the directory contents
                try:
                    print(f"DEBUG: Attempting to list directory: {path}")
                    
                    # Call the list_directory method with a timeout
                    print(f"DEBUG: Checking timeout before listing directory")
                    if check_timeout():
                        print("DEBUG: Directory listing timed out")
                        return
                        
                    # Get directory listing
                    try:
                        print(f"DEBUG: Attempting to list directory: {path}")
                        print(f"DEBUG: comm object type: {type(comm).__name__}")
                        print(f"DEBUG: comm.list_directory type: {'Callable' if callable(getattr(comm, 'list_directory', None)) else 'Not callable'}")
                        
                        # Debug comm object attributes
                        print("DEBUG: comm object attributes:", dir(comm))
                        
                        listing = comm.list_directory(path)
                        print(f"DEBUG: Received directory listing (type: {type(listing).__name__}, length: {len(listing) if hasattr(listing, '__len__') else 'N/A'})")
                        
                        if listing is None:
                            error_msg = "Received None response from list_directory"
                            print(f"ERROR: {error_msg}")
                            update_ui_with_error(error_msg)
                            return
                            
                        # Check if we got a valid response
                        if not isinstance(listing, (list, tuple)):
                            error_msg = f"Invalid response type from controller. Expected list/tuple, got {type(listing).__name__}"
                            print(f"ERROR: {error_msg}")
                            print(f"DEBUG: Listing content: {listing}")
                            update_ui_with_error(error_msg)
                            return
                            
                        print(f"DEBUG: Directory listing contains {len(listing)} items")
                        if listing:
                            print(f"DEBUG: First item in listing: {listing[0]}")
                        else:
                            print("DEBUG: Directory listing is empty")
                        
                        # Define function to update UI with the listing
                        def update_ui_with_listing():
                            success = False
                            try:
                                print(f"DEBUG: Updating UI with directory listing ({len(listing)} items)")
                                
                                # Clear existing items using our safe method
                                if not self._safe_clear_treeview():
                                    error_msg = "Failed to clear treeview before updating"
                                    print(f"WARNING: {error_msg}")
                                    self._show_error_in_ui(loading_id, error_msg)
                                    return False
                                
                                # Add parent directory reference (..) if not at root
                                if path != 'Home':
                                    try:
                                        parent_path = '/'.join(path.split('/')[:-1]) if '/' in path else 'Home'
                                        item_id = self.tree.insert(
                                            '', 'end',
                                            text='..',
                                            values=('', ''),
                                            tags=('directory', parent_path)
                                        )
                                        # Set the image after insertion to ensure it's displayed
                                        if hasattr(self, 'folder_icon'):
                                            self.tree.item(item_id, image=self.folder_icon)
                                    except Exception as e:
                                        print(f"WARNING: Failed to add parent directory reference: {str(e)}")
                                
                                # Add directory contents to treeview
                                items_added = 0
                                for item in listing:
                                    if not item or not isinstance(item, dict):
                                        print(f"WARNING: Skipping invalid item: {item}")
                                        continue
                                        
                                    try:
                                        # Get item properties with type conversion and defaults
                                        name = str(item.get('name', 'Unknown')).strip()
                                        if not name:  # Skip empty names
                                            print("WARNING: Skipping item with empty name")
                                            continue
                                            
                                        is_dir = bool(item.get('is_dir', False))
                                        try:
                                            size = int(item.get('size', 0))
                                        except (ValueError, TypeError):
                                            size = 0
                                            
                                        modified = str(item.get('modified', '')).strip()
                                        full_path = f"{path}/{name}" if path != 'Home' else name
                                        
                                        # Skip hidden files/directories
                                        if name.startswith('.'):
                                            continue
                                        
                                        # Insert into treeview
                                        if hasattr(self, 'tree') and self.tree is not None:
                                            try:
                                                # Determine icon to use
                                                icon = None
                                                if is_dir:
                                                    icon = getattr(self, 'folder_icon', None)
                                                elif name.lower().endswith(('.gcode', '.nc', '.ngc', '.tap', '.gc')):
                                                    icon = getattr(self, 'macro_icon', None)
                                                else:
                                                    icon = getattr(self, 'file_icon', None)
                                                
                                                # Format size for display
                                                size_display = self._format_size(size) if not is_dir else ''
                                                
                                                # Insert the item
                                                item_id = self.tree.insert(
                                                    '', 'end',
                                                    text=name,
                                                    values=(size_display, modified),
                                                    tags=('directory' if is_dir else 'file', full_path)
                                                )
                                                
                                                # Set the image if available
                                                if icon is not None:
                                                    self.tree.item(item_id, image=icon)
                                                
                                                items_added += 1
                                                print(f"DEBUG: Added item to tree: {name} (dir: {is_dir}, size: {size})")
                                                
                                            except Exception as e:
                                                print(f"ERROR adding item {name} to treeview: {str(e)}")
                                                import traceback
                                                traceback.print_exc()
                                                continue
                                        
                                    except Exception as e:
                                        print(f"ERROR processing item {item}: {str(e)}")
                                        import traceback
                                        traceback.print_exc()
                                        continue
                                
                                # Update UI state
                                try:
                                    self.current_path = path
                                    if hasattr(self, 'path_var'):
                                        self.path_var.set(f"Path: {path}")
                                    
                                    # Update navigation buttons
                                    if hasattr(self, '_update_navigation_buttons'):
                                        self._update_navigation_buttons()
                                    
                                    # Update button states
                                    if hasattr(self, '_update_external_button_states'):
                                        self._update_external_button_states()
                                    
                                    print(f"DEBUG: Successfully updated directory listing. Added {items_added} items.")
                                    success = True
                                    
                                except Exception as e:
                                    error_msg = f"Error updating UI state: {str(e)}"
                                    print(f"ERROR: {error_msg}")
                                    import traceback
                                    traceback.print_exc()
                                    self._show_error_in_ui(loading_id, error_msg)
                                    return False
                                
                            except Exception as e:
                                error_msg = f"Error updating UI with directory listing: {str(e)}"
                                print(f"ERROR: {error_msg}")
                                import traceback
                                traceback.print_exc()
                                self._show_error_in_ui(loading_id, error_msg)
                                return False
                            
                            # If we got here, everything was successful
                            if success and hasattr(self, 'tree') and self.tree is not None:
                                try:
                                    self.tree.delete(loading_id)
                                except Exception as e:
                                    print(f"WARNING: Failed to remove loading indicator: {str(e)}")
                            
                            return success
                        
                        # Update the UI with the listing on the main thread
                        safe_update_ui(update_ui_with_listing)
                        
                    except Exception as e:
                        error_msg = f"Error listing directory: {str(e)}"
                        print(f"ERROR: {error_msg}")
                        import traceback
                        traceback.print_exc()
                        update_ui_with_error(error_msg)
                        return
                        update_ui_with_error("Failed to list directory contents. The controller may be unreachable.")
                        
                except Exception as e:
                    error_msg = f"Unexpected error in load_directory_async: {str(e)}"
                    print(f"ERROR: {error_msg}")
                    import traceback
                    traceback.print_exc()
                    update_ui_with_error("An unexpected error occurred while loading the directory.")
                    
            except Exception as e:
                print(f"ERROR in load_directory_async initialization: {str(e)}")
                import traceback
                traceback.print_exc()
                return
            
            # Check if we can update the UI from this thread
            try:
                self.after(100, lambda: print("DEBUG: UI update test from background thread successful"))
                print("DEBUG: Successfully scheduled UI update test")
            except Exception as e:
                print(f"ERROR: Failed to schedule UI update: {str(e)}")
            
            # Check if communication interface is available
            if not hasattr(self, 'comm') or self.comm is None:
                error_msg = "Controller communication interface is not available"
                print(f"ERROR: {error_msg}")
                update_ui_with_error(error_msg)
                return
            
            # Check if controller is connected
            if not getattr(self.comm, 'connected', False):
                error_msg = "Controller is not connected. Please check the connection and try again."
                print(f"ERROR: {error_msg}")
                update_ui_with_error(error_msg)
                return
            
            items = []
            try:
                print(f"\nDEBUG: Preparing to list directory: '{path}'")
                
                # Log communication interface status
                print(f"DEBUG: Communication interface status:")
                print(f"  - Connected: {getattr(self.comm, 'connected', 'N/A')}")
                print(f"  - WebSocket: {getattr(self.comm, 'ws', 'N/A')}")
                
                # Add a small delay to ensure UI updates are processed
                print("\nDEBUG: Starting directory listing...")
                start_time = time.time()
                
                # Call the directory listing function with timeout
                try:
                    print(f"DEBUG: Calling comm.list_directory('{path}')...")
                    items = self.comm.list_directory(path)
                    print(f"DEBUG: comm.list_directory() call completed")
                except requests.exceptions.ConnectionError as ce:
                    error_msg = f"Failed to connect to controller: {str(ce)}"
                    print(f"ERROR: {error_msg}")
                    update_ui_with_error(error_msg)
                    return
                except requests.exceptions.Timeout:
                    error_msg = "Connection to controller timed out"
                    print(f"ERROR: {error_msg}")
                    update_ui_with_error(error_msg)
                    return
                except Exception as e:
                    error_msg = f"Error listing directory: {str(e)}"
                    print(f"ERROR: {error_msg}")
                    import traceback
                    traceback.print_exc()
                    update_ui_with_error(error_msg)
                    return
                
                elapsed = time.time() - start_time
                print(f"\nDEBUG: Directory listing completed in {elapsed:.2f} seconds")
                print(f"DEBUG: Received {len(items)} items from controller")
                
                if not items:
                    print("WARNING: No items returned from controller (empty directory or error)")
                
                # Log first few items for debugging
                print("\nDEBUG: First 5 items (if any):")
                for i, item in enumerate(items[:5]):
                    item_type = item.get('type', 'unknown')
                    item_name = item.get('name', 'unnamed')
                    item_size = item.get('size', 0)
                    print(f"  {i+1}. {item_name} (type: {item_type}, size: {item_size})")
                    
                if len(items) > 5:
                    print(f"  ... and {len(items) - 5} more items")
                
                if not items:
                    print(f"WARNING: No items returned for path: {path}")
                
                # Update UI on the main thread
                def update_ui():
                    try:
                        # Remove loading indicator
                        self.tree.delete(loading_id)
                        
                        # Add parent directory reference (..) if not at root
                        if path != 'Home':
                            parent_path = '/'.join(path.split('/')[:-1]) if '/' in path else 'Home'
                            item_id = self.tree.insert(
                                '', 'end',
                                text='..',
                                values=('', ''),
                                tags=('directory', parent_path)
                            )
                            # Set the image after insertion to ensure it's displayed
                            self.tree.item(item_id, image=self.folder_icon)
                        
                        # Separate directories and files for better sorting
                        dirs = []
                        files = []
                        
                        for item in items:
                            name = item.get('name', '')
                            if not name or name.startswith('.'):
                                continue  # Skip hidden files/directories
                                
                            full_path = f"{path}/{name}" if path != 'Home' else name
                            item['full_path'] = full_path
                            
                            if item.get('type', '').lower() == 'directory' or item.get('dir', False):
                                dirs.append(item)
                            else:
                                files.append(item)
                        
                        # Sort directories and files
                        dirs.sort(key=lambda x: x.get('name', '').lower())
                        files.sort(key=lambda x: x.get('name', '').lower())
                        
                        # Add directories first
                        for item in dirs:
                            name = item.get('name', '')
                            full_path = item['full_path']
                            modified = item.get('modified', '')
                            
                            # Format date if it's a timestamp
                            if modified and isinstance(modified, (int, float)) and modified > 0:
                                try:
                                    dt = datetime.fromtimestamp(modified)
                                    modified = dt.strftime('%Y-%m-%d %H:%M')
                                except (ValueError, OSError):
                                    modified = str(modified)
                            
                            # Insert the item first
                            item_id = self.tree.insert(
                                '', 'end',
                                text=name,
                                values=('', modified),
                                tags=('directory', full_path)
                            )
                            # Then set the image
                            self.tree.item(item_id, image=self.folder_icon)
                        
                        # Then add files
                        for item in files:
                            name = item.get('name', '')
                            full_path = item['full_path']
                            size = self._format_size(item.get('size', 0))
                            modified = item.get('modified', '')
                            
                            # Format date if it's a timestamp
                            if modified and isinstance(modified, (int, float)) and modified > 0:
                                try:
                                    dt = datetime.fromtimestamp(modified)
                                    modified = dt.strftime('%Y-%m-%d %H:%M')
                                except (ValueError, OSError):
                                    modified = str(modified)
                            
                            # Determine the appropriate icon
                            icon = self.macro_icon if name.lower().endswith(('.gcode', '.ngc')) else self.file_icon
                            
                            # Insert the item first
                            item_id = self.tree.insert(
                                '', 'end',
                                text=name,
                                values=(size, modified),
                                tags=('file', full_path)
                            )
                            # Then set the image
                            self.tree.item(item_id, image=icon)
                            
                        # Update button states
                        self._update_external_button_states()
                        
                    except Exception as e:
                        print(f"Error updating UI: {str(e)}")
                        import traceback
                        traceback.print_exc()
                        
                        # Show error in UI
                        self.tree.delete(loading_id)
                        self.tree.insert('', 'end', text=f'Error: {str(e)}', values=('', ''), tags=('error',))
                        self.tree.tag_configure('error', foreground='red')
                
                # Schedule UI update on the main thread
                self.after(0, update_ui)
                
            except Exception as e:
                error_msg = f"Error listing directory {path}: {str(e)}"
                print(error_msg)
                import traceback
                traceback.print_exc()
                
                # Update UI on the main thread
                def show_error():
                    try:
                        self.tree.delete(loading_id)
                        self.tree.insert('', 'end', text=f'Error: {str(e)}', values=('', ''), tags=('error',))
                        self.tree.tag_configure('error', foreground='red')
                    except Exception as ui_error:
                        print(f"ERROR updating UI: {str(ui_error)}")
                
                self.after(0, show_error)
            
            finally:
                # Update navigation buttons
                self._update_navigation_buttons()
        
        # Start the directory loading in a background thread
        print("DEBUG: Starting directory loading thread...")
        try:
            thread_obj = threading.Thread(target=load_directory_async, daemon=True, name=f"DirLoad-{path}")
            thread_obj.start()
            print(f"DEBUG: Directory loading thread started: {thread_obj.name}")
        except Exception as e:
            print(f"ERROR: Failed to start directory loading thread: {str(e)}")
            import traceback
            traceback.print_exc()
            # Show error in UI
            self.after(0, lambda: self.tree.delete(loading_id))
            self.after(0, lambda: self.tree.insert('', 'end', text=f'Error: {str(e)}', values=('', ''), tags=('error',)))
        
        # Update navigation buttons after loading directory
        print("DEBUG: Updating navigation buttons...")
        self._update_navigation_buttons()
        self._update_external_button_states()
        print("DEBUG: Navigation buttons updated")
    
    def _format_size(self, size_bytes):
        """Convert file size in bytes to human-readable format.
        
        Args:
            size_bytes: File size in bytes
            
        Returns:
            str: Formatted file size (e.g., "1.2 KB", "3.4 MB")
        """
        if size_bytes is None or not isinstance(size_bytes, (int, float)) or size_bytes < 0:
            return ''
            
        if size_bytes == 0:
            return '0 B'
            
        size_names = ("B", "KB", "MB", "GB", "TB")
        i = 0
        size = float(size_bytes)
        
        while size >= 1024 and i < len(size_names) - 1:
            size /= 1024.0
            i += 1
            
        if i == 0:
            return f"{int(size)} {size_names[i]}"
        else:
            return f"{size:.1f} {size_names[i]}"
            
    def _refresh_macro_lists(self):
        """Refresh both macro list displays."""
        self._refresh_local_macro_list()
        self._refresh_external_macro_list()

    def _refresh_local_macro_list(self):
        """Refresh the local macro list display."""
        self.local_macro_listbox.delete(0, tk.END)
        
        local_macros = self.local_macro_manager.get_all_local_macros()
        for macro in sorted(local_macros, key=lambda m: (m.category, m.name)):
            # Color code by category
            color_prefix = self._get_category_prefix(macro.category)
            display_text = f"{color_prefix} {macro.name}"
            if macro.description:
                display_text += f" - {macro.description[:25]}"
                if len(macro.description) > 25:
                    display_text += "..."
            
            self.local_macro_listbox.insert(tk.END, display_text)
        
        self._update_local_button_states()
    
    def _open_file(self, file_path):
        """Open a file for viewing/editing."""
        try:
            main_window = self._get_main_window()
            if not main_window or not hasattr(main_window, 'code_editor'):
                messagebox.showerror("Error", "Could not access the code editor.")
                return
                
            # Get the file content from the controller
            try:
                content = self.comm.read_file(file_path)
                if content is None:
                    raise Exception("Failed to read file content")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to read file: {str(e)}")
                return
            
            # Clear and populate the editor
            main_window.code_editor.text_widget.delete('1.0', tk.END)
            main_window.code_editor.text_widget.insert('1.0', content)
            
            # Update window title and status
            file_name = file_path.split('/')[-1] if '/' in file_path else file_path
            main_window.current_file_path = file_path
            if hasattr(main_window, 'file_status'):
                main_window.file_status.set(f"Viewing: {file_name}")
            
            # Mark as clean since we just loaded this content
            if hasattr(main_window, 'mark_editor_clean'):
                main_window.mark_editor_clean()
                
            # Apply syntax highlighting
            main_window.code_editor.highlight_all()
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to open file: {str(e)}")
            
    def _load_icon(self, icon_name):
        """
        Load an icon from the resources or use a default symbol.
        
        Args:
            icon_name: Base name of the icon (without extension)
            
        Returns:
            A PhotoImage object or None if loading fails
        """
        # Initialize icon cache if it doesn't exist
        if not hasattr(self, '_icon_cache'):
            self._icon_cache = {}
            
        # Return cached icon if available
        if icon_name in self._icon_cache:
            return self._icon_cache[icon_name]
            
        try:
            # Try to load from the icons directory
            script_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            icon_path = os.path.join(script_dir, 'resources', 'icons', f'{icon_name}.png')
            
            print(f"DEBUG: Loading icon: {icon_path}")
            
            if os.path.exists(icon_path):
                # Load and resize the icon
                img = Image.open(icon_path).convert('RGBA')
                img = img.resize((16, 16), Image.Resampling.LANCZOS)
                photo = ImageTk.PhotoImage(img)
                
                # Store reference to prevent garbage collection
                self._icon_cache[icon_name] = photo
                print(f"DEBUG: Successfully loaded icon: {icon_name}")
                return photo
            else:
                print(f"DEBUG: Icon not found: {icon_path}")
            
            # Default icons if file not found
            default_icons = {
                'folder': '📁',
                'file': '📄',
                'macro': '⚙️'
            }
            
            # Create a simple image with the text
            img = Image.new('RGBA', (16, 16), (0, 0, 0, 0))
            
            # If we have a text fallback, draw it on the image
            if icon_name in default_icons:
                from PIL import ImageDraw, ImageFont
                try:
                    draw = ImageDraw.Draw(img)
                    # Try to use a default font, fallback to default if not available
                    try:
                        font = ImageFont.truetype("Arial", 12)
                    except IOError:
                        font = ImageFont.load_default()
                    text = default_icons[icon_name]
                    draw.text((0, 0), text, font=font, fill="black")
                except Exception as e:
                    print(f"Warning: Could not draw text for icon {icon_name}: {e}")
            
            photo = ImageTk.PhotoImage(img)
            self._icon_cache[icon_name] = photo
            return photo
            
        except Exception as e:
            print(f"Error loading icon {icon_name}: {str(e)}")
            # Return a blank image as fallback
            img = Image.new('RGBA', (16, 16), (0, 0, 0, 0))
            photo = ImageTk.PhotoImage(img)
            self._icon_cache[f'error_{icon_name}'] = photo
            return photo
    
    def _on_tree_item_double_click(self, event):
        """Handle double-click on a tree item."""
        item = self.tree.identify('item', event.x, event.y)
        if not item:
            return
            
        tags = self.tree.item(item, 'tags')
        if not tags or len(tags) < 2:  # Need at least type and path
            return
            
        item_type = tags[0]
        full_path = tags[1]
        
        if item_type == 'directory':
            # If it's the parent directory (..), navigate up
            if self.tree.item(item, 'text') == '..':
                parts = self.current_path.split('/')
                if len(parts) > 1:
                    parent_path = '/'.join(parts[:-1]) if len(parts) > 1 else 'Home'
                    self._load_directory(parent_path)
                else:
                    self._load_directory('Home')
            else:
                # Navigate into the directory
                self._load_directory(full_path)
        else:
            # Open the file
            self._open_file(full_path)
    
    def _on_tree_item_select(self, event):
        """Handle selection of a tree item."""
        selection = self.tree.selection()
        if not selection:
            self.selected_macro = None
            self._update_external_button_states()
            return
            
        item = selection[0]
        tags = self.tree.item(item, 'tags')
        
        # Update selected macro
        if tags and len(tags) > 1:
            item_type = tags[0]
            full_path = tags[1]
            if item_type == 'file':
                # Create a macro object for the selected file
                self.selected_macro = type('Macro', (), {
                    'name': full_path.split('/')[-1] if '/' in full_path else full_path,
                    'path': full_path,
                    'is_file': True
                })
            else:
                self.selected_macro = None
        else:
            self.selected_macro = None
        
        # Update button states based on selection
        self._update_external_button_states()
    
    def _on_tree_right_click(self, event):
        """Handle right-click on a tree item to show context menu."""
        item = self.tree.identify_row(event.y)
        if not item:
            return
            
        # Select the item that was right-clicked
        self.tree.selection_set(item)
        
        # Update button states
        self._update_external_buttons()
        
        # Show the context menu
        try:
            self.tree_menu.tk_popup(event.x_root, event.y_root)
        finally:
            self.tree_menu.grab_release()
    
    def _on_open_item(self):
        """Handle Open command from context menu."""
        selection = self.tree.selection()
        if not selection:
            return
            
        item = selection[0]
        tags = self.tree.item(item, 'tags')
        if not tags:
            return
            
        item_type = tags[0]
        full_path = tags[1] if len(tags) > 1 else ''
        
        if item_type == 'directory':
            self._load_directory(full_path)
        else:
            self._open_file(full_path)
    
    def _on_edit_item(self):
        """Handle Edit command from context menu."""
        selection = self.tree.selection()
        if not selection:
            return
            
        item = selection[0]
        tags = self.tree.item(item, 'tags')
        if not tags or len(tags) < 2:
            return
            
        item_type = tags[0]
        full_path = tags[1]
        
        if item_type == 'file':
            self._open_file(full_path)
    
    def _on_delete_item(self):
        """Handle Delete command from context menu."""
        selection = self.tree.selection()
        if not selection:
            return
            
        item = selection[0]
        tags = self.tree.item(item, 'tags')
        if not tags or len(tags) < 2:
            return
            
        item_type = tags[0]
        full_path = tags[1]
        
        if full_path == '..':
            return  # Can't delete parent directory reference
        
        # Confirm deletion
        if not messagebox.askyesno("Confirm Delete", 
                                 f"Are you sure you want to delete {item_type} '{full_path}'?",
                                 parent=self):
            return
            
        try:
            if item_type == 'directory':
                # Delete directory
                self.comm.delete_directory(full_path)
            else:
                # Delete file
                self.comm.delete_file(full_path)
                
            # Refresh the view
            self._refresh_external_macro_list()
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to delete {item_type}: {str(e)}", parent=self)
    
    def _on_rename_item(self):
        """Handle Rename command from context menu."""
        selection = self.tree.selection()
        if not selection:
            return
            
        item = selection[0]
        tags = self.tree.item(item, 'tags')
        if not tags or len(tags) < 2:
            return
            
        item_type = tags[0]
        full_path = tags[1]
        old_name = os.path.basename(full_path)
        
        # Get new name from user
        new_name = simpledialog.askstring("Rename", 
                                         f"Enter new name for {item_type}:",
                                         initialvalue=old_name,
                                         parent=self)
        
        if not new_name or new_name == old_name:
            return  # User cancelled or didn't change the name
            
        try:
            # Build new full path
            parent_dir = os.path.dirname(full_path)
            new_full_path = os.path.join(parent_dir, new_name)
            
            # Rename the file or directory
            if item_type == 'directory':
                self.comm.rename_directory(full_path, new_full_path)
            else:
                self.comm.rename_file(full_path, new_full_path)
                
            # Refresh the view
            self._refresh_external_macro_list()
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to rename {item_type}: {str(e)}", parent=self)
    
    def _get_category_prefix(self, category: str) -> str:
        """Get emoji prefix for macro category."""
        # Convert to lowercase and strip whitespace for consistent matching
        if category:
            category = str(category).lower().strip()
        
        # Define all possible categories with their emojis
        prefixes = {
            "system": "⚙️",
            "sys": "⚙️",
            "homing": "🏠",
            "home": "🏠",
            "tool_change": "🔧",
            "toolchange": "🔧",
            "tool": "🔧",
            "probing": "📐",
            "probe": "📐",
            "user": "👤",
            "custom": "⭐",
            "debug": "🐛",
            "mdi": "⌨️",
            "gcode": "📜",
            "setup": "🔧",
            "calibration": "🎚️",
            "utility": "🛠️",
            "maintenance": "🔧",
            "test": "🧪",
            "safety": "⚠️",
            "spindle": "🌀",
            "coolant": "💧",
            "jog": "🎮",
            "zero": "0️⃣",
            "reference": "📍"
        }
        
        # Try exact match first
        if category in prefixes:
            return prefixes[category]
            
        # Try partial matching (e.g., "toolchange" matches "tool_change")
        for key, emoji in prefixes.items():
            if key in category or category in key:
                print(f"DEBUG: Matched category '{category}' to emoji '{emoji}'")
                return emoji
        
        # Default emoji for unknown categories
        print(f"DEBUG: Using default emoji for unknown category: '{category}'")
        return "📝"
    
    # Local macro event handlers
    def _on_local_macro_select(self, event):
        """Handle local macro selection and load into editor."""
        selection = self.local_macro_listbox.curselection()
        if selection:
            macro_text = self.local_macro_listbox.get(selection[0])
            # Extract macro name (remove emoji and description)
            macro_name = macro_text.split(' - ')[0].split(' ', 1)[1]  # Remove emoji prefix
            self.selected_local_macro = self.local_macro_manager.get_local_macro(macro_name)
            
            # Load the macro into the editor
            if self.selected_local_macro:
                self._load_macro_into_editor(self.selected_local_macro, is_local=True)
        else:
            self.selected_local_macro = None
        
        self._update_local_button_states()
    
    def _update_local_button_states(self):
        """Update local macro button enabled/disabled states."""
        has_selection = self.selected_local_macro is not None
        
        self.local_execute_btn.config(state=tk.NORMAL if has_selection else tk.DISABLED)
        self.local_delete_btn.config(state=tk.NORMAL if has_selection else tk.DISABLED)
        self.local_export_btn.config(state=tk.NORMAL if has_selection else tk.DISABLED)
    
    # External macro event handlers
    def _on_external_macro_select(self, event):
        """Handle external macro selection and load into editor."""
        selection = self.external_macro_listbox.curselection()
        if selection:
            macro_text = self.external_macro_listbox.get(selection[0])
            # Extract macro name (remove emoji and description)
            macro_name = macro_text.split(' - ')[0].split(' ', 1)[1]  # Remove emoji prefix
            self.selected_macro = self.macro_manager.get_macro(macro_name)
            
            # Load the macro into the editor
            if self.selected_macro:
                self._load_macro_into_editor(self.selected_macro, is_local=False)
        else:
            self.selected_macro = None
        
        self._update_external_button_states()
        
    def _save_current_macro(self, main_window) -> bool:
        """Save the current macro content back to the macro manager.
        
        Returns:
            bool: True if save was successful, False otherwise.
        """
        print("DEBUG: Starting _save_current_macro")
        
        if not hasattr(main_window, 'code_editor'):
            print("DEBUG: No code_editor in main_window")
            return False
            
        if not hasattr(main_window, 'debugger'):
            print("DEBUG: No debugger in main_window")
            return False
            
        try:
            # Get the current content from the editor
            content = main_window.code_editor.text_widget.get('1.0', tk.END).strip()
            print(f"DEBUG: Got editor content, length: {len(content)}")
            
            # Parse the content to extract the macro name and commands
            lines = [line.strip() for line in content.split('\n') if line.strip()]
            print(f"DEBUG: Parsed {len(lines)} non-empty lines")
            
            if not lines:
                print("DEBUG: No content to save")
                return False
                
            # The first line should contain the macro name
            first_line = lines[0]
            print(f"DEBUG: First line: {first_line}")
            
            if not first_line.startswith('; '):
                print("DEBUG: First line doesn't start with '; ' (semicolon space)")
                return False
                
            # Extract macro name from the first line
            macro_name = first_line[2:].split(':', 1)[1].strip() if ':' in first_line else first_line[2:].strip()
            print(f"DEBUG: Extracted macro name: '{macro_name}'")
            
            # Skip header lines (starting with ';') to get the actual commands
            commands = [line for line in lines if not line.startswith(';')]
            print(f"DEBUG: Found {len(commands)} command lines")
            
            # Get the current tab (local or external macros)
            try:
                current_tab = self.notebook.tab(self.notebook.select(), "text").lower()
                print(f"DEBUG: Current tab text: '{current_tab}'")
                
                # Check if this is a local macro tab (handle emoji prefix)
                is_local = 'local' in current_tab
                print(f"DEBUG: Detected macro type: {'local' if is_local else 'external'}")
                
                if is_local:
                    print("DEBUG: Processing local macro")
                    if hasattr(main_window, 'local_macro_manager'):
                        print("DEBUG: Found local_macro_manager, updating macro")
                        # Try to get the macro first to ensure it exists
                        existing_macro = main_window.local_macro_manager.get_local_macro(macro_name)
                        if existing_macro is None:
                            print(f"DEBUG: Local macro '{macro_name}' not found, creating new one")
                            result = main_window.local_macro_manager.create_local_macro(
                                name=macro_name,
                                commands=commands,
                                description=existing_macro.description if hasattr(existing_macro, 'description') else ""
                            )
                        else:
                            print("DEBUG: Updating existing local macro")
                            result = main_window.local_macro_manager.update_local_macro(
                                name=macro_name,
                                commands=commands,
                                description=existing_macro.description if hasattr(existing_macro, 'description') else ""
                            )
                        print(f"DEBUG: Local macro update result: {result}")
                        return result
                    else:
                        print("DEBUG: No local_macro_manager found in main_window")
                else:  # External macros
                    print("DEBUG: Processing external macro")
                    if hasattr(main_window, 'macro_manager'):
                        print("DEBUG: Found macro_manager, updating macro")
                        # Try to get the macro first to ensure it exists
                        existing_macro = main_window.macro_manager.get_macro(macro_name)
                        if existing_macro is None:
                            print(f"DEBUG: External macro '{macro_name}' not found, creating new one")
                            result = main_window.macro_manager.create_macro(
                                name=macro_name,
                                commands=commands,
                                description=existing_macro.description if hasattr(existing_macro, 'description') else ""
                            )
                        else:
                            print("DEBUG: Updating existing external macro")
                            result = main_window.macro_manager.update_macro(
                                name=macro_name,
                                commands=commands,
                                description=existing_macro.description if hasattr(existing_macro, 'description') else ""
                            )
                        print(f"DEBUG: External macro update result: {result}")
                        return result
                    else:
                        print("DEBUG: No macro_manager found in main_window")
                        
            except Exception as e:
                print(f"DEBUG: Error in tab detection or macro update: {e}")
                import traceback
                traceback.print_exc()
                return False
                    
            print("DEBUG: No appropriate macro manager found")
            return False
            
        except Exception as e:
            print(f"ERROR in _save_current_macro: {e}", file=sys.stderr)
            import traceback
            traceback.print_exc()
            return False
    
    def _prompt_save_changes(self, main_window) -> bool:
        """Prompt the user to save changes if there are any unsaved changes.
        
        Returns:
            bool: True if the user wants to continue (saved or discarded changes),
                  False if the user cancelled the operation.
        """
        if not hasattr(main_window, 'code_editor'):
            return True
            
        try:
            if hasattr(main_window.code_editor, 'has_unsaved_changes') and \
               main_window.code_editor.has_unsaved_changes():
                response = messagebox.askyesnocancel(
                    "Unsaved Changes",
                    "You have unsaved changes in the editor. Do you want to save them?\n"
                    "Click 'Yes' to save, 'No' to discard changes, or 'Cancel' to stay.",
                    icon='warning'
                )
                
                if response is None:  # User clicked Cancel
                    return False
                    
                if response:  # User clicked Yes
                    if not self._save_current_macro(main_window):
                        messagebox.showerror("Error", "Failed to save changes to macro.")
                        return False
                
                # Clear the modified flag in either case (save or discard)
                if hasattr(main_window.code_editor, 'clear_modified_flag'):
                    main_window.code_editor.clear_modified_flag()
                    
            return True
            
        except Exception as e:
            print(f"Error checking for unsaved changes: {e}")
            return True  # Continue on error to avoid blocking
    
    def _load_macro_into_editor(self, macro, is_local=True):
        """Load macro content into the debugger panel."""
        import tempfile
        import os
        
        # Get the main window
        main_window = self._get_main_window()
        if not main_window or not hasattr(main_window, 'debugger'):
            messagebox.showerror("Error", "Could not access the debugger components.")
            return
            
        # Check for unsaved changes
        if not self._prompt_save_changes(main_window):
            return  # User cancelled the operation
            
        try:
            # Create a header for the macro
            macro_type = "Local" if is_local else "External"
            macro_content = f"; {macro_type} Macro: {macro.name}\n"
            
            if hasattr(macro, 'description') and macro.description:
                macro_content += f"; Description: {macro.description}\n"
            if is_local and hasattr(macro, 'category') and macro.category:
                macro_content += f"; Category: {macro.category}\n"
            elif hasattr(macro, 'group') and macro.group:
                macro_content += f"; Group: {macro.group}\n"
                
            macro_content += ";\n"
            
            # Add the macro commands
            macro_content += '\n'.join(macro.commands)
            
            # Create a temporary file with the macro content
            with tempfile.NamedTemporaryFile(mode='w', suffix='.gcode', delete=False) as temp_file:
                temp_file.write(macro_content)
                temp_path = temp_file.name
            
            try:
                # Load the temporary file using the debugger's load_file method
                if main_window.debugger.load_file(temp_path):
                    # Update window title and status
                    main_window.current_file_path = f"[{macro_type} Macro] {macro.name}"
                    if hasattr(main_window, 'file_status'):
                        main_window.file_status.set(f"Viewing: {macro.name} ({macro_type} Macro)")
                    
                    # Log the action
                    if hasattr(main_window, '_log_message'):
                        main_window._log_message(f"Loaded {macro_type.lower()} macro '{macro.name}' into debugger")
                    
                    # Update the code editor if available
                    if hasattr(main_window, 'code_editor') and hasattr(main_window.code_editor, 'load_gcode'):
                        main_window.code_editor.load_gcode(main_window.debugger.parser)
                        
                        # Clear the modified flag since we just loaded new content
                        if hasattr(main_window.code_editor, 'clear_modified_flag'):
                            main_window.code_editor.clear_modified_flag()
                else:
                    raise Exception("Failed to load macro content")
                    
            finally:
                # Clean up the temporary file
                try:
                    if os.path.exists(temp_path):
                        os.unlink(temp_path)
                except Exception as e:
                    print(f"Warning: Failed to delete temporary file: {e}")
            
        except Exception as e:
            error_msg = f"Failed to load macro into debugger: {e}"
            messagebox.showerror("Error", error_msg)
            if hasattr(main_window, '_log_message'):
                main_window._log_message(f"Error loading macro: {str(e)}", color="red")
    
    def _update_external_button_states(self):
        """Update external macro button enabled/disabled states.
        
        This method updates the state of all external macro buttons based on the current selection
        and execution state. It ensures that buttons are only enabled when their actions are valid.
        """
        # Get the main window to check execution state
        main_window = self._get_main_window()
        is_executing = hasattr(main_window, 'is_external_macro_executing') and main_window.is_external_macro_executing()
        has_selection = self.selected_macro is not None
        
        # Update button states
        self.external_execute_btn.config(
            state=tk.NORMAL if (has_selection and not is_executing) else tk.DISABLED
        )
        self.external_stop_btn.config(
            state=tk.NORMAL if is_executing else tk.DISABLED
        )
        self.external_delete_btn.config(
            state=tk.NORMAL if (has_selection and not is_executing) else tk.DISABLED
        )
        self.external_export_btn.config(
            state=tk.NORMAL if (has_selection and not is_executing) else tk.DISABLED
        )
        self.external_import_btn.config(
            state=tk.NORMAL if not is_executing else tk.DISABLED
        )
        self.external_new_btn.config(
            state=tk.NORMAL if not is_executing else tk.DISABLED
        )
    
    # Local macro execution and management methods
    def _on_execute_local_macro(self, event=None):
        """Execute the selected local macro."""
        if not self.selected_local_macro:
            return
        
        # Get main window and execute local macro
        main_window = self._get_main_window()
        if main_window and hasattr(main_window, 'execute_local_macro'):
            main_window.execute_local_macro(self.selected_local_macro.name)
            self.local_stop_btn.config(state=tk.NORMAL)
    
    def _on_stop_local_macro(self):
        """Stop local macro execution."""
        main_window = self._get_main_window()
        if main_window and hasattr(main_window, 'local_macro_executor'):
            main_window.local_macro_executor.cancel_execution()
            self.local_stop_btn.config(state=tk.DISABLED)
    
    def _on_new_local_macro(self):
        """Create a new local macro."""
        try:
            dialog = LocalMacroEditDialog(self, "Create New Local Macro")
            if dialog.result:
                name, description, commands, category = dialog.result
                if self.local_macro_manager.create_local_macro(name, commands, description, category):
                    self._refresh_local_macro_list()
                    messagebox.showinfo("Success", f"Local macro '{name}' created successfully!")
                else:
                    messagebox.showerror("Error", f"Failed to create local macro '{name}'. Name may already exist.")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to create local macro dialog: {e}")
    
    def _on_edit_local_macro(self):
        """Edit the selected local macro."""
        if not self.selected_local_macro:
            return
        
        dialog = LocalMacroEditDialog(self, "Edit Local Macro", self.selected_local_macro)
        if dialog.result:
            name, description, commands, category = dialog.result
            if self.local_macro_manager.update_local_macro(
                name, 
                commands=commands, 
                description=description, 
                category=category
            ):
                self._refresh_local_macro_list()
                # No success message - just update the list silently
            else:
                messagebox.showerror("Error", f"Failed to update local macro '{name}'")
    
    def _on_delete_local_macro(self):
        """Delete the selected local macro."""
        if not self.selected_local_macro:
            return
        
        result = messagebox.askyesno(
            "Confirm Delete", 
            f"Are you sure you want to delete local macro '{self.selected_local_macro.name}'?"
        )
        
        if result:
            if self.local_macro_manager.delete_local_macro(self.selected_local_macro.name):
                self._refresh_local_macro_list()
                messagebox.showinfo("Success", f"Local macro '{self.selected_local_macro.name}' deleted.")
            else:
                messagebox.showerror("Error", f"Failed to delete local macro.")
    
    def _on_import_local_macro(self):
        """Import a local macro from G-code file."""
        from tkinter import filedialog
        
        file_path = filedialog.askopenfilename(
            title="Import Local Macro from G-code File",
            filetypes=[
                ("G-code files", "*.nc *.gcode *.tap *.ngc *.gc"),
                ("All files", "*.*")
            ]
        )
        
        if file_path:
            name = simpledialog.askstring("Import Local Macro", "Enter local macro name:")
            if name:
                description = simpledialog.askstring("Import Local Macro", "Enter description (optional):") or ""
                
                if self.local_macro_manager.import_local_macro_from_file(name, file_path, description):
                    self._refresh_local_macro_list()
                    messagebox.showinfo("Success", f"Local macro '{name}' imported successfully!")
                else:
                    messagebox.showerror("Error", f"Failed to import local macro from file.")
    
    def _on_export_local_macro(self):
        """Export the selected local macro to G-code file."""
        if not self.selected_local_macro:
            return
        
        from tkinter import filedialog
        
        file_path = filedialog.asksaveasfilename(
            title="Export Local Macro to G-code File",
            defaultextension=".gcode",
            filetypes=[
                ("G-code files", "*.gcode *.nc *.tap *.cnc *.ngc *.gc"),
                ("All files", "*.*")
            ]
        )
        
        if file_path:
            if self.local_macro_manager.export_local_macro(self.selected_local_macro.name, file_path):
                messagebox.showinfo("Success", f"Local macro exported to '{file_path}'!")
            else:
                messagebox.showerror("Error", f"Failed to export local macro.")
    def _on_view_local_macro_in_editor(self, event=None):
        """View the selected local macro in the code editor."""
        # If no macro is selected, try to get the current selection
        if not self.selected_local_macro:
            selection = self.local_macro_listbox.curselection()
            if not selection:
                return
            self._on_local_macro_select(event)  # Update the selection
            if not self.selected_local_macro:  # Still no selection
                return
            
        # Get the main window
        main_window = self._get_main_window()
        if not main_window or not hasattr(main_window, 'code_editor'):
            messagebox.showerror("Error", "Could not access the code editor.")
            return
            
        try:
            # Check for unsaved changes in the editor
            if hasattr(main_window, 'is_editor_dirty') and main_window.is_editor_dirty():
                if not messagebox.askyesno(
                    "Unsaved Changes",
                    "You have unsaved changes in the editor. Load macro anyway?"
                ):
                    return  # User chose not to discard changes
            
            # Create a header for the macro
            macro_content = f"; Local Macro: {self.selected_local_macro.name}\n"
            if self.selected_local_macro.description:
                macro_content += f"; Description: {self.selected_local_macro.description}\n"
            if self.selected_local_macro.category:
                macro_content += f"; Category: {self.selected_local_macro.category}\n"
            macro_content += ";\n"
            
            # Add the macro commands
            macro_content += '\n'.join(self.selected_local_macro.commands)
            
            # Load the content into the editor
            main_window.code_editor.text_widget.delete('1.0', tk.END)
            main_window.code_editor.text_widget.insert('1.0', macro_content)
            
            # Update window title and status
            main_window.current_file_path = f"[Local Macro] {self.selected_local_macro.name}"
            if hasattr(main_window, 'file_status'):
                main_window.file_status.set(f"Viewing: {self.selected_local_macro.name} (Local Macro)")
            
            # Mark as clean since we just loaded this content
            if hasattr(main_window, 'mark_editor_clean'):
                main_window.mark_editor_clean()
            
            # Log the action
            if hasattr(main_window, '_log_message'):
                main_window._log_message(f"Loaded local macro '{self.selected_local_macro.name}' into editor")
            
            # Apply syntax highlighting
            main_window.code_editor.highlight_all()
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load macro into editor: {e}")
    
    # Controller file operations
    def _on_execute_external_macro(self, event=None):
        """Execute the selected controller file as a macro."""
        if not self.selected_macro:
            return
            
        try:
            # Get main window and execute external macro
            main_window = self._get_main_window()
            if main_window and hasattr(main_window, 'execute_external_macro'):
                # Update UI to reflect execution state
                self.external_execute_btn.config(state=tk.DISABLED)
                self.external_stop_btn.config(state=tk.NORMAL)
                self.external_import_btn.config(state=tk.DISABLED)
                self.external_new_btn.config(state=tk.DISABLED)
                
                # Execute the macro
                main_window.execute_external_macro(self.selected_macro.name)
                
                # Update button states after execution starts
                self._update_external_button_states()
                
        except Exception as e:
            error_msg = f"Failed to execute external macro: {e}"
            messagebox.showerror("Error", error_msg)
            if hasattr(main_window, '_log_message'):
                main_window._log_message(f"Error executing macro: {str(e)}", color="red")
            # Ensure button states are reset on error
            self._update_external_button_states()
    
    def _on_stop_external_macro(self):
        """Stop controller file execution."""
        try:
            main_window = self._get_main_window()
            if main_window and hasattr(main_window, 'stop_external_macro'):
                # Stop the execution
                main_window.stop_external_macro()
                
                # Update button states
                self._update_external_button_states()
                
        except Exception as e:
            error_msg = f"Failed to stop external macro: {e}"
            messagebox.showerror("Error", error_msg)
            if hasattr(main_window, '_log_message'):
                main_window._log_message(f"Error stopping macro: {str(e)}", color="red")
    
    def _on_new_external_macro(self):
        """Create a new file on the controller."""
        dialog = MacroEditDialog(self, "Create New Controller File")
        if dialog.result:
            name, description, commands, category = dialog.result
            if self.macro_manager.create_macro(name, commands, description, category):
                self._refresh_external_macro_list()
                messagebox.showinfo("Success", f"File '{name}' created successfully on controller!")
            else:
                messagebox.showerror("Error", f"Failed to create file '{name}'. Name may already exist.")
    
    def _on_edit_external_macro(self):
        """Edit the selected controller file."""
        if not self.selected_macro:
            return
        
        dialog = MacroEditDialog(self, "Edit Controller File", self.selected_macro)
        if dialog.result:
            name, description, commands, category = dialog.result
            if self.macro_manager.update_macro(
                name, 
                commands=commands, 
                description=description, 
                category=category
            ):
                self._refresh_external_macro_list()
                messagebox.showinfo("Success", f"File '{name}' updated successfully on controller!")
            else:
                messagebox.showerror("Error", f"Failed to update file '{name}' on controller.")
    
    def _on_delete_external_macro(self):
        """Delete the selected controller file."""
        if not self.selected_macro:
            return
        
        result = messagebox.askyesno(
            "Confirm Delete", 
            f"Are you sure you want to delete file '{self.selected_macro.name}' from the controller?"
        )
        
        if result:
            if self.macro_manager.delete_macro(self.selected_macro.name):
                self._refresh_external_macro_list()
                messagebox.showinfo("Success", f"File '{self.selected_macro.name}' deleted from controller.")
            else:
                messagebox.showerror("Error", f"Failed to delete file from controller.")
    
    def _on_import_external_macro(self):
        """Import a G-code file to the controller."""
        from tkinter import filedialog
        
        file_path = filedialog.askopenfilename(
            title="Import File to Controller",
            filetypes=[
                ("G-code files", "*.nc *.gcode *.tap *.ngc *.gc"),
                ("All files", "*.*")
            ]
        )
        
        if file_path:
            name = simpledialog.askstring("Import to Controller", "Enter file name:")
            if name:
                description = simpledialog.askstring("Import to Controller", "Enter description (optional):") or ""
                
                if self.macro_manager.import_macro_from_file(name, file_path, description):
                    self._refresh_external_macro_list()
                    messagebox.showinfo("Success", f"File '{name}' imported to controller successfully!")
                else:
                    messagebox.showerror("Error", f"Failed to import file to controller.")
    
    def _on_export_external_macro(self):
        """Export the selected controller file to local G-code file."""
        if not self.selected_macro:
            return
        
        from tkinter import filedialog
        
        file_path = filedialog.asksaveasfilename(
            title="Export Controller File",
            defaultextension=".gcode",
            filetypes=[
                ("G-code files", "*.gcode *.nc *.tap *.cnc *.ngc *.gc"),
                ("All files", "*.*")
            ]
        )
        
        if file_path:
            if self.macro_manager.export_macro(self.selected_macro.name, file_path):
                messagebox.showinfo("Success", f"Controller file exported to '{file_path}'")
            else:
                messagebox.showerror("Error", f"Failed to export controller file.")
    
    def _on_view_external_macro_in_editor(self, event=None):
        """View the selected controller file in the code editor."""
        # If no macro is selected, try to get the current selection
        if not self.selected_macro:
            selection = self.external_macro_listbox.curselection()
            if not selection:
                return
            self._on_external_macro_select(event)  # Update the selection
            if not self.selected_macro:  # Still no selection
                return
            
        # Get the main window
        main_window = self._get_main_window()
        if not main_window or not hasattr(main_window, 'code_editor'):
            messagebox.showerror("Error", "Could not access the code editor.")
            return
            
        try:
            # Check for unsaved changes in the editor
            if hasattr(main_window, 'is_editor_dirty') and main_window.is_editor_dirty():
                if not messagebox.askyesno(
                    "Unsaved Changes",
                    "You have unsaved changes in the editor. Load macro anyway?"
                ):
                    return  # User chose not to discard changes
                    
            # Create a header for the macro
            macro_content = f"; Controller File: {self.selected_macro.name}\n"
            if self.selected_macro.description:
                macro_content += f"; Description: {self.selected_macro.description}\n"
            if hasattr(self.selected_macro, 'group') and self.selected_macro.group:
                macro_content += f"; Group: {self.selected_macro.group}\n"
            macro_content += ";\n"
            
            # Add the macro commands
            macro_content += '\n'.join(self.selected_macro.commands)
            
            # Load the content into the editor
            main_window.code_editor.text_widget.delete('1.0', tk.END)
            main_window.code_editor.text_widget.insert('1.0', macro_content)
            
            # Update window title and status
            main_window.current_file_path = f"[Controller] {self.selected_macro.name}"
            if hasattr(main_window, 'file_status'):
                main_window.file_status.set(f"Viewing: {self.selected_macro.name} (External Macro)")
            
            # Mark as clean since we just loaded this content
            if hasattr(main_window, 'mark_editor_clean'):
                main_window.mark_editor_clean()
            
            # Log the action
            if hasattr(main_window, '_log_message'):
                main_window._log_message(f"Loaded external macro '{self.selected_macro.name}' into editor")
            
            # Apply syntax highlighting
            main_window.code_editor.highlight_all()
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load macro into editor: {e}")
    
    def _on_nav_back(self):
        """Handle Back button click to navigate back in history."""
        if len(self.path_history) > 1:
            # Remove current path from history
            current_path = self.path_history.pop()
            # Get previous path
            previous_path = self.path_history[-1] if self.path_history else 'Home'
            # Load the previous path without adding to history (will be done in _load_directory)
            self.path_history = self.path_history[:-1]  # Remove last item to avoid duplication
            self._load_directory(previous_path)
            
    def _on_nav_forward(self):
        """Handle Forward button click to navigate forward in history."""
        # Not implemented yet as we don't have forward history
        pass
        
    def _format_size(self, size_bytes: int) -> str:
        """Format file size in bytes to a human-readable string.
        
        Args:
            size_bytes: File size in bytes
            
        Returns:
            str: Formatted file size string (e.g., '1.2 KB', '3.5 MB')
        """
        try:
            size_bytes = int(size_bytes)
            if size_bytes < 0:
                return "0 B"
                
            size_names = ('B', 'KB', 'MB', 'GB', 'TB', 'PB', 'EB', 'ZB', 'YB')
            i = 0
            while size_bytes >= 1024 and i < len(size_names) - 1:
                size_bytes /= 1024.0
                i += 1
                
            if i == 0:
                return f"{size_bytes} {size_names[i]}"
            else:
                return f"{size_bytes:.1f} {size_names[i]}"
                
        except (ValueError, TypeError):
            return "0 B"
    
    def _safe_clear_treeview(self):
        """Safely clear all items from the treeview with thread safety.
        
        Returns:
            bool: True if the treeview was cleared successfully, False otherwise
        """
        print(f"\n{'='*80}")
        print(f"DEBUG: _safe_clear_treeview() called from thread: {threading.current_thread().name}")
        
        def _do_clear():
            try:
                # Check if treeview exists and is accessible
                if not hasattr(self, 'tree') or self.tree is None:
                    print("WARNING: Treeview widget not found or already destroyed")
                    return False
                
                print("DEBUG: Treeview widget found")
                
                # Check if the widget is still valid
                try:
                    exists = self.tree.winfo_exists()
                    print(f"DEBUG: Treeview exists check: {exists}")
                    if not exists:
                        print("WARNING: Treeview widget exists but is not valid")
                        return False
                except tk.TclError as e:
                    print(f"WARNING: Treeview widget is no longer valid: {str(e)}")
                    return False
                
                # Get all children with error handling
                try:
                    children = self.tree.get_children()
                    print(f"DEBUG: Found {len(children)} items to clear")
                    if not children:
                        print("DEBUG: No items to clear")
                        return True  # Nothing to clear
                except tk.TclError as e:
                    print(f"WARNING: Failed to get treeview children: {str(e)}")
                    return False
                
                # Remove all items in a single operation with error handling
                try:
                    print("DEBUG: Attempting to clear treeview items")
                    self.tree.delete(*children)
                    # Force update to ensure the treeview is cleared before continuing
                    self.tree.update_idletasks()
                    print("DEBUG: Successfully cleared treeview items")
                    return True
                except tk.TclError as e:
                    print(f"WARNING: Failed to clear treeview items: {str(e)}")
                    return False
                except Exception as e:
                    print(f"ERROR: Unexpected error in _do_clear: {str(e)}")
                    import traceback
                    traceback.print_exc()
                    return False
                
            except Exception as e:
                print(f"ERROR in _do_clear: {str(e)}")
                import traceback
                traceback.print_exc()
                return False
                
        try:
            # If we're on the main thread, execute directly
            if threading.current_thread() is threading.main_thread():
                print("DEBUG: Running on main thread, executing directly")
                return _do_clear()
                
            print("DEBUG: Not on main thread, scheduling operation")
            
            # Otherwise, use a queue to get the result from the main thread
            result_queue = queue.Queue()
            
            def wrapper():
                try:
                    print("DEBUG: Wrapper executing on main thread")
                    result = _do_clear()
                    result_queue.put(result)
                    print(f"DEBUG: Wrapper completed with result: {result}")
                except Exception as e:
                    print(f"ERROR in wrapper: {str(e)}")
                    import traceback
                    traceback.print_exc()
                    result_queue.put(False)
                    
            # Schedule the operation on the main thread
            if hasattr(self, 'after') and callable(self.after):
                print("DEBUG: Scheduling clear operation on main thread")
                self.after(0, wrapper)
                
                # Wait for the result with a timeout to prevent hanging
                try:
                    print("DEBUG: Waiting for clear operation to complete...")
                    result = result_queue.get(timeout=5.0)  # Increased timeout to 5 seconds
                    print(f"DEBUG: Clear operation completed with result: {result}")
                    return result
                except queue.Empty:
                    print("WARNING: Timeout waiting for treeview clear operation")
                    return False
            else:
                print("WARNING: Cannot schedule treeview clear - no 'after' method available")
                return False
        except Exception as e:
            print(f"ERROR in thread handling: {str(e)}")
            import traceback
            traceback.print_exc()
            return False
            
    def _show_error_in_ui(self, loading_id, error_msg):
        """Display an error message in the UI.
        
        Args:
            loading_id: The ID of the loading item to remove
            error_msg: The error message to display
        """
        def _do_show_error():
            try:
                # Remove loading indicator if it exists
                if loading_id is not None and hasattr(self, 'tree') and self.tree is not None:
                    try:
                        self.tree.delete(loading_id)
                    except:
                        pass  # Ignore errors when removing loading indicator
                
                # Clear existing items using our safe method
                self._safe_clear_treeview()
                
                # Add error message
                if hasattr(self, 'tree') and self.tree is not None:
                    self.tree.insert('', 'end', text=error_msg, tags=('error',))
                    
            except Exception as e:
                print(f"Error showing error message: {str(e)}")
                import traceback
                traceback.print_exc()
                
        # Ensure we're on the main thread
        if threading.current_thread() is threading.main_thread():
            _do_show_error()
        else:
            if hasattr(self, 'after') and callable(self.after):
                self.after(0, _do_show_error)

    def _on_nav_up(self):
        """Handle Up button click to navigate to parent directory."""
        if self.current_path == 'Home':
            return  # Already at root
            
        # Get parent directory
        if '/' in self.current_path:
            parent_path = '/'.join(self.current_path.split('/')[:-1])
            if not parent_path:  # In case we're at a top-level directory
                parent_path = 'Home'
        else:
            parent_path = 'Home'
            
        self._load_directory(parent_path)
    
    def _update_navigation_buttons(self):
        """Update the state of navigation buttons based on current state."""
        # Enable/disable back button
        self.back_btn['state'] = 'normal' if len(self.path_history) > 1 else 'disabled'
        
        # Currently not implementing forward navigation
        self.forward_btn['state'] = 'disabled'
        
        # Enable/disable up button
        self.up_btn['state'] = 'normal' if self.current_path != 'Home' else 'disabled'
    
    # Fallback: search up the widget hierarchy
    def _get_main_window(self):
        parent = self.master
        while parent:
            # Check for any attribute that would identify the main window
            if (hasattr(parent, 'code_editor') or 
                hasattr(parent, 'debugger') or 
                hasattr(parent, 'macro_manager')):
                return parent
            parent = parent.master
            
        print("Warning: Could not find main window")
        return None

class LocalMacroEditDialog:
    """Dialog for creating/editing local macros."""
    
    def __init__(self, parent, title: str, local_macro=None):
        self.result = None
        self.local_macro = local_macro
        
        # Create dialog window
        self.dialog = tk.Toplevel(parent)
        self.dialog.title(title)
        self.dialog.geometry("600x500")
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        # Add protocol handler for window close
        self.dialog.protocol("WM_DELETE_WINDOW", self._on_cancel)
        
        # Center the dialog
        self.dialog.update_idletasks()
        x = (self.dialog.winfo_screenwidth() // 2) - (600 // 2)
        y = (self.dialog.winfo_screenheight() // 2) - (500 // 2)
        self.dialog.geometry(f"600x500+{x}+{y}")
        
        self.setup_ui()
        
        # Pre-fill if editing
        if local_macro:
            self.name_var.set(local_macro.name)
            self.description_var.set(local_macro.description)
            self.category_var.set(local_macro.category)
            self.commands_text.delete('1.0', tk.END)
            self.commands_text.insert('1.0', '\n'.join(local_macro.commands))
        
        # Wait for dialog
        try:
            self.dialog.wait_window()
        except Exception:
            # If wait_window fails, just destroy the dialog
            if self.dialog.winfo_exists():
                self.dialog.destroy()
    
    def setup_ui(self):
        """Setup the dialog UI."""
        main_frame = ttk.Frame(self.dialog)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Name
        ttk.Label(main_frame, text="Name:").grid(row=0, column=0, sticky="w", pady=(0, 5))
        self.name_var = tk.StringVar()
        name_entry = ttk.Entry(main_frame, textvariable=self.name_var, width=50)
        name_entry.grid(row=0, column=1, sticky="ew", pady=(0, 5))
        
        # Description
        ttk.Label(main_frame, text="Description:").grid(row=1, column=0, sticky="w", pady=(0, 5))
        self.description_var = tk.StringVar()
        desc_entry = ttk.Entry(main_frame, textvariable=self.description_var, width=50)
        desc_entry.grid(row=1, column=1, sticky="ew", pady=(0, 5))
        
        # Category
        ttk.Label(main_frame, text="Category:").grid(row=2, column=0, sticky="w", pady=(0, 5))
        self.category_var = tk.StringVar(value="user")
        category_combo = ttk.Combobox(
            main_frame, 
            textvariable=self.category_var,
            values=["system", "user", "homing", "tool_change", "probing", "custom", "debug"],
            state="readonly"
        )
        category_combo.grid(row=2, column=1, sticky="ew", pady=(0, 5))
        
        # Commands
        ttk.Label(main_frame, text="G-code Commands:").grid(row=3, column=0, sticky="nw", pady=(0, 5))
        
        # Text area with scrollbar
        text_frame = ttk.Frame(main_frame)
        text_frame.grid(row=3, column=1, sticky="nsew", pady=(0, 10))
        
        self.commands_text = tk.Text(
            text_frame,
            height=15,
            width=50,
            font=("Consolas", 10),
            wrap=tk.NONE
        )
        self.commands_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        text_scrollbar = ttk.Scrollbar(text_frame, orient=tk.VERTICAL)
        text_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.commands_text.config(yscrollcommand=text_scrollbar.set)
        text_scrollbar.config(command=self.commands_text.yview)
        
        # Buttons
        btn_frame = ttk.Frame(main_frame)
        btn_frame.grid(row=4, column=0, columnspan=2, sticky="ew", pady=(10, 0))
        
        ttk.Button(btn_frame, text="OK", command=self._on_ok).pack(side=tk.RIGHT, padx=(5, 0))
        ttk.Button(btn_frame, text="Cancel", command=self._on_cancel).pack(side=tk.RIGHT)
        
        # Configure grid weights
        main_frame.columnconfigure(1,
weight=1)
        main_frame.rowconfigure(3, weight=1)
        
        # Focus on name entry
        name_entry.focus()
    
    def _on_ok(self):
        """Handle OK button."""
        try:
            name = self.name_var.get().strip()
            description = self.description_var.get().strip()
            category = self.category_var.get()
            commands_text = self.commands_text.get('1.0', tk.END).strip()
            
            if not name:
                messagebox.showerror("Error", "Name is required!")
                return
            
            if not commands_text:
                messagebox.showerror("Error", "Commands are required!")
                return
            
            # Parse commands
            commands = [line.strip() for line in commands_text.split('\n') if line.strip()]
            
            self.result = (name, description, commands, category)
            if self.dialog.winfo_exists():
                self.dialog.destroy()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to process dialog: {e}")
    
    def _on_cancel(self):
        """Handle Cancel button."""
        try:
            self.result = None
            if self.dialog.winfo_exists():
                self.dialog.destroy()
        except Exception:
            pass

class MacroEditDialog:
    """Dialog for creating/editing files on the controller."""
    
    def __init__(self, parent, title: str, macro=None):
        self.result = None
        self.macro = macro
        
        # Create dialog window
        self.dialog = tk.Toplevel(parent)
        self.dialog.title(title)
        self.dialog.geometry("600x500")
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        # Add protocol handler for window close
        self.dialog.protocol("WM_DELETE_WINDOW", self._on_cancel)
        
        # Center the dialog
        self.dialog.update_idletasks()
        x = (self.dialog.winfo_screenwidth() // 2) - (600 // 2)
        y = (self.dialog.winfo_screenheight() // 2) - (500 // 2)
        self.dialog.geometry(f"600x500+{x}+{y}")
        
        self.setup_ui()
        
        # Pre-fill if editing
        if macro:
            self.name_var.set(macro.name)
            self.description_var.set(macro.description)
            self.category_var.set(macro.category)
            self.commands_text.delete('1.0', tk.END)
            self.commands_text.insert('1.0', '\n'.join(macro.commands))
        
        # Wait for dialog
        try:
            self.dialog.wait_window()
        except Exception:
            # If wait_window fails, just destroy the dialog
            if self.dialog.winfo_exists():
                self.dialog.destroy()
    
    def setup_ui(self):
        """Setup the dialog UI."""
        main_frame = ttk.Frame(self.dialog)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Name
        ttk.Label(main_frame, text="Name:").grid(row=0, column=0, sticky="w", pady=(0, 5))
        self.name_var = tk.StringVar()
        name_entry = ttk.Entry(main_frame, textvariable=self.name_var, width=50)
        name_entry.grid(row=0, column=1, sticky="ew", pady=(0, 5))
        
        # Description
        ttk.Label(main_frame, text="Description:").grid(row=1, column=0, sticky="w", pady=(0, 5))
        self.description_var = tk.StringVar()
        desc_entry = ttk.Entry(main_frame, textvariable=self.description_var, width=50)
        desc_entry.grid(row=1, column=1, sticky="ew", pady=(0, 5))
        
        # Category
        ttk.Label(main_frame, text="Category:").grid(row=2, column=0, sticky="w", pady=(0, 5))
        self.category_var = tk.StringVar(value="user")
        category_combo = ttk.Combobox(
            main_frame, 
            textvariable=self.category_var,
            values=["system", "user", "homing", "tool_change", "probing", "custom"],
            state="readonly"
        )
        category_combo.grid(row=2, column=1, sticky="ew", pady=(0, 5))
        
        # Commands
        ttk.Label(main_frame, text="G-code Commands:").grid(row=3, column=0, sticky="nw", pady=(0, 5))
        
        # Text area with scrollbar
        text_frame = ttk.Frame(main_frame)
        text_frame.grid(row=3, column=1, sticky="nsew", pady=(0, 10))
        
        self.commands_text = tk.Text(
            text_frame,
            height=15,
            width=50,
            font=("Consolas", 10),
            wrap=tk.NONE
        )
        self.commands_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        text_scrollbar = ttk.Scrollbar(text_frame, orient=tk.VERTICAL)
        text_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.commands_text.config(yscrollcommand=text_scrollbar.set)
        text_scrollbar.config(command=self.commands_text.yview)
        
        # Buttons
        btn_frame = ttk.Frame(main_frame)
        btn_frame.grid(row=4, column=0, columnspan=2, sticky="ew", pady=(10, 0))
        
        ttk.Button(btn_frame, text="OK", command=self._on_ok).pack(side=tk.RIGHT, padx=(5, 0))
        ttk.Button(btn_frame, text="Cancel", command=self._on_cancel).pack(side=tk.RIGHT)
        
        # Configure grid weights
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(3, weight=1)
        
        # Focus on name entry
        name_entry.focus()
    
    def _on_ok(self):
        """Handle OK button."""
        try:
            name = self.name_var.get().strip()
            description = self.description_var.get().strip()
            category = self.category_var.get()
            commands_text = self.commands_text.get('1.0', tk.END).strip()
            
            if not name:
                messagebox.showerror("Error", "Name is required!")
                return
            
            if not commands_text:
                messagebox.showerror("Error", "Commands are required!")
                return
            
            # Parse commands
            commands = [line.strip() for line in commands_text.split('\n') if line.strip()]
            
            self.result = (name, description, commands, category)
            if self.dialog.winfo_exists():
                self.dialog.destroy()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to process dialog: {e}")
    
    def _on_cancel(self):
        """Handle Cancel button."""
        try:
            self.result = None
            if self.dialog.winfo_exists():
                self.dialog.destroy()
        except Exception:
            pass