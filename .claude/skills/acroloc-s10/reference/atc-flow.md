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
G4 p1           ; wait for ATCStage to start (PLC computes the bin)
M100 /93016     ; wait here until ATCStage resets (PLC bit 93016)
M95 /8          ; RST M6_SV — handshake cleanup
```

Guard at top (standard Centroid pattern, must be preserved):
```gcode
IF #4202 || #4201 THEN GOTO 1000   ; skip if graphing or searching
IF #50001                           ; prevent lookahead
M109 /1/2                           ; disable overrides
```

The macro ends with `M108 /1/2`, re-enabling the overrides that `M109 /1/2` turned off.
The pair must always be balanced: an unpaired `M109` leaves CNC12's override control
disabled for the rest of the program, which also disables the lockout that normally forces
feed override to 100% during a G74/G84 tapping cycle — a tap fed at a reduced override will
break.

The macro does **not** drive any ATC hardware directly. It relies entirely
on the PLC stage to index the carousel and signal completion. The chosen bin is
shown on the **retro VCP** as a live `BIN` readout (`plc_word` 8 =
`TargetToolBinDisp_W`), not as a macro message — `M225` is a *modal* box that
would pause the change until dismissed.

### 2. `MainStage` — kickoff and spindle-stop safety

In `MainStage` (STG4), two blocks handle the ATC entry. Search the `.src`
for the comment `; Acroloc tool stage start` to find them.

**Kickoff — guard the bin CNC12 sent, then set the stage:**

The machine runs CNC12's non-random enhanced ATC (`P160 = 1`), so `SV_TOOL_NUMBER`
is the requested tool's **carousel bin** as assigned in the Tool Library — `M107`
sends the bin, not the tool number:
```plc
IF M6_SV && !ATCStage THEN ATCSpin_T = ATC_SPIN_TIMEOUT_MS_C, SET ATCSpin_T, CurrentToolBin_W = 0
IF M6_SV && !ATCStage && (SV_TOOL_NUMBER < 1 || SV_TOOL_NUMBER > MaxToolBins_W) THEN
  FaultMsg_W = ATC_BIN_RANGE_MSG_C, SET ShowFaultStage, SET OtherFault_M,
  RST M6_SV, RST ATCSpin_T, TargetToolBinDisp_W = SV_TOOL_NUMBER
IF M6_SV && !ATCStage THEN
  TargetToolBin_W = SV_TOOL_NUMBER, TargetToolBinDisp_W = SV_TOOL_NUMBER, SET ATCStage
```
`M6_SV` is `SV_M94_M95_8`. `MaxToolBins_W` (W79) is P161, re-read every scan. A
bin outside 1..P161 (an unassigned tool, a bad library, P161 unset) faults
`9067 ATC BIN OUT OF RANGE` at once and never starts the carousel; the 9xxx fault
cancels the job during mfunc6's `G4 P1` dwell, so CNC12 does not record the change
as complete. `TargetToolBinDisp_W` (W8) holds the bin for the retro VCP `BIN`
readout (`plc_word` 8). `ATCStage` (STG16) then indexes the carousel to
`TargetToolBin_W` — its search/decode/match logic is unchanged.

**Position report and ATC Reset — the CNC12 handshake:**
```plc
IF !ATCStage THEN ReportedToolBin_W = CurrentToolBin_W
IF True_M THEN SV_PLC_CAROUSEL_POSITION = ReportedToolBin_W
IF M18_SV && !ATCStage THEN CurrentToolBin_W = SV_ATC_CAROUSEL_POSITION
```
CNC12 refuses to run a tool change until the PLC reports a carousel position, and
at the end of every M6 it records the reported value as the new tool's putback bin
(its bin field is restored from that when the tool is next swapped out). So the
report must be the **settled** bin: it is latched only while `ATCStage` is idle,
the match rung leaves `CurrentToolBin_W` at the matched bin, and every abort rung
and the manual unlock zero it, so 0 (unknown) is reported honestly.
`InitialStage` seeds `CurrentToolBin_W` from `SV_ATC_CAROUSEL_POSITION`, the
position CNC12 persisted in `cncm.job`. `M18` (`mfunc18.mac`) is run by the Tool
Library's F2 ATC Reset (`P164 = 1`) after the operator enters the true position;
the rung re-seeds from the value CNC12 sent.

**Hand-moved carousel interlock — nothing in the spindle until proven:**
```plc
IF (ATC_Pos1_I || ATC_Pos2_I || ATC_Pos3_I || ATC_Pos4_I || ATC_Pos5_I) && !ATCMotor_O THEN
  SET CarouselMovedByHand_M, CurrentToolBin_W = 0, TargetToolBinDisp_W = 0
