  o9102 
  ; 
  ;  Home switch testing 
  ; 
  ; 
  ;  Variables used in limit/home switch testing 
  ;  #140 = number of times to test each switch 
  ;  #29101- home posiiton recordings 
  ;  #29201- home count recordings  (UNUNSED) 
  ;  #29301- off limit position recordings 
  ;  #29401- off limit counts recordings (UNUSED) 
  m123 ; 
  m123 ;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;; 
  m123 ;; Starting home switch testing 
  if #6001 
  ;#140 = 3       ; number of times to check each switch 
  #143 = 8       ; denominator of fraction of encoder revolution 
                 ; used to determine possible homing error 
                 ;  
  #[t] = 0.0005  ; tolerance for home position repeatability 
  #[o] = 0.002   ; tolerance for off limit switch repeatability 
  if [#25001 == 21] then #[t] = #t * 25.4 
  if [#25001 == 21] then #[o] = #o * 25.4 
   
  ;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;; 
  ; Check that homing is set to Ref Mark-HS or Home Switch 
  ; Display warning if set to Jog 
  ; 
  if [#25007 == 0] goto 1000 
   
  ;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;; 
  ; Check that every axis with a valid axis label 
  ; other than (M, N, or S) has at least one home switch 
  ; input assigned. Display warning if not. 
  ; Exception for rotary axes. 
  ; 
  #[a] = 1 
   
n2 
  if [#(20100+#a) == 77] then goto 3  ; skip if axis label is 'M' 
  if [#(20100+#a) == 78] then goto 3  ; skip if axis label is 'N' 
  if [#(20100+#a) == 83] then goto 3  ; skip if axis label is 'S' 
   
  if [not ((#(21300+#a) == 0) && (#(21400+#a) == 0))] goto 3 
   
  ; Check to see if axis is set to rotary before warning 
  if [#a <= 4 && ((#(9090+#a) and 1) == 1)]  goto 3 
  if [#a >= 5 && ((#(9166+(#a-4)) and 1) == 1)]  goto 3 
   
  
  M123 ; 
  M123 l1 ;*  WARNING: Axis 
  M123 l1q0p#a 
  M123 ;has no assigned home switch. 
   
n3 
  #[a] = #a + 1 
  if [#a < 6] goto 2 
   
   
  ;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;; 
  ;      Loop through axes 
  ; 
  #[a] = 1 
n1 
  ;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;; 
  ; Check for axis(n) minus switch 
  ; 
  #[r] = 11  ; return N number 
  if [#(21300+#a) == 0] goto #r 
  #[s] = 91  ; home minus 
  goto 98 
  ;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;; 
  ;  Check for axis(n) plus switch 
  ;  test only if non-zero and not the same as minus switch 
n11 
  ; record machine home minus position 
  #[29500+#a] = #29101 
  #[r] = 12 ; return N number 
  if [(#(21400+#a) == 0) || (#(21400+#a) == #(21300+#a))] goto #r 
  #[s] = 92 ; home plus 
  goto 98 
   
n12 
  ; record machine home plus position 
  #[29600+#a] = #29101 
   
  if [#(20100+#a) == 77] then goto 50  ; skip if axis label is 'M' 
  if [#(20100+#a) == 78] then goto 50  ; skip if axis label is 'N' 
  if [#(20100+#a) == 83] then goto 50  ; skip if axis label is 'S' 
   
  ;;;;;;;;;;;;;;;;; 
  ; Compare distances between home positions with travel limits. 
  ; Travel limit distance must be less than distance between 
  ; home positions and within 1.00 inch. 
  ; 
  ; For systems that have one home switch on an axis, 
  ; we attempt a move from the home position out to the 
  ; travel limit distance as a check. Note that in this 
  ; case, we cannot detect a travel limit set too short. 
  ; A travel limit that is too long in this case will 
  ; cause the test program to abort with a full power 
  ; without motion or position error. 
  ; 
  ;;;; 
  ; Check for home switches at both ends 
  if [#(21300+#a) == #(21400+#a)] goto 30 
  if [(#(21300+#a) != 0) && (#(21400+#a) != 0)] goto 20 
  goto 30 
   
n20 
  ; 
  #101 = #(29600+#a) - #(29500+#a) 
  #102 = #(23600+#a) - #(23500+#a)  
  #103 = #101 - #102 
  m123 ;Axis has both minus and plus home switches 
  m123 l1;-Distance between home positions is 
  m123 p#101 
  m123 l1;-Distance between travel limits  is 
  m123 p#102 
  m123 l1;-Difference between distances is 
  m123 p#103 
  #111 = 1.0 
  if [#25001 == 21] then #111 = #111 * 25.4 
  if [(#103 >= 0) && (#103 < #111)] then goto 50 
   
  m123 ;*** FAILURE Travel limits set incorrectly 
  #149 = 1 
  if [#112 == 0] then goto 9999 
  goto 50 
   
n30 
  m123 ; 
  m123 ;-- Checking minus travel limit 
  #[d] = 23500 
n33 
  m123 l1;Moving axis 
  m123 l1q0p#a 
  m123 ;to machine home position 
   
  if [#(20100+#a) == 65] then g90 g53 A0 
  if [#(20100+#a) == 66] then g90 g53 B0 
  if [#(20100+#a) == 67] then g90 g53 C0 
  if [#(20100+#a) == 85] then g90 g53 U0 
  if [#(20100+#a) == 86] then g90 g53 V0 
  if [#(20100+#a) == 87] then g90 g53 W0 
  if [#(20100+#a) == 88] then g90 g53 X0 
  if [#(20100+#a) == 89] then g90 g53 Y0 
  if [#(20100+#a) == 90] then g90 g53 Z0 
   
  #109 = #(#d+#a) 
   
  m123 l1;Moving incrementally 
  m123 p#109 
  g91 g1 f[#(20200+#a)]  ; move at slow jog rate for axis 
  
  if [#(20100+#a) == 65] then A#109 
  if [#(20100+#a) == 66] then B#109 
  if [#(20100+#a) == 67] then C#109 
  if [#(20100+#a) == 85] then U#109 
  if [#(20100+#a) == 86] then V#109 
  if [#(20100+#a) == 87] then W#109 
  if [#(20100+#a) == 88] then X#109 
  if [#(20100+#a) == 89] then Y#109 
  if [#(20100+#a) == 90] then Z#109 
  g90 
   
  if [#d == 23600] goto 50 
  #[d] = 23600 
  m123 ; 
  m123 ;-- Checking plus travel limit 
  goto 33 
   
n50 
  ; move to center of travel 
  if [#(20100+#a) == 65] then g90 g53 A0 
  if [#(20100+#a) == 66] then g90 g53 B0 
  if [#(20100+#a) == 67] then g90 g53 C0 
  if [#(20100+#a) == 85] then g90 g53 U0 
  if [#(20100+#a) == 86] then g90 g53 V0 
  if [#(20100+#a) == 87] then g90 g53 W0 
  if [#(20100+#a) == 88] then g90 g53 X0 
  if [#(20100+#a) == 89] then g90 g53 Y0 
  if [#(20100+#a) == 90] then g90 g53 Z0 
  #118 = [(#(23500+#a) + #(23600+#a)) / 2.0] 
  if [#(20100+#a) == 65] then g91 A#118 
  if [#(20100+#a) == 66] then g91 B#118 
  if [#(20100+#a) == 67] then g91 C#118 
  if [#(20100+#a) == 85] then g91 U#118 
  if [#(20100+#a) == 86] then g91 V#118 
  if [#(20100+#a) == 87] then g91 W#118 
  if [#(20100+#a) == 88] then g91 X#118 
  if [#(20100+#a) == 89] then g91 Y#118 
  if [#(20100+#a) == 90] then g91 Z#118 
  g90 
  #[a] = #a + 1 
  if [#a < 6] goto 1 
   
  goto 101 
   
n98 
  ;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;; 
  ; 
  ; Subroutine to check home switch 
  ; returns to line specified by #r 
  ; 
  if [#(20100+#a) == 77] then goto #r  ; return if axis label is 'M' 
  if [#(20100+#a) == 78] then goto #r  ; return if axis label is 'N' 
  if [#(20100+#a) == 83] then goto #r  ; return if axis label is 'S' 
   
  M123    ;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;; 
  M123 L1 ;    Homing axis 
  M123 L1q0 P#a 
   
  if [#s == 91] then M123 ;minus 
  if [#s == 92] then M123 ;plus 
   
   
  #101 = 1/(#143*#(20400+#a)) 
  #109 = #143 - 1 
  #102 = #101 * #109 
  #104 = #101 * #143 
  M123 L1 ;1 / 
  m123 q0l1 p#143 
  m123 L1 ;turn distance is 
  M123 p#101 
  m123 q0l1p#109 
  M123 L1;/ 
  m123 q0l1p#143 
  m123 l1;turn distance is 
  M123 p#102 
  M123 L1 ;full  turn distance is 
  M123 p#104 
  
  M123 ;Off switch|  error  |  home  |  error  | differnce 
  #[i] = 1 
n99 
  if [#(20100+#a) == 65] then M#s/A L1 
  if [#(20100+#a) == 66] then M#s/B L1 
  if [#(20100+#a) == 67] then M#s/C L1 
  if [#(20100+#a) == 85] then M#s/U L1 
  if [#(20100+#a) == 86] then M#s/V L1 
  if [#(20100+#a) == 87] then M#s/W L1 
  if [#(20100+#a) == 88] then M#s/X L1 
  if [#(20100+#a) == 89] then M#s/Y L1 
  if [#(20100+#a) == 90] then M#s/Z L1 
  if #6001 
  #[29300+#i] = #[5020+#a] 
  #[29400+#i] = #[23800+#a] 
  if [#i == 1] then #29300 = #29301 ; record first for error stats 
  if [#i == 1] then #29400 = #29401 ; record first for error stats 
  ; log the off switch position and error 
  M123 r9q4L1 p#[29300+#i] 
  #146 = abs(#29300 - #(29300+#i)) 
  M123 r9q4L1 p#146 
   
  if [#(20100+#a) == 65] then M#s/A 
  if [#(20100+#a) == 66] then M#s/B 
  if [#(20100+#a) == 67] then M#s/C 
  if [#(20100+#a) == 85] then M#s/U 
  if [#(20100+#a) == 86] then M#s/V 
  if [#(20100+#a) == 87] then M#s/W 
  if [#(20100+#a) == 88] then M#s/X 
  if [#(20100+#a) == 89] then M#s/Y 
  if [#(20100+#a) == 90] then M#s/Z 
  if #6001 
  #[29100+#i] = #[5020+#a] 
  #[29200+#i] = #[23800+#a] 
  if [#i == 1] then #29100 = #29101 ; record first for error stats 
  if [#i == 1] then #29200 = #29201 ; record first for error stats 
  ; log home position and error 
  M123 r9q4L1 p#[29100+#i] 
  #146 = abs(#29100-#(29100+#i)) 
  M123 r9q4l1 P#146 
  ; log distance between off switch and home position 
  #146 = abs[#(29100+#i)-#(29300+#i)] 
  M123 r9q4 P#146 
  #[i] = #i + 1 
  if [#i <= #140] goto 99 
  ;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;; 
  ; Analyze data 
  ; 
  ; 
  ; Check that all measurements are within tolerance. 
  ; Count the number of errors 
  ; 
  #29903 = -9999.999    ; max off switch position 
  #29904 =  9999.999    ; min 
  #29901 = -9999.999    ; max home position 
  #29902 =  9999.999    ; min 
   
  #[e] = 0 
  #[i] = 1 
n97 
   
  #141 = abs(#(29100+#i)-#29100)  ; home position error 
  #142 = abs(#(29300+#i)-#29300)  ; off switch error 
   
  if [#(29100+#i) > #29901] then #29901 = #(29100+#i) 
  if [#(29300+#i) > #29903] then #29903 = #(29300+#i) 
   
  if [#(29100+#i) < #29902] then #29902 = #(29100+#i) 
  if [#(29300+#i) < #29904] then #29904 = #(29300+#i) 
   
  if [#141 > #t] then #[e] = #e + 1 
  ;if [#142 > #o] then #[e] = #e + 1 
  #[i] = #[i] + 1 
  if [#i <= #140] goto 97 
  ; 
  ; log max/min difference 
  ; 
  M123 ;Off switch      Max     Min    Difference 
  M123 L1 ;        
  M123 r9q4l1 p#29903 
  M123 r9q4l1 p#29904 
  #146 = #29903 - #29904 
  M123 r9q4 p#146 
   
  M123 ;home posiiton   Max     Min    Difference 
  M123 L1 ;        
  M123 r9q4l1 p#29901 
  M123 r9q4l1 p#29902 
  #146 = #29901 - #29902 
  M123 r9q4 p#146 
   
  if [#e == 0] then goto 88 
  
  #149 = 1 
  M123 ;*** FAILURE MACHINE HOME SWITCH REPEATABILITY  
  ; 
  ; Suspect limit switch problem 
  ; if error in homing positions 
  ; is approximately one full turn. 
  ; Otherwise, suspect faulty index pulse. 
  ; 
  #111 = 0.001 
  if [#25001 == 21] then #111 = #111 * 25.4 
  
  if [abs(#146-#104) < #111] then  M123 ;--SUSPECTED LIMIT SWITCH PROBLEM 
  if [abs(#146-#104) >= #111] then M123 ;--SUSPECTED ENCODER INDEX PROBLEM 
  if [#112 == 0] goto 9999 
  ; 
  ; Check for conditions in which home position is within 
  ; 1/#143 revolution of coming off switch 
  ; 
n88 
  #[b] = abs(#29100 - #29300) 
  if [(#b > #101) && (#b < (#102))] then goto #r 
  M123 ;*** FAILURE Home position too close to encoder index pulse 
  #149 = 1 
  if [#112 == 1] then goto #r 
  goto 9999 
   
   
n101 M123 ;Finished testing home/limit switches 
  goto 10000 
   
n1000 
   
  M123 ; 
  M123 ;* WARNING: Machine home at power up set to Jog 
  M123 ;           Home switch testing skipped 
  M123 ; 
  goto 10000 
   
N9999 
  #149 = 1 
   
N10000 
  M99 
