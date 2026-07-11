# Acroloc ATC Tool-Change Flow

> **Source grounding:** Every description below is derived from the live
> `Centroid-Acroloc-ALLIN1DC.src` and `mfunc6.mac`. Search `; Acroloc` in
> the `.src` to locate every custom addition. Do **not** edit `plc.map` — it
> is regenerated on compile.
>
> For machine overview and build/deploy instructions see `README.md` and
> `CLAUDE.md`. This document focuses on the flow and gotchas, not the
> background prose.
>
> For the fully line-referenced specification see ../../../../docs/plc-spec/atc.md.

---

## Three places the change lives

The M6 tool change is split across three cooperating pieces.

### 1. `mfunc6.mac` — the G-code-level orchestrator

When the CNC executes `M6`, this macro runs:

```gcode
S0
M5              ; stop spindle
M9              ; turn off coolant
G53 Z0          ; move Z to tool-change position
M107            ; send target tool number to PLC
G4 P.1          ; brief settle delay
M94 /8          ; SET M6_SV (SV_M94_M95_8) — kicks off ATCStage
G4 p1           ; wait for ATCStage to start
M100 /93016     ; wait here until ATCStage resets (PLC bit 93016)
M95 /8          ; RST M6_SV — handshake cleanup
```

Guard at top (standard Centroid pattern, must be preserved):
```gcode
IF #4202 || #4201 THEN GOTO 1000   ; skip if graphing or searching
IF #50001                           ; prevent lookahead
M109 /1/2                           ; disable overrides
```

The macro does **not** drive any ATC hardware directly. It relies entirely
on the PLC stage to index the carousel and signal completion.

### 2. `MainStage` — kickoff and spindle-stop safety

In `MainStage` (STG4), two blocks handle the ATC entry. Search the `.src`
for the comment `; Acroloc tool stage start` to find them.

**Kickoff — latch target and set stage:**
```plc
IF M6_SV THEN ChangeToTool_W = SV_TOOL_NUMBER, SET ATCStage
```
`M6_SV` is `SV_M94_M95_8` (system variable for M94/M95 bit 8). The moment
the macro fires `M94 /8`, this line latches the requested tool number into
`ChangeToTool_W` (W72) and enables `ATCStage` (STG16).

**Spindle-in-changer feed-hold interlock — `ChangerStopTimer_T` and `ZeroSpeed_I`:**

Search for `; Acroloc -- Spindle-in-changer feed-hold interlock` in `MainStage`. It is
**not** gated on `M6_SV` — it protects *any* program/MDI move that drives Z into the
changer, not just a tool change.

```plc
; unconditional zone-kill: spindle off whenever Z is in the changer, ALL modes
IF !ATC_Z_ClearedToolChanger_I THEN
  RST SpindleEnableOut_O

; arm only if the spindle is NOT already confirmed stopped at entry
IF (SV_PROGRAM_RUNNING || SV_MDI_MODE) && !ATC_Z_ClearedToolChanger_I
   && !ZeroSpeed_I && !ChangerHoldDone_M && !ChangerHoldActive_M THEN
  SET ChangerHoldActive_M, SET ActivateFeedHold_M,
  ChangerStopTimer_T = 5000, SET ChangerStopTimer_T

; resume the instant zero confirms
IF ChangerHoldActive_M && ZeroSpeed_I THEN ... SET DoCycleStart_SV

; 5 s timeout, spindle still turning -> fault; motion stays held
IF ChangerHoldActive_M && ChangerStopTimer_T && !ZeroSpeed_I THEN ... SPINDLE_FAULT_MSG_C
```

- `ChangerStopTimer_T` (T23, renamed from the dead `StopSpinBeforATC_T`) is a **5 s timeout
  backstop** loaded at arm time — not a boot preset, and not a countdown-to-zero. Timer idiom:
  a bare timer is true **when expired** (`== 0` would mean "just armed").
- Normal M6 takes **no hold**: mfunc6 runs `M5` before the `G53 Z0` park move, so `ZeroSpeed_I`
  already reads stopped at zone entry and the arm rung never fires.