IF CarouselMovedByHand_M THEN RST SpindleEnableOut_O
IF CarouselMovedByHand_M && (SV_PROGRAM_RUNNING || SV_MDI_MODE) &&
   (SpinStart_M || M3_SV || M4_SV) && !ErrorFlag_M THEN
  FaultMsg_W = ATC_HAND_MOVED_MSG_C, SET ShowFaultStage, SET ErrorFlag_M
```
Owner's rule: CNC12 only knows a bin after it has put the tool there. The
carousel parks in the all-switches-off gap, so a hand spin at Z0 cannot be
decoded at rest, but any move trips a switch with the motor off. CNC12 keeps
believing its old tool is in the spindle and will skip an M6 for it, so
`CarouselMovedByHand_M` (MEM454; also set at power-up) holds spindle enable off
and cancels a program/MDI spindle start with `9068 CAROUSEL MOVED BY HAND - ATC
RESET OR TOOL CHANGE` (`ErrorFlag_M`: job cancel, no E-stop needed). It clears
only on an `ATCStage` match or M18. After every boot: one ATC Reset or one M6 to
a different tool before the spindle will run.

**Recovery: the ATC RESET button.** The recovery is one button. CNC12 decides whether to skip an M6 from the tool
its status window names, which is read-only to the PLC and to macros, so after a
hand move a change back to that tool is silently ignored. **Tool 200** is a dummy
the operator maps to a bin in the Tool Library (H and D offsets 0). CNC12 never
believes it is loaded, so `T200 M6` always runs: the carousel search proves the
position, the interlock clears, and CNC12's own end-of-M6 bookkeeping puts the
previously loaded tool back in its bin. Follow it with a real `T## M6`. It is
bound in two places, both running that one line:
- the **ATC RESET** button on the retro VCP (row 11, column 6, under TOOL CHECK);
- **wireless MPG macro button 4**, via `system/plcmacro4.mac`
  (`MpgMacro4_M` -> `SV_SYS_MACRO = 4` was already in the stock PLC).

Because the carousel moves, both only fire from the main CNC12 menu, and both
park Z with `G53 Z0` first like any tool change. While CNC12 believes tool 200
is loaded, whatever sits in that bin is physically under the spindle; the next
real tool change corrects it, which is why the offsets are zero.
The PLC also posts `175 CAROUSEL MOVED - PRESS ATC RESET` the moment the position
becomes unverified, and `176 ATC POSITION RE-ESTABLISHED` when it is proven again,
so the operator is not left to discover it through a refused spindle start.

