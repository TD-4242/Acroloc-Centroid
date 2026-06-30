# RPM-Based Automatic Gear Shifting — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make `Centroid-Acroloc-ALLIN1DC.src` automatically select and engage the two-speed transmission gear from the commanded spindle RPM, driving the previously-unused clutch outputs `Spindle_Low_gear_O` (OUT19) / `Spindle_High_gear_O` (OUT20).

**Architecture:** A range-decision block in `MainStage` (STG4) computes `DesiredRange_W` from `SV_PC_COMMANDED_SPINDLE_SPEED` vs a crossover machine parameter with hysteresis, and triggers a new `GearShiftStage` (STG17). `GearShiftStage` performs an open-loop, on-the-fly clutch swap: release both clutches → command the new gear so the motor rev-matches → when `SV_MEASURED_SPINDLE_SPEED` is within tolerance of the commanded speed, engage the target clutch. The two clutch outputs are mutually exclusive at all times.

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
- Fixed resource assignments (verified free against the current source on 2026-06-27): `GearShiftStage IS STG17`, `DesiredRange_W IS W73`, `EngagedRange_W IS W74`, `GearRevMatch_T IS T25`, `GearClutchSettle_T IS T26`, `GearRevMatched_M IS MEM452`, `GearRevMatchStarted_M IS MEM453`. Machine parameters: `SV_MACHINE_PARAMETER_941` crossover RPM, `_942` hysteresis RPM, `_943` rev-match tolerance RPM, `_944` rev-match timeout ms, `_945` clutch-settle/lockout ms.
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
- Produces: `GearShiftStage` (STG17), `DesiredRange_W` (W73), `EngagedRange_W` (W74), `GearRevMatch_T` (T25), `GearClutchSettle_T` (T26), `GearRevMatched_M` (MEM452), `GearRevMatchStarted_M` (MEM453). Consumed by Tasks 2-4.

- [ ] **Step 1: Confirm the target resource numbers are still free**

Run:
```bash
# from the repo root
grep -nE "IS (STG17|W73|W74|T25|T26|MEM452|MEM453)\b" Centroid-Acroloc-ALLIN1DC.src || echo "all free"
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

- [ ] **Step 4: Add the timer definitions after `ATCSpin_T`**

Find `ATCSpin_T                       IS T24 ; used to detect fault if unable to find position` and add immediately after it:
```
GearRevMatch_T                  IS T25 ; Acroloc rev-match wait timeout
GearClutchSettle_T              IS T26 ; Acroloc post-engage clutch settle / re-shift lockout
```

- [ ] **Step 5: Add the memory-bit definitions**

Find the highest existing `IS MEM45x` definition (around `MEM451`) and add after the last one in that group:
```
GearRevMatched_M                IS MEM452 ; Acroloc rev-match achieved flag
GearRevMatchStarted_M           IS MEM453 ; Acroloc rev-match timer started flag
```

- [ ] **Step 6: Add a parameter documentation comment near the gear definitions**

Immediately after the `EngagedRange_W` line added in Step 3, add this comment block:
```
; Acroloc gear-shift machine parameters (set in CNC12 machine parameters):
;   P941 = gear crossover RPM (commanded speed at/above which high gear is used; 0 disables auto-shift)
;   P942 = crossover hysteresis (RPM) — deadband half-width to prevent hunting
;   P943 = rev-match speed tolerance (RPM) — |measured - commanded| allowed before engaging
;   P944 = rev-match timeout (ms; 0 -> default 3000)
;   P945 = clutch settle / re-shift lockout (ms; 0 -> default 500)
```

- [ ] **Step 7: Verify the definitions are present and unique**

Run:
```bash
grep -nE "GearShiftStage +IS STG17|DesiredRange_W +IS W73|EngagedRange_W +IS W74|GearRevMatch_T +IS T25|GearClutchSettle_T +IS T26|GearRevMatched_M +IS MEM452|GearRevMatchStarted_M +IS MEM453" Centroid-Acroloc-ALLIN1DC.src
# no duplicate resource assignment anywhere:
for r in STG17 W73 W74 T25 T26 MEM452 MEM453; do n=$(grep -cE "IS $r\b" Centroid-Acroloc-ALLIN1DC.src); echo "$r: $n"; done
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
             SET Spindle_Low_gear_O,
             RST Spindle_High_gear_O,
             EngagedRange_W = 1,
             DesiredRange_W = 1,
             SpindleRange_W = 1,
