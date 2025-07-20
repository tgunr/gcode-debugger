#!/usr/bin/env python3
"""
Main GUI Window for G-code Debugger

The primary interface that integrates all debugger components.
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext, simpledialog
import os
from typing import Optional

from core.communication import BBCtrlCommunicator
from core.debugger import GCodeDebugger, DebugState
from core.macro_manager import MacroManager, MacroExecutor
from core.local_macro_manager import LocalMacroManager, LocalMacroExecutor
from gui.code_editor import CodeEditor
from gui.control_panel import ControlPanel, QuickCommandEntry
from gui.status_panel import StatusPanel
from gui.macro_panel import MacroPanel

import threading

class MainWindow:
    """Main window for the G-code debugger application."""
    
    def __init__(self):
        print("MainWindow: __init__ starting")
        self.root = tk.Tk()
        print("MainWindow: after tk.Tk()")
        self._main_thread = threading.get_ident()
        print("MainWindow: after threading.get_ident()")
        self.root.title("G-Code Debugger - Buildbotics Controller")
        print("MainWindow: after root.title")
        self.root.geometry("1400x900")
        print("MainWindow: after root.geometry")
        
        # Store reference to this MainWindow instance in the root for widget access
        self.root.main_window = self
        
        # Initialize configuration
        from core.config import get_config
        self.config = get_config()
        
        # Initialize core components with configured host and port
        host = self.config.get('connection.host', 'bbctrl.polymicro.net')
        port = self.config.get('connection.port', 80)
        self.communicator = BBCtrlCommunicator(
            host=host,
            port=port,
            callback_scheduler=self._thread_safe_callback
        )
        self.debugger = GCodeDebugger(self.communicator)
        
        # Initialize macro managers with configured paths
        macros_dir = self.config.get_external_macros_dir()
        local_macros_dir = self.config.get('paths.local_macros', 'local_macros')
        
        self.macro_manager = MacroManager(macros_dir)
        self.macro_executor = MacroExecutor(self.communicator)
        
        # Initialize local macro components
        self.local_macro_manager = LocalMacroManager(local_macros_dir)
        self.local_macro_executor = LocalMacroExecutor(self.communicator)
        
        # GUI components
        self.code_editor: Optional[CodeEditor] = None
        self.control_panel: Optional[ControlPanel] = None
        self.status_panel: Optional[StatusPanel] = None
        self.macro_panel: Optional[MacroPanel] = None
        self.mdi_panel: Optional[QuickCommandEntry] = None
        self.console: Optional[scrolledtext.ScrolledText] = None
        
        # State variables
        self.current_file_path = ""
        self.connection_status = tk.StringVar(value="Disconnected")
        
        # Setup GUI
        self._setup_menu()
        self._setup_toolbar()
        self._setup_main_layout()
        self._setup_status_bar()
        self._setup_callbacks()
        self._setup_keyboard_shortcuts()
        
        # Initialize connection
        # Defer WebSocket connection until after mainloop starts
        self.root.after(1000, self._attempt_connection)

    def _thread_safe_callback(self, func, *args, **kwargs):
        """Ensure func runs on the main thread."""
        if threading.get_ident() == self._main_thread:
            return func(*args, **kwargs)
        else:
            self.root.after(0, lambda: func(*args, **kwargs))
    
    def _update_macro_ui(self):
        """Safely update the macro UI components."""
        try:
            if hasattr(self, 'macro_panel') and self.macro_panel:
                print("  Refreshing macro panel...")
                # Ensure we're on the main thread
                if threading.get_ident() != self._main_thread:
                    self.root.after(0, self._update_macro_ui)
                    return
                    
                self.macro_panel.refresh_macro_lists()
                print("  Macro panel refreshed successfully")
        except Exception as e:
            print(f"ERROR in _update_macro_ui: {str(e)}")
            
    def show_preferences(self):
        """Show the preferences dialog."""
        from gui.preferences_dialog import PreferencesDialog
        
        def on_preferences_saved():
            """Callback when preferences are saved."""
            try:
                # Get new paths from config
                new_macros_dir = self.config.get('paths.external_macros')
                new_local_macros_dir = self.config.get('paths.local_macros', 'local_macros')
                
                print(f"DEBUG: Preferences saved, checking for directory changes...")
                print(f"  Current external macros dir: {getattr(self.macro_manager, 'macros_directory', 'N/A')}")
                print(f"  New external macros dir: {new_macros_dir}")
                
                # Ensure we're on the main thread for UI operations
                if threading.get_ident() != self._main_thread:
                    self.root.after(0, on_preferences_saved)
                    return
                    
                # Reinitialize macro managers if paths changed
                if hasattr(self, 'macro_manager') and new_macros_dir:
                    new_macros_dir = os.path.abspath(os.path.expanduser(str(new_macros_dir)))
                    current_dir = getattr(self.macro_manager, 'macros_directory', '')
                    
                    if new_macros_dir != current_dir:
                        print(f"  External macros directory changed to: {new_macros_dir}")
                        try:
                            # Ensure the directory exists and is writable
                            os.makedirs(new_macros_dir, exist_ok=True)
                            if not os.access(new_macros_dir, os.W_OK):
                                raise PermissionError(f"Directory is not writable: {new_macros_dir}")
                            
                            # Clean up any existing macro manager resources
                            if hasattr(self.macro_manager, 'cleanup'):
                                self.macro_manager.cleanup()
                            
                            # Reinitialize the macro manager
                            self.macro_manager = MacroManager(new_macros_dir)
                            print("  Successfully reinitialized macro manager with new directory")
                            
                            # Schedule UI update on the main thread
                            self.root.after(100, self._update_macro_ui)
                            
                        except Exception as e:
                            print(f"ERROR: Failed to reinitialize macro manager: {str(e)}")
                            messagebox.showerror(
                                "Error",
                                f"Failed to set external macros directory to {new_macros_dir}:\n\n{str(e)}\n\n"
                                "Please check that the directory exists and is writable."
                            )
                            return  # Don't proceed with UI updates if there was an error
                
                # Handle local macro directory changes
                if hasattr(self, 'local_macro_manager') and new_local_macros_dir:
                    new_local_macros_dir = os.path.abspath(os.path.expanduser(str(new_local_macros_dir)))
                    current_local_dir = getattr(self.local_macro_manager, 'macros_directory', '')
                    
                    if new_local_macros_dir != current_local_dir:
                        print(f"  Local macros directory changed to: {new_local_macros_dir}")
                        try:
                            # Clean up any existing local macro manager resources
                            if hasattr(self.local_macro_manager, 'cleanup'):
                                self.local_macro_manager.cleanup()
                                
                            os.makedirs(new_local_macros_dir, exist_ok=True)
                            self.local_macro_manager = LocalMacroManager(new_local_macros_dir)
                            
                            # Schedule UI update on the main thread
                            self.root.after(100, self._update_macro_ui)
                            
                        except Exception as e:
                            print(f"WARNING: Failed to reinitialize local macro manager: {str(e)}")
                
                # Refresh UI if not already handled by directory changes
                if not (hasattr(self, 'macro_manager') and new_macros_dir):
                    self.root.after(100, self._update_macro_ui)
                    
            except Exception as e:
                print(f"ERROR in on_preferences_saved: {str(e)}")
                messagebox.showerror(
                    "Error",
                    f"An error occurred while applying preferences:\n\n{str(e)}"
                )
        
        try:
            # Create and show the preferences dialog
            print("DEBUG: Showing preferences dialog...")
            dialog = PreferencesDialog(self.root, self.config, on_save=on_preferences_saved)
            dialog.show()
            print("DEBUG: Preferences dialog closed")
        except Exception as e:
            print(f"ERROR: Failed to show preferences dialog: {str(e)}")
            messagebox.showerror("Error", f"Failed to open preferences: {str(e)}")
    
    def _setup_menu(self):
        """Setup the menu bar."""
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)
        
        # File menu
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="Open G-code File...", command=self.open_file, accelerator="Ctrl+O")
        file_menu.add_command(label="Reload File", command=self.reload_file, accelerator="F5")
        file_menu.add_separator()
        file_menu.add_command(label="Preferences...", command=self.show_preferences, accelerator="Ctrl+,")
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.exit_application, accelerator="Ctrl+Q")
        
        # Debug menu
        debug_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Debug", menu=debug_menu)
        debug_menu.add_command(label="Continue", command=self.continue_execution, accelerator="F5")
        debug_menu.add_command(label="Step Over", command=self.step_over, accelerator="F10")
        debug_menu.add_command(label="Step To Line...", command=self.step_to_line_dialog, accelerator="Ctrl+F10")
        debug_menu.add_command(label="Go Back", command=self.go_back, accelerator="Shift+F10")
        debug_menu.add_separator()
        debug_menu.add_command(label="Skip Line", command=self.skip_line, accelerator="Shift+F11")
        debug_menu.add_command(label="Skip To Line...", command=self.skip_to_line_dialog, accelerator="Ctrl+Shift+F10")
        debug_menu.add_separator()
        debug_menu.add_command(label="Toggle Breakpoint", command=self.toggle_breakpoint, accelerator="F9")
        debug_menu.add_command(label="Clear All Breakpoints", command=self.clear_all_breakpoints)
        debug_menu.add_separator()
        debug_menu.add_command(label="Pause", command=self.pause_execution, accelerator="Ctrl+Break")
        debug_menu.add_command(label="Stop", command=self.stop_execution, accelerator="Shift+F5")
        debug_menu.add_command(label="Emergency Stop", command=self.emergency_stop, accelerator="Esc")
        
        # Connection menu
        connection_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Connection", menu=connection_menu)
        connection_menu.add_command(label="Connect", command=self.connect_to_controller)
        connection_menu.add_command(label="Disconnect", command=self.disconnect_from_controller)
        connection_menu.add_command(label="Test Connection", command=self.test_connection)
        
        # Help menu
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Help", menu=help_menu)
        help_menu.add_command(label="Keyboard Shortcuts", command=self.show_shortcuts_help)
        help_menu.add_command(label="About", command=self.show_about)
        
        # Add status indicator and E-Stop to the right side of the menu bar
        
        # Execution status (right-aligned)
        self.status_var = tk.StringVar(value="STOPPED")
        self.status_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Status: ", menu=self.status_menu, state='disabled')
        
        # Add a label to the menu bar for status display
        self.status_label = tk.Label(
            menubar,
            textvariable=self.status_var,
            font=("Arial", 10, "bold"),
            padx=10
        )
        self.status_label.pack(side=tk.RIGHT)
        
        # E-Stop button (far right)
        menubar.add_command(
            label="🚨 E-STOP", 
            command=self.emergency_stop, 
            activebackground="red",
            activeforeground="white",
            background="red",
            foreground="white",
            font=("Arial", 10, "bold"),
            compound=tk.RIGHT
        )
    
    def save_current_file(self):
        """Save the current file or macro."""
        if not hasattr(self, 'macro_panel') or not hasattr(self, 'code_editor'):
            return
            
        # Check if we're currently viewing a macro
        current_tab = self.macro_panel.notebook.tab(self.macro_panel.notebook.select(), "text").lower()
        if 'local' in current_tab or 'external' in current_tab:
            # Save macro
            if hasattr(self.macro_panel, '_save_current_macro'):
                if self.macro_panel._save_current_macro(self):
                    self._log_message("Macro saved successfully")
                    # Clear the modified flag after successful save
                    if hasattr(self.code_editor, 'clear_modified_flag'):
                        self.code_editor.clear_modified_flag()
                else:
                    self._log_message("Failed to save macro", color="red")
        else:
            # TODO: Implement file save for non-macro files
            self._log_message("Save not implemented for this file type", color="orange")
    
    def _setup_toolbar(self):
        """Setup the toolbar."""
        toolbar = ttk.Frame(self.root)
        toolbar.pack(side=tk.TOP, fill=tk.X, padx=2, pady=2)
        
        # File operations
        ttk.Button(toolbar, text="📁 Open", command=self.open_file).pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar, text="💾 Save", command=self.save_current_file).pack(side=tk.LEFT, padx=2)
        ttk.Separator(toolbar, orient=tk.VERTICAL).pack(side=tk.LEFT, padx=5, fill=tk.Y)
        
        # Debug controls
        ttk.Button(toolbar, text="▶️ Continue", command=self.continue_execution).pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar, text="⏸️ Pause", command=self.pause_execution).pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar, text="⏭️ Step", command=self.step_over).pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar, text="⏪ Back", command=self.go_back).pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar, text="🛑 Stop", command=self.stop_execution).pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar, text="🚨 E-Stop", command=self.emergency_stop, 
                  style="Emergency.TButton").pack(side=tk.LEFT, padx=2)
        
        ttk.Separator(toolbar, orient=tk.VERTICAL).pack(side=tk.LEFT, padx=5, fill=tk.Y)
        
        # Connection status
        ttk.Label(toolbar, text="Status:").pack(side=tk.RIGHT, padx=2)
        status_label = ttk.Label(toolbar, textvariable=self.connection_status)
        status_label.pack(side=tk.RIGHT, padx=2)
        
        # Configure emergency stop button style
        style = ttk.Style()
        style.configure("Emergency.TButton", foreground="red")
    
    def _setup_main_layout(self):
        """Setup the main application layout."""
        # Create main paned window
        main_paned = ttk.PanedWindow(self.root, orient=tk.HORIZONTAL)
        main_paned.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Left panel (code editor)
        left_frame = ttk.Frame(main_paned)
        main_paned.add(left_frame, weight=3)
        
        # Right panel (controls and macros)
        right_paned = ttk.PanedWindow(main_paned, orient=tk.VERTICAL)
        main_paned.add(right_paned, weight=3)  # Increased weight to give more space to the right panel
        
        # Setup left panel (code editor)
        self.code_editor = CodeEditor(left_frame)
        self.code_editor.pack(fill=tk.BOTH, expand=True)
        
        # Setup right panel top (controls only - status is in menu bar)
        top_right_frame = ttk.Frame(right_paned)
        right_paned.add(top_right_frame, weight=0)  # Minimal space for controls
               
        # Control panel (breakpoints only)
        self.control_panel = ControlPanel(top_right_frame)
        self.control_panel.pack(fill=tk.X, pady=(0, 2))  # Reduced padding
        
        # Setup right panel middle (macros) - now with more space
        macro_frame = ttk.Frame(right_paned)
        right_paned.add(macro_frame, weight=4)  # Increased weight to give more space to macros
        
        self.macro_panel = MacroPanel(macro_frame, self.macro_manager, self.local_macro_manager)
        self.macro_panel.pack(fill=tk.BOTH, expand=True)
        
        # Setup right panel bottom (MDI + console)
        console_container = ttk.Frame(right_paned)
        right_paned.add(console_container, weight=1)  # Keep console at minimum height
        
        # MDI panel (Manual Data Input) - now directly above console
        mdi_frame = ttk.LabelFrame(console_container, text="Manual Data Input (MDI)")
        mdi_frame.pack(fill=tk.X, padx=5, pady=(5, 2))
        
        self.mdi_panel = QuickCommandEntry(mdi_frame)
        self.mdi_panel.pack(fill=tk.X, padx=5, pady=5)
        
        # Console output - now directly below MDI
        console_frame = ttk.LabelFrame(console_container, text="Console Output")
        console_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=(2, 5))
        
        self.console = scrolledtext.ScrolledText(
            console_frame,
            height=8,
            font=("Consolas", 10),
            bg="black",
            fg="green",
            insertbackground="green"
        )
        self.console.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
    
    def _setup_status_bar(self):
        """Setup the status bar."""
        status_bar = ttk.Frame(self.root)
        status_bar.pack(side=tk.BOTTOM, fill=tk.X)
        
        # Status information
        self.file_status = tk.StringVar(value="No file loaded")
        ttk.Label(status_bar, textvariable=self.file_status).pack(side=tk.LEFT, padx=5)
        
        # Progress information
        self.progress_status = tk.StringVar(value="")
        ttk.Label(status_bar, textvariable=self.progress_status).pack(side=tk.RIGHT, padx=5)
    
    def _setup_callbacks(self):
        """Setup callbacks for core components."""
        # Communication callbacks
        self.communicator.set_callbacks(
            state_callback=self._on_machine_state_changed,
            message_callback=self._on_communication_message,
            error_callback=self._on_communication_error
        )
        
        # Debugger callbacks
        self.debugger.set_callbacks(
            line_changed=self._on_current_line_changed,
            state_changed=self._on_debug_state_changed,
            error=self._on_debugger_error
        )
        
        # Code editor callbacks
        if self.code_editor:
            self.code_editor.set_breakpoint_callback(self._on_breakpoint_toggled)
            self.code_editor.set_line_edit_callback(self._on_line_edited)
        
        # Macro executor callbacks
        self.macro_executor.set_callbacks(
            progress=self._on_macro_progress,
            completion=self._on_macro_completed,
            error=self._on_macro_error
        )
        
        # Local macro executor callbacks
        self.local_macro_executor.set_callbacks(
            progress=self._on_local_macro_progress,
            completion=self._on_local_macro_completed,
            error=self._on_local_macro_error
        )
    
    def _setup_keyboard_shortcuts(self):
        """Setup keyboard shortcuts."""
        self.root.bind('<Control-o>', lambda e: self.open_file())
        self.root.bind('<Control-s>', lambda e: self.save_current_file())
        self.root.bind('<F5>', lambda e: self.continue_execution())
        self.root.bind('<F9>', lambda e: self.toggle_breakpoint())
        self.root.bind('<F10>', lambda e: self.step_over())
        self.root.bind('<Shift-F10>', lambda e: self.go_back())
        self.root.bind('<Control-F10>', lambda e: self.step_to_line_dialog())
        self.root.bind('<Shift-F11>', lambda e: self.skip_line())
        self.root.bind('<Control-Shift-F10>', lambda e: self.skip_to_line_dialog())
        self.root.bind('<Escape>', lambda e: self.emergency_stop())
        self.root.bind('<Control-q>', lambda e: self.exit_application())
    
    def _attempt_connection(self):
        """Attempt to connect to the controller on startup."""
        self._log_message("Attempting to connect to controller...", "yellow")
        self.communicator.connect_websocket()
    
    # File operations
    def open_file(self):
        """Open a G-code file."""
        file_path = filedialog.askopenfilename(
            title="Open G-code File",
            filetypes=[
                ("G-code files", "*.nc *.gcode *.tap *.cnc *.ngc *.gc"),
                ("All files", "*.*")
            ]
        )
        
        if file_path:
            try:
                if self.debugger.load_file(file_path):
                    self.current_file_path = file_path
                    self.file_status.set(f"Loaded: {os.path.basename(file_path)}")
                    
                    # Update code editor
                    if self.code_editor:
                        self.code_editor.load_gcode(self.debugger.parser)
                    
                    self._log_message(f"Loaded G-code file: {file_path}")
                    self._update_progress_display()
                else:
                    messagebox.showerror("Error", "Failed to load G-code file")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to open file: {e}")
    
    def reload_file(self):
        """Reload the current file."""
        if self.current_file_path:
            if self.debugger.load_file(self.current_file_path):
                if self.code_editor:
                    self.code_editor.load_gcode(self.debugger.parser)
                self._log_message("File reloaded")
                self._update_progress_display()
    
    # Debug operations
    def continue_execution(self):
        """Continue execution from current line."""
        if self.debugger.continue_execution():
            self._log_message("Continuing execution...")
    
    def step_over(self):
        """Execute current line and move to next."""
        if self.debugger.step_over():
            self._log_message("Stepped to next line")
    
    def step_to_line_dialog(self):
        """Show dialog to step to specific line."""
        line_num = simpledialog.askinteger(
            "Step to Line", 
            "Enter line number:",
            minvalue=1
        )
        if line_num:
            if self.debugger.step_to_line(line_num):
                self._log_message(f"Stepping to line {line_num}...")
    
    def skip_line(self):
        """Skip current line without executing."""
        if self.debugger.skip_line():
            self._log_message("Skipped current line")
    
    def skip_to_line_dialog(self):
        """Show dialog to skip to specific line."""
        line_num = simpledialog.askinteger(
            "Skip to Line", 
            "Enter line number:",
            minvalue=1
        )
        if line_num:
            if self.debugger.skip_to_line(line_num):
                self._log_message(f"Skipped to line {line_num}")
    
    def go_back(self):
        """Go back to previous execution point."""
        if self.debugger.go_back():
            self._log_message("Went back to previous line")
    
    def toggle_breakpoint(self):
        """Toggle breakpoint at current line."""
        if self.code_editor:
            current_line = self.code_editor.get_current_line_number()
            if self.debugger.toggle_breakpoint(current_line):
                self._log_message(f"Toggled breakpoint at line {current_line}")
                self.code_editor.update_breakpoints(self.debugger.breakpoints)
    
    def clear_all_breakpoints(self):
        """Clear all breakpoints."""
        self.debugger.breakpoints.clear()
        if self.code_editor:
            self.code_editor.update_breakpoints(set())
        self._log_message("Cleared all breakpoints")
    
    def pause_execution(self):
        """Pause current execution."""
        if self.debugger.pause_execution():
            self._log_message("Execution paused")
    
    def stop_execution(self):
        """Stop current execution."""
        if self.debugger.stop_execution():
            self._log_message("Execution stopped")
    
    def emergency_stop(self):
        """Execute emergency stop."""
        if self.debugger.emergency_stop():
            self._log_message("EMERGENCY STOP ACTIVATED!")
            messagebox.showwarning("Emergency Stop", "Emergency stop has been activated!")

    # Connection operations
    def _attempt_connection(self):
        """Attempt to connect to the controller on startup and sync macros."""
        try:
            if self.communicator.connect_websocket():
                self.connection_status.set("Connected")
                self._log_message("Successfully connected to controller")
                
                # Request initial state
                state = self.communicator.get_state()
                if state:
                    self._on_machine_state_changed(state)
                
                # Start position updates
                self._start_position_updates()
                
                # Sync macros from controller in a background thread to avoid blocking the UI
                def sync_macros():
                    try:
                        self._thread_safe_callback(self._log_message,
                                                   "Starting macro synchronization from controller...",
                                                   "blue")
                        if self.macro_manager.sync_from_controller(self.communicator):
                            self._thread_safe_callback(self._log_message,
                                                       "Macro synchronization completed successfully",
                                                       "green")
                            # Refresh macro panel if it exists
                            if hasattr(self, 'macro_panel') and self.macro_panel:
                                self.root.after(0, self.macro_panel.refresh_macro_lists)
                        else:
                            self._thread_safe_callback(self._log_message,
                                                       "Warning: Macro synchronization completed with issues",
                                                       "orange")
                    except Exception as e:
                        self._thread_safe_callback(self._log_message,
                                                   f"Error during macro synchronization: {e}",
                                                   "red")
                
                # Start macro sync in a separate thread
                threading.Thread(target=sync_macros, daemon=True).start()
                
            else:
                self.connection_status.set("Connection failed")
                self._log_message("Failed to connect to controller", "red")
        except Exception as e:
            self.connection_status.set("Connection error")
            self._log_message(f"Connection error: {e}", "red")

    def _start_position_updates(self):
        """Start periodic position updates."""
        # Initial update
        self._update_position_display()
        # Schedule periodic updates (every 100ms)
        self.root.after(100, self._periodic_position_update)

    def _periodic_position_update(self):
        """Periodically update the position display."""
        if self.communicator.connected:
            self._update_position_display()
        # Schedule next update
        self.root.after(100, self._periodic_position_update)

    def _update_position_display(self):
        """Update the position display if control panel exists."""
        if hasattr(self, 'control_panel') and self.control_panel:
            state = self.communicator.last_state
            self.control_panel.update_position_display(
                state.get('xp', 0),  # Using xp, yp, zp as per API spec
                state.get('yp', 0),
                state.get('zp', 0)
            )

    def get_current_position(self):
        """Get the current machine position from the communicator.
        
        Returns:
            tuple: (x, y, z) coordinates from the controller
        """
        state = self.communicator.last_state
        return (
            state.get('xp', 0),  # Using xp, yp, zp as per API spec
            state.get('yp', 0),
            state.get('zp', 0)
        )
    
    def connect_to_controller(self):
        """Connect to the controller."""
        try:
            if self.communicator.connect_websocket():
                self.connection_status.set("Connected")
                self._log_message("Connected to controller")
                self._start_position_updates()
                return True
            else:
                self.connection_status.set("Connection failed")
                self._log_message("Failed to connect to controller", "red")
                return False
        except Exception as e:
            self.connection_status.set("Connection error")
            self._log_message(f"Connection error: {e}", "red")
            return False
    
    def disconnect_from_controller(self):
        """Disconnect from the controller."""
        try:
            self.communicator.close()
            self.connection_status.set("Disconnected")
            self._log_message("Disconnected from controller")
            return True
        except Exception as e:
            self._log_message(f"Error disconnecting: {e}", "red")
            return False
    
    def test_connection(self):
        """Test the controller connection."""
        try:
            state = self.communicator.get_state()
            if state:
                self._log_message("Connection test successful")
                return True
            else:
                messagebox.showerror("Connection Test", "Connection failed!")
                return False
        except Exception as e:
            messagebox.showerror("Connection Test", f"Error: {e}")
            return False

    # Callback handlers
    def _on_machine_state_changed(self, state):
        """Handle machine state and connection state changes.
        
        Args:
            state: Dictionary containing the machine state or connection state.
                  For connection state, expects {'connected': bool}.
                  For machine state, expects {'xx': state_str, ...}.
        """
        def update():
            try:
                if not self.root or not self.root.winfo_exists():
                    print("DEBUG: Root window no longer exists, skipping state update")
                    return
                
                # Handle connection state updates
                if isinstance(state, dict) and 'connected' in state:
                    is_connected = state['connected']
                    status_text = "Connected" if is_connected else "Disconnected"
                    self.connection_status.set(status_text)
                    
                    # Log the connection state change
                    color = "green" if is_connected else "red"
                    self._log_message(f"Connection: {status_text}", color)
                    
                    # If we just connected, update the position display
                    if is_connected and hasattr(self, '_update_position_display'):
                        self._update_position_display()
                    
                    return  # Skip machine state processing for connection updates
                
                # Handle machine state updates (original behavior)
                if isinstance(state, dict):
                    state_str = state.get('xx', 'Unknown')  # 'xx' is the state key in the API
                    self._log_message(f"Machine state: {state_str}", "blue")
                    
                    # Update position display when state changes
                    if hasattr(self, '_update_position_display'):
                        self._update_position_display()
                
            except Exception as e:
                print(f"ERROR in _on_machine_state_changed: {e}")
                import traceback
                traceback.print_exc()
        
        # Ensure we're on the main thread
        if self._main_thread == threading.get_ident():
            update()
        else:
            self._thread_safe_callback(update)

    def _on_communication_message(self, message, color="green"):
        """Handle communication messages.
        
        Args:
            message: The message to display
            color: Color for the message (default: "green")
        """
        def log_message():
            try:
                # Check if we can safely access the root window
                try:
                    if not hasattr(self, 'root') or not self.root:
                        print("DEBUG: Root window not available")
                        return
                        
                    # Check if the root window still exists and is valid
                    try:
                        if not self.root.winfo_exists():
                            print("DEBUG: Root window no longer exists")
                            return
                    except Exception as e:
                        print(f"DEBUG: Error checking root window: {e}")
                        return
                except Exception as e:
                    print(f"DEBUG: Error in root window check: {e}")
                    return
                
                # Safely handle the message
                try:
                    if message is None:
                        print("DEBUG: Received None message")
                        return
                        
                    msg_str = str(message)  # Convert to string safely
                    if not msg_str.strip():
                        print("DEBUG: Received empty message")
                        return
                    
                    # Log the raw message for debugging
                    print(f"DEBUG: Processing message: {msg_str[:200]}{'...' if len(msg_str) > 200 else ''}")
                    
                    # Enhanced handling for different message types
                    if not hasattr(self, '_log_message'):
                        print("ERROR: _log_message method not available")
                        return
                        
                    try:
                        if "RAW WS MESSAGE:" in msg_str:
                            self._log_message(msg_str, "cyan")
                        elif "COMMAND RESPONSE:" in msg_str:
                            self._log_message(msg_str, "yellow")
                        elif "NON-JSON MESSAGE:" in msg_str:
                            self._log_message(msg_str, "white")
                        elif msg_str.startswith("[") and "]" in msg_str:  # Check for [TAG] format
                            try:
                                tag = msg_str[1:msg_str.find("]")].upper()
                                if tag == "MSG":
                                    self._log_message(msg_str, "yellow")
                                elif tag == "DEBUG":
                                    self._log_message(msg_str, "magenta")
                                else:
                                    self._log_message(f"COMM: {msg_str}", color)
                            except Exception as e:
                                print(f"WARNING: Error processing tagged message: {e}")
                                self._log_message(f"COMM: {msg_str}", color)
                        else:
                            self._log_message(f"COMM: {msg_str}", color)
                    except Exception as e:
                        print(f"ERROR in message processing: {e}")
                        
                except Exception as e:
                    error_msg = f"Error converting message to string: {str(e)}"
                    print(f"ERROR: {error_msg}")
                    if hasattr(self, '_log_message'):
                        self._log_message(f"ERROR: {error_msg}", "red")
                    
            except Exception as e:
                error_msg = f"Critical error in log_message: {str(e)}"
                print(f"CRITICAL ERROR: {error_msg}")
                import traceback
                traceback.print_exc()
        
        # Ensure thread safety
        try:
            current_thread = threading.get_ident()
            if current_thread == self._main_thread:
                log_message()
            else:
                # Use after() to schedule on the main thread if we're not on it
                try:
                    if hasattr(self, 'root') and self.root and hasattr(self.root, 'after'):
                        self.root.after(0, log_message)
                    else:
                        print("WARNING: Cannot schedule log_message - root window not ready")
                except Exception as e:
                    print(f"ERROR scheduling log_message: {e}")
        except Exception as e:
            print(f"CRITICAL: Error in thread safety check: {e}")
    
    def _on_communication_error(self, error):
        """Handle communication errors.
        
        Args:
            error: The error message to display
        """
        def log_error():
            try:
                if not self.root or not self.root.winfo_exists():
                    print(f"DEBUG: Root window no longer exists, dropping error: {error}")
                    return
                self._log_message(f"ERROR: {error}", "red")
            except Exception as e:
                print(f"ERROR in _on_communication_error: {e}")
                import traceback
                traceback.print_exc()
        
        # Ensure we're on the main thread
        if self._main_thread == threading.get_ident():
            log_error()
        else:
            self._thread_safe_callback(log_error)
    
    def _on_current_line_changed(self, line_number):
        """Handle current line changes."""
        def update():
            if self.code_editor:
                self.code_editor.highlight_current_line(line_number)
            self._update_progress_display()
        self._thread_safe_callback(update)
    
    def _on_debug_state_changed(self, debug_state):
        """Handle debug state changes."""
        def update():
            if self.control_panel:
                self.control_panel.update_debug_state(debug_state)
            
            # Update status display in menu bar
            state_info = {
                DebugState.STOPPED: ("STOPPED", "black"),
                DebugState.RUNNING: ("RUNNING", "green"),
                DebugState.PAUSED: ("PAUSED", "orange"),
                DebugState.STEPPING: ("STEPPING", "blue")
            }
            
            status_text, color = state_info.get(debug_state, ("UNKNOWN", "gray"))
            if hasattr(self, 'status_var') and hasattr(self, 'status_label'):
                self.status_var.set(status_text)
                self.status_label.config(foreground=color)
            
            self._log_message(f"Debug state: {debug_state.value}")
        
        self._thread_safe_callback(update)
    
    def _on_debugger_error(self, error):
        """Handle debugger errors."""
        def update():
            self._log_message(f"DEBUGGER ERROR: {error}", "red")
            messagebox.showerror("Debugger Error", error)
        self._thread_safe_callback(update)
    
    def _on_breakpoint_toggled(self, line_number):
        """Handle breakpoint toggle from code editor."""
        self._thread_safe_callback(self.debugger.toggle_breakpoint, line_number)
    
    def _on_line_edited(self, line_number, new_content):
        """Handle line editing from code editor."""
        def update():
            if self.debugger.parser.modify_line(line_number, new_content):
                self._log_message(f"Modified line {line_number}")
        self._thread_safe_callback(update)
    
    def _on_macro_progress(self, progress, command):
        """Handle macro execution progress."""
        self._thread_safe_callback(self._log_message, f"Macro progress: {progress:.1f}% - {command}")
    
    def _on_macro_completed(self, macro_name):
        """Handle macro completion."""
        self._thread_safe_callback(self._log_message, f"Macro '{macro_name}' completed")
    
    def _on_macro_error(self, error):
        """Handle local macro execution errors."""
        self._log_message(f"Macro error: {error}", color="red")
        self._update_progress_display()
        
    def send_gcode_command(self, command: str) -> bool:
        """Send a G-code command to the controller via MDI.
        
        Args:
            command: The G-code command to send
            
        Returns:
            bool: True if command was sent successfully, False otherwise
        """
        if not command or not command.strip():
            return False
            
        try:
            # Send the command using the communicator's MDI interface
            self._log_message(f"Sending MDI command: {command}", color="blue")
            success = self.communicator.send_mdi_command(command)
            if not success:
                self._log_message(f"Failed to send command: {command}", color="red")
            return success
        except Exception as e:
            self._log_message(f"Error sending command: {e}", color="red")
            return False
    
    def _on_local_macro_progress(self, progress, command):
        """Handle local macro execution progress."""
        self._thread_safe_callback(self._log_message, f"Local macro progress: {progress:.1f}% - {command}")
    
    def _on_local_macro_completed(self, macro_name):
        """Handle local macro completion."""
        self._thread_safe_callback(self._log_message, f"Local macro '{macro_name}' completed")
        # Re-enable the stop button in macro panel
        if self.macro_panel:
            self.macro_panel.local_stop_btn.config(state=tk.DISABLED)
    
    def _on_local_macro_error(self, error):
        """Handle local macro execution errors."""
        self._thread_safe_callback(self._log_message, f"LOCAL MACRO ERROR: {error}", "red")
        # Re-enable the stop button in macro panel
        if self.macro_panel:
            self.macro_panel.local_stop_btn.config(state=tk.DISABLED)
    
    # Utility methods
    def _log_message(self, message, color="green"):
        """Log a message to the console with color support."""
        if self.console:
            self.console.configure(state=tk.NORMAL)
            
            # Configure color tags if not already done
            if not hasattr(self, '_color_tags_configured'):
                self.console.tag_configure("green", foreground="green")
                self.console.tag_configure("red", foreground="red")
                self.console.tag_configure("yellow", foreground="yellow")
                self.console.tag_configure("cyan", foreground="cyan")
                self.console.tag_configure("white", foreground="white")
                self.console.tag_configure("magenta", foreground="magenta")
                self._color_tags_configured = True
            
            # Insert message with color
            start_pos = self.console.index(tk.END)
            self.console.insert(tk.END, f"> {message}\n")
            end_pos = self.console.index(tk.END)
            
            # Apply color tag to the inserted text
            self.console.tag_add(color, start_pos, end_pos)
            
            self.console.configure(state=tk.DISABLED)
            self.console.see(tk.END)
    
    def _update_progress_display(self):
        """Update the progress display."""
        stats = self.debugger.get_statistics()
        if stats['total_executable'] > 0:
            progress_text = (f"Line {stats['current_line']} / "
                           f"{stats['total_executable']} "
                           f"({stats['progress_percent']:.1f}%)")
            self.progress_status.set(progress_text)
        else:
            self.progress_status.set("")
    
    # Help and utility dialogs
    def show_shortcuts_help(self):
        """Show keyboard shortcuts help."""
        shortcuts = """
