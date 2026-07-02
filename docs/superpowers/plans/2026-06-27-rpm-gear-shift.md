# RPM-Based Automatic Gear Shifting — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make `Centroid-Acroloc-ALLIN1DC.src` automatically select and engage the two-speed transmission gear from the commanded spindle RPM, driving the previously-unused clutch outputs `Spindle_Low_gear_O` (OUT19) / `Spindle_High_gear_O` (OUT20).

**Architecture:** A range-decision block in `MainStage` (STG4) computes `DesiredRange_W` from the un-overridden S value (`GearBaseSpeed_FW` — `SV_PC_COMMANDED_SPINDLE_SPEED` with the spindle-override knob backed out, so the override never triggers a shift) vs a crossover machine parameter with hysteresis, and triggers a new `GearShiftStage` (STG17). `GearShiftStage` performs an open-loop clutch swap: release both clutches → coast in neutral for a fixed dwell (the DAC already re-commands the motor through the new gear's ratio, a passive motor-side speed match) → engage the target clutch. No speed feedback is read and there is no fault path (a dwell always elapses). The two clutch outputs are mutually exclusive at all times.

**Tech Stack:** Centroid CNC12 / MPU11 PLC stage language (`.src`). There is **no build/test tooling in this repo** — the `.src` is compiled by CNC12's PLC compiler on the Windows control PC, and behavior is validated on the machine/simulator.

## Verification model (read this first)

There is no offline compiler or test runner. For every task:
- **Automated gate (in this repo):** structural `grep` checks that the exact code is present, that the mutual-exclusion / open-loop invariants hold textually, and that no resource number is double-assigned.
- **Real gate (operator, off-repo):** the `.src` MUST compile with no errors in CNC12's PLC compiler, and the shift MUST be validated on the machine/simulator. Each task notes this; the implementer cannot perform it and must not claim it was done.

Treat "Run:" blocks below as the structural checks. Do not invent a test framework.

## Global Constraints

- Match the surrounding style: fixed-column `Name IS Resource` alignment; tag every new definition and logic line group with `; Acroloc`.
- Two ranges only are driven: **1 = low**, **4 = high** (reuse the existing `SpindleRange_W` → `SpinRangeAdjust_FW` mapping at the spindle block; do not touch the unused range-2/3 mapping lines).
- The two clutch outputs `Spindle_Low_gear_O` (OUT19) and `Spindle_High_gear_O` (OUT20) are **never energized simultaneously**.
- Open-loop: there is no gear-position input. Engaged gear is tracked in `EngagedRange_W` and reflected by the clutch output state. `SpinLowRange_I` (INP13) is no longer used for selection.
- Power-up default is **low** range.
- Crossover RPM **≤ 0 disables** auto-shift (hold current gear) — a freshly loaded, unconfigured PLC must not shift on its own.
- Fixed resource assignments (verified free against the current source on 2026-06-27): `GearShiftStage IS STG17`, `DesiredRange_W IS W73`, `EngagedRange_W IS W74`, `GearBaseSpeed_FW IS FW7`, `GearCoast_T IS T25`, `GearClutchSettle_T IS T26`, `GearCoastStarted_M IS MEM453`. Machine parameters: `SV_MACHINE_PARAMETER_941` crossover RPM, `_942` hysteresis RPM, `_943` reserved (was rev-match tolerance; unused), `_944` coast dwell ms (0 → default 1500), `_945` clutch-settle/lockout ms.
- Reuse the existing `SPINDLE_FAULT_MSG_C` message for shift faults (deviation from the spec's `GearShiftFault_C`: avoids needing an external CNC12 `plcmsg.txt` edit that can't be made or verified in this repo; a dedicated message can be added later).
- Branch: `feat/rpm-gear-shift`. Commit after each task.

---

## File Structure

Only one source file changes: `Centroid-Acroloc-ALLIN1DC.src`.

- **Definitions section (top):** new symbols (Task 1).
- **`InitialStage` (~line 1248):** power-up default gear (Task 2).
- **`MainStage` spindle-range block (~lines 2259-2260) + end of `MainStage` (~line 2344):** RPM decision, shift trigger, range tracking, mutual-exclusion interlock (Task 3).
- **New `GearShiftStage` block (inserted after `ATCStage`, ~line 2946):** the shift state machine (Task 4).

Documentation: `README.md` "Spindle speed & range" section is updated to reflect the now-implemented shift (Task 5).

---

## Task 1: Add gear-shift definitions

**Files:**
- Modify: `Centroid-Acroloc-ALLIN1DC.src` (definitions area: stages ~1199, words ~1079-1095, timers ~1181, memory ~ after 451)

**Interfaces:**
- Produces: `GearShiftStage` (STG17), `DesiredRange_W` (W73), `EngagedRange_W` (W74), `GearCoast_T` (T25), `GearClutchSettle_T` (T26), `GearCoastStarted_M` (MEM453), `GearSettleActive_M` (MEM454). Consumed by Tasks 2-4.

- [ ] **Step 1: Confirm the target resource numbers are still free**

Run:
```bash
# from the repo root
grep -nE "IS (STG17|W73|W74|T25|T26|MEM453|MEM454)\b" Centroid-Acroloc-ALLIN1DC.src || echo "all free"
```
Expected: `all free` (no existing definitions collide). If any collide, STOP and report.

- [ ] **Step 2: Add the stage definition after `ATCStage`**

Find the line `ATCStage                        IS STG16 ; Acroloc ATC Stage` and add immediately after it:
```
GearShiftStage                  IS STG17 ; Acroloc RPM gear-shift state machine
```

- [ ] **Step 3: Add the word definitions near `SpindleRange_W`**

Find `SpindleRange_W                  IS W64  ; 1 = low ... 4 = high` and add immediately after it:
```
DesiredRange_W                  IS W73  ; Acroloc gear wanted by RPM logic (1=low, 4=high)
EngagedRange_W                  IS W74  ; Acroloc gear currently engaged (open-loop, tracks clutch outputs)
```

Also find `SpinSpeedCommand_FW           IS FW6` (the float-word group) and add after it:
```
GearBaseSpeed_FW              IS FW7 ; Acroloc un-overridden commanded S (override knob backed out)
```

- [ ] **Step 4: Add the timer definitions after `ATCSpin_T`**

Find `ATCSpin_T                       IS T24 ; used to detect fault if unable to find position` and add immediately after it:
```
GearCoast_T                     IS T25 ; Acroloc gear-shift coast dwell (neutral) before engage
GearClutchSettle_T              IS T26 ; Acroloc post-engage clutch settle / re-shift lockout
```

- [ ] **Step 5: Add the memory-bit definitions**

Find the highest existing `IS MEM45x` definition (around `MEM451`) and add after the last one in that group:
```
GearCoastStarted_M              IS MEM453 ; Acroloc gear-shift coast dwell timer started flag
GearSettleActive_M              IS MEM454 ; Acroloc post-shift settle lockout active (held until GearClutchSettle_T expires)
```

- [ ] **Step 6: Add a parameter documentation comment near the gear definitions**

Immediately after the `EngagedRange_W` line added in Step 3, add this comment block:
```
; Acroloc gear-shift machine parameters (set in CNC12 machine parameters):
;   P941 = gear crossover RPM (commanded speed at/above which high gear is used; 0 disables auto-shift)
;   P942 = crossover hysteresis (RPM) — deadband half-width to prevent hunting
;   P943 = reserved (was rev-match tolerance; no longer used)
;   P944 = coast dwell (ms) spent in neutral before engaging the new gear (0 -> default 1500)
;   P945 = clutch settle / re-shift lockout (ms; 0 -> default 500)
```

- [ ] **Step 7: Verify the definitions are present and unique**

Run:
```bash
grep -nE "GearShiftStage +IS STG17|DesiredRange_W +IS W73|EngagedRange_W +IS W74|GearCoast_T +IS T25|GearClutchSettle_T +IS T26|GearCoastStarted_M +IS MEM453|GearSettleActive_M +IS MEM454" Centroid-Acroloc-ALLIN1DC.src
# no duplicate resource assignment anywhere:
for r in STG17 W73 W74 T25 T26 MEM453 MEM454; do n=$(grep -cE "IS $r\b" Centroid-Acroloc-ALLIN1DC.src); echo "$r: $n"; done
```
Expected: all 7 definition lines print once; each resource count is exactly `1`.

- [ ] **Step 8: Commit**

```bash
git add Centroid-Acroloc-ALLIN1DC.src
git commit -m "feat(plc): add gear-shift symbol definitions"
```

**Operator gate:** none yet (definitions only); full compile is verified after Task 4.

---

## Task 2: Power-up default gear (low) in InitialStage

**Files:**
- Modify: `Centroid-Acroloc-ALLIN1DC.src` `InitialStage` block (~lines 1248-1267)

**Interfaces:**
- Consumes: `Spindle_Low_gear_O`, `Spindle_High_gear_O`, `EngagedRange_W`, `DesiredRange_W`, `SpindleRange_W`.
- Produces: deterministic boot state (low gear engaged, `EngagedRange_W = 1`).

- [ ] **Step 1: Add the default-gear actions into the InitialStage SET block**

In the `IF 1==1 THEN SET True_M, ...` block, find the line `StopSpinBeforeATC_T = 5000,` and add immediately after it (keeping the trailing comma chain intact — these are additional comma-separated actions before the final `RST InitialStage`):
```
             SET Spindle_Low_gear_O,   ; Acroloc power-up gear = LOW
             RST Spindle_High_gear_O,  ; Acroloc
             EngagedRange_W = 1,       ; Acroloc
             DesiredRange_W = 1,       ; Acroloc
             SpindleRange_W = 1,       ; Acroloc
             RST GearSettleActive_M,   ; Acroloc
```
(Every custom line inside stock code carries an `; Acroloc` tag per CLAUDE.md.)

- [ ] **Step 2: Verify the actions are inside InitialStage and the block still ends correctly**

Run:
```bash
sed -n '/^                          InitialStage/,/RST InitialStage/p' Centroid-Acroloc-ALLIN1DC.src | grep -nE "SET Spindle_Low_gear_O|RST Spindle_High_gear_O|EngagedRange_W = 1|DesiredRange_W = 1|SpindleRange_W = 1|RST GearSettleActive_M|RST InitialStage"
```
Expected: the six new actions appear, followed by `RST InitialStage` as the last line. Confirm every added action line ends with a comma except that `RST InitialStage` remains the terminator.

- [ ] **Step 3: Commit**

```bash
git add Centroid-Acroloc-ALLIN1DC.src
git commit -m "feat(plc): default to low gear on power-up"
```

**Operator gate:** verified together with Task 4 (compile + boot state shows low clutch energized).

---

## Task 3: RPM decision, shift trigger, range tracking, and mutual-exclusion interlock in MainStage

**Files:**
- Modify: `Centroid-Acroloc-ALLIN1DC.src` (replace the sense-switch selection at ~lines 2259-2260; add interlock near ~line 2344)

**Interfaces:**
- Consumes: `SV_PC_COMMANDED_SPINDLE_SPEED`, `SV_PLC_SPINDLE_KNOB`, `GearBaseSpeed_FW`, `SV_MACHINE_PARAMETER_941/942`, `DesiredRange_W`, `EngagedRange_W`, `SpindleRange_W`, `GearShiftStage`, `ATCStage`, `GearClutchSettle_T`, `GearSettleActive_M`, `Spindle_Low_gear_O`, `Spindle_High_gear_O`, `SPINDLE_FAULT_MSG_C`, `ShowFaultStage`, `OtherFault_M`.
- Produces: `DesiredRange_W` each scan; `SET GearShiftStage` trigger; `SpindleRange_W` tracking the engaged gear when not shifting; the both-clutch safety interlock. Consumed by Task 4 / the existing DAC math.

- [ ] **Step 1: Replace the sense-switch selection lines**

Find exactly these two lines (currently ~2259-2260):
```
IF True_M THEN SpindleRange_W = 4
IF SpinLowRange_I THEN SpindleRange_W = 1
```
Replace them with:
```
; Acroloc: RPM-based automatic gear selection (replaces the old INP13 sense-switch
; selection).  DesiredRange_W is held in the hysteresis deadband; P941<=0 disables.
;
; Decide from the UN-overridden S value: SV_PC_COMMANDED_SPINDLE_SPEED includes
; the spindle-override knob (SV_PLC_SPINDLE_KNOB, clamped 1-200 in the override
; section above), so back the knob out — otherwise sweeping the override across
; the crossover mid-cut would trigger a gear shift (a neutral drop under load).
IF True_M THEN GearBaseSpeed_FW = SV_PC_COMMANDED_SPINDLE_SPEED * 100.0 / SV_PLC_SPINDLE_KNOB

IF SV_MACHINE_PARAMETER_941 <= 0.0 THEN DesiredRange_W = EngagedRange_W
IF (SV_MACHINE_PARAMETER_941 > 0.0) &&
   (GearBaseSpeed_FW >= (SV_MACHINE_PARAMETER_941 + SV_MACHINE_PARAMETER_942))
  THEN DesiredRange_W = 4
IF (SV_MACHINE_PARAMETER_941 > 0.0) &&
   (GearBaseSpeed_FW <= (SV_MACHINE_PARAMETER_941 - SV_MACHINE_PARAMETER_942))
  THEN DesiredRange_W = 1

; While not shifting, the effective range tracks the actually-engaged clutch so the
; ratio/DAC math below always reflects reality.
IF !GearShiftStage THEN SpindleRange_W = EngagedRange_W

; Post-shift settle lockout: GearSettleActive_M is latched when a shift completes (in
; GearShiftStage) and held until the settle dwell GearClutchSettle_T expires. A bare
; timer is true once it reaches its set point, so this fires at expiry; clearing the
; timer too returns its elapsed count to 0 so it is reusable for the next shift.
IF GearSettleActive_M && GearClutchSettle_T THEN
  RST GearSettleActive_M,
  RST GearClutchSettle_T

; Kick off a shift when the desired gear differs from the engaged gear and we are not
; already shifting, not in a tool change, and not inside the post-shift settle lockout.
IF (DesiredRange_W != EngagedRange_W) && !GearShiftStage && !ATCStage && !GearSettleActive_M
  THEN SET GearShiftStage
```

- [ ] **Step 2: Add the mutual-exclusion interlock at the end of MainStage**

Find the line `IF True_M THEN SV_PLC_SPINDLE_SPEED = SpinSpeedCommand_FW` (~line 2347, the last line before the `JogKeysNormalStage` header). Add immediately after it:
```

; Acroloc: clutches are mutually exclusive — never allow both engaged.
; EngagedRange_W = 0 marks the gear state unknown (we forced neutral), so the
; next valid demand re-triggers a full shift instead of trusting a stale value.
IF Spindle_Low_gear_O && Spindle_High_gear_O THEN
  RST Spindle_Low_gear_O,
  RST Spindle_High_gear_O,
  EngagedRange_W = 0,
  FaultMsg_W = SPINDLE_FAULT_MSG_C,
  SET ShowFaultStage,
  SET OtherFault_M
```

- [ ] **Step 3: Verify the old selection lines are gone and the new logic is present**

Run:
```bash
# old sense-switch selection must be gone:
grep -nE "IF SpinLowRange_I THEN SpindleRange_W = 1" Centroid-Acroloc-ALLIN1DC.src && echo "STILL PRESENT (bad)" || echo "removed (good)"
# new decision + trigger + interlock present:
grep -nE "RPM-based automatic gear selection|SET GearShiftStage|IF !GearShiftStage THEN SpindleRange_W = EngagedRange_W|clutches are mutually exclusive" Centroid-Acroloc-ALLIN1DC.src
```
Expected: `removed (good)`, and all four new markers print.

- [ ] **Step 4: Verify the trigger is correctly guarded**

Run:
```bash
grep -nE "DesiredRange_W != EngagedRange_W.*!GearShiftStage.*!ATCStage.*!GearSettleActive_M" Centroid-Acroloc-ALLIN1DC.src
```
Expected: one line — the trigger includes all three guards (not already shifting, not in ATC, not in settle lockout).

- [ ] **Step 5: Commit**

```bash
git add Centroid-Acroloc-ALLIN1DC.src
git commit -m "feat(plc): RPM gear decision, shift trigger, and clutch interlock"
```

**Operator gate:** verified with Task 4.

---

## Task 4: GearShiftStage state machine

**Files:**
- Modify: `Centroid-Acroloc-ALLIN1DC.src` (insert a new stage block after `ATCStage`, before `SafetySwitchInterruptStage` ~line 2947)

**Interfaces:**
- Consumes: `GearShiftStage`, `DesiredRange_W`, `EngagedRange_W`, `SpindleRange_W`, `Spindle_Low_gear_O`, `Spindle_High_gear_O`, `SV_MACHINE_PARAMETER_944/945`, `GearCoast_T`, `GearClutchSettle_T`, `GearCoastStarted_M`.
- Produces: `SET GearSettleActive_M` on shift completion (held until `GearClutchSettle_T` expires, then both cleared in MainStage).
- Produces: the completed shift (engaged clutch + `EngagedRange_W` updated). There is no fault path — a dwell always elapses.

- [ ] **Step 1: Insert the GearShiftStage block**

Find the `ATCStage` block's final action line (the one ending `RST ATCStage` inside `IF CarouselToolID_W == ChangeToTool_W THEN ...`, ~line 2945). After that block and before the `SafetySwitchInterruptStage` header (`;====` ... `SafetySwitchInterruptStage`), insert:
```

;=============================================================================
   GearShiftStage ; Acroloc
;=============================================================================
; Open-loop two-clutch gear shift driven by DesiredRange_W (1=low, 4=high).
; Sequence: release BOTH clutches (neutral) -> coast for a fixed dwell -> engage
; the target clutch.  No exact rev-match is required: during the coast the DAC
; already commands the motor through the NEW gear's ratio (Step A retargets
; SpindleRange_W), so the motor side arrives near the right speed passively while
; the spindle side coasts.  The two clutches are never engaged together.  There
; is no gear-position or speed feedback in this sequence (open loop); the coast
; dwell + settle lockout are the only assurances.  There is no fault path — a
; dwell always elapses, so a shift always completes.

; --- Step A: neutral + retarget the motor (every scan while shifting) ---
IF GearShiftStage THEN
  RST Spindle_Low_gear_O,
  RST Spindle_High_gear_O,
  SpindleRange_W = DesiredRange_W

; --- Step B: start the coast dwell once on entry ---
IF GearShiftStage && !GearCoastStarted_M THEN GearCoast_T = 1500
IF GearShiftStage && !GearCoastStarted_M && (SV_MACHINE_PARAMETER_944 > 0) THEN
  GearCoast_T = SV_MACHINE_PARAMETER_944
IF GearShiftStage && !GearCoastStarted_M THEN
  SET GearCoast_T,
  SET GearCoastStarted_M

; --- Step C: choose the settle/lockout dwell value (before starting the timer) ---
; A bare timer is true once it reaches its set point, so GearCoast_T below fires
; when the coast dwell has fully elapsed (NOT == 0, which would mean "just armed").
IF GearShiftStage && GearCoastStarted_M && GearCoast_T THEN GearClutchSettle_T = 500
IF GearShiftStage && GearCoastStarted_M && GearCoast_T && (SV_MACHINE_PARAMETER_945 > 0) THEN
  GearClutchSettle_T = SV_MACHINE_PARAMETER_945

; --- Step D: coast elapsed -> engage exactly one clutch, then finish the shift ---
IF GearShiftStage && GearCoastStarted_M && GearCoast_T && (DesiredRange_W == 1) THEN
  SET Spindle_Low_gear_O,
  RST Spindle_High_gear_O
IF GearShiftStage && GearCoastStarted_M && GearCoast_T && (DesiredRange_W == 4) THEN
  SET Spindle_High_gear_O,
  RST Spindle_Low_gear_O
IF GearShiftStage && GearCoastStarted_M && GearCoast_T THEN
  EngagedRange_W = DesiredRange_W,
  SET GearClutchSettle_T,
  SET GearSettleActive_M,
  RST GearCoastStarted_M,
  RST GearCoast_T,
  RST GearShiftStage
```

- [ ] **Step 2: Verify the stage block is present, ordered, and self-consistent**

Run:
```bash
# header present and placed before SafetySwitchInterruptStage:
grep -nE "GearShiftStage ; Acroloc|SafetySwitchInterruptStage" Centroid-Acroloc-ALLIN1DC.src | head
# all four phases present:
grep -nE "Step A: neutral|Step B: start the coast dwell|Step C: choose the settle|Step D: coast elapsed" Centroid-Acroloc-ALLIN1DC.src
```
Expected: the `GearShiftStage ; Acroloc` header line number is **less** than the `SafetySwitchInterruptStage` line number; all four phase markers print.

- [ ] **Step 3: Verify the never-both-engaged invariant textually**

Run:
```bash
# every line that SETs one clutch must RST the other in the same action group:
grep -nE "SET Spindle_(Low|High)_gear_O" Centroid-Acroloc-ALLIN1DC.src
```
Expected: in `GearShiftStage` Step D, `SET Spindle_Low_gear_O` is paired with `RST Spindle_High_gear_O` and vice versa; the only unpaired `SET Spindle_Low_gear_O` is in `InitialStage` (where `RST Spindle_High_gear_O` immediately follows). Confirm by eye there is no `SET` of one clutch without an adjacent `RST` of the other.

- [ ] **Step 4: Commit**

```bash
git add Centroid-Acroloc-ALLIN1DC.src
git commit -m "feat(plc): add GearShiftStage open-loop clutch shift state machine"
```

- [ ] **Step 5: Operator compile gate (MUST be done before merge)**

This cannot be done in-repo. Hand off to the operator with these instructions and record the result in the PR:
1. Load `Centroid-Acroloc-ALLIN1DC.src` in CNC12's PLC compiler (`cncm` / PLC Detective) on the control PC.
2. Confirm it **compiles with no errors** and emits an updated `plc.map`.
3. On the machine/simulator, set `P941` (crossover), `P942` (hysteresis), `P944` (coast dwell ms), `P945` (settle ms) and verify: commanding S below/above the crossover engages exactly one clutch; a crossing S triggers neutral→coast→engage; both outputs are never on together; power-up leaves the low clutch engaged.
4. **Tune the coast dwell (P944):** shift under load and at various speeds; lengthen the dwell if engagement is rough (the spindle side needs longer to coast toward the motor side), shorten it if shifts feel needlessly slow. Start at the 1500 ms default. Report findings on the PR.

---

## Task 5: Update README to reflect the implemented shift

**Files:**
- Modify: `README.md` ("Spindle speed & range (transmission) shifting" section, specifically the "⚠️ Not yet implemented: commanding the shift" subsection)

**Interfaces:**
- Consumes: nothing in code. Produces: accurate docs.

- [ ] **Step 1: Replace the "Not yet implemented" subsection**

Find the subsection beginning `### ⚠️ Not yet implemented: commanding the shift` and replace that subsection's body (down to, but not including, the next `##`/`###` heading) with:
```
### Automatic RPM-based gear shifting

The PLC now **commands** the two-speed transmission automatically from the commanded
spindle RPM (it no longer relies on the `SpinLowRange_I`/INP13 lever sense for selection).

- `MainStage` computes `DesiredRange_W` from the **un-overridden S value**
  (`GearBaseSpeed_FW` = `SV_PC_COMMANDED_SPINDLE_SPEED` with the spindle-override knob
  backed out) versus a crossover machine parameter with a hysteresis deadband
  (Parameter 941 crossover RPM, 942 hysteresis; 941 ≤ 0 disables auto-shift). Sweeping
  the override knob never triggers a shift.
- When the desired gear differs from the engaged gear, `GearShiftStage` (STG17) performs an
  **open-loop clutch swap**: release both clutches (`Spindle_Low_gear_O`/OUT19,
  `Spindle_High_gear_O`/OUT20), **coast in neutral for a fixed dwell** (Parameter 944 ms;
  0 → default 1500), then engage the target clutch. No exact rev-match is required — during
  the coast the DAC already commands the motor through the new gear's ratio, so the motor
  side arrives near the right speed passively. There is **no fault path**: a dwell always
  elapses, so a shift always completes.
- The two clutch outputs are **mutually exclusive** (a safety interlock forces neutral if
  both are ever energized, and marks the gear unknown so the next demand re-shifts).
  Power-up engages **low** range.

> **Open-loop caveat:** there is no gear-position or speed feedback in the shift sequence;
> the engaged gear is tracked in `EngagedRange_W` from the clutch-output state, and the
> coast dwell + clutch-settle lockout (Parameter 945) are the only confirmation that a
> shift completed.
```

- [ ] **Step 2: Verify the stale text is gone and the new text is present**

Run:
```bash
grep -nE "Not yet implemented: commanding the shift" README.md && echo "STALE (bad)" || echo "updated (good)"
grep -nE "Automatic RPM-based gear shifting|mutually exclusive|Open-loop caveat" README.md
```
Expected: `updated (good)` and the three new markers print.

- [ ] **Step 3: Commit**

```bash
git add README.md
git commit -m "docs: README — document implemented RPM gear shifting"
```

---

## Self-Review (completed by plan author)

- **Spec coverage:** RPM decision + hysteresis (Task 3); neutral→coast-dwell→engage sequence (Task 4); mutual-exclusion interlock with `EngagedRange_W = 0` on fault (Task 3 + verified Task 4); open-loop tracking via `EngagedRange_W`/output state (Tasks 2-4); parameter-driven crossover/hysteresis/dwells (Tasks 1,3,4); low-range power-up default (Task 2); ATC inhibit (Task 3 trigger guard); coast-dwell tuning (Task 4 operator gate); docs (Task 5). All spec success criteria map to a task. ✓
- **Deviation (documented):** spec's `GearShiftFault_C` is replaced by reusing `SPINDLE_FAULT_MSG_C` to avoid an unverifiable external `plcmsg.txt` edit — noted in Global Constraints. ✓
- **Design revision (owner decision):** the original rev-match gate (measured-vs-commanded tolerance + timeout fault, P943/P944, `GearRevMatched_M`/MEM452) was replaced by the fixed coast dwell — no speed feedback, no fault path; see the spec's "Why a fixed coast dwell" section. MEM452 and P943 are now unused/reserved. ✓
- **Placeholder scan:** no TBD/TODO; every code step shows the exact lines. ✓
- **Name/resource consistency:** symbol names and resource numbers (STG17, W73/74, T25/26, MEM453/454, P941/942/944/945) are identical across Tasks 1-4; no double assignment (Task 1 Step 7 enforces). ✓
