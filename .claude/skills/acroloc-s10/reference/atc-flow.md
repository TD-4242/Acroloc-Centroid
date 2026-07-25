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

The macro does **not** drive any ATC hardware directly. It relies entirely
on the PLC stage to index the carousel and signal completion. The chosen bin is
shown on the **retro VCP** as a live `BIN` readout (`plc_word` 8 =
`TargetToolBinDisp_W`), not as a macro message — `M225` is a *modal* box that
would pause the change until dismissed.

### 2. `MainStage` — kickoff and spindle-stop safety

In `MainStage` (STG4), two blocks handle the ATC entry. Search the `.src`
for the comment `; Acroloc tool stage start` to find them.

**Kickoff — translate the requested tool to its bin, then set the stage:**

At `P160 = 0` (this machine's mode) `SV_TOOL_NUMBER` is the **raw tool number**
(`M6T##`). MainStage maps it to a carousel **bin** through the fixed loadout
table — machine parameters **P701–712** = the tool loaded in bins 1–12, cached
in `ToolInBin1_W..ToolInBin12_W` at `LoadParametersStage`:
```plc
IF M6_SV THEN TargetToolBin_W = 99                          ; default: tool in no bin
IF M6_SV && ToolInBin1_W  == SV_TOOL_NUMBER THEN TargetToolBin_W = 1
IF M6_SV && ToolInBin2_W  == SV_TOOL_NUMBER THEN TargetToolBin_W = 2
; ... bins 3..12 ...
IF M6_SV THEN TargetToolBinDisp_W = TargetToolBin_W, SET ATCStage
```
`M6_SV` is `SV_M94_M95_8`. `TargetToolBin_W` (W72) becomes the bin whose loaded
tool equals the request; the **99** default is an unreachable bin, so a tool in
no bin never matches and faults on the 20 s watchdog instead of false-matching
bin 0. `TargetToolBinDisp_W` (W8) holds the chosen bin for the retro VCP `BIN`
readout (`plc_word` 8). `ATCStage` (STG16) then indexes the carousel to
`TargetToolBin_W` — its search/decode/match logic is unchanged.

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
`TargetToolBinDisp_W` are forced to **0 = unknown**. The PLC cannot clear CNC12's
current tool at `P160 = 0`, so the operator re-establishes the tool after a manual
swap; the next `M6` re-derives the bin by absolute-switch search regardless.

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
tool number. (Bin and tool coincide only for a 1:1 loadout; the P701–712 map
decouples them.) The bit weights in source are:

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

## Tool-to-bin map (P701–712) — how M6T## reaches a bin

This machine runs at **`P160 = 0`** (Centroid's built-in ATC modes are *not*
used — see below). A tool number is mapped to a fixed carousel bin entirely in
the PLC:

- **`P701–712` = the tool number loaded in bins 1–12** (end-user parameters).
  Set `P702 = 31` to say "bin 2 holds tool 31"; a plain 1:1 loadout is
  `P701=1 … P712=12`; an empty bin is left `0`. Cached into
  `ToolInBin1_W..ToolInBin12_W` at `LoadParametersStage` **every scan**, so
  edits on the parameter screen take effect with no reboot.
- The `MainStage` kickoff (above) sets `TargetToolBin_W` to the bin whose loaded
  tool equals `SV_TOOL_NUMBER`, or `99` if none — then `ATCStage` indexes there.
- `mfunc6` prints `Change to T# in bin # (P70#)` (or "not assigned to a bin" for
  the `99` case).

**Why not CNC12's enhanced ATC (P160≠0):** ruled out on-machine. Random
(`P160=2`) reshuffles the bin map after every change (it assumes tools move
between bins); non-random (`P160=1`) forces tool == bin. This is a **fixed-pocket**
carousel (a tool from bin 5 always returns to bin 5), so it needs an
arbitrary-but-fixed map, which only the PLC table provides.

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
