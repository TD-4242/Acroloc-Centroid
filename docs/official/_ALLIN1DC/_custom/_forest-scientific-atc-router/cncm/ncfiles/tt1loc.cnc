; TT1LOC.CNC
; Purpose:    Position tool close to the TT1 in preparation
;             for protected moves to measure tool.
; Parameters: A    - 0 means position Z close to TT1
;                    1 (nonzero) means position Z away from TT1
; Note: Change the moves below to the actual location of your TT1
;       if not specified in parameter 17.
;       Call this subroutine from any job that needs to move to
;       the TT1.
;       If you move the TT1, you need to edit this file.

; Check parameter 17 for reference point.
IF [[#9017 LT 0] OR [#9017 GT 2]] THEN GOTO 100 ELSE GOTO [100 + #9017]

N100
  ;Return point not specified - move as indicated below
  G53 X10 Y10 Z0          ; Rapid abs. move to move above TT1.
  IF #A EQ 0 THEN G53 Z-4 ; Rapid abs. move to close in on TT1 height.
  M99

N101
  ; Reference point 1
  IF #A EQ 0 THEN G28 ELSE G29
  M99
 
N102
  ; Reference point 2
  IF #A EQ 0 THEN G30 ELSE G29
  M99
