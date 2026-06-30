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
- `plc.map` — **generated** symbol→source-line map produced by the PLC compiler. Do not edit
  by hand; it is regenerated on compile.
- `mfunc*.mac` — M-code macros (G-code-like) executed by the CNC when an M-function fires.
  - `mfunc3/4` = spindle CW/CCW, `mfunc6` = **tool change (M6)**, `mfunc7/8` = mist/flood
    coolant, `mfunc10/11` = clamp on/off.

## Build / deploy

There is no build tooling in this repo. The `.src` is compiled and the `.mac` files are
installed by **Centroid CNC12 on the control PC**:
- The PLC source is compiled to a `.plc` binary via CNC12's PLC compiler (`cncm` /
  `PLC Detective`), which also emits `plc.map`. Compile errors surface in CNC12.
- `.mac` files are placed in the CNC12 macro directory and invoked by M-number
  (`mfuncN.mac` runs on `MN`).
- Validation is done on the machine/simulator — there are no automated tests.

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
2. `MainStage` sees `M6_SV`, latches the target into `ChangeToTool_W`, and `SET ATCStage`.
   The spindle is stopped before the changer by the general **spindle-in-changer feed-hold
   interlock** (feed hold + spindle-off + dwell/`ZeroSpeed_I` + auto-resume, timer
   `ChangerStopTimer_T`), which fires for *any* program/MDI move into the zone — not just M6.
   `ATCStage` then independently re-checks `ZeroSpeed_I` and Z-parked
   (`ATC_Z_Zero_Release_I`) before allowing carousel motion.
3. `ATCStage` spins the carousel (`ATCMotor_O`, `ATCUnlocked_O`) and reads the **5 position
   switches** (`ATC_Pos1_I`..`ATC_Pos5_I`, INP32..INP28). Tool IDs are **base-16 encoded as
   decimal** across those 5 bits (note `ATC_Pos5_I` adds `10`, not `16`). The accumulated
   `CarouselToolID_W` is compared to `ChangeToTool_W`; on match it stops the motor, relocks,
   and `RST M6_SV` / `RST ATCStage` to finish.

Custom ATC I/O (all marked `; Acroloc`): inputs `INP24`,`INP26`,`INP27`,`INP28..32`;
outputs `OUT17` (`ATCMotor_O`), `OUT18` (`ATCUnlocked_O`); words `W71`/`W72`.

## Conventions & cautions

- **Match the surrounding style.** Centroid's stock code uses fixed-column alignment for
  `Name IS Resource` and heavy `;` comments. Keep new definitions aligned and tag custom
  ones with `; Acroloc`.
- Every M-function macro guards against graph/search mode with
  `IF #4201 || #4202 THEN GOTO 1000` and ends at the `N1000` label — preserve this pattern.
- Macro PLC variables: a PLC `OUT`/`MEM` is read from a macro as `#(60000 + n)` (e.g.
  `OUT1058` → `#61058`). M-functions are triggered from macros via `M94 /bit` (set) and
  `M95 /bit` (reset).
- The carousel has **no timeout if a tool is never found** (see `;TODO` in `ATCStage`) — be
  careful when editing the match/exit conditions; an off-by-one in the position decode means
  the carousel spins indefinitely.
- `plc.map` is build output; never hand-edit it and don't rely on its line numbers staying
  in sync after you edit the `.src`.
