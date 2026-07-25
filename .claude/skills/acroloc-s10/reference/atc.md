# ATC & tooling

Physical facts about the Acroloc Series 10 automatic tool changer (ATC). For the M6
tool-change control flow and carousel position encoding, see
[atc-flow.md](atc-flow.md).

## Capacity

- **Carousel capacity:** 12 tools.

## Tool-change mechanism (Z-motion, unique to Acroloc)

This is **not** a typical modern ATC (no arm, gripper, or separate clamp/unclamp step). The
tool locks to and unlocks from the spindle purely by **Z depth** as the spindle travels
through the carousel ring:

- **Z0** (tool-change position): **no tool in the spindle** — it is deposited and resting in
  the carousel bin under the spindle.
- **~Z -1.5"**: the tool automatically, mechanically **locks** into the spindle.
- **~Z -1.75 to -2"**: fully engaged; the spindle may spin.

Two consequences the PLC must respect:

- The spindle must **not** spin while Z is travelling through the ring (the tool is
  locking/unlocking there). This is the reason for the spindle-stop / `ZeroSpeed_I` (INP12)
  feed-hold interlock in `MainStage` (see [atc-flow.md](atc-flow.md)).
- **A manual carousel spin (`ATCManualUnlock_I`, only usable at Z clear/Z0) is a full tool
  swap:** the spindle is empty at Z0, so hand-spinning the carousel changes which tool gets
  picked up on the next Z descent. After a manual spin **both the bin and the active tool are
  unknown.** The PLC forces the bin to 0 = UNKNOWN on manual unlock (`CurrentToolBin_W` /
  `TargetToolBinDisp_W`), but it cannot clear CNC12's current tool at `P160 = 0`
  (`SV_ATC_TOOL_IN_SPINDLE` is CNC12->PLC only) — the operator re-establishes the current
  tool after a manual swap.

## Bin numbering and tool→bin map

The five position switches (`ATC_Pos1_I`..`ATC_Pos5_I`) encode the carousel **bin
(physical position)** — 1..12 — in **base-16 as decimal**; note `ATC_Pos5_I`
contributes **+10**, not +16. The full decode is in [atc-flow.md](atc-flow.md).

**Tool→bin mapping (operator-defined, fixed):** each physical bin permanently
holds one tool ("a tool from bin 5 always returns to bin 5"). Which tool sits in
which bin is set by the operator in machine parameters **P701–712** (`P70b` =
the tool number in bin *b*). `M6T##` looks the tool up and indexes the carousel
to its bin. This is a PLC-side map at `P160 = 0`; CNC12's enhanced-ATC modes are
**not** used (see [atc-flow.md](atc-flow.md#tool-to-bin-map-p701712--how-m6t-reaches-a-bin)).
For a plain 1:1 setup, `P701=1 … P712=12`.

## Tooling limits

- **Maximum tool diameter:** TBD — confirm with owner
- **Maximum tool length:** TBD — confirm with owner
- **Maximum tool weight:** TBD — confirm with owner
- **Retention knob / pull-stud type:** TBD — confirm with owner
- **ATC air pressure requirement:** TBD — confirm with owner
