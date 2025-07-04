#!/usr/bin/env python3
"""
Status Panel for G-code Debugger

Displays machine state, position, and other real-time information.
"""

import tkinter as tk
from tkinter import ttk
from typing import Dict, Any

class StatusPanel(ttk.LabelFrame):
    """Panel displaying machine status and position information."""
    
    def __init__(self, parent):
        super().__init__(parent, text="Machine Status")
        
        # State variables
        self.machine_state = tk.StringVar(value="UNKNOWN")
        self.cycle_state = tk.StringVar(value="UNKNOWN")
        self.pos_x = tk.StringVar(value="0.000")
        self.pos_y = tk.StringVar(value="0.000")
        self.pos_z = tk.StringVar(value="0.000")
        self.feed_rate = tk.StringVar(value="0")
        self.spindle_speed = tk.StringVar(value="0")
        self.spindle_state = tk.StringVar(value="OFF")
        self.coolant_state = tk.StringVar(value="OFF")
        self.tool_number = tk.StringVar(value="0")
        self.units = tk.StringVar(value="MM")
        
        self.setup_ui()
    
    def setup_ui(self):
        """Setup the status panel UI."""
        main_frame = ttk.Frame(self)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Machine state section
        state_frame = ttk.LabelFrame(main_frame, text="State")
        state_frame.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, 5))
        
        ttk.Label(state_frame, text="Machine:").grid(row=0, column=0, sticky="w", padx=5)
        state_label = ttk.Label(state_frame, textvariable=self.machine_state, font=("Arial", 10, "bold"))
        state_label.grid(row=0, column=1, sticky="w", padx=5)
        
        ttk.Label(state_frame, text="Cycle:").grid(row=0, column=2, sticky="w", padx=5)
        cycle_label = ttk.Label(state_frame, textvariable=self.cycle_state)
        cycle_label.grid(row=0, column=3, sticky="w", padx=5)
        
        # Position section
        pos_frame = ttk.LabelFrame(main_frame, text="Position")
        pos_frame.grid(row=1, column=0, columnspan=2, sticky="ew", pady=(0, 5))
        
        # X position
        ttk.Label(pos_frame, text="X:").grid(row=0, column=0, sticky="w", padx=5)
        ttk.Label(pos_frame, textvariable=self.pos_x, font=("Consolas", 10)).grid(row=0, column=1, sticky="w", padx=5)
        
        # Y position
        ttk.Label(pos_frame, text="Y:").grid(row=0, column=2, sticky="w", padx=5)
        ttk.Label(pos_frame, textvariable=self.pos_y, font=("Consolas", 10)).grid(row=0, column=3, sticky="w", padx=5)
        
        # Z position
        ttk.Label(pos_frame, text="Z:").grid(row=0, column=4, sticky="w", padx=5)
        ttk.Label(pos_frame, textvariable=self.pos_z, font=("Consolas", 10)).grid(row=0, column=5, sticky="w", padx=5)
        
        # Units
        ttk.Label(pos_frame, textvariable=self.units).grid(row=0, column=6, sticky="w", padx=5)
        
        # Control section
        control_frame = ttk.LabelFrame(main_frame, text="Control")
        control_frame.grid(row=2, column=0, columnspan=2, sticky="ew")
        
        # Feed rate
        ttk.Label(control_frame, text="Feed:").grid(row=0, column=0, sticky="w", padx=5)
        ttk.Label(control_frame, textvariable=self.feed_rate).grid(row=0, column=1, sticky="w", padx=5)
        ttk.Label(control_frame, text="mm/min").grid(row=0, column=2, sticky="w", padx=5)
        
        # Spindle
        ttk.Label(control_frame, text="Spindle:").grid(row=0, column=3, sticky="w", padx=5)
        ttk.Label(control_frame, textvariable=self.spindle_state).grid(row=0, column=4, sticky="w", padx=5)
        ttk.Label(control_frame, textvariable=self.spindle_speed).grid(row=0, column=5, sticky="w", padx=5)
        ttk.Label(control_frame, text="RPM").grid(row=0, column=6, sticky="w", padx=5)
        
        # Tool and coolant
        ttk.Label(control_frame, text="Tool:").grid(row=1, column=0, sticky="w", padx=5)
        ttk.Label(control_frame, textvariable=self.tool_number).grid(row=1, column=1, sticky="w", padx=5)
        
        ttk.Label(control_frame, text="Coolant:").grid(row=1, column=3, sticky="w", padx=5)
        ttk.Label(control_frame, textvariable=self.coolant_state).grid(row=1, column=4, sticky="w", padx=5)
        
        # Configure grid weights
        main_frame.columnconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
    
    def update_state(self, state: Dict[str, Any]):
        """Update the status display with new machine state."""
        # Machine state
        if 'xx' in state:
            self.machine_state.set(state['xx'])
        
        if 'cycle' in state:
            self.cycle_state.set(state['cycle'])
        
        # Position (work coordinates)
        if 'posx' in state:
            self.pos_x.set(f"{state['posx']:.3f}")
        if 'posy' in state:
            self.pos_y.set(f"{state['posy']:.3f}")
        if 'posz' in state:
            self.pos_z.set(f"{state['posz']:.3f}")
        
        # Units
        if 'imperial' in state:
            self.units.set("INCH" if state['imperial'] else "MM")
        
        # Feed rate
        if 'feed' in state:
            self.feed_rate.set(f"{state['feed']:.0f}")
        
        # Spindle
        if 'speed' in state:
            self.spindle_speed.set(f"{state['speed']:.0f}")
        
        # Tool
        if 'tool' in state:
            self.tool_number.set(f"T{state['tool']}")
        
        # Update colors based on state
        self._update_state_colors()
    
    def _update_state_colors(self):
        """Update label colors based on machine state."""
        state = self.machine_state.get()
        
        # Color mapping for machine states
        colors = {
            'READY': 'green',
            'RUNNING': 'blue',
            'HOLDING': 'orange',
            'STOPPING': 'red',
            'ESTOPPED': 'red',
            'HOMING': 'purple'
        }
        
        # Find the state label and update its color
        for child in self.winfo_children():
            for grandchild in child.winfo_children():
                if isinstance(grandchild, ttk.Frame):
                    for widget in grandchild.winfo_children():
                        if isinstance(widget, ttk.Label) and widget['textvariable'] == str(self.machine_state):
                            # Note: ttk.Label doesn't support foreground color directly
                            # This would need a different approach in a real implementation
                            pass