**VCP `TOOL XX  BIN XX` readout.** `BIN` is `TargetToolBinDisp_W` (W8). `TOOL` is
`ToolInSpindleDisp_W` (W80), the verified tool: `mfunc6.mac` writes the requested
tool number with `G10 P700 R[#4120]` **after `M95 /8`**, a `MainStage` rung tracks
`SV_MACHINE_PARAMETER_700` while `ToolSelected_M` (a change completed since the
last kickoff / hand move / ATC Reset) is set, the M18 rung takes
`SV_ATC_TOOL_IN_SPINDLE` after an ATC Reset, and the hand-move rung forces 0.
**Never move the G10 earlier:** issued mid-M6 it made CNC12 commit the tool
library early and record the new tool's putback from the pre-move carousel
position (2026-09-08: tool 15 ended up in the previous tool's bin). **Never
remove the `G4 P2` before `M95 /8`:** CNC12 samples the reported position on
its own schedule and records the putback from what it last saw; without the
dwell the putback was intermittently the previous tool's bin.
`TOOL 0` therefore means the spindle will refuse to start. Margins live in
`BIN_ELEMENTS` in `tools/vcpgen.py`.

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
IF ATCManualUnlock_I && ATC_Z_Zero_Release_I && !ATCStage THEN SET ATCUnlocked_O,
  CurrentToolBin_W = 0,
  TargetToolBinDisp_W = 0
IF !ATCManualUnlock_I && !ATCStage THEN RST ATCUnlocked_O
```
The front-panel `ATCManualUnlock_I` (INP24) button lets an operator unlock
the carousel by hand, but only when Z is clear (`ATC_Z_Zero_Release_I`,
INP27) and `ATCStage` is not running. Because this is a **Z-motion changer**
(the spindle is empty at Z0 — see [atc.md](atc.md)), a hand-spin is a full tool
swap: the known bin is now stale, so both `CurrentToolBin_W` and the VCP readout
`TargetToolBinDisp_W` are forced to **0 = unknown**. CNC12 sees the 0 through the position
report and the hand-moved interlock (below) refuses the spindle; the operator
declares the new state with the Tool Library's F2 ATC Reset (position, tool in
spindle, its bin) or runs an `M6` to a different tool, which re-derives the bin
by absolute-switch search and clears the latch.

### 3. `ATCStage` (STG16) — carousel indexing and match

Find this stage with `; Acroloc` or the comment `; Acroloc ATC Stage`
(`ATCStage IS STG16`).

**Entry safety re-check:** two aborts, both with **full cleanup**:
```plc
IF ATCStage && !ZeroSpeed_I THEN
  FaultMsg_W = SPINDLE_FAULT_MSG_C, SET ShowFaultStage, SET OtherFault_M,
  RST ATCMotor_O, RST ATCUnlocked_O, RST M6_SV, TargetToolBin_W = 0, RST ATCStage

IF !ATC_Z_Zero_Release_I THEN
  FaultMsg_W = ATC_Spindle_Not_Parked_C, SET ShowFaultStage, SET OtherFault_M,
  RST ATCMotor_O, RST ATCUnlocked_O, RST M6_SV, TargetToolBin_W = 0, RST ATCStage
```
Two defensive checks at stage entry: spindle must be stopped (`ZeroSpeed_I`,
INP12) and Z must be clear of the carousel ring (`ATC_Z_Zero_Release_I`,
INP27). Either failure aborts with a fault message.

**Gotcha:** both aborts must clean up fully — stop the motor, relock, drop `M6_SV`, clear
`TargetToolBin_W`. `RST ATCStage` alone (which is what the Z-parked abort used to do) leaves
`ATCMotor_O`/`ATCUnlocked_O` energized and `M6_SV` set, so the carousel keeps spinning unlocked
while `MainStage` re-arms the stage every scan. Any new abort path needs the same cleanup.

**Start the carousel:**
```plc
IF ATCStage && TargetToolBin_W > 0 THEN
  SET ATCUnlocked_O,     ; OUT18 — unlock piston
  SET ATCMotor_O         ; OUT17 — spin carousel
```

**Position detection — `InBinDecode_M` gating (peak decode):**
```plc
; leading edge only (&& !InBinDecode_M): reset the peak once per switch group
IF ATCMotor_O && ( ATC_Pos1_I || ... || ATC_Pos5_I ) && !InBinDecode_M THEN
  CurrentToolBin_W = 0,
  SET InBinDecode_M
```
On the first switch of a group `CurrentToolBin_W` (W71) is zeroed and
`InBinDecode_M` (MEM443) is set. Each scan the **instantaneous** switch sum is
built in `InstBinID_W` (W75) and its running **peak** is kept in
`CurrentToolBin_W`:

```plc
IF InBinDecode_M THEN InstBinID_W = 0
If InBinDecode_M && ATC_Pos1_I THEN InstBinID_W = InstBinID_W + 1
If InBinDecode_M && ATC_Pos2_I THEN InstBinID_W = InstBinID_W + 2
If InBinDecode_M && ATC_Pos3_I THEN InstBinID_W = InstBinID_W + 4
If InBinDecode_M && ATC_Pos4_I THEN InstBinID_W = InstBinID_W + 8
If InBinDecode_M && ATC_Pos5_I THEN InstBinID_W = InstBinID_W + 10
IF InBinDecode_M && InstBinID_W > CurrentToolBin_W THEN CurrentToolBin_W = InstBinID_W
```

The position switches do **not** open/close simultaneously, so the instantaneous
sum passes through single-switch values (e.g. Pos3 alone = 4) at the entry and
exit edges. Only the **peak** — reached when all of a pocket's switches are on at
the aligned dwell — is the true tool ID, so the decode uses the peak and ignores
the edge partials (this is what stops a requested T4 from false-matching the Pos3
transient at T5/T6/T7).

When all switches drop to 0 (gap between tool positions), `InBinDecode_M`
is cleared and `CurrentToolBin_W` holds the peak = the ID of the tool just seen:
```plc
IF ATCMotor_O && ( !ATC_Pos1_I && !ATC_Pos2_I && !ATC_Pos3_I && !ATC_Pos4_I && !ATC_Pos5_I ) THEN
  RST InBinDecode_M
```

**Match and exit:**
```plc
IF !InBinDecode_M && CurrentToolBin_W == TargetToolBin_W THEN
  TargetToolBin_W = 0,
  SET ToolSelected_M,
  RST ATCMotor_O,
  RST ATCUnlocked_O,
  RST M6_SV,
  RST ATCSpin_T,
  RST ATCStage
```
The compare is gated on `!InBinDecode_M` so it only fires **after all five position
switches return to 0** (the settled ID) — never on the half-built sum during accumulation,
which otherwise let a single-switch transient (e.g. `Pos3` = 4) false-match while passing
another tool (requested T4 stopping at T6/T7). When the settled ID matches the target: motor
stops, piston relocks, `M6_SV` clears (releasing `mfunc6.mac`'s `M100` wait), the search
watchdog `ATCSpin_T` resets, and `ATCStage` resets. The macro then cleans up with `M95 /8`.

`CurrentToolBin_W` is also **cleared once at the M6 kickoff** (in the arm rung), so a stale ID
from the previous change cannot immediate-match — the carousel always physically re-indexes to
the requested tool, even the same tool number (a manual change may have left the wrong tool
under the spindle).

---

## Carousel position encoding

The five position switches (INP28–INP32, highest to lowest bit) encode the
carousel **bin (physical position)** in **base-16 written as decimal** — not the
tool number. (Bin and tool coincide only for a 1:1 loadout; the Tool Library's Bin
column decouples them.) The bit weights in source are:

| Switch | Input | Adds to CurrentToolBin_W |
|--------|-------|--------------------------|
| ATC_Pos1_I | INP32 | +1 |
| ATC_Pos2_I | INP31 | +2 |
| ATC_Pos3_I | INP30 | +4 |
| ATC_Pos4_I | INP29 | +8 |
| ATC_Pos5_I | INP28 | **+10** (not +16) |

The source comment on the Pos5 line reads:
`; Not 16 due to base16 encoded as decimal`

This means bin numbers beyond 9 are encoded so that the "tens digit"
represents the base-16 high nibble. For example:

| Bin | Switch pattern (1=closed) Pos1–Pos5 |
|-----|--------------------------------------|
| B1  | 1 0 0 0 0 |
| B2  | 0 1 0 0 0 |
| B3  | 1 1 0 0 0 |
| B4  | 0 0 1 0 0 |
| B5  | 1 0 1 0 0 |
| B6  | 0 1 1 0 0 |
| B7  | 1 1 1 0 0 |
| B8  | 0 0 0 1 0 |
| B9  | 1 0 0 1 0 |
| B10 | 0 0 0 0 1 |
| B11 | 1 0 0 0 1 |
| B12 | 0 1 0 0 1 |

(Table from the inline comment block in `ATCStage`.)

`CurrentToolBin_W` accumulates while any position switch is high (gated by
`InBinDecode_M`). The compare `IF CurrentToolBin_W == TargetToolBin_W THEN ...`
(src line 2939) is **unconditional** — it runs every PLC scan, including
mid-accumulation while switches are still asserted. The accumulator is zeroed
(`CurrentToolBin_W = 0`) at the leading edge of each bin's switch group (the
first scan where any position switch asserts). A transient partial sum that
equals the target bin during the accumulation window would stop the carousel
prematurely — any edit to the accumulator lines (`+1 / +2 / +4 / +8 / +10`)
must account for this timing sensitivity.

---

## Tool-to-bin map — how M6T## reaches a bin

This machine runs CNC12's **non-random enhanced ATC**: `P160 = 1`, `P161 = 12`
(bins), `P6 = 1` (ATC installed), `P164 = 1` (F2 ATC Reset). The map is CNC12's:

- **Tool Library Bin column** (F1 Setup > F2 Tool > F2 Tool Lib): any of the 200
  tools can be given any bin 1-12; several tools may share a bin; dashes (F1
  Clear Bin) = not in the carousel; 0 = in the spindle (set by CNC12, not by
  hand). F10 saves. The column is locked at `P160 = 0`.
- **`M6T##`**: CNC12 skips the change if tool ## is already in the spindle;
  otherwise `M107` sends that tool's bin in `SV_TOOL_NUMBER` and the kickoff
  (above) guards and latches it.
- **End of M6** (CNC12 bookkeeping, non-random): the previous tool's bin field is
  restored from its putback field; the new tool gets bin = 0 and putback = the
  bin the PLC is reporting. That is why the report must be settled and correct
  when `ATCStage` clears. The M6 start sets an ATC error flag in the job file and
  a normal end clears it; an interrupted or faulted change leaves it set, and the
  next job or MDI start prompts the operator to clear it with Y.
- **After a manual unlock / hand-spin** the operator uses **F2 ATC Reset** to
  declare the position, the tool under the spindle and its bin; that runs
  `mfunc18.mac`.

Vendor references: CNC12 Mill Operator Manual 15.4.118 (Parameter 160), Tool
Library p.64; ATC3 Umbrella Operating Instructions (tool library interface, ATC
Reset). Random mode (`P160 = 2`) is wrong here: it puts the outgoing tool in the
bin the incoming one left, reshuffling the map after every change.

---

## ⚠️ Known gaps

### 1. Carousel search timeout — 20 s watchdog

`ATCSpin_T` (T24) is armed once at M6 kickoff in `MainStage`
(`IF M6_SV && !ATCStage THEN ATCSpin_T = ATC_SPIN_TIMEOUT_MS_C, SET ATCSpin_T`,
`ATC_SPIN_TIMEOUT_MS_C = 20000` ms). A fault rung after the match rung
(`IF ATCStage && ATCSpin_T THEN`) posts `CAROUSEL MOVE TIME OUT` (msg 63),
stops the motor, relocks, and clears the change. Every `ATCStage` exit RSTs the
timer so it re-arms cleanly. If `TargetToolBin_W` never matches — an off-by-one
in the position decode, a faulty switch, or an invalid tool number — the
carousel faults at 20 s instead of spinning forever.

**Risk:** Any edit to the accumulator lines (`+1 / +2 / +4 / +8 / +10`) or to
the `InBinDecode_M` gating must still be tested carefully. A value of
`+16` for Pos5 instead of `+10` would cause bins 10–15 to never match (now a
20 s fault rather than an infinite spin).

### 2. Transmission shift is open-loop by design

`Spindle_Low_gear_O` (OUT19) and `Spindle_High_gear_O` (OUT20) are driven by
the RPM-based auto-shift logic: a decision block in `MainStage` picks the gear
from the un-overridden commanded S (crossover **P860** ± hysteresis **P861**) and
`GearShiftStage` (STG17) swaps clutches with a neutral coast dwell (**P862**;
**P863** is the high-gear ratio). These live in the free 860-870 "Not Used"
block — **do not use P941-943**: the 900-block is reserved on this control
(P911-940 force MEM bits off, and **P941 is the PLC limit-defeat button**).
This is **intentionally open-loop** — the engaged gear is tracked only from the
commanded clutch outputs (`EngagedRange_W`), and a shift is inhibited during
`ATCStage`. Closed-loop gear confirmation is **not planned**: the stock
gear-sense inputs (INP13-15) are unwired and their PLC symbols were removed. See
the "Automatic RPM-based gear shifting" section of `README.md` and
`reference/spindle-transmission.md`.
