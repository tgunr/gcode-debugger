#!/usr/bin/env python3
"""
Unit tests for CodeEditor modification state tracking.
"""

import unittest
import tkinter as tk
from gui.code_editor import CodeEditor

class TestCodeEditorModificationState(unittest.TestCase):
    def setUp(self):
        """Create a root window and CodeEditor instance for testing."""
        self.root = tk.Tk()
        self.editor = CodeEditor(self.root)
    
    def tearDown(self):
        """Clean up resources after each test."""
        self.root.destroy()
    
    def test_initial_state_not_modified(self):
        """Test that the editor starts in an unmodified state."""
        self.assertFalse(self.editor._is_modified, 
                         "Editor should start in an unmodified state")
        self.assertFalse(self.editor.has_unsaved_changes(), 
                         "Editor should report no unsaved changes initially")
    
    def test_modification_tracking(self):
        """Test that modifications are correctly tracked."""
        # Get initial content
        initial_content = self.editor.text_widget.get('1.0', 'end-1c')
        
        # Insert some text
        self.editor.text_widget.insert('1.0', "Test modification")
        
        # Allow for any async operations to complete
        self.root.update()
        
        # Check modification state
        self.assertTrue(self.editor._is_modified, 
                        "Editor should be marked as modified after text change")
        self.assertTrue(self.editor.has_unsaved_changes(), 
                        "Editor should report unsaved changes after modification")
    
    def test_clear_modified_flag(self):
        """Test clearing the modified flag."""
        # Insert some text
        self.editor.text_widget.insert('1.0', "Test modification")
        self.root.update()
        
        # Verify modified state
        self.assertTrue(self.editor._is_modified, 
                        "Editor should be modified before clearing")
        
        # Clear modified flag
        result = self.editor.clear_modified_flag()
        self.assertTrue(result, "clear_modified_flag should return True")
        
        # Verify unmodified state
        self.assertFalse(self.editor._is_modified, 
                         "Editor should not be modified after clearing")
        self.assertFalse(self.editor.has_unsaved_changes(), 
                         "Editor should report no unsaved changes after clearing")
    
    def test_whitespace_handling(self):
        """Test that whitespace differences are handled correctly."""
        # Insert content with extra whitespace
        self.editor.text_widget.insert('1.0', "Test content  \n")
        self.root.update()
        
        # Clear modified flag
        self.editor.clear_modified_flag()
        
        # Insert equivalent content without extra whitespace
        self.editor.text_widget.delete('1.0', 'end-1c')
        self.editor.text_widget.insert('1.0', "Test content\n")
        self.root.update()
        
        # Verify unmodified state
        self.assertFalse(self.editor._is_modified, 
                         "Editor should not be modified due to whitespace differences")
        self.assertFalse(self.editor.has_unsaved_changes(), 
                         "Editor should report no unsaved changes with whitespace differences")
    
    def test_force_reset(self):
        """Test forced reset of modified flag."""
        # Insert some text
        self.editor.text_widget.insert('1.0', "Test modification")
        self.root.update()
        
        # Verify modified state
        self.assertTrue(self.editor._is_modified, 
                        "Editor should be modified before clearing")
        
        # Clear modified flag with force reset
        result = self.editor.clear_modified_flag(force_reset=True)
        self.assertTrue(result, "clear_modified_flag should return True with force reset")
        
        # Verify unmodified state
        self.assertFalse(self.editor._is_modified, 
                         "Editor should not be modified after force reset")
        self.assertFalse(self.editor.has_unsaved_changes(), 
                         "Editor should report no unsaved changes after force reset")

if __name__ == '__main__':
    unittest.main()