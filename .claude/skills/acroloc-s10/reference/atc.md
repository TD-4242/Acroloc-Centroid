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
- **Pick the tool up at full rapid.** The descent from Z0 through the lock engages best
  at the machine's maximum rapid rate (owner, 2026-09-11), so a pickup is a plain `G53 Z-2.000`
  with no `L` rate word. Slow only moves made after the tool is locked.

Two consequences the PLC must respect:

- The spindle must **not** spin while Z is travelling through the ring (the tool is
  locking/unlocking there). This is the reason for the spindle-stop / `ZeroSpeed_I` (INP12)
  feed-hold interlock in `MainStage` (see [atc-flow.md](atc-flow.md)).
- **A manual carousel spin (`ATCManualUnlock_I`, only usable at Z clear/Z0) is a full tool
  swap:** the spindle is empty at Z0, so hand-spinning the carousel changes which tool gets
  picked up on the next Z descent. After a manual spin **both the bin and the active tool are
  unknown.** The PLC forces the bin to 0 = UNKNOWN on manual unlock (`CurrentToolBin_W` /
  `TargetToolBinDisp_W`), reports 0 to CNC12 and **refuses the spindle** until the
  position is proven again (`CarouselMovedByHand_M`; also set at power-up): the operator
  declares the true position, the tool now under the spindle and its bin with the Tool
  Library's **F2 ATC Reset** (which runs `mfunc18.mac`), or runs an M6 to a different
  tool. A program that tries to start the spindle first is cancelled with
  `9068 CAROUSEL MOVED BY HAND - ATC RESET OR TOOL CHANGE`.

## Bin numbering and tool→bin map

The five position switches (`ATC_Pos1_I`..`ATC_Pos5_I`) encode the carousel **bin
(physical position)** — 1..12 — in **base-16 as decimal**; note `ATC_Pos5_I`
contributes **+10**, not +16. The full decode is in [atc-flow.md](atc-flow.md).

**Tool→bin mapping (operator-defined, fixed):** each physical bin permanently
holds one tool ("a tool from bin 5 always returns to bin 5"). Which tool sits in
which bin is set in CNC12's **Tool Library Bin column** (F1 Setup > F2 Tool >
F2 Tool Lib; editable because the machine runs non-random enhanced ATC,
`P160 = 1`). Any of the 200 tools may be assigned any bin 1-12, several tools may
share a bin, dashes = not in the carousel, 0 = in the spindle. `M6T##` makes
CNC12 send that tool's bin to the PLC, which indexes the carousel to it (see
[atc-flow.md](atc-flow.md#tool-to-bin-map--how-m6t-reaches-a-bin)).

## Tooling limits

- **Maximum tool diameter:** TBD — confirm with owner
- **Maximum tool length:** TBD — confirm with owner
- **Maximum tool weight:** TBD — confirm with owner
- **Retention knob / pull-stud type:** TBD — confirm with owner
- **ATC air pressure requirement:** TBD — confirm with owner
