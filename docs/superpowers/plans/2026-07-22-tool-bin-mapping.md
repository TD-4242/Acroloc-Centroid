# Tool-to-Bin Mapping (tools > 12) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Assign a tool to a physical carousel bin in CNC12's tool library (e.g. tool 31 -> bin 2) and have `M6T31` index the carousel to that bin, by running CNC12 in random ATC mode (P160 = 2) and adding the PLC carousel-position handshake that random mode requires.

**Architecture:** Random ATC (P160 = 2) gives the tool-library bin column and loads `SV_TOOL_NUMBER` with the bin. Our existing `ATCStage` already indexes to `ChangeToTool_W = SV_TOOL_NUMBER`, so it needs no change; the missing piece is `SV_PLC_CAROUSEL_POSITION` reporting, without which CNC12 keeps the carousel still (this is why M6 was silent on-machine). Put-back is mechanical (Z-zero + `ATC_Z_Zero_Release_I`), so there is no put-back-move logic. See `docs/superpowers/specs/2026-07-22-tool-bin-mapping-design.md`.

**Tech Stack:** Centroid CNC12 (ALLIN1DC / MPU11) PLC stage language (`.src`) and M-code macros (`.mac`); `./compile.sh` (Wine `mpucomp`) for compile/lint; `tools/plcfmt.py` for canonical formatting. No automated behavior tests exist - PLC validation is `./compile.sh` clean plus on-machine checks (per CLAUDE.md).

## Global Constraints

- **ASCII-only, CRLF line endings** for `Centroid-Acroloc-ALLIN1DC.src` and `mfunc6.mac` (7-bit ASCII; no em dashes / smart quotes).
- **Tag every custom PLC addition** with a trailing `; Acroloc` comment.
- **Run `./compile.sh` after every `.src` change** and report the error/warning-count delta. Baseline must not gain errors.
- **Do not touch `ATCStage`** (STG16): the 5-switch decode, peak/`InToolSelect_M` gating, match/exit rung, and the 20 s `ATCSpin_T` watchdog stay byte-for-byte.
- **Preserve macro guards:** `mfunc6.mac` keeps `IF #4202 || #4201 THEN GOTO 1000` and its `N1000` label.
- **`plc.map` is generated** - never hand-edit; it is gitignored.
- **`docs/plc-spec/` line references are pinned to a commit.** On a `.src` edit, fix any content the edit made false and update the pinned commit hash; do not re-baseline unrelated line numbers.
- Python tooling is **stdlib-only** (no pip/pytest on the dev box).

---

### Task 1: Config + Phase 0 probe (on-machine, owner-run)

Runs on the control PC, not in the repo. Produces a recorded finding that gates Task 3 (whether `mfunc6` needs completion signaling). An agent cannot execute it.

**Files:** none in the repo; the recorded outcome feeds Task 4's docs.

**Interfaces:**
- Consumes: nothing.
- Produces: a recorded finding - "at P160 = 2 with the position report NOT yet built, is M6 silent (as expected)? Does CNC12 mark a change complete on the existing `M95 /8`, or does it demand extra completion signaling? Is there an ATC-position reset screen? On-screen labels for P160/P161?"

- [ ] **Step 1: Set random ATC mode and bin count**

In CNC12, set machine parameter **160 = 2** (random ATC) and **161 = 12** (max bin). Note the on-screen label/description text for both.

- [ ] **Step 2: Build the tool-library bin table**

Assign bins: tools 1-12 -> bins 1-12 (backward-compatible), tool 31 -> bin 2, plus any other tools > 12.

- [ ] **Step 3: Probe M6 with diagnostics open**

Open the PLC diagnostic screen (**ALT+I**). Run `M6T5` in MDI. Record: does Z move? does `W72` (`ChangeToTool_W`) change? any status/message-line text? Expected (pre-fix): nothing moves, because `SV_PLC_CAROUSEL_POSITION` is not reported yet - this confirms Task 2 is the fix.

- [ ] **Step 4: Look for an ATC reset / carousel-position screen**

Find any CNC12 screen to declare the current carousel bin / tool in spindle (used at cold start to sync `SV_ATC_CAROUSEL_POSITION`). Record whether it exists and where. This decides how the cold-start seed in Task 2 is validated.

---

### Task 2: PLC carousel-position handshake (required)

Adds `CurrentBin_W`, seeds it at power-up from `SV_ATC_CAROUSEL_POSITION`, and reports it to CNC12 each scan via `SV_PLC_CAROUSEL_POSITION`. All additions live in the definitions section, `InitialStage`, and `MainStage` - never inside `ATCStage`. Agent-executable.

