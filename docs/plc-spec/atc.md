# ATC tool-change specification

One-line purpose: the authoritative, line-referenced spec for the custom Acroloc automatic
tool changer (ATC) — `mfunc6.mac`'s macro orchestration, the `MainStage` kickoff/safety rungs,
and the `ATCStage` (STG16) carousel-indexing state machine.

Line numbers as of commit 41f3fd6 (`Centroid-Acroloc-ALLIN1DC.src` unchanged since then —
verified via `git log -1 --format=%H -- Centroid-Acroloc-ALLIN1DC.src` returning
`21128a9006ef99abb061276807d38401787105f0`, whose most recent change to this file predates
41f3fd6, and `git status` shows no working-tree modifications to the `.src`).

Resource name -> definition-line lookups are in [definitions.md](definitions.md); stage sweep
order and `SET`/`RST` timing rules are in [scan-model.md](scan-model.md). The `MainStage`
kickoff/safety rungs are summarized at
[main-stage.md#atc-kickoff](main-stage.md#atc-kickoff); this file gives the full treatment
of those rungs plus the `ATCStage` carousel logic that main-stage.md defers here.

## The three-piece flow

A tool change (`M6`) is split across three cooperating pieces that hand off to each other via
PLC bits: `mfunc6.mac` (macro, runs on the CNC interpreter) -> `MainStage` (STG4, kickoff and
entry safety) -> `ATCStage` (STG16, carousel indexing and match).

### 1. `mfunc6.mac` — macro orchestrator

```gcode
IF #4202 || #4201 THEN GOTO 1000   ; mfunc6.mac:11 — skip if graphing/searching
IF #50001                          ; mfunc6.mac:12 — prevent lookahead
M109 /1/2                          ; mfunc6.mac:13 — disable overrides

S0                                 ; mfunc6.mac:15
M5                                 ; mfunc6.mac:16 — stop spindle
M9                                 ; mfunc6.mac:17 — coolant off
G53 Z0                             ; mfunc6.mac:20 — move Z to tool-change position
M107                               ; mfunc6.mac:21 — send target tool number to PLC
G4 P.1                             ; mfunc6.mac:22 — 0.1 s settle delay
M94 /8                             ; mfunc6.mac:23 — SET M6_SV, arms ATCStage
G4 p1                              ; mfunc6.mac:24 — 1 s wait (comment asks "can I shorten this wait?")
M100 /93016                        ; mfunc6.mac:25 — block until ATCStage's bit clears
M95 /8                             ; mfunc6.mac:26 — RST M6_SV, handshake cleanup

N1000                              ; mfunc6.mac:28 — end
```

The macro never touches ATC hardware bits directly (no `ATCMotor_O`/`ATCUnlocked_O` writes).
It stops the spindle and coolant, parks Z, tells the PLC which tool it wants via `M107`
(the standard Centroid tool-number handoff macro), then flips `M6_SV` on with `M94 /8` and
blocks on `M100 /93016` — a wait on PLC bit `93016`, which per Centroid's stage-bit numbering
convention is `ATCStage`'s (STG16) own active/complete bit; the inline comment at
`mfunc6.mac:25` ("ATCStage RST") confirms this is a wait-for-stage-to-clear, not an
arbitrary bit. Once `ATCStage` resets (see match/exit below), the macro falls through and
tidies up with `M95 /8`.

Both guard patterns (`#4202`/`#4201` graph/search skip, ending at `N1000`) follow the
standard M-function macro convention documented in `CLAUDE.md` and must be preserved on any
edit.

### 2. `MainStage` — kickoff and entry safety

Summarized in [main-stage.md#atc-kickoff](main-stage.md#atc-kickoff); full detail here.

**Kickoff** (`src:2910-2911`, tagged `; Acroloc tool stage start` at `src:2910`):
```plc
IF M6_SV THEN ChangeToTool_W = SV_TOOL_NUMBER, SET ATCStage
```
The instant `mfunc6.mac`'s `M94 /8` sets `M6_SV` (`SV_M94_M95_8`, `M6_SV` (src:1036)),
this rung latches the CNC's currently-selected tool number (`SV_TOOL_NUMBER`, the system
variable `M107` populated) into `ChangeToTool_W` (`W72`, `ChangeToTool_W` (src:1094))
and `SET`s `ATCStage`. Because `ATCStage` (`STG16`, `ATCStage` (src:1207)) is swept
**after** `MainStage` (`STG4`) in file order, per `scan-model.md` this `SET` takes effect in
the **same scan** — `ATCStage`'s body runs immediately on the same pass that saw `M6_SV`
go true.

**Manual carousel unlock** (`src:2913-2922`, tagged `; Acroloc manual tool changes`):
```plc
IF ATCManualUnlock_I && ATC_Z_Zero_Release_I && !ATCStage THEN SET ATCUnlocked_O
IF !ATCManualUnlock_I && !ATCStage THEN RST ATCUnlocked_O

IF ATCManualUnlock_I THEN
  FaultMsg_W = ATC_Lock_Not_Released_C,
  SET ShowFaultStage
IF !ATCManualUnlock_I THEN
  FaultMsg_W = ATC_Lock_Released_C,
  SET ShowFaultStage
```
`ATCManualUnlock_I` (`INP24`, `ATCManualUnlock_I` (src:226)) is the front-panel manual-unlock
button. It only drives `ATCUnlocked_O` (`OUT18`, `ATCUnlocked_O` (src:383)) while
`ATC_Z_Zero_Release_I` (`INP27`, `ATC_Z_Zero_Release_I` (src:229), "Z axis has cleared tool
ring") is true and `ATCStage` is **not** running — this keeps manual unlock from fighting
`ATCStage`'s own lock/unlock control once an automatic change has started. Note the two
`ATCManualUnlock_I` message rungs (`src:2917-2922`) are **unconditional** on `ATCStage`
(no `!ATCStage` guard) — they post `ATC_Lock_Not_Released_C` (src:201) /
`ATC_Lock_Released_C` (src:202) via `ShowFaultStage` purely as an operator status echo of the
button state, every scan the button state is read, independent of whether a change is in
progress.

**Spindle-stopped-before-entry safety** (`src:2924-2932`, tagged `; Acroloc Make sure spindle
stops before entering tool changer`):
```plc
IF !ATC_Z_ClearedToolChanger_I THEN
  RST SpindleEnableOut_O,
  SET StopSpinBeforATC_T
  ;SavedCurrentFeedrate = CurrentFeedrate ??

;IF StopSpinBeforeATC_T THEN
  ; feedrate to zero
```
While `ATC_Z_ClearedToolChanger_I` (`INP26`, `ATC_Z_ClearedToolChanger_I` (src:228), "the
spindle has entered the tool changer (zero rpm)") is false, the spindle enable output
`SpindleEnableOut_O` (`OUT7`, `SpindleEnableOut_O` (src:374)) is forcibly held reset and
`StopSpinBeforATC_T` (`T23`, `StopSpinBeforATC_T` (src:1187), preset to 1000 ms once in
`InitialStage` at `src:1275` — see [boot.md](boot.md)) is armed. This rung is
**unconditional on `M6_SV`** — it fires any time `ATC_Z_ClearedToolChanger_I` reads false,
not only during a tool change, forcibly killing spindle enable whenever the Z-in-tool-changer
input isn't asserted. The commented-out `SavedCurrentFeedrate` line (`src:2961`) and the
commented `;IF StopSpinBeforeATC_T` block (`src:2963-2964`, feedrate-to-zero idea — note the
dead comment misspells the live symbol, which is `StopSpinBeforATC_T` without the "e") are dead
code — no live rung reads `StopSpinBeforATC_T` anywhere in the file to gate a fault/timeout;
its only consumer is decorative. This is the same gap main-stage.md's ATC-kickoff section
flags and leaves to this file to confirm: **confirmed here — `StopSpinBeforATC_T` has no
timeout consumer.**

### 3. `ATCStage` (STG16) — carousel indexing and match

Banner at `src:2934-2936` (`ATCStage` (src:2935), tagged `; Acroloc`).

**Known-timeout gap, stated in source** (`src:2937`):
```plc
;TODO: add timer to error so carousol doesn't spin for ever if tool not found
```
See [Known gaps](#known-gaps) below.

**Entry safety re-check** (`src:2939-2943`):
```plc
IF !ATC_Z_Zero_Release_I THEN
  FaultMsg_W = ATC_Spindle_Not_Parked_C,
  SET ShowFaultStage,
  SET OtherFault_M,
  RST ATCStage
```
Unlike `MainStage`'s check (which gates on `ATC_Z_ClearedToolChanger_I`, `INP26`), this rung
inside `ATCStage` checks `ATC_Z_Zero_Release_I` (`INP27`) — "Z axis has cleared tool ring."
If Z is not clear of the carousel ring, the stage posts `ATC_Spindle_Not_Parked_C` (src:200,
despite the constant's name referencing "spindle," the message text is "Spindle not parked.
Z Axis not tool change position."), sets the generic `OtherFault_M` fault latch (folds into
the fault OR-gate documented in main-stage.md's fault-aggregation section), and immediately
`RST`s `ATCStage` — aborting the change before the carousel ever turns. Gotcha for future
edits: **there is no check of `ZeroSpeed_I` (spindle-stopped) inside `ATCStage` itself** —
spindle-stop safety lives entirely in `MainStage`'s `StopSpinBeforATC_T`/
`ATC_Z_ClearedToolChanger_I` rung above (which, as noted, doesn't actually timeout/fault on
its own); `ATCStage`'s own guard is Z-position only.

**Start the carousel** (`src:2945-2948`):
```plc
; z axis is clear of tool carousel, carousel is ready to spin
IF ATCStage && ChangeToTool_W > 0 THEN
  SET ATCUnlocked_O,
  SET ATCMotor_O
```
Once `ATCStage` is active and a nonzero target tool is latched, the stage unlocks the
carousel piston (`ATCUnlocked_O`, `OUT18`) and starts the carousel motor (`ATCMotor_O`,
`OUT17`, `ATCMotor_O` (src:382)). This rung re-evaluates every scan `ATCStage` is set; it
does not one-shot, so both outputs stay driven for the stage's duration.

**Position detection — `InToolSelect_M` gating** (`src:2950-2954`):
```plc
; If carousel is moving and any of the position switchs are triggered we need to start
; tracking the switches to calculate what position we are at
IF ATCMotor_O && ( ATC_Pos1_I || ATC_POS2_I || ATC_Pos3_I || ATC_Pos4_I || ATC_pos5_I ) THEN
  CarouselToolID_W = 0,
  SET InToolSelect_M
```
(Note: the source mixes case on `ATC_POS2_I`/`ATC_pos5_I` vs. the canonical
`ATC_Pos2_I`/`ATC_Pos5_I` spelling used in the definitions block — PLC stage language is
case-insensitive for identifiers, so this resolves to the same symbols; it is not a bug, just
inconsistent capitalization.) While the motor is running, the leading edge of **any** of the
five position switches (`ATC_Pos1_I` (`INP32`, src:234) through `ATC_Pos5_I`
(`INP28`, src:230)) zeroes the accumulator `CarouselToolID_W` (`W71`, src:1093) and sets
`InToolSelect_M` (`MEM443`, src:710) — entering "accumulating this tool's ID" mode.

**Accumulator** (`src:2956-2967`, comment block at `src:2956-2962` documents the encoding
and a worked T1-T12 truth table):
```plc
If InToolSelect_M && ATC_Pos1_I THEN CarouselToolID_W = CarouselToolID_W + 1
If InToolSelect_M && ATC_Pos2_I THEN CarouselToolId_W = CarouselToolID_W + 2
If InToolSelect_M && ATC_Pos3_I THEN CarouselToolID_W = CarouselToolID_W + 4
If InToolSelect_M && ATC_Pos4_I THEN CarouselToolId_W = CarouselToolID_W + 8
If InToolSelect_M && ATC_Pos5_I THEN CarouselToolId_W = CarouselToolID_W + 10; Not 16 due to base16 encoded as decimal
```
(`CarouselToolId_W` on the Pos2/Pos4/Pos5 lines is the same case-insensitive resolution to
`CarouselToolID_W`.) Each switch adds its weight while `InToolSelect_M` holds and that switch
is closed. `ATC_Pos5_I` adds **10, not 16** — the comment on that line and the block comment
above spell out why: tool IDs beyond 9 are encoded as base-16 values but *written and compared
as decimal*, so the "16s place" is represented by an offset of 10 (the decimal-looking "tens
digit") rather than a true binary 16. The five switches therefore encode 31 possible raw sums
(1+2+4+8+10), of which the tool-ID space in use is 1-12 per the source's own comment table:

| Tool | Pos1 (+1) | Pos2 (+2) | Pos3 (+4) | Pos4 (+8) | Pos5 (+10) | Sum |
|------|-----------|-----------|-----------|-----------|------------|-----|
| T1   | * | | | | | 1 |
| T2   | | * | | | | 2 |
| T3   | * | * | | | | 3 |
| T4   | | | * | | | 4 |
| T5   | * | | * | | | 5 |
| T6   | | * | * | | | 6 |
| T7   | * | * | * | | | 7 |
| T8   | | | | * | | 8 |
| T9   | * | | | * | | 9 |
| T10  | | | | | * | 10 |
| T11  | * | | | | * | 11 |
| T12  | | * | | | * | 12 |

(Table transcribed from the inline comment at `src:2958-2962`; `*` = switch closed.)

**Exit accumulation mode** (`src:2969-2972`):
```plc
; If all tool position switches go back to 0 then we need to exit the tool selection mode
; and CarouselToolId_W should be the tool number passing the spindle.
IF ATCMotor_O && ( !ATC_Pos1_I && !ATC_Pos2_I && !ATC_Pos3_I && !ATC_Pos4_I && !ATC_Pos5_I ) THEN
  RST InToolSelect_M
```
Once all five switches drop (the gap between tool positions on the carousel), `InToolSelect_M`
clears and `CarouselToolID_W` holds the settled ID of the tool that just passed the read
position.

**Match and exit** (`src:2974-2981`, comment `; lets fire and stop on tool`):
```plc
IF CarouselToolID_W == ChangeToTool_W THEN
  ChangeToTool_W = 0,
  SET ToolSelected_M,
  RST ATCMotor_O,
  RST ATCUnlocked_O,
  RST M6_SV,
  RST ATCStage
```
This compare is **unconditional** — it is a bare `IF`, gated on neither `InToolSelect_M` nor
`ATCMotor_O`, and it runs every PLC scan regardless of where in the switch-accumulation cycle
the carousel currently is. **Timing sensitivity:** because `CarouselToolID_W` is zeroed at the
leading edge of each tool's switch group and then accumulates across several scans as
individual switches assert (see Accumulator above), the *partial* sum during that
accumulation window is a live value this rung reads every scan. If a partial sum transiently
equals `ChangeToTool_W` before the group finishes settling, the carousel stops prematurely on
the wrong tool (or the right tool, by luck, mid-transition). Any edit to the accumulator
weights or to the `InToolSelect_M` gating rungs must preserve — or explicitly reason about —
this window; it is not merely a stylistic quirk but the actual mechanism (in combination with
correct weight design) that makes stopping on the fully-settled ID reliable in practice. On
match: `ChangeToTool_W` is zeroed, `ToolSelected_M` (`MEM444`, src:711) is set, the motor
(`ATCMotor_O`) and unlock (`ATCUnlocked_O`) outputs are both reset (carousel stops and
relocks), `M6_SV` is reset (releasing `mfunc6.mac`'s `M100 /93016` wait), and `ATCStage`
itself resets — which is also the write to stage-bit `93016` that `mfunc6.mac:25` was
blocked on.

## Known gaps

### No carousel timeout

Stated directly in source at `src:2937`:
```plc
;TODO: add timer to error so carousol doesn't spin for ever if tool not found
```
`ATCSpin_T` (`T24`, `ATCSpin_T` (src:1188), comment "used to detect fault if unable to find
position") is **defined but never `SET`, armed, or read** anywhere in the current `.src` —
grep confirms no other occurrence of `ATCSpin_T` in the file. If `ChangeToTool_W` never
matches `CarouselToolID_W` — a faulty position switch, an out-of-range tool number, a wiring
fault, or a mismatched accumulator edit — the match rung (`src:2975`) never fires,
`ATCMotor_O` stays asserted indefinitely, and `mfunc6.mac`'s `M100 /93016` wait
(`mfunc6.mac:25`) never returns. There is no operator-visible fault path for this condition;
the carousel simply keeps spinning. `CLAUDE.md` calls this out as a caution for anyone
touching the match/exit rungs.

### Message-rung unconditional posting

Not gated on any change of state, `ATCManualUnlock_I`'s status messages (`src:2917-2922`)
re-post every scan the button is read in either state — a cosmetic gap (repeated identical
message posts), not a safety one, but worth knowing before assuming these are edge-triggered.

## Verification

Every `(src:NNNN)` and `mfunc6.mac:N` citation above was checked against
`Centroid-Acroloc-ALLIN1DC.src` / `mfunc6.mac` at commit 41f3fd6 with `sed -n '<line>p'`;
`git log -1 --format=%H -- Centroid-Acroloc-ALLIN1DC.src` returns
`21128a9006ef99abb061276807d38401787105f0` and `git status` shows the `.src` unmodified in
the working tree, confirming line numbers as of 41f3fd6 still apply.
