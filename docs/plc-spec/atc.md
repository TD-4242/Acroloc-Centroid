# ATC tool-change specification

One-line purpose: the authoritative, line-referenced spec for the custom Acroloc automatic
tool changer (ATC) — `mfunc6.mac`'s macro orchestration, the `MainStage` kickoff/safety rungs,
and the `ATCStage` (STG16) carousel-indexing state machine.

Line numbers as of commit 41f3fd6.

> Both `Centroid-Acroloc-ALLIN1DC.src` and `mfunc6.mac` have moved since that pin. Per this
> doc set's convention the `src:` / `mfunc6.mac:` references below are **not** re-baselined —
> they remain pointers into 41f3fd6, so search by symbol rather than jumping to the cited line
> when reading current source. Lines with no reference are ones added after the pin.

> ⚠️ **Superseded by the tool→bin mapping change (PR #22).** The tool change was reworked:
> a fixed **tool→bin map** (machine parameters **P701–712**, at `P160 = 0`) now
> translates `SV_TOOL_NUMBER` to a carousel bin in `MainStage`, and the ATC variables were
> renamed for tool-vs-bin clarity — `CarouselToolID_W → CurrentToolBin_W`,
> `ChangeToTool_W → TargetToolBin_W`, `InstToolID_W → InstBinID_W`,
> `InToolSelect_M → InBinDecode_M` (plus `ToolInBin1_W..12_W`, `TargetToolBinDisp_W`).
> The line numbers **and** variable names below reflect the 41f3fd6 snapshot and no longer
> match the current program. For the current flow and the map, see
> [`../../.claude/skills/acroloc-s10/reference/atc-flow.md`](../../.claude/skills/acroloc-s10/reference/atc-flow.md).
> This pinned spec should be re-based to the merge commit as a dedicated pass (re-deriving
> the citations), per the "don't re-baseline line refs piecemeal" convention.

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

M108 /1/2                          ; re-enable overrides — pairs the M109 /1/2 above

N1000                              ; mfunc6.mac:28 — end
```

`M109 /1/2` and `M108 /1/2` must always be balanced. An unpaired `M109` leaves CNC12's
override control disabled for the remainder of the program, which also disables the lockout
that normally forces feed override to 100% during a G74/G84 tapping cycle — a tap fed at a
reduced override will break. See
[../superpowers/specs/2026-08-05-rapid-override-g0-only-design.md](../superpowers/specs/2026-08-05-rapid-override-g0-only-design.md).

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

**Spindle-in-changer feed-hold interlock** (`MainStage`, banner `src:2959`, tagged
`; Acroloc -- Spindle-in-changer feed-hold interlock`). The old always-on stop block was
replaced 2026-07-09 (spec
[2026-07-09-spindle-changer-feedhold-design.md](../superpowers/specs/2026-07-09-spindle-changer-feedhold-design.md)).
It **keeps** the unconditional zone spindle-kill -- `IF !ATC_Z_ClearedToolChanger_I THEN
RST SpindleEnableOut_O`, every scan, all modes, so the spindle can never run while Z is in the
changer -- and **adds**, for any program/MDI move driving Z into the changer with the spindle
still turning: feed hold (`SET ActivateFeedHold_M`) + spindle off, then resume the instant
`ZeroSpeed_I` (INP12) confirms a stop (`SET DoCycleStart_SV`), with a **5 s timeout ->
`SPINDLE_FAULT_MSG_C`** if the spindle never stops. If the spindle is already stopped at entry
(normal M6 -- mfunc6 runs `M5` before the park move) the hold never arms and motion proceeds.
The dead `StopSpinBeforATC_T` timer was renamed **`ChangerStopTimer_T`** (`T23`, src:1206) and
given that real timeout role -- so unlike the old block, this one **does** fault on a stuck
spindle. Its dead boot preset and the commented feedrate-to-zero block are gone. INP26 polarity:
**TRUE = Z clear (spindle may run); FALSE = spindle in changer (danger).**

### 3. `ATCStage` (STG16) — carousel indexing and match

Banner at `src:2934-2936` (`ATCStage` (src:2935), tagged `; Acroloc`).

**Search watchdog:** `ATCSpin_T` (T24) is armed at M6 kickoff; if the target tool is never
matched within `ATC_SPIN_TIMEOUT_MS_C` (20 s), `ATCStage` faults `CAROUSEL MOVE TIME OUT`
(message 63) and stops/relocks the carousel. See [Search timeout](#search-timeout) below.

**Entry safety guards.** `ATCStage` has **two** aborts, and (since 2026-07-09) both perform the
same full cleanup the match/finish rung does — stop the motor, relock, drop the M6 request:

```plc
; zero-speed guard (new, src:3014)
IF ATCStage && !ZeroSpeed_I THEN
  FaultMsg_W = SPINDLE_FAULT_MSG_C,
  SET ShowFaultStage, SET OtherFault_M,
  RST ATCMotor_O, RST ATCUnlocked_O, RST M6_SV, ChangeToTool_W = 0,
  RST ATCStage

; Z-parked guard
IF !ATC_Z_Zero_Release_I THEN
  FaultMsg_W = ATC_Spindle_Not_Parked_C,
  SET ShowFaultStage, SET OtherFault_M,
  RST ATCMotor_O, RST ATCUnlocked_O, RST M6_SV, ChangeToTool_W = 0,
  RST ATCStage
```

- **Zero-speed guard** (`ZeroSpeed_I`, `INP12`): the carousel never indexes against a turning
  spindle. INP12 is wired from the F510 VFD and tested; this is a live interlock, not just
  defense-in-depth. It complements — does not replace — `MainStage`'s feed-hold interlock above.
- **Z-parked guard** (`ATC_Z_Zero_Release_I`, `INP27`, "Z axis has cleared tool ring"): posts
  `ATC_Spindle_Not_Parked_C` (src:200 — despite the constant's name referencing "spindle," the
  message text is "Spindle not parked. Z Axis not tool change position.").

Both set the generic `OtherFault_M` latch (folds into the fault OR-gate documented in
main-stage.md's fault-aggregation section) and abort before the carousel turns. **Historical
gotcha, now fixed:** the Z-parked abort previously did `RST ATCStage` *only*, leaving
`ATCMotor_O`/`ATCUnlocked_O` energized and `M6_SV` set — the carousel could keep spinning
unlocked while `MainStage` re-armed the stage every scan. Any new abort path must include the
full cleanup.

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
IF InToolSelect_M THEN InstToolID_W = 0
If InToolSelect_M && ATC_Pos1_I THEN InstToolID_W = InstToolID_W + 1
If InToolSelect_M && ATC_Pos2_I THEN InstToolID_W = InstToolID_W + 2
If InToolSelect_M && ATC_Pos3_I THEN InstToolID_W = InstToolID_W + 4
If InToolSelect_M && ATC_Pos4_I THEN InstToolID_W = InstToolID_W + 8
If InToolSelect_M && ATC_Pos5_I THEN InstToolID_W = InstToolID_W + 10; Not 16 due to base16 encoded as decimal
IF InToolSelect_M && InstToolID_W > CarouselToolID_W THEN CarouselToolID_W = InstToolID_W
```
Each scan the **instantaneous** switch sum is built in `InstToolID_W` (W75) and its running
**peak** is kept in `CarouselToolID_W`. The switches for a pocket do not close simultaneously,
so only the peak — all of the pocket's switches on at the aligned dwell — is the true tool ID;
the entry/exit single-switch partials (e.g. Pos3 alone = 4) are always smaller and never
false-match. `ATC_Pos5_I` adds **10, not 16** — the comment on that line and the block comment
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

**Match and exit** (comment `; lets fire and stop on tool`):
```plc
IF !InToolSelect_M && CarouselToolID_W == ChangeToTool_W THEN
  ChangeToTool_W = 0,
  SET ToolSelected_M,
  RST ATCMotor_O,
  RST ATCUnlocked_O,
  RST M6_SV,
  RST ATCSpin_T,
  RST ATCStage
```
The compare is gated on **`!InToolSelect_M`**, so it fires **only after the switch group has
fully settled** (all five switches returned to 0). `CarouselToolID_W` is zeroed at the leading
edge of each tool's switch group and accumulates across several scans as individual switches
assert (see Accumulator above), so the *partial* sum is a live value during that window.
Comparing it directly (an earlier bug) let a single-switch transient — e.g. `Pos3` = 4 arriving
a scan ahead of its companions — false-match while passing another tool, stopping a requested
**T4 on T6/T7**. Gating on `!InToolSelect_M` compares only the settled ID; this is the design's
intent ("do not act on the tool until all switches return to 0") and is timing-independent.
Separately, `CarouselToolID_W` is **cleared once at the M6 kickoff** (in the arm rung), so a
stale ID from the previous change cannot immediate-match — the carousel always physically
re-indexes to the requested tool, **even the same tool** (guarding against a manual tool change
that left the wrong tool under the spindle). On match: `ChangeToTool_W` is zeroed,
`ToolSelected_M` (`MEM452`) is set, the motor (`ATCMotor_O`) and unlock (`ATCUnlocked_O`)
outputs reset (carousel stops and relocks), `M6_SV` resets (releasing `mfunc6.mac`'s
`M100 /93016` wait), the `ATCSpin_T` search watchdog resets, and `ATCStage` itself resets —
which is also the write to stage-bit `93016` that `mfunc6.mac:25` was blocked on.

### Decode assumptions (validated on-machine)

The peak/settled-ID decode rests on a few mechanical assumptions. All were confirmed working
on the machine; each failure mode degrades to the 20 s `CAROUSEL MOVE TIME OUT` fault (never a
wrong tool or an infinite spin), so they are safe:

- **Stop point is the all-switches-off gap, just past the pocket, not the dwell.** The match
  fires only when `!InToolSelect_M`, so the motor stops after the switches drop and the lock
  pin seats the carousel. This is the intended "do not act until all return to 0" behavior;
  on-machine testing confirms it locks cleanly on the pocket.
- **Requires a clean all-off gap of at least one PLC scan between pockets.** The leading-edge
  reset (`&& !InToolSelect_M`) discards the prior peak when the next pocket's switches begin,
  and the match only evaluates while `!InToolSelect_M`. If the carousel ever spun fast enough
  that the switches never all cleared for a scan, `InToolSelect_M` would never drop, peaks
  would merge across pockets, and the change would time out. Holds comfortably at this
  machine's speed (<10 s/revolution).
- **Requires all of a pocket's switches to co-assert at the aligned dwell** so the peak equals
  the full tool ID. A pocket whose flags never overlap would peak below its true ID and never
  match (-> timeout). Confirmed: the dwell reads the full multi-bit code (e.g. T12 = Pos2+Pos5
  = 12, T7 = Pos1+Pos2+Pos3 = 7).
- **`M6 T0`** (or any `ChangeToTool_W == 0`) exits `ATCStage` immediately without spinning,
  because kickoff clears `CarouselToolID_W` to 0 and `0 == 0` matches at once. Intended (T0 =
  no tool).

**Maintenance caution:** the 20 s watchdog is disarmed by `RST ATCSpin_T` in **all four**
`ATCStage` exits (both entry aborts, the match rung, and the timeout rung). They must stay in
sync — dropping the `RST` from any one exit could leave a stale-expired timer that
immediate-faults the next change.

## Known gaps

### Search timeout

Resolved (was the "no carousel timeout" `;TODO`). `ATCSpin_T` (T24) is armed once at M6
kickoff in `MainStage` — `IF M6_SV && !ATCStage THEN ATCSpin_T = ATC_SPIN_TIMEOUT_MS_C, SET
ATCSpin_T` — with `ATC_SPIN_TIMEOUT_MS_C = 20000` (ms). A fault rung placed after the match
rung, `IF ATCStage && ATCSpin_T THEN`, posts `CAROUSEL_TIMEOUT_MSG_C` (message 63, "CAROUSEL
MOVE TIME OUT"), stops the motor, relocks, and clears `M6_SV`/`ChangeToTool_W`/`ATCStage`.
Every `ATCStage` exit (both aborts and the match) `RST ATCSpin_T` so the timer is clean
before the next change re-arms. So if `ChangeToTool_W` never matches `CarouselToolID_W` — a
faulty position switch, an out-of-range tool number, a wiring fault, or a mismatched
accumulator edit — the carousel now faults at 20 s instead of spinning forever (and
`mfunc6.mac`'s wait returns once the stage clears). Placing the fault rung after the match
rung lets a genuine same-scan match win the tie.

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
