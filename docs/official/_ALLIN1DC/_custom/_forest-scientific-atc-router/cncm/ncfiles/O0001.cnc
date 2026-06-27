#[a] = #4001            ;save mode rapid or linear 
#[b] = #4003            ;save mode positioning 
#[c] = #4109            ;save feedrate
#[d] = #4006            ;save units of measure
G20                     ;use imperial units
G00 G91 
X[16.2750-#5021] ;RAPID X TO CHANGE POSITION 
G#A G#B F#C G#D
M99 