- If the spindle is still coasting at entry: feed hold engages and motion auto-resumes
  (`SET DoCycleStart_SV`) the instant `ZeroSpeed_I` asserts. If it never stops within 5 s:
  `SPINDLE_FAULT_MSG_C`, motion stays held, no auto-resume.
- `ZeroSpeed_I` (INP12) is the F510 VFD zero-speed output — wired and tested.

**Manual unlock (outside M6):**
```plc
IF ATCManualUnlock_I && ATC_Z_Zero_Release_I && !ATCStage THEN SET ATCUnlocked_O
IF !ATCManualUnlock_I && !ATCStage THEN RST ATCUnlocked_O
```
The front-panel `ATCManualUnlock_I` (INP24) button lets an operator unlock
the carousel by hand, but only when Z is clear (`ATC_Z_Zero_Release_I`,
INP27) and `ATCStage` is not running.

### 3. `ATCStage` (STG16) — carousel indexing and match

Find this stage with `; Acroloc` or the comment `; Acroloc ATC Stage`
(`ATCStage IS STG16`).

**Entry safety re-check:** two aborts, both with **full cleanup**:
```plc
IF ATCStage && !ZeroSpeed_I THEN
  FaultMsg_W = SPINDLE_FAULT_MSG_C, SET ShowFaultStage, SET OtherFault_M,
  RST ATCMotor_O, RST ATCUnlocked_O, RST M6_SV, ChangeToTool_W = 0, RST ATCStage

IF !ATC_Z_Zero_Release_I THEN
  FaultMsg_W = ATC_Spindle_Not_Parked_C, SET ShowFaultStage, SET OtherFault_M,
  RST ATCMotor_O, RST ATCUnlocked_O, RST M6_SV, ChangeToTool_W = 0, RST ATCStage
```
Two defensive checks at stage entry: spindle must be stopped (`ZeroSpeed_I`,
INP12) and Z must be clear of the carousel ring (`ATC_Z_Zero_Release_I`,
INP27). Either failure aborts with a fault message.

**Gotcha:** both aborts must clean up fully — stop the motor, relock, drop `M6_SV`, clear
`ChangeToTool_W`. `RST ATCStage` alone (which is what the Z-parked abort used to do) leaves
`ATCMotor_O`/`ATCUnlocked_O` energized and `M6_SV` set, so the carousel keeps spinning unlocked
while `MainStage` re-arms the stage every scan. Any new abort path needs the same cleanup.

**Start the carousel:**
```plc
IF ATCStage && ChangeToTool_W > 0 THEN
  SET ATCUnlocked_O,     ; OUT18 — unlock piston
  SET ATCMotor_O         ; OUT17 — spin carousel
```

**Position detection — `InToolSelect_M` gating:**
```plc
IF ATCMotor_O && ( ATC_Pos1_I || ATC_Pos2_I || ATC_Pos3_I || ATC_Pos4_I || ATC_Pos5_I ) THEN
  CarouselToolID_W = 0,
  SET InToolSelect_M
```
When any position switch asserts while the motor is running, `CarouselToolID_W`
(W71) is zeroed and `InToolSelect_M` (MEM443) is set. The accumulator lines
then fire:

```plc
If InToolSelect_M && ATC_Pos1_I THEN CarouselToolID_W = CarouselToolID_W + 1
If InToolSelect_M && ATC_Pos2_I THEN CarouselToolID_W = CarouselToolID_W + 2
If InToolSelect_M && ATC_Pos3_I THEN CarouselToolID_W = CarouselToolID_W + 4
If InToolSelect_M && ATC_Pos4_I THEN CarouselToolID_W = CarouselToolID_W + 8
If InToolSelect_M && ATC_Pos5_I THEN CarouselToolID_W = CarouselToolID_W + 10
```

When all switches drop to 0 (gap between tool positions), `InToolSelect_M`
is cleared and `CarouselToolID_W` holds the ID of the tool just seen:
```plc
IF ATCMotor_O && ( !ATC_Pos1_I && !ATC_Pos2_I && !ATC_Pos3_I && !ATC_Pos4_I && !ATC_Pos5_I ) THEN
  RST InToolSelect_M
```

