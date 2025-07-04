#!/usr/bin/env python3
"""
Macro Panel for G-code Debugger

Provides macro management and execution interface.
"""

import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
from typing import Optional

class MacroPanel(ttk.LabelFrame):
    """Panel for macro management and execution."""
    
    def __init__(self, parent, macro_manager):
        super().__init__(parent, text="Macros")
        self.macro_manager = macro_manager
        self.selected_macro = None
        self.setup_ui()
        self._refresh_macro_list()
    
    def setup_ui(self):
        """Setup the macro panel UI."""
        # Main frame
        main_frame = ttk.Frame(self)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Macro list frame
        list_frame = ttk.Frame(main_frame)
        list_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 5))
        
        # Macro listbox with scrollbar
        self.macro_listbox = tk.Listbox(
            list_frame, 
            height=8,
            font=("Arial", 9),
            selectmode=tk.SINGLE
        )
        self.macro_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.macro_listbox.config(yscrollcommand=scrollbar.set)
        scrollbar.config(command=self.macro_listbox.yview)
        
        # Bind events
        self.macro_listbox.bind('<<ListboxSelect>>', self._on_macro_select)
        self.macro_listbox.bind('<Double-Button-1>', self._on_execute_macro)
        
        # Buttons frame
        btn_frame = ttk.Frame(main_frame)
        btn_frame.pack(fill=tk.X)
        
        # Row 1: Execution buttons
        exec_frame = ttk.Frame(btn_frame)
        exec_frame.pack(fill=tk.X, pady=(0, 5))
        
        self.execute_btn = ttk.Button(
            exec_frame, 
            text="▶️ Execute", 
            command=self._on_execute_macro,
            width=12
        )
        self.execute_btn.pack(side=tk.LEFT, padx=(0, 5))
        
        self.stop_macro_btn = ttk.Button(
            exec_frame, 
            text="⏹️ Stop", 
            command=self._on_stop_macro,
            width=12,
            state=tk.DISABLED
        )
        self.stop_macro_btn.pack(side=tk.LEFT)
        
        # Row 2: Management buttons
        mgmt_frame = ttk.Frame(btn_frame)
        mgmt_frame.pack(fill=tk.X, pady=(0, 5))
        
        self.new_btn = ttk.Button(
            mgmt_frame, 
            text="➕ New", 
            command=self._on_new_macro,
            width=12
        )
        self.new_btn.pack(side=tk.LEFT, padx=(0, 5))
        
        self.edit_btn = ttk.Button(
            mgmt_frame, 
            text="✏️ Edit", 
            command=self._on_edit_macro,
            width=12,
            state=tk.DISABLED
        )
        self.edit_btn.pack(side=tk.LEFT, padx=(0, 5))
        
        self.delete_btn = ttk.Button(
            mgmt_frame, 
            text="🗑️ Delete", 
            command=self._on_delete_macro,
            width=12,
            state=tk.DISABLED
        )
        self.delete_btn.pack(side=tk.LEFT)
        
        # Row 3: Import/Export buttons
        io_frame = ttk.Frame(btn_frame)
        io_frame.pack(fill=tk.X)
        
        self.import_btn = ttk.Button(
            io_frame, 
            text="📁 Import", 
            command=self._on_import_macro,
            width=12
        )
        self.import_btn.pack(side=tk.LEFT, padx=(0, 5))
        
        self.export_btn = ttk.Button(
            io_frame, 
            text="💾 Export", 
            command=self._on_export_macro,
            width=12,
            state=tk.DISABLED
        )
        self.export_btn.pack(side=tk.LEFT, padx=(0, 5))
        
        self.refresh_btn = ttk.Button(
            io_frame, 
            text="🔄 Refresh", 
            command=self._refresh_macro_list,
            width=12
        )
        self.refresh_btn.pack(side=tk.LEFT)
    
    def _refresh_macro_list(self):
        """Refresh the macro list display."""
        self.macro_listbox.delete(0, tk.END)
        
        macros = self.macro_manager.get_all_macros()
        for macro in sorted(macros, key=lambda m: (m.category, m.name)):
            # Color code by category
            color_prefix = self._get_category_prefix(macro.category)
            display_text = f"{color_prefix} {macro.name}"
            if macro.description:
                display_text += f" - {macro.description[:30]}"
                if len(macro.description) > 30:
                    display_text += "..."
            
            self.macro_listbox.insert(tk.END, display_text)
        
        self._update_button_states()
    
    def _get_category_prefix(self, category: str) -> str:
        """Get emoji prefix for macro category."""
        prefixes = {
            "system": "⚙️",
            "homing": "🏠",
            "tool_change": "🔧",
            "probing": "📐",
            "user": "👤",
            "custom": "⭐"
        }
        return prefixes.get(category, "📝")
    
    def _on_macro_select(self, event):
        """Handle macro selection."""
        selection = self.macro_listbox.curselection()
        if selection:
            macro_text = self.macro_listbox.get(selection[0])
            # Extract macro name (remove emoji and description)
            macro_name = macro_text.split(' - ')[0].split(' ', 1)[1]  # Remove emoji prefix
            self.selected_macro = self.macro_manager.get_macro(macro_name)
        else:
            self.selected_macro = None
        
        self._update_button_states()
    
    def _update_button_states(self):
        """Update button enabled/disabled states."""
        has_selection = self.selected_macro is not None
        
        self.execute_btn.config(state=tk.NORMAL if has_selection else tk.DISABLED)
        self.edit_btn.config(state=tk.NORMAL if has_selection else tk.DISABLED)
        self.delete_btn.config(state=tk.NORMAL if has_selection else tk.DISABLED)
        self.export_btn.config(state=tk.NORMAL if has_selection else tk.DISABLED)
    
    def _on_execute_macro(self, event=None):
        """Execute the selected macro."""
        if not self.selected_macro:
            return
        
        # Get main window and execute macro
        main_window = self._get_main_window()
        if main_window and hasattr(main_window, 'macro_executor'):
            main_window.macro_executor.execute_macro(self.selected_macro)
            self.stop_macro_btn.config(state=tk.NORMAL)
    
    def _on_stop_macro(self):
        """Stop macro execution."""
        main_window = self._get_main_window()
        if main_window and hasattr(main_window, 'macro_executor'):
            main_window.macro_executor.cancel_execution()
            self.stop_macro_btn.config(state=tk.DISABLED)
    
    def _on_new_macro(self):
        """Create a new macro."""
        dialog = MacroEditDialog(self, "Create New Macro")
        if dialog.result:
            name, description, commands, category = dialog.result
            if self.macro_manager.create_macro(name, commands, description, category):
                self._refresh_macro_list()
                messagebox.showinfo("Success", f"Macro '{name}' created successfully!")
            else:
                messagebox.showerror("Error", f"Failed to create macro '{name}'. Name may already exist.")
    
    def _on_edit_macro(self):
        """Edit the selected macro."""
        if not self.selected_macro:
            return
        
        dialog = MacroEditDialog(self, "Edit Macro", self.selected_macro)
        if dialog.result:
            name, description, commands, category = dialog.result
            if self.macro_manager.update_macro(
                self.selected_macro.name, 
                commands=commands, 
                description=description, 
                category=category
            ):
                self._refresh_macro_list()
                messagebox.showinfo("Success", f"Macro '{name}' updated successfully!")
            else:
                messagebox.showerror("Error", f"Failed to update macro '{name}'.")
    
    def _on_delete_macro(self):
        """Delete the selected macro."""
        if not self.selected_macro:
            return
        
        result = messagebox.askyesno(
            "Confirm Delete", 
            f"Are you sure you want to delete macro '{self.selected_macro.name}'?"
        )
        
        if result:
            if self.macro_manager.delete_macro(self.selected_macro.name):
                self._refresh_macro_list()
                messagebox.showinfo("Success", f"Macro '{self.selected_macro.name}' deleted.")
            else:
                messagebox.showerror("Error", f"Failed to delete macro.")
    
    def _on_import_macro(self):
        """Import a macro from G-code file."""
        from tkinter import filedialog
        
        file_path = filedialog.askopenfilename(
            title="Import Macro from G-code File",
            filetypes=[
                ("G-code files", "*.nc *.gcode *.tap"),
                ("All files", "*.*")
            ]
        )
        
        if file_path:
            name = simpledialog.askstring("Import Macro", "Enter macro name:")
            if name:
                description = simpledialog.askstring("Import Macro", "Enter description (optional):") or ""
                
                if self.macro_manager.import_macro_from_file(name, file_path, description):
                    self._refresh_macro_list()
                    messagebox.showinfo("Success", f"Macro '{name}' imported successfully!")
                else:
                    messagebox.showerror("Error", f"Failed to import macro from file.")
    
    def _on_export_macro(self):
        """Export the selected macro to G-code file."""
        if not self.selected_macro:
            return
        
        from tkinter import filedialog
        
        file_path = filedialog.asksaveasfilename(
            title="Export Macro to G-code File",
            defaultextension=".gcode",
            filetypes=[
                ("G-code files", "*.gcode"),
                ("NC files", "*.nc"),
                ("All files", "*.*")
            ]
        )
        
        if file_path:
            if self.macro_manager.export_macro(self.selected_macro.name, file_path):
                messagebox.showinfo("Success", f"Macro exported to '{file_path}'!")
            else:
                messagebox.showerror("Error", f"Failed to export macro.")
    
    def _get_main_window(self):
        """Get reference to main window."""
        parent = self.master
        while parent:
            if hasattr(parent, 'macro_executor'):
                return parent
            parent = parent.master
        return None

class MacroEditDialog:
    """Dialog for creating/editing macros."""
    
    def __init__(self, parent, title: str, macro=None):
        self.result = None
        self.macro = macro
        
        # Create dialog window
        self.dialog = tk.Toplevel(parent)
        self.dialog.title(title)
        self.dialog.geometry("600x500")
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
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
        self.dialog.wait_window()
    
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
        self.dialog.destroy()
    
    def _on_cancel(self):
        """Handle Cancel button."""
        self.dialog.destroy()