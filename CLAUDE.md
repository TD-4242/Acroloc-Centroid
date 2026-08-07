# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

This repository is the **Centroid CNC12 PLC program and M-code macros** for an Acroloc
mill retrofitted with a Centroid **ALLIN1DC** motion controller (MPU11-based). It is not a
software application you build/run on this machine — it is controller firmware-level source
that is compiled and loaded by Centroid's CNC12 software (`cncm`) on the Windows control PC.

The bulk of original work here is the **custom Acroloc Automatic Tool Changer (ATC)** logic
grafted onto Centroid's stock ALLIN1DC mill PLC. Search for the comment marker `; Acroloc`
to find every custom addition (definitions and logic alike).

## Files

- `Centroid-Acroloc-ALLIN1DC.src` — the PLC program (ladder logic in Centroid's text/stage
  language). This is the primary file. ~3000 lines.
- `plc.map` — **generated** symbol→source-line map produced by the PLC compiler. Not tracked
  in git (gitignored build output); regenerated on every compile, locally or on the control PC.
  Do not hand-edit.
- `mfunc*.mac` — M-code macros (G-code-like) executed by the CNC when an M-function fires.
  - `mfunc3/4` = spindle CW/CCW, `mfunc6` = **tool change (M6)**, `mfunc7/8` = mist/flood
    coolant, `mfunc10/11` = clamp on/off.
- `resources/vcp/` — **generated** operator panel (retro VCP). Emitted by `tools/vcpgen.py`;
  do not hand-edit. `resources/colors/` holds the color themes.
- **Customized CNC12 control-PC files** — `language.msg` (parameter/UI labels: P860-863 gear
  shift, P701-712 ATC tool->bin map), `plcmsg.txt` (custom ATC/spindle operator messages, keyed
  to the `.src` message constants), `cncm.hom` (homing + HomeSync latch). These look stock but
  are ours, and a **CNC12 upgrade can overwrite them** — see
  `docs/control-pc-customizations.md` for what is customized and how to restore it.

## Build / deploy

There is no build tooling in this repo. The `.src` is compiled and the `.mac` files are
installed by **Centroid CNC12 on the control PC**:
- The PLC source is compiled to a `.plc` binary via CNC12's PLC compiler (`cncm` /
  `PLC Detective`), which also emits `plc.map`. Compile errors surface in CNC12.
- `.mac` files are placed in the CNC12 macro directory and invoked by M-number
  (`mfuncN.mac` runs on `MN`).
- Validation is done on the machine/simulator — there are no automated tests.

Local helper scripts (run on the dev box; they shell out to the vendor compiler via Wine):
- `./compile.sh` — syntax/lint-check the `.src` with Centroid `mpucomp` (reports errors +
  a warning count).
- `tools/plcfmt.py` — reformat the `.src` to canonical style (`--fix`), guarded by a
  fingerprint check that the compiled program is unchanged. See `tools/README.md`. Run
  `./compile.sh` after `--fix`. Tests: `python3 tools/test_plcfmt.py`.
- `tools/vcpgen.py` — **generates the whole retro VCP** (`resources/vcp/` skin, button XML +
  SVGs). Edit the generator and re-run it; **never hand-edit the emitted files** — they are
  overwritten. Tests: `python3 tools/test_vcpgen.py`.

## PLC architecture (how the .src is organized)

The file has two halves:

1. **Definitions** (top, through ~line 1185): symbolic names bound to hardware/system
   resources with `Name IS Resource`. Naming convention by suffix:
   - `_I` = input bit (`INP`), `_O` = output bit (`OUT`), `_M` = memory bit (`MEM`),
     `_W` = 32-bit word (`W`), `_T` = timer (`T`), `_SV` = CNC system variable,
     `_C` = integer constant. Stages are `IS STGn`.
   - Message constants (`_C`) encode as `value = msgNumber + 256 * msgFile` — e.g.
     `ATC_Lock_Released_C IS 45546 ;(2+256*174)`. The message text lives in CNC12's
     message files keyed by that `(file, number)` pair, not in this repo.

2. **Stages** (bottom): the program is a flat scan of `STG`-numbered stages. A stage runs
   only while SET; logic uses `IF <cond> THEN SET/RST Stage, ...` to enable/disable stages
   each scan. Key stages (defined ~1185–1212):
   - `WatchDogStage`, `InitialStage`, `LoadParametersStage` — boot/param plumbing.
   - `MainStage` — the big one: fault aggregation, coolant/spindle/clamp handling, and the
     **Acroloc ATC entry point** (`IF M6_SV THEN ... SET ATCStage`).
   - `ATCStage` (STG16) — the custom carousel tool-change state machine (see below).
   - `JogPanelStage`, `MPGStage`, `WirelessMpgStage`, `JogKeys*Stage` — operator jog/MPG
     handling. `CheckCycloneStatusStage`/`MiniPLCErrorStage` — drive/fiber comm faults.
   - `Show*Stage` / `MessageStage` — operator message display.

