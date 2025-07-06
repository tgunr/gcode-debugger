#!/usr/bin/env python3
"""
Control Panel for G-code Debugger

Provides debug control buttons and execution management.
"""

import tkinter as tk
from tkinter import ttk, simpledialog
from core.debugger import DebugState

class ControlPanel(ttk.LabelFrame):
    """Control panel with debug operation buttons."""
    
    def __init__(self, parent):
        super().__init__(parent, text="Debug Controls")
        
        self.debug_state = DebugState.STOPPED
        self.setup_ui()
    
    def setup_ui(self):
        """Setup the control panel UI with breakpoint controls and status."""
        # Create main container
        container = ttk.Frame(self)
        container.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Breakpoint controls
        bp_frame = ttk.LabelFrame(container, text="Breakpoints")
        bp_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Breakpoint buttons row
        bp_btn_frame = ttk.Frame(bp_frame)
        bp_btn_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # Toggle breakpoint button
        self.toggle_bp_btn = ttk.Button(
            bp_btn_frame, 
            text="🔴 Toggle Breakpoint (F9)", 
            command=self._on_toggle_breakpoint,
            width=20
        )
        self.toggle_bp_btn.pack(side=tk.LEFT, padx=(0, 5))
        
        # Clear breakpoints button
        self.clear_bp_btn = ttk.Button(
            bp_btn_frame, 
            text="🧹 Clear All Breakpoints", 
            command=self._on_clear_breakpoints,
            width=20
        )
        self.clear_bp_btn.pack(side=tk.LEFT)
        
        # Status frame
        status_frame = ttk.LabelFrame(container, text="Status")
        status_frame.pack(fill=tk.X, pady=(0, 5))
        
        # Status label
        self.status_label = ttk.Label(
            status_frame,
            text="Status: STOPPED",
            font=("Arial", 10),
            anchor=tk.CENTER
        )
        self.status_label.pack(fill=tk.X, padx=5, pady=5)
        
        # Position information
        self.position_label = ttk.Label(
            status_frame,
            text="Position: X0.000 Y0.000 Z0.000",
            font=("Arial", 9),
            anchor=tk.CENTER
        )
        self.position_label.pack(fill=tk.X, padx=5, pady=(0, 5))
        
        # Initialize button states
        self._update_button_states()
    
    def update_debug_state(self, debug_state: DebugState):
        """Update the control panel based on debug state."""
        self.debug_state = debug_state
        self._update_button_states()
        self._update_status_display()
    
    def _update_button_states(self):
        """Update button enabled/disabled states based on current debug state.
        
        Note: Debug controls are now available in the menu bar.
        This method only needs to update the breakpoint controls and status.
        """
        # Breakpoint controls are always available
        self.toggle_bp_btn.config(state=tk.NORMAL)
        self.clear_bp_btn.config(state=tk.NORMAL)
        
        # Update status display based on debug state
        self._update_status_display()
    
    def update_position_display(self, x, y, z):
        """Update the position display with new coordinates.
        
        Args:
            x: X coordinate
            y: Y coordinate
            z: Z coordinate
        """
        if hasattr(self, 'position_label'):
            position_text = f"Position: X{x:.3f} Y{y:.3f} Z{z:.3f}"
            self.position_label.config(text=position_text)
    
    def _update_status_display(self):
        """Update the status display with current debug state."""
        # Update status text
        status_text = {
            DebugState.STOPPED: "Status: STOPPED",
            DebugState.RUNNING: "Status: RUNNING",
            DebugState.PAUSED: "Status: PAUSED",
            DebugState.STEPPING: "Status: STEPPING"
        }
        
        # Update status label with color coding
        status_colors = {
            DebugState.STOPPED: "black",
            DebugState.RUNNING: "green",
            DebugState.PAUSED: "orange",
            DebugState.STEPPING: "blue"
        }
        
        current_status = status_text.get(self.debug_state, "Status: UNKNOWN")
        current_color = status_colors.get(self.debug_state, "black")
        
        if hasattr(self, 'status_label'):
            self.status_label.config(
                text=current_status,
                foreground=current_color
            )
    
    def _on_continue(self):
        """Handle continue button click."""
        main_window = self._get_main_window()
        if main_window and hasattr(main_window, 'continue_execution'):
            main_window.continue_execution()
    
    def _on_emergency_stop(self):
        """Handle emergency stop button click."""
        main_window = self._get_main_window()
        if main_window and hasattr(main_window, 'emergency_stop'):
            main_window.emergency_stop()
    
    def _on_toggle_breakpoint(self):
        """Handle toggle breakpoint button click."""
        main_window = self._get_main_window()
        if main_window and hasattr(main_window, 'toggle_breakpoint'):
            main_window.toggle_breakpoint()
    
    def _on_clear_breakpoints(self):
        """Handle clear breakpoints button click."""
        main_window = self._get_main_window()
        if main_window and hasattr(main_window, 'clear_all_breakpoints'):
            main_window.clear_all_breakpoints()
    
    def _get_main_window(self):
        """Get reference to main window."""
        # Walk up the widget hierarchy to find the main window
        parent = self.master
        while parent:
            if hasattr(parent, 'debugger'):  # MainWindow has debugger attribute
                return parent
            parent = parent.master
        return None