**Match and exit:**
```plc
IF CarouselToolID_W == ChangeToTool_W THEN
  ChangeToTool_W = 0,
  SET ToolSelected_M,
  RST ATCMotor_O,
  RST ATCUnlocked_O,
  RST M6_SV,
  RST ATCStage
```
When the accumulated ID matches the latched target: motor stops, piston
relocks, `M6_SV` is cleared (releasing `mfunc6.mac`'s `M100` wait), and
`ATCStage` resets. The macro then cleans up with `M95 /8`.

---

## Carousel position encoding

The five position switches (INP28–INP32, highest to lowest bit) encode tool
numbers in **base-16 written as decimal**. The bit weights in source are:

| Switch | Input | Adds to CarouselToolID_W |
|--------|-------|--------------------------|
| ATC_Pos1_I | INP32 | +1 |
| ATC_Pos2_I | INP31 | +2 |
| ATC_Pos3_I | INP30 | +4 |
| ATC_Pos4_I | INP29 | +8 |
| ATC_Pos5_I | INP28 | **+10** (not +16) |

The source comment on the Pos5 line reads:
`; Not 16 due to base16 encoded as decimal`

This means tool numbers beyond 9 are encoded so that the "tens digit"
represents the base-16 high nibble. For example:

| Tool | Switch pattern (1=closed) Pos1–Pos5 |
|------|--------------------------------------|
| T1   | 1 0 0 0 0 |
| T2   | 0 1 0 0 0 |
| T3   | 1 1 0 0 0 |
| T4   | 0 0 1 0 0 |
| T5   | 1 0 1 0 0 |
| T6   | 0 1 1 0 0 |
| T7   | 1 1 1 0 0 |
| T8   | 0 0 0 1 0 |
| T9   | 1 0 0 1 0 |
| T10  | 0 0 0 0 1 |
| T11  | 1 0 0 0 1 |
| T12  | 0 1 0 0 1 |

(Table from the inline comment block in `ATCStage`.)

`CarouselToolID_W` accumulates while any position switch is high (gated by
`InToolSelect_M`). The compare `IF CarouselToolID_W == ChangeToTool_W THEN ...`
(src line 2939) is **unconditional** — it runs every PLC scan, including
mid-accumulation while switches are still asserted. The accumulator is zeroed
(`CarouselToolID_W = 0`) at the leading edge of each tool's switch group (the
first scan where any position switch asserts). A transient partial sum that
equals the target tool ID during the accumulation window would stop the carousel
prematurely — any edit to the accumulator lines (`+1 / +2 / +4 / +8 / +10`)
must account for this timing sensitivity.

---

## ⚠️ Known gaps

### 1. No carousel timeout — motor can spin forever

At the top of `ATCStage`, the source contains:
```plc
;TODO: add timer to error so carousol doesn't spin for ever if tool not found
```

`ATCSpin_T` (T24) is **defined** (`ATCSpin_T IS T24 ; used to detect fault
if unable to find position`) but is **never set or checked** anywhere in the
current logic. If `ChangeToTool_W` never matches — due to an off-by-one in
the position decode, a faulty switch, or an invalid tool number — `ATCMotor_O`
stays asserted and the carousel spins indefinitely.

**Risk:** Any edit to the accumulator lines (`+1 / +2 / +4 / +8 / +10`) or to
the `InToolSelect_M` gating must be tested extremely carefully. A value of
`+16` for Pos5 instead of `+10` would cause tools 10–15 to never match.

### 2. Transmission shift is automated open-loop (no gear-position feedback)

`Spindle_Low_gear_O` (OUT19) and `Spindle_High_gear_O` (OUT20) are driven by
the RPM-based auto-shift logic: a decision block in `MainStage` picks the gear
from the un-overridden commanded S (crossover P941 ± hysteresis P942) and
`GearShiftStage` (STG17) swaps clutches with a neutral coast dwell (P943).
There is **no gear-position or speed feedback** — the engaged gear is tracked
only from the commanded clutch outputs (`EngagedRange_W`), and a shift is
inhibited during `ATCStage`. See the "Automatic RPM-based gear shifting"
section of `README.md` and `reference/spindle-transmission.md`.
