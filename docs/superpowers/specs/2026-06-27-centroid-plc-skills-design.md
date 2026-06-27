# Design: Centroid PLC Skills for the Acroloc Retrofit

**Date:** 2026-06-27
**Status:** Approved (design phase)

## Purpose

Create Claude Code skills that give instant, accurate reference for working on this
repository's Centroid CNC12 / MPU11 PLC program and M-code macros, plus a reusable
knowledge base of official Centroid PLC stage-language programming facts distilled from
the official manual and the bundled example projects.

Two skills are produced, both versioned in this repo under `.claude/skills/`:

1. **`centroid-plc-programming`** — reusable, machine-agnostic reference for the Centroid
   stage/ladder PLC language, resources, system variables, message encoding, and an index
   of the official example projects.
2. **`acroloc-atc`** — this machine's custom logic: a thin, task-oriented navigator over
   the Acroloc ATC + spindle-range code that points to existing docs/code rather than
   duplicating them.

## Goals

- When working in this repo, Claude has immediate orientation to the custom Acroloc logic
  and knows the safety gotchas before editing tool-change code.
- When doing any Centroid PLC work, Claude can resolve syntax, resource types, and system
  variables from distilled reference files instead of re-reading a 1.5 MB PDF each time.
- Knowledge is grounded in primary sources: the official PDF manual cross-checked against
  the ~21 working example `.src` / `.sym` / `plcmsg.txt` files under `docs/official/`.

## Non-goals (YAGNI)

- No exhaustive transcription of the full manuals (no deep hardware/wiring/electrical
  minutiae, no full PLCEXP1616 transcription).
- No duplication of `README.md` / `CLAUDE.md` content — the machine skill links to them.
- No build/test tooling (there is none in this repo; validation is on the machine).

## Decisions (from brainstorming)

| Decision | Choice |
| --- | --- |
| Packaging | Two split skills (general reusable + machine-specific) |
| KB depth | Core language + indexed examples (skip deep hardware minutiae) |
| Location | Both skills in this repo under `.claude/skills/` |
| KB sourcing | PDF manual extraction cross-checked against example `.src`/`.sym` |

## Skill 1 — `centroid-plc-programming`

Location: `.claude/skills/centroid-plc-programming/`

Frontmatter `description` triggers on: any Centroid CNC12 / MPU11 / ALLIN1DC PLC
stage-language or `.src` / `mfunc*.mac` work — syntax, resources, system variables,
messages, or referencing official example PLCs.

### Files

- **`SKILL.md`** — When-to-use; language essentials inline (flat-scan execution model, the
  stage concept, `Name IS Resource` binding, `IF <cond> THEN SET/RST <stage>, ...`); a
  router table pointing into the `reference/` files.
- **`reference/syntax.md`** — Statement forms (`IF/THEN`, `SET`/`RST`, assignment),
  comparison and logic operators (`&&`, `||`, `!`, relational), word↔bit operations
  (e.g. `WTB`), comment style, directives, and the per-scan stage execution model.
- **`reference/resources.md`** — Resource types and addressing: `INP`, `OUT`, `MEM`, `W`,
  `T`, `STG`, float words (`FW`); the suffix naming convention
  (`_I/_O/_M/_W/_T/_SV/_C`); and macro↔PLC access (`#(60000+n)` to read a PLC `OUT`/`MEM`,
  `M94 /bit` set, `M95 /bit` reset).
- **`reference/system-variables.md`** — The `SV_*` system-variable catalog, grouped by
  function (spindle, tool, jog/MPG, coolant, machine parameters, `M94`/`M95` flags).
  Names verified against the example `.sym` files and real usage, not memory.
- **`reference/messages.md`** — Operator-message constant encoding
  (`value = msgNumber + 256 * msgFile`) and the `plcmsg.txt` file format, with a worked
  example (e.g. `45546 = 2 + 256*174`).
- **`reference/examples-index.md`** — Curated index of the example ALLIN1DC projects under
  `docs/official/_ALLIN1DC/`: path + one-line "what this demonstrates" for each (basic
  mill, basic VCP/MPG beta, BOSS VCP, umbrella ATC, umbrella no-throwaway, swingarm ATC,
  spindle brake, low-range reverse, 3rd-axis brake, MSC handbrake, remote start,
  bp-boss, dm45, forest-scientific ATC router, cptools, and the `k1000xx` custom builds).

## Skill 2 — `acroloc-atc`

Location: `.claude/skills/acroloc-atc/`

Frontmatter `description` triggers on: editing or understanding this repo's
`Centroid-Acroloc-ALLIN1DC.src` or `mfunc*.mac` — especially tool-change, carousel, or
spindle-range logic.

### Files

- **`SKILL.md`** — When-to-use; machine orientation (Acroloc mill + ALLIN1DC retrofit,
  custom ATC is the heart); a compact at-a-glance table of the custom `; Acroloc` I/O and
  variables; **task playbooks** (e.g. "to edit tool-change logic: read `mfunc6.mac`, the
  `MainStage` kickoff, and `ATCStage`; mind the no-timeout and position-decode gotchas").
  Links to `centroid-plc-programming`, `README.md`, and `CLAUDE.md` instead of copying
  their content. Notes how to locate custom code (`; Acroloc` marker) and use `plc.map` /
  the `.sym` symbol map (without relying on stale line numbers).
- **`reference/atc-flow.md`** — Tool-change state-machine walkthrough across the three
  places it lives (`mfunc6.mac` → `MainStage` kickoff & safety → `ATCStage` STG16
  indexing); the carousel position encoding table (base-16 written in decimal; `Pos5 = +10`
  not `+16`); and the documented gaps: **no carousel timeout** (`;TODO`) and the
  transmission **shift outputs defined but not driven** (`OUT19`/`OUT20`).
- **`reference/macros.md`** — One line per macro (`mfunc3/4` spindle CW/CCW, `mfunc6` M6
  tool change, `mfunc7/8` mist/flood coolant, `mfunc10/11` clamp on/off) and the shared
  graph/search-mode guard pattern (`IF #4201 || #4202 THEN GOTO 1000` … `N1000`).

## Cross-skill relationship

`acroloc-atc` references `centroid-plc-programming` for all language/syntax/system-variable
lookups, keeping the machine skill thin and task-focused. The general skill has no
dependency on the machine skill.

## Implementation approach

1. Extract text from `docs/official/centroid_plc_programming_manual.pdf` (read in page
   ranges) to source the syntax, resource, system-variable, and message facts.
2. Cross-check every system-variable and resource claim against the real symbols in the
   example `.sym` files and usage in the example `.src` files; prefer what the working code
   actually uses where the manual and code differ.
3. Build `examples-index.md` by scanning each example project's header comment block and
   distinctive logic.
4. Write the machine skill from `README.md`, `CLAUDE.md`, the `.src`, and the macros —
   pointing to them, not duplicating.

## Success criteria

- Both skills load with valid frontmatter and are discoverable in this repo.
- A spot-check of 5+ system variables and 3+ syntax facts in the general skill matches the
  PDF manual and the example `.sym`/`.src` files.
- The machine skill's custom-I/O table and ATC encoding match `README.md` / the `.src`.
- No reference file duplicates `README.md` / `CLAUDE.md` prose; machine skill links to them.
