# ATC & tooling

Physical facts about the Acroloc Series 10 automatic tool changer (ATC). For the M6
tool-change control flow and carousel position encoding, see
[atc-flow.md](atc-flow.md).

## Capacity

- **Carousel capacity:** 12 tools.

## Tool numbering

Carousel tool IDs are **base-16 encoded as decimal** across the five position switches
(`ATC_Pos1_I`..`ATC_Pos5_I`); note `ATC_Pos5_I` contributes **+10**, not +16. The full
decode is documented in [atc-flow.md](atc-flow.md).

- **Tool-numbering scheme as used at the machine (pocket-to-tool convention):** TBD — confirm with owner

## Tooling limits

- **Maximum tool diameter:** TBD — confirm with owner
- **Maximum tool length:** TBD — confirm with owner
- **Maximum tool weight:** TBD — confirm with owner
- **Retention knob / pull-stud type:** TBD — confirm with owner
- **ATC air pressure requirement:** TBD — confirm with owner
