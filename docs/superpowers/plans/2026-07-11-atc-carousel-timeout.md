# ATC Carousel Search Timeout Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Bound the ATC carousel search with a 20 s watchdog so a jam, broken position switch, or invalid tool number faults ("CAROUSEL MOVE TIME OUT") and stops/relocks the carousel instead of spinning forever.

**Architecture:** Arm the already-defined `ATCSpin_T` (T24) off the `M6_SV` rising edge in `MainStage` (fires once per change, no new memory bit); add a timeout-fault rung in `ATCStage` after the match rung; disarm the timer on every `ATCStage` exit. Two new constants; message 63 already exists in `plcmsg.txt`.

**Tech Stack:** Centroid CNC12 / MPU11 PLC stage language (`Centroid-Acroloc-ALLIN1DC.src`). Only in-repo verification is `./compile.sh` (MPUCOMP via wine) — syntax/lint only. Real behavior is validated on the machine by the owner (off-repo); the implementer cannot do it and must not claim it was done.

**Design spec:** `docs/superpowers/specs/2026-07-11-atc-carousel-timeout-design.md`

> **Historical note:** this plan was executed as written; its before/after code anchors show
> the file state **at execution time**. Two *later, separate* commits on the same
> `post-release-fixes` branch then corrected `ATC_Lock_Released_C` (`45546 -> 44546`) and
> removed the `; DEBUG` tracing — so the `45546` value and the `SPINDLE_IN_CHANGER_DBG_C`
> anchor shown in Steps 2/8 no longer exist in the final source. Do not reintroduce them; the
> "out of scope" note below was accurate for this task only.

## Global Constraints

- **ASCII only** for `.src` — no em dashes/smart quotes/non-ASCII.
- **`.src` is CRLF.** The Edit tool inserts LF; after editing, run `sed -i 's/\r*$/\r/' Centroid-Acroloc-ALLIN1DC.src` and confirm `git diff` shows content-only changes.
- **Tag custom code `; Acroloc`.** Match the surrounding fixed-column style (constant `IS` column at 33).
- **Compile gate:** `./compile.sh` -> `Compilation successful`, **0 errors**. Baseline: 4799 tokens, 195 warnings. Expect tokens up slightly (added rungs) and warnings <= 195 (arming `ATCSpin_T` may clear an unused-resource warning); investigate any *new* warning.
- **Doc line-number pins:** `docs/plc-spec/` files anchor `src:` refs to a pinned commit and are **not** re-baselined per edit. Fix now-false content only; do not chase drifted line numbers.
- **Commit only when asked** — each task ends with a commit step, but confirm before committing if not pre-authorized.
- **Out of scope:** the adjacent `ATC_Lock_Released_C` value typo (backlog item) — do not fold it in unless separately asked.

---

### Task 1: Carousel search timeout (PLC source)

**Files:**
- Modify: `Centroid-Acroloc-ALLIN1DC.src` — ATC message constants (~src:210), `MainStage` M6 kickoff (src:2854), `ATCStage` (src:2924-2985).

**Interfaces:**
- Consumes (existing): `M6_SV`, `ATCStage` (STG16), `ATCSpin_T` (T24), `ShowFaultStage`, `OtherFault_M`, `ATCMotor_O`, `ATCUnlocked_O`, `ChangeToTool_W`, `FaultMsg_W`.
- Produces: `ATCSpin_T` armed at kickoff and read as the timeout; two new constants `CAROUSEL_TIMEOUT_MSG_C`, `ATC_SPIN_TIMEOUT_MS_C`.

- [ ] **Step 1: Confirm clean baseline.**

Run: `./compile.sh`
Expected: `Compilation successful`, `Program size: 4799 tokens`, `Warnings: 195`.

- [ ] **Step 2: Add the two constants** in the ATC message block. Replace:

```
ATC_Lock_Released_C             IS 45546;(2+256*174) Tool Carousel locked.
SPINDLE_IN_CHANGER_DBG_C        IS 44802;(2+256*175) DEBUG spindle in changer zone
```

with:

```
ATC_Lock_Released_C             IS 45546;(2+256*174) Tool Carousel locked.
CAROUSEL_TIMEOUT_MSG_C          IS 16130 ;(2+256*63) CAROUSEL MOVE TIME OUT
ATC_SPIN_TIMEOUT_MS_C           IS 20000 ; Acroloc carousel search timeout (ms)
SPINDLE_IN_CHANGER_DBG_C        IS 44802;(2+256*175) DEBUG spindle in changer zone
```

- [ ] **Step 3: Arm the watchdog at M6 kickoff** (MainStage). Replace:

```
IF M6_SV THEN ChangeToTool_W = SV_TOOL_NUMBER, SET ATCStage
```

with:

```
; Acroloc: arm the carousel search watchdog once, as the change kicks off.
; Runs before the SET ATCStage below, so !ATCStage is true only on the first
; scan of a change; it will not re-arm (reset) the timer on later scans.
IF M6_SV && !ATCStage THEN ATCSpin_T = ATC_SPIN_TIMEOUT_MS_C, SET ATCSpin_T
IF M6_SV THEN ChangeToTool_W = SV_TOOL_NUMBER, SET ATCStage
```

