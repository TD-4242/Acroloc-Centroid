# Tool-to-Bin Mapping (tools numbered > 12) - Design

Date: 2026-07-22
Status: approved (brainstorm)

## Goal

Let a tool numbered higher than the 12 physical carousel bins be changed by
number. The operator assigns a tool to a bin once (e.g. tool 31 -> bin 2), and
`M6T31` then spins the carousel to bin 2 and Z snaps the tool in as it does
today. Tools 1-12 keep working unchanged.

## Background: how the change works today, and the one thing that must change

The tool swap on this machine is **purely Z-driven**. The carousel is a special
tool ring with a mechanical snap in/out: the PLC only has to **index the
carousel to the correct bin**, and the tool snaps in or out as the Z axis
retracts through the ring. There is no deposit-then-fetch, no "tool in spindle"
choreography, nothing for software or the PLC to sequence.

The current tool-change flow (see `.claude/skills/acroloc-s10/reference/atc-flow.md`):

```
M6 -> mfunc6.mac: stop spindle/coolant, G53 Z0 park, M107, M94 /8 (M6_SV)
   -> MainStage: IF M6_SV THEN ChangeToTool_W = SV_TOOL_NUMBER, SET ATCStage
   -> ATCStage: spin carousel, decode 5 position switches into CarouselToolID_W,
                stop/relock when CarouselToolID_W == ChangeToTool_W
```

Two facts make this feature small:

- **`SV_TOOL_NUMBER` is read in exactly one rung** - `ChangeToTool_W =
  SV_TOOL_NUMBER` at `Centroid-Acroloc-ALLIN1DC.src:2931`. Nothing else in the
  PLC reads it. So if that value becomes a **bin** instead of a raw tool number,
  the entire carousel state machine (`ATCStage`, the switch decode, the
  match/exit, the 20 s watchdog) keeps running unchanged.
- Today `SV_TOOL_NUMBER` equals the tool number, and bins map 1:1 to tools, so
  `M6T31` asks the carousel for a nonexistent bin 31 and faults at the 20 s
  watchdog.

## Approach: enable Centroid Enhanced ATC mode (native tool-library bins)

Centroid CNC12 has an **Enhanced ATC** (random tool changer) mode. In that mode
CNC12 keeps the tool->bin table itself - the tool library's **bin** column,
which is exactly the "assign tool 31 to bin 2" UI - and `M107` loads
`SV_TOOL_NUMBER` with the **bin location**, not the tool number.

From the SV catalog (`system-variables.md:50`):

> `SV_TOOL_NUMBER` ... In enhanced ATC mode, this is actually a request for a
> carousel bin location.

Because the PLC's only use of `SV_TOOL_NUMBER` is `ChangeToTool_W =
SV_TOOL_NUMBER`, enabling Enhanced ATC means the carousel already chases the
bin. **No change to the tool-change state machine.** The enhanced-ATC variable
names are demonstrated in Centroid's umbrella example
(`docs/official/_ALLIN1DC/_atc/_umbrella/cncm/allin1dc-umbrella-v7.src`):
`RequestedBinPosition_W = SV_TOOL_NUMBER` (line 2543) and `SV_PLC_CAROUSEL_POSITION
= CarouselPosition_W` (line 2530). The umbrella is a **variable-name reference
only** - its two-move put-back flow does not apply here, because this machine's
swap is mechanical/Z-driven.

## Phase A - CNC12 commissioning and discovery (on-machine, no repo change)

1. **Enable Enhanced ATC and set the bin count.** Set the CNC12 ATC-type /
   enhanced-ATC parameter, and `SV_MACHINE_PARAMETER_161` (max carousel bin) =
   12. The exact enable parameter is the one discovery item; confirm it against
   CNC12's ATC configuration screen, cross-checked with how the umbrella example
   is set up.
2. **Build the bin table** in the tool library: tools 1-12 -> bins 1-12 (keeps
   them 1:1 and backward-compatible), then tool 31 -> bin 2, and any other
   high-numbered tools as desired.
3. **Pivotal check (go / no-go for Phase B).** On the CNC12 PLC diagnostic
   screen, run `M6T31` and watch `SV_TOOL_NUMBER` / `ChangeToTool_W`.
   - Reads **2** (the bin) and the carousel indexes to bin 2 -> the feature
     works end to end with **no PLC edit**. Done.
   - CNC12 refuses to proceed without position feedback -> do Phase B.

## Phase B - Minimal PLC handshake (only if Phase A step 3 requires it)

Kept entirely **outside** `ATCStage` so the search logic stays frozen; every
addition tagged `; Acroloc`.

- **Report current bin.** `SV_PLC_CAROUSEL_POSITION` = current bin, sourced from
  the last matched `CarouselToolID_W` (the carousel reads absolute bin IDs off
  its 5 switches, so no dead-reckoning is needed). Place this report in a small
  block in `MainStage` or its own tiny stage.
- **Seed at power-up.** In `InitialStage` (STG2) / `LoadParametersStage` (STG10),
  seed the reported position from `SV_ATC_CAROUSEL_POSITION` (CNC12's last known
  position), mirroring umbrella lines 1198-1199.
- **Ignore put-back entirely.** `SV_ATC_TOOL_IN_SPINDLE` / `PutBackPosition_W`
  are not consumed - there is no put-back to seed on this machine.
- `./compile.sh` after the edit; report the token / warning delta.

## Non-goals

- **No put-back sequencing.** The tool snaps in/out mechanically as Z retracts
  through the ring; the umbrella's two-move `PutBackPosition` dance is not ported.
- No change to `ATCStage`, the 5-switch decode, the match/exit rung, or the 20 s
  `ATCSpin_T` watchdog.
- No change to `mfunc6.mac`. It still runs `M107`; CNC12 decides what
  `SV_TOOL_NUMBER` holds.
- No bidirectional / shortest-path indexing; the carousel spins as it does today.
- No change to how tool offsets are keyed (CNC12 keeps those by tool number).

## Deliverables

1. This design doc.
2. Phase A commissioning procedure (executed on-machine by the owner): enhanced
   ATC enabled, bin table populated, the step-3 check recorded.
3. **If Phase A step 3 requires it:** the minimal `SV_PLC_CAROUSEL_POSITION`
   report + startup seed in the `.src`, tagged `; Acroloc`, verified with
   `./compile.sh`.
4. Doc updates: note enhanced-ATC bin mapping in `docs/plc-spec/atc.md` and in
   the `acroloc-s10` ATC reference (`reference/atc.md` / `reference/atc-flow.md`),
   including that `SV_TOOL_NUMBER` now carries a bin and that tools 1-12 remain
   1:1.

## Testing / rollout

- Phase A is validated on-machine: set P161 = 12 and the enable parameter, build
  the bin table, then confirm `M6T31` drives `SV_TOOL_NUMBER` / `ChangeToTool_W`
  to the assigned bin and the carousel indexes there.
- Regression: confirm tools 1-12 (bins 1-12) still change exactly as before.
- If Phase B is needed: `./compile.sh` clean (token/warning delta reported),
  then re-run the `M6T31` and 1-12 checks on-machine.
