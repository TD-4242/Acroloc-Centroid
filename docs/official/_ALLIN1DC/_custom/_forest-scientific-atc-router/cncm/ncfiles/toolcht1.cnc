; TOOLCHT1.CNC
; Purpose:    1. Measure current tool offset using TT1
;             2. adjust tool offset for wear.
;             3. Change tool on excessive wear/breakage.
; Updated:    27-Aug-2002
; Author:     Ron Eichenlaub
; Parameters: 
;             #149 - Z reference position (machine)
; Notes:      This routine handles one tool only.
;             Measure the tool before starting the job.
;             This subroutine establishes its Z reference
;             the first time that it is called and assumes no wear.
;             The variable (#149) that holds the Z reference is reset
;             to 0.0 at the start of the job.  
; Copyright 2002 Centroid Corporation  www.centroidcnc.com

  M5                       ; Spindle off
  M9                       ; Coolant off
  G43                      ; length comp. on
  G65 "TT1LOC.CNC" A0      ; Move to TT1 position.
  M115 /Z P[-#9011] F#9014 ; Fast contact with TT1.
  M116 /Z P[ #9011] F#9015 ; Break contact slowly.
  G4 P1
  M116 /Z P[ #9011] F#9015 ; Break contact slowly.
  M115 /Z P[-#9011] F#9015 ; Make contact again slowly.

  ; If not already set, establish the Z reference
  IF [#149 EQ 0] THEN #149 = #5023
  ; Check for excessive wear or broken tool.
  IF [ABS[#5023 - #149] GT 0.001] GOTO 1000
  ; Update the current height offset.
  #10000 = #10000 - ABS[#5023 - #149]
  G65 "TT1LOC.CNC" A1      ; Move away from TT1.

  M99                      ; Return to main program

N1000
  G65 "TT1LOC.CNC" A1      ; Move away from TT1.
  ;
  ; Excessive tool wear or broken tool!
  ; Please change it.
  M0

  M99                      ; Return to main program
