# Spindle-in-Changer Feed-Hold Interlock — Design

**Date:** 2026-06-29
**File touched:** `Centroid-Acroloc-ALLIN1DC.src` (PLC stage language)
**Status:** Design approved, pending implementation plan

---

## Problem

On the Acroloc S10, the spindle nose enters the automatic tool changer at roughly
**Z −1.75 in**. The spindle must **not be turning** — not even coasting or braking — when it
enters that region. Today the only protection is inside the M6 tool-change flow
(`MainStage` line ~2870 and `ATCStage`), which kills the spindle before the carousel
moves. There is **no protection for any other move** that drives Z into the changer: a
stray `G53 Z0`, an operator MDI move, or a program error could carry a spinning spindle
straight into the changer.

We want a **general interlock**, independent of M6, that fires whenever Z enters the
changer zone during a program or MDI run.

## The danger signal — INP26

`ATC_Z_ClearedToolChanger_I` (**INP26**) is the changer-clearance switch:

- **TRUE  = clear / safe** — Z is clear of the changer; spindle may run.
- **FALSE = danger zone** — the spindle has entered the changer.

So the danger / act condition is **`!ATC_Z_ClearedToolChanger_I`**. This matches how the
existing M6 block at line 2870 already uses the input.

The source *comment* on the definition (line 228) is **misleading** and will be corrected
as part of this work — see "Fix the misleading INP26 comment" below.

## Requirements (confirmed with owner)

1. **General protection.** Any programmed or MDI move that drives Z into the changer —
   a tool change *or any other axis move* — must trigger the interlock. Manual jogging is
   out of scope (feed hold / cycle start act only on program/MDI motion anyway).
2. **On entry to the danger zone:** hold all programmed motion (feed **and** rapid) and
   command the spindle to stop.
3. **Spindle stays off the entire time Z is in the zone.** No oscillation, no re-spin
   while inside.
4. **Reach zero before resuming**, by one of two selectable means:
   - **Option A (default):** an unconditional fixed **3-second dwell** on every zone entry
     — sensor-independent; assumes the spindle coasts to rest within 3 s.
   - **Option B (commented):** wait for the **`ZeroSpeed_I` (INP12)** signal to confirm an
     actual stop before resuming. Arms only when the spindle is genuinely turning
     (`!ZeroSpeed_I`).
   Switching between A and B is a clearly-labeled comment swap.
5. **Auto-resume motion** once zero is reached (PLC pulses cycle start) — no operator
   action required.
6. **Spindle speed resumes after the changer is cleared** — if the spindle was running
   (modal `M3`/`M4` still active), it restarts at its commanded RPM once INP26 goes TRUE.
   A program `M5` (as inside M6) correctly keeps it off.

## Relationship to the existing M6 flow

The interlock is **purely additive** and does not replace the existing M6 spindle-stop
logic:

- The M6 block (lines ~2870–2887) and `ATCStage` (line ~2897) still **hard-enforce**
  `ZeroSpeed_I` before and during the carousel move, with a `SPINDLE_FAULT_MSG_C` fault on
  a 5 s timeout. So a tool change retains true zero-speed enforcement regardless of which
  option is selected here.
- In a normal M6 the spindle is usually already stopped by the time Z reaches the changer
  (mfunc6 issues `S0`/`M5` first), so the new interlock typically adds no pause there. It
  exists to catch the moves the M6 logic never sees.

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

Add the block to **`MainStage`**, immediately **after** the existing M6 spindle-stop block
(after line ~2887), tagged `; Acroloc`. This is critical: it must run **after** the spindle
seal-in at line 2210 so that the per-scan `RST SpindleEnableOut_O` actually holds the
output off for the scan (same ordering the proven M6 stop at line 2870 relies on).

### New resources (verified free)

| Symbol | Resource | Role |
|--------|----------|------|
| `ChangerHoldActive_M` | MEM448 | Latched while holding feed + waiting for the spindle to stop |
| `ChangerHoldDone_M`   | MEM449 | "Already handled this entry" — blocks re-arming until Z clears |
| `ChangerStopDelay_T`  | T25    | 3000 ms coast-down dwell (Option A only) |

Definitions to add, column-aligned with the surrounding stock style and `; Acroloc`-tagged:

```
; with the other MEM definitions (near lines 710–711)
ChangerHoldActive_M           IS MEM448 ; Acroloc feed-hold active while spindle stops in changer zone
ChangerHoldDone_M             IS MEM449 ; Acroloc once-per-entry latch, cleared when Z clears changer

; with the other timer definitions (near lines 1180–1181)
ChangerStopDelay_T              IS T25 ; Acroloc spindle coast-down dwell before resuming into changer zone
```

### Logic block

