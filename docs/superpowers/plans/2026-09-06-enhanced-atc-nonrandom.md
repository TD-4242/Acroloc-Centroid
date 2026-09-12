# Enhanced ATC Non-Random Mode (P160 = 1) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Move the Acroloc's fixed tool->bin map out of machine parameters P701-P712 and into CNC12's Tool Library Bin column by running non-random enhanced ATC (P160 = 1), with the PLC consuming the bin CNC12 sends and reporting its carousel position back.

**Architecture:** CNC12 at P160 = 1 sends the requested tool's **bin** in `SV_TOOL_NUMBER`, so the PLC's P701 lookup and twelve cached words are deleted; the M6 kickoff range-guards the bin (1..P161) with a new 9067 fault and hands it straight to the unchanged `ATCStage` search. Two new handshakes make CNC12 cooperate: the settled carousel bin is reported every scan via `SV_PLC_CAROUSEL_POSITION` (seeded at boot from `SV_ATC_CAROUSEL_POSITION`, zeroed on every abort), and M18 re-seeds it after the operator's F2 ATC Reset. Everything else (mfunc6 flow, VCP readout, 20 s watchdog) is unchanged.

**Tech Stack:** Centroid CNC12 (ALLIN1DC / MPU11) PLC stage language (`.src`) + M-code macros (`.mac`); `./compile.sh` (Wine `mpucomp`) is the only automated check; `tools/plcfmt.py` for style. Docs are Markdown. No pip; Python tooling is stdlib-only.

**Spec:** `docs/superpowers/specs/2026-09-06-enhanced-atc-nonrandom-design.md`

## Global Constraints

- Work in the worktree `.worktrees/enhanced-atc-nonrandom` on branch `feature/enhanced-atc-nonrandom` (already created from `main`). All paths below are relative to that worktree root. Do **not** touch the main checkout, which carries unrelated uncommitted edits.
- Controller source files (`.src`, `.mac`, `plcmsg.txt`, `cncm.hom`) must stay **plain 7-bit ASCII** and keep their existing line endings. `language.msg` is UTF-8 with LF: edit only `eng:` lines, never re-encode.
- Every PLC edit: run `./compile.sh` before committing. It must print `Compilation successful` with 0 errors. Report the warning count delta against the baseline (**190 warnings, 5040 tokens** at `main`).
- Every new or changed PLC line is tagged `; Acroloc`. Match the surrounding fixed-column style (`Name<spaces>IS Resource ; comment`, names padded to column 33).
- `docs/plc-spec/*.md` pin `src:NNNN` line references to commit 41f3fd6. **Never re-baseline them.** Fix false content; give lines added by this change **no** line reference.
- Current-state docs (`docs/plc-spec/`, `.claude/skills/`, `CLAUDE.md`, `README.md`) describe what the machine does **now**. Delete removed features outright; no "previously", "REMOVED", or "used to" tombstones. Historical specs under `docs/superpowers/specs/` may be annotated.
- New message constant value: `2 + 256 * 67 = 17154`. plcmsg slot 67 is free (60-66 and 70-73 are used).
- M-function bit 18 (`SV_M94_M95_18`) is free; bits 1-8 are in use.
- Commit after every task with the trailer:
  ```
  Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>
  Claude-Session: https://claude.ai/code/session_01JybVRnfYAPvLWhZWbL3DgN
  ```
- The repo `.gitignore` is a whitelist (`/*` ignore-all). After `git add`, always check `git status --short` shows every intended file staged; a silently ignored new file is the known failure mode. `mfunc*.mac`, `docs/`, `.claude/`, `plcmsg.txt`, `language.msg` are already whitelisted.

---

## File structure

| File | Responsibility in this change |
|---|---|
| `Centroid-Acroloc-ALLIN1DC.src` | PLC: definitions (Task 1), boot seed + P161 cache (Task 1), M6 kickoff guard + position report + M18 (Task 2), abort rungs zero the bin (Task 3) |
| `mfunc18.mac` (new) | ATC Reset macro: pulses M-function bit 18 (Task 4) |
| `mfunc6.mac` | comment only: M107 now sends a bin (Task 4) |
| `plcmsg.txt` | new fault line `67  9067 ATC BIN OUT OF RANGE` (Task 5) |
| `language.msg` | P701-P712 labels back to stock (Task 5) |
| `docs/control-pc-customizations.md` | drop the P701 label set; add the ATC parameter settings (Task 5) |
| `docs/testing/enhanced-atc-nonrandom-test.md` (new), `docs/testing/tool-bin-mapping-test.md` (delete) | owner's on-machine procedure (Task 6) |
| `CLAUDE.md`, `README.md` | top-level ATC description (Task 7) |
| `docs/plc-spec/{atc,main-stage,boot,definitions,parameters,faults-and-messages}.md` | pinned PLC spec, content corrected (Task 8) |
| `.claude/skills/acroloc-s10/{SKILL.md,reference/atc.md,reference/atc-flow.md,reference/macros.md}`, `.claude/skills/centroid-plc-programming/reference/system-variables.md` | skill knowledge base (Task 9; macros.md in Task 4) |
| `docs/superpowers/specs/2026-07-22-tool-bin-mapping-design.md` | historical annotation (Task 10) |

---

### Task 1: PLC definitions, boot seed, and P161 cache

**Files:**
- Modify: `Centroid-Acroloc-ALLIN1DC.src:1060-1066` (M-function SVs), `:1113-1128` (ATC words), `:1211-1212` (message constants), `:1319-1320` (InitialStage tail), `:1340-1355` (LoadParametersStage P701 block)

**Interfaces:**
- Produces (used by Tasks 2 and 3): `ReportedToolBin_W` (W78), `MaxToolBins_W` (W79), `M18_SV` (`SV_M94_M95_18`), `ATC_BIN_RANGE_MSG_C` (17154). Existing names kept: `CurrentToolBin_W` (W71), `TargetToolBin_W` (W72), `TargetToolBinDisp_W` (W8), `M6_SV`, `ATCSpin_T`, `ATC_SPIN_TIMEOUT_MS_C`.

- [ ] **Step 1: Baseline compile**

Run: `./compile.sh`
Expected: `Compilation successful`, `Program size: 5040 tokens`, `Warnings: 190`. Note these numbers.

- [ ] **Step 2: Add the M18 system variable**

In the M-function block (search `M6_SV                           IS SV_M94_M95_8`), the file currently reads:

```
M6_SV                           IS SV_M94_M95_8 ; Acroloc Tool change request
M8_SV                           IS SV_M94_M95_3 ; (Flood mode: coolant pump + flood valve)
M10_SV                          IS SV_M94_M95_4 ; Clamp
M7_SV                           IS SV_M94_M95_5 ; (Mist/wash mode: coolant pump only)
HomeSync_SV                     IS SV_M94_M95_6 ; Acroloc pulsed by cncm.hom (M94/6 .. M95/6) at machine zero to latch home encoder counts
;                                IS SV_M94_M95_7 ;
```

Insert after the `HomeSync_SV` line (before the commented `SV_M94_M95_7` placeholder):

```
M18_SV                          IS SV_M94_M95_18 ; Acroloc ATC Reset (mfunc18.mac, run by CNC12's F2 ATC Reset): re-seed the carousel bin from SV_ATC_CAROUSEL_POSITION
```

- [ ] **Step 3: Replace the twelve map words with the two new words**

The word block currently reads (search `ToolInBin1_W`):

```
CurrentToolBin_W                IS W71 ; Acroloc
TargetToolBin_W                 IS W72 ; Acroloc
TargetToolBinDisp_W             IS W8  ; Acroloc last chosen carousel bin, held for the retro VCP live BIN readout (plc_word 8)
ToolInBin1_W                    IS W78 ; Acroloc bin 1 loaded tool number (from P701; fixed tool-bin map)
ToolInBin2_W                    IS W79 ; Acroloc bin 2 loaded tool number (P702)
ToolInBin3_W                    IS W80 ; Acroloc bin 3 loaded tool number (P703)
ToolInBin4_W                    IS W81 ; Acroloc bin 4 loaded tool number (P704)
ToolInBin5_W                    IS W82 ; Acroloc bin 5 loaded tool number (P705)
ToolInBin6_W                    IS W83 ; Acroloc bin 6 loaded tool number (P706)
ToolInBin7_W                    IS W84 ; Acroloc bin 7 loaded tool number (P707)
ToolInBin8_W                    IS W85 ; Acroloc bin 8 loaded tool number (P708)
ToolInBin9_W                    IS W86 ; Acroloc bin 9 loaded tool number (P709)
ToolInBin10_W                   IS W87 ; Acroloc bin 10 loaded tool number (P710)
ToolInBin11_W                   IS W88 ; Acroloc bin 11 loaded tool number (P711)
ToolInBin12_W                   IS W89 ; Acroloc bin 12 loaded tool number (P712)
InstBinID_W                     IS W75 ; Acroloc instantaneous position-switch sum; per-group peak latched into CurrentToolBin_W
```

