# Development Environment Memory

## CRITICAL: Application Execution Issues

### ❌ DO NOT TRY THESE COMMANDS (They fail on this system):
- `python main.py` → Command not found
- `python3 main.py` → Crashes with macOS compatibility issues:
  ```
  macOS 26 (2600) or later required, have instead 16 (1600) !
  Abort trap: 6
  ```

### ✅ WORKING APPROACH:
- **Cannot run the full GUI application** due to macOS version compatibility
- **Use isolated test scripts** to verify logic without GUI dependencies
- **Test scripts work fine** with `python3 test_script.py`

## System Environment
- **OS**: macOS with older version (16/1600 instead of required 26/2600)
- **Python**: python3 available, python not available
- **GUI Framework**: Tkinter has compatibility issues with this macOS version
- **Working Directory**: `/Volumes/Work/Buildbotics/gcode-debugger`

## Testing Strategy That Works
1. **Create isolated test scripts** that mock GUI components
2. **Use unittest.mock** to simulate application behavior
3. **Test logic without Tkinter dependencies**
4. **Verify fixes through unit tests, not live application**

## Successful Test Commands
```bash
cd /Volumes/Work/Buildbotics/gcode-debugger
python3 test_save_fix.py          # ✅ Works - tests save logic
python3 test_modified_flag_fix.py # ✅ Works - tests flag handling
```

## Files That Can Be Modified Safely
- `gui/macro_panel.py` - Core save logic (modified successfully)
- `gui/main_window.py` - Main window logic (enhanced with debug logging)
- `gui/code_editor.py` - Editor logic (enhanced with debug logging)
- Test scripts - Always work for verification

## Key Lessons Learned
1. **Don't attempt to run main.py** - it will always fail on this system
2. **Focus on unit testing** the specific logic being debugged
3. **Mock GUI components** rather than trying to instantiate them
4. **Verify fixes through isolated tests** that simulate the real behavior
5. **Use debug logging** in the actual code for when the user runs it

## Debugging Approach That Works
1. **Analyze the code** to understand the problem
2. **Add debug logging** to the actual source files
3. **Create test scripts** that simulate the problematic scenarios
4. **Verify the fix logic** through mocked tests
5. **Document the solution** for the user to test with real hardware

## Current Status
- ✅ Controller file save issue identified and fixed
- ✅ Debug logging added throughout save flow
- ✅ Test scripts verify the fix works correctly
- ✅ Ready for user testing with actual controller connection
- ❌ Cannot demonstrate with live GUI due to system limitations

## Next Time: Remember
- **Skip trying to run main.py** - go straight to test scripts
- **Focus on logic verification** through unit tests
- **Trust the test results** - they accurately simulate the real behavior
- **Document the fix clearly** for user verification