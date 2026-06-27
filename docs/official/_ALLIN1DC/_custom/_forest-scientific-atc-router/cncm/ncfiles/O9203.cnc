  o9203 
  m123 ; 
  M123 ;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;; 
  M123 ;;  Starting  Spindle Test 
  if [#9078 != 1] then m123 ;* WARNING - Setting P78 to 1.0 
  if [#9036 != 1] then m123 ;* WARNING - Setting P36 to 5.0 
  if [#9033 != 1] then m123 ;* WARNING - Settign P33 to 1.0 
  ; set p78 = 1 (to see actual measured spindle speed) 
  g10 p78 r1 
  ; set p36 = 5 (enable rigid tap, wait for index) 
  g10 p36 r1 
  ; set p33 = 1 (spindle motor gear ratio) 
  g10 p33 r1 
   
  ;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;; 
  ; Try to determine which axis spindle encoder 
  ; is connected to. 
  ; 
  ; Take initial reading of all abs encoder positions 
  ; 
  #[i] = 1 
  #29000 = #25010  ; spindle counts according to axis set by P35 
   
n3 
  #[29000+#i] = #[23800+#i] 
  #[i] = #i + 1 
  if [#i <= 6] then goto 3 
   
  ; 
  ; Command spindle at max speed (according to control config) 
  ; for a few seconds 
  ; 
  m109/2 
  m3 s#25006   
  g4 p3        
  m5 
  m108/2 
  g4 p5        
   
  ; 
  ; Determine which axis has moved at least 10000 encoder counts 
  ; 
  #[i] = 1 
  #[e] = 0 
n4 
  if [abs(#(29000+#i)-#(23800+#i)) > 10000] then #[e] = #i 
  #[i] = #i + 1 
  if [#i <= 6] then goto 4 
   
  if [#e != 0] then goto 5 
  m123 ;*** FAILURE SPINDLE ENCODER NOT DETECTED 
  #149 = 1  ; flag error 
  goto 20   ; exit routine 
   
  ; 
  ; Report the axis spindle encoder is connected to 
  ; and check machine parmeter 35 for correct setting. 
  ; 
n5 
  m123 l1;Spindle encoder detected on axis 
  m123 q0p#e 
  #148 = #e - 1 
  if [abs(#29000-#25010) > 10000] then goto 6 
  m123 ;*** FAILURE Machine parameter 35 is set wrong. 
  m123 l1;It should be 
  m123 l1q0p#148 
  m123 l1;or 
  #148 = #148 + 16 
  m123 l1q0p#148 
  m123 ;(if AC system connected to CPU card) 
  #149 = 1  ; flag error 
  goto 20 
   
n6 
  ;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;; 
  ; Check P34 for correct sign 
  ; Command M3, if spindle axis counts up, P34 should be positive 
  ; 
  m109/2 
  if #6001 
  #148 = #25010 
  m3 s600 
  g4 p1 
  m5 
  m108/2 
  if #6001 
  #148 = #25010 - #148 
  if [#148 * #9034 < 0] then m123 ;* WARNING: P34 wrong sign, reversing sign 
  if [#148 * #9034 < 0] then g10 p34 r[-#9034] 
 
  #[i] = 1; 
  #[t] = 0; 
  m123 ;-- Determining spindle decel time at 2000RPM 
  m109/2 
n7 
  m3 s2000 
  g4 p3 
  #146 = #25012 
  #145 = #25010 
  m5  
  g4 p.1 
n8 
  if [#145 == #25010] goto 9 
  #145 = #25010 
  g4 p.1      
  goto 8 
   
n9 
  m123 l1;-- Spindle decel time measured at 
  #145 = #25012 - #146 
  #[t] = #t + #145 
  m123 l1q2 p#145 
  m123 ;seconds. 
  #[i] = #i + 1 
  if [#i <= 3] goto 7 
  #145 = #t / 3 
  m123 l1;-- Average decel time 
  m123 l1q2p#145 
  m123 ;seconds. 
   
  #[s] = 0.1 * #25006 ; Start at 10% of max 
  #[i] = 1 
  M123 ;Commanded   Measured   Error 
  M109/2 
n10 
  M123 r8q0L1 p#s 
  M3 s#s 
  g4 p5 
  if #6001 
  #118 = #25009 
  M123 r8q0l1p#118 
  #146 = #118 - #s 
  m123 r8q0l1p#146 
  #146 = 100*(abs(#118 - #s)/#s) 
  m123 l1 ;( 
  m123 r5q3l1 p#146 
  m123 ;%) 
  #[29000+#i] = #146 
  #[i] = #i + 1 
  #[s] = #25006 * #i/10 ; increment by 10% of max 
  if [#s <= #25006] goto 10 
n20 
  ;;;;;;;;;;;;;;;;;;;;;;; 
  ; Analyze data 
  s0 
  m5 
  m108/2 
  g4 p5 
  if #6001 
  #[i] = 1 
n23 
  if [(#[29000+#i] > 3.0)] then goto 30 
  #[i] = #i + 1 
  if [#i <= 10] then goto 23 
  m123 l1;Spindle speeds within 3% from 
  #146 = #25006/10 
  m123 l1q0p#146 
  m123 l1;RPM to Max 
  goto 40 
n30 
  m123 ;*** FAILURE SPINDLE SPEED VARIATION 
  #149 = 1 
  goto 40 
n40 
  m99 