Replace the twelve `ToolInBin` lines with exactly these two lines (keep the three lines above and the `InstBinID_W` line below):

```
ReportedToolBin_W               IS W78 ; Acroloc settled carousel bin reported to CNC12 via SV_PLC_CAROUSEL_POSITION (enhanced ATC handshake); 0 = unknown
MaxToolBins_W                   IS W79 ; Acroloc P161 (ATC Maximum Tool Bins) cached every scan; upper bound of the M6 bin guard
```

Also update the two comment lines that describe the map words' role: `CurrentToolBin_W` and `TargetToolBin_W` keep `; Acroloc` as-is (no change needed).

- [ ] **Step 4: Add the fault message constant**

After the line `CAROUSEL_TIMEOUT_MSG_C          IS 16130 ; (2+256*63) CAROUSEL MOVE TIME OUT` insert:

```
ATC_BIN_RANGE_MSG_C             IS 17154 ; (2+256*67) ATC BIN OUT OF RANGE -- Acroloc: CNC12 sent a bin outside 1..P161 at M6 kickoff
```

- [ ] **Step 5: Seed the carousel bin at boot**

In `InitialStage` the rung currently ends:

```
             SpindleRange_W = 1,       ; Acroloc safe default ratio until first engage
             RST InitialStage
```

Change to:

```
             SpindleRange_W = 1,       ; Acroloc safe default ratio until first engage
             CurrentToolBin_W = SV_ATC_CAROUSEL_POSITION, ; Acroloc enhanced ATC: seed the last known bin CNC12 persisted (cncm.job)
             RST InitialStage
```

- [ ] **Step 6: Replace the P701 cache block with the P161 cache**

In `LoadParametersStage`, delete this entire block (comment lines included):

```
; Acroloc -- fixed tool->bin map: P701-712 = the tool number loaded in bins 1-12.
; Re-read every scan here, so editing a bin's tool on the parameter screen takes
; effect without a reboot. The M6 kickoff (MainStage) looks the requested tool up
; in these to pick the carousel bin.
IF True_M THEN ToolInBin1_W  = SV_MACHINE_PARAMETER_701,  ; Acroloc
               ToolInBin2_W  = SV_MACHINE_PARAMETER_702,  ; Acroloc
               ToolInBin3_W  = SV_MACHINE_PARAMETER_703,  ; Acroloc
               ToolInBin4_W  = SV_MACHINE_PARAMETER_704,  ; Acroloc
               ToolInBin5_W  = SV_MACHINE_PARAMETER_705,  ; Acroloc
               ToolInBin6_W  = SV_MACHINE_PARAMETER_706,  ; Acroloc
               ToolInBin7_W  = SV_MACHINE_PARAMETER_707,  ; Acroloc
               ToolInBin8_W  = SV_MACHINE_PARAMETER_708,  ; Acroloc
               ToolInBin9_W  = SV_MACHINE_PARAMETER_709,  ; Acroloc
               ToolInBin10_W = SV_MACHINE_PARAMETER_710,  ; Acroloc
               ToolInBin11_W = SV_MACHINE_PARAMETER_711,  ; Acroloc
               ToolInBin12_W = SV_MACHINE_PARAMETER_712   ; Acroloc
```

and put in its place:

```
; Acroloc -- enhanced ATC (P160=1): P161 = number of carousel bins. Re-read every
; scan; the M6 kickoff (MainStage) rejects any bin CNC12 sends outside 1..P161.
IF True_M THEN MaxToolBins_W = SV_MACHINE_PARAMETER_161  ; Acroloc
```

- [ ] **Step 7: Compile**

Run: `./compile.sh`
Expected: `Compilation successful`, 0 errors. Compile will report the new words as defined-but-unused until Task 2; that is fine. Record the warning count and token count.

Run: `grep -nE "ToolInBin|SV_MACHINE_PARAMETER_7(0[1-9]|1[0-2])" Centroid-Acroloc-ALLIN1DC.src`
Expected: no output.

Run: `grep -nE "ReportedToolBin_W|MaxToolBins_W|M18_SV|ATC_BIN_RANGE_MSG_C|SV_ATC_CAROUSEL_POSITION" Centroid-Acroloc-ALLIN1DC.src`
Expected: 6 lines (four definitions, the InitialStage seed, the P161 cache).

Run: `LC_ALL=C grep -nP '[^\x00-\x7F]' Centroid-Acroloc-ALLIN1DC.src`
Expected: no output (still ASCII).

- [ ] **Step 8: Commit**

```bash
git add Centroid-Acroloc-ALLIN1DC.src
git status --short
git commit -m "plc: enhanced ATC definitions, boot seed, P161 cache; drop the P701-712 map words

CNC12 at P160=1 sends the requested tool's bin, so the twelve ToolInBin words
and their P701-712 reads go. Adds ReportedToolBin_W (W78), MaxToolBins_W (W79,
from P161), M18_SV (bit 18) and the 9067 ATC BIN OUT OF RANGE constant, and
seeds CurrentToolBin_W from SV_ATC_CAROUSEL_POSITION at power-up.

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>
Claude-Session: https://claude.ai/code/session_01JybVRnfYAPvLWhZWbL3DgN"
```

---

### Task 2: M6 kickoff guard, position report, and M18 reset (`MainStage`)

**Files:**
- Modify: `Centroid-Acroloc-ALLIN1DC.src:2957-2983` (the `; Acroloc tool stage start` block)

**Interfaces:**
- Consumes: Task 1 names (`ReportedToolBin_W`, `MaxToolBins_W`, `M18_SV`, `ATC_BIN_RANGE_MSG_C`).
- Produces: `SV_PLC_CAROUSEL_POSITION` written every scan; `TargetToolBin_W` = the bin CNC12 sent; `ATCStage` armed only for a bin in range.

- [ ] **Step 1: Replace the kickoff block**

The block currently reads exactly:

```
; Acroloc tool stage start
; Acroloc: once per change (before SET ATCStage below, so !ATCStage is true only on the
; first scan): arm the carousel search watchdog, AND clear CurrentToolBin_W so a stale
; value from the previous change cannot cause an immediate match -- the carousel always
; re-indexes to the requested tool, even the same tool (a manual change may have left the
; wrong tool under the spindle).
IF M6_SV && !ATCStage THEN ATCSpin_T = ATC_SPIN_TIMEOUT_MS_C, SET ATCSpin_T, CurrentToolBin_W = 0
; Acroloc -- fixed tool->bin map: translate the requested TOOL number to its BIN.
; ToolInBin1_W..ToolInBin12_W hold the tool loaded in each bin (from P701-712). Set
; TargetToolBin_W to the bin whose loaded tool == SV_TOOL_NUMBER. Default 99 (an
; unreachable bin) so a tool that is in no bin never matches and faults on the
; 20 s ATCSpin_T watchdog instead of false-matching bin 0 and completing without
; moving. ATCStage then indexes the carousel to TargetToolBin_W exactly as before.
IF M6_SV THEN TargetToolBin_W = 99
IF M6_SV && ToolInBin1_W  == SV_TOOL_NUMBER THEN TargetToolBin_W = 1
IF M6_SV && ToolInBin2_W  == SV_TOOL_NUMBER THEN TargetToolBin_W = 2
IF M6_SV && ToolInBin3_W  == SV_TOOL_NUMBER THEN TargetToolBin_W = 3
IF M6_SV && ToolInBin4_W  == SV_TOOL_NUMBER THEN TargetToolBin_W = 4
IF M6_SV && ToolInBin5_W  == SV_TOOL_NUMBER THEN TargetToolBin_W = 5
IF M6_SV && ToolInBin6_W  == SV_TOOL_NUMBER THEN TargetToolBin_W = 6
IF M6_SV && ToolInBin7_W  == SV_TOOL_NUMBER THEN TargetToolBin_W = 7
IF M6_SV && ToolInBin8_W  == SV_TOOL_NUMBER THEN TargetToolBin_W = 8
IF M6_SV && ToolInBin9_W  == SV_TOOL_NUMBER THEN TargetToolBin_W = 9
IF M6_SV && ToolInBin10_W == SV_TOOL_NUMBER THEN TargetToolBin_W = 10
IF M6_SV && ToolInBin11_W == SV_TOOL_NUMBER THEN TargetToolBin_W = 11
IF M6_SV && ToolInBin12_W == SV_TOOL_NUMBER THEN TargetToolBin_W = 12
IF M6_SV THEN TargetToolBinDisp_W = TargetToolBin_W, SET ATCStage  ; Acroloc hold chosen bin for the VCP BIN readout
```

Replace the whole block (from `; Acroloc tool stage start` through the `SET ATCStage` line) with:

