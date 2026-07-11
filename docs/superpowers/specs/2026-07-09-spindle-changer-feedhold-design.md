# Spindle-in-Changer Feed-Hold Interlock -- Design (redo)

**Date:** 2026-07-09
**File touched:** `Centroid-Acroloc-ALLIN1DC.src` (PLC stage language)
**Status:** Design approved; targets current `main` (post PR #2/#10/#11). Supersedes the
2026-06-29 draft and the stale PLC changes on branch `spindle-changer-feedhold` (PR #6).

---

## Why this is a redo

The 2026-06-29 design (PR #6) was written against an earlier `main`, before the
running-machine baseline (PR #10) and the gear-shift work (PR #2) merged, and while
`ZeroSpeed_I` (INP12) was still **unwired**. Two things changed:

1. The PR #6 `.src` diff is stale against the moved baseline -- abandoned; this design is
   re-implemented against current `main`.
2. **`ZeroSpeed_I` (INP12) is now wired from the F510 VFD and tested on the machine.** The
   sensor is trustworthy, so the design drops the fixed-dwell workaround and the dual-option
   hedge in favor of a single **signal-driven** path.

The problem statement, the danger signal, and the overall shape carry over from the 2026-06-29
draft; the resume strategy and the target baseline are what change.

## Post-implementation finding (2026-07-09, on-machine)

Validated on the machine, with one correction to the design intent below:

- **The MainStage interlock does NOT arm for the M6 macro's own park move.** A macro's `G53`
  move does not assert `SV_PROGRAM_RUNNING`/`SV_MDI_MODE`, so the arm rung never sees it
  (confirmed: spindle spinning, Z drove straight to `Z0` with no feed hold). The interlock's
  **confirmed scope is direct programmed/MDI `G53` moves** into the zone (a hand-typed
  `G53 Z0`, a program bug), which it does catch -- feed-hold + wait + resume verified.
- **The M6 path is protected in the macro instead.** `mfunc6.mac` now waits on `ZeroSpeed_I`
  before parking: `M5` (stop) -> `M101 /50012` (block until INP12 confirms zero) -> `G53 Z0`.
  The spindle is confirmed stopped before Z moves toward the changer, independent of the PLC
  interlock.
- **Fail-safe verified:** a disconnected/dead ZeroSpeed sensor reads "not stopped" (INP12 = 0),
  so the macro holds (Z never enters) and the `ATCStage` guard aborts. Software-forcing INP12
  does **not** reach the macro's `M101` wait, so it is not a valid way to test the macro layer --
  use a physical disconnect. See `docs/testing/spindle-changer-safety-test.md`.

Net protection layering: **L1** macro `M101` wait (M6 path), **L2** MainStage interlock (direct
moves), **L3** unconditional zone-kill (all modes), **L4** `ATCStage` zero-speed carousel guard.
The sections below describe L2-L4 (this spec's original scope); L1 lives in `mfunc6.mac`.

## Problem

On the Acroloc S10 the spindle nose enters the automatic tool changer at roughly **Z -1.75 in**.
The spindle must **not be turning** -- not even coasting -- when it enters that region. The
current stock protection (src:2957-2960) drops the spindle **enable** whenever Z is in the zone,
but it never holds motion, never confirms the spindle actually reached zero, and never faults: a
stray `G53 Z0`, an operator MDI move, or a program error can carry a still-coasting spindle into
the changer while the move keeps going.

We want **one** interlock that keeps that unconditional spindle-kill and adds, for any program or
MDI move entering the zone: hold motion, confirm zero speed via the sensor, auto-resume or fault.

## Signals

### Danger signal -- INP26

`ATC_Z_ClearedToolChanger_I` (**INP26**) is the changer-clearance switch:

- **TRUE  = clear / safe** -- Z is clear of the changer; spindle may run.
- **FALSE = danger zone** -- the spindle has entered the changer.

The act condition is **`!ATC_Z_ClearedToolChanger_I`**. The stock stop block already uses the
input this way. The definition comment (INP26) is misleading and is corrected as part of this
work.

### Zero-speed signal -- INP12 (now live)

`ZeroSpeed_I` (**INP12**) is the F510 VFD's zero-speed output, now wired and bench/on-machine
tested. **TRUE = spindle confirmed stopped.** This is the signal the resume decision hangs on;
because it is trusted, resume is immediate on assert rather than after a fixed dwell.

## Requirements

1. **Single unified rule.** One block replaces the stock stop block, keeping its unconditional
   zone spindle-kill and adding the hold / confirm-zero / auto-resume machinery. (Original intent
   was for this to fire during M6's `G53 Z0` park too; on-machine it does not -- macro moves are
   handled by the `mfunc6` `M101` wait, see the post-implementation finding above. This rule
   catches **direct** programmed/MDI moves.)
2. **General protection.** Any programmed or MDI move that drives Z into the changer -- a tool
   change *or any other axis move* -- triggers it. Manual jogging motion is out of scope (feed
   hold / cycle start act only on program/MDI motion); the spindle side is still covered in
   manual mode by the unconditional zone-kill.
3. **On entry to the danger zone:** hold all programmed motion (feed **and** rapid) and command
   the spindle off.
4. **Spindle stays off the entire time Z is in the zone -- in every mode** (program, MDI,
   manual). No re-spin while inside; no manual spindle-start with Z parked in the changer.
5. **Reach zero, signal-driven.** The hold arms only when the spindle is not already confirmed
   stopped at entry (`!ZeroSpeed_I`). Once armed, motion resumes the **instant** `ZeroSpeed_I`
   confirms a stop.
6. **Timeout -> fault.** If `ZeroSpeed_I` does not confirm a stop within **5 s**, raise
   `SPINDLE_FAULT_MSG_C`, leave the feed held, and do **not** resume -- a stuck spindle errors
   out instead of proceeding or hanging.
7. **Auto-resume motion** once zero is confirmed (PLC pulses cycle start) -- no operator action.
8. **Spindle speed resumes after the changer is cleared** -- if the spindle was running (modal
   `M3`/`M4` still active), it restarts at its commanded RPM once INP26 goes TRUE. A program
   `M5` (as inside M6) correctly keeps it off.
9. **Carousel never indexes against a turning spindle.** `ATCStage` gains a `ZeroSpeed_I` guard
   that aborts (with full cleanup) if the spindle is not confirmed stopped.

## What this replaces, and the safety that stays

- **Replaced:** the stock always-on stop block (src:2957-2960,
  `IF !ATC_Z_ClearedToolChanger_I THEN RST SpindleEnableOut_O, SET StopSpinBeforATC_T`). Its
  unconditional zone-kill is kept; the interlock adds the hold / confirm-zero / auto-resume
  machinery for program/MDI moves. The dead commented `;IF StopSpinBeforeATC_T` /
  feedrate-to-zero block (src:2961-2964) is deleted.
- **Added (new):** `ATCStage`'s `ZeroSpeed_I` guard. The base code has no `ZeroSpeed_I` logic
  anywhere; with INP12 now live this is a real interlock, not just defense-in-depth.
- **Fixed (in scope):** the `ATCStage` abort on `!ATC_Z_Zero_Release_I` (src:2972-2976)
  currently does `RST ATCStage` + fault only -- it leaves `ATCMotor_O`/`ATCUnlocked_O` energized
  and `M6_SV` set, so the carousel can keep spinning unlocked and MainStage re-arms the stage
  every scan. Both aborts get the same full cleanup the finish rung (src:3008-3014) already does.
- **Untouched:** the M6 kickoff (`ChangeToTool_W = SV_TOOL_NUMBER, SET ATCStage`), the
  manual-unlock logic, and the gear-shift subsystem.

In a normal M6, mfunc6 issues `M5`/`S0` before the `G53 Z0` park move, so `ZeroSpeed_I` normally
confirms a stop before Z reaches the zone and **no hold is taken** -- the park move runs straight
through. The hold engages only when the spindle is still coasting at zone entry; the fault path
trips only on a genuinely stuck spindle. A run started with Z already parked in the changer (the
tool-change position) starts immediately.

## Design

### Fix the misleading INP26 comment

The INP26 definition comment implies the input is TRUE when the spindle has entered the changer,
which is backwards. Correct it to the real polarity (comment-only, keep column alignment and the
`; Acroloc` tag):

```
; after
ATC_Z_ClearedToolChanger_I      IS INP26 ; Acroloc TRUE = Z clear of tool changer (spindle may run); FALSE = spindle in changer (danger)
```

### Placement

Add the unified block to **`MainStage`**, in place of the replaced stop block, tagged
`; Acroloc`. It must run **after** the `SpinStart_M` seal-in coil (the "Turn spindle on/off"
section) so the per-scan `RST SpindleEnableOut_O` actually holds the output off for the scan --
the same ordering the stock block relied on. Anchor by section name, not line number.

### Resources

| Symbol | Resource | Status | Role |
|--------|----------|--------|------|
| `ChangerHoldActive_M` | MEM448 | **new** | Latched while feed is held and we are waiting for the spindle to stop |
| `ChangerHoldDone_M`   | MEM449 | **new** | Once-per-entry latch; blocks re-arming until Z clears the changer |
| `ChangerStopTimer_T`  | T23    | **reused/renamed** | 5 s timeout backstop; renamed from `StopSpinBeforATC_T` (note the original's missing "e") |

`StopSpinBeforATC_T` is dead in current `main` (armed at src:2960, no live consumer). Renaming it
frees no new resource cost. Its boot preset (`StopSpinBeforATC_T = 1000` in `InitialStage`,
src:1292) is **deleted, not renamed**: the set point is assigned at arm time (`= 5000`), so a
boot preset would be dead code and a second source of truth. MEM448/449 are confirmed free.

Definitions (column-aligned, `; Acroloc`-tagged):

```
; with the other MEM definitions
ChangerHoldActive_M           IS MEM448 ; Acroloc feed-hold active while spindle stops in changer zone
ChangerHoldDone_M             IS MEM449 ; Acroloc once-per-entry latch, cleared when Z clears changer

; rename the existing timer definition (was: StopSpinBeforATC_T IS T23)
ChangerStopTimer_T            IS T23    ; Acroloc spindle-stop timeout backstop for changer-entry hold
```

### MainStage logic block (signal-driven)

```plc
;=============================================================================
; Acroloc -- Spindle-in-changer feed-hold interlock (single unified rule)
;=============================================================================
; Danger zone = !ATC_Z_ClearedToolChanger_I  (INP26 FALSE = spindle in changer).
; ANY programmed or MDI move that drives Z into the changer is held while the
; spindle is commanded off and allowed to reach zero (confirmed by ZeroSpeed_I,
; INP12), then auto-resumed. The spindle is held OFF the whole time Z is in the
; zone and resumes at its commanded speed only after Z exits.
;
; Replaces the stock always-on stop block, KEEPING its unconditional zone
; spindle-kill. Resume is signal-driven: the instant ZeroSpeed_I confirms a
; stop; a 5 s timeout with the spindle still turning faults instead.

; -- 1. clear the once-per-entry latch whenever Z is clear of the changer
IF ATC_Z_ClearedToolChanger_I THEN RST ChangerHoldDone_M

; -- 2. keep the spindle commanded OFF the entire time Z is in the zone, ALL
;       modes (also kills a manual spindle-start with Z parked in the changer,
;       and a running spindle jogged into the zone).
IF !ATC_Z_ClearedToolChanger_I THEN
  RST SpindleEnableOut_O

; -- 3. clean bail-out if the program is stopped/canceled mid-hold; clear the
;       once-per-entry latch so the next run re-confirms zero from scratch.
IF !(SV_PROGRAM_RUNNING || SV_MDI_MODE) THEN
  RST ChangerHoldActive_M, RST ChangerStopTimer_T, RST ChangerHoldDone_M

; -- 4. arm: a program/MDI move into the zone with the spindle NOT already
;       confirmed stopped. If ZeroSpeed_I already reads stopped at entry, this
;       never arms -- no hold, motion proceeds (zone-kill still holds spindle off).
IF (SV_PROGRAM_RUNNING || SV_MDI_MODE) && !ATC_Z_ClearedToolChanger_I
   && !ZeroSpeed_I && !ChangerHoldDone_M && !ChangerHoldActive_M THEN
  SET ChangerHoldActive_M,
  SET ActivateFeedHold_M,            ; hold ALL programmed motion (feed + rapid)
  ChangerStopTimer_T = 5000,
  SET ChangerStopTimer_T

; -- 5. resume the instant zero is confirmed (signal-driven)
IF ChangerHoldActive_M && ZeroSpeed_I THEN
  SET ChangerHoldDone_M,
  RST ChangerHoldActive_M,
  RST ChangerStopTimer_T,
  SET DoCycleStart_SV                ; SET (pulse), not a coil: a coil would RST
                                     ; DoCycleStart_SV every non-resume scan and
                                     ; clobber the stock operator cycle-start coil;
                                     ; that coil clears this SET next scan -> 1-scan pulse

; -- 6. timeout with spindle still turning -> fault; motion stays held, no resume
IF ChangerHoldActive_M && ChangerStopTimer_T && !ZeroSpeed_I THEN
  FaultMsg_W = SPINDLE_FAULT_MSG_C,
  SET ShowFaultStage,
  SET OtherFault_M,
  SET ChangerHoldDone_M,             ; latch handled so we don't re-arm/loop
  RST ChangerHoldActive_M,
  RST ChangerStopTimer_T             ; NOTE: no cycle-start -- motion stays held
```

Timer idiom (PR #2 review lesson): a bare timer is true **when expired**; `ChangerStopTimer_T`
in rung 6 therefore fires only at the 5 s deadline, never on the just-armed scan. `== 0` would
mean "just armed" -- the opposite -- and is not used.

Feed-hold / cycle-start handshake (stock machinery, so no explicit clear is missing): rung 4's
`SET ActivateFeedHold_M` (MEM45) is a self-clearing **trigger** -- the stock code RSTs it ~100 ms
after set (src:2937-2938) and, while it is set, SETs `FeedHoldLED_O` (src:1866-1868), which drives
`DoFeedHold_SV` (src:2101) to hold motion. Rung 5's `SET DoCycleStart_SV` **clears**
`FeedHoldLED_O` (src:1869-1872), dropping `DoFeedHold_SV` and resuming -- the same handshake the
operator's own feed-hold/cycle-start uses. So the interlock deliberately does **not** RST
`ActivateFeedHold_M` (it self-clears) and relies on the cycle-start pulse, not a hold clear, to
resume.

### ATCStage -- zero-speed guard + unified abort cleanup

Add a `ZeroSpeed_I` guard, and give both aborts the same full cleanup the finish rung
(src:3008-3014) already does:

```plc
; NEW: refuse to index the carousel unless the spindle is confirmed stopped.
IF ATCStage && !ZeroSpeed_I THEN
  FaultMsg_W = SPINDLE_FAULT_MSG_C,
  SET ShowFaultStage,
  SET OtherFault_M,
  RST ATCMotor_O,
  RST ATCUnlocked_O,
  RST M6_SV,
  ChangeToTool_W = 0,
  RST ATCStage

; EXISTING abort (Z not parked) -- gains the same full cleanup:
IF !ATC_Z_Zero_Release_I THEN
  FaultMsg_W = ATC_Spindle_Not_Parked_C,
  SET ShowFaultStage,
  SET OtherFault_M,
  RST ATCMotor_O,
  RST ATCUnlocked_O,
  RST M6_SV,
  ChangeToTool_W = 0,
  RST ATCStage
```

Without the cleanup, an abort after the motor started leaves `ATCMotor_O`/`ATCUnlocked_O`
energized and `M6_SV` set -- the carousel keeps spinning unlocked and MainStage re-arms
`ATCStage` every scan.

## How it satisfies each requirement

| Requirement | Mechanism |
|-------------|-----------|
| Single unified rule | One MainStage block replacing the stock stop block; fires on direct programmed/MDI moves (NOT the M6 macro park -- that is the `mfunc6` `M101` wait, per the post-implementation finding) |
| General protection | Arm gated on `(SV_PROGRAM_RUNNING \|\| SV_MDI_MODE) && !ATC_Z_ClearedToolChanger_I && !ZeroSpeed_I` |
| Hold all motion | `SET ActivateFeedHold_M` -> `DoFeedHold_SV` (halts feed **and** rapid) |
| Stop spindle | `RST SpindleEnableOut_O`, re-applied every scan while in the zone -- unconditional, every mode |
| Spindle off entire visit | Zone-kill (rung 2) is independent of the hold latch and of run state |
| Reach zero, signal-driven | Resume on `ZeroSpeed_I` (rung 5); never arms if already stopped at entry |
| Timeout -> fault | Rung 6: `SPINDLE_FAULT_MSG_C` + `ShowFaultStage`/`OtherFault_M`, no cycle-start, at 5 s with `!ZeroSpeed_I` |
| Auto-resume motion | `SET DoCycleStart_SV` pulse on confirmed stop |
| Spindle speed resumes on clear | `SpinStart_M` seal-in + stock speed reload; modal `M3`/`M4` never cleared |
| No oscillation / no re-arm loop | Spindle can't re-spin in the zone; `ChangerHoldDone_M` (set on resume **and** on fault) blocks re-arming until Z exits; cleared on bail-out so a fresh run re-confirms |
| Carousel never indexes a spinning spindle | `ATCStage` `!ZeroSpeed_I` guard with full abort cleanup |

## Lessons from PR #2 folded in

1. **Timer idiom.** Bare-truthy timer = expired (rung 6); no `== 0` expiry misuse (the class of
   bug the PR #2 review caught in the gear-shift timers).
2. **Latch lifecycle.** Every latch has a defined clear -- `ChangerHoldActive_M` on
   resume/fault/bail-out; `ChangerHoldDone_M` on Z-clear and bail-out. No set-but-never-RST latch
   (the `GearSettleActive_M` permanent-lockout bug class).
3. **Full abort cleanup.** ATCStage aborts mirror the finish rung, preventing the
   "stage re-arms every scan / motor spins unlocked" failure -- the same cleanup rigor the ATC
   match path already had.
4. **Observable state.** MEM448/449 and T23 are watchable on PLC Diagnostics; the on-machine
   test plan reads them so behavior is verified against reality, not assumed.

## Behavior walkthrough (general case -- spindle running, errant Z plunge)

1. Z crosses into the changer; INP26 -> FALSE. Zone-kill (rung 2) drops the spindle enable this
   scan on.
2. Spindle still turning (`!ZeroSpeed_I`): rung 4 arms -- feed hold engaged (Z decelerates to a
   stop), spindle coasts down, `ChangerStopTimer_T` started (5 s).
3. As soon as `ZeroSpeed_I` asserts: rung 5 sets `ChangerHoldDone_M`, pulses `DoCycleStart_SV` ->
   motion resumes. If 5 s elapses first with the spindle still turning: rung 6 raises
   `SPINDLE_FAULT_MSG_C`, feed stays held, no resume.
4. After resume, Z is still in the zone, so the spindle stays commanded off and motion continues
   per the program.
5. When motion carries Z out of the zone (INP26 -> TRUE): `ChangerHoldDone_M` cleared, spindle
   kill released; the seal-in restores the spindle at its commanded RPM (if `M3`/`M4` is modally
   active).

## Edge cases

- **Normal M6:** mfunc6 issues `M5`/`S0` before `G53 Z0`, so `ZeroSpeed_I` confirms a stop before
  Z reaches the zone -- rung 4 never arms, park move runs straight through, `ATCStage`'s guard is
  already satisfied.
- **Run started with Z parked in the changer** (tool-change position): spindle already stopped ->
  no hold, motion proceeds; zone-kill holds the spindle off.
- **Manual spindle-start with Z parked:** killed every scan by rung 2 (zone-kill, all modes).
- **Program stop/cancel mid-hold:** rung 3 clears all three latches; the next run re-arms and
  re-confirms zero from scratch.
- **Stuck spindle:** 5 s timeout -> fault, motion held, operator intervenes.

## Out of scope

- **Holding a manual jog.** Feed hold / cycle start act only on program/MDI motion. The spindle
  side is still covered in manual mode by the unconditional zone-kill.
- **Transmission gear-shift automation** -- unrelated, untouched (already merged via PR #2).

## Validation

No automated tests exist for this repo. Verification is on the machine after compiling the `.src`
(`./compile.sh` for syntax/lint; CNC12's compiler on the control PC regenerates `plc.map`).

- Compile clean: no new errors/warnings; the renamed `ChangerStopTimer_T` resolves everywhere and
  the old `StopSpinBeforATC_T` name is gone.
- MDI a Z move into the changer with the spindle running: confirm feed hold + spindle stop,
  resume the instant `ZeroSpeed_I` asserts, and spindle restart after Z clears. Watch MEM448
  (`ChangerHoldActive_M`), MEM449 (`ChangerHoldDone_M`), T23, and INP12 on PLC Diagnostics.
- MDI/run the same move with the spindle already stopped: confirm **no** hold -- motion proceeds
  with the spindle enable held off.
- Manual mode, Z parked in the changer, press jog-panel spindle-start: spindle does **not** start.
- Stuck spindle (hold `ZeroSpeed_I` false, e.g. sensor disconnected): confirm the 5 s timeout,
  `SPINDLE_FAULT_MSG_C`, and motion stays held (no auto-resume).
- Carousel guard: with `ATCStage` reached, force `!ZeroSpeed_I`: confirm the carousel does not
  index, the abort faults, the motor stops, the carousel relocks, and `M6_SV` clears.
