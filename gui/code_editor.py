#!/usr/bin/env python3
"""
Code Editor for G-code Debugger

Provides syntax highlighting, breakpoints, and editing capabilities for G-code files.
"""

import tkinter as tk
from tkinter import ttk, font
import re
from typing import Set, Optional, Callable
from core.gcode_parser import GCodeParser, GCodeLine

class CodeEditor(ttk.Frame):
    """G-code editor with syntax highlighting and debugging features."""
    
    def __init__(self, parent):
        super().__init__(parent)
        
        # Callbacks
        self.breakpoint_callback: Optional[Callable] = None
        self.line_edit_callback: Optional[Callable] = None
        
        # State
        self.parser: Optional[GCodeParser] = None
        self.breakpoints: Set[int] = set()
        self.current_line = 0
        self.context_window_size = 15
        self._is_modified = False  # Track if content has been modified
        self._is_loading = False
        self._original_content = ""  # Store original content for comparison
        
        # Colors and fonts
        self.colors = {
            'background': '#1e1e1e',
            'foreground': '#d4d4d4',
            'gcode': '#569cd6',      # Blue for G/M codes
            'coordinates': '#b5cea8', # Green for coordinates
            'comments': '#6a9955',    # Dark green for comments
            'numbers': '#b5cea8',     # Light green for numbers
            'current_line': '#264f78', # Blue highlight for current line (more visible)
            'breakpoint': '#ff0000',   # Red for breakpoints
            'line_numbers': '#858585', # Gray for line numbers
            'modified': '#ffff99'      # Yellow for modified lines
        }
        
        self.setup_ui()
        self.setup_syntax_patterns()
        
        # Set initial original content
        self._original_content = self.text_widget.get('1.0', 'end-1c')
        
        # Reset modified flag
        self.text_widget.edit_modified(False)
    
    def setup_ui(self):
        """Setup the user interface."""
        # Create main frame with scrollbars
        main_frame = ttk.Frame(self)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Create text widget with scrollbars
        text_frame = tk.Frame(main_frame, bg=self.colors['background'])
        text_frame.pack(fill=tk.BOTH, expand=True)
        
        # Line numbers text widget
        self.line_numbers = tk.Text(
            text_frame,
            width=6,
            padx=3,
            takefocus=0,
            border=0,
            state='disabled',
            wrap='none',
            font=('Consolas', 10),
            bg='#252526',
            fg=self.colors['line_numbers'],
            selectbackground=self.colors['line_numbers'],
            selectforeground='#252526'
        )
        self.line_numbers.pack(side=tk.LEFT, fill=tk.Y)
        
        # Main text widget
        self.text_widget = tk.Text(
            text_frame,
            wrap='none',
            font=('Consolas', 10),
            bg=self.colors['background'],
            fg=self.colors['foreground'],
            insertbackground='white',
            selectbackground='#264f78',
            selectforeground='white',
            tabs='4c'
        )
        self.text_widget.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # Vertical scrollbar
        v_scrollbar = ttk.Scrollbar(main_frame, orient=tk.VERTICAL)
        v_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Horizontal scrollbar
        h_scrollbar = ttk.Scrollbar(self, orient=tk.HORIZONTAL)
        h_scrollbar.pack(side=tk.BOTTOM, fill=tk.X)
        
        # Configure scrolling
        self.text_widget.config(yscrollcommand=v_scrollbar.set, xscrollcommand=h_scrollbar.set)
        self.line_numbers.config(yscrollcommand=v_scrollbar.set)
        v_scrollbar.config(command=self._on_vertical_scroll)
        h_scrollbar.config(command=self.text_widget.xview)
        
        # Context window frame
        self.context_frame = ttk.LabelFrame(self, text="Context Window")
        self.context_frame.pack(fill=tk.X, pady=(5, 0))
        
        # Context window text
        self.context_text = tk.Text(
            self.context_frame,
            height=self.context_window_size,
            font=('Consolas', 9),
            bg=self.colors['background'],
            fg=self.colors['foreground'],
            state='disabled',
            wrap='none'
        )
        self.context_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Bind events
        self.text_widget.bind('<KeyRelease>', self._on_text_changed)
        self.text_widget.bind('<Button-1>', self._on_click)
        self.text_widget.bind('<MouseWheel>', self._on_mousewheel)
        self.text_widget.bind('<Control-a>', self._select_all)
        self.line_numbers.bind('<Button-1>', self._on_line_number_click)
        self.line_numbers.bind('<MouseWheel>', self._on_mousewheel)
        
        # Configure tags for syntax highlighting
        self._configure_tags()
    
    def setup_syntax_patterns(self):
        """Setup regex patterns for syntax highlighting."""
        self.syntax_patterns = [
            (r'\b[GM]\d+\b', 'gcode'),          # G and M codes
            (r'\b[XYZABCIJKR][-+]?\d*\.?\d*\b', 'coordinates'),  # Coordinates
            (r'\b[FS]\d+\b', 'gcode'),          # Feed and spindle
            (r'\bT\d+\b', 'gcode'),             # Tool numbers
            (r';.*$', 'comments'),              # Semicolon comments
            (r'\(.*?\)', 'comments'),           # Parenthesis comments
            (r'\b\d+\.?\d*\b', 'numbers'),      # Numbers
        ]
    
    def _configure_tags(self):
        """Configure text tags for syntax highlighting."""
        self.text_widget.tag_configure('gcode', foreground=self.colors['gcode'])
        self.text_widget.tag_configure('coordinates', foreground=self.colors['coordinates'])
        self.text_widget.tag_configure('comments', foreground=self.colors['comments'])
        self.text_widget.tag_configure('numbers', foreground=self.colors['numbers'])
        self.text_widget.tag_configure('current_line', background=self.colors['current_line'])
        self.text_widget.tag_configure('breakpoint', background=self.colors['breakpoint'])
        self.text_widget.tag_configure('modified', background=self.colors['modified'])
        
        # Context window tags
        self.context_text.tag_configure('gcode', foreground=self.colors['gcode'])
        self.context_text.tag_configure('coordinates', foreground=self.colors['coordinates'])
        self.context_text.tag_configure('comments', foreground=self.colors['comments'])
        self.context_text.tag_configure('current_line', background=self.colors['current_line'])
        self.context_text.tag_configure('breakpoint', background=self.colors['breakpoint'])
    
    def set_breakpoint_callback(self, callback: Callable):
        """Set callback for breakpoint toggle events."""
        self.breakpoint_callback = callback
    
    def set_line_edit_callback(self, callback: Callable):
        """Set callback for line edit events."""
        self.line_edit_callback = callback
    
    def has_unsaved_changes(self) -> bool:
        """Check if there are unsaved changes in the editor."""
        if self._is_loading:
            return False
        current_content = self.text_widget.get('1.0', 'end-1c')
        
        # Normalize content by stripping trailing whitespace and normalizing line endings
        normalized_current = '\n'.join(line.rstrip() for line in current_content.splitlines())
        normalized_original = '\n'.join(line.rstrip() for line in self._original_content.splitlines())
        
        has_changes = normalized_current != normalized_original
        
        # Enhanced logging with stack trace to identify caller
        import traceback
        caller_info = traceback.extract_stack()[-2]
        caller_filename = caller_info.filename.split('/')[-1]
        caller_lineno = caller_info.lineno
        caller_function = caller_info.name
        
        print(f"\n{'='*80}")
        print(f"DEBUG: has_unsaved_changes() called from {caller_filename}:{caller_lineno} ({caller_function})")
        print(f"DEBUG: Current content len: {len(current_content)}, Original content len: {len(self._original_content)}")
        print(f"DEBUG: Normalized current content len: {len(normalized_current)}")
        print(f"DEBUG: Normalized original content len: {len(normalized_original)}")
        print(f"DEBUG: Tkinter edit_modified: {self.text_widget.edit_modified()}")
        
        if has_changes:
            print("DEBUG: Content differs:")
            print("Current content (normalized, last 50 chars):", repr(normalized_current[-50:]))
            print("Original content (normalized, last 50 chars):", repr(normalized_original[-50:]))
            
            # Detailed diff for debugging
            from difflib import unified_diff
            diff_lines = list(unified_diff(
                normalized_original.splitlines(),
                normalized_current.splitlines(),
                fromfile='original',
                tofile='current'
            ))
            print("\nDIFF:")
            for line in diff_lines[:10]:  # Limit to first 10 diff lines
                print(line)
            if len(diff_lines) > 10:
                print(f"... and {len(diff_lines) - 10} more lines")
        
        print(f"{'='*80}\n")
        
        return has_changes
    
    def clear_modified_flag(self, log_caller=True, force_reset=False, update_original_content=True):
        """Comprehensive method to clear modified flags with enhanced logging and error handling.
        
        Args:
            log_caller (bool): Whether to log the caller's information. Defaults to True.
            force_reset (bool): Force reset even if content appears unchanged. Defaults to False.
        
        Returns:
            bool: True if the modified flag was successfully cleared, False otherwise.
        """
        import traceback
        
        # Log caller information for debugging
        if log_caller:
            caller_info = traceback.extract_stack()[-2]
            caller_filename = caller_info.filename.split('/')[-1]
            caller_lineno = caller_info.lineno
            caller_function = caller_info.name
            
            print(f"\n{'='*80}")
            print(f"DEBUG: clear_modified_flag() called from {caller_filename}:{caller_lineno} ({caller_function})")
            print(f"  Force reset: {force_reset}")
        
        # Capture current state before modification
        old_content = self._original_content
        current_content = self.text_widget.get('1.0', 'end-1c')
        
        # Normalize content to handle whitespace differences
        def normalize_content(content):
            return '\n'.join(line.rstrip() for line in content.splitlines())
        
        normalized_old = normalize_content(old_content)
        normalized_current = normalize_content(current_content)
        
        # Determine if reset is needed
        needs_reset = force_reset or normalized_old != normalized_current
        
        # Detailed logging of current state
        print(f"DEBUG: Before clearing:")
        print(f"  _is_modified: {self._is_modified}")
        print(f"  Tkinter edit_modified: {self.text_widget.edit_modified()}")
        print(f"  Old content len: {len(old_content)}")
        print(f"  Current content len: {len(current_content)}")
        print(f"  Needs reset: {needs_reset}")
        
        # Reset modified state
        if needs_reset:
            if update_original_content:
                self._original_content = current_content

            self._is_modified = False
            
            # Clear Tkinter's modified flag
            try:
                self.text_widget.edit_modified(False)
                print("DEBUG: Successfully cleared Tkinter edit_modified flag")
            except Exception as e:
                print(f"ERROR: Failed to clear Tkinter edit_modified flag: {e}")
                import traceback
                traceback.print_exc()
            
            # Mark modified lines (this might reset some state)
            self._mark_modified_lines()
        
        # Verify the change took effect
        verification = self.has_unsaved_changes()
        
        # Final state logging
        print(f"DEBUG: After clearing:")
        print(f"  _is_modified: {self._is_modified}")
        print(f"  Tkinter edit_modified: {self.text_widget.edit_modified()}")
        print(f"  Verification - has_unsaved_changes: {verification}")
        print(f"{'='*80}\n")
        
        # Raise a warning if changes are still detected
        if verification and needs_reset:
            print("WARNING: Modified flag not fully cleared!")
            print(f"Remaining changes: {repr(self.text_widget.get('1.0', 'end-1c'))}")
        
        return not verification  # Return True if successfully cleared
    
    def mark_editor_clean(self):
        """Alias for clear_modified_flag to support multiple naming conventions."""
        return self.clear_modified_flag(log_caller=False)
    
    def load_gcode(self, parser: GCodeParser):
        """Load G-code from parser into the editor."""
        self._is_loading = True
        self.parser = parser
        
        # Clear existing content
        self.text_widget.delete('1.0', tk.END)
        
        # Load lines without adding extra newline to the last line
        if parser.lines:
            for line in parser.lines[:-1]:
                self.text_widget.insert(tk.END, line.original + '\n')
            self.text_widget.insert(tk.END, parser.lines[-1].original)
        
        # Store original content
        self._original_content = self.text_widget.get('1.0', 'end-1c')
        print(f"DEBUG: load_gcode set _original_content len: {len(self._original_content)}, last 10: {repr(self._original_content[-10:])}")
        self._is_modified = False
        
        # Reset modified flag
        self.text_widget.edit_modified(False)
        
        # Update line numbers and syntax highlighting
        self._update_line_numbers()
        self._apply_syntax_highlighting()
        self._mark_modified_lines()
        self._is_loading = False
    
    def load_text_content(self, content: str, title: str = "Text Content"):
        """Load text content directly into the editor (for viewing macros, etc.)."""
        # Clear existing content
        self.text_widget.delete('1.0', tk.END)
        
        # Clear parser since we're not loading from a parser
        self._is_loading = True
        try:
            self.text_widget.delete('1.0', tk.END)
            self.text_widget.insert('1.0', content)
            self.text_widget.edit_modified(False)
            self._original_content = self.get_content()
        finally:
            self._is_loading = False
        
        print(f"DEBUG: load_text_content set _original_content len: {len(self._original_content)}, last 10: {repr(self._original_content[-10:])}")
        self._is_modified = False
        
        # Reset modified flag
        self.text_widget.edit_modified(False)
        
        # Clear line numbers since we don't have a parser
        self.line_numbers.config(state='normal')
        self.line_numbers.delete('1.0', tk.END)
        
        # Add simple line numbers
        lines = content.split('\n')
        for i in range(1, len(lines) + 1):
            self.line_numbers.insert(tk.END, f"  {i:4d}\n")
        
        self.line_numbers.config(state='disabled')
        
        # Apply basic syntax highlighting
        self._apply_syntax_highlighting()
        
        # Clear context window
        self.context_text.config(state='normal')
        self.context_text.delete('1.0', tk.END)
        self.context_text.insert('1.0', f"Viewing: {title}\n\nDouble-click a macro to view its content here.")
        self.context_text.config(state='disabled')
    
    def _update_line_numbers(self):
        """Update the line numbers display."""
        self.line_numbers.config(state='normal')
        self.line_numbers.delete('1.0', tk.END)
        
        if self.parser:
            for i, line in enumerate(self.parser.lines, 1):
                # Add breakpoint indicator
                prefix = "●" if line.line_number in self.breakpoints else " "
                line_text = f"{prefix}{i:4d}\n"
                
                self.line_numbers.insert(tk.END, line_text)
                
                # Color breakpoint lines
                if line.line_number in self.breakpoints:
                    start_index = f"{i}.0"
                    end_index = f"{i}.end"
                    self.line_numbers.tag_add('breakpoint', start_index, end_index)
        
        self.line_numbers.config(state='disabled')
    
    def _apply_syntax_highlighting(self):
        """Apply syntax highlighting to the text."""
        content = self.text_widget.get('1.0', 'end-1c')
        lines = content.split('\n')
        
        # Clear existing tags
        for tag in ['gcode', 'coordinates', 'comments', 'numbers']:
            self.text_widget.tag_remove(tag, '1.0', tk.END)
        
        for line_num, line in enumerate(lines, 1):
            if not line.strip():
                continue
            
            for pattern, tag in self.syntax_patterns:
                for match in re.finditer(pattern, line, re.IGNORECASE):
                    start = f"{line_num}.{match.start()}"
                    end = f"{line_num}.{match.end()}"
                    self.text_widget.tag_add(tag, start, end)
    
    def _mark_modified_lines(self):
        """Mark modified lines with special highlighting."""
        # First, clear all modified line highlighting
        self.text_widget.tag_remove('modified', '1.0', tk.END)
        
        # If we don't have a parser, we can't track modifications
        if not self.parser:
            return
            
        # Get current content for comparison
        current_content = self.text_widget.get('1.0', 'end-1c').splitlines()
        original_lines = self._original_content.splitlines()
        
        # Highlight modified lines
        for i in range(min(len(current_content), len(original_lines))):
            if i < len(original_lines) and (i >= len(current_content) or current_content[i] != original_lines[i]):
                line_num = i + 1  # Line numbers are 1-based
                start_index = f"{line_num}.0"
                end_index = f"{line_num}.end"
                self.text_widget.tag_add('modified', start_index, end_index)
        
        # Handle case where new lines were added at the end
        if len(current_content) > len(original_lines):
            for i in range(len(original_lines), len(current_content)):
                line_num = i + 1
                start_index = f"{line_num}.0"
                end_index = f"{line_num}.end"
                self.text_widget.tag_add('modified', start_index, end_index)
    
    def highlight_all(self) -> None:
        """
        Apply syntax highlighting to the entire editor content.
        """
        self._apply_syntax_highlighting()

    def highlight_current_line(self, line_number: int):
        """Highlight the current execution line."""
        # Remove previous current line highlighting
        self.text_widget.tag_remove('current_line', '1.0', tk.END)
        
        self.current_line = line_number
        
        if line_number > 0 and self.parser:
            # Find the actual line index in the editor
            editor_line = self._find_editor_line_for_gcode_line(line_number)
            if editor_line:
                start_index = f"{editor_line}.0"
                end_index = f"{editor_line}.end"
                self.text_widget.tag_add('current_line', start_index, end_index)
                
                # Scroll to make line visible
                self.text_widget.see(start_index)
        
        # Update context window
        self._update_context_window()
    
    def _find_editor_line_for_gcode_line(self, gcode_line_number: int) -> Optional[int]:
        """Find the editor line number for a G-code line number."""
        if not self.parser:
            return None
        
        for i, line in enumerate(self.parser.lines, 1):
            if line.line_number == gcode_line_number:
                return i
        return None
    
    def _update_context_window(self):
        """Update the context window with lines around current execution."""
        if not self.parser or self.current_line == 0:
            return
        
        # Clear context window
        self.context_text.config(state='normal')
        self.context_text.delete('1.0', tk.END)
        
        # Get context lines
        context_lines = self.parser.get_context_window(
            self.current_line, 
            self.context_window_size
        )
        
        # Display context lines
        for i, line in enumerate(context_lines, 1):
            prefix = "► " if line.line_number == self.current_line else "  "
            display_text = f"{prefix}{line.line_number:4d}: {line.original}\n"
            
            self.context_text.insert(tk.END, display_text)
            
            # Apply syntax highlighting
            line_start = f"{i}.0"
            line_end = f"{i}.end"
            
            if line.line_number == self.current_line:
                self.context_text.tag_add('current_line', line_start, line_end)
            
            if line.line_number in self.breakpoints:
                self.context_text.tag_add('breakpoint', line_start, line_end)
            
            # Apply syntax highlighting to content
            content = line.original
            for pattern, tag in self.syntax_patterns:
                for match in re.finditer(pattern, content, re.IGNORECASE):
                    start_col = match.start() + 7  # Account for prefix
                    end_col = match.end() + 7
                    start_pos = f"{i}.{start_col}"
                    end_pos = f"{i}.{end_col}"
                    self.context_text.tag_add(tag, start_pos, end_pos)
        
        self.context_text.config(state='disabled')
    
    def update_breakpoints(self, breakpoints: Set[int]):
        """Update breakpoint visualization."""
        self.breakpoints = breakpoints
        self._update_line_numbers()
        self._update_context_window()
    
    def get_current_line_number(self) -> int:
        """Get the line number at cursor position."""
        cursor_pos = self.text_widget.index(tk.INSERT)
        line_num = int(cursor_pos.split('.')[0])
        
        if self.parser and line_num <= len(self.parser.lines):
            return self.parser.lines[line_num - 1].line_number
        return 0
    
    def get_line_content(self, line_number: int) -> str:
        """Get the content of a specific line."""
        if self.parser:
            line = self.parser.get_line_by_number(line_number)
            if line:
                return line.content
        return ""
    
    def modify_line(self, line_number: int, new_content: str):
        """Modify the content of a specific line."""
        if self.parser and self.parser.modify_line(line_number, new_content):
            # Update the display
            editor_line = self._find_editor_line_for_gcode_line(line_number)
            if editor_line:
                start_index = f"{editor_line}.0"
                end_index = f"{editor_line}.end"
                
                # Replace line content
                self.text_widget.delete(start_index, end_index)
                self.text_widget.insert(start_index, new_content)
                
                # Reapply highlighting
                self._apply_syntax_highlighting()
                self._mark_modified_lines()
                
                # Notify callback
                if self.line_edit_callback:
                    self.line_edit_callback(line_number, new_content)
    
    # Event handlers
    def _on_vertical_scroll(self, *args):
        """Handle vertical scrolling for both text widgets."""
        self.text_widget.yview(*args)
        self.line_numbers.yview(*args)
    
    def _on_mousewheel(self, event):
        """Handle mouse wheel scrolling."""
        self.text_widget.yview_scroll(int(-1 * (event.delta / 120)), "units")
        self.line_numbers.yview_scroll(int(-1 * (event.delta / 120)), "units")
    
    def _on_text_changed(self, event):
        """Handle text changes with comprehensive modification tracking."""
        # Capture current content
        current_content = self.text_widget.get('1.0', 'end-1c')
        
        # Normalize content to handle whitespace differences
        def normalize_content(content):
            return '\n'.join(line.rstrip() for line in content.splitlines())
        
        normalized_current = normalize_content(current_content)
        normalized_original = normalize_content(self._original_content)
        
        # Detailed logging of text change
        print(f"\n{'='*80}")
        print(f"DEBUG: Text changed event triggered")
        print(f"  Current content length: {len(current_content)}")
        print(f"  Original content length: {len(self._original_content)}")
        print(f"  Normalized current content length: {len(normalized_current)}")
        print(f"  Normalized original content length: {len(normalized_original)}")
        
        # Mark as modified if normalized content differs
        was_modified = self._is_modified
        self._is_modified = normalized_current != normalized_original
        
        # Log modification state changes
        print(f"  Previous modified state: {was_modified}")
        print(f"  Current modified state: {self._is_modified}")
        
        # If modification state changed, log details
        if was_modified != self._is_modified:
            print("DEBUG: Modification state changed!")
            if self._is_modified:
                # Detailed diff for debugging
                from difflib import unified_diff
                diff_lines = list(unified_diff(
                    normalized_original.splitlines(),
                    normalized_current.splitlines(),
                    fromfile='original',
                    tofile='current'
                ))
                print("\nDIFF:")
                for line in diff_lines[:10]:  # Limit to first 10 diff lines
                    print(line)
                if len(diff_lines) > 10:
                    print(f"... and {len(diff_lines) - 10} more lines")
        
        # Reapply syntax highlighting after a short delay
        self.after_idle(self._apply_syntax_highlighting)
        
        # Update modified lines highlighting
        self.after_idle(self._mark_modified_lines)
        
        # Optional: Log first few characters of changes
        if self._is_modified:
            print("DEBUG: Content changes:")
            print(f"  First 50 chars of current content: {repr(current_content[:50])}")
            print(f"  First 50 chars of original content: {repr(self._original_content[:50])}")
        
        print(f"{'='*80}\n")
    
    def _on_click(self, event):
        """Handle mouse clicks."""
        # Update context window when clicking to a different line
        self.after_idle(self._update_context_window)
    
    def _on_line_number_click(self, event):
        """Handle clicks on line numbers (for breakpoint toggle)."""
        # Get the line number that was clicked
        line_pos = self.line_numbers.index(f"@{event.x},{event.y}")
        line_num = int(line_pos.split('.')[0])
        
        if self.parser and line_num <= len(self.parser.lines):
            gcode_line_number = self.parser.lines[line_num - 1].line_number
            
            # Toggle breakpoint
            if self.breakpoint_callback:
                self.breakpoint_callback(gcode_line_number)
    
    def _select_all(self, event):
        """Select all text."""
        self.text_widget.tag_add(tk.SEL, "1.0", tk.END)
        return 'break'  # Prevent default behavior
    
    def search_text(self, pattern: str, regex: bool = False):
        """Search for text in the editor."""
        if not self.parser:
            return
        
        matches = self.parser.find_lines(pattern, regex)
        
        # Clear previous search results
        self.text_widget.tag_remove('search_result', '1.0', tk.END)
        
        # Highlight matches
        for match in matches:
            editor_line = self._find_editor_line_for_gcode_line(match.line_number)
            if editor_line:
                start_index = f"{editor_line}.0"
                end_index = f"{editor_line}.end"
                self.text_widget.tag_add('search_result', start_index, end_index)
        
        # Configure search result tag
        self.text_widget.tag_configure('search_result', background='yellow', foreground='black')
        
        return len(matches)
    
    def clear_search(self):
        """Clear search highlighting."""
        self.text_widget.tag_remove('search_result', '1.0', tk.END)
    
    def goto_line(self, line_number: int):
        """Go to a specific line number."""
        editor_line = self._find_editor_line_for_gcode_line(line_number)
        if editor_line:
            self.text_widget.mark_set(tk.INSERT, f"{editor_line}.0")
            self.text_widget.see(f"{editor_line}.0")
            self._update_context_window()