```
; Acroloc tool stage start
; Acroloc: once per change (before SET ATCStage below, so !ATCStage is true only on the
; first scan): arm the carousel search watchdog, AND clear CurrentToolBin_W so a stale
; value from the previous change cannot cause an immediate match -- the carousel always
; re-indexes to the requested bin.
IF M6_SV && !ATCStage THEN ATCSpin_T = ATC_SPIN_TIMEOUT_MS_C, SET ATCSpin_T, CurrentToolBin_W = 0
; Acroloc -- enhanced ATC (P160=1): CNC12 looks the requested tool up in its Tool
; Library and M107 sends that tool's BIN in SV_TOOL_NUMBER. Guard it: anything
; outside 1..P161 (an unassigned tool, a bad library, P161 unset) faults here and
; never starts the carousel. The 9xxx fault cancels the job during mfunc6's G4 P1
; dwell, so CNC12 does not record the change as complete.
IF M6_SV && !ATCStage && (SV_TOOL_NUMBER < 1 || SV_TOOL_NUMBER > MaxToolBins_W) THEN
  FaultMsg_W = ATC_BIN_RANGE_MSG_C,
  SET ShowFaultStage,
  SET OtherFault_M,
  RST M6_SV,
  RST ATCSpin_T,
  TargetToolBinDisp_W = SV_TOOL_NUMBER
; Bin in range: latch it as the search target and arm ATCStage (its search/decode/
; match logic is unchanged). TargetToolBinDisp_W feeds the retro VCP TOOL BIN readout.
IF M6_SV && !ATCStage THEN
  TargetToolBin_W = SV_TOOL_NUMBER,
  TargetToolBinDisp_W = SV_TOOL_NUMBER,
  SET ATCStage

; Acroloc -- enhanced ATC handshake: report the SETTLED carousel bin to CNC12.
; Latched only while no change is running, so mid-spin partial sums never reach
; CNC12. CNC12 records this value as the new tool's putback bin at the end of M6,
; so it must be right the moment ATCStage clears -- and it is: the match rung
; leaves CurrentToolBin_W = the matched bin, and every abort path zeroes it.
; 0 is reported honestly whenever the bin is unknown.
IF !ATCStage THEN ReportedToolBin_W = CurrentToolBin_W
IF True_M THEN SV_PLC_CAROUSEL_POSITION = ReportedToolBin_W

; Acroloc -- enhanced ATC reset: CNC12's F2 ATC Reset (P164=1) sends the operator-
; entered carousel position in SV_ATC_CAROUSEL_POSITION and then runs mfunc18.mac,
; which pulses M18_SV. Re-seed the known bin from it.
IF M18_SV && !ATCStage THEN CurrentToolBin_W = SV_ATC_CAROUSEL_POSITION
```

Leave the `; Acroloc manual tool changes` block that follows untouched.

- [ ] **Step 2: Compile and check the rung order**

Run: `./compile.sh`
Expected: `Compilation successful`, 0 errors. Record warnings/tokens.

Run: `grep -nE "ATC_BIN_RANGE_MSG_C|SV_PLC_CAROUSEL_POSITION|ReportedToolBin_W = CurrentToolBin_W|M18_SV && !ATCStage|TargetToolBin_W = SV_TOOL_NUMBER|TargetToolBin_W = 99" Centroid-Acroloc-ALLIN1DC.src`
Expected: the guard, the report pair, the M18 rung and the kickoff latch each appear once inside `MainStage`; `TargetToolBin_W = 99` appears nowhere.

