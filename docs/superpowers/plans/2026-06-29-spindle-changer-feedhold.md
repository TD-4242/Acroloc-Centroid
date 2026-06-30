# Spindle-in-Changer Feed-Hold Interlock Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a single PLC interlock that holds feed and stops the spindle whenever a program/MDI move drives Z into the tool changer, faults if the spindle won't stop, and auto-resumes (restoring spindle speed) once Z clears — replacing the M6-only stop block.

**Architecture:** One new logic block in `MainStage` of `Centroid-Acroloc-ALLIN1DC.src`, gated on `(SV_PROGRAM_RUNNING || SV_MDI_MODE) && !ATC_Z_ClearedToolChanger_I`. It uses the stock feed-hold mechanism (`ActivateFeedHold_M`), drops the spindle enable output, dwells/waits for zero speed, then pulses `DoCycleStart_SV`. The old M6-only spindle-stop block is removed; `ATCStage`'s own zero-speed carousel guard is retained as defense-in-depth.

**Tech Stack:** Centroid CNC12 / MPU11 (ALLIN1DC) PLC stage language (`.src`). Single source file. No application code, no package manager.

## Global Constraints

- **One file only:** all edits are in `Centroid-Acroloc-ALLIN1DC.src`. Do **not** edit `plc.map` (generated on compile).
- **No automated tests in this repo.** The `.src` is compiled by CNC12's PLC compiler and validated on the machine/simulator on the Windows control PC. In-repo verification for each task is a `grep` sanity check; the real compile + behavior validation is the final on-machine section.
- **Match the surrounding fixed-column style** for `Name IS Resource` definitions, and tag every custom addition with a `; Acroloc` comment.
- **Resource naming suffixes:** `_I` input, `_O` output, `_M` memory bit, `_W` word, `_T` timer, `_SV` system variable, `_C` message constant.
- **Spec:** `docs/superpowers/specs/2026-06-29-spindle-changer-feedhold-design.md`. Line numbers below are from the current `main`/branch state; if an earlier task shifts them, re-locate by the quoted text, not the number.

---

### Task 1: Correct the misleading INP26 definition comment

**Files:**
- Modify: `Centroid-Acroloc-ALLIN1DC.src:228`

**Interfaces:**
- Consumes: nothing.
- Produces: nothing (comment-only). Establishes the correct documented polarity that the rest of the work relies on: INP26 TRUE = clear/safe, FALSE = in changer.

- [ ] **Step 1: Make the edit**

Replace the comment on the `ATC_Z_ClearedToolChanger_I` definition.

Old line (228):
```
ATC_Z_ClearedToolChanger_I      IS INP26 ; Acroloc the spindle has entered the tool changer (zero rpm)
```
New line:
```
ATC_Z_ClearedToolChanger_I      IS INP26 ; Acroloc TRUE = Z clear of tool changer (spindle may run); FALSE = spindle in changer (danger)
```

- [ ] **Step 2: Verify the edit landed**

Run: `grep -n "ATC_Z_ClearedToolChanger_I      IS INP26" Centroid-Acroloc-ALLIN1DC.src`
Expected: one line, ending `... FALSE = spindle in changer (danger)`. The old text `the spindle has entered the tool changer (zero rpm)` must be gone:
Run: `grep -c "has entered the tool changer (zero rpm)" Centroid-Acroloc-ALLIN1DC.src`
Expected: `0`

- [ ] **Step 3: Commit**

```bash
git add Centroid-Acroloc-ALLIN1DC.src
git commit -m "fix(plc): correct misleading INP26 (ATC_Z_ClearedToolChanger_I) comment

TRUE = Z clear of changer (spindle may run); FALSE = spindle in changer.
The prior comment implied the opposite of the actual signal polarity.

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

### Task 2: Add the two new memory-bit definitions

**Files:**
- Modify: `Centroid-Acroloc-ALLIN1DC.src` — in the "Tool changer position state tracking" group (after line 711)

**Interfaces:**
- Consumes: nothing.
- Produces: `ChangerHoldActive_M` (MEM448) and `ChangerHoldDone_M` (MEM449) — the latch bits Task 3's logic uses. (MEM448/MEM449 verified unused in the current source.)

- [ ] **Step 1: Make the edit**

Insert two definitions immediately after the `ToolSelected_M` line. Keep the `IS` column aligned with the surrounding lines and tag `; Acroloc`.

Old (lines 710–711):
```
InToolSelect_M                IS MEM443 ; Acroloc 0=false, 1=true
ToolSelected_M                IS MEM444 ; Acroloc 0=false, 1=true
```
New:
```
InToolSelect_M                IS MEM443 ; Acroloc 0=false, 1=true
ToolSelected_M                IS MEM444 ; Acroloc 0=false, 1=true
ChangerHoldActive_M           IS MEM448 ; Acroloc feed-hold active while spindle stops in changer zone
ChangerHoldDone_M             IS MEM449 ; Acroloc once-per-entry latch, cleared when Z clears changer
```

- [ ] **Step 2: Verify the edit landed**

Run: `grep -nE "Changer(HoldActive|HoldDone)_M\s+IS MEM44[89]" Centroid-Acroloc-ALLIN1DC.src`
Expected: two lines — `ChangerHoldActive_M ... IS MEM448` and `ChangerHoldDone_M ... IS MEM449`.

Confirm no accidental duplicate resource use:
Run: `grep -cE "IS MEM448\b" Centroid-Acroloc-ALLIN1DC.src; grep -cE "IS MEM449\b" Centroid-Acroloc-ALLIN1DC.src`
Expected: `1` and `1`.

- [ ] **Step 3: Commit**

```bash
git add Centroid-Acroloc-ALLIN1DC.src
git commit -m "feat(plc): define ChangerHoldActive_M / ChangerHoldDone_M (MEM448/449)

