  o9201 
  ;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;; 
  ; Subprogram to measure tool height using TT-1 located at G30 P3 
  ; This subprogram assumes that a data file has been previously opened. 
  ; 
  ; This routine uses variable #29000 - #29xxx to record Z machine 
  ; positions.  If these variables are zero, the routine makes 
  ; an initial measurement.  Otherwise, it makes a tolerance check. 
  ; 
  ; #t is the tolerance 
  ; 
  if #6001 
  ;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;; 
  ; Determine TT-1 input number 
  ; Default to input specified in machine parameter 11 
  ; if machine parameter 44 = 0. 
  ;  
  #[a] = #9011 
  if [#9044 != 0] then #[a] = #9044 
  
  m5        ; turn off spindle 
  m9        ; turn off coolant 
  g30 p3    ; position to tool detector position 
   
  ; DETERMINING TOOL NUMBER IN SPINDLE 
  ; WHEN THIS LOOP FINISHES, #115 = TOOL NUMBER IN THE SPINDLE 
   
  #130 = 1 ; VARIABLE FOR TOOL AT BIN 0 (ACTIVE TOOL BIN NUMBER) 
  #115 = 0 ; RESETTING TOOL # TO 0 
   
N5 
  if [#[17000+#130] == 0] then #115 = #130 
  if [#115 > 0] then goto 10 
  #130 = #130+1 
  if [#130 > 199] then #ERROR TOOL IN SPINDLE NOT FOUND 
  goto 5 
   
N10 ; CHECKING TOOL HEIGHT 
  m123 l1;  Tool in spindle is 
  m123 q0p#115 
  
  #[d] = #23503             ; set max distance to travel limit 
  #[d] = #d - #2700         ; 
                            ; 
  #111 = 50 
  if [#25001 == 21] then #111 = #111 * 25.4 
  M115/Z#d P[-#a] L1 F#111  ; Move down until probe contact (50 IPM) 
  M116/Z P[#a] F[#111/2]    ; Move up until probe clear     (25 IPM) 
  #111 = 0.025 
  if [#25001 == 21] then #111 = #111 * 25.4 
  G91 Z#111                 ; clearance move (0.025 in) 
  G90 
   
  #111 = 10 
  if [#25001 == 21] then #111 = #111 * 25.4 
  M115/Z#d P[-#a] L1 F#111  ; move down until probe contact (10 IPM) 
   
  ; record current Z machine position 
  if #6001 
  #29999 = 0   
  if [#[29000+#115] == 0] then #[29000+#115] = #5023 else #29999 = #5023 
  
  m123 l1;  Z height measured at 
  m123 l1 p#5023 
  if [#29999 == 0] then m123 ;-- INITIAL CHECK 
  if [#29999 != 0] then m123 ; 
  M116/Z P[#a] F10          ; move up until probe clear 
  G91 Z.100 F30             ; clearance move 
  G90 
   
  ; skip tolerance check if initial check 
  if [#29999 == 0] then goto 300  
  
  ; otherwise, compute absolute difference 
  ; between last recorded Z machine position 
  ; and the current recorded Z machine position 
  ; 
  #114 = abs[#29999 - #(29000 + #115)]    
  ; if position within tolerance, skip to the end 
  if [#114 <= #t] then goto 300 
   
n200 
  m123 ;*** FAILURE TOOL CHECK 
  m123 l1 ;Initial check was 
  m123 l1 p#[29000+]] 
  m123 l1 ;current check is 
  m123 l1 p#29999 
  m123 l1 ;error 
  m123 p#114 
  if [#112 == 1] then goto 300 
  #ERROR 
   
N300 
   
  m99 