```

- [ ] **Step 2: Verify the actions are inside InitialStage and the block still ends correctly**

Run:
```bash
sed -n '/^                          InitialStage/,/RST InitialStage/p' Centroid-Acroloc-ALLIN1DC.src | grep -nE "SET Spindle_Low_gear_O|RST Spindle_High_gear_O|EngagedRange_W = 1|DesiredRange_W = 1|SpindleRange_W = 1|RST InitialStage"
```
Expected: the five new actions appear, followed by `RST InitialStage` as the last line. Confirm every added action line ends with a comma except that `RST InitialStage` remains the terminator.

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
- Consumes: `SV_PC_COMMANDED_SPINDLE_SPEED`, `SV_MACHINE_PARAMETER_941/942`, `DesiredRange_W`, `EngagedRange_W`, `SpindleRange_W`, `GearShiftStage`, `ATCStage`, `GearClutchSettle_T`, `Spindle_Low_gear_O`, `Spindle_High_gear_O`, `SPINDLE_FAULT_MSG_C`, `ShowFaultStage`, `OtherFault_M`.
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
IF SV_MACHINE_PARAMETER_941 <= 0.0 THEN DesiredRange_W = EngagedRange_W
IF (SV_MACHINE_PARAMETER_941 > 0.0) &&
   (SV_PC_COMMANDED_SPINDLE_SPEED >= (SV_MACHINE_PARAMETER_941 + SV_MACHINE_PARAMETER_942))
  THEN DesiredRange_W = 4
IF (SV_MACHINE_PARAMETER_941 > 0.0) &&
   (SV_PC_COMMANDED_SPINDLE_SPEED <= (SV_MACHINE_PARAMETER_941 - SV_MACHINE_PARAMETER_942))
  THEN DesiredRange_W = 1

; While not shifting, the effective range tracks the actually-engaged clutch so the
; ratio/DAC math below always reflects reality.
IF !GearShiftStage THEN SpindleRange_W = EngagedRange_W

; Kick off a shift when the desired gear differs from the engaged gear and we are not
; already shifting, not in a tool change, and not inside the post-shift settle lockout.
IF (DesiredRange_W != EngagedRange_W) && !GearShiftStage && !ATCStage && !GearClutchSettle_T
  THEN SET GearShiftStage
```

- [ ] **Step 2: Add the mutual-exclusion interlock at the end of MainStage**

Find the line `IF True_M THEN SV_PLC_SPINDLE_SPEED = SpinSpeedCommand_FW` (~line 2347, the last line before the `JogKeysNormalStage` header). Add immediately after it:
```

; Acroloc: clutches are mutually exclusive — never allow both engaged.
IF Spindle_Low_gear_O && Spindle_High_gear_O THEN
  RST Spindle_Low_gear_O,
  RST Spindle_High_gear_O,
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
grep -nE "DesiredRange_W != EngagedRange_W.*!GearShiftStage.*!ATCStage.*!GearClutchSettle_T" Centroid-Acroloc-ALLIN1DC.src
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
- Consumes: `GearShiftStage`, `DesiredRange_W`, `EngagedRange_W`, `SpindleRange_W`, `Spindle_Low_gear_O`, `Spindle_High_gear_O`, `SpindleEnableOut_O`, `SV_MEASURED_SPINDLE_SPEED`, `SV_PC_COMMANDED_SPINDLE_SPEED`, `SV_MACHINE_PARAMETER_943/944/945`, `GearRevMatch_T`, `GearClutchSettle_T`, `GearRevMatched_M`, `GearRevMatchStarted_M`, `SPINDLE_FAULT_MSG_C`, `ShowFaultStage`, `OtherFault_M`.
- Produces: the completed shift (engaged clutch + `EngagedRange_W` updated), or a clean timeout fault (neutral + spindle disabled).

- [ ] **Step 1: Insert the GearShiftStage block**

Find the `ATCStage` block's final action line (the one ending `RST ATCStage` inside `IF CarouselToolID_W == ChangeToTool_W THEN ...`, ~line 2945). After that block and before the `SafetySwitchInterruptStage` header (`;====` ... `SafetySwitchInterruptStage`), insert:
```

