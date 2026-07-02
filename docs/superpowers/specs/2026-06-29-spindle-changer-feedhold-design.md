# Spindle-in-Changer Feed-Hold Interlock — Design

**Date:** 2026-06-29
**File touched:** `Centroid-Acroloc-ALLIN1DC.src` (PLC stage language)
**Status:** Implemented on branch `spindle-changer-feedhold` (PR #6); on-machine validation pending

---

## Problem

On the Acroloc S10, the spindle nose enters the automatic tool changer at roughly
**Z −1.75 in**. The spindle must **not be turning** — not even coasting or braking — when it
enters that region. Today the only protection is inside the M6 tool-change flow
(`MainStage` lines ~2870–2887 and `ATCStage`), which kills the spindle before the carousel
moves. The original PLC block killed the spindle **enable** whenever Z was in the zone
(unconditionally, all modes) — but it never held motion, never confirmed the spindle had
actually reached zero, and never faulted: a stray `G53 Z0`, an operator MDI move, or a
program error could carry a **still-coasting** spindle straight into the changer while the
move kept going.

We want **one** interlock that keeps that unconditional spindle-kill and adds, for any
program or MDI move entering the zone: hold motion, confirm zero speed, auto-resume or
fault.

## The danger signal — INP26

`ATC_Z_ClearedToolChanger_I` (**INP26**) is the changer-clearance switch:

- **TRUE  = clear / safe** — Z is clear of the changer; spindle may run.
- **FALSE = danger zone** — the spindle has entered the changer.

So the danger / act condition is **`!ATC_Z_ClearedToolChanger_I`**. This matches how the
original stop block already used the input.

The source *comment* on the definition (line 228) is **misleading** and will be corrected
as part of this work — see "Fix the misleading INP26 comment" below.

## Requirements (confirmed with owner)

1. **Single unified rule.** One interlock handles all cases. The original always-on
   spindle-stop block is **replaced** (its unconditional kill kept, hold/confirm machinery
   added); the new rule fires during M6's `G53 Z0` park move too.
2. **General protection.** Any programmed or MDI move that drives Z into the changer — a
   tool change *or any other axis move* — must trigger it. Manual jogging is out of scope
   (feed hold / cycle start act only on program/MDI motion anyway).
3. **On entry to the danger zone:** hold all programmed motion (feed **and** rapid) and
   command the spindle to stop.
4. **Spindle stays off the entire time Z is in the zone — in every mode.** The zone-kill is
   unconditional (program, MDI, and manual alike, matching the original block it replaces):
   no oscillation, no re-spin while inside, and no manual spindle-start with Z parked in the
   changer.
5. **Reach zero before resuming.** The hold arms only when the spindle is not already
   confirmed stopped (`!ZeroSpeed_I` at entry — if `ZeroSpeed_I` already reads stopped, no
   hold is taken and motion proceeds; the zone-kill still holds the spindle off). Two
   selectable confirmation styles:
   - **Option A (default):** fixed **3-second dwell** to let the spindle coast, then a
     single `ZeroSpeed_I` confirmation.
   - **Option B (commented):** resume the instant **`ZeroSpeed_I` (INP12)** confirms a stop.
   Switching between A and B is a clearly-labeled comment swap.
6. **Timeout → fault.** If the spindle has **not** reached zero by the deadline (end of the
   dwell for A; a 5 s timeout for B), raise `SPINDLE_FAULT_MSG_C`, leave the feed held, and
   do **not** resume — a stuck spindle errors out instead of proceeding or hanging.
7. **Auto-resume motion** once zero is confirmed (PLC pulses cycle start) — no operator
   action required.
8. **Spindle speed resumes after the changer is cleared** — if the spindle was running
   (modal `M3`/`M4` still active), it restarts at its commanded RPM once INP26 goes TRUE.
   A program `M5` (as inside M6) correctly keeps it off.

## What this replaces, and the safety that stays

- **Replaced:** the original always-on spindle-stop block
  (`IF !ATC_Z_ClearedToolChanger_I THEN RST SpindleEnableOut_O, SET StopSpinBeforATC_T` —
  unconditional, all modes, no zero-speed confirmation). Its unconditional zone-kill is
  **kept verbatim in spirit** (`IF !ATC_Z_ClearedToolChanger_I THEN RST SpindleEnableOut_O`,
  ungated); the new interlock adds the hold / confirm-zero / auto-resume machinery on top
  for program/MDI moves.
- **Added (new in this change, defense-in-depth):** `ATCStage`'s carousel guard
  (`IF ATCStage && !ZeroSpeed_I THEN ...fault + full cleanup..., RST ATCStage`). The base
  code had **no** `ZeroSpeed_I` logic anywhere; this guard is introduced together with the
  interlock so the carousel can never index against a spinning spindle even if the MainStage
  rule is bypassed. Its abort — like the pre-existing `!ATC_Z_Zero_Release_I` check, which
  gains the same cleanup — stops the motor, relocks, and drops the M6 request
  (`RST ATCMotor_O, RST ATCUnlocked_O, RST M6_SV, ChangeToTool_W = 0`); `RST ATCStage`
  alone would leave the motor energized and let MainStage re-arm the stage every scan.
- **Untouched:** the M6 kickoff (`ChangeToTool_W = SV_TOOL_NUMBER, SET ATCStage`) and the
  manual-unlock logic.

In a normal M6 the spindle is already commanded off early by mfunc6 (`S0`/`M5`) before the
park move, so `ZeroSpeed_I` usually confirms a stop before Z reaches the zone and **no hold
is taken at all** — the park move proceeds directly. The hold + dwell only engages when the
spindle is still coasting at zone entry; the fault path only trips on a genuinely stuck
spindle. Likewise a run started with Z already parked in the changer (common: that is the
tool-change position) starts immediately instead of paying a dwell.

## Design

### Fix the misleading INP26 comment

The definition comment on line 228 currently implies the input is TRUE when the spindle has
entered the changer, which is backwards from how the signal actually behaves and how the
code uses it. Correct it to state the real polarity:

```
; before
ATC_Z_ClearedToolChanger_I      IS INP26 ; Acroloc the spindle has entered the tool changer (zero rpm)

; after
ATC_Z_ClearedToolChanger_I      IS INP26 ; Acroloc TRUE = Z clear of tool changer (spindle may run); FALSE = spindle in changer (danger)
```

Comment-only change — keep the column alignment and the `; Acroloc` tag.

### Placement

Add the unified block to **`MainStage`**, in place of the replaced stop block ("Make sure
spindle stops before entering tool changer"), tagged `; Acroloc`. This is critical: it must
run **after** the `SpinStart_M` seal-in coil (in the "Turn spindle on/off" section) so that
the per-scan `RST SpindleEnableOut_O` actually holds the output off for the scan — the same
ordering the original block relied on. (Anchor by the section name, not a line number;
line numbers rot.)

### Resources

| Symbol | Resource | Status | Role |
|--------|----------|--------|------|
| `ChangerHoldActive_M` | MEM448 | **new** | Latched while holding feed + waiting for the spindle to stop |
| `ChangerHoldDone_M`   | MEM449 | **new** | "Already handled this entry" — blocks re-arming until Z clears |
| `ChangerStopTimer_T`  | T23    | **reused** | Dwell (Option A) / timeout (Option B). Renamed from `StopSpinBeforATC_T`, freed by replacing the original block |

No new timer is needed — replacing the original block frees `StopSpinBeforATC_T` (T23,
note the original's missing "e"), which we rename to `ChangerStopTimer_T`. (The earlier draft reserved T25; that is no longer used.)

Definition changes, column-aligned with the surrounding stock style and `; Acroloc`-tagged:

```
; with the other MEM definitions (near lines 710–711)
ChangerHoldActive_M           IS MEM448 ; Acroloc feed-hold active while spindle stops in changer zone
ChangerHoldDone_M             IS MEM449 ; Acroloc once-per-entry latch, cleared when Z clears changer

; rename the existing timer definition
; before:  StopSpinBeforATC_T              IS T23
ChangerStopTimer_T              IS T23 ; Acroloc spindle stop dwell / timeout for changer-entry hold
```

The old InitialStage preset (`StopSpinBeforATC_T = 1000,`) is **deleted, not renamed**: both
options assign the timer's set point inline at arm time (`= 3000` for A, `= 5000` for B), so
a boot-time preset would be dead code and a misleading second source of truth for the dwell.

### Logic block

```plc
;=============================================================================
; Acroloc — Spindle-in-changer feed-hold interlock (single unified rule)
;=============================================================================
; Danger zone = !ATC_Z_ClearedToolChanger_I  (INP26 FALSE = spindle in changer).
; ANY programmed or MDI move that drives Z into the changer — a tool change or
; any other axis move — is held while the spindle is commanded off and allowed
; to reach zero, then auto-resumed. The spindle is held OFF the whole time Z is
; in the zone and resumes at its commanded speed only after Z exits.
;
; This replaces the original always-on stop block ("Make sure spindle stops
; before entering tool changer"), KEEPING its unconditional zone spindle-kill
; and adding the feed-hold / dwell / confirm machinery for program moves.
; A NEW defense-in-depth check in ATCStage (added together with this
; interlock) also refuses to run the carousel unless ZeroSpeed_I confirms
; the spindle is stopped.
;
; Spindle resume is automatic: we only drop the enable output (SpindleEnableOut_O)
; while Z is in the zone; the modal M3/M4 command (SpinStart_M) is untouched, so
; the SpinStart_M seal-in coil (in the "Turn spindle on/off" section above)
; restores the spindle at SV_PC_COMMANDED_SPINDLE_SPEED
; once INP26 goes TRUE. A program M5 (e.g. inside M6) correctly keeps it off.

; -- Clear the once-per-entry latch whenever Z is clear of the changer
IF ATC_Z_ClearedToolChanger_I THEN RST ChangerHoldDone_M

; -- Keep the spindle commanded OFF the entire time Z is in the zone — in ALL
; modes, exactly like the original block this interlock replaced. This also
; kills a manual spindle-start (jog panel / keyboard key) attempted with Z
; parked inside the changer, and kills a running spindle jogged into the zone.
IF !ATC_Z_ClearedToolChanger_I THEN
  RST SpindleEnableOut_O

; -- Clean bail-out if the program is stopped/canceled mid-hold.
; Also clear the once-per-entry latch so the next run re-arms the hold and
; re-confirms zero speed from scratch instead of trusting a latch left over
; from the canceled run.
IF !(SV_PROGRAM_RUNNING || SV_MDI_MODE) THEN
  RST ChangerHoldActive_M, RST ChangerStopTimer_T, RST ChangerHoldDone_M

;-----------------------------------------------------------------------------
; OPTION A  (DEFAULT / ACTIVE): fixed 3-second dwell, then confirm-or-fault
; If Z enters the zone during a run with the spindle NOT confirmed stopped:
; hold feed, stop spindle, dwell 3 s, then resume if ZeroSpeed_I confirms a
; stop — otherwise fault. If ZeroSpeed_I already reads stopped at entry (M6
; issued M5 well before the Z move, or a run starts with Z parked in the
; changer), NO hold is taken — the unconditional zone-kill above still holds
; the spindle off for the whole visit, so skipping the dwell costs no safety.
;-----------------------------------------------------------------------------
IF (SV_PROGRAM_RUNNING || SV_MDI_MODE) && !ATC_Z_ClearedToolChanger_I
   && !ZeroSpeed_I && !ChangerHoldDone_M && !ChangerHoldActive_M THEN
  SET ChangerHoldActive_M,
  SET ActivateFeedHold_M,            ; hold ALL programmed motion (feed + rapid)
  ChangerStopTimer_T = 3000,
  SET ChangerStopTimer_T

IF ChangerHoldActive_M && ChangerStopTimer_T && ZeroSpeed_I THEN
  SET ChangerHoldDone_M,             ; dwell elapsed & spindle confirmed stopped — auto-resume
  RST ChangerHoldActive_M,
  RST ChangerStopTimer_T,
  SET DoCycleStart_SV                ; pulse cycle-start (SET, not a coil: a coil would RST
                                     ; DoCycleStart_SV every non-resume scan and clobber the
                                     ; stock operator cycle-start coil; that coil clears this
                                     ; SET next scan, making it a one-scan pulse)

IF ChangerHoldActive_M && ChangerStopTimer_T && !ZeroSpeed_I THEN
  FaultMsg_W = SPINDLE_FAULT_MSG_C,  ; dwell elapsed, spindle still turning
  SET ShowFaultStage,
  SET OtherFault_M,
  SET ChangerHoldDone_M,             ; latch handled so we don't re-arm/loop
  RST ChangerHoldActive_M,
  RST ChangerStopTimer_T             ; NOTE: no cycle-start — motion stays held

;-----------------------------------------------------------------------------
; OPTION B  (COMMENTED): resume as soon as the zero-speed SIGNAL confirms a stop
; To switch: comment out ALL THREE OPTION A "IF" blocks above, uncomment these.
; Same arm condition as Option A (only when the spindle is actually turning);
; differs on resume: Option A always waits the full dwell, Option B resumes the
; instant ZeroSpeed_I confirms a stop, faulting if it never stops within 5 s.
;-----------------------------------------------------------------------------
; IF (SV_PROGRAM_RUNNING || SV_MDI_MODE) && !ATC_Z_ClearedToolChanger_I
;    && !ZeroSpeed_I && !ChangerHoldDone_M && !ChangerHoldActive_M THEN
;   SET ChangerHoldActive_M,
;   SET ActivateFeedHold_M,
;   ChangerStopTimer_T = 5000,
;   SET ChangerStopTimer_T
; IF ChangerHoldActive_M && ZeroSpeed_I THEN
;   SET ChangerHoldDone_M,
;   RST ChangerHoldActive_M,
;   RST ChangerStopTimer_T,
;   SET DoCycleStart_SV
; IF ChangerHoldActive_M && ChangerStopTimer_T && !ZeroSpeed_I THEN
;   FaultMsg_W = SPINDLE_FAULT_MSG_C,
;   SET ShowFaultStage,
;   SET OtherFault_M,
;   SET ChangerHoldDone_M,
;   RST ChangerHoldActive_M,
;   RST ChangerStopTimer_T
```

## How it satisfies each requirement

| Requirement | Mechanism |
|-------------|-----------|
| Single unified rule | One block replacing the original stop block; fires during the M6 park move and any other move |
| General protection (any program/MDI move) | Hold gated on `(SV_PROGRAM_RUNNING \|\| SV_MDI_MODE) && !ATC_Z_ClearedToolChanger_I && !ZeroSpeed_I` |
| Hold all motion | `SET ActivateFeedHold_M` → `FeedHoldLED_O` → `DoFeedHold_SV` (halts feed **and** rapid) |
| Stop spindle | `RST SpindleEnableOut_O`, re-applied every scan while in the zone — **unconditional, every mode** (also covers manual spindle-start with Z in the changer) |
| Spindle off entire time in zone | Kill is zone-gated only, independent of the hold latch and of run state |
| Reach zero via wait **or** signal | Option A dwell (T23) + confirm / Option B continuous `ZeroSpeed_I`; neither arms if `ZeroSpeed_I` already reads stopped at entry |
| Timeout → fault | `SPINDLE_FAULT_MSG_C` + `ShowFaultStage`/`OtherFault_M`, no cycle-start, on deadline with `!ZeroSpeed_I` |
| Auto-resume motion | `SET DoCycleStart_SV` pulse on confirmed stop (SET, not a coil — a coil would clobber the stock operator cycle-start) |
| Spindle speed resumes on clear | `SpinStart_M` seal-in + stock speed reload; modal `M3`/`M4` never cleared |
| No oscillation / no re-arm loop | Spindle can't re-spin in the zone; `ChangerHoldDone_M` (set on resume *and* on fault) blocks re-arming until Z exits — but it is also cleared on the run-stopped bail-out, so a fresh run re-confirms from scratch if Z is still in the zone |
| Carousel never indexes a spinning spindle | `ATCStage`'s `!ZeroSpeed_I` guard — **new, added with this change** — with full abort cleanup (stop motor, relock, `RST M6_SV`, `ChangeToTool_W = 0`) |

## Behavior walkthrough (general case — spindle running, errant Z plunge)

1. Z crosses into the changer; INP26 → FALSE. The unconditional zone-kill drops the spindle
   enable from this scan on.
2. The spindle is still turning (`!ZeroSpeed_I`), so the interlock arms: feed hold engaged
   (Z decelerates to a stop), spindle coasts down, `ChangerStopTimer_T` started (3 s for A).
3. At the deadline:
   - **stopped** (`ZeroSpeed_I`): `ChangerHoldDone_M` set, `SET DoCycleStart_SV` pulsed →
     motion resumes;
   - **still spinning** (`!ZeroSpeed_I`): `SPINDLE_FAULT_MSG_C` raised, feed stays held, no
     resume — operator must intervene.
4. After a successful resume, Z is still in the zone, so the spindle stays commanded off and
   motion continues per the program.
5. When the resumed motion carries Z out of the zone (INP26 → TRUE): `ChangerHoldDone_M`
   cleared, spindle kill released; the seal-in restores the spindle at its commanded RPM
   (if `M3`/`M4` is still modally active).

For an M6, mfunc6 already issued `M5` well before `G53 Z0`, so `ZeroSpeed_I` normally
confirms a stop before Z reaches the zone and **no hold occurs** — the park move runs
straight through, the macro sets `M6_SV`, and `ATCStage` runs with its own zero-speed guard
satisfied. Only if the spindle is still coasting at zone entry does the hold + dwell engage.

## Known caveat — Option A and the zero-speed sensor

Option A reads `ZeroSpeed_I` at zone entry (to decide whether a hold is needed at all) and
again at the end of the 3 s dwell (to decide resume-vs-fault). So Option A is not
sensor-independent: a working `ZeroSpeed_I` is required to avoid spurious holds and faults. The dwell remains the grace
period (assumed ≥ worst-case coast-down). If `ZeroSpeed_I` is ever untrustworthy, either
lengthen the dwell or drop the fault branch — both are localized, commented changes.

## Out of scope

- **Holding a manual jog.** Feed hold and cycle start act only on program/MDI motion; a
  hand jog can't be paused or resumed by this logic. (The spindle side IS covered in manual
  mode: the unconditional zone-kill drops the spindle enable whenever Z is in the changer,
  whatever the mode.)
- **Transmission gear-shift automation** (`Spindle_Low_gear_O` / `Spindle_High_gear_O`) —
  unrelated, untouched.

## Validation

No automated tests exist for this repo. Verification is on the machine/simulator after
compiling the `.src` in CNC12 (which also regenerates `plc.map`). Suggested checks:

- Compile cleanly in CNC12's PLC compiler (no new errors; confirm the renamed
  `ChangerStopTimer_T` resolves everywhere and the old `StopSpinBeforATC_T` name is gone).
- MDI a Z move into the changer with the spindle running: confirm feed hold + spindle stop,
  ~3 s dwell, auto-resume, and spindle restart after Z clears.
- MDI/run the same move with the spindle already stopped: confirm **no** hold or dwell —
  motion proceeds straight into the zone with the spindle enable held off.
- In manual mode with Z parked in the changer, press the jog-panel spindle-start key:
  confirm the spindle does **not** start (unconditional zone-kill).
- Simulate a spindle that won't stop (hold `ZeroSpeed_I` false): confirm the dwell elapses,
  `SPINDLE_FAULT_MSG_C` shows, and motion stays held (no auto-resume).
- Run an M6: confirm no regression — spindle stops, carousel indexes, tool change completes;
  confirm `ATCStage`'s `!ZeroSpeed_I` fault path still works.
- Confirm a program `M5` before entering the zone leaves the spindle off after clearing.
```
