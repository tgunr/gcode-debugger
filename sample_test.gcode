; Sample G-code file for testing the debugger
; This file demonstrates various G-code commands

; Initialize
G90         ; Absolute positioning
G21         ; Metric units
G17         ; XY plane selection
G94         ; Feed rate per minute

; Home all axes
G28

; Set work coordinate system
G54

; Move to start position
G0 X10 Y10 Z5
G0 Z0.5

; Test cutting pattern - simple rectangle
G1 Z-1 F100     ; Plunge down
G1 X50 F1000    ; Move right
G1 Y50          ; Move up
G1 X10          ; Move left
G1 Y10          ; Move down
G0 Z5           ; Retract

; Tool change example
M5              ; Stop spindle
G0 Z25          ; Safe height
G0 X0 Y0        ; Go to tool change position
M0              ; Program pause for tool change

; Spindle test
M3 S1000        ; Start spindle at 1000 RPM
G4 P2           ; Dwell for 2 seconds
M5              ; Stop spindle

; Coolant test
M8              ; Coolant on
G4 P1           ; Dwell
M9              ; Coolant off

; Final positioning
G0 Z25          ; Safe height
G0 X0 Y0        ; Return to origin

; Program end
M30             ; End program