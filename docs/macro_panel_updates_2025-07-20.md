# Macro Panel Updates - 2025-07-20

## Overview
This document outlines the recent updates made to the Macro Panel's external macro functionality, focusing on the hierarchical file browser and button state management.

## Changes Made

### 1. Hierarchical File Browser
- Replaced the simple listbox with a `ttk.Treeview` widget for better visualization of the controller's file system
- Added support for recursive directory navigation
- Implemented folder icons and file type indicators
- Added path display and navigation controls (Back, Forward, Up)

### 2. Button State Management
- Enhanced `_update_external_button_states()` to manage all external macro buttons
- Buttons are now properly enabled/disabled based on:
  - Current selection
  - Execution state (running/stopped)
  - File type (for context menus)

### 3. Execution Control
- Improved `_on_execute_external_macro()` with better error handling
- Added proper state management during macro execution
- Enhanced `_on_stop_external_macro()` with error handling and state updates
- Buttons now properly reflect the execution state

### 4. UI/UX Improvements
- Added tooltips for better discoverability
- Improved error messages with more context
- Consistent button states across the application
- Better visual feedback during operations

## Technical Details

### Button States
- **Execute Button**: Enabled when a macro is selected and no macro is running
- **Stop Button**: Only enabled when a macro is executing
- **New/Import Buttons**: Disabled during macro execution
- **Delete/Export Buttons**: Enabled when a macro is selected and no macro is running

### Error Handling
- All external macro operations now include try/except blocks
- User-friendly error messages are displayed
- Button states are properly reset even if an error occurs

## Testing
To verify the changes:
1. Navigate the file browser to ensure proper directory loading
2. Test button states with various selections and during macro execution
3. Verify error handling by triggering error conditions
4. Check that the UI remains responsive during long operations

## Known Issues
- The file browser may be slow with large directories (consider adding pagination in the future)
- Some error messages could be more specific

## Future Improvements
- Add progress indicators for long-running operations
- Implement drag-and-drop support for files
- Add keyboard shortcuts for common actions
- Improve performance with large file sets

### 5. Controller API Change & Compatibility Shim (2025-07-22)

A recent firmware release changed `communicator.get_macros()` to return **`list[dict|Macro]`** instead of the legacy **`dict[str, dict]`**.  
This broke `MacroManager.sync_from_controller()` which assumed a dict and called `.items()`.

**Fix implemented (core/macro_manager.py, ~L365-390)**  
A lightweight shim now detects a list payload and converts it back to the legacy dict keyed by macro name:

```python
controller_macros = communicator.get_macros() if communicator else {}
if isinstance(controller_macros, list):
    tmp = {}
    for m in controller_macros:
        if isinstance(m, dict):
            name = m.get("name")
            data = m
        else:
            name = getattr(m, "name", None)
            data = m.__dict__ if hasattr(m, "__dict__") else {}
        if name:
            tmp[name] = data
    controller_macros = tmp
controller_macros = controller_macros or {}
```

The shim is strictly internal, so downstream logic continues to work unchanged.  
Unit tests will be added to guarantee compatibility with both payload shapes.