Latch bits for the spindle-in-changer feed-hold interlock.

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

### Task 3: Replace the M6-only stop block with the unified interlock (and rename the timer)

This task is **atomic** — the three edits must ship together so the source still compiles and the machine is never left without changer spindle protection. Do all edits, then verify, then a single commit.

**Files:**
- Modify: `Centroid-Acroloc-ALLIN1DC.src:1180` (timer definition rename)
- Modify: `Centroid-Acroloc-ALLIN1DC.src:1266` (InitialStage preset rename)
- Modify: `Centroid-Acroloc-ALLIN1DC.src:2866-2887` (remove M6 stop block, insert unified interlock)

**Interfaces:**
- Consumes: `ChangerHoldActive_M`, `ChangerHoldDone_M` (Task 2); existing `ATC_Z_ClearedToolChanger_I` (INP26), `SpindleEnableOut_O` (OUT7), `ActivateFeedHold_M` (MEM45), `ZeroSpeed_I` (INP12), `DoCycleStart_SV` (SV_PLC_FUNCTION_2), `FaultMsg_W`, `SPINDLE_FAULT_MSG_C`, `ShowFaultStage`, `OtherFault_M`, `SV_PROGRAM_RUNNING`, `SV_MDI_MODE`.
- Produces: `ChangerStopTimer_T` (T23, renamed from `StopSpinBeforeATC_T`) and the live interlock. Removes the symbol `StopSpinBeforeATC_T` from the codebase entirely.

- [ ] **Step 1: Rename the timer definition (line 1180)**

Old:
```
StopSpinBeforeATC_T             IS T23
```
New:
```
ChangerStopTimer_T              IS T23 ; Acroloc spindle stop dwell / timeout for changer-entry hold
```

- [ ] **Step 2: Rename the InitialStage preset (line 1266)**

This line is one entry in a comma-separated `InitialStage` assignment block — preserve the leading indentation and trailing comma.

Old:
```
             StopSpinBeforeATC_T = 5000,
```
New:
```
             ChangerStopTimer_T = 5000,
```

- [ ] **Step 3: Remove the old M6 stop block and insert the unified interlock (lines 2866–2887)**

Delete this entire block:
```
; Acroloc Make sure spindle stops before entering tool changer
; Enhanced spindle stop logic with speed monitoring and timeout protection

; Start spindle stop sequence when ATC is requested and spindle is not cleared
IF M6_SV && !ATC_Z_ClearedToolChanger_I && !ZeroSpeed_I THEN
  RST SpindleEnableOut_O,
  SET StopSpinBeforeATC_T

; Monitor spindle stop with timeout protection (5 seconds)
IF StopSpinBeforeATC_T && !ZeroSpeed_I THEN
  ; Spindle still running - continue waiting
  IF StopSpinBeforeATC_T == 0 THEN
    ; Timeout reached - spindle failed to stop
    FaultMsg_W = SPINDLE_FAULT_MSG_C,
    SET ShowFaultStage,
    SET OtherFault_M,
    RST ATCStage,
    RST StopSpinBeforeATC_T

; Spindle has stopped successfully - clear timer and allow ATC to proceed
IF StopSpinBeforeATC_T && ZeroSpeed_I THEN
  RST StopSpinBeforeATC_T
```