;=============================================================================
   GearShiftStage ; Acroloc
;=============================================================================
; Open-loop two-clutch gear shift driven by DesiredRange_W (1=low, 4=high).
; Sequence: release BOTH clutches (neutral) -> command the new gear so the motor
; rev-matches -> when measured spindle speed is within tolerance of the commanded
; speed, engage the target clutch.  The two clutches are never engaged together.
; There is no gear-position feedback (open loop); the rev-match + settle dwell are
; the only assurances.

; --- Step A: neutral + rev-match command (every scan while shifting) ---
IF GearShiftStage THEN
  RST Spindle_Low_gear_O,
  RST Spindle_High_gear_O,
  SpindleRange_W = DesiredRange_W

; --- Step B: start the rev-match timeout once on entry ---
IF GearShiftStage && !GearRevMatchStarted_M THEN GearRevMatch_T = 3000
IF GearShiftStage && !GearRevMatchStarted_M && (SV_MACHINE_PARAMETER_944 > 0) THEN
  GearRevMatch_T = SV_MACHINE_PARAMETER_944
IF GearShiftStage && !GearRevMatchStarted_M THEN
  SET GearRevMatch_T,
  SET GearRevMatchStarted_M

; --- Step C: detect rev-match (measured within tolerance of commanded) ---
IF GearShiftStage && GearRevMatchStarted_M &&
   (SV_MEASURED_SPINDLE_SPEED >= (SV_PC_COMMANDED_SPINDLE_SPEED - SV_MACHINE_PARAMETER_943)) &&
   (SV_MEASURED_SPINDLE_SPEED <= (SV_PC_COMMANDED_SPINDLE_SPEED + SV_MACHINE_PARAMETER_943))
  THEN SET GearRevMatched_M

; --- Step D: choose settle/lockout dwell value (before starting the timer) ---
IF GearShiftStage && GearRevMatched_M THEN GearClutchSettle_T = 500
IF GearShiftStage && GearRevMatched_M && (SV_MACHINE_PARAMETER_945 > 0) THEN
  GearClutchSettle_T = SV_MACHINE_PARAMETER_945

; --- Step E: engage exactly one clutch, then finish the shift ---
IF GearShiftStage && GearRevMatched_M && (DesiredRange_W == 1) THEN
  SET Spindle_Low_gear_O,
  RST Spindle_High_gear_O
IF GearShiftStage && GearRevMatched_M && (DesiredRange_W == 4) THEN
  SET Spindle_High_gear_O,
  RST Spindle_Low_gear_O
IF GearShiftStage && GearRevMatched_M THEN
  EngagedRange_W = DesiredRange_W,
  SET GearClutchSettle_T,
  RST GearRevMatched_M,
  RST GearRevMatchStarted_M,
  RST GearRevMatch_T,
  RST GearShiftStage

; --- Timeout: rev-match never achieved -> fault, hold neutral, drop spindle enable ---
IF GearShiftStage && GearRevMatchStarted_M && !GearRevMatched_M && (GearRevMatch_T == 0) THEN
  RST Spindle_Low_gear_O,
  RST Spindle_High_gear_O,
  RST SpindleEnableOut_O,
  FaultMsg_W = SPINDLE_FAULT_MSG_C,
  SET ShowFaultStage,
  SET OtherFault_M,
  RST GearRevMatchStarted_M,
  RST GearRevMatch_T,
  RST GearShiftStage
