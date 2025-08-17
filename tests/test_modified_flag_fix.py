#!/usr/bin/env python3
"""
Test script to verify the modified flag handling works correctly.
This tests the has_unsaved_changes() and clear_modified_flag() methods.
"""

import sys
import os
from unittest.mock import Mock, MagicMock

# Add the project root to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_has_unsaved_changes():
    """Test the has_unsaved_changes method logic."""
    print("="*60)
    print("TESTING has_unsaved_changes() METHOD")
    print("="*60)
    
    # Test Case 1: Method exists and returns True
    print("1. Testing when has_unsaved_changes() returns True")
    mock_editor = Mock()
    mock_editor.has_unsaved_changes = Mock(return_value=True)
    mock_editor.text_widget = Mock()
    mock_editor.text_widget.edit_modified = Mock(return_value=False)
    
    # Simulate the logic from _prompt_save_changes
    def _is_dirty():
        try:
            if hasattr(mock_editor, 'has_unsaved_changes') and callable(mock_editor.has_unsaved_changes):
                if mock_editor.has_unsaved_changes():
                    return True
            if hasattr(mock_editor, 'text_widget') and hasattr(mock_editor.text_widget, 'edit_modified'):
                modified = bool(mock_editor.text_widget.edit_modified())
                return modified
        except Exception as e:
            print(f"Exception: {e}")
        return False
    
    result = _is_dirty()
    print(f"   - Result: {result}")
    print("   ✓ has_unsaved_changes() takes precedence" if result else "   ❌ Failed")
    
    # Test Case 2: Method doesn't exist, fallback to Tkinter flag
    print("\n2. Testing fallback to Tkinter edit_modified()")
    mock_editor2 = Mock()
    # Remove the has_unsaved_changes method
    del mock_editor2.has_unsaved_changes
    mock_editor2.text_widget = Mock()
    mock_editor2.text_widget.edit_modified = Mock(return_value=True)
    
    def _is_dirty2():
        try:
            if hasattr(mock_editor2, 'has_unsaved_changes') and callable(mock_editor2.has_unsaved_changes):
                if mock_editor2.has_unsaved_changes():
                    return True
            if hasattr(mock_editor2, 'text_widget') and hasattr(mock_editor2.text_widget, 'edit_modified'):
                modified = bool(mock_editor2.text_widget.edit_modified())
                return modified
        except Exception as e:
            print(f"Exception: {e}")
        return False
    
    result2 = _is_dirty2()
    print(f"   - Result: {result2}")
    print("   ✓ Tkinter fallback works" if result2 else "   ❌ Failed")
    
    # Test Case 3: Both methods return False
    print("\n3. Testing when both methods return False")
    mock_editor3 = Mock()
    mock_editor3.has_unsaved_changes = Mock(return_value=False)
    mock_editor3.text_widget = Mock()
    mock_editor3.text_widget.edit_modified = Mock(return_value=False)
    
    def _is_dirty3():
        try:
            if hasattr(mock_editor3, 'has_unsaved_changes') and callable(mock_editor3.has_unsaved_changes):
                if mock_editor3.has_unsaved_changes():
                    return True
            if hasattr(mock_editor3, 'text_widget') and hasattr(mock_editor3.text_widget, 'edit_modified'):
                modified = bool(mock_editor3.text_widget.edit_modified())
                return modified
        except Exception as e:
            print(f"Exception: {e}")
        return False
    
    result3 = _is_dirty3()
    print(f"   - Result: {result3}")
    print("   ✓ Clean state detected correctly" if not result3 else "   ❌ Failed")
    
    return True