Keyboard Shortcuts:

File Operations:
  Ctrl+O        Open G-code file
  F5            Reload file

Debug Operations:
  F5            Continue execution
  F10           Step over (next line)
  Shift+F10     Go back
  Ctrl+F10      Step to line...
  Shift+F11     Skip line
  Ctrl+Shift+F10 Skip to line...
  F9            Toggle breakpoint
  Ctrl+Break    Pause execution
  Shift+F5      Stop execution
  Esc           Emergency stop

General:
  Ctrl+Q        Exit application
        """
        messagebox.showinfo("Keyboard Shortcuts", shortcuts)
    
    def show_about(self):
        """Show about dialog."""
        about_text = """
G-Code Debugger v1.0.0

A comprehensive debugging tool for G-code files
with the Buildbotics Controller.

Features:
• Step-by-step execution
• Breakpoints and line editing
• State restoration (go back)
• Macro system
• Real-time machine monitoring

Built for Buildbotics LLC
        """
        messagebox.showinfo("About G-Code Debugger", about_text)
    
    def exit_application(self):
        """Exit the application."""
        # Cleanup
        if self.communicator:
            self.communicator.close()
        
        self.root.quit()
        self.root.destroy()
    
    def run(self):
        """Run the application."""
        print("Mainloop starting")
        self.root.mainloop()
        print("Mainloop ended")

if __name__ == "__main__":
    app = MainWindow()
    app.run()