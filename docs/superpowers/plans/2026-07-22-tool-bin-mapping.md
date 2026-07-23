# Tool-to-Bin Mapping (tools > 12) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Let `M6T<n>` for any tool number (including n > 12) spin the carousel to the bin that tool is assigned to in CNC12's tool library, by enabling Centroid Enhanced ATC mode and (only if the drive-side handshake requires it) reporting carousel position back from the PLC.

**Architecture:** Enhanced ATC makes CNC12 do the tool->bin lookup itself and load `SV_TOOL_NUMBER` with the *bin*. The PLC reads `SV_TOOL_NUMBER` in exactly one rung (`ChangeToTool_W = SV_TOOL_NUMBER`, `Centroid-Acroloc-ALLIN1DC.src:2931`), so the carousel state machine is unchanged. Phase A (CNC12 config + tool-library bin table) is the whole feature in the likely case. Phase B is a conditional, additive PLC change (a `SV_PLC_CAROUSEL_POSITION` report plus a power-up seed) placed entirely outside `ATCStage`, needed only if CNC12 gates the change on position feedback.

**Tech Stack:** Centroid CNC12 (ALLIN1DC / MPU11) PLC stage language (`.src`); `./compile.sh` (Wine `mpucomp`) for compile/lint; `tools/plcfmt.py` for canonical formatting. No automated behavior tests exist -- PLC validation is `./compile.sh` clean plus on-machine/simulator checks (per CLAUDE.md).

## Global Constraints

- **ASCII-only, CRLF line endings** for `Centroid-Acroloc-ALLIN1DC.src` (7-bit ASCII; no em dashes / smart quotes).
- **Tag every custom addition** with a trailing `; Acroloc` comment.
- **Run `./compile.sh` after every `.src` change** and report the error/warning-count delta before moving on. Baseline must not gain errors.
- **Do not touch `ATCStage`** (STG16): the 5-switch decode, the peak/`InToolSelect_M` gating, the match/exit rung, and the 20 s `ATCSpin_T` watchdog stay byte-for-byte as they are.
- **`plc.map` is generated** -- never hand-edit it; it is gitignored.
- **`docs/plc-spec/` line references are pinned to a commit.** On a `.src` edit, fix any content the edit made false and update the pinned commit hash; do not re-baseline unrelated line numbers.
- **Whitelist `.gitignore`:** new root/doc files can be silently skipped by `git add`; verify staging with `git status --short` before committing.
- Python tooling is **stdlib-only** (no pip/pytest on the dev box).

---

### Task 1: Phase A -- Enhanced ATC commissioning (on-machine, owner-run)

This task runs on the control PC, not in the repo. It produces one artifact: a recorded **go/no-go decision** that gates Task 2. An agent cannot execute it; the machine owner runs it and reports the result back.

**Files:**
- No repo files change in this task. The recorded outcome is captured in Task 3's doc update.

**Interfaces:**
- Consumes: nothing.
- Produces: a recorded finding -- "after enabling Enhanced ATC, does `SV_TOOL_NUMBER` carry the assigned **bin**, and does CNC12 complete the change without PLC position feedback?" This yes/no answer decides whether Task 2 is executed.

- [ ] **Step 1: Enable Enhanced ATC and set the bin count**

In CNC12, open the ATC configuration and switch the ATC type to the random / enhanced tool changer option (the mode in which `M107` loads `SV_TOOL_NUMBER` with a carousel *bin location* rather than the raw tool number). Set machine parameter 161 (`SV_MACHINE_PARAMETER_161`, max carousel bin) to `12`.

- [ ] **Step 2: Build the tool-library bin table**

In the tool library, assign bins so existing tools stay 1:1 and the new high-numbered tool maps as desired:
- Tools 1-12 -> bins 1-12 (keeps them backward-compatible).
- Tool 31 -> bin 2 (the worked example), plus any other tools > 12.

- [ ] **Step 3: Pivotal diagnostic check (records the go/no-go)**

Open the CNC12 PLC diagnostic screen so `SV_TOOL_NUMBER` and `ChangeToTool_W` (W72) are visible. Run `M6T31` from MDI.
- Expected (mapping works): `SV_TOOL_NUMBER` / `ChangeToTool_W` read **2** (the bin, not 31), and the carousel indexes to bin 2 and Z snaps the tool in. If so, record **"Phase A sufficient -- no PLC change"**: the feature is complete after Task 3's docs.
- If instead CNC12 refuses to start or complete the change while waiting on carousel-position feedback, record **"Phase B required"** and proceed to Task 2.

- [ ] **Step 4: Regression sanity check on-machine**