Replace it with the unified interlock:
```
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
; Also clear the once-per-entry latch: if a run is stopped/canceled with Z still
; in the zone, the next run must RE-ARM the hold (an operator could manually spin
; the spindle while stopped, since the zone-kill above is gated to a run). Without
; this, ChangerHoldDone_M would stay latched and motion could resume into the zone
; with the spindle still coasting.
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

Note: the `ChangeToTool_W = SV_TOOL_NUMBER, SET ATCStage` kickoff (around line 2853) and the manual-unlock logic just above the removed block are **not** touched — only the spindle-stop block from `; Acroloc Make sure spindle stops...` through the final `RST StopSpinBeforeATC_T` is removed.

- [ ] **Step 4: Verify the old symbol is gone everywhere**

Run: `grep -n "StopSpinBeforeATC_T" Centroid-Acroloc-ALLIN1DC.src`
Expected: **no output** (definition renamed, preset renamed, all M6-block uses deleted).

- [ ] **Step 5: Verify the rename and new logic are present**

Run: `grep -n "ChangerStopTimer_T" Centroid-Acroloc-ALLIN1DC.src`
Expected: the `IS T23` definition, the `= 5000` InitialStage preset, plus the Option-A uses (`= 3000`, `SET`, two `== 0` tests, and `RST` lines). At least 6 lines.

Run: `grep -n "M6_SV && !ATC_Z_ClearedToolChanger_I" Centroid-Acroloc-ALLIN1DC.src`
Expected: **no output** (old M6 stop trigger removed).

Run: `grep -n "Spindle-in-changer feed-hold interlock" Centroid-Acroloc-ALLIN1DC.src`
Expected: one line (the new block header).

- [ ] **Step 6: Verify the active vs. commented option state**

Confirm OPTION A is live (uncommented) and OPTION B is commented:
Run: `grep -n "ChangerStopTimer_T = 3000" Centroid-Acroloc-ALLIN1DC.src`
Expected: one line, **not** starting with `;`.
Run: `grep -n "ChangerStopTimer_T = 5000" Centroid-Acroloc-ALLIN1DC.src`
Expected: two lines — the InitialStage preset (not commented) and the OPTION B arm (commented, starts with `;`).

- [ ] **Step 7: Confirm no dangling references to undefined symbols**

Sanity-check every symbol the new block consumes is defined in the file:
Run: `for s in ChangerHoldActive_M ChangerHoldDone_M ChangerStopTimer_T ActivateFeedHold_M ZeroSpeed_I DoCycleStart_SV FaultMsg_W SPINDLE_FAULT_MSG_C ShowFaultStage OtherFault_M SpindleEnableOut_O ATC_Z_ClearedToolChanger_I; do printf '%s: ' "$s"; grep -cE "\b$s\b\s+IS |^$s |\b$s\s+IS " Centroid-Acroloc-ALLIN1DC.src; done`
Expected: every symbol prints a count `>= 1` (each has a definition). If any prints `0`, stop and re-check the definition section before committing.

- [ ] **Step 8: Commit**

```bash
git add Centroid-Acroloc-ALLIN1DC.src
git commit -m "feat(plc): unified spindle-in-changer feed-hold interlock

Replace the M6-only spindle-stop block with one rule that fires on any
program/MDI move into the changer (INP26 FALSE): feed hold, stop spindle,
3 s dwell then confirm-or-fault on ZeroSpeed_I (Option A; Option B waits on
the signal, commented), auto-resume on stop, spindle restarts at commanded
speed once Z clears. Rename StopSpinBeforeATC_T (T23) -> ChangerStopTimer_T.
ATCStage's own zero-speed carousel guard is retained.

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

## Final validation (on the Windows control PC — cannot be done in this repo)

These steps require CNC12 and the machine/simulator; they are the real test of the change. Record results when run on the control PC.

- [ ] **Compile** the `.src` in CNC12's PLC compiler. Expected: no new errors; `plc.map` regenerates. Confirm the symbols `ChangerStopTimer_T`, `ChangerHoldActive_M`, `ChangerHoldDone_M` appear and `StopSpinBeforeATC_T` does not.
- [ ] **MDI move into the zone, spindle running:** MDI a Z move that crosses into the changer with the spindle on. Expected: feed holds, spindle stops, ~3 s dwell, motion auto-resumes, and the spindle restarts at its commanded RPM after Z clears (INP26 TRUE).
- [ ] **Stuck-spindle fault:** force `ZeroSpeed_I` to stay false (e.g., bench/sim) and repeat. Expected: after the dwell, `SPINDLE_FAULT_MSG_C` is displayed, motion stays held, and there is no auto-resume.
- [ ] **M6 regression:** run a tool change. Expected: spindle stops, carousel indexes, change completes; `ATCStage`'s `!ZeroSpeed_I` guard still aborts if the spindle is spinning at carousel entry.
- [ ] **M5-before-zone:** run a program that issues `M5` then moves Z through the zone. Expected: spindle stays off after Z clears (does not auto-restart).
- [ ] **(Optional) Option B swap:** comment OPTION A's three `IF` blocks, uncomment OPTION B's, recompile, and confirm resume occurs on the `ZeroSpeed_I` signal rather than a fixed dwell.

---

## Plan self-review

- **Spec coverage:** INP26 comment fix → Task 1. New latch bits → Task 2. Single unified rule, general protection, feed hold, spindle stop, zone-gated kill, dwell/signal reach-zero, timeout→fault, auto-resume, speed-resume-on-clear, M6-block removal, timer rename, ATCStage guard retained → Task 3. On-machine checks → Final validation. All spec sections map to a task.
- **Placeholders:** none — every edit shows exact old/new text and exact verification commands.
- **Symbol consistency:** `ChangerStopTimer_T`, `ChangerHoldActive_M`, `ChangerHoldDone_M` are defined in Tasks 2–3 and used consistently in Task 3's block; `StopSpinBeforeATC_T` is fully removed (Step 4 asserts zero occurrences).