```plc
;=============================================================================
; Acroloc — Spindle-in-changer feed-hold interlock (general protection)
;=============================================================================
; Danger zone = !ATC_Z_ClearedToolChanger_I  (INP26 FALSE = spindle in changer).
; ANY programmed or MDI move that drives Z into the changer — a tool change or
; any other axis move — is held while the spindle is commanded off and allowed
; to reach zero, then auto-resumed. The spindle is held OFF the whole time Z is
; in the zone and resumes at its commanded speed only after Z exits.
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

; -- Clean bail-out if the program is stopped/canceled mid-hold
IF !(SV_PROGRAM_RUNNING || SV_MDI_MODE) THEN
  RST ChangerHoldActive_M, RST ChangerStopDelay_T

;-----------------------------------------------------------------------------
; OPTION A  (DEFAULT / ACTIVE): unconditional 3-second dwell on zone entry
; Any time Z enters the zone during a run: hold feed, stop spindle, dwell 3 s.
;-----------------------------------------------------------------------------
IF (SV_PROGRAM_RUNNING || SV_MDI_MODE) && !ATC_Z_ClearedToolChanger_I
   && !ChangerHoldDone_M && !ChangerHoldActive_M THEN
  SET ChangerHoldActive_M,
  SET ActivateFeedHold_M,            ; hold ALL programmed motion (feed + rapid)
  ChangerStopDelay_T = 3000,
  SET ChangerStopDelay_T

IF ChangerHoldActive_M && ChangerStopDelay_T == 0 THEN
  SET ChangerHoldDone_M,
  RST ChangerHoldActive_M,
  RST ChangerStopDelay_T,
  (DoCycleStart_SV)                  ; auto-resume motion

;-----------------------------------------------------------------------------
; OPTION B  (COMMENTED): wait for the zero-speed SIGNAL instead of a dwell
; To switch: comment out BOTH OPTION A "IF" blocks above, uncomment these two.
; Arms only when the spindle is actually turning (!ZeroSpeed_I); resumes only
; once ZeroSpeed_I (INP12) confirms a real stop. (Timer T25 is unused here.)
;-----------------------------------------------------------------------------
; IF (SV_PROGRAM_RUNNING || SV_MDI_MODE) && !ATC_Z_ClearedToolChanger_I
;    && !ZeroSpeed_I && !ChangerHoldDone_M && !ChangerHoldActive_M THEN
;   SET ChangerHoldActive_M,
;   SET ActivateFeedHold_M
; IF ChangerHoldActive_M && ZeroSpeed_I THEN
;   SET ChangerHoldDone_M,
;   RST ChangerHoldActive_M,
;   (DoCycleStart_SV)
```

## How it satisfies each requirement

| Requirement | Mechanism |
|-------------|-----------|
| General protection (any program/MDI move) | Trigger gated on `(SV_PROGRAM_RUNNING \|\| SV_MDI_MODE) && !ATC_Z_ClearedToolChanger_I`, not on M6 |
| Hold all motion | `SET ActivateFeedHold_M` → `FeedHoldLED_O` → `DoFeedHold_SV` (halts feed **and** rapid) |
| Stop spindle | `RST SpindleEnableOut_O`, re-applied every scan while in the zone |
| Spindle off entire time in zone | Kill is zone-gated, independent of the hold latch |
| Reach zero via wait **or** signal | Option A dwell (T25) / Option B `ZeroSpeed_I` |
| Auto-resume motion | `(DoCycleStart_SV)` pulse |
| Spindle speed resumes on clear | Line-2210 seal-in + line-2300 speed reload, since modal `M3`/`M4` is never cleared |
| No oscillation | Spindle can't re-spin in the zone; `ChangerHoldDone_M` blocks re-arming until Z exits |

## Behavior walkthrough (general case — spindle running, errant Z plunge)

1. Z crosses into the changer; INP26 → FALSE.
2. Interlock arms: feed hold engaged (Z decelerates to a stop), spindle enable dropped
   (spindle coasts down), dwell timer started.
3. After 3 s (Option A) or `ZeroSpeed_I` (Option B): `ChangerHoldDone_M` set,
   `(DoCycleStart_SV)` pulsed → motion resumes.
4. Z is still in the zone, so the spindle stays commanded off; motion continues per the
   program.
5. When the resumed motion carries Z out of the zone (INP26 → TRUE): `ChangerHoldDone_M`
   cleared, spindle kill released; the seal-in restores the spindle at its commanded RPM
   (if `M3`/`M4` is still modally active).

## Known caveat — Option A's blind dwell

Option A resumes after a fixed 3 s **whether or not the spindle has actually stopped**. It
is safe only if 3 s reliably exceeds the worst-case spindle coast-down on this machine. If
that is ever in doubt, switch to **Option B** (sensor-confirmed stop) — a one-comment-swap
change. Note that tool changes are unaffected by this caveat: the existing `ATCStage` logic
independently requires `ZeroSpeed_I` before the carousel moves.

## Out of scope

- **Manual jogging into the zone.** Feed hold and cycle start act only on program/MDI
  motion; a hand jog can't be paused or resumed by this logic. (An owner-selected
  "always RST the spindle in the zone even outside a program" variant was considered and
  declined.)
- **Transmission gear-shift automation** (`Spindle_Low_gear_O` / `Spindle_High_gear_O`) —
  unrelated, untouched.

## Validation

No automated tests exist for this repo. Verification is on the machine/simulator after
compiling the `.src` in CNC12 (which also regenerates `plc.map`). Suggested checks:

- Compile cleanly in CNC12's PLC compiler (no new errors).
- MDI a Z move into the changer with the spindle running: confirm feed hold + spindle stop,
  ~3 s dwell, auto-resume, and spindle restart after Z clears.
- Run an M6: confirm no regression — spindle stops, carousel indexes, tool change completes;
  confirm the existing `ZeroSpeed_I` fault path still works (e.g., simulate spindle not
  stopping).
- Confirm a program `M5` before entering the zone leaves the spindle off after clearing.
```
