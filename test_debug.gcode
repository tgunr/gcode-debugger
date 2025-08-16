; Test G-code file for debugging
G21 ; Set units to millimeters
G90 ; Absolute positioning
G0 X0 Y0 Z5 ; Move to start position
G1 Z0 F100 ; Move down to work surface
G1 X10 Y10 F200 ; Move to point 1
G1 X20 Y10 ; Move to point 2
G1 X20 Y20 ; Move to point 3
G1 X10 Y20 ; Move to point 4
G1 X10 Y10 ; Return to point 1
G0 Z5 ; Lift up
M30 ; End program