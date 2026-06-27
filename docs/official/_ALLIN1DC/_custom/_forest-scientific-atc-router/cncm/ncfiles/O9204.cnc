  o9204 
  m123 ; 
  m123 ;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;; 
  m123 ;; Starting tapping test 
  m109/2 
  g90 g53 z0 
  m3 s1000 
  g91 
  #111 = -3 
  if [#25001 == 21] then #111 = #111 * 25.4 
  #113 = 0.01 
  if [#25001 == 21] then #113 = 25.4 * #113 
  m123 l1;Tapping Z = 
  m123 l1p#111 
  m123 l1;q = 
  m123 p#113 
  g84 x0 z#111 q#113 r0 
  g80 
  g90 
  m108/2 
  m5 
  g4 p5 
  m123 ;Tapping test completed successfully. 
  m99 