- [ ] **Step 4: Remove the resolved TODO.** Delete the line:

```
;TODO: add timer to error so carousol doesn't spin for ever if tool not found
```

- [ ] **Step 5: Disarm the timer on the `!ZeroSpeed_I` abort.** Replace:

```
IF ATCStage && !ZeroSpeed_I THEN
  FaultMsg_W = SPINDLE_FAULT_MSG_C,
  SET ShowFaultStage,
  SET OtherFault_M,
  RST ATCMotor_O,
  RST ATCUnlocked_O,
  RST M6_SV,
  ChangeToTool_W = 0,
  RST ATCStage
```

with (add `RST ATCSpin_T,` before `RST ATCStage`):

```
IF ATCStage && !ZeroSpeed_I THEN
  FaultMsg_W = SPINDLE_FAULT_MSG_C,
  SET ShowFaultStage,
  SET OtherFault_M,
  RST ATCMotor_O,
  RST ATCUnlocked_O,
  RST M6_SV,
  ChangeToTool_W = 0,
  RST ATCSpin_T,
  RST ATCStage
```

- [ ] **Step 6: Disarm the timer on the `!ATC_Z_Zero_Release_I` abort.** Replace:

```
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

with:

```
IF !ATC_Z_Zero_Release_I THEN
  FaultMsg_W = ATC_Spindle_Not_Parked_C,
  SET ShowFaultStage,
  SET OtherFault_M,
  RST ATCMotor_O,
  RST ATCUnlocked_O,
  RST M6_SV,
  ChangeToTool_W = 0,
  RST ATCSpin_T,
  RST ATCStage
```

- [ ] **Step 7: Disarm the timer on the match/exit rung.** Replace:

```
IF CarouselToolID_W == ChangeToTool_W THEN
  ChangeToTool_W = 0,
  SET ToolSelected_M,
  RST ATCMotor_O,
  RST ATCUnlocked_O,
  RST M6_SV,
  RST ATCStage
```

with:

```
IF CarouselToolID_W == ChangeToTool_W THEN
  ChangeToTool_W = 0,
  SET ToolSelected_M,
  RST ATCMotor_O,
  RST ATCUnlocked_O,
  RST M6_SV,
  RST ATCSpin_T,
  RST ATCStage
```

- [ ] **Step 8: Add the timeout-fault rung** after the match rung (so a real match wins a same-scan tie). Replace:

```
  RST ATCSpin_T,
  RST ATCStage


;=============================================================================
   GearShiftStage ; Acroloc
```

with:

```
  RST ATCSpin_T,
  RST ATCStage

; Acroloc: carousel never found the tool within ATC_SPIN_TIMEOUT_MS_C ->
; fault, stop the motor, relock. Placed after the match rung so a genuine
; match on the same scan wins (it RSTs ATCStage/ATCSpin_T first).
IF ATCStage && ATCSpin_T THEN
  FaultMsg_W = CAROUSEL_TIMEOUT_MSG_C,
  SET ShowFaultStage,
  SET OtherFault_M,
  RST ATCMotor_O,
  RST ATCUnlocked_O,
  RST M6_SV,
  ChangeToTool_W = 0,
  RST ATCSpin_T,
  RST ATCStage


;=============================================================================
   GearShiftStage ; Acroloc
```

- [ ] **Step 9: Renormalize line endings.**

Run: `sed -i 's/\r*$/\r/' Centroid-Acroloc-ALLIN1DC.src`
Then: `grep -Pc '[^\r]$' Centroid-Acroloc-ALLIN1DC.src` -> expected `0` (no LF-only lines).

- [ ] **Step 10: Compile.**

Run: `./compile.sh`
Expected: `Compilation successful`, **0 errors**, `Warnings: <= 195`, tokens slightly above 4799. Investigate any new warning.

- [ ] **Step 11: Verify the timer is now wired and diff is clean.**

Run:
```bash
grep -nE "ATCSpin_T" Centroid-Acroloc-ALLIN1DC.src
git diff --stat Centroid-Acroloc-ALLIN1DC.src
```
Expected: `ATCSpin_T` now appears in the def line, the arm rung, the timeout rung, and all three exit RSTs (6 references total). Diff touches only the constants block, the kickoff, and `ATCStage` — nothing else. Eyeball `git diff` to confirm.

- [ ] **Step 12: Commit.**

```bash
git add Centroid-Acroloc-ALLIN1DC.src
git commit -m "feat(plc): bound ATC carousel search with a 20s timeout

Arm ATCSpin_T (T24) at M6 kickoff; fault CAROUSEL MOVE TIME OUT + stop motor
+ relock if CarouselToolID_W never matches ChangeToTool_W within 20s. Disarm
on every ATCStage exit. Closes the no-timeout ;TODO / previously-unused timer.

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

