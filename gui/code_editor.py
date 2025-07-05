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
        
        # Colors and fonts
        self.colors = {
            'background': '#1e1e1e',
            'foreground': '#d4d4d4',
            'gcode': '#569cd6',      # Blue for G/M codes
            'coordinates': '#b5cea8', # Green for coordinates
            'comments': '#6a9955',    # Dark green for comments
            'numbers': '#b5cea8',     # Light green for numbers
            'current_line': '#3a3d41', # Dark gray for current line
            'breakpoint': '#ff0000',   # Red for breakpoints
            'line_numbers': '#858585', # Gray for line numbers
            'modified': '#ffff99'      # Yellow for modified lines
        }
        
        self.setup_ui()
        self.setup_syntax_patterns()
    
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
    
    def load_gcode(self, parser: GCodeParser):
        """Load G-code from parser into the editor."""
        self.parser = parser
        
        # Clear existing content
        self.text_widget.delete('1.0', tk.END)
        
        # Load lines
        for line in parser.lines:
            self.text_widget.insert(tk.END, line.original + '\n')
        
        # Update line numbers and syntax highlighting
        self._update_line_numbers()
        self._apply_syntax_highlighting()
        self._mark_modified_lines()
    
    def load_text_content(self, content: str, title: str = "Text Content"):
        """Load text content directly into the editor (for viewing macros, etc.)."""
        # Clear existing content
        self.text_widget.delete('1.0', tk.END)
        
        # Clear parser since we're not loading from a parser
        self.parser = None
        
        # Insert content
        self.text_widget.insert('1.0', content)
        
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
        content = self.text_widget.get('1.0', tk.END)
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
        if not self.parser:
            return
        
        for line in self.parser.lines:
            if line.is_modified:
                start_index = f"{line.line_number}.0"
                end_index = f"{line.line_number}.end"
                self.text_widget.tag_add('modified', start_index, end_index)
    
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
        """Handle text changes."""
        # Reapply syntax highlighting after a short delay
        self.after_idle(self._apply_syntax_highlighting)
    
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