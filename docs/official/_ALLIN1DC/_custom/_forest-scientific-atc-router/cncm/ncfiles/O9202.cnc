  o9202 
  m123 ; 
  m123 ;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;; 
  m123 ;;  Checking TT-1 operation and parameter settings 
  ; * Connect TT-1 and verify the XY location of the TT-1 
  ; * is set in return point #3. Verify that the spindle  
  ; * face is above the TT-1 when at the Z minus travel 
  ; * limit. After pressing CYCLE START, 
  ; * trigger the TT-1 twice. 
  m0 
  if [#9044 != 0] then #[a] = #9044 
  if [#9044 == 0] then #[a] = #9011 
  M123 L1 ;TT-1 set to be input 
  M123 q0 p#a 
  m101/#a 
  g4 p.1 
  m100/#a 
  g4 p.1 
  m101/#a 
  g4 p.1 
  m100/#a 
  g4 p.1 
  if #6001 
  M123 l1;TT-1 has been detected on input 
  m123 q0p#a 
  m0 ; Press CYCLE_START to continue          
  m99 
