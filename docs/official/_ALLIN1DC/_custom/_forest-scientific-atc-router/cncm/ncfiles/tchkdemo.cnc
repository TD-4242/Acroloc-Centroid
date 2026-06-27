; Tool check demo program
; Checks tool length and prompts for tool change if tool is worn or broken
; This is a simple demonstration that checks only one tool.
; 
; Variables: #149 - Z reference point
;
; Subroutines: TOOLCHT1.CNC
;              TT1LOC.CNC   (called from TOOLCHT1.CNC)

N1
  T1 H#12000 D#13000 ; Select tool and default offsets
  M98 "toolcht1.cnc" ; Measure tool
  ;M98 "job.cnc"     ; Run job (call your job here)
  #3901 = #3901 + 1  ; Increment job #
  IF [#3901 LT #3902] GOTO 1
  ;Note: cannot use M102 because it will reset Z reference variable #149
  ;      If you need to interrupt your job, you should re-measure the tool.
  ;      A non-volatile variable (#150 - #159) should be used if you want
  ;      to retain the Z reference between runs.