**Operator gate (off-repo, MUST precede machine trust):** load in CNC12, confirm a clean compile, and run the on-machine checklist (Task 3). The implementer cannot perform this and must not claim it was done.

---

### Task 2: Sync affected documentation

**Files:**
- Modify: `CLAUDE.md`, `docs/plc-spec/atc.md`, `docs/plc-spec/definitions.md`, `.claude/skills/acroloc-s10/SKILL.md`, `.claude/skills/acroloc-s10/reference/atc-flow.md`, `docs/backlog.md`

**Scope note:** Fix only content made false by Task 1. Do not re-baseline `src:` line numbers or bump the plc-spec pins.

- [ ] **Step 1: `CLAUDE.md`.** In the "Conventions & cautions" section, the bullet stating the carousel has no timeout ("The carousel has **no timeout if a tool is never found**...") — rewrite: the search is now bounded by a 20 s `ATCSpin_T` watchdog that faults `CAROUSEL MOVE TIME OUT` and stops/relocks; note the position-decode off-by-one still matters (wrong/never match) but no longer means an infinite spin.

- [ ] **Step 2: `docs/plc-spec/atc.md`.** Update the flow description and the "Known gaps" section: the no-carousel-timeout gap (the quoted `;TODO`, unused `ATCSpin_T`) is **closed** — describe the arm-at-kickoff / fault-after-20s behavior and the reused message 63. Remove or rewrite the quoted `;TODO` lines so they no longer read as an open gap.

- [ ] **Step 3: `docs/plc-spec/definitions.md`.** Remove `ATCSpin_T` from the "Defined but unused" section (it is now armed and read). Add two rows for the new constants in the message-constants table: `CAROUSEL_TIMEOUT_MSG_C` (`16130`, `(2+256*63)`) and `ATC_SPIN_TIMEOUT_MS_C` (`20000`, Acroloc). Update the `ATCSpin_T` timer row note from "defined but unused" to "carousel search watchdog (armed at M6 kickoff)".

- [ ] **Step 4: acroloc-s10 skill.** In `SKILL.md` (the "No timeout" critical gotcha under *Edit tool-change logic*) and `reference/atc-flow.md` (the known-gaps / no-timeout note), replace the "spins indefinitely / no timeout" text with a description of the 20 s watchdog and the `CAROUSEL MOVE TIME OUT` fault. Keep the position-decode `+10-not-+16` caution as-is.

- [ ] **Step 5: `docs/backlog.md`.** Mark item #1 done: change `[~]` to `[x]` and note "shipped <branch/PR>".

- [ ] **Step 6: Commit.**

```bash
git add CLAUDE.md docs/plc-spec/atc.md docs/plc-spec/definitions.md .claude/skills/acroloc-s10/SKILL.md .claude/skills/acroloc-s10/reference/atc-flow.md docs/backlog.md
git commit -m "docs: carousel search timeout closes the no-timeout ATC gap

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

### Task 3: On-machine test checklist

**Files:**
- Create: `docs/testing/atc-timeout-test.md`

- [ ] **Step 1: Write the checklist** mirroring the spec's Testing section, in the `docs/testing/` style (watch `ATCMotor_O` OUT17, `ATCSpin_T` T24, the message line; keep no tool in the spindle):

1. **No false trips:** several `M6` changes to near and far tools all complete normally (< 10 s); watchdog never fires.
2. **Unreachable tool -> timeout:** with no tool in the spindle, command a tool with no pocket / that never decodes (e.g. `M6 T13` on a 12-pocket carousel). Expect the carousel to spin and, at ~20 s, fault "CAROUSEL MOVE TIME OUT", `ATCMotor_O` -> 0, carousel relocks, `M6_SV`/`ChangeToTool_W` clear.
3. **Recovery:** clear the fault, run a normal `M6` to a valid tool — completes, proving the watchdog re-armed cleanly.

Include a sign-off table (date/operator, PLC source commit tested, pass/fail per item, notes). Note the operator may substitute physically stalling the carousel for test 2 if commanding an out-of-range tool is undesirable.

- [ ] **Step 2: Commit.**

```bash
git add docs/testing/atc-timeout-test.md
git commit -m "docs(testing): ATC carousel timeout on-machine checklist

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

## Self-Review

- **Spec coverage:** constants (T1 S2), arm-once at kickoff (T1 S3), timeout fault rung after match (T1 S8), disarm on all three existing exits (T1 S5-7), TODO removal (T1 S4), doc sync incl. CLAUDE.md/atc.md/definitions/skill (T2), backlog #1 done (T2 S5), testing (T3). All spec sections mapped.
- **Placeholder scan:** none — every edit shows exact before/after text; the constant values (`16130`, `20000`) and rung text match the spec verbatim.
- **Name consistency:** `ATCSpin_T`, `ATC_SPIN_TIMEOUT_MS_C`, `CAROUSEL_TIMEOUT_MSG_C`, and the `RST ATCSpin_T` cleanup are identical across spec and all tasks; the timeout rung condition `ATCStage && ATCSpin_T` matches the spec.
