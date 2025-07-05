# G-Code Debugger for Buildbotics Controller

A comprehensive debugging tool for stepping through G-code files with full control over execution, breakpoints, and state monitoring.

## Features

- **Step-by-step execution** with full control
- **Breakpoint system** for stopping at specific lines
- **Line editing** capability during debugging
- **Go-back functionality** with state restoration
- **Context window** showing lines around current execution
- **Local Macro Systen for holding gcode to be sent but not stored on the controller
- **External Macro system** for creeating, editing, and running of macros stored on the controller
- **Real-time machine monitoring**
- **Emergency stop** with ESC key
- **Syntax highlighting** for G-code
- **Skip and jump** functionality
- **MDI** for manual G-code input
- **MSG and DEBUG commands** for sending messages to the controller to display variables

## Installation

1. Ensure you have Python 3.7+ installed
2. Install required dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Usage

### Starting the Application

```bash
cd Tools/gcode_debugger
python main.py
```

Or make it executable and run directly:

```bash
chmod +x main.py
./main.py
```

### Basic Operation

1. **Open a G-code file**: File → Open or Ctrl+O
2. **Set breakpoints**: Click on line numbers or press F9
3. **Start debugging**: Use the control buttons or keyboard shortcuts

### Keyboard Shortcuts

| Shortcut | Action |
|----------|--------|
| `F5` | Continue execution |
| `F10` | Step over (next line) |
| `Shift+F10` | Go back to previous line |
| `Ctrl+F10` | Step to specific line |
| `Shift+F11` | Skip current line |
| `Ctrl+Shift+F10` | Skip to specific line |
| `F9` | Toggle breakpoint at current line |
| `Ctrl+Break` | Pause execution |
| `Shift+F5` | Stop execution |
| `Esc` | Emergency stop |
| `Ctrl+O` | Open G-code file |
| `Ctrl+Q` | Exit application |

### Debug Controls

- **▶️ Continue**: Resume execution from current line until breakpoint or end
- **⏸️ Pause**: Pause the current execution
- **⏭️ Step Over**: Execute current line and move to next
- **⏩ Step To...**: Execute until reaching specified line number
- **⏪ Go Back**: Return to previous execution point (with state restoration)
- **🔄 Skip Line**: Skip current line without executing
- **🎯 Skip To...**: Jump to specified line without execution
- **🛑 Stop**: Stop execution completely
- **🚨 E-Stop**: Emergency stop (also ESC key)

### Breakpoints

- Click on line numbers to toggle breakpoints
- Red dots indicate active breakpoints
- Execution will pause when reaching a breakpoint
- Use Debug menu to clear all breakpoints

### Line Editing
- Double-click on G-code lines to edit them
- Modified lines are highlighted in yellow
- Changes are applied immediately to the debugging session and the G-code file

### LocalMacros
The application includes a built-in macro system:
- **Local macros are stored in the debugger and are not sent to the controller**
- **Local macros are not stored in a local file
- **Local macros are selected from a local panel**

#### External Macros
External macros are stored on the controller and are executed by the controller when the macro is run.
- **System Macros**: Home All, Zero All, Safe Z, Spindle On/Off
- **Tool Change**: Automated tool change sequence
- **Probing**: Z-axis probing with automatic zero setting
- **Custom Macros**: Create your own macro sequences

#### Creating Macros
1. Select Local or External from the Macros panel
2. Click "➕ New" in the Macros panel
3. Enter name, description, and G-code commands
4. Choose a category for organization
5. Save the macro for future use

#### Importing/Exporting Macros
- **Import**: Load macros from existing G-code files
- **Export**: Save macros as G-code files for external use

### Machine Status

The status panel shows real-time information:

- **Machine State**: READY, RUNNING, HOLDING, etc.
- **Position**: Current X, Y, Z coordinates
- **Feed Rate**: Current feed rate setting
- **Spindle**: Speed and on/off status
- **Tool**: Current tool number
- **Units**: Imperial or metric mode

### Context Window
Shows lines around the current execution point:
- Current line marked with ►
- Breakpoints shown with red highlighting
- Syntax highlighting for better readability

## Configuration

### Controller Connection

The debugger automatically attempts to connect to `bbctrl.local` on startup. If your controller has a different address, you can modify the connection settings in the code or use IP address instead.

### Safety Settings

The application includes several safety features:
- Confirmation dialogs for dangerous moves
- Emergency stop always available
- Speed and position limit checking
- Safe Z height for tool changes

## Troubleshooting

### Connection Issues

1. Ensure the Buildbotics controller is powered on and connected to network
2. Verify you can access the web interface at `http://bbctrl.local`
3. Check that WebSocket connections are not blocked by firewall
4. Try using the controller's IP address instead of `bbctrl.local`

### Application Issues

1. Check that all dependencies are installed: `pip install -r requirements.txt`
2. Ensure Python 3.7+ is being used
3. Check console output for error messages
4. Verify G-code file format is supported

### Performance Issues

1. Large G-code files may load slowly
2. Reduce context window size for better performance
3. Limit execution stack size in debugger settings

## File Formats

Supported G-code file extensions:
- `.nc` - Numerical Control files
- `.gcode` - G-code files
- `.tap` - Tape files
- `.cnc` - CNC files
- `.ngc` - Next Generation Controller files
- `.gc` - G-code files (short extension)

## Development

### Project Structure

```
gcode_debugger/
├── main.py              # Application entry point
├── gui/                 # GUI components
│   ├── main_window.py   # Main application window
│   ├── code_editor.py   # G-code editor with syntax highlighting
│   ├── control_panel.py # Debug control buttons
│   ├── status_panel.py  # Machine status display
│   └── macro_panel.py   # Macro management
├── core/                # Core functionality
│   ├── communication.py # WebSocket/HTTP communication
│   ├── debugger.py      # Debug engine
│   ├── gcode_parser.py  # G-code file parsing
│   └── macro_manager.py # Macro system
└── macros/              # Default macro files
```

### Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## License

This software is part of the Buildbotics firmware project and follows the same license terms.

## Support

For support and questions:
1. Check the Buildbotics documentation
2. Visit the Buildbotics community forums
3. Contact support@buildbotics.com

## Version History

### v1.0.0
- Initial release
- Full debugging functionality
- Macro system
- Real-time machine monitoring
- Breakpoint and line editing support