Run: `grep -cE "^[^;]*SV_TOOL_NUMBER" Centroid-Acroloc-ALLIN1DC.src`
Expected: `4` code lines (the guard condition, the guard's `TargetToolBinDisp_W = SV_TOOL_NUMBER`, and the two latch lines; comment-only mentions are excluded by the pattern). If the count is higher, a P701 compare rung survived; remove it.

- [ ] **Step 3: Style check**

Run: `python3 tools/plcfmt.py --check Centroid-Acroloc-ALLIN1DC.src; echo exit=$?`
Expected: `exit=0`. If `exit=1`, the printed diff shows the alignment it wants; apply it by hand (do not run `--fix` mid-task) and re-run until `exit=0`.

- [ ] **Step 4: Commit**

```bash
git add Centroid-Acroloc-ALLIN1DC.src
git status --short
git commit -m "plc: M6 takes the bin CNC12 sends; range guard, position report, M18 reset

At P160=1 SV_TOOL_NUMBER is the requested tool's bin (M107 sends it), so the
kickoff latches it straight into TargetToolBin_W after a 1..P161 guard that
faults ATC BIN OUT OF RANGE (9067). The settled bin is reported every scan via
SV_PLC_CAROUSEL_POSITION (0 = unknown), and M18 (F2 ATC Reset) re-seeds
CurrentToolBin_W from SV_ATC_CAROUSEL_POSITION.

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>
Claude-Session: https://claude.ai/code/session_01JybVRnfYAPvLWhZWbL3DgN"
```

---

### Task 3: Abort paths zero the known bin (`ATCStage`)

**Files:**
- Modify: `Centroid-Acroloc-ALLIN1DC.src` `ATCStage` fault rungs (search `IF ATCStage && !ZeroSpeed_I THEN`, `IF !ATC_Z_Zero_Release_I THEN`, `IF ATCStage && ATCSpin_T THEN`)

**Interfaces:**
- Consumes: `CurrentToolBin_W`; the report rung from Task 2 picks up the 0 on the next scan.

- [ ] **Step 1: Add `CurrentToolBin_W = 0` to each of the three abort rungs**

Each rung currently has the line `TargetToolBin_W = 0,`. Insert `CurrentToolBin_W = 0,` directly after it in all three rungs, so the spindle-not-stopped rung becomes:

```
IF ATCStage && !ZeroSpeed_I THEN
  FaultMsg_W = SPINDLE_FAULT_MSG_C,
  SET ShowFaultStage,
  SET OtherFault_M,
  RST ATCMotor_O,
  RST ATCUnlocked_O,
  RST M6_SV,
  TargetToolBin_W = 0,
  CurrentToolBin_W = 0,   ; Acroloc enhanced ATC: aborted mid-decode -> bin unknown, report 0 not a partial peak
  RST ATCSpin_T,
  RST ATCStage
```

Apply the identical insertion (same comment) to the `IF !ATC_Z_Zero_Release_I THEN` rung and the `IF ATCStage && ATCSpin_T THEN` rung. Do not touch the match rung (`IF !InBinDecode_M && CurrentToolBin_W == TargetToolBin_W THEN`), which must keep `CurrentToolBin_W` at the matched bin.

- [ ] **Step 2: Compile and verify**

Run: `./compile.sh`
Expected: `Compilation successful`, 0 errors. Record the final warning count and token count; report the delta from the 190 / 5040 baseline in the commit body.

Run: `grep -c "CurrentToolBin_W = 0" Centroid-Acroloc-ALLIN1DC.src`
Expected: `6` (kickoff arm, manual unlock, decode leading edge, three abort rungs).

Run: `python3 tools/plcfmt.py --check Centroid-Acroloc-ALLIN1DC.src; echo exit=$?`
Expected: `exit=0`.

Run: `LC_ALL=C grep -nP '[^\x00-\x7F]' Centroid-Acroloc-ALLIN1DC.src`
Expected: no output.

- [ ] **Step 3: Commit**

```bash
git add Centroid-Acroloc-ALLIN1DC.src
git status --short
git commit -m "plc: ATCStage aborts zero CurrentToolBin_W so CNC12 is told 0, not a partial peak

Compile: <fill in> warnings (baseline 190), <fill in> tokens (baseline 5040), 0 errors.

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>
Claude-Session: https://claude.ai/code/session_01JybVRnfYAPvLWhZWbL3DgN"
```

---

### Task 4: Macros: new `mfunc18.mac`, `mfunc6.mac` comment, macros.md

**Files:**
- Create: `mfunc18.mac`
- Modify: `mfunc6.mac` (one comment), `.claude/skills/acroloc-s10/reference/macros.md`

**Interfaces:**
- Produces: `mfunc18.mac` pulses `M94 /18` / `M95 /18`, which Task 2's rung consumes as `M18_SV`.

- [ ] **Step 1: Create `mfunc18.mac`** (ASCII, CRLF like the other macros: check with `file mfunc6.mac`; if it says `with CRLF line terminators`, write CRLF)

```
;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;
; File: mfunc18.mac
; Desc: ATC Reset (enhanced ATC, P160=1)
;
; Run by CNC12's F2 ATC Reset (Tool Library, P164=1) after the operator has
; entered the carousel position, the tool in the spindle and its putback bin.
; CNC12 has already sent the position in SV_ATC_CAROUSEL_POSITION; pulsing
; M18_SV (bit 18) tells the PLC to re-seed CurrentToolBin_W from it.
; Do not run M18 from MDI.
;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;

;Skip if graphing or searching
IF #4201 || #4202 THEN GOTO 1000

M94 /18         ; Set M18_SV: PLC re-seeds the carousel bin from CNC12
G4 P1           ; hold the request one second
M95 /18         ; Reset M18_SV

N1000           ; end of program
```

Run: `file mfunc18.mac mfunc6.mac` and confirm both report the same line-terminator style. Run: `LC_ALL=C grep -nP '[^\x00-\x7F]' mfunc18.mac` — expect no output.

- [ ] **Step 2: Fix the `mfunc6.mac` comment**

Change the line

```
M107            ; Send tool number 
```

to

```
M107            ; Send the requested tool's BIN (enhanced ATC, P160=1: CNC12 looks it up in the Tool Library)
```

Nothing else in `mfunc6.mac` changes.

- [ ] **Step 3: Update `macros.md`**

In the macro summary table, after the `mfunc11` row add:

```
| `mfunc18`  | M18      | ATC Reset (enhanced ATC): pulses `M94 /18` / `M95 /18` so the PLC re-seeds the carousel bin from `SV_ATC_CAROUSEL_POSITION`. Run by CNC12's F2 ATC Reset in the Tool Library (P164 = 1); never from MDI |
```

Change the sentence "All seven macros skip execution in graph/search mode" to "All eight macros skip execution in graph/search mode", and "functionally identical to the other six macros" to "functionally identical to the other seven macros".

In "mfunc6 key steps", change step 5 from

```
5. `M107` — send target tool number to PLC
```

to

```
5. `M107` — send the requested tool's **bin** to the PLC (`SV_TOOL_NUMBER`; at P160 = 1 CNC12 looks the bin up in the Tool Library)
```

- [ ] **Step 4: Verify and commit**

Run: `git add mfunc18.mac mfunc6.mac .claude/skills/acroloc-s10/reference/macros.md && git status --short`
Expected: all three listed as staged (`A  mfunc18.mac`, `M  mfunc6.mac`, `M  .claude/...macros.md`). If `mfunc18.mac` is missing, the whitelist gitignore skipped it: check `git check-ignore -v mfunc18.mac` and add an un-ignore line to `.gitignore` next to the existing `mfunc*` entry.

```bash
git commit -m "macros: mfunc18.mac for CNC12's ATC Reset; mfunc6 M107 comment now says bin

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>
Claude-Session: https://claude.ai/code/session_01JybVRnfYAPvLWhZWbL3DgN"
```

---

### Task 5: Control-PC files: `plcmsg.txt`, `language.msg`, customization doc

**Files:**
- Modify: `plcmsg.txt` (after line 46 `66  9066 ORIENT TIMEOUT`), `language.msg` (24 `eng:` lines for P701-P712), `docs/control-pc-customizations.md`

- [ ] **Step 1: Add the fault message**

`plcmsg.txt` lines 44-47 currently read:

```
63  9063 CAROUSEL MOVE TIME OUT
64  9064 TOOL CLAMP UNCLAMP FAULT
65  9065 ORIENT LOST FAULT
66  9066 ORIENT TIMEOUT
```

Insert after the `66` line:

```
67  9067 ATC BIN OUT OF RANGE
```

Match the file's line endings (`file plcmsg.txt`). Run: `grep -n "^67 " plcmsg.txt` — expect exactly one line.

- [ ] **Step 2: Revert the P701-P712 labels to stock with a stdlib script**

Run this from the worktree root (it edits only the 24 `eng:` lines, preserves the BOM, UTF-8 and LF):

```bash
python3 - <<'EOF'
import re, io
p = "language.msg"
raw = open(p, "rb").read()
text = raw.decode("utf-8")           # keeps a leading BOM as U+FEFF
stock = 'Reserved for Enduser/Integrator custom PLC and Macro use'
pat = re.compile(r'^( eng: @P7(?:0[1-9]|1[0-2])_LABEL(?:_L)? = )"[^"\n]*"$', re.M)
new, n = pat.subn(lambda m: m.group(1) + '"' + stock + '"', text)
assert n == 24, n
assert "\r\n" not in new
open(p, "wb").write(new.encode("utf-8"))
print("replaced", n)
EOF
```

Expected: `replaced 24`.

Run: `git diff --stat language.msg` — expect `1 file changed, 24 insertions(+), 24 deletions(-)`.
Run: `git diff language.msg | grep -c '^+ eng: @P7'` — expect `24`.
Run: `grep -c 'Acroloc tool->bin map' language.msg` — expect `0`.
Run: `head -c 3 language.msg | xxd | head -1` and compare with `git show HEAD:language.msg | head -c 3 | xxd | head -1` — the bytes must be identical (BOM preserved or absent, same as before).

- [ ] **Step 3: Update `docs/control-pc-customizations.md`**

Replace the `language.msg` row of the "Customized files" table with:

```
| `language.msg` | Parameter-screen labels: **P860-P863** (gear shift). Everything else is the stock baseline. | `dfab98c` (P860-863 + baseline) | P860-P863 read "Not Used". | **Re-apply the label set onto the upgraded file** (don't overwrite it wholesale). See "language.msg" below. |
```

Replace the `plcmsg.txt` row's commit list with `` `e1ab3c5` (add), `4c329ee` (feed-hold interlock msgs), `96ccf68` (ATC timeout), this branch (ATC BIN OUT OF RANGE) `` and keep the rest of the row.

In the "### `language.msg`" details section, replace the two-item "**Two customizations here**" list with:

```
- **One customization here** (everything else is the stock baseline):
  - **P860-P863** (gear shift, commit `dfab98c`) -- CNC12 shows the 860-870 block as "Not
    Used", so these were named: `Gear Crossover RPM`, `Gear Crossover Hysteresis`,
    `Gear Shift Coast Dwell ms`, `High Gear Ratio`.
- **Restore after upgrade:** keep the upgraded `language.msg` and re-apply the label set.
  The exact before/after is in `git show dfab98c -- language.msg`; target the `eng:` line
  for each `@P<n>_LABEL` / `_L` and preserve UTF-8 + LF.
```

In the "### `plcmsg.txt`" details, change the `60-66:` bullet to `60-67:` and append `, **ATC BIN OUT OF RANGE** (67)` after `tool clamp/orient faults`.

Add a new section before "## After-upgrade checklist":

```
### Machine parameters for the ATC (not a file, but reset by a re-install)

The tool changer runs CNC12's **non-random enhanced ATC**. These must be set on the
Machine Parameters screen (F1 Setup > F3 Config > F3 Parms); a CNC12 re-install or a
parameter-file restore from an old backup reverts them:

| Param | Value | Why |
|---|---|---|
| P6 | 1 | ATC installed; on-screen tool updates after M6 |
| P160 | 1 | non-random enhanced ATC: M107 sends the bin, Tool Library Bin column editable |
| P161 | 12 | number of carousel bins; the PLC's M6 bin guard limit. **Reboot after changing** |
| P164 | 1 | F2 ATC Reset key in the Tool Library |

The tool->bin map itself lives in the **Tool Library Bin column** (F1 Setup > F2 Tool >
F2 Tool Lib), saved by CNC12 in its tool library file, and is not tracked in this repo.
Export it (F5 Export Lib) after changes so it can be restored.
```

In the "After-upgrade checklist", replace the `language.msg` line with `- [ ] `language.msg`: re-apply the P860-P863 label edits onto the upgraded file.`, change `(60-66, 70-73, 101-110, 171-174)` to `(60-67, 70-73, 101-110, 171-174)`, replace `- [ ] Parameters screen: P701-P712 show the ATC bin labels (not "Reserved...").` with `- [ ] Parameters screen: P860-P863 show the gear-shift labels; P6 = 1, P160 = 1, P161 = 12, P164 = 1.`, and add `- [ ] Tool Library: Bin column editable and matches the carousel (re-import the exported library if not).`

- [ ] **Step 4: Verify and commit**

Run: `grep -nE "P70[1-9]|P71[0-2]|75c2acb" docs/control-pc-customizations.md`
Expected: no output.

```bash
git add plcmsg.txt language.msg docs/control-pc-customizations.md
git status --short
git commit -m "control-pc: 9067 ATC BIN OUT OF RANGE message; P701-712 labels back to stock; ATC params documented

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>
Claude-Session: https://claude.ai/code/session_01JybVRnfYAPvLWhZWbL3DgN"
```

---

### Task 6: On-machine test procedure

**Files:**
- Create: `docs/testing/enhanced-atc-nonrandom-test.md`
- Delete: `docs/testing/tool-bin-mapping-test.md`

- [ ] **Step 1: Write the new procedure**

```markdown
# Enhanced ATC (non-random, P160 = 1) - On-Machine Test Procedure

Covers the Tool Library bin map, the PLC position report, the bin range guard,
the VCP `TOOL BIN` readout, and F2 ATC Reset. Phases are gated: stop at the first
failing step and record what happened. Rollback is at the end.

Spec: `docs/superpowers/specs/2026-09-06-enhanced-atc-nonrandom-design.md`.

## 0. Record the starting state

- [ ] Machine parameters screen (F1 Setup > F3 Config > F3 Parms): write down the
      current values of **P6, P160, P161, P164**. (Expected before this change:
      P160 = 0.)
- [ ] Tool Library (F1 Setup > F2 Tool > F2 Tool Lib): note that the Bin column
      shows "Bin fields are locked".

## 1. Deploy (control PC)

- [ ] Copy `Centroid-Acroloc-ALLIN1DC.src`; compile/reload the `.plc` in CNC12
      (expect: compiles, no errors).
- [ ] Copy `mfunc6.mac` and `mfunc18.mac` into the CNC12 macro directory.
- [ ] Copy `plcmsg.txt` and `language.msg` over the control-PC copies.
- [ ] Set **P6 = 1, P160 = 1, P161 = 12, P164 = 1**. CNC12 warns that enhanced ATC
      needs a matching PLC program: accept.
- [ ] **Reboot CNC12** (P161 is sent to the PLC at power-up; macros and messages
      reload).

## 2. Phase A - handshake and identity loadout

- [ ] Home the machine.
- [ ] Tool Library: the Bin column is now editable and F1 Clear Bin / F2 Clear All
      appear. Set tools 1-12 to bins 1-12 (if CNC12 has not already initialised
      them that way). Set the tool that is physically under the spindle to bin
      **0**. F10 Save.
- [ ] **ALT+K** shows `ATC BIN n` where n is the bin under the spindle (the PLC's
      boot seed from CNC12; may read 0 the first time - that is allowed).
- [ ] MDI `M6T5` -> carousel indexes to **bin 5**, tool changes normally.
      `TOOL BIN` reads **5**; ALT+K reads 5; the status window shows **T5** after
      the change.
- [ ] Tool Library: tool 5's Bin now reads **0** (in spindle); the previous
      tool's Bin is back to its own number.
- [ ] MDI `M6T5` again -> **nothing happens** (CNC12 skips a change to the tool
      already in the spindle).
- [ ] MDI `M6T12` then `M6T1` -> bins 12 and 1; readout and ALT+K track; Bin
      column tracks (0 for the in-spindle tool, own bin for the rest).
- [ ] Interrupt: MDI `M6T7`, press **Escape** during the carousel move. Then MDI
      anything (e.g. `G4 P1`): CNC12 must prompt that the last tool change did not
      complete; answer **Y**. Check the Bin column and fix it by hand or with F6 ATC
      Reset (section 4) so it matches the carousel.

## 3. Phase B - the feature: arbitrary tool -> bin, and an unassigned tool

- [ ] Tool Library: tool 2 -> F1 Clear Bin (dashes). Tool **31** -> Bin **2**.
      F10 Save.
- [ ] MDI `M6T31` -> carousel indexes to **bin 2**; `TOOL BIN` reads 2; status
      shows T31; tool 31's Bin reads 0.
- [ ] MDI `M6T1` -> tool 31's Bin returns to **2** (not 0, not another bin).
- [ ] Unassigned tool: MDI `M6T2` (tool 2 has dashes). Record exactly what
      happens - one of:
      - CNC12 refuses the M6 with its own message (record the text), or
      - the PLC faults **`9067 ATC BIN OUT OF RANGE`** immediately, the job
        cancels, and the next MDI prompts about the incomplete change (answer Y), or
      - the carousel moves to some bin (record which; this means M107 sent a
        number in 1..12 for an unassigned tool and the guard needs a follow-up).
- [ ] Restore: tool 31 -> dashes, tool 2 -> Bin 2, F10 Save.

## 4. Phase C - manual unlock and F2 ATC Reset

- [ ] Z at the tool-change position (clear). Press the **manual unlock** button
      (`ATCManualUnlock_I`, INP24). `TOOL BIN` drops to **0**; ALT+K reads 0.
- [ ] Hand-spin the carousel **two bins forward**, release the button (relock).
      Note the bin now under the spindle (n) and the tool in it.
- [ ] Tool Library > **F2 ATC Reset**: carousel position = n (the default offered
      will be 0; type n), tool in spindle = the tool in bin n, putback = n. Confirm
      with Y. Expect the message `ATC INITIALIZED` or similar; if CNC12 refuses,
      record the text (open question 2 in the spec) and instead edit the Bin
      column by hand.
- [ ] ALT+K now reads n. The Bin column shows that tool at 0 and the previously
      "in spindle" tool back in its own bin.
- [ ] MDI `M6T<m>` for a tool in another bin -> lands on the right bin, readout
      correct.

## 5. Readout appearance

- [ ] `TOOL BIN` still renders as before next to the spindle readout (this change
      did not touch the VCP).

## 6. Rollback (if any phase fails and the machine is needed)

- [ ] Set **P160 = 0** and P6 back to the value recorded in section 0. Same
      `.plc` stays loaded: `SV_TOOL_NUMBER` is then the tool number, which equals
      the bin for tools 1-12, so `M6T1..T12` keep working. Tools above 12 are
      unavailable until the branch is fixed or reverted.
- [ ] Full rollback: reload the previous `.plc`, `mfunc6.mac`, `plcmsg.txt`,
      `language.msg` from `main`, set P701-P712, P160 = 0.

## Report back

Record, for the spec's open questions: (1) what the unassigned-tool M6 did,
(2) whether F2 ATC Reset worked, (3) any CNC12 complaint about a reported bin
of 0, (4) whether the incomplete-change prompt appeared after the 9067 fault.
```

- [ ] **Step 2: Delete the old procedure and commit**

```bash
git rm docs/testing/tool-bin-mapping-test.md
git add docs/testing/enhanced-atc-nonrandom-test.md
git status --short
git commit -m "docs(testing): enhanced ATC non-random on-machine procedure replaces the P701 map test

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>
Claude-Session: https://claude.ai/code/session_01JybVRnfYAPvLWhZWbL3DgN"
```

---

### Task 7: `CLAUDE.md` and `README.md`

**Files:**
- Modify: `CLAUDE.md:29`, `CLAUDE.md:85-108`; `README.md:84-90`

- [ ] **Step 1: `CLAUDE.md` line 29** - change `(parameter/UI labels: P860-863 gear shift, P701-712 ATC tool->bin map)` to `(parameter/UI labels: P860-863 gear shift)`.

- [ ] **Step 2: `CLAUDE.md` ATC flow step 2** - replace the whole numbered item 2 with:

```
2. `MainStage` sees `M6_SV`. The machine runs CNC12's **non-random enhanced ATC**
   (`P160 = 1`, `P161 = 12`, `P6 = 1`, `P164 = 1`): the operator assigns each tool a
   carousel bin in the **Tool Library Bin column**, and `M107` sends that **bin**, not the
   tool number, in `SV_TOOL_NUMBER`. `MainStage` range-guards it (1..`P161`, cached in
   `MaxToolBins_W`; anything else faults `9067 ATC BIN OUT OF RANGE` and never starts the
   carousel), latches it into `TargetToolBin_W`, then `SET ATCStage`. While Z has not
   cleared the tool changer (`ATC_Z_ClearedToolChanger_I` low) it drops spindle enable;
   `ATCStage` posts the "spindle not parked" fault.
```

- [ ] **Step 3: `CLAUDE.md` naming rule paragraph** - replace

```
**Naming rule:** anything `...ToolBin...` holds a **carousel bin**; `ToolInBinN_W` holds a
**tool number**. CNC12's own enhanced-ATC modes are deliberately unused (`P160 = 0`) — they
either reshuffle the map (random) or force tool == bin (non-random).
```

with

```
**Naming rule:** anything `...ToolBin...` holds a **carousel bin**. Tool numbers never reach
the PLC; CNC12 owns the tool->bin map. **CNC12 handshake:** the PLC reports the settled bin
every scan in `SV_PLC_CAROUSEL_POSITION` (`ReportedToolBin_W`, 0 = unknown) — CNC12 will not
run a change without it and records it as the new tool's putback bin at the end of M6 — and
seeds `CurrentToolBin_W` from `SV_ATC_CAROUSEL_POSITION` at boot and on `M18` (`mfunc18.mac`,
run by the Tool Library's F2 ATC Reset). Random mode (`P160 = 2`) is wrong for this
fixed-pocket carousel: it reshuffles bins after every change.
```

- [ ] **Step 4: `CLAUDE.md` I/O list** - change `` `W78-W89` (`ToolInBin1_W..12_W`) `` to `` `W78` (`ReportedToolBin_W`), `W79` (`MaxToolBins_W`, P161) ``.

- [ ] **Step 5: `README.md`** - replace the "**Tool-to-bin mapping.**" paragraph (lines 84-90) with:

```
**Tool-to-bin mapping.** Tool numbers are decoupled from bins, so a tool numbered above the 12
physical bins can be used. The map lives in CNC12's **Tool Library Bin column** (non-random
enhanced ATC, `P160 = 1`): `M107` sends the requested tool's bin to the PLC, which
range-guards it and indexes the carousel, and reports its settled position back so CNC12 can
keep the library's bin fields current. See
[`docs/superpowers/specs/2026-09-06-enhanced-atc-nonrandom-design.md`](docs/superpowers/specs/2026-09-06-enhanced-atc-nonrandom-design.md)
and the on-machine procedure in
[`docs/testing/enhanced-atc-nonrandom-test.md`](docs/testing/enhanced-atc-nonrandom-test.md).
```

- [ ] **Step 6: Verify and commit**

Run: `grep -nE "P70[1-9]|P71[0-2]|ToolInBin|P160 = 0|tool-bin-mapping-test" CLAUDE.md README.md`
Expected: no output.

```bash
git add CLAUDE.md README.md
git status --short
git commit -m "docs: CLAUDE.md and README describe the Tool Library bin map and the CNC12 handshake

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>
Claude-Session: https://claude.ai/code/session_01JybVRnfYAPvLWhZWbL3DgN"
```

---

### Task 8: `docs/plc-spec/` content corrections (pinned line refs untouched)

**Files:**
- Modify: `docs/plc-spec/atc.md:14-24`, `:80-95`; `docs/plc-spec/main-stage.md:222-227`; `docs/plc-spec/boot.md` (InitialStage bullets); `docs/plc-spec/definitions.md` (word rows, SV rows); `docs/plc-spec/parameters.md` (table); `docs/plc-spec/faults-and-messages.md` (OtherFault producers)

Rule for every edit here: describe the current program; keep every existing `src:NNNN`; do **not** invent line numbers for new rungs (cite them by the `; Acroloc` comment text instead).

- [ ] **Step 1: `atc.md` banner (lines 14-24)** - replace the blockquote that starts `> ⚠️ **Superseded by the tool→bin mapping change (PR #22).**` with:

```
> ⚠️ **Variable names below are the 41f3fd6 snapshot's.** Current names:
> `CarouselToolID_W → CurrentToolBin_W`, `ChangeToTool_W → TargetToolBin_W`,
> `InstToolID_W → InstBinID_W`, `InToolSelect_M → InBinDecode_M`; added since the pin:
> `TargetToolBinDisp_W` (W8, VCP readout), `ReportedToolBin_W` (W78, position report),
> `MaxToolBins_W` (W79, P161), `M18_SV`. The tool->bin map is CNC12's Tool Library
> (non-random enhanced ATC, `P160 = 1`); `SV_TOOL_NUMBER` arrives as a **bin**. For the
> current flow see
> [`../../.claude/skills/acroloc-s10/reference/atc-flow.md`](../../.claude/skills/acroloc-s10/reference/atc-flow.md).
> This pinned spec should be re-based to a current commit as a dedicated pass (re-deriving
> the citations), per the "don't re-baseline line refs piecemeal" convention.
```

- [ ] **Step 2: `atc.md` kickoff paragraph (section "2. `MainStage` — kickoff and entry safety")** - replace the block from `**Kickoff** (`src:2910-2911`...` through the paragraph ending `...go true.` with:

```
**Kickoff** (tagged `; Acroloc tool stage start`; the 41f3fd6 rung at `src:2910-2911` was
`IF M6_SV THEN ChangeToTool_W = SV_TOOL_NUMBER, SET ATCStage`). The current program has four
rungs here, none with a pinned line:
```plc
IF M6_SV && !ATCStage THEN ATCSpin_T = ATC_SPIN_TIMEOUT_MS_C, SET ATCSpin_T, CurrentToolBin_W = 0
IF M6_SV && !ATCStage && (SV_TOOL_NUMBER < 1 || SV_TOOL_NUMBER > MaxToolBins_W) THEN
  FaultMsg_W = ATC_BIN_RANGE_MSG_C, SET ShowFaultStage, SET OtherFault_M,
  RST M6_SV, RST ATCSpin_T, TargetToolBinDisp_W = SV_TOOL_NUMBER
IF M6_SV && !ATCStage THEN
  TargetToolBin_W = SV_TOOL_NUMBER, TargetToolBinDisp_W = SV_TOOL_NUMBER, SET ATCStage
```
The machine runs CNC12's non-random enhanced ATC (`P160 = 1`), so `SV_TOOL_NUMBER` (the
system variable `M107` populates) is the requested tool's **carousel bin** as assigned in the
Tool Library, not the tool number. The first rung arms the 20 s watchdog and clears the stale
bin; the second faults `ATC_BIN_RANGE_MSG_C` (9067) for a bin outside 1..P161
(`MaxToolBins_W`) without starting the carousel; the third latches the bin into
`TargetToolBin_W` (`W72`) and the VCP readout word and `SET`s `ATCStage`. Because `ATCStage`
(`STG16`, `ATCStage` (src:1207)) is swept **after** `MainStage` (`STG4`) in file order, per
`scan-model.md` this `SET` takes effect in the **same scan**.

**Position report and reset** (tagged `; Acroloc -- enhanced ATC handshake` and
`; Acroloc -- enhanced ATC reset`, directly after the kickoff; no pinned line):
```plc
IF !ATCStage THEN ReportedToolBin_W = CurrentToolBin_W
IF True_M THEN SV_PLC_CAROUSEL_POSITION = ReportedToolBin_W
IF M18_SV && !ATCStage THEN CurrentToolBin_W = SV_ATC_CAROUSEL_POSITION
```
CNC12 will not run a tool change until the PLC reports a carousel position, monitors it
continuously, and at the end of every M6 records it as the new tool's putback bin. The report
is latched only while `ATCStage` is idle so mid-spin partial sums never reach CNC12; every
`ATCStage` abort rung zeroes `CurrentToolBin_W`, so a fault reports 0 (unknown), as does a
manual unlock. `InitialStage` seeds `CurrentToolBin_W` from `SV_ATC_CAROUSEL_POSITION`
(CNC12's persisted last position) and `M18` (`mfunc18.mac`, run by the Tool Library's F6 ATC
Reset at `P164 = 1`) re-seeds it after the operator declares the true position.
```

- [ ] **Step 3: `main-stage.md` "Tool-change entry" bullet (lines 222-227)** - replace the bullet with:

```
- **Tool-change entry** (tagged "Acroloc tool stage start" at src:2910; the pinned rung
  src:2911 `IF M6_SV THEN ChangeToTool_W = SV_TOOL_NUMBER, SET ATCStage` is now four rungs, no
  pinned lines): arm the 20 s watchdog and clear `CurrentToolBin_W`; fault
  `ATC_BIN_RANGE_MSG_C` (9067) if `SV_TOOL_NUMBER` is outside 1..`MaxToolBins_W` (P161);
  otherwise latch it into `TargetToolBin_W` and `TargetToolBinDisp_W` and arm `ATCStage`.
  `SV_TOOL_NUMBER` is the requested tool's **bin** (CNC12 non-random enhanced ATC,
  `P160 = 1`). Directly after: the position report (`ReportedToolBin_W` ->
  `SV_PLC_CAROUSEL_POSITION`, latched only while `ATCStage` is idle) and the `M18_SV` reset
  re-seed from `SV_ATC_CAROUSEL_POSITION`. Because `ATCStage` (STG16, src:1207) appears
  **after** `MainStage` (STG4) in file order, per `scan-model.md` the `SET` takes effect
  **in this same scan** — `ATCStage`'s body runs immediately. Full detail in
  [atc.md](atc.md).
```

- [ ] **Step 4: `boot.md` InitialStage bullets** - after the "Timer preset loads" bullet (the one ending `— see [atc.md](atc.md).`) add:

```
- Acroloc gear-state init (src:1276-1280) and, added later with no pinned line,
  `CurrentToolBin_W = SV_ATC_CAROUSEL_POSITION` — seeds the carousel bin from the position
  CNC12 persisted in `cncm.job`, for the enhanced-ATC position report described in
  [atc.md](atc.md).
```

Also in `boot.md` line 17-19, change `none of the rungs in `WatchDogStage` or `LoadParametersStage` are tagged `; Acroloc`. The only Acroloc-specific content in this file is the power-up gear-state init inside `InitialStage` (src:1276-1280), called out below.` to `none of the rungs in `WatchDogStage` are tagged `; Acroloc`. The Acroloc-specific content in this file is the power-up gear-state init and carousel-bin seed inside `InitialStage` (src:1276-1280 plus one unpinned line), and the P161 cache in `LoadParametersStage` (`MaxToolBins_W = SV_MACHINE_PARAMETER_161`, unpinned), called out below.` Then, in the `## LoadParametersStage (src:1284-1376)` section of `boot.md`, directly after the `- **Probe protection** (src:1373-1375): ...` bullet (the last bullet of that section's rung list), add:

```
- **ATC bin count** (unpinned, tagged `; Acroloc -- enhanced ATC (P160=1)`):
  `IF True_M THEN MaxToolBins_W = SV_MACHINE_PARAMETER_161` — P161 (ATC Maximum Tool Bins)
  re-read every scan; the M6 kickoff bin guard's upper bound. [atc.md](atc.md)
```

- [ ] **Step 5: `definitions.md`** - in the Words table, after the `EngagedRange_W` row add (no src line):

```
| `ReportedToolBin_W` | W78 | — | Acroloc | Settled carousel bin reported to CNC12 via `SV_PLC_CAROUSEL_POSITION` (latched while `ATCStage` idle; 0 = unknown). [atc.md](atc.md) |
| `MaxToolBins_W` | W79 | — | Acroloc | P161 cached every scan; upper bound of the M6 bin guard. [atc.md](atc.md), [parameters.md](parameters.md) |
```

In the System variables table, after the `HomeSync_SV` row add:

```
| `M18_SV` | `SV_M94_M95_18` | — | Acroloc | ATC Reset pulse from `mfunc18.mac` (CNC12 F2 ATC Reset); re-seeds `CurrentToolBin_W` from `SV_ATC_CAROUSEL_POSITION`. [atc.md](atc.md) |
```

In the Constants table, directly after the row `| `CAROUSEL_TIMEOUT_MSG_C` | 16130 (2+256*63) | 211 | Acroloc | ...` add:

```
| `ATC_BIN_RANGE_MSG_C` | 17154 (2+256*67) | — | Acroloc | "ATC BIN OUT OF RANGE" — M6 kickoff fault when CNC12 sends a bin outside 1..P161 (message 67, added to `plcmsg.txt`). [atc.md](atc.md) |
```

- [ ] **Step 6: `parameters.md`** - add rows to the table (no src line for the new read; cite the rung text):

```
| P6 | ATC installed (CNC12-side; not read by the PLC) | none | [atc.md](atc.md) | 1: with P160 non-zero the on-screen tool updates after M6 |
| P160 | Enhanced ATC type (CNC12-side; not read by the PLC) | none | [atc.md](atc.md) | **1** = non-random: `M107` sends the requested tool's Tool-Library bin in `SV_TOOL_NUMBER`. 0 = off (P701-style maps would be needed; not used). 2 = random: reshuffles bins, wrong for this carousel |
| P161 | ATC Maximum Tool Bins (`MaxToolBins_W`) | `MaxToolBins_W = SV_MACHINE_PARAMETER_161` in `LoadParametersStage` (unpinned) | [atc.md](atc.md) | **12**; M6 faults 9067 for a bin outside 1..P161. CNC12 sends it to the PLC at power-up: reboot after changing |
| P164 | ATC feature bit (CNC12-side; not read by the PLC) | none | [atc.md](atc.md) | 1 = F2 ATC Reset in the Tool Library, which runs `mfunc18.mac` |
```

Update the Verification paragraph's distinct-parameter list to add `161` and change the sentence claiming the `.src` has had no commits since 41f3fd6 to: "Lines added after 41f3fd6 (the P161 read) are cited by rung text, not line number, per the pinning convention."

- [ ] **Step 7: `faults-and-messages.md`** - in the `OtherFault_M` producer lists (both the prose paragraph and the table row) append: `, the ATC kickoff bin guard (`ATC_BIN_RANGE_MSG_C`, 9067, unpinned) and the three `ATCStage` abort rungs (atc.md)`.

- [ ] **Step 8: Verify and commit**

Run: `grep -nE "P70[1-9]|P71[0-2]|ToolInBin|P160 = 0|P160=0" docs/plc-spec/*.md`
Expected: no output (the `parameters.md` P160 row says "0 = off", which this pattern does not match).

Run: `git diff docs/plc-spec | grep -E "^[-+].*src:[0-9]+" | grep -E "^-" `
Expected: no removed `src:` citations (the pinned numbers must all survive; moved text is fine as long as the citation reappears in a `+` line).

```bash
git add docs/plc-spec
git status --short
git commit -m "docs(plc-spec): enhanced ATC kickoff, position report, M18 reset, new words and params

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>
Claude-Session: https://claude.ai/code/session_01JybVRnfYAPvLWhZWbL3DgN"
```

---

### Task 9: Skill references (`acroloc-s10`, `centroid-plc-programming`)

**Files:**
- Modify: `.claude/skills/acroloc-s10/SKILL.md:96-98`, `:109`, `:117`; `.claude/skills/acroloc-s10/reference/atc.md:27-47`; `.claude/skills/acroloc-s10/reference/atc-flow.md:56-79`, `:124-129`, `:225-227`, `:273-295`; `.claude/skills/centroid-plc-programming/reference/system-variables.md:50-53`

- [ ] **Step 1: `SKILL.md` word table** - replace the `TargetToolBin_W` and `ToolInBin1_W` rows with:

```
| `TargetToolBin_W` | W72 | Target carousel **bin** for the change, latched from `SV_TOOL_NUMBER` (which CNC12 non-random enhanced ATC fills with the requested tool's Tool-Library bin), after a 1..P161 range guard |
| `TargetToolBinDisp_W` | W8 | Chosen bin held for the retro VCP live `BIN` readout (`plc_word` 8); latched from `SV_TOOL_NUMBER` each M6; 0 after a manual unlock |
| `ReportedToolBin_W` | W78 | Settled carousel bin reported to CNC12 every scan via `SV_PLC_CAROUSEL_POSITION`; latched from `CurrentToolBin_W` only while `ATCStage` is idle; 0 = unknown |
| `MaxToolBins_W` | W79 | P161 (ATC Maximum Tool Bins) cached every scan; upper bound of the M6 bin guard |
```

(keep the existing `TargetToolBinDisp_W` row's position; this just rewrites it). In the M-function table after `M6_SV` add:

```
| `M18_SV` | SV_M94_M95_18 | ATC Reset pulse from `mfunc18.mac` (CNC12 Tool Library F2 ATC Reset); re-seeds `CurrentToolBin_W` from `SV_ATC_CAROUSEL_POSITION` |
```

- [ ] **Step 2: `SKILL.md` playbook item 2** - replace `on `M6_SV`, maps the requested tool to its bin (`TargetToolBin_W` = the bin whose loaded tool == `SV_TOOL_NUMBER`, from the P701–712 map; `99` if unmapped) and `SET ATCStage`.` with `on `M6_SV`, range-guards the bin CNC12 sent in `SV_TOOL_NUMBER` (1..P161, else fault `9067 ATC BIN OUT OF RANGE`), latches it into `TargetToolBin_W` and `SET ATCStage`; it also reports the settled bin to CNC12 every scan (`SV_PLC_CAROUSEL_POSITION`) and re-seeds on `M18`.`

- [ ] **Step 3: `SKILL.md` gotcha bullet** - replace the `**Tool→bin map lives in the PLC (P160=0), not CNC12.**` bullet with:

```
- **Tool→bin map lives in CNC12's Tool Library, not the PLC.** The machine runs non-random enhanced ATC (`P160=1`, `P161=12`, `P6=1`, `P164=1`): `M107` sends the requested tool's **bin** in `SV_TOOL_NUMBER`. The PLC must keep reporting its position in `SV_PLC_CAROUSEL_POSITION` or CNC12 will not run a change at all, and that reported value becomes the new tool's putback bin at the end of every M6 — so it must be the settled bin, never a mid-spin partial. Random mode (`P160=2`) reshuffles bins after every change and is wrong for this fixed-pocket carousel. See [reference/atc-flow.md](reference/atc-flow.md#tool-to-bin-map--how-m6t-reaches-a-bin).
```

- [ ] **Step 4: `reference/atc.md`** - in the manual-unlock bullet replace `but it cannot clear CNC12's current tool at `P160 = 0` (`SV_ATC_TOOL_IN_SPINDLE` is CNC12->PLC only) — the operator re-establishes the current tool after a manual swap.` with `and reports 0 to CNC12; the operator then declares the true position, the tool now under the spindle and its bin with the Tool Library's **F2 ATC Reset** (which runs `mfunc18.mac` so the PLC re-seeds its bin).`

Replace the "**Tool→bin mapping (operator-defined, fixed):**" paragraph with:

```
**Tool→bin mapping (operator-defined, fixed):** each physical bin permanently
holds one tool ("a tool from bin 5 always returns to bin 5"). Which tool sits in
which bin is set in CNC12's **Tool Library Bin column** (F1 Setup > F2 Tool >
F2 Tool Lib; editable because the machine runs non-random enhanced ATC,
`P160 = 1`). Any of the 200 tools may be assigned any bin 1-12, several tools may
share a bin, dashes = not in the carousel, 0 = in the spindle. `M6T##` makes
CNC12 send that tool's bin to the PLC, which indexes the carousel to it (see
[atc-flow.md](atc-flow.md#tool-to-bin-map--how-m6t-reaches-a-bin)).
```

- [ ] **Step 5: `reference/atc-flow.md` kickoff section (lines 61-79)** - replace from `**Kickoff — translate the requested tool to its bin, then set the stage:**` through `...its search/decode/match logic is unchanged.` with:

```
**Kickoff — guard the bin CNC12 sent, then set the stage:**

The machine runs CNC12's non-random enhanced ATC (`P160 = 1`), so `SV_TOOL_NUMBER`
is the requested tool's **carousel bin** as assigned in the Tool Library — `M107`
sends the bin, not the tool number:
```plc
IF M6_SV && !ATCStage THEN ATCSpin_T = ATC_SPIN_TIMEOUT_MS_C, SET ATCSpin_T, CurrentToolBin_W = 0
IF M6_SV && !ATCStage && (SV_TOOL_NUMBER < 1 || SV_TOOL_NUMBER > MaxToolBins_W) THEN
  FaultMsg_W = ATC_BIN_RANGE_MSG_C, SET ShowFaultStage, SET OtherFault_M,
  RST M6_SV, RST ATCSpin_T, TargetToolBinDisp_W = SV_TOOL_NUMBER
IF M6_SV && !ATCStage THEN
  TargetToolBin_W = SV_TOOL_NUMBER, TargetToolBinDisp_W = SV_TOOL_NUMBER, SET ATCStage
```
`M6_SV` is `SV_M94_M95_8`. `MaxToolBins_W` (W79) is P161, re-read every scan. A
bin outside 1..P161 (an unassigned tool, a bad library, P161 unset) faults
`9067 ATC BIN OUT OF RANGE` at once and never starts the carousel; the 9xxx fault
cancels the job during mfunc6's `G4 P1` dwell, so CNC12 does not record the change
as complete. `TargetToolBinDisp_W` (W8) holds the bin for the retro VCP `BIN`
readout (`plc_word` 8). `ATCStage` (STG16) then indexes the carousel to
`TargetToolBin_W` — its search/decode/match logic is unchanged.

**Position report and ATC Reset — the CNC12 handshake:**
```plc
IF !ATCStage THEN ReportedToolBin_W = CurrentToolBin_W
IF True_M THEN SV_PLC_CAROUSEL_POSITION = ReportedToolBin_W
IF M18_SV && !ATCStage THEN CurrentToolBin_W = SV_ATC_CAROUSEL_POSITION
```
CNC12 refuses to run a tool change until the PLC reports a carousel position, and
at the end of every M6 it records the reported value as the new tool's putback bin
(its bin field is restored from that when the tool is next swapped out). So the
report must be the **settled** bin: it is latched only while `ATCStage` is idle,
the match rung leaves `CurrentToolBin_W` at the matched bin, and every abort rung
and the manual unlock zero it, so 0 (unknown) is reported honestly.
`InitialStage` seeds `CurrentToolBin_W` from `SV_ATC_CAROUSEL_POSITION`, the
position CNC12 persisted in `cncm.job`. `M18` (`mfunc18.mac`) is run by the Tool
Library's F2 ATC Reset (`P164 = 1`) after the operator enters the true position;
the rung re-seeds from the value CNC12 sent.
```

- [ ] **Step 6: `reference/atc-flow.md` manual-unlock paragraph (lines 124-129)** - replace `The PLC cannot clear CNC12's current tool at `P160 = 0`, so the operator re-establishes the tool after a manual swap; the next `M6` re-derives the bin by absolute-switch search regardless.` with `CNC12 sees the 0 through the position report; the operator declares the new state with the Tool Library's F2 ATC Reset (position, tool in spindle, its bin), and the next `M6` re-derives the bin by absolute-switch search regardless.`

- [ ] **Step 7: `reference/atc-flow.md` encoding intro (lines 225-227)** - change `(Bin and tool coincide only for a 1:1 loadout; the P701–712 map decouples them.)` to `(Bin and tool coincide only for a 1:1 loadout; the Tool Library's Bin column decouples them.)`

- [ ] **Step 8: `reference/atc-flow.md` map section (lines 273-295)** - replace the whole `## Tool-to-bin map (P701–712) — how M6T## reaches a bin` section (through the paragraph ending `...which only the PLC table provides.`) with:

```
## Tool-to-bin map — how M6T## reaches a bin

This machine runs CNC12's **non-random enhanced ATC**: `P160 = 1`, `P161 = 12`
(bins), `P6 = 1` (ATC installed), `P164 = 1` (F2 ATC Reset). The map is CNC12's:

- **Tool Library Bin column** (F1 Setup > F2 Tool > F2 Tool Lib): any of the 200
  tools can be given any bin 1-12; several tools may share a bin; dashes (F1
  Clear Bin) = not in the carousel; 0 = in the spindle (set by CNC12, not by
  hand). F10 saves. The column is locked at `P160 = 0`.
- **`M6T##`**: CNC12 skips the change if tool ## is already in the spindle;
  otherwise `M107` sends that tool's bin in `SV_TOOL_NUMBER` and the kickoff
  (above) guards and latches it.
- **End of M6** (CNC12 bookkeeping, non-random): the previous tool's bin field is
  restored from its putback field; the new tool gets bin = 0 and putback = the
  bin the PLC is reporting. That is why the report must be settled and correct
  when `ATCStage` clears. The M6 start sets an ATC error flag in the job file and
  a normal end clears it; an interrupted or faulted change leaves it set, and the
  next job or MDI start prompts the operator to clear it with Y.
- **After a manual unlock / hand-spin** the operator uses **F2 ATC Reset** to
  declare the position, the tool under the spindle and its bin; that runs
  `mfunc18.mac`.

Vendor references: CNC12 Mill Operator Manual 15.4.118 (Parameter 160), Tool
Library p.64; ATC3 Umbrella Operating Instructions (tool library interface, ATC
Reset). Random mode (`P160 = 2`) is wrong here: it puts the outgoing tool in the
bin the incoming one left, reshuffling the map after every change.
```

- [ ] **Step 9: `centroid-plc-programming/reference/system-variables.md`** - append to the `SV_TOOL_NUMBER` row's meaning: ` **This program:** enhanced ATC (P160=1), so it is the requested tool's bin; guarded 1..P161 at the M6 kickoff.` To `SV_ATC_CAROUSEL_POSITION`: ` **This program:** seeds `CurrentToolBin_W` in `InitialStage` and on `M18_SV`.` To `SV_PLC_CAROUSEL_POSITION`: ` **This program:** written every scan from `ReportedToolBin_W` (settled bin, 0 = unknown).` Leave `SV_ATC_TOOL_IN_SPINDLE` as-is (not read by this program).

- [ ] **Step 10: Verify and commit**

Run: `grep -rnE "P70[1-9]|P71[0-2]|ToolInBin|P160 ?= ?0|forces tool" .claude/skills/acroloc-s10 .claude/skills/centroid-plc-programming/reference/system-variables.md`
Expected: only the `atc-flow.md` line "The column is locked at `P160 = 0`." and nothing else.

Run: `grep -rn "tool-to-bin-map-p701712" .claude/skills docs CLAUDE.md README.md`
Expected: no output (the anchor changed; Steps 3 and 4 already use the new one).

```bash
git add .claude/skills
git status --short
git commit -m "docs(skills): acroloc-s10 and plc-programming references describe the Tool Library map and CNC12 handshake

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>
Claude-Session: https://claude.ai/code/session_01JybVRnfYAPvLWhZWbL3DgN"
```

---

### Task 10: Annotate the July spec

**Files:**
- Modify: `docs/superpowers/specs/2026-07-22-tool-bin-mapping-design.md:1-30`

- [ ] **Step 1: Change the status line and add a superseding note**

Change `Status: implemented (P160=0 PLC map); pending on-machine verification` to `Status: superseded 2026-09-06 by `2026-09-06-enhanced-atc-nonrandom-design.md` (see note below); the P701-P712 PLC map shipped in PR #22 and is being replaced`.

Directly under `## Revision history (why the approach changed)` insert:

```
> **2026-09-06 correction.** The bullet below, "Non-random (P160=1) forces tool == bin",
> entered this spec in commit 190f737 as an inference from the example configs in
> `docs/official`; P160 = 1 was never set on the machine. The only on-machine trials were
> at P160 = 2. Centroid's docs say the opposite (operator manual 15.4.118: "An M107 command
> sends the bin number for the specified tool number"; ATC3 instructions: "Any of the 200
> tools can be specified as belonging to one of the carousel bins"). Non-random mode is now
> being adopted; see the 2026-09-06 spec.
```

- [ ] **Step 2: Commit**

```bash
git add docs/superpowers/specs/2026-07-22-tool-bin-mapping-design.md
git status --short
git commit -m "docs(spec): annotate the July tool-bin spec: non-random claim was an inference; superseded

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>
Claude-Session: https://claude.ai/code/session_01JybVRnfYAPvLWhZWbL3DgN"
```

---

### Task 11: Final verification pass (whole branch)

**Files:** none modified unless a check fails.

- [ ] **Step 1: Full checks**

```bash
./compile.sh                                   # Compilation successful, 0 errors; note warnings/tokens
python3 tools/plcfmt.py --check Centroid-Acroloc-ALLIN1DC.src; echo exit=$?   # exit=0
python3 tools/test_plcfmt.py | tail -1         # 33 passed
python3 tools/test_vcpgen.py 2>&1 | tail -1    # OK
LC_ALL=C grep -nP '[^\x00-\x7F]' Centroid-Acroloc-ALLIN1DC.src mfunc6.mac mfunc18.mac plcmsg.txt   # no output
git grep -nE "P70[1-9]|P71[0-2]|ToolInBin" -- ':!docs/superpowers' ':!docs/official' ':!language.msg'   # no output
git grep -nE "tool-bin-mapping-test"           # no output
git log --oneline main..HEAD                   # 11 commits (spec + tasks 1-10)
```

- [ ] **Step 2: Report**

Report the warning and token deltas against the 190 / 5040 baseline, the list of commits, and that the branch is ready for the owner's Phase A on-machine run per `docs/testing/enhanced-atc-nonrandom-test.md`. The PR #22 artifact update is done by the main session, not by a subagent.
