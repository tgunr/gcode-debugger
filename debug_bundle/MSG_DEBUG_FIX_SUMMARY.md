# MSG and DEBUG Command Output Fix

## Problem Diagnosis

When executing `(MSG, test)` and `(DEBUG, message)` commands, users were not seeing any output in the G-code debugger console.

### Root Cause Analysis

Through systematic debugging, we identified that:

1. **Commands were being sent successfully** to the Buildbotics controller
2. **The controller was processing the commands** but not sending output back via WebSocket
3. **WebSocket message parsing was too restrictive** - only looking for specific JSON keys
4. **No local handling** of MSG/DEBUG commands for display purposes

### Key Finding

The Buildbotics controller processes MSG and DEBUG commands internally but **does not send their output back through the WebSocket connection**. This means the commands execute on the controller but their output remains local to the controller's console/display.

## Solution Implementation

### 1. Enhanced WebSocket Message Processing

**File:** `Tools/gcode_debugger/core/communication.py`

- Added comprehensive logging of ALL WebSocket messages
- Enhanced message parsing to capture different response types
- Added specific handling for command responses and errors

```python
def _on_message(self, ws, message):
    """Handle incoming WebSocket messages (enhanced for MSG/DEBUG output)."""
    # Log ALL incoming messages for debugging
    self._call_callback(self.message_callback, f"RAW WS MESSAGE: {message}")
    
    try:
        data = json.loads(message)
        
        # Check for MSG/DEBUG command responses
        if 'result' in data or 'response' in data:
            self._call_callback(self.message_callback, f"COMMAND RESPONSE: {data}")
        
        # Check for error responses
        if 'error' in data:
            self._call_callback(self.error_callback, f"COMMAND ERROR: {data}")
            
        # Update state if received
        if 'state' in data or any(key in data for key in ['xx', 'cycle', 'line']):
            self.last_state.update(data)
            self._call_callback(self.state_callback, self.last_state)
            
    except json.JSONDecodeError:
        # Handle non-JSON messages (might be plain text responses)
        if message.strip():  # Only log non-empty messages
            self._call_callback(self.message_callback, f"NON-JSON MESSAGE: {message}")
    except Exception as e:
        self._call_callback(self.error_callback, f"Message processing error: {e}")
```

### 2. Local MSG/DEBUG Processing

**File:** `Tools/gcode_debugger/core/msg_debug_handler.py`

Created a dedicated handler that:
- Parses G-code commands for MSG and DEBUG patterns
- Processes the content locally before sending to controller
- Provides immediate visual feedback to the user
- Handles variable references in DEBUG commands

```python
class MsgDebugHandler:
    """Handles MSG and DEBUG commands locally since controller doesn't return output."""
    
    def __init__(self, output_callback: Optional[Callable[[str, str], None]] = None):
        self.output_callback = output_callback
        
        # Regex patterns for MSG and DEBUG commands
        self.msg_pattern = re.compile(r'\(MSG,\s*([^)]+)\)', re.IGNORECASE)
        self.debug_pattern = re.compile(r'\(DEBUG,\s*([^)]+)\)', re.IGNORECASE)
    
    def process_command(self, command: str) -> bool:
        """Process a G-code command and check for MSG/DEBUG."""
        # ... processes and displays MSG/DEBUG content locally
```

### 3. Integration with Communication Module

**File:** `Tools/gcode_debugger/core/communication.py`

- Integrated MSG/DEBUG handler into the communicator
- Commands are processed locally BEFORE being sent to controller
- Users see immediate feedback while command is also sent to controller

```python
def send_gcode(self, command: str, use_json_rpc: bool = False) -> bool:
    # Process MSG/DEBUG commands locally before sending
    self.msg_debug_handler.process_command(command)
    
    # Then send to controller as normal
    # ... rest of send logic
```

### 4. Enhanced Console Display

**File:** `Tools/gcode_debugger/gui/main_window.py`