Run `M6T5` (bin 5) and confirm it changes exactly as before. Record the result. This confirms the 1:1 tools are unaffected regardless of the go/no-go outcome.

---

### Task 2: Phase B -- report carousel position to CNC12 (CONDITIONAL)

**Execute this task ONLY if Task 1 Step 3 recorded "Phase B required."** If Task 1 recorded "Phase A sufficient," skip directly to Task 3.

Adds a new word `CurrentBin_W`, seeds it at power-up from CNC12's last-known position, and reports it to CNC12 every scan via `SV_PLC_CAROUSEL_POSITION`. All additions live in the definitions section, `InitialStage`, and `MainStage` -- never inside `ATCStage`.

**Files:**
- Modify: `Centroid-Acroloc-ALLIN1DC.src` (definitions near line 1117; `InitialStage` near line 1311; `MainStage` right after line 2931)

**Interfaces:**
- Consumes: `CarouselToolID_W` (W71, the settled matched bin after a change), `ATCStage` (STG16, set only while a change runs), `SV_ATC_CAROUSEL_POSITION` (CNC12's persisted last-known bin at power-up), `True_M`.
- Produces: `CurrentBin_W IS W78` (the current carousel bin) and a live `SV_PLC_CAROUSEL_POSITION` report.

- [ ] **Step 1: Record the compile baseline**

Run: `./compile.sh`
Expected: note the exact error count (must be 0) and the warning count. Write both down; every later compile is compared to this.

- [ ] **Step 2: Add the `CurrentBin_W` definition**

In the definitions section, immediately after the `ChangeToTool_W` line (`Centroid-Acroloc-ALLIN1DC.src:1117`), add, column-aligned with the surrounding `Name IS Resource` block:

```
CurrentBin_W                    IS W78 ; Acroloc current carousel bin reported to CNC12 (enhanced ATC)
```

- [ ] **Step 3: Seed the bin at power-up**

In `InitialStage`, inside the `IF 1==1 THEN SET ...` block (the Acroloc lines end at `Centroid-Acroloc-ALLIN1DC.src:1310`, `SpindleRange_W = 1,`), add one seed line before `RST InitialStage`:

```
             CurrentBin_W = SV_ATC_CAROUSEL_POSITION,  ; Acroloc seed last-known bin from CNC12 (enhanced ATC)
```

- [ ] **Step 4: Add the report block in MainStage**

Immediately after the ATC kickoff rung (`IF M6_SV THEN ChangeToTool_W = SV_TOOL_NUMBER, SET ATCStage`, `Centroid-Acroloc-ALLIN1DC.src:2931`), add:

```
; Acroloc -- enhanced ATC: report current carousel bin to CNC12 (outside ATCStage; search logic untouched)
; Latch only when no change is running and a settled ID is present, so mid-spin
; transients never reach CNC12. CarouselToolID_W holds the matched bin from end
; of change until the next kickoff zeroes it.
IF !ATCStage && CarouselToolID_W > 0 THEN CurrentBin_W = CarouselToolID_W
IF True_M THEN SV_PLC_CAROUSEL_POSITION = CurrentBin_W
```

- [ ] **Step 5: Reformat to canonical style**

Run: `python3 tools/plcfmt.py --fix`
Expected: exit 0; only whitespace/alignment of the new lines changes. If it reports a fingerprint mismatch, that is expected here (the program intentionally changed) -- re-read `tools/README.md` for the `--fix` invocation that applies to a changed program, or apply alignment by hand to match the surrounding columns.

- [ ] **Step 6: Compile and check the delta**

Run: `./compile.sh`
Expected: 0 errors (same as Step 1 baseline). Report the warning-count delta versus Step 1; it should be 0. If errors appear, fix them before continuing -- likely a mis-aligned column, a duplicate `W78`, or an unavailable SV name on this firmware (if `SV_ATC_CAROUSEL_POSITION` or `SV_PLC_CAROUSEL_POSITION` is rejected at compile, stop and report -- Phase B cannot proceed without them).

- [ ] **Step 7: Verify the additions and their placement**

Run: `grep -nE "CurrentBin_W|SV_PLC_CAROUSEL_POSITION|SV_ATC_CAROUSEL_POSITION" Centroid-Acroloc-ALLIN1DC.src`
Expected: the `IS W78` definition, the `InitialStage` seed, and the two `MainStage` report rungs -- four hits total, none inside `ATCStage`.

Run: `LC_ALL=C grep -nP '[^\x00-\x7F]' Centroid-Acroloc-ALLIN1DC.src || echo ASCII-clean`
Expected: `ASCII-clean`.

- [ ] **Step 8: Commit**

```bash
git add Centroid-Acroloc-ALLIN1DC.src
git commit -m "feat: report carousel bin to CNC12 for enhanced ATC (Phase B)

Adds CurrentBin_W (W78), seeded at power-up from SV_ATC_CAROUSEL_POSITION and
reported each scan via SV_PLC_CAROUSEL_POSITION. All additions are outside
ATCStage; the carousel search/decode/match logic is unchanged.

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

### Task 3: Documentation updates

Record that Enhanced ATC is enabled, what `SV_TOOL_NUMBER` now means, and the Phase A outcome. Always executed (Phase A alone still changes machine behavior).

**Files:**
- Modify: `docs/plc-spec/atc.md` (enhanced-ATC note + pinned commit hash; if Task 2 ran, the `CurrentBin_W` report)
- Modify: `.claude/skills/acroloc-s10/reference/atc-flow.md` (SV_TOOL_NUMBER-as-bin note)
- Modify: `.claude/skills/acroloc-s10/reference/atc.md` (bin-mapping under Tool numbering)

**Interfaces:**
- Consumes: the Task 1 recorded finding; if Task 2 ran, the `CurrentBin_W` / `SV_PLC_CAROUSEL_POSITION` names.
- Produces: docs consistent with the shipped behavior.

- [ ] **Step 1: Update the machine ATC reference**

In `.claude/skills/acroloc-s10/reference/atc.md`, under "Tool numbering," add:

```
## Tool-to-bin mapping (Enhanced ATC)

CNC12 runs in Enhanced ATC mode: the tool library's bin column maps a tool
number to a physical carousel bin, and M107 loads SV_TOOL_NUMBER with the
**bin**, not the tool number. So M6T31 with tool 31 -> bin 2 indexes the
carousel to bin 2. Tools 1-12 are assigned bins 1-12 (1:1, unchanged).
Machine parameter 161 (max bin) = 12.
```

- [ ] **Step 2: Update the ATC flow reference**

In `.claude/skills/acroloc-s10/reference/atc-flow.md`, at the `MainStage` kickoff description (the `IF M6_SV THEN ChangeToTool_W = SV_TOOL_NUMBER` line), append a note:

```
Under Enhanced ATC, SV_TOOL_NUMBER is the requested **carousel bin** (CNC12
maps tool->bin from the tool library), so ChangeToTool_W is a bin and the
carousel search is unchanged. If Phase B shipped, CurrentBin_W (W78) is
reported to CNC12 via SV_PLC_CAROUSEL_POSITION from MainStage (outside
ATCStage).
```

Remove the "If Phase B shipped" sentence if Task 2 was skipped.

- [ ] **Step 3: Update the pinned plc-spec section**

In `docs/plc-spec/atc.md`, add an "Enhanced ATC / tool-bin mapping" note describing the same behavior. If Task 2 ran, document `CurrentBin_W` (W78), the `InitialStage` seed, and the `MainStage` report rung, and **update the pinned commit hash** at the top of that section to the Task 2 commit. Fix any line references the Task 2 edit shifted; do not re-baseline unrelated ones.

- [ ] **Step 4: Verify docs are ASCII-clean and consistent**

Run:
```bash
LC_ALL=C grep -rnP '[^\x00-\x7F]' docs/plc-spec/atc.md .claude/skills/acroloc-s10/reference/atc.md .claude/skills/acroloc-s10/reference/atc-flow.md || echo ASCII-clean
grep -rniE "enhanced atc|bin" docs/plc-spec/atc.md .claude/skills/acroloc-s10/reference/atc.md
```
Expected: `ASCII-clean`; the enhanced-ATC notes appear.

- [ ] **Step 5: Commit**

```bash
git add docs/plc-spec/atc.md .claude/skills/acroloc-s10/reference/atc.md .claude/skills/acroloc-s10/reference/atc-flow.md
git commit -m "docs: enhanced ATC tool-to-bin mapping (atc spec + acroloc-s10 skill)

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

## Notes for the executor

- **Task ordering is gated, not linear.** Task 1 is on-machine and owner-run; its Step 3 finding decides whether Task 2 runs at all. Do not write any `.src` change until Task 1 records "Phase B required." Task 3 always runs.
- If Task 1 records "Phase A sufficient," the entire feature is Phase A + Task 3 docs (drop the Phase B sentences from the doc edits).
- There is no automated behavior test for the PLC. "Green" for Task 2 means `./compile.sh` clean with no new warnings; real behavior is verified on-machine by re-running the Task 1 Step 3 / Step 4 checks after loading the new `.plc`.
