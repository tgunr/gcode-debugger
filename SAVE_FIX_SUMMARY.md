# Controller File Save Issue - Debug Summary & Fix

## Problem Description
The user reported a critical save issue with controller files:
1. Click on a controller file → loads into editor
2. Make changes → click 'Save'
3. Select another file → get unsaved changes dialog (shouldn't happen)
4. Click back to first file → changes are reverted
5. **Result**: File not saved to local cache OR sent to controller

## Root Cause Analysis

### Investigation Process
1. **Added comprehensive debug logging** to track the save operation flow
2. **Analyzed the save architecture** across three key files:
   - `gui/main_window.py`: Main save function that delegates to macro panel
   - `gui/code_editor.py`: Editor state tracking and modified flag management  
   - `gui/macro_panel.py`: Actual save implementation for different file types

### Key Finding: Architectural Mismatch
The core issue was **architectural**: controller files and local macros have different formats and save mechanisms, but were being handled by the same code path.

- **Local Macros**: Structured format with headers like `; Local Macro: name`
- **Controller Files**: Raw G-code files without special formatting
- **Problem**: The `_save_current_macro()` method was trying to parse controller files as macro format, failing when they didn't match the expected structure

## The Fix

### Modified `gui/macro_panel.py`
Restructured the `_save_current_macro()` method to handle controller files differently:

```python
# For controller files, handle them as raw files (not macros)
if not is_local:
    print("DEBUG: This is a controller file - saving as raw file")
    # Check if we have a selected controller file
    if not hasattr(self, 'selected_macro') or self.selected_macro is None:
        print("DEBUG: No controller file selected, cannot save")
        return False
    
    # For controller files, we need to save back to the controller
    print(f"DEBUG: Attempting to save controller file: {self.selected_macro.name}")
    
    # Get the file path from the selected macro
    if hasattr(self.selected_macro, 'path'):
        file_path = self.selected_macro.path
        print(f"DEBUG: Controller file path: {file_path}")
        
        # Save the content back to the controller
        try:
            if hasattr(main_window, 'comm') and main_window.comm:
                print("DEBUG: Saving content to controller via main_window.comm")
                success = main_window.comm.write_file(file_path, content)
                print(f"DEBUG: Controller file save result: {success}")
                return success
            elif hasattr(self, 'comm') and self.comm:
                print("DEBUG: Saving content to controller via self.comm")
                success = self.comm.write_file(file_path, content)
                print(f"DEBUG: Controller file save result: {success}")
                return success
            else:
                print("DEBUG: No comm object available")
                return False
        except Exception as e:
            print(f"DEBUG: Error saving to controller: {e}")
            import traceback
            traceback.print_exc()
            return False
    else:
        print("DEBUG: Selected macro has no path attribute")
        return False

# For local macros, parse the content to extract the macro name and commands
# [Original macro parsing logic continues...]
```

### Key Changes
1. **Early Detection**: Detect controller files before attempting macro parsing
2. **Direct Save**: Use `comm.write_file()` directly for controller files
3. **Raw Content**: Preserve raw G-code content without modification
4. **Bypass Parsing**: Skip macro header parsing for controller files
5. **Maintain Compatibility**: Local macros still use original parsing logic

## Verification

### Test Results
Created and ran `test_save_fix.py` which confirmed:
- ✅ Controller files are detected correctly
- ✅ Controller files bypass macro parsing
- ✅ Controller files use `comm.write_file()` directly
- ✅ Raw content is preserved without modification
- ✅ Local macros still use the original parsing logic

### Debug Logging Added
Enhanced logging throughout the save flow:
- `gui/main_window.py`: Save function entry and delegation
- `gui/code_editor.py`: Content comparison and modified flag tracking
- `gui/macro_panel.py`: Tab detection, file type identification, and save operations

## Expected Behavior After Fix

### Before Fix (Broken)
1. User clicks controller file → loads into editor
2. User makes changes → clicks 'Save'
3. Save attempts to parse as macro → fails silently
4. File not saved to controller
5. Modified flag not cleared
6. User sees unsaved changes dialog when switching files

### After Fix (Working)
1. User clicks controller file → loads into editor
2. User makes changes → clicks 'Save'
3. Save detects controller file → uses `comm.write_file()` directly
4. Raw content sent to controller successfully
5. Modified flag cleared properly
6. No unsaved changes dialog when switching files

## Files Modified
- `gui/macro_panel.py`: Major restructuring of `_save_current_macro()` method
- Added comprehensive debug logging throughout save flow
- Fixed indentation issues in the save logic

## Testing
- Created `test_save_fix.py` to verify the fix logic
- All tests pass confirming the architectural fix is correct
- Ready for user testing with actual controller connection

The fix addresses the exact issue reported by the user and should resolve the controller file save problem completely.