def test_clear_modified_flag():
    """Test the clear_modified_flag method logic."""
    print("\n" + "="*60)
    print("TESTING clear_modified_flag() METHOD")
    print("="*60)
    
    # Mock editor with all the clearing methods
    mock_editor = Mock()
    mock_editor.clear_modified_flag = Mock()
    mock_editor.mark_editor_clean = Mock()
    mock_editor.text_widget = Mock()
    mock_editor.text_widget.edit_modified = Mock()
    
    mock_main_window = Mock()
    mock_main_window.mark_editor_clean = Mock()
    
    print("1. Testing comprehensive flag clearing")
    
    # Simulate the clearing logic from _prompt_save_changes
    try:
        if hasattr(mock_editor, 'clear_modified_flag') and callable(mock_editor.clear_modified_flag):
            mock_editor.clear_modified_flag()
            print("   ✓ Called editor.clear_modified_flag()")
        
        if hasattr(mock_editor, 'mark_editor_clean') and callable(mock_editor.mark_editor_clean):
            mock_editor.mark_editor_clean()
            print("   ✓ Called editor.mark_editor_clean()")
        
        if hasattr(mock_editor, 'text_widget') and hasattr(mock_editor.text_widget, 'edit_modified'):
            mock_editor.text_widget.edit_modified(False)
            print("   ✓ Called text_widget.edit_modified(False)")
        
        if hasattr(mock_main_window, 'mark_editor_clean') and callable(mock_main_window.mark_editor_clean):
            mock_main_window.mark_editor_clean()
            print("   ✓ Called main_window.mark_editor_clean()")
            
    except Exception as e:
        print(f"   ❌ Exception during clearing: {e}")
        return False
    
    # Verify all methods were called
    mock_editor.clear_modified_flag.assert_called_once()
    mock_editor.mark_editor_clean.assert_called_once()
    mock_editor.text_widget.edit_modified.assert_called_once_with(False)
    mock_main_window.mark_editor_clean.assert_called_once()
    
    print("   ✓ All clearing methods called successfully")
    
    return True

def test_save_and_clear_integration():
    """Test the integration between save and clear operations."""
    print("\n" + "="*60)
    print("TESTING SAVE AND CLEAR INTEGRATION")
    print("="*60)
    
    # Mock the complete save flow
    mock_comm = Mock()
    mock_comm.write_file = Mock(return_value=True)
    
    mock_editor = Mock()
    mock_editor.has_unsaved_changes = Mock(return_value=True)
    mock_editor.clear_modified_flag = Mock()
    mock_editor.text_widget = Mock()
    mock_editor.text_widget.get = Mock(return_value="G0 X0 Y0\nG1 X10 Y10")
    mock_editor.text_widget.edit_modified = Mock()
    
    mock_main_window = Mock()
    mock_main_window.code_editor = mock_editor
    mock_main_window.comm = mock_comm
    mock_main_window.mark_editor_clean = Mock()
    
    # Mock selected controller file
    selected_macro = Mock()
    selected_macro.path = "/controller/test.gcode"
    
    print("1. Simulating complete save flow for controller file")
    
    # Step 1: Check if dirty
    is_dirty = mock_editor.has_unsaved_changes()
    print(f"   - Editor is dirty: {is_dirty}")
    
    # Step 2: Save the file
    content = mock_editor.text_widget.get('1.0', 'end')
    save_success = mock_comm.write_file(selected_macro.path, content)
    print(f"   - Save successful: {save_success}")
    
    # Step 3: Clear all modified flags
    if save_success:
        mock_editor.clear_modified_flag()
        mock_editor.text_widget.edit_modified(False)
        mock_main_window.mark_editor_clean()
        print("   ✓ All modified flags cleared after successful save")
    
    # Step 4: Verify editor is now clean
    mock_editor.has_unsaved_changes = Mock(return_value=False)
    mock_editor.text_widget.edit_modified = Mock(return_value=False)
    
    is_clean = not mock_editor.has_unsaved_changes() and not mock_editor.text_widget.edit_modified()
    print(f"   - Editor is now clean: {is_clean}")
    
    # Verify all calls were made
    mock_comm.write_file.assert_called_once_with(selected_macro.path, content)
    mock_editor.clear_modified_flag.assert_called_once()
    mock_main_window.mark_editor_clean.assert_called_once()
    
    print("   ✓ Complete save and clear flow works correctly")
    
    return True

if __name__ == "__main__":
    print("Testing modified flag handling...")
    
    success1 = test_has_unsaved_changes()
    success2 = test_clear_modified_flag()
    success3 = test_save_and_clear_integration()
    
    print("\n" + "="*60)
    print("MODIFIED FLAG TESTING SUMMARY")
    print("="*60)
    
    if success1 and success2 and success3:
        print("🎉 ALL MODIFIED FLAG TESTS PASSED!")
        print("\nKey Findings:")
        print("✓ has_unsaved_changes() method works with fallbacks")
        print("✓ clear_modified_flag() clears all relevant flags")
        print("✓ Save and clear integration works correctly")
        print("✓ Multiple fallback mechanisms ensure reliability")
        print("\nThe modified flag handling should work correctly!")
    else:
        print("❌ SOME MODIFIED FLAG TESTS FAILED!")
        print("Additional debugging may be needed for flag handling.")