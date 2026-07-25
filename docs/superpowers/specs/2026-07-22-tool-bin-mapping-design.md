# Tool-to-Bin Mapping (tools numbered > 12) - Design

Date: 2026-07-22
Status: implemented (P160=0 PLC map); pending on-machine verification

## Revision history (why the approach changed)

The first two drafts of this spec chased CNC12's built-in "enhanced ATC" modes.
On-machine testing ruled both out for this machine, so the shipped design is a
fixed tool->bin map held in the PLC. The dead ends, briefly, so nobody retries
them:

- **Machine parameter 160 is the ATC-type selector** (confirmed by comparing
  every example config in `docs/official`): `0` = no built-in ATC, `1` =
  non-random, `2` = random. The tool-library **bin** column only exists at
  `P160 != 0`.
- **Random (P160=2) reshuffles the map.** CNC12's random model assumes tools
  move between bins ("the tool in the spindle is placed into the same bin the
  next tool is picked up from"), so it renumbers bins after every change. On
  the machine, `M6T5` rewrote tool 1's bin to 5. This machine is a **fixed-pocket**
  carousel - a tool from bin 5 always returns to bin 5 - so a reshuffling map is
  wrong.
- **Non-random (P160=1) forces tool == bin.** It could not accept an arbitrary
  fixed assignment (e.g. tool 13 in bin 1), which is the whole requirement.

Neither native mode can express **arbitrary AND fixed**. So the map lives in the
PLC at **P160 = 0** (the machine's proven custom tool-change flow), where we
fully control it and nothing reshuffles it.

## Goal

Assign a tool to a physical carousel bin (e.g. tool 31 -> bin 2) and have
`M6T31` index the carousel to that bin and snap the tool in as it does today.
Tools 1-12 keep working. Assignments are operator-editable and never change on
their own.

## Background: how the tool change works (P160 = 0)

The swap is **Z-driven and mechanical**. `mfunc6.mac` stops the spindle, parks
Z at tool-change zero (`G53 Z0`), and fires `M94 /8` (`M6_SV`); at Z zero with
`ATC_Z_Zero_Release_I` (INP27) true the outgoing tool is released mechanically
(no software put-back move). The PLC's `ATCStage` (STG16) spins the carousel,
decodes the 5 position switches into a bin ID, and stops/relocks when that bin
matches the target. The target bin is latched in `MainStage`.

At P160 = 0, `SV_TOOL_NUMBER` is the **raw tool number** (`M6T##`). The one and
only change needed is: translate that tool number into the **bin** it lives in,
before `ATCStage` runs. `ATCStage` itself is unchanged - it always chased a bin
ID; it just now receives a mapped bin instead of the tool number.

## Approach: fixed tool->bin map in the PLC

**The map: machine parameters P701-712 = the tool number loaded in bins 1-12.**
These are end-user parameters (free for PLC/macro use). The operator sets, e.g.,
`P702 = 31` to say "bin 2 holds tool 31"; a plain 1:1 loadout is `P701=1 ...
P712=12`; an empty bin is left 0.

**PLC (`Centroid-Acroloc-ALLIN1DC.src`):**

- `LoadParametersStage` caches P701-712 into `ToolInBin1_W..ToolInBin12_W`
  every scan, so editing the loadout on the parameter screen takes effect with
  no reboot.
- `MainStage` M6 kickoff translates the request: `TargetToolBin_W` = the bin
  whose loaded tool equals `SV_TOOL_NUMBER`; default **99** (an unreachable bin)
  so a tool that is in no bin never matches and faults on the 20 s `ATCSpin_T`
  watchdog rather than false-matching bin 0 and completing without moving. Then
  `SET ATCStage`.
- `ATCStage` search/decode/match is unchanged - it indexes the carousel to
  `TargetToolBin_W`.

**Operator feedback (retro VCP `TOOL BIN` readout):** because this is a custom,
undocumented feature, the chosen bin is shown to the operator. The PLC latches it
into `TargetToolBinDisp_W` (W8) on every M6 and holds it; the retro VCP displays
it live as a `TOOL BIN` readout (`plc_word` 8) at row 2 cols 1-3. `99` means the
tool is in no bin; `0` means the position is unknown (set on manual unlock).

This is deliberately **not** a macro message: `M225` is a *modal* message box
that pauses the change until the operator dismisses it (confirmed on-machine), so
`mfunc6.mac` posts no message at all.

**Naming scheme** (so tool vs bin is never ambiguous):

- `...ToolBin...` = a carousel bin/position number: `CurrentToolBin_W` (bin at
  the spindle, decoded from switches), `TargetToolBin_W` (target bin),
  `TargetToolBinDisp_W` (macro-readable copy).
- `ToolInBinN_W` = the tool number loaded in bin N (the map entry, compared to
  `SV_TOOL_NUMBER`).

## Non-goals

- **No CNC12 enhanced-ATC mode** (P160 stays 0). The tool-library bin column and
  its automatic renumbering are exactly what we are avoiding.
- **No `SV_PLC_CAROUSEL_POSITION` / `SV_ATC_CAROUSEL_POSITION` handshake.** That
  belonged to the abandoned P160=2 approach and was removed.
- No change to `ATCStage`'s switch decode, peak gating, match/exit rung, or the
  20 s watchdog (the tool-bin rename touched variable names inside it but the
  compiled program is byte-identical).
- No put-back move logic (put-back is mechanical, Z-driven).
- No change to how tool offsets are keyed (CNC12 keeps those by tool number).

## Deliverables

1. This design doc.
2. PLC map: `ToolInBin1_W..12_W` cached from P701-712, the `MainStage`
   translation into `TargetToolBin_W`, tagged `; Acroloc`, `./compile.sh` clean.
3. Retro VCP `TOOL BIN` readout (`plc_word` 8 = `TargetToolBinDisp_W`) via
   `tools/vcpgen.py`; no macro message in `mfunc6.mac`.
4. Operator setup: P160 = 0; P701-712 = the tool in each bin.
5. Doc updates: `docs/plc-spec/atc.md` (+ pinned hash) and the `acroloc-s10` ATC
   references, to the P160=0 map and the final variable names.

## Testing / rollout

- `./compile.sh` clean (token/warning delta reported).
- On-machine at **P160 = 0**: set P701-712, load the `.plc` + `mfunc6.mac`, and
  copy `resources/vcp/` (restart CNC12) for the readout.
  - Identity map (P701..P712 = 1..12): `M6T5` -> bin 5, `TOOL BIN` reads 5.
  - Remap: `P705 = 31` -> `M6T31` -> bin 5, `TOOL BIN` reads 5.
  - Unmapped tool -> `CAROUSEL MOVE TIME OUT` fault at 20 s; `TOOL BIN` reads 99.
  - Manual unlock at Z clear -> `TOOL BIN` drops to 0 (position unknown).
- Confirm the change runs start-to-finish with **no pop-up to dismiss** (the
  readout is non-blocking; the modal `M225` message was removed for this reason).
