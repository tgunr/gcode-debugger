"""
Core functionality for the G-code Debugger application.
"""

from .communication import BBCtrlCommunicator, CommunicationError
from .debugger import GCodeDebugger, DebugState, ExecutionFrame
from .gcode_parser import GCodeParser, GCodeLine
from .macro_manager import MacroManager, MacroExecutor, MacroRecorder, Macro

__all__ = [
    'BBCtrlCommunicator',
    'CommunicationError',
    'GCodeDebugger', 
    'DebugState',
    'ExecutionFrame',
    'GCodeParser',
    'GCodeLine',
    'MacroManager',
    'MacroExecutor',
    'MacroRecorder',
    'Macro'
]