class MacroPanel(ttk.LabelFrame):
    """Panel for macro management and execution."""
    
    def __init__(self, parent, macro_manager):
        super().__init__(parent, text="Macros")
        self.macro_manager = macro_manager
        self.setup_ui()
        self._refresh_macro_list()
    
    def setup_ui(self):
        """Setup the macro panel UI."""
        # Macro list
        list_frame = ttk.Frame(self)
        list_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Scrollable macro list
        self.macro_listbox = tk.Listbox(list_frame, height=8)
        self.macro_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.macro_listbox.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.macro_listbox.config(yscrollcommand=scrollbar.set)
        
        # Buttons
        btn_frame = ttk.Frame(self)
        btn_frame.pack(fill=tk.X, padx=5, pady=(0, 5))
        
        self.execute_btn = ttk.Button(btn_frame, text="Execute", command=self._execute_macro)
        self.execute_btn.pack(side=tk.LEFT, padx=(0, 5))
        
        self.refresh_btn = ttk.Button(btn_frame, text="Refresh", command=self._refresh_macro_list)
        self.refresh_btn.pack(side=tk.LEFT)
        
        # Bind double-click to execute
        self.macro_listbox.bind('<Double-Button-1>', lambda e: self._execute_macro())
    
    def _refresh_macro_list(self):
        """Refresh the macro list display."""
        self.macro_listbox.delete(0, tk.END)
        
        macros = self.macro_manager.get_all_macros()
        for macro in sorted(macros, key=lambda m: m.name):
            display_text = f"{macro.name} - {macro.description[:30]}..."
            self.macro_listbox.insert(tk.END, display_text)
    
    def _execute_macro(self):
        """Execute the selected macro."""
        selection = self.macro_listbox.curselection()
        if not selection:
            return
        
        macro_text = self.macro_listbox.get(selection[0])
        macro_name = macro_text.split(' - ')[0]
        
        macro = self.macro_manager.get_macro(macro_name)
        if macro:
            # Get main window and execute macro
            main_window = self._get_main_window()
            if main_window and hasattr(main_window, 'macro_executor'):
                main_window.macro_executor.execute_macro(macro)
    
    def _get_main_window(self):
        """Get reference to main window."""
        parent = self.master
        while parent:
            if hasattr(parent, 'macro_executor'):
                return parent
            parent = parent.master
        return None