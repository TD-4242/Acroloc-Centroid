# Tool-to-Bin Mapping (tools > 12) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development or superpowers:executing-plans to implement task-by-task. Steps use checkbox (`- [ ]`) syntax.

**Goal:** `M6T<n>` for any tool number (including n > 12) indexes the carousel to the bin that tool is assigned to, via a fixed operator-editable tool->bin map held in the PLC.

**Architecture:** CNC12's enhanced-ATC modes were ruled out on-machine (random P160=2 reshuffles the bin map every change; non-random P160=1 forces tool==bin). This machine is a fixed-pocket carousel, so the map lives in the PLC at **P160 = 0** (the proven custom flow). Parameters P701-712 hold the tool loaded in each bin; the `MainStage` M6 kickoff translates `SV_TOOL_NUMBER` (the requested tool) into the target bin; `ATCStage`'s search is unchanged. See `docs/superpowers/specs/2026-07-22-tool-bin-mapping-design.md`.

**Tech Stack:** Centroid CNC12 (ALLIN1DC / MPU11) PLC stage language (`.src`) + M-code macros (`.mac`); `./compile.sh` (Wine `mpucomp`); `tools/plcfmt.py`. No automated behavior tests - validation is `./compile.sh` clean + on-machine checks.

## Global Constraints

- **ASCII-only, CRLF** for `Centroid-Acroloc-ALLIN1DC.src` and `mfunc6.mac`.
- **Tag custom PLC additions** with `; Acroloc`.
- **Run `./compile.sh` after every `.src` change**; report error/warning delta.
- **Do not change `ATCStage`'s logic** (STG16 switch decode, peak gating, match/exit, 20 s `ATCSpin_T` watchdog). Variable renames that keep the compiled program byte-identical are allowed.
- **Preserve `mfunc6.mac` guards:** `IF #4202 || #4201 THEN GOTO 1000` and `N1000`.
- **Naming:** `...ToolBin...` = a carousel bin/position; `ToolInBinN_W` = the tool number in bin N.
- `plc.map` is generated (gitignored); `docs/plc-spec/` line refs are pinned to a commit - fix false content, update the pinned hash, do not re-baseline.

---

### Task 1: PLC fixed tool->bin map

**Files:** Modify `Centroid-Acroloc-ALLIN1DC.src` (definitions; `LoadParametersStage`; `MainStage` M6 kickoff).

**Interfaces:**
- Consumes: `SV_MACHINE_PARAMETER_701..712`, `SV_TOOL_NUMBER`, `M6_SV`, `ATCStage`.
- Produces: `ToolInBin1_W..ToolInBin12_W` (W78-W89), `TargetToolBin_W` (W72, renamed target-bin word), `TargetToolBinDisp_W` (W8, macro-readable #96008).

- [x] Cache the map in `LoadParametersStage` (re-read each scan -> live edits):
  `ToolInBin1_W = SV_MACHINE_PARAMETER_701 ... ToolInBin12_W = SV_MACHINE_PARAMETER_712`.
- [x] Replace the M6 latch in `MainStage`: default `TargetToolBin_W = 99`, then
  `IF M6_SV && ToolInBinK_W == SV_TOOL_NUMBER THEN TargetToolBin_W = K` for K=1..12,
  then `TargetToolBinDisp_W = TargetToolBin_W, SET ATCStage`.
- [x] `./compile.sh` clean (4930 -> 5056 tokens, warnings unchanged at 190).

### Task 2: Operator feedback -- retro VCP `TOOL BIN` readout

**Files:** Modify `tools/vcpgen.py` (regenerate `resources/vcp/`); `mfunc6.mac`.

- [x] PLC latches the chosen bin into `TargetToolBinDisp_W` (W8) on every M6 and holds it.
- [x] `tools/vcpgen.py`: `BIN_ELEMENTS` renders a live `TOOL BIN` readout (`plc_word` 8)
  over a reused bezel at row 2 cols 1-3; regenerate and keep `test_vcpgen.py` green.
- [x] **No macro message.** `M225` is a *modal* box that pauses the change until dismissed
  (confirmed on-machine), so `mfunc6.mac` posts none -- do **not** reintroduce it.
- [x] `mfunc6.mac` keeps the graph/search guard and `N1000`; ASCII-clean.

### Task 3: Tool-vs-bin naming clarity

**Files:** Modify `Centroid-Acroloc-ALLIN1DC.src` (rename only, program-identical).

- [x] Bin-valued vars use `...ToolBin`: `CurrentToolBin_W` (carousel bin at spindle),
  `TargetToolBin_W`, `TargetToolBinDisp_W`. Loadout uses `ToolInBinN_W`.
- [x] Fix decode comments that called a bin a "tool ID/number"; switch table `T->B`.
- [x] Verify program-identical (compile token/warning count unchanged; diff is rename+whitespace only).

### Task 4: Documentation

**Files:** Modify `docs/plc-spec/atc.md` (+ pinned hash), `.claude/skills/acroloc-s10/reference/atc.md`, `.claude/skills/acroloc-s10/reference/atc-flow.md`, `.claude/skills/acroloc-s10/SKILL.md`.

- [ ] Document the P160=0 fixed map (P701-712), the `MainStage` translation, and the operator message.
- [ ] Update the ATC references to the final variable names (`CurrentToolBin_W`, `TargetToolBin_W`, `ToolInBinN_W`, `InstBinID_W`, `InBinDecode_M`).
- [ ] Do NOT rewrite historical `docs/superpowers/` plan/spec records under other dates.

---

## On-machine verification (owner-run, P160 = 0)

- Set P701-712 = tool in each bin; load the `.plc` + `mfunc6.mac`; copy `resources/vcp/` and restart CNC12.
- Identity map `M6T5` -> bin 5; remap `P705=31` -> `M6T31` -> bin 5, `TOOL BIN` readout tracks; unmapped tool -> `CAROUSEL MOVE TIME OUT` with `TOOL BIN` = 99; manual unlock -> `TOOL BIN` = 0.
- Confirm the change completes with no pop-up to dismiss.