class ExecutionProgressBar(ttk.Frame):
    """Progress bar showing execution progress."""
    
    def __init__(self, parent):
        super().__init__(parent)
        
        # Progress variables
        self.current_line = tk.IntVar()
        self.total_lines = tk.IntVar()
        
        self.setup_ui()
    
    def setup_ui(self):
        """Setup the progress bar UI."""
        # Progress bar
        self.progress = ttk.Progressbar(
            self, 
            mode='determinate',
            length=200
        )
        self.progress.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        
        # Progress label
        self.progress_label = ttk.Label(self, text="0 / 0 (0%)")
        self.progress_label.pack(side=tk.RIGHT)
    
    def update_progress(self, current: int, total: int):
        """Update the progress display."""
        self.current_line.set(current)
        self.total_lines.set(total)
        
        if total > 0:
            percentage = (current / total) * 100
            self.progress['value'] = percentage
            self.progress_label.config(text=f"{current} / {total} ({percentage:.1f}%)")
        else:
            self.progress['value'] = 0
            self.progress_label.config(text="0 / 0 (0%)")

class QuickCommandEntry(ttk.Frame):
    """Quick G-code command entry widget for MDI operations."""
    
    def __init__(self, parent):
        super().__init__(parent)
        
        self.command_history = []
        self.history_index = -1
        
        self.setup_ui()
    
    def setup_ui(self):
        """Setup the command entry UI."""
        # Main entry frame
        entry_frame = ttk.Frame(self)
        entry_frame.pack(fill=tk.X, pady=(0, 5))
        
        # Label
        ttk.Label(entry_frame, text="G-code:").pack(side=tk.LEFT, padx=(0, 5))
        
        # Command entry
        self.command_var = tk.StringVar()
        self.command_entry = ttk.Entry(
            entry_frame, 
            textvariable=self.command_var,
            width=30,
            font=("Consolas", 10)
        )
        self.command_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        
        # Send button
        self.send_btn = ttk.Button(
            entry_frame, 
            text="Send", 
            command=self._on_send_command
        )
        self.send_btn.pack(side=tk.RIGHT)
        
        # Bind events
        self.command_entry.bind('<Return>', lambda e: self._on_send_command())
        self.command_entry.bind('<Up>', self._on_history_up)
        self.command_entry.bind('<Down>', self._on_history_down)
    
    def _insert_command(self, command):
        """Insert a command into the entry field."""
        self.command_var.set(command)
        self.command_entry.focus()
    
    def _on_send_command(self):
        """Handle send command."""
        command = self.command_var.get().strip()
        if not command:
            return
        
        # Add to history
        if command not in self.command_history:
            self.command_history.insert(0, command)
            # Limit history size
            if len(self.command_history) > 50:
                self.command_history.pop()
        
        self.history_index = -1
        
        # Send command
        main_window = self._get_main_window()
        if main_window and hasattr(main_window, 'send_gcode_command'):
            main_window.send_gcode_command(command)
        
        # Clear entry
        self.command_var.set("")
    
    def _on_history_up(self, event):
        """Handle up arrow for command history."""
        if self.command_history and self.history_index < len(self.command_history) - 1:
            self.history_index += 1
            self.command_var.set(self.command_history[self.history_index])
    
    def _on_history_down(self, event):
        """Handle down arrow for command history."""
        if self.history_index > 0:
            self.history_index -= 1
            self.command_var.set(self.command_history[self.history_index])
        elif self.history_index == 0:
            self.history_index = -1
            self.command_var.set("")
    
    def _get_main_window(self):
        """Get reference to main window."""
        parent = self.master
        while parent:
            # Check if this is the root window (Tk instance) and has main_window reference
            if isinstance(parent, tk.Tk) and hasattr(parent, 'main_window'):
                main_window = parent.main_window
                if hasattr(main_window, 'send_gcode_command'):
                    return main_window
                    
            if hasattr(parent, 'communicator'):
                return parent
            parent = parent.master
        return None