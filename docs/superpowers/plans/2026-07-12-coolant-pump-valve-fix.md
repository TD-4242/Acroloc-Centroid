# Coolant Pump / Flood-Valve Fix Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make flood coolant actually flow: OUT4 (`Mist_O`) is really the coolant pump and OUT3 (`Flood_O`) is the flood valve. Drive them from the selected mode so flood = pump + valve and wash = pump only.

**Architecture:** Rename the two outputs, decouple mode-selection (the panel LEDs) from the physical outputs, derive `FloodValve_O`/`CoolantPump_O` from the mode LEDs, and make the panel flood/wash buttons mutually exclusive.

**Tech Stack:** Centroid CNC12 / MPU11 PLC stage language (`Centroid-Acroloc-ALLIN1DC.src`). Only in-repo verification is `./compile.sh` (MPUCOMP via wine) — syntax/lint. Real behavior is validated on the machine by the owner (off-repo); the implementer cannot do it and must not claim it.

**Design spec:** `docs/superpowers/specs/2026-07-12-coolant-pump-valve-fix-design.md`

## Global Constraints

- **ASCII only** for `.src`.
- **`.src` is CRLF.** Edit tool inserts LF; after editing run `sed -i 's/\r*$/\r/' Centroid-Acroloc-ALLIN1DC.src` and confirm `git diff` is content-only.
- **Tag custom code `; Acroloc`.** Match the fixed-column style (output-def `IS` at column 33).
- **Compile gate:** `./compile.sh` -> `Compilation successful`, **0 errors**. Baseline: 4812 tokens, 190 warnings. Expect tokens up slightly (added rungs), warnings unchanged (190); investigate any new warning.
- **Doc line pins:** fix now-false plc-spec content only; do not re-baseline `src:` line numbers.
- **Commit only when asked** — end each task with a commit step but confirm before committing.

---

### Task 1: Fix the coolant outputs (PLC source)

**Files:**
- Modify: `Centroid-Acroloc-ALLIN1DC.src` — output defs (src:390-391), `M8_SV`/`M7_SV` comments (src:1059/1061), coolant coil rungs (src:2036-2046).

**Interfaces:**
- Consumes (existing): `CoolFloodLED_O`, `CoolMistLED_O`, `CoolantFloodPD_PD`, `CoolantMistPD_PD`, `CoolAutoModeLED_O`, `M8_SV`, `M7_SV`, `SelectCoolantFlood_SV`, `SelectCoolantMist_SV`, and the kill terms.
- Produces: `FloodValve_O` (OUT3, renamed), `CoolantPump_O` (OUT4, renamed), driven only by the new derivation rungs.

- [ ] **Step 1: Confirm clean baseline.**

Run: `./compile.sh`
Expected: `Compilation successful`, `4812 tokens`, `Warnings: 190`.

- [ ] **Step 2: Rename the two output definitions.** Replace:

```
Flood_O                         IS OUT3  ;SPST Type
Mist_O                          IS OUT4  ;SPST Type
```

with:

```
FloodValve_O                    IS OUT3  ; Acroloc flood valve: opens the coolant pump to the workspace nozzles (SPST)
CoolantPump_O                   IS OUT4  ; Acroloc coolant pump: pressurizes coolant (+valve=flood nozzles, no valve=cleaning hose) (SPST)
```

- [ ] **Step 3: Update the `M8_SV` comment.** Replace:

```
M8_SV                            IS SV_M94_M95_3 ;(Flood_O On)
```

with:

```
M8_SV                            IS SV_M94_M95_3 ;(Flood mode: coolant pump + flood valve)
```

- [ ] **Step 4: Update the `M7_SV` comment.** Replace:

```
M7_SV                            IS SV_M94_M95_5 ;(Mist_O)
```

with:

```
M7_SV                            IS SV_M94_M95_5 ;(Mist/wash mode: coolant pump only)
```

- [ ] **Step 5: Decouple the flood rung** (toggle the mode LED, drop the output drive). Replace:

```
IF ((Flood_O ^ (!CoolAutoModeLED_O && CoolantFloodPD_PD)) ||
   CoolAutoModeLED_O && M8_SV) &&
   !(SV_STOP || CoolantAutoManualPD_PD || CoolAutoModeLED_O && !M8_SV || ErrorFlag_M || DoToolCheck_SV)
  THEN (Flood_O), (CoolFloodLED_O), (SelectCoolantFlood_SV)
```

with:

```
IF ((CoolFloodLED_O ^ (!CoolAutoModeLED_O && CoolantFloodPD_PD)) ||
   CoolAutoModeLED_O && M8_SV) &&
   !(SV_STOP || CoolantAutoManualPD_PD || CoolAutoModeLED_O && !M8_SV || ErrorFlag_M || DoToolCheck_SV)
  THEN (CoolFloodLED_O), (SelectCoolantFlood_SV)
```

- [ ] **Step 6: Decouple the mist rung and add the mutual-exclusion + derivation rungs.** Replace:

```
IF ((Mist_O ^ (!CoolAutoModeLED_O && CoolantMistPD_PD)) ||
   CoolAutoModeLED_O && M7_SV) &&
   !(SV_STOP || CoolantAutoManualPD_PD || CoolAutoModeLED_O && !M7_SV || ErrorFlag_M || DoToolCheck_SV)
  THEN (Mist_O), (CoolMistLED_O), (SelectCoolantMist_SV)
```

with:

```
IF ((CoolMistLED_O ^ (!CoolAutoModeLED_O && CoolantMistPD_PD)) ||
   CoolAutoModeLED_O && M7_SV) &&
   !(SV_STOP || CoolantAutoManualPD_PD || CoolAutoModeLED_O && !M7_SV || ErrorFlag_M || DoToolCheck_SV)
  THEN (CoolMistLED_O), (SelectCoolantMist_SV)

; Acroloc: flood and wash are mutually exclusive (valve open XOR closed while pump runs).
; Manual mode only; auto mode is handled by the M7/M8 macros. After both toggle rungs so the
; just-pressed mode wins.
IF !CoolAutoModeLED_O && CoolantFloodPD_PD THEN RST CoolMistLED_O   ; flood press clears wash
IF !CoolAutoModeLED_O && CoolantMistPD_PD  THEN RST CoolFloodLED_O  ; wash press clears flood

; Acroloc: drive the coolant hardware from the selected mode.
; Pump (OUT4) runs in either mode; the flood valve (OUT3) opens only in flood mode. The mode
; LEDs are already gated off by SV_STOP/errors/tool-check above, so these inherit that.
IF CoolFloodLED_O THEN (FloodValve_O)
IF CoolFloodLED_O || CoolMistLED_O THEN (CoolantPump_O)
```

- [ ] **Step 7: Renormalize line endings.**

Run: `sed -i 's/\r*$/\r/' Centroid-Acroloc-ALLIN1DC.src`
Then: `grep -Pc '[^\r]$' Centroid-Acroloc-ALLIN1DC.src` -> expected `0`.

- [ ] **Step 8: Verify renames and single-driver.**

Run:
```bash
grep -nE "\bFlood_O\b|\bMist_O\b" Centroid-Acroloc-ALLIN1DC.src || echo "(old names gone -- good)"
grep -nE "\bFloodValve_O\b|\bCoolantPump_O\b" Centroid-Acroloc-ALLIN1DC.src
```
Expected: no `Flood_O`/`Mist_O` remain; `FloodValve_O` appears exactly twice (def + one derivation rung); `CoolantPump_O` appears exactly twice (def + one derivation rung).

- [ ] **Step 9: Compile.**

Run: `./compile.sh`
Expected: `Compilation successful`, **0 errors**, `Warnings: 190`, tokens slightly above 4812.

- [ ] **Step 10: Review the diff.**

Run: `git diff Centroid-Acroloc-ALLIN1DC.src`
Confirm only the two defs, the two M-code comments, the two coil rungs, and the four new rungs changed.

- [ ] **Step 11: Commit.**

```bash
git add Centroid-Acroloc-ALLIN1DC.src
git commit -m "fix(plc): coolant outputs match real plumbing (pump + flood valve)

OUT4 is the coolant pump (Mist_O -> CoolantPump_O), OUT3 is the flood valve
(Flood_O -> FloodValve_O). Derive them from the selected mode: flood = pump +
valve, wash = pump only. Fixes flood never running the pump (no nozzle flow).
Panel flood/wash made mutually exclusive.

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

**Operator gate (off-repo, MUST precede machine trust):** load in CNC12, confirm a clean compile, and run the on-machine checklist (Task 3).

---

### Task 2: Sync affected documentation

**Files:**
- Modify: `docs/plc-spec/definitions.md`, `docs/plc-spec/main-stage.md`, `.claude/skills/acroloc-s10/reference/macros.md`, `docs/backlog.md`

- [ ] **Step 1: `definitions.md`.** Replace the two output rows:

```
| `Flood_O` | OUT3 | 370 | | Flood coolant, SPST. [main-stage.md](main-stage.md) |
| `Mist_O` | OUT4 | 371 | | Mist coolant, SPST. [main-stage.md](main-stage.md) |
```

with:

```
| `FloodValve_O` | OUT3 | 370 | Acroloc | Flood valve — opens the coolant pump to the workspace nozzles; SPST. [main-stage.md](main-stage.md) |
| `CoolantPump_O` | OUT4 | 371 | Acroloc | Coolant pump — pressurizes coolant (+valve = flood nozzles, no valve = cleaning hose); SPST. [main-stage.md](main-stage.md) |
```

- [ ] **Step 2: `main-stage.md`.** Rewrite the Flood/Mist coil bullets (src:2117-2127 area) to describe the corrected model: the two coolant rungs now toggle the **mode LEDs** (`CoolFloodLED_O`/`CoolMistLED_O`) and report `SelectCoolant*_SV`; the physical outputs are **derived** — `FloodValve_O` (OUT3) = flood mode, `CoolantPump_O` (OUT4) = flood OR wash mode — so flood runs the pump and opens the valve while wash runs the pump only. Note the panel modes are mutually exclusive and the derived outputs inherit the LEDs' stop/fault gating.

- [ ] **Step 3: `.claude/skills/acroloc-s10/reference/macros.md`.** In the `mfunc7`/`mfunc8` rows, add a note that on this machine OUT4 is the coolant pump and OUT3 the flood valve: `M8` = flood (pump + valve), `M7` = wash/hose (pump only). The macros are unchanged; the behavior lives in the PLC output derivation.

- [ ] **Step 4: `docs/backlog.md`.** Add a completed item under Robustness/safety (or a new "Fixes" note): coolant pump/flood-valve corrected so flood coolant actually flows; renamed OUT3/OUT4; mutually exclusive flood/wash. Mark `[x]`, note *shipped on `post-release-fixes`*.

- [ ] **Step 5: Commit.**

```bash
git add docs/plc-spec/definitions.md docs/plc-spec/main-stage.md .claude/skills/acroloc-s10/reference/macros.md docs/backlog.md
git commit -m "docs: coolant outputs are pump + flood valve (flood now runs the pump)

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

### Task 3: On-machine test checklist

**Files:**
- Create: `docs/testing/coolant-pump-valve-test.md`

- [ ] **Step 1: Write the checklist** (watch OUT3 `FloodValve_O` and OUT4 `CoolantPump_O` in Alt-I), mirroring the spec's six tests:

1. Flood button -> OUT4 and OUT3 both on; coolant at the nozzles (pump runs, valve opens).
2. Wash/"mist" button -> OUT4 on, OUT3 off; cleaning hose pressurizes, no nozzle flow.
3. Switch flood <-> wash -> pump (OUT4) stays on while valve (OUT3) toggles; one LED at a time.
4. Coolant off -> both off.
5. Auto-coolant MDI: `M8` -> flood (pump+valve), `M7` -> wash (pump only), `M9` -> off.
6. E-stop / `SV_STOP` with coolant on -> both outputs drop.

Include a sign-off table (date/operator, PLC source commit tested, pass/fail per item, notes).

- [ ] **Step 2: Commit.**

```bash
git add docs/testing/coolant-pump-valve-test.md
git commit -m "docs(testing): coolant pump/flood-valve on-machine checklist

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

## Self-Review

- **Spec coverage:** renames (T1 S2-4), decouple flood + mist rungs (T1 S5-6), derivation rungs (T1 S6), panel mutual exclusion (T1 S6), doc sync (T2), testing (T3). All mapped.
- **Placeholder scan:** none — exact before/after for every source edit; constants/rung text match the spec verbatim.
- **Name consistency:** `FloodValve_O` (OUT3) and `CoolantPump_O` (OUT4), the derivation conditions (`CoolFloodLED_O`; `CoolFloodLED_O || CoolMistLED_O`), and the mutual-exclusion RSTs are identical across spec and plan.
