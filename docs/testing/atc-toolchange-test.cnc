; Acroloc ATC tool-change test  (enhanced ATC, P160 = 1)
; File: docs/testing/atc-toolchange-test.cnc
;
; Covers: changes across the carousel (near and far bins), a change to the
; tool already loaded (CNC12 skips it; the spindle must still start), a tool
; numbered above 12, and a return to the starting tool.
;
; Motion rules:
;  - Every Z move is G53 (machine coordinates), never below Z-4.000.
;    G53 is always a rapid in CNC12; the L word slows it (units/min).
;  - Tool pickup is at FULL rapid (no L): it engages best that way on this
;    machine. Only the in-air plunge with the spindle running is slowed.
;  - No XY moves. No tool length offsets are used, so H values do not matter.
;  - The spindle starts only at Z-2.000: above that the tool is not locked
;    and the PLC holds spindle enable off while Z is in the changer.
;
; Before running:
;  - Machine homed, and the ATC RESET button dark (press it if it is lit).
;  - Spindle mode AUTO on the VCP (M3 waits for it).
;  - Tool Library: tools 1-12 in bins 1-12. Tool 15 needs a bin for its
;    block below; delete that block if it has none.
;  - Nothing under the spindle down to Z-4.000.
;  - Optional Stop ON pauses after each tool (M1) so the Tool Library Bin
;    column can be checked; OFF runs straight through.
;
; Expect: every tool lands on its own bin, the VCP reads TOOL n BIN n after
; each change, and the job ends with tool 1 loaded and every other tool back
; in its own bin.

G90 G20 G17 G40 G49 G80
M5
M9
G53 Z0                    ; start at the tool-change height

; ---- tool 1, bin 1 ----
T1 M6
G53 Z-2.000               ; pick up the tool at full rapid
S500 M3                   ; spindle on at the spin height
G4 P3                     ; let it reach speed
G53 Z-3.500 L10           ; plunge in air with the spindle running
G53 Z-2.000 L20           ; back to the spin height
M5                        ; the next M6 waits for zero speed, then parks Z
M1                        ; optional stop: check the Bin column

; ---- tool 12, bin 12 (far side of the carousel) ----
T12 M6
G53 Z-2.000               ; pick up at full rapid
S500 M3
G4 P3
G53 Z-3.500 L10
G53 Z-2.000 L20
M5
M1

; ---- tool 5, bin 5 ----
T5 M6
G53 Z-2.000               ; pick up at full rapid
S500 M3
G4 P3
G53 Z-3.500 L10
G53 Z-2.000 L20
M5
M1

; ---- tool 5 again: CNC12 must SKIP this change (no carousel motion) ----
; ---- and the spindle must still start, since the position is verified ----
T5 M6
G53 Z-2.000               ; already here: no motion
S500 M3
G4 P3
M5
M1

; ---- tool 15, a tool above 12 (needs a bin in the Tool Library) ----
T15 M6
G53 Z-2.000               ; pick up at full rapid
S500 M3
G4 P3
G53 Z-3.500 L10
G53 Z-2.000 L20
M5
M1

; ---- tool 7, bin 7 ----
T7 M6
G53 Z-2.000               ; pick up at full rapid
S500 M3
G4 P3
G53 Z-3.500 L10
G53 Z-2.000 L20
M5
M1

; ---- back to tool 1, bin 1 ----
T1 M6
G53 Z-2.000               ; pick up at full rapid
S500 M3
G4 P3
G53 Z-3.500 L10
G53 Z-2.000 L20
M5
M101 /50012               ; wait for zero speed before Z passes through the changer
G53 Z0                    ; park: tool 1 back in bin 1
M30