```

- [ ] **Step 2: Verify the stage block is present, ordered, and self-consistent**

Run:
```bash
# header present and placed before SafetySwitchInterruptStage:
grep -nE "GearShiftStage ; Acroloc|SafetySwitchInterruptStage" Centroid-Acroloc-ALLIN1DC.src | head
# all five phases present:
grep -nE "Step A: neutral|Step B: start the rev-match|Step C: detect rev-match|Step E: engage exactly one clutch|Timeout: rev-match never achieved" Centroid-Acroloc-ALLIN1DC.src
```
Expected: the `GearShiftStage ; Acroloc` header line number is **less** than the `SafetySwitchInterruptStage` line number; all five phase markers print.

- [ ] **Step 3: Verify the never-both-engaged invariant textually**

Run:
```bash
# every line that SETs one clutch must RST the other in the same action group:
grep -nE "SET Spindle_(Low|High)_gear_O" Centroid-Acroloc-ALLIN1DC.src
```
Expected: in `GearShiftStage` Step E, `SET Spindle_Low_gear_O` is paired with `RST Spindle_High_gear_O` and vice versa; the only unpaired `SET Spindle_Low_gear_O` is in `InitialStage` (where `RST Spindle_High_gear_O` immediately follows). Confirm by eye there is no `SET` of one clutch without an adjacent `RST` of the other.

- [ ] **Step 4: Commit**

```bash
git add Centroid-Acroloc-ALLIN1DC.src
git commit -m "feat(plc): add GearShiftStage open-loop clutch shift state machine"
```

- [ ] **Step 5: Operator compile gate (MUST be done before merge)**

This cannot be done in-repo. Hand off to the operator with these instructions and record the result in the PR:
1. Load `Centroid-Acroloc-ALLIN1DC.src` in CNC12's PLC compiler (`cncm` / PLC Detective) on the control PC.
2. Confirm it **compiles with no errors** and emits an updated `plc.map`.
3. On the machine/simulator, set `P941` (crossover), `P942` (hysteresis), `P943` (tolerance), `P944` (timeout ms), `P945` (settle ms) and verify: commanding S below/above the crossover engages exactly one clutch; a crossing S triggers neutral→rev-match→engage; both outputs are never on together; power-up leaves the low clutch engaged.
4. **Validate the rev-match assumption:** confirm `SV_MEASURED_SPINDLE_SPEED` tracks the motor through the neutral phase (it is documented to scale by the LOW/MID range flags the PLC sets). If it instead reads a coasting spindle and never converges, the shift will time out — switch Step C to a fixed dwell (engage after `GearRevMatch_T` regardless of measured speed). Report findings on the PR.

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

- `MainStage` computes `DesiredRange_W` from `SV_PC_COMMANDED_SPINDLE_SPEED` versus a
  crossover machine parameter with a hysteresis deadband (Parameter 941 crossover RPM,
  942 hysteresis; 941 ≤ 0 disables auto-shift).
- When the desired gear differs from the engaged gear, `GearShiftStage` (STG16-adjacent,
  STG17) performs an **open-loop, on-the-fly clutch swap**: release both clutches
  (`Spindle_Low_gear_O`/OUT19, `Spindle_High_gear_O`/OUT20), command the new gear so the
  motor rev-matches, and — when `SV_MEASURED_SPINDLE_SPEED` is within tolerance
  (Parameter 943) of the commanded speed — engage the target clutch. A rev-match timeout
  (Parameter 944) faults into neutral with the spindle disabled.
- The two clutch outputs are **mutually exclusive** (a safety interlock forces neutral if
  both are ever energized). Power-up engages **low** range.

> **Open-loop caveat:** there is no gear-position feedback; the engaged gear is tracked in
> `EngagedRange_W` from the clutch-output state, and the rev-match + clutch-settle dwell
> (Parameter 945) are the only confirmation that a shift completed.
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

- **Spec coverage:** RPM decision + hysteresis (Task 3); on-the-fly neutral→rev-match→engage sequence (Task 4); mutual-exclusion interlock (Task 3 + verified Task 4); open-loop tracking via `EngagedRange_W`/output state (Tasks 2-4); parameter-driven crossover/tolerance/timeouts (Tasks 1,3,4); low-range power-up default (Task 2); ATC inhibit (Task 3 trigger guard); rev-match timeout → neutral + disable + fault (Task 4); the speed-feedback risk + fixed-dwell fallback (Task 4 operator gate); docs (Task 5). All spec success criteria map to a task. ✓
- **Deviation (documented):** spec's `GearShiftFault_C` is replaced by reusing `SPINDLE_FAULT_MSG_C` to avoid an unverifiable external `plcmsg.txt` edit — noted in Global Constraints. ✓
- **Placeholder scan:** no TBD/TODO; every code step shows the exact lines. ✓
- **Name/resource consistency:** symbol names and resource numbers (STG17, W73/74, T25/26, MEM452/453, P941-945) are identical across Tasks 1-4; no double assignment (Task 1 Step 7 enforces). ✓
