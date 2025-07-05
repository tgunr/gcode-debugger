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
        
        # Initialize core components
        self.communicator = BBCtrlCommunicator(callback_scheduler=self._thread_safe_callback)
        self.debugger = GCodeDebugger(self.communicator)
        self.macro_manager = MacroManager("macros")
        self.macro_executor = MacroExecutor(self.communicator)
        
        # Initialize local macro components
        self.local_macro_manager = LocalMacroManager("local_macros")
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
    
    def _setup_toolbar(self):
        """Setup the toolbar."""
        toolbar = ttk.Frame(self.root)
        toolbar.pack(side=tk.TOP, fill=tk.X, padx=2, pady=2)
        
        # File operations
        ttk.Button(toolbar, text="📁 Open", command=self.open_file).pack(side=tk.LEFT, padx=2)
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
        self.control_panel.pack(fill=tk.X, pady=(0, 5))
        
        # Setup right panel middle (macros) - now with more space
        macro_frame = ttk.Frame(right_paned)
        right_paned.add(macro_frame, weight=2)  # Increased weight to give more space to macros
        
        self.macro_panel = MacroPanel(macro_frame, self.macro_manager, self.local_macro_manager)
        self.macro_panel.pack(fill=tk.BOTH, expand=True)
        
        # Setup right panel bottom (MDI + console)
        console_container = ttk.Frame(right_paned)
        right_paned.add(console_container, weight=1)
        
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
        if self.communicator.connect_websocket():
            self.connection_status.set("Connected")
            self._log_message("Connected to bbctrl controller")
        else:
            self.connection_status.set("Disconnected")
            self._log_message("Failed to connect to bbctrl controller")
    
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
    def connect_to_controller(self):
        """Connect to the controller."""
        if self.communicator.connect_websocket():
            self.connection_status.set("Connected")
            self._log_message("Connected to controller")
        else:
            self.connection_status.set("Disconnected")
            messagebox.showerror("Connection Error", "Failed to connect to controller")
    
    def disconnect_from_controller(self):
        """Disconnect from the controller."""
        self.communicator.close()
        self.connection_status.set("Disconnected")
        self._log_message("Disconnected from controller")
    
    def test_connection(self):
        """Test the controller connection."""
        state = self.communicator.get_state()
        if state:
            messagebox.showinfo("Connection Test", "Connection successful!")
            self._log_message("Connection test successful")
        else:
            messagebox.showerror("Connection Test", "Connection failed!")
    
    def send_gcode_command(self, command):
        """Send a G-code command to the controller via MDI."""
        # Ensure connection for MDI command (reconnect if needed)
        if not self.communicator.connected:
            self._log_message("Reconnecting for MDI command...")
            if not self.communicator.connect_websocket():
                self._log_message("Failed to connect for MDI command", "red")
                return False
        
        # Send command
        result = self.communicator.send_mdi_command(command)
        
        if result:
            self._log_message(f"MDI: {command}")
            return True
        else:
            self._log_message(f"Failed to send MDI command: {command}", "red")
            return False
    
    def execute_local_macro(self, macro_name):
        """Execute a local macro by name."""
        try:
            local_macro = self.local_macro_manager.get_local_macro(macro_name)
            if local_macro:
                self._log_message(f"Executing local macro: {macro_name}")
                self.local_macro_executor.execute_local_macro(local_macro)
                return True
            else:
                self._log_message(f"Local macro not found: {macro_name}", "red")
                return False
        except Exception as e:
            self._log_message(f"Failed to execute local macro '{macro_name}': {e}", "red")
            return False
    
    # Callback handlers
    def _on_machine_state_changed(self, state):
        """Handle machine state changes."""
        def update():
            if self.status_panel:
                self.status_panel.update_state(state)
        self._thread_safe_callback(update)
    
    def _on_communication_message(self, message, color="green"):
        """Handle communication messages."""
        # Enhanced handling for different message types
        if "RAW WS MESSAGE:" in message:
            self._thread_safe_callback(self._log_message, message, "cyan")
        elif "COMMAND RESPONSE:" in message:
            self._thread_safe_callback(self._log_message, message, "yellow")
        elif "NON-JSON MESSAGE:" in message:
            self._thread_safe_callback(self._log_message, message, "white")
        elif message.startswith("[MSG]"):
            # MSG command output - display prominently
            self._thread_safe_callback(self._log_message, message, "yellow")
        elif message.startswith("[DEBUG]"):
            # DEBUG command output - display prominently
            self._thread_safe_callback(self._log_message, message, "magenta")
        else:
            self._thread_safe_callback(self._log_message, f"COMM: {message}", color)
    
    def _on_communication_error(self, error):
        """Handle communication errors."""
        self._thread_safe_callback(self._log_message, f"ERROR: {error}", "red")
    
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
        """Handle macro execution errors."""
        self._thread_safe_callback(self._log_message, f"MACRO ERROR: {error}", "red")
    
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