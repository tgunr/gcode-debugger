#!/usr/bin/env python3
"""
Macro Panel for G-code Debugger

Provides macro management and execution interface for both local and external macros.
"""

import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
from typing import Optional

class MacroPanel(ttk.LabelFrame):
    """Panel for both local and external macro management and execution."""
    
    def __init__(self, parent, macro_manager, local_macro_manager):
        super().__init__(parent, text="Macros")
        self.macro_manager = macro_manager  # External macros
        self.local_macro_manager = local_macro_manager  # Local macros
        self.selected_macro = None
        self.selected_local_macro = None
        self.current_tab = "local"  # Track which tab is active
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
        
        # External macros tab
        self.external_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.external_frame, text="🔧 External Macros")
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
        
        self.local_edit_btn = ttk.Button(
            local_main_frame,
            text="✏️ Edit",
            command=self._on_edit_local_macro,
            width=8,
            state=tk.DISABLED
        )
        self.local_edit_btn.pack(side=tk.LEFT, padx=(0, 2))
        
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
        """Setup the external macros tab."""
        # External macro list frame
        list_frame = ttk.Frame(self.external_frame)
        list_frame.pack(fill=tk.X, pady=(5, 5), padx=5)
        
        # External macro listbox with scrollbar
        self.external_macro_listbox = tk.Listbox(
            list_frame,
            height=10,  # Increased from 3 to 10 to show more macros
            font=("Arial", 8),
            selectmode=tk.SINGLE
        )
        self.external_macro_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        external_scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL)
        external_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.external_macro_listbox.config(yscrollcommand=external_scrollbar.set)
        external_scrollbar.config(command=self.external_macro_listbox.yview)
        
        # Bind events for external macros
        self.external_macro_listbox.bind('<<ListboxSelect>>', self._on_external_macro_select)
        self.external_macro_listbox.bind('<Double-Button-1>', self._on_view_external_macro_in_editor)
        
        # External macro buttons frame
        external_btn_frame = ttk.Frame(self.external_frame)
        external_btn_frame.pack(fill=tk.X, padx=5, pady=(0, 5))
        
        # Row 1: Main action buttons
        external_main_frame = ttk.Frame(external_btn_frame)
        external_main_frame.pack(fill=tk.X, pady=(0, 2))
        
        self.external_execute_btn = ttk.Button(
            external_main_frame,
            text="▶️ Run",
            command=self._on_execute_external_macro,
            width=8
        )
        self.external_execute_btn.pack(side=tk.LEFT, padx=(0, 2))
        
        self.external_new_btn = ttk.Button(
            external_main_frame,
            text="➕ New",
            command=self._on_new_external_macro,
            width=8
        )
        self.external_new_btn.pack(side=tk.LEFT, padx=(0, 2))
        
        self.external_edit_btn = ttk.Button(
            external_main_frame,
            text="✏️ Edit",
            command=self._on_edit_external_macro,
            width=8,
            state=tk.DISABLED
        )
        self.external_edit_btn.pack(side=tk.LEFT, padx=(0, 2))
        
        self.external_delete_btn = ttk.Button(
            external_main_frame,
            text="🗑️ Del",
            command=self._on_delete_external_macro,
            width=8,
            state=tk.DISABLED
        )
        self.external_delete_btn.pack(side=tk.LEFT)
        
        # Row 2: Secondary buttons
        external_sec_frame = ttk.Frame(external_btn_frame)
        external_sec_frame.pack(fill=tk.X)
        
        self.external_stop_btn = ttk.Button(
            external_sec_frame,
            text="⏹️ Stop",
            command=self._on_stop_external_macro,
            width=8,
            state=tk.DISABLED
        )
        self.external_stop_btn.pack(side=tk.LEFT, padx=(0, 2))
        
        self.external_import_btn = ttk.Button(
            external_sec_frame,
            text="📁 Import",
            command=self._on_import_external_macro,
            width=8
        )
        self.external_import_btn.pack(side=tk.LEFT, padx=(0, 2))
        
        self.external_export_btn = ttk.Button(
            external_sec_frame,
            text="💾 Export",
            command=self._on_export_external_macro,
            width=8,
            state=tk.DISABLED
        )
        self.external_export_btn.pack(side=tk.LEFT, padx=(0, 2))
        
        self.external_refresh_btn = ttk.Button(
            external_sec_frame,
            text="🔄",
            command=self._refresh_external_macro_list,
            width=4
        )
        self.external_refresh_btn.pack(side=tk.LEFT)
    
    def _on_tab_changed(self, event):
        """Handle tab change event."""
        selected_tab = self.notebook.index(self.notebook.select())
        if selected_tab == 0:
            self.current_tab = "local"
        else:
            self.current_tab = "external"
    
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
        """Refresh the external macro list display."""
        self.external_macro_listbox.delete(0, tk.END)
        
        external_macros = self.macro_manager.get_all_macros()
        for macro in sorted(external_macros, key=lambda m: (m.category, m.name)):
            # Color code by category
            color_prefix = self._get_category_prefix(macro.category)
            display_text = f"{color_prefix} {macro.name}"
            if macro.description:
                display_text += f" - {macro.description[:25]}"
                if len(macro.description) > 25:
                    display_text += "..."
            
            self.external_macro_listbox.insert(tk.END, display_text)
        
        self._update_external_button_states()
    
    def _get_category_prefix(self, category: str) -> str:
        """Get emoji prefix for macro category."""
        prefixes = {
            "system": "⚙️",
            "homing": "🏠",
            "tool_change": "🔧",
            "probing": "📐",
            "user": "👤",
            "custom": "⭐",
            "debug": "🐛"
        }
        return prefixes.get(category, "📝")
    
    # Local macro event handlers
    def _on_local_macro_select(self, event):
        """Handle local macro selection."""
        selection = self.local_macro_listbox.curselection()
        if selection:
            macro_text = self.local_macro_listbox.get(selection[0])
            # Extract macro name (remove emoji and description)
            macro_name = macro_text.split(' - ')[0].split(' ', 1)[1]  # Remove emoji prefix
            self.selected_local_macro = self.local_macro_manager.get_local_macro(macro_name)
        else:
            self.selected_local_macro = None
        
        self._update_local_button_states()
    
    def _update_local_button_states(self):
        """Update local macro button enabled/disabled states."""
        has_selection = self.selected_local_macro is not None
        
        self.local_execute_btn.config(state=tk.NORMAL if has_selection else tk.DISABLED)
        self.local_edit_btn.config(state=tk.NORMAL if has_selection else tk.DISABLED)
        self.local_delete_btn.config(state=tk.NORMAL if has_selection else tk.DISABLED)
        self.local_export_btn.config(state=tk.NORMAL if has_selection else tk.DISABLED)
    
    # External macro event handlers
    def _on_external_macro_select(self, event):
        """Handle external macro selection."""
        selection = self.external_macro_listbox.curselection()
        if selection:
            macro_text = self.external_macro_listbox.get(selection[0])
            # Extract macro name (remove emoji and description)
            macro_name = macro_text.split(' - ')[0].split(' ', 1)[1]  # Remove emoji prefix
            self.selected_macro = self.macro_manager.get_macro(macro_name)
        else:
            self.selected_macro = None
        
        self._update_external_button_states()
    
    def _update_external_button_states(self):
        """Update external macro button enabled/disabled states."""
        has_selection = self.selected_macro is not None
        
        self.external_execute_btn.config(state=tk.NORMAL if has_selection else tk.DISABLED)
        self.external_edit_btn.config(state=tk.NORMAL if has_selection else tk.DISABLED)
        self.external_delete_btn.config(state=tk.NORMAL if has_selection else tk.DISABLED)
        self.external_export_btn.config(state=tk.NORMAL if has_selection else tk.DISABLED)
    
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
        if not self.selected_local_macro:
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
            main_window.code_editor.delete('1.0', tk.END)
            main_window.code_editor.insert('1.0', macro_content)
            
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
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load macro into editor: {e}")
    
    # External macro execution and management methods
    def _on_execute_external_macro(self, event=None):
        """Execute the selected external macro."""
        if not self.selected_macro:
            return
        
        # Get main window and execute external macro
        main_window = self._get_main_window()
        if main_window and hasattr(main_window, 'macro_executor'):
            main_window.macro_executor.execute_macro(self.selected_macro)
            self.external_stop_btn.config(state=tk.NORMAL)
    
    def _on_stop_external_macro(self):
        """Stop external macro execution."""
        main_window = self._get_main_window()
        if main_window and hasattr(main_window, 'macro_executor'):
            main_window.macro_executor.cancel_execution()
            self.external_stop_btn.config(state=tk.DISABLED)
    
    def _on_new_external_macro(self):
        """Create a new external macro."""
        dialog = MacroEditDialog(self, "Create New External Macro")
        if dialog.result:
            name, description, commands, category = dialog.result
            if self.macro_manager.create_macro(name, commands, description, category):
                self._refresh_external_macro_list()
                messagebox.showinfo("Success", f"External macro '{name}' created successfully!")
            else:
                messagebox.showerror("Error", f"Failed to create external macro '{name}'. Name may already exist.")
    
    def _on_edit_external_macro(self):
        """Edit the selected external macro."""
        if not self.selected_macro:
            return
        
        dialog = MacroEditDialog(self, "Edit External Macro", self.selected_macro)
        if dialog.result:
            name, description, commands, category = dialog.result
            if self.macro_manager.update_macro(
                name, 
                commands=commands, 
                description=description, 
                category=category
            ):
                self._refresh_external_macro_list()
                messagebox.showinfo("Success", f"External macro '{name}' updated successfully!")
            else:
                messagebox.showerror("Error", f"Failed to update external macro '{name}'.")
    
    def _on_delete_external_macro(self):
        """Delete the selected external macro."""
        if not self.selected_macro:
            return
        
        result = messagebox.askyesno(
            "Confirm Delete", 
            f"Are you sure you want to delete external macro '{self.selected_macro.name}'?"
        )
        
        if result:
            if self.macro_manager.delete_macro(self.selected_macro.name):
                self._refresh_external_macro_list()
                messagebox.showinfo("Success", f"External macro '{self.selected_macro.name}' deleted.")
            else:
                messagebox.showerror("Error", f"Failed to delete external macro.")
    
    def _on_import_external_macro(self):
        """Import an external macro from G-code file."""
        from tkinter import filedialog
        
        file_path = filedialog.askopenfilename(
            title="Import External Macro from G-code File",
            filetypes=[
                ("G-code files", "*.nc *.gcode *.tap *.ngc *.gc"),
                ("All files", "*.*")
            ]
        )
        
        if file_path:
            name = simpledialog.askstring("Import External Macro", "Enter external macro name:")
            if name:
                description = simpledialog.askstring("Import External Macro", "Enter description (optional):") or ""
                
                if self.macro_manager.import_macro_from_file(name, file_path, description):
                    self._refresh_external_macro_list()
                    messagebox.showinfo("Success", f"External macro '{name}' imported successfully!")
                else:
                    messagebox.showerror("Error", f"Failed to import external macro from file.")
    
    def _on_export_external_macro(self):
        """Export the selected external macro to G-code file."""
        if not self.selected_macro:
            return
        
        from tkinter import filedialog
        
        file_path = filedialog.asksaveasfilename(
            title="Export External Macro to G-code File",
            defaultextension=".gcode",
            filetypes=[
                ("G-code files", "*.gcode *.nc *.tap *.cnc *.ngc *.gc"),
                ("All files", "*.*")
            ]
        )
        
        if file_path:
            if self.macro_manager.export_macro(self.selected_macro.name, file_path):
                messagebox.showinfo("Success", f"External macro exported to '{file_path}'!")
            else:
                messagebox.showerror("Error", f"Failed to export external macro.")
    
    def _on_view_external_macro_in_editor(self, event=None):
        """View the selected external macro in the code editor."""
        if not self.selected_macro:
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
            macro_content = f"; External Macro: {self.selected_macro.name}\n"
            if self.selected_macro.description:
                macro_content += f"; Description: {self.selected_macro.description}\n"
            if self.selected_macro.category:
                macro_content += f"; Category: {self.selected_macro.category}\n"
            macro_content += "; Type: External (executed by controller)\n"
            macro_content += ";\n"
            
            # Add the macro commands
            macro_content += '\n'.join(self.selected_macro.commands)
            
            # Load the content into the editor
            main_window.code_editor.delete('1.0', tk.END)
            main_window.code_editor.insert('1.0', macro_content)
            
            # Update window title and status
            main_window.current_file_path = f"[External Macro] {self.selected_macro.name}"
            if hasattr(main_window, 'file_status'):
                main_window.file_status.set(f"Viewing: {self.selected_macro.name} (External Macro)")
            
            # Mark as clean since we just loaded this content
            if hasattr(main_window, 'mark_editor_clean'):
                main_window.mark_editor_clean()
            
            # Log the action
            if hasattr(main_window, '_log_message'):
                main_window._log_message(f"Loaded external macro '{self.selected_macro.name}' into editor")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load macro into editor: {e}")
    
    def _get_main_window(self):
        """Get reference to main window."""
        parent = self.master
        while parent:
            if hasattr(parent, 'macro_executor') or hasattr(parent, 'local_macro_manager'):
                return parent
            parent = parent.master
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
    """Dialog for creating/editing external macros."""
    
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