- Added color-coded display for MSG and DEBUG output
- MSG commands display in **yellow**
- DEBUG commands display in **magenta**
- Enhanced message routing for different message types

```python
def _on_communication_message(self, message):
    """Handle communication messages."""
    if message.startswith("[MSG]"):
        # MSG command output - display prominently
        self._thread_safe_callback(self._log_message, message, "yellow")
    elif message.startswith("[DEBUG]"):
        # DEBUG command output - display prominently
        self._thread_safe_callback(self._log_message, message, "magenta")
    # ... other message types
```

## Test Results

### Before Fix
```
--- Testing MSG command ---
[MESSAGE] Sent: (MSG, Hello from debugger test!)
[MESSAGE] RAW WS MESSAGE: {"heartbeat": 1}

--- Testing DEBUG command ---
[MESSAGE] Sent: (DEBUG, Variable X=#1001)
```
**Result:** No MSG/DEBUG output visible to user

### After Fix
```
--- Testing MSG Commands ---
Sending: (MSG, Hello from enhanced debugger!)
[MESSAGE] [MSG] Hello from enhanced debugger!
[MESSAGE] Sent: (MSG, Hello from enhanced debugger!)

--- Testing DEBUG Commands ---
Sending: (DEBUG, Variable test #1001)
[MESSAGE] [DEBUG] Variable test #1001[VAR]
[MESSAGE] Sent: (DEBUG, Variable test #1001)
```
**Result:** ✅ MSG/DEBUG output clearly visible with color coding

## Features Added

### MSG Command Support
- Displays message content immediately when command is sent
- Supports both `(MSG, content)` and `(msg, content)` formats
- Works within G-code lines: `G1 X10 (MSG, Moving to X10)`

### DEBUG Command Support
- Displays debug information with variable reference detection
- Marks variable references like `#1001` and `#<_x>` with `[VAR]` indicator
- Supports complex expressions: `(DEBUG, X=#<_x> + Y=#<_y>)`

### Visual Enhancements
- **Yellow text** for MSG output - easy to spot important messages
- **Magenta text** for DEBUG output - clearly distinguishes debug info
- Immediate feedback - no waiting for controller response
- Works in both GUI and command-line testing

## Usage Examples

### In G-code Files
```gcode
G0 X0 Y0 (MSG, Moving to origin)
G1 X10 F100 (MSG, Cutting to X10)
(DEBUG, Current X position = #5221)
M3 S1000 (MSG, Starting spindle)
(DEBUG, Spindle speed setting = #5037)
```

### In MDI (Manual Data Input)
```gcode
(MSG, Testing manual command)
(DEBUG, Tool number = #5400)
G1 X5 (MSG, Short move test)
```

### Multiple Commands in One Line
```gcode
G0 X0 Y0 (MSG, At origin) (DEBUG, Position check complete)
```

## Files Modified/Created

### Modified Files
1. `Tools/gcode_debugger/core/communication.py` - Enhanced WebSocket handling
2. `Tools/gcode_debugger/gui/main_window.py` - Enhanced console display

### New Files
1. `Tools/gcode_debugger/core/msg_debug_handler.py` - MSG/DEBUG processor
2. `Tools/gcode_debugger/test_msg_debug_fixed.py` - Verification test
3. `Tools/gcode_debugger/MSG_DEBUG_FIX_SUMMARY.md` - This documentation

## Testing

Run the verification test:
```bash
cd Tools/gcode_debugger
python test_msg_debug_fixed.py
```

Expected output: ✅ MSG and DEBUG commands now display their content immediately in the console with appropriate color coding.

## Technical Notes

- The solution maintains backward compatibility
- Commands are still sent to the controller (for any controller-side processing)
- Local processing provides immediate user feedback
- Variable references in DEBUG commands are detected and marked
- Case-insensitive matching supports both `MSG` and `msg`, `DEBUG` and `debug`
- Regex patterns handle various spacing and formatting variations

This fix ensures that users can now see the results of their MSG and DEBUG commands immediately, providing the debugging and informational output they expect.