**Files:**
- Modify: `Centroid-Acroloc-ALLIN1DC.src` (definitions near line 1117; `InitialStage` near line 1311; `MainStage` right after line 2931)

**Interfaces:**
- Consumes: `CarouselToolID_W` (W71, settled matched bin), `ATCStage` (STG16), `SV_ATC_CAROUSEL_POSITION`, `True_M`.
- Produces: `CurrentBin_W IS W78` and a live `SV_PLC_CAROUSEL_POSITION` report.

- [ ] **Step 1: Record the compile baseline**

Run: `./compile.sh`
Expected: note the exact error count (0) and warning count. Every later compile compares to this.

- [ ] **Step 2: Add the `CurrentBin_W` definition**

After the `ChangeToTool_W` line (`Centroid-Acroloc-ALLIN1DC.src:1117`), column-aligned with the surrounding block:

```
CurrentBin_W                    IS W78 ; Acroloc current carousel bin reported to CNC12 (random ATC)
```

- [ ] **Step 3: Seed the bin at power-up**

In `InitialStage`, inside the `IF 1==1 THEN SET ...` block (Acroloc lines end at line 1310, `SpindleRange_W = 1,`), add before `RST InitialStage`:

```
             CurrentBin_W = SV_ATC_CAROUSEL_POSITION,  ; Acroloc seed last-known bin from CNC12 (random ATC)
```

- [ ] **Step 4: Add the report block in MainStage**

Immediately after the ATC kickoff rung (`IF M6_SV THEN ChangeToTool_W = SV_TOOL_NUMBER, SET ATCStage`, line 2931):

```
; Acroloc -- random ATC: report current carousel bin to CNC12 (outside ATCStage; search logic untouched)
; Latch only when no change is running and a settled ID is present, so mid-spin
; transients never reach CNC12. CarouselToolID_W holds the matched bin from end
; of change until the next kickoff zeroes it.
IF !ATCStage && CarouselToolID_W > 0 THEN CurrentBin_W = CarouselToolID_W
IF True_M THEN SV_PLC_CAROUSEL_POSITION = CurrentBin_W
```

- [ ] **Step 5: Reformat to canonical style**

Run: `python3 tools/plcfmt.py --fix`
Expected: exit 0; only whitespace/alignment of new lines changes. A fingerprint mismatch is expected (the program intentionally changed) - see `tools/README.md` for the changed-program `--fix` path, or align by hand to match surrounding columns.

- [ ] **Step 6: Compile and check the delta**

Run: `./compile.sh`
Expected: 0 errors (same as Step 1). Report the warning delta vs Step 1 (should be 0). If `SV_ATC_CAROUSEL_POSITION` or `SV_PLC_CAROUSEL_POSITION` is rejected at compile on this firmware, STOP and report - the handshake cannot proceed without them.

- [ ] **Step 7: Verify additions and placement**

Run: `grep -nE "CurrentBin_W|SV_PLC_CAROUSEL_POSITION|SV_ATC_CAROUSEL_POSITION" Centroid-Acroloc-ALLIN1DC.src`
Expected: the `IS W78` def, the `InitialStage` seed, and the two `MainStage` rungs - four hits, none inside `ATCStage`.

Run: `LC_ALL=C grep -nP '[^\x00-\x7F]' Centroid-Acroloc-ALLIN1DC.src || echo ASCII-clean`
Expected: `ASCII-clean`.

- [ ] **Step 8: Commit**

```bash
git add Centroid-Acroloc-ALLIN1DC.src
git commit -m "feat: report carousel bin to CNC12 for random ATC (P160=2 handshake)

Adds CurrentBin_W (W78), seeded at power-up from SV_ATC_CAROUSEL_POSITION and
reported each scan via SV_PLC_CAROUSEL_POSITION -- the handshake CNC12 random
ATC requires before it will index the carousel. All additions are outside
ATCStage; the search/decode/match logic is unchanged.

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

### Task 3: mfunc6 completion signaling (CONDITIONAL on Task 1 Step 3)

**Execute ONLY if Task 1 recorded that CNC12 does not mark the change complete on the existing `M95 /8` in random mode.** If Task 1 shows the existing handshake suffices, skip to Task 4.

**Files:**
- Modify: `mfunc6.mac`

**Interfaces:**
- Consumes: the Task 1 finding naming the exact completion signal CNC12 waits on.
- Produces: an `mfunc6.mac` that completes a random-mode change.

- [ ] **Step 1: Add the minimum completion signaling the probe identified**

Mirror the umbrella macro's completion pattern (`docs/official/_ALLIN1DC/_atc/_umbrella/cncm/mfunc6.mac`, e.g. its `M94 /41` "report tool info"), adding only the specific bit(s) Task 1 named, placed after the `M100 /93016` wait and before `M95 /8`. Preserve the `IF #4202 || #4201 THEN GOTO 1000` guard and the `N1000` label.

