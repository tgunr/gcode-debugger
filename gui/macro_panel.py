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
        """Setup the external macros tab with a list of available macros and action buttons."""
        # External macro list frame with border and padding
        list_frame = ttk.LabelFrame(self.external_frame, text="Available Macros", padding=5)
        list_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Configure grid weights for the frame
        list_frame.columnconfigure(0, weight=1)
        list_frame.rowconfigure(0, weight=1)
        
        # Create a frame for the listbox and scrollbar
        list_container = ttk.Frame(list_frame)
        list_container.grid(row=0, column=0, sticky='nsew')
        
        # Configure grid weights for the container
        list_container.columnconfigure(0, weight=1)
        list_container.rowconfigure(0, weight=1)
        
        # External macro listbox with scrollbar
        self.external_macro_listbox = tk.Listbox(
            list_container,
            height=10,  # Show 10 items by default
            font=("Arial", 10),  # Slightly larger font for better readability
            selectmode=tk.SINGLE,
            bg='white',
            fg='black',
            selectbackground='#4a7abc',
            selectforeground='white',
            activestyle='none',  # Remove underline on active item
            relief=tk.FLAT,
            borderwidth=1,
            highlightthickness=1
        )
        
        # Add a vertical scrollbar
        scrollbar = ttk.Scrollbar(
            list_container,
            orient=tk.VERTICAL,
            command=self.external_macro_listbox.yview
        )
        
        # Configure the listbox to use the scrollbar
        self.external_macro_listbox.configure(yscrollcommand=scrollbar.set)
        
        # Grid the listbox and scrollbar
        self.external_macro_listbox.grid(row=0, column=0, sticky='nsew')
        scrollbar.grid(row=0, column=1, sticky='ns')
        
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
        
        # Edit button removed - double-click macro to edit in debugger
        
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
        """Refresh the external macro list display."""
        try:
            # Clear the listbox first
            self.external_macro_listbox.delete(0, tk.END)
            
            # Get all macros from the manager
            external_macros = self.macro_manager.get_all_macros()
            
            # Try to reload macros if none found
            if not external_macros and hasattr(self.macro_manager, 'load_macros'):
                self.macro_manager.load_macros()
                external_macros = self.macro_manager.get_all_macros()
            
            # Sort macros by category and name (case-insensitive)
            sorted_macros = sorted(
                external_macros,
                key=lambda m: (str(getattr(m, 'category', '')).lower(), 
                             str(getattr(m, 'name', '')).lower())
            )
            
            # Add macros to the listbox
            for macro in sorted_macros:
                try:
                    # Get macro attributes with safe defaults
                    name = str(getattr(macro, 'name', 'Unnamed')).strip()
                    category = str(getattr(macro, 'category', 'uncategorized')).strip()
                    desc = str(getattr(macro, 'description', '')).strip()
                    
                    # Get emoji prefix for the category
                    color_prefix = self._get_category_prefix(category)
                    
                    # Build display text
                    display_text = f"{color_prefix} {name}"
                    if desc:
                        display_text += f" - {desc[:25]}"
                        if len(desc) > 25:
                            display_text += "..."
                    
                    # Add to listbox
                    self.external_macro_listbox.insert(tk.END, display_text)
                    
                except Exception as e:
                    print(f"Error processing macro: {str(e)}")
                    continue
            
        except Exception as e:
            print(f"Error refreshing external macro list: {str(e)}")
            # Show error in the UI
            self.external_macro_listbox.insert(tk.END, "Error loading macros. Check console for details.")
        
        self._update_external_button_states()
    
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
        """Update external macro button enabled/disabled states."""
        has_selection = self.selected_macro is not None
        
        self.external_execute_btn.config(state=tk.NORMAL if has_selection else tk.DISABLED)
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
            macro_content = f"; External Macro: {self.selected_macro.name}\n"
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
            main_window.current_file_path = f"[External Macro] {self.selected_macro.name}"
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
    def _get_main_window(self):
        """Get reference to main window."""
        # Try to get the root window first
        root = self.winfo_toplevel()
        
        # If we have a root and it has a main_window attribute, return that
        if hasattr(root, 'main_window') and root.main_window is not None:
            return root.main_window
            
        # Fallback: search up the widget hierarchy
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