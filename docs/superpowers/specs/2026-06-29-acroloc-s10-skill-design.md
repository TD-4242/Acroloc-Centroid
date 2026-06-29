# Design: `acroloc-s10` machine knowledge-base skill

**Date:** 2026-06-29
**Status:** Approved (design phase)
**Supersedes:** the existing `acroloc-atc` skill (renamed and broadened)

## Purpose

Turn the existing code-focused `acroloc-atc` skill into the **complete, extensible
knowledge base for this physical machine** — an **Acroloc Series 10** vertical mill
retrofitted with a Centroid ALLIN1DC (MPU11) motion controller running CNC12.

The ATC (automatic tool changer) is one subsystem, not the whole machine. The skill must
answer questions about the machine's specifications and capabilities (travels, spindle,
work envelope, tooling limits) **and** continue to guide edits to this repo's custom PLC
(`Centroid-Acroloc-ALLIN1DC.src`) and M-code macros (`mfunc*.mac`).

## Rename rationale

`acroloc-atc` implies the skill is only about the tool changer. The machine is an Acroloc
Series 10; the ATC is one capability. Renaming to `acroloc-s10` makes it the umbrella skill
for everything about this machine, with the ATC as one feature among many.

## Architecture: one skill, split into many feature files

A single skill (`acroloc-s10`) whose `SKILL.md` is a thin router over many small,
single-subsystem `reference/*.md` files — one file per feature/capability. Adding a
capability later = drop in a new `reference/<feature>.md` and add one router row. This
mirrors the shape of the sibling `centroid-cnc12-operating` and `centroid-allin1dc-install`
skills.

### Mechanics

- **Move** `.claude/skills/acroloc-atc/` → `.claude/skills/acroloc-s10/` (preserve the
  existing `reference/atc-flow.md` and `reference/macros.md` via `git mv`).
- **`SKILL.md`**: update `name:` to `acroloc-s10`; broaden the `description` to trigger on
  **both** machine-spec/capability questions ("what's the Y travel? how many tools? spindle
  RPM ranges? table size?") **and** the existing custom-PLC/macro editing triggers. Body =
  machine identity (Acroloc Series 10 + Centroid ALLIN1DC retrofit) + a router table with
  one row per reference file.

### `SKILL.md` description scope

Triggers on: this machine's physical specs and capabilities (axis travels, spindle/gear
ranges, work envelope, table, ATC/tooling limits) **and** editing/understanding
`Centroid-Acroloc-ALLIN1DC.src` or `mfunc*.mac` (custom ATC carousel, M6 flow, spindle
two-speed range logic, any code tagged `; Acroloc`). Continues to point to
`centroid-plc-programming` for PLC language reference.

## Reference files (seed set)

Two categories: **machine-fact** files (new) and **control-implementation** files (existing,
carried over). Each file is self-contained.

| File | Category | Covers | Known now |
| --- | --- | --- | --- |
| `reference/axes-and-travel.md` | machine-fact | Per-axis travel, usable envelope, rapids/feedrates, ways/ballscrews, accuracy/repeatability, home/reference positions | X = **31.5 in**, Y = **16 in**, Z = **8 in** (only ~6 in usable, from **−2 to −8**; heavy machining should be done as close to **−2** as possible). Rates/ways/accuracy/home = TBD |
| `reference/spindle-transmission.md` | machine-fact | Gear ranges & RPM per range, max RPM, shift mechanism, spindle taper, drawbar/retention, spindle motor HP/type | Two-speed transmission (low/high gear — ties to `Spindle_Low_gear_O` / `Spindle_High_gear_O` in the PLC). All numeric values = TBD |
| `reference/atc.md` | machine-fact | Carousel capacity, max tool diameter/length/weight, retention-knob/pull-stud type, ATC air pressure, tool-numbering scheme | Capacity = **12 tools**; tool IDs are base-16 encoded as decimal (per the PLC position-switch decode). Size/weight limits, retention type, air pressure = TBD |
| `reference/work-envelope-and-table.md` | machine-fact | Table working surface size, T-slot count/spacing, max workpiece weight, machine footprint & weight | All TBD |
| `reference/atc-flow.md` | control (existing) | M6 tool-change state machine, carousel position encoding, known gaps (no timeout) | Already written — carried over unchanged |
| `reference/macros.md` | control (existing) | `mfunc*.mac` quick reference and PLC-variable addressing rules | Already written — carried over unchanged |

A `reference/utilities.md` (electrical supply, pneumatics, coolant, way-lube) is a natural
later addition — flagged as a follow-up, not part of this initial build.

## Source-of-truth / no-fabrication principle

Unlike the manual-derived sibling skills, there is **no document to transcribe** — the
machine owner is the source of truth. Therefore:

- Record only values the owner supplies, or facts verifiable in-repo (e.g., 12-tool
  capacity and the `; Acroloc` I/O map are derivable from the PLC source).
- **Never invent spec numbers.** Any value not yet supplied is written as an explicit
  **`TBD — confirm with owner`** placeholder so the gap is visible and fillable.
- This makes the skill safe to ship partially complete and to extend incrementally.

## Extensibility convention (documented in `SKILL.md`)

To add a new feature/capability over time:
1. Create `reference/<feature>.md` (one subsystem, self-contained).
2. Add a single row to the `SKILL.md` router table.
3. Fill known values; leave unknowns as `TBD — confirm with owner`.

## Non-goals (YAGNI)

- No PLC language reference — that stays in `centroid-plc-programming`.
- No generic CNC12 operating content — that is `centroid-cnc12-operating`.
- No changes to PLC source or macros as part of this skill work (documentation only).
- No invented specifications; TBD placeholders instead.
- `reference/utilities.md` deferred to a future addition.

## Success criteria

- `.claude/skills/acroloc-s10/` exists (renamed from `acroloc-atc`), with `SKILL.md` +
  the four new machine-fact reference files + the two carried-over control files.
- `SKILL.md` `name:` is `acroloc-s10`; its `description` triggers on both machine-spec
  questions and the existing PLC/macro-editing triggers, and routes correctly.
- Confirmed facts (Series 10; X/Y/Z travels; usable-Z note; 12-tool ATC; two-speed
  transmission) are recorded accurately.
- Every unconfirmed value is an explicit `TBD — confirm with owner`, with no fabricated
  numbers anywhere.
- The existing `atc-flow.md` and `macros.md` content is preserved (no regression to the
  current ATC/macro guidance).
- Skill style and structure match the existing in-repo skills.
