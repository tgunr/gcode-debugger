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
        """Setup the control panel UI."""
        # Create button frame
        button_frame = ttk.Frame(self)
        button_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # Row 1: Primary controls
        row1 = ttk.Frame(button_frame)
        row1.pack(fill=tk.X, pady=(0, 5))
        
        self.continue_btn = ttk.Button(
            row1, 
            text="▶️ Continue", 
            command=self._on_continue,
            width=12
        )
        self.continue_btn.pack(side=tk.LEFT, padx=(0, 5))
        
        self.pause_btn = ttk.Button(
            row1, 
            text="⏸️ Pause", 
            command=self._on_pause,
            width=12
        )
        self.pause_btn.pack(side=tk.LEFT, padx=(0, 5))
        
        self.stop_btn = ttk.Button(
            row1, 
            text="🛑 Stop", 
            command=self._on_stop,
            width=12
        )
        self.stop_btn.pack(side=tk.LEFT)
        
        # Row 2: Step controls
        row2 = ttk.Frame(button_frame)
        row2.pack(fill=tk.X, pady=(0, 5))
        
        self.step_btn = ttk.Button(
            row2, 
            text="⏭️ Step Over", 
            command=self._on_step_over,
            width=12
        )
        self.step_btn.pack(side=tk.LEFT, padx=(0, 5))
        
        self.step_to_btn = ttk.Button(
            row2, 
            text="⏩ Step To...", 
            command=self._on_step_to,
            width=12
        )
        self.step_to_btn.pack(side=tk.LEFT, padx=(0, 5))
        
        self.go_back_btn = ttk.Button(
            row2, 
            text="⏪ Go Back", 
            command=self._on_go_back,
            width=12
        )
        self.go_back_btn.pack(side=tk.LEFT)
        
        # Row 3: Skip controls
        row3 = ttk.Frame(button_frame)
        row3.pack(fill=tk.X, pady=(0, 5))
        
        self.skip_line_btn = ttk.Button(
            row3, 
            text="🔄 Skip Line", 
            command=self._on_skip_line,
            width=12
        )
        self.skip_line_btn.pack(side=tk.LEFT, padx=(0, 5))
        
        self.skip_to_btn = ttk.Button(
            row3, 
            text="🎯 Skip To...", 
            command=self._on_skip_to,
            width=12
        )
        self.skip_to_btn.pack(side=tk.LEFT, padx=(0, 5))
        
        # Emergency stop (separate styling)
        self.estop_btn = tk.Button(
            row3, 
            text="🚨 E-STOP", 
            command=self._on_emergency_stop,
            bg="red",
            fg="white",
            font=("Arial", 9, "bold"),
            width=12
        )
        self.estop_btn.pack(side=tk.LEFT)
        
        # Breakpoint controls
        bp_frame = ttk.LabelFrame(button_frame, text="Breakpoints")
        bp_frame.pack(fill=tk.X, pady=(10, 0))
        
        bp_row = ttk.Frame(bp_frame)
        bp_row.pack(fill=tk.X, padx=5, pady=5)
        
        self.toggle_bp_btn = ttk.Button(
            bp_row, 
            text="🔴 Toggle BP", 
            command=self._on_toggle_breakpoint,
            width=12
        )
        self.toggle_bp_btn.pack(side=tk.LEFT, padx=(0, 5))
        
        self.clear_bp_btn = ttk.Button(
            bp_row, 
            text="🧹 Clear All", 
            command=self._on_clear_breakpoints,
            width=12
        )
        self.clear_bp_btn.pack(side=tk.LEFT)
        
        # Status display
        status_frame = ttk.LabelFrame(button_frame, text="Execution Status")
        status_frame.pack(fill=tk.X, pady=(10, 0))
        
        self.status_label = ttk.Label(
            status_frame, 
            text="STOPPED",
            font=("Arial", 10, "bold")
        )
        self.status_label.pack(pady=5)
        
        # Update button states
        self._update_button_states()
    
    def update_debug_state(self, debug_state: DebugState):
        """Update the control panel based on debug state."""
        self.debug_state = debug_state
        self._update_button_states()
        self._update_status_display()
    
    def _update_button_states(self):
        """Update button enabled/disabled states based on current debug state."""
        state = self.debug_state
        
        # Continue button
        if state in [DebugState.STOPPED, DebugState.PAUSED]:
            self.continue_btn.config(state=tk.NORMAL)
        else:
            self.continue_btn.config(state=tk.DISABLED)
        
        # Pause button
        if state == DebugState.RUNNING:
            self.pause_btn.config(state=tk.NORMAL)
        else:
            self.pause_btn.config(state=tk.DISABLED)
        
        # Stop button
        if state in [DebugState.RUNNING, DebugState.PAUSED, DebugState.STEPPING]:
            self.stop_btn.config(state=tk.NORMAL)
        else:
            self.stop_btn.config(state=tk.DISABLED)
        
        # Step controls
        if state in [DebugState.STOPPED, DebugState.PAUSED]:
            self.step_btn.config(state=tk.NORMAL)
            self.step_to_btn.config(state=tk.NORMAL)
            self.go_back_btn.config(state=tk.NORMAL)
            self.skip_line_btn.config(state=tk.NORMAL)
            self.skip_to_btn.config(state=tk.NORMAL)
        else:
            self.step_btn.config(state=tk.DISABLED)
            self.step_to_btn.config(state=tk.DISABLED)
            self.go_back_btn.config(state=tk.DISABLED)
            self.skip_line_btn.config(state=tk.DISABLED)
            self.skip_to_btn.config(state=tk.DISABLED)
        
        # Breakpoint controls are always available
        self.toggle_bp_btn.config(state=tk.NORMAL)
        self.clear_bp_btn.config(state=tk.NORMAL)
        
        # Emergency stop is always available
        self.estop_btn.config(state=tk.NORMAL)
    
    def _update_status_display(self):
        """Update the status display."""
        status_text = self.debug_state.value.upper()
        
        # Color coding
        colors = {
            DebugState.STOPPED: "gray",
            DebugState.RUNNING: "green",
            DebugState.PAUSED: "orange",
            DebugState.STEPPING: "blue",
            DebugState.WAITING: "yellow",
            DebugState.ERROR: "red"
        }
        
        self.status_label.config(
            text=status_text,
            foreground=colors.get(self.debug_state, "black")
        )
    
    # Button event handlers - these would be connected to the main window
    def _on_continue(self):
        """Handle continue button click."""
        # Get parent window and call continue method
        main_window = self._get_main_window()
        if main_window and hasattr(main_window, 'continue_execution'):
            main_window.continue_execution()
    
    def _on_pause(self):
        """Handle pause button click."""
        main_window = self._get_main_window()
        if main_window and hasattr(main_window, 'pause_execution'):
            main_window.pause_execution()
    
    def _on_stop(self):
        """Handle stop button click."""
        main_window = self._get_main_window()
        if main_window and hasattr(main_window, 'stop_execution'):
            main_window.stop_execution()
    
    def _on_step_over(self):
        """Handle step over button click."""
        main_window = self._get_main_window()
        if main_window and hasattr(main_window, 'step_over'):
            main_window.step_over()
    
    def _on_step_to(self):
        """Handle step to button click."""
        line_num = simpledialog.askinteger(
            "Step to Line", 
            "Enter line number:",
            minvalue=1
        )
        if line_num:
            main_window = self._get_main_window()
            if main_window and hasattr(main_window, 'debugger'):
                main_window.debugger.step_to_line(line_num)
    
    def _on_go_back(self):
        """Handle go back button click."""
        main_window = self._get_main_window()
        if main_window and hasattr(main_window, 'go_back'):
            main_window.go_back()
    
    def _on_skip_line(self):
        """Handle skip line button click."""
        main_window = self._get_main_window()
        if main_window and hasattr(main_window, 'skip_line'):
            main_window.skip_line()
    
    def _on_skip_to(self):
        """Handle skip to button click."""
        line_num = simpledialog.askinteger(
            "Skip to Line", 
            "Enter line number:",
            minvalue=1
        )
        if line_num:
            main_window = self._get_main_window()
            if main_window and hasattr(main_window, 'debugger'):
                main_window.debugger.skip_to_line(line_num)
    
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
    """Quick G-code command entry widget."""
    
    def __init__(self, parent):
        super().__init__(parent)
        
        self.command_history = []
        self.history_index = -1
        
        self.setup_ui()
    
    def setup_ui(self):
        """Setup the command entry UI."""
        # Label
        ttk.Label(self, text="Quick Command:").pack(side=tk.LEFT, padx=(0, 5))
        
        # Command entry
        self.command_var = tk.StringVar()
        self.command_entry = ttk.Entry(
            self, 
            textvariable=self.command_var,
            width=30
        )
        self.command_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        
        # Send button
        self.send_btn = ttk.Button(
            self, 
            text="Send", 
            command=self._on_send_command
        )
        self.send_btn.pack(side=tk.RIGHT)
        
        # Bind events
        self.command_entry.bind('<Return>', lambda e: self._on_send_command())
        self.command_entry.bind('<Up>', self._on_history_up)
        self.command_entry.bind('<Down>', self._on_history_down)
    
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
        if main_window and hasattr(main_window, 'communicator'):
            main_window.communicator.send_gcode(command)
        
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
            if hasattr(parent, 'communicator'):
                return parent
            parent = parent.master
        return None