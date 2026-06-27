  o9101 
  ;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;; 
  ;  Check that travel limits are set and axis is homed 
  ;  for each axis that has a valid axis label 
  ;  (other than N, M, or S) 
  ; 
  m123 ; 
  m123 ;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;; 
  m123 ;;   Checking travel limits and home set 
  #[a] = 1 
n5 
  if [#(20100+#a) == 77] then goto 7  ; skip if axis label is 'M' 
  if [#(20100+#a) == 78] then goto 7  ; skip if axis label is 'N' 
  if [#(20100+#a) == 83] then goto 7  ; skip if axis label is 'S' 
   
  if [not ((#(23500+#a) < 0) || (#(23600+#a) > 0))] then goto 10 
   
n6 
  ; Check that the machine has been homed for axis(n) 
  if [#(23700+#a) == 0] then goto 20 
n7 
  #[a] = #a + 1 
  if [#a < 6] goto 5 
  m123 ;Travel limits set and machine is homed. 
  goto 100 
   
n10 
  ; Check to see if axis is set to rotary before failing 
  if [#a <= 4 && ((#(9090+#a) and 1) != 1)]  goto 15 
  if [#a >= 5 && ((#(9166+(#a-4)) and 1) != 1)]  goto 15 
  m123 l1;Axis 
  m123 l1q0p#a 
  m123 ;is set as rotary without travel limits. 
  goto 6 
   
n15 
  m123 l1 ;***  FAILURE: AXIS 
  m123 q0l1p#a 
  m123 ;INVALID TRAVEL LIMITS 
  goto 99 
   
n20 
  m123 l1 ;***  FAILURE: AXIS 
  m123 q0l1p#a 
  m123 ;NOT HOMED 
  goto 99 
   
n99 
  #149 = 1  ; flag error 
   
n100 
  M99 
