#!/usr/bin/env python3
"""
G-code Parser for G-code Debugger

Handles loading, parsing, and managing G-code files for debugging.
"""

import os
import re
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass

@dataclass
class GCodeLine:
    """Represents a single line of G-code with metadata."""
    line_number: int           # Original line number in file
    content: str              # The actual G-code content
    original: str             # Original line before processing
    is_executable: bool       # Whether this line can be executed
    is_comment: bool          # Whether this is a comment line
    is_blank: bool            # Whether this is a blank line
    is_modified: bool = False # Whether the line has been modified

class GCodeParser:
    """Parses and manages G-code files for debugging."""
    
    def __init__(self):
        self.lines: List[GCodeLine] = []
        self.filename: str = ""
        self.filepath: str = ""
        
        # G-code patterns for validation
        self.gcode_pattern = re.compile(r'^[GMTFNOS]\d+', re.IGNORECASE)
        self.coordinate_pattern = re.compile(r'[XYZABCIJKR][-+]?\d*\.?\d*', re.IGNORECASE)
        self.comment_patterns = [
            re.compile(r'^\s*;'),      # Semicolon comments
            re.compile(r'^\s*\(.*\)'), # Parentheses comments
            re.compile(r'^\s*%'),      # Percent comments
        ]
    
    def load_file(self, filepath: str) -> bool:
        """Load and parse a G-code file."""
        try:
            self.filepath = os.path.abspath(filepath)
            self.filename = os.path.basename(filepath)
            
            if not os.path.exists(self.filepath):
                raise FileNotFoundError(f"File not found: {filepath}")
            
            with open(self.filepath, 'r', encoding='utf-8') as f:
                raw_lines = f.readlines()
            
            self.lines.clear()
            
            for line_num, raw_line in enumerate(raw_lines, 1):
                processed_line = self._process_line(line_num, raw_line)
                self.lines.append(processed_line)
            
            return True
            
        except Exception as e:
            raise Exception(f"Error loading file {filepath}: {e}")
    
    def _process_line(self, line_number: int, raw_line: str) -> GCodeLine:
        """Process a single line of G-code."""
        original = raw_line.rstrip('\n\r')
        stripped = original.strip()
        
        # Check if blank line
        if not stripped:
            return GCodeLine(
                line_number=line_number,
                content="",
                original=original,
                is_executable=False,
                is_comment=False,
                is_blank=True
            )
        
        # Check if comment line
        is_comment = any(pattern.match(stripped) for pattern in self.comment_patterns)
        
        # Process content - remove inline comments
        content = self._remove_inline_comments(stripped)
        
        # Determine if executable
        is_executable = not is_comment and bool(content.strip()) and self._is_valid_gcode(content)
        
        return GCodeLine(
            line_number=line_number,
            content=content.strip(),
            original=original,
            is_executable=is_executable,
            is_comment=is_comment,
            is_blank=False
        )
    
    def _remove_inline_comments(self, line: str) -> str:
        """Remove inline comments from a line."""
        # Remove semicolon comments
        if ';' in line:
            line = line.split(';', 1)[0]
        
        # Remove parentheses comments
        while '(' in line and ')' in line:
            start = line.find('(')
            end = line.find(')', start)
            if end > start:
                line = line[:start] + line[end+1:]
            else:
                break
        
        return line.strip()
    
    def _is_valid_gcode(self, line: str) -> bool:
        """Check if a line contains valid G-code."""
        if not line.strip():
            return False
        
        # Check for G-code commands
        if self.gcode_pattern.search(line):
            return True
        
        # Check for coordinate values
        if self.coordinate_pattern.search(line):
            return True
        
        # Check for other valid codes (like feed rates, spindle speeds)
        if re.search(r'[FS]\d+', line, re.IGNORECASE):
            return True
        
        return False
    
    def get_executable_lines(self) -> List[GCodeLine]:
        """Get all executable lines."""
        return [line for line in self.lines if line.is_executable]
    
    def get_line_by_number(self, line_number: int) -> Optional[GCodeLine]:
        """Get a line by its original line number."""
        for line in self.lines:
            if line.line_number == line_number:
                return line
        return None
    
    def get_executable_line_at_index(self, index: int) -> Optional[GCodeLine]:
        """Get executable line at specific index in executable lines list."""
        executable_lines = self.get_executable_lines()
        if 0 <= index < len(executable_lines):
            return executable_lines[index]
        return None
    
    def get_context_window(self, current_line_number: int, window_size: int = 7) -> List[GCodeLine]:
        """Get lines around the current line for context display."""
        # Find the index of the current line
        current_index = -1
        for i, line in enumerate(self.lines):
            if line.line_number == current_line_number:
                current_index = i
                break
        
        if current_index == -1:
            return []
        
        # Calculate window bounds
        half_window = window_size // 2
        start_index = max(0, current_index - half_window)
        end_index = min(len(self.lines), current_index + half_window + 1)
        
        return self.lines[start_index:end_index]
    
    def modify_line(self, line_number: int, new_content: str) -> bool:
        """Modify the content of a specific line."""
        for line in self.lines:
            if line.line_number == line_number:
                line.content = new_content.strip()
                line.is_modified = True
                line.is_executable = self._is_valid_gcode(new_content)
                return True
        return False
    
    def insert_line_after(self, line_number: int, content: str) -> bool:
        """Insert a new line after the specified line number."""
        insert_index = -1
        for i, line in enumerate(self.lines):
            if line.line_number == line_number:
                insert_index = i + 1
                break
        
        if insert_index == -1:
            return False
        
        # Create new line with a fractional line number to maintain order
        new_line = GCodeLine(
            line_number=line_number + 0.5,
            content=content.strip(),
            original=content,
            is_executable=self._is_valid_gcode(content),
            is_comment=False,
            is_blank=False,
            is_modified=True
        )
        
        self.lines.insert(insert_index, new_line)
        return True
    
    def find_lines(self, pattern: str, regex: bool = False) -> List[GCodeLine]:
        """Find lines matching a pattern."""
        matches = []
        
        if regex:
            try:
                compiled_pattern = re.compile(pattern, re.IGNORECASE)
                for line in self.lines:
                    if compiled_pattern.search(line.content) or compiled_pattern.search(line.original):
                        matches.append(line)
            except re.error:
                pass
        else:
            pattern_lower = pattern.lower()
            for line in self.lines:
                if (pattern_lower in line.content.lower() or 
                    pattern_lower in line.original.lower()):
                    matches.append(line)
        
        return matches
    
    def get_line_count(self) -> int:
        """Get total number of lines."""
        return len(self.lines)
    
    def get_executable_count(self) -> int:
        """Get number of executable lines."""
        return len(self.get_executable_lines())
    
    def save_file(self, filepath: Optional[str] = None) -> bool:
        """Save the current G-code to a file."""
        save_path = filepath or self.filepath
        
        try:
            with open(save_path, 'w', encoding='utf-8') as f:
                for line in self.lines:
                    if line.is_modified:
                        f.write(line.content + '\n')
                    else:
                        f.write(line.original + '\n')
            return True
        except Exception as e:
            raise Exception(f"Error saving file {save_path}: {e}")
    
    def get_statistics(self) -> Dict[str, int]:
        """Get statistics about the loaded G-code."""
        total_lines = len(self.lines)
        executable_lines = len(self.get_executable_lines())
        comment_lines = len([line for line in self.lines if line.is_comment])
        blank_lines = len([line for line in self.lines if line.is_blank])
        modified_lines = len([line for line in self.lines if line.is_modified])
        
        return {
            'total_lines': total_lines,
            'executable_lines': executable_lines,
            'comment_lines': comment_lines,
            'blank_lines': blank_lines,
            'modified_lines': modified_lines
        }