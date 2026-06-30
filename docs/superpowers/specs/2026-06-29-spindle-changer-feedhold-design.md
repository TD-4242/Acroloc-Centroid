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
moves. There is **no protection for any other move** that drives Z into the changer: a
stray `G53 Z0`, an operator MDI move, or a program error could carry a spinning spindle
straight into the changer.

We want **one** interlock that fires whenever Z enters the changer zone during a program or
MDI run — covering the tool change and every other move — replacing the M6-only stop block.

## The danger signal — INP26

`ATC_Z_ClearedToolChanger_I` (**INP26**) is the changer-clearance switch:

- **TRUE  = clear / safe** — Z is clear of the changer; spindle may run.
- **FALSE = danger zone** — the spindle has entered the changer.

So the danger / act condition is **`!ATC_Z_ClearedToolChanger_I`**. This matches how the
existing M6 block at line 2870 already uses the input.

The source *comment* on the definition (line 228) is **misleading** and will be corrected
as part of this work — see "Fix the misleading INP26 comment" below.

## Requirements (confirmed with owner)

1. **Single unified rule.** One interlock handles all cases. The M6-only spindle-stop block
   (lines 2870–2887) is **removed**; the new rule fires during M6's `G53 Z0` park move too.
2. **General protection.** Any programmed or MDI move that drives Z into the changer — a
   tool change *or any other axis move* — must trigger it. Manual jogging is out of scope
   (feed hold / cycle start act only on program/MDI motion anyway).
3. **On entry to the danger zone:** hold all programmed motion (feed **and** rapid) and
   command the spindle to stop.
4. **Spindle stays off the entire time Z is in the zone.** No oscillation, no re-spin while
   inside.
5. **Reach zero before resuming**, by one of two selectable means:
   - **Option A (default):** unconditional fixed **3-second dwell** on every zone entry to
     let the spindle coast, then a single `ZeroSpeed_I` confirmation.
   - **Option B (commented):** resume the instant **`ZeroSpeed_I` (INP12)** confirms a stop;
     arms only when the spindle is genuinely turning (`!ZeroSpeed_I`).
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

- **Removed:** the M6-only spindle-stop block, `Centroid-Acroloc-ALLIN1DC.src` lines
  ~2870–2887 (`IF M6_SV && !ATC_Z_ClearedToolChanger_I ...` through the
  `StopSpinBeforeATC_T` timeout handling). Its job — stop the spindle on changer approach,
  fault if it won't stop — is now done by the unified rule for **all** moves, not just M6.
- **Kept (not a duplicate):** `ATCStage`'s own carousel guard at line ~2897
  (`IF ATCStage && !ZeroSpeed_I THEN ...fault..., RST ATCStage`) and the `!ATC_Z_Zero_Release_I`
  check. These prevent the carousel from indexing against a spinning spindle and are
  independent defense-in-depth — they remain untouched.
- **Untouched:** the M6 kickoff (`ChangeToTool_W = SV_TOOL_NUMBER, SET ATCStage`, line 2853)
  and the manual-unlock logic (lines 2856–2864).

In a normal M6 the spindle is already commanded off early by mfunc6 (`S0`/`M5`) before the
park move, so by the end of the dwell it is stopped and the rule auto-resumes without
faulting; the fault path only trips on a genuinely stuck spindle.

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

Add the unified block to **`MainStage`**, in place of the removed M6 stop block (around the
old lines 2866–2887), tagged `; Acroloc`. This is critical: it must run **after** the
spindle seal-in at line 2210 so that the per-scan `RST SpindleEnableOut_O` actually holds
the output off for the scan (same ordering the proven M6 stop at line 2870 relied on).

### Resources

| Symbol | Resource | Status | Role |
|--------|----------|--------|------|
| `ChangerHoldActive_M` | MEM448 | **new** | Latched while holding feed + waiting for the spindle to stop |
| `ChangerHoldDone_M`   | MEM449 | **new** | "Already handled this entry" — blocks re-arming until Z clears |
| `ChangerStopTimer_T`  | T23    | **reused** | Dwell (Option A) / timeout (Option B). Renamed from `StopSpinBeforeATC_T`, freed by removing the M6 block |

No new timer is needed — removing the M6 block frees `StopSpinBeforeATC_T` (T23), which we
rename to `ChangerStopTimer_T`. (The earlier draft reserved T25; that is no longer used.)

Definition changes, column-aligned with the surrounding stock style and `; Acroloc`-tagged:

```
; with the other MEM definitions (near lines 710–711)
ChangerHoldActive_M           IS MEM448 ; Acroloc feed-hold active while spindle stops in changer zone
ChangerHoldDone_M             IS MEM449 ; Acroloc once-per-entry latch, cleared when Z clears changer

; rename the existing timer definition (line 1180)
; before:  StopSpinBeforeATC_T             IS T23
ChangerStopTimer_T              IS T23 ; Acroloc spindle stop dwell / timeout for changer-entry hold

; InitialStage preset (line 1266): rename the symbol; value is also set inline at arm time
; before:  StopSpinBeforeATC_T = 5000,
ChangerStopTimer_T = 5000,
```

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
; This is the ONE place the spindle is stopped on changer entry. The old M6-only
; stop block was removed; ATCStage still independently guards the carousel with
; its own !ZeroSpeed_I check, so the carousel can never index a spinning spindle.
;
; Spindle resume is automatic: we only drop the enable output (SpindleEnableOut_O)
; while Z is in the zone; the modal M3/M4 command (SpinStart_M) is untouched, so
; the line-2210 seal-in restores the spindle at SV_PC_COMMANDED_SPINDLE_SPEED
; once INP26 goes TRUE. A program M5 (e.g. inside M6) correctly keeps it off.

; -- Clear the once-per-entry latch whenever Z is clear of the changer
IF ATC_Z_ClearedToolChanger_I THEN RST ChangerHoldDone_M

; -- Keep the spindle commanded OFF the entire time Z is in the zone, during a run
IF (SV_PROGRAM_RUNNING || SV_MDI_MODE) && !ATC_Z_ClearedToolChanger_I THEN
  RST SpindleEnableOut_O

; -- Clean bail-out if the program is stopped/canceled mid-hold.
; Also clear ChangerHoldDone_M so a fresh run RE-ARMS the hold if Z is still in
; the zone (an operator could manually spin the spindle while stopped, since the
; zone-kill above is gated to a run). Without this, the once-per-entry latch could
; let motion resume into the zone with the spindle still coasting.
IF !(SV_PROGRAM_RUNNING || SV_MDI_MODE) THEN
  RST ChangerHoldActive_M, RST ChangerStopTimer_T, RST ChangerHoldDone_M

;-----------------------------------------------------------------------------
; OPTION A  (DEFAULT / ACTIVE): fixed 3-second dwell, then confirm-or-fault
; Any time Z enters the zone during a run: hold feed, stop spindle, dwell 3 s,
; then resume if ZeroSpeed_I confirms a stop — otherwise fault.
;-----------------------------------------------------------------------------
IF (SV_PROGRAM_RUNNING || SV_MDI_MODE) && !ATC_Z_ClearedToolChanger_I
   && !ChangerHoldDone_M && !ChangerHoldActive_M THEN
  SET ChangerHoldActive_M,
  SET ActivateFeedHold_M,            ; hold ALL programmed motion (feed + rapid)
  ChangerStopTimer_T = 3000,
  SET ChangerStopTimer_T

IF ChangerHoldActive_M && ChangerStopTimer_T && ZeroSpeed_I THEN
  SET ChangerHoldDone_M,             ; dwell elapsed & spindle confirmed stopped — auto-resume
  RST ChangerHoldActive_M,
  RST ChangerStopTimer_T,
  (DoCycleStart_SV)

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
; Arms only when the spindle is actually turning (!ZeroSpeed_I); resumes the
; instant ZeroSpeed_I confirms a stop; faults if it never stops within 5 s.
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
;   (DoCycleStart_SV)
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
| Single unified rule | One block; M6 stop block removed; fires during M6 park move and any other move |
| General protection (any program/MDI move) | Trigger gated on `(SV_PROGRAM_RUNNING \|\| SV_MDI_MODE) && !ATC_Z_ClearedToolChanger_I` |
| Hold all motion | `SET ActivateFeedHold_M` → `FeedHoldLED_O` → `DoFeedHold_SV` (halts feed **and** rapid) |
| Stop spindle | `RST SpindleEnableOut_O`, re-applied every scan while in the zone |
| Spindle off entire time in zone | Kill is zone-gated, independent of the hold latch |
| Reach zero via wait **or** signal | Option A dwell (T23) + confirm / Option B continuous `ZeroSpeed_I` |
| Timeout → fault | `SPINDLE_FAULT_MSG_C` + `ShowFaultStage`/`OtherFault_M`, no cycle-start, on deadline with `!ZeroSpeed_I` |
| Auto-resume motion | `(DoCycleStart_SV)` pulse on confirmed stop |
| Spindle speed resumes on clear | Line-2210 seal-in + line-2300 speed reload; modal `M3`/`M4` never cleared |
| No oscillation / no re-arm loop | Spindle can't re-spin in the zone; `ChangerHoldDone_M` (set on resume *and* on fault) blocks re-arming until Z exits — but it is also cleared on the run-stopped bail-out, so a fresh run re-arms if Z is still in the zone |
| Carousel never indexes a spinning spindle | `ATCStage`'s existing `!ZeroSpeed_I` guard (line 2897), retained |

## Behavior walkthrough (general case — spindle running, errant Z plunge)

1. Z crosses into the changer; INP26 → FALSE.
2. Interlock arms: feed hold engaged (Z decelerates to a stop), spindle enable dropped
   (spindle coasts down), `ChangerStopTimer_T` started (3 s for A).
3. At the deadline:
   - **stopped** (`ZeroSpeed_I`): `ChangerHoldDone_M` set, `(DoCycleStart_SV)` pulsed →
     motion resumes;
   - **still spinning** (`!ZeroSpeed_I`): `SPINDLE_FAULT_MSG_C` raised, feed stays held, no
     resume — operator must intervene.
4. After a successful resume, Z is still in the zone, so the spindle stays commanded off and
   motion continues per the program.
5. When the resumed motion carries Z out of the zone (INP26 → TRUE): `ChangerHoldDone_M`
   cleared, spindle kill released; the seal-in restores the spindle at its commanded RPM
   (if `M3`/`M4` is still modally active).

For an M6, the same flow runs during `G53 Z0`; because mfunc6 already issued `M5`, the
spindle is stopped by the deadline (no fault), motion resumes, the macro proceeds to set
`M6_SV`, and `ATCStage` runs with its own zero-speed guard satisfied.

## Known caveat — Option A and the zero-speed sensor

With the timeout→fault, Option A now reads `ZeroSpeed_I` **once**, at the end of the 3 s
dwell, to decide resume-vs-fault. So Option A is no longer fully sensor-independent: a
working `ZeroSpeed_I` is required to avoid spurious faults. The dwell remains the grace
period (assumed ≥ worst-case coast-down). If `ZeroSpeed_I` is ever untrustworthy, either
lengthen the dwell or drop the fault branch — both are localized, commented changes.

## Out of scope

- **Manual jogging into the zone.** Feed hold and cycle start act only on program/MDI
  motion; a hand jog can't be paused or resumed by this logic.
- **Transmission gear-shift automation** (`Spindle_Low_gear_O` / `Spindle_High_gear_O`) —
  unrelated, untouched.

## Validation

No automated tests exist for this repo. Verification is on the machine/simulator after
compiling the `.src` in CNC12 (which also regenerates `plc.map`). Suggested checks:

- Compile cleanly in CNC12's PLC compiler (no new errors; confirm the renamed
  `ChangerStopTimer_T` resolves everywhere and the old `StopSpinBeforeATC_T` name is gone).
- MDI a Z move into the changer with the spindle running: confirm feed hold + spindle stop,
  ~3 s dwell, auto-resume, and spindle restart after Z clears.
- Simulate a spindle that won't stop (hold `ZeroSpeed_I` false): confirm the dwell elapses,
  `SPINDLE_FAULT_MSG_C` shows, and motion stays held (no auto-resume).
- Run an M6: confirm no regression — spindle stops, carousel indexes, tool change completes;
  confirm `ATCStage`'s `!ZeroSpeed_I` fault path still works.
- Confirm a program `M5` before entering the zone leaves the spindle off after clearing.
```