- [ ] **Step 2: Verify guard and ASCII**

Run: `grep -nE "#4202|N1000" mfunc6.mac` (guard + label present) and `LC_ALL=C grep -nP '[^\x00-\x7F]' mfunc6.mac || echo ASCII-clean`.
Expected: guard at top, `N1000` at end, `ASCII-clean`.

- [ ] **Step 3: Commit**

```bash
git add mfunc6.mac
git commit -m "feat: random-ATC completion signaling in mfunc6 (M6 handshake)

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

### Task 4: Documentation updates

Record random-ATC mode, the position handshake, and `SV_TOOL_NUMBER`-as-bin. Always runs.

**Files:**
- Modify: `docs/plc-spec/atc.md` (random-ATC note + pinned commit hash + the `CurrentBin_W` report)
- Modify: `.claude/skills/acroloc-s10/reference/atc.md` (tool-to-bin mapping under Tool numbering)
- Modify: `.claude/skills/acroloc-s10/reference/atc-flow.md` (SV_TOOL_NUMBER-as-bin + position report)

**Interfaces:**
- Consumes: Task 1 finding; the `CurrentBin_W` / `SV_PLC_CAROUSEL_POSITION` names from Task 2.
- Produces: docs consistent with shipped behavior.

- [ ] **Step 1: Update the machine ATC reference**

In `.claude/skills/acroloc-s10/reference/atc.md`, under "Tool numbering," add:

```
## Tool-to-bin mapping (random ATC, P160 = 2)

CNC12 runs in random ATC mode (machine parameter 160 = 2, 161 = 12): the tool
library's bin column maps a tool number to a physical carousel bin, and M107
loads SV_TOOL_NUMBER with the **bin**, not the tool number. So M6T31 with tool
31 -> bin 2 indexes the carousel to bin 2. Tools 1-12 are assigned bins 1-12.
The PLC reports SV_PLC_CAROUSEL_POSITION (from CurrentBin_W, W78) so CNC12 will
permit the change; put-back stays mechanical (Z-zero + ATC_Z_Zero_Release_I).
```

- [ ] **Step 2: Update the ATC flow reference**

In `.claude/skills/acroloc-s10/reference/atc-flow.md`, at the `MainStage` kickoff description, append:

```
Under random ATC (P160=2), SV_TOOL_NUMBER is the requested **carousel bin**
(CNC12 maps tool->bin from the tool library), so ChangeToTool_W is a bin and
the carousel search is unchanged. MainStage also reports CurrentBin_W (W78) to
CNC12 via SV_PLC_CAROUSEL_POSITION (outside ATCStage), seeded at power-up from
SV_ATC_CAROUSEL_POSITION -- without this report CNC12 will not index the
carousel.
```

- [ ] **Step 3: Update the pinned plc-spec section**

In `docs/plc-spec/atc.md`, add a "Random ATC / tool-bin mapping" note describing the same behavior, document `CurrentBin_W` (W78), the `InitialStage` seed, and the `MainStage` report rung, and **update the pinned commit hash** to the Task 2 commit. Fix line references the Task 2 edit shifted; do not re-baseline unrelated ones.

- [ ] **Step 4: Verify ASCII + consistency**

Run:
```bash
LC_ALL=C grep -rnP '[^\x00-\x7F]' docs/plc-spec/atc.md .claude/skills/acroloc-s10/reference/atc.md .claude/skills/acroloc-s10/reference/atc-flow.md || echo ASCII-clean
grep -rniE "random atc|P160|bin" docs/plc-spec/atc.md .claude/skills/acroloc-s10/reference/atc.md
```
Expected: `ASCII-clean`; the random-ATC notes appear.

- [ ] **Step 5: Commit**

```bash
git add docs/plc-spec/atc.md .claude/skills/acroloc-s10/reference/atc.md .claude/skills/acroloc-s10/reference/atc-flow.md
git commit -m "docs: random ATC tool-to-bin mapping (atc spec + acroloc-s10 skill)

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

## Notes for the executor

- **Task ordering is gated.** Task 1 is on-machine and owner-run; its Step 3 finding decides whether Task 3 runs. Task 2 (the position report) is required regardless and is the agent's main deliverable. Task 4 always runs.
- There is no automated behavior test. "Green" for Task 2/3 means `./compile.sh` clean with no new warnings; real behavior is verified on-machine by running `M6T31` (tool 31 -> bin 2) and `M6T5` after loading the new `.plc`.
