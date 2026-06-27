  o9301 
  m123 ; 
  m123 ;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;; 
  m123 ;; Starting tool changes 
   
  #[a] = 1            ; starting tool number 
  #[b] = #9161 / 2    ; next tool number 
  if [#9161 % 2] then #[b] = #b - 0.5  ; adjust for odd number bins 
  #[i] = 0            ; tool change counter 
  #[n] = #9161 * 3    ; number of tool changes  
  #111 = 0.005        ; tolerance for TT-1 check 
  if [#25001 == 21] then #111 = #111 * 25.4 
   
n307 
  M123 L1 ;;Tool change to T 
  M123 q0p#a 
  t#a m6 
  if #6001 
  ; position measurement and check 
  g65 p9201 t#111 
   
  M123 L1 ;;Tool change to T 
  M123 q0p#b 
  t#b m6 
  if #6001 
  ; position measurement and check 
  g65 p9201 t#111 
   
  #[a] = #a + 1 
  #[b] = #b + 1 
  #[i] = #i + 2 
  if [#a > #9161] then #[a] = 1 
  if [#b > #9161] then #[b] = 1 
  if [#i <  #n] then goto 307 
   
  m99 
