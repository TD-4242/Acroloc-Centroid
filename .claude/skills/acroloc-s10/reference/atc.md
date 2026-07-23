# ATC & tooling

Physical facts about the Acroloc Series 10 automatic tool changer (ATC). For the M6
tool-change control flow and carousel position encoding, see
[atc-flow.md](atc-flow.md).

## Capacity

- **Carousel capacity:** 12 tools.

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