### The Acroloc ATC tool-change flow (the custom heart)

Understand this before touching tool-change logic; it spans `mfunc6.mac`, `MainStage`, and
`ATCStage`:

1. `M6` runs `mfunc6.mac`: stops spindle/coolant, moves Z to the tool-change position via
   `G53 Z0`, sends the target tool with `M107`, then sets `M6_SV` (`M94 /8`) to kick off the
   tool-change stage and resets it (`M95 /8`) when `ATCStage` clears.
2. `MainStage` sees `M6_SV` and **maps the requested tool to a carousel bin**: machine
   parameters `P701-P712` hold the tool loaded in bins 1-12 (cached in
   `ToolInBin1_W..ToolInBin12_W` at `LoadParametersStage`, re-read every scan). It sets
   `TargetToolBin_W` to the bin whose loaded tool equals `SV_TOOL_NUMBER` — or `99`, an
   unreachable bin, if the tool is in no bin, so it faults on the watchdog instead of
   false-matching — then `SET ATCStage`. While Z has not cleared the tool changer
   (`ATC_Z_ClearedToolChanger_I` low) it drops spindle enable; `ATCStage` posts the "spindle
   not parked" fault.
3. `ATCStage` spins the carousel (`ATCMotor_O`, `ATCUnlocked_O`) and reads the **5 position
   switches** (`ATC_Pos1_I`..`ATC_Pos5_I`, INP32..INP28). These encode the **carousel bin
   (physical position)**, not the tool number — **base-16 as decimal** across those 5 bits
   (note `ATC_Pos5_I` adds `10`, not `16`). The decoded `CurrentToolBin_W` is compared to
   `TargetToolBin_W`; on match it stops the motor, relocks, and `RST M6_SV` / `RST ATCStage`
   to finish.

**Naming rule:** anything `...ToolBin...` holds a **carousel bin**; `ToolInBinN_W` holds a
**tool number**. CNC12's own enhanced-ATC modes are deliberately unused (`P160 = 0`) — they
either reshuffle the map (random) or force tool == bin (non-random).

Custom ATC I/O (all marked `; Acroloc`): inputs `INP24`,`INP26`,`INP27`,`INP28..32`;
outputs `OUT17` (`ATCMotor_O`), `OUT18` (`ATCUnlocked_O`); words `W71` (`CurrentToolBin_W`),
`W72` (`TargetToolBin_W`), `W8` (`TargetToolBinDisp_W`, the VCP `TOOL BIN` readout), and
`W78-W89` (`ToolInBin1_W..12_W`).

## Conventions & cautions

- **Match the surrounding style.** Centroid's stock code uses fixed-column alignment for
  `Name IS Resource` and heavy `;` comments. Keep new definitions aligned and tag custom
  ones with `; Acroloc`.
- Every M-function macro guards against graph/search mode with
  `IF #4201 || #4202 THEN GOTO 1000` and ends at the `N1000` label — preserve this pattern.
- Macro PLC variables: a PLC `OUT`/`MEM` is read from a macro as `#(60000 + n)` (e.g.
  `OUT1058` → `#61058`). M-functions are triggered from macros via `M94 /bit` (set) and
  `M95 /bit` (reset).
- The carousel search is bounded by a **20 s watchdog** (`ATCSpin_T`, T24, armed at M6
  kickoff): if the target tool is never matched, `ATCStage` faults `CAROUSEL MOVE TIME OUT`
  and stops/relocks the carousel. Still edit the match/exit conditions carefully — an
  off-by-one in the position decode (e.g. Pos5 `+16` instead of `+10`) makes tools mismatch,
  but it now faults at 20 s instead of spinning forever.
- `plc.map` is gitignored build output; never hand-edit it and don't rely on its line numbers
  staying in sync after you edit the `.src`.
- When changing the PLC source, update the affected docs/plc-spec/ section(s) as part of the
  change, so their **content** is true. Do **not** re-baseline the `src:` line references or
  the `Line numbers as of commit <hash>` header — those are deliberately pinned to a snapshot
  (see the note at `docs/plc-spec/definitions.md:20`). Fix false statements, leave the numbers
  alone, and give lines added after the pin **no** line reference rather than a number from a
  different baseline.
- **Current docs describe the current state — never what it used to be.** `docs/plc-spec/`
  and the `.claude/skills/` references document what the machine does *now*. When a feature is
  removed, delete its section outright; do not leave a tombstone (`REMOVED`, "previously
  documented", "this used to…"). The record of what changed and why belongs in
  `docs/superpowers/specs/`, which is where historical design documents live and may be
  annotated freely. Documenting *vendor* behaviour that still exists — a system variable's
  measured semantics, say — is current fact, not a tombstone, and stays.
