# PLC Specification Document — Design

**Date:** 2026-07-05
**Status:** Approved by owner (this conversation)
**Goal:** A comprehensive, line-referenced specification of the current
`Centroid-Acroloc-ALLIN1DC.src`, organized by subsystem: what each subsystem
does, why it does it, and where it lives in the source.

## Shape (owner decision)

`README.md` is the hub. It gains/restructures into a "PLC subsystems" section:
one short paragraph per subsystem (what it is, in a sentence or two), each
linking to a detail file under `docs/plc-spec/`. Existing README deep-dives
(ATC overview, gear-shift section) are trimmed to summaries that link out —
no duplicated prose.

Rejected alternatives: one monolithic spec file (owner prefers README-linked
sections); putting it all under the acroloc-s10 skill (the skill references
link to these docs instead).

## Detail files (`docs/plc-spec/`)

| File | Covers |
| --- | --- |
| `scan-model.md` | How the PLC executes: flat stage sweep, SET/RST stage enabling, per-scan input/timer snapshot semantics, timer arm/expire/RST behavior, last-write-wins outputs. Every other file links back here instead of re-explaining. |
| `definitions.md` | Resource atlas of the definitions half (src ~1–1185): tables per resource class (INP, OUT, MEM, W/FW, T, SV, constants, STG) — name, resource, line, physical meaning, who reads/writes. `; Acroloc` custom entries flagged. Message-constant encoding (`value = msg + 256*file`) explained once here. |
| `boot.md` | WatchDogStage, InitialStage (power-up defaults incl. low-gear init), LoadParametersStage. |
| `main-stage.md` | MainStage (STG4) decomposed rung-group by rung-group: fault aggregation, spindle enable/direction/DAC ratio math, override knob clamp, coolant, clamp, lube, gear-shift decision block, ATC kickoff + spindle-stop safety, manual carousel unlock. |
| `atc.md` | ATCStage (STG16) + `mfunc6.mac` handshake (M94/M95 /8, M107, M100 wait), 5-switch base-16-as-decimal position decode, InToolSelect_M gating, match/exit, known no-timeout gap. Links to (and supersedes overlap with) `.claude/skills/acroloc-s10/reference/atc-flow.md`. |
| `gear-shift.md` | Gear decision (un-overridden S vs P941±P942 hysteresis) + GearShiftStage (STG17) coast-dwell shift, P943, mutual-exclusion interlock, ATC inhibit, open-loop caveats. Links to the test plan. |
| `jog-and-mpg.md` | JogPanelStage, MPGStage, WirelessMpgStage, JogKeys* stages. |
| `faults-and-messages.md` | CheckCycloneStatusStage/MiniPLCErrorStage (drive/fiber comm), Show*/MessageStage display plumbing, fault bits and message flow. |
| `parameters.md` | Machine-parameter table (P941–P943, P65, and any others the source reads), value semantics, intended values. |

## Per-file conventions

- Every code reference written as `` `Name` (src:NNNN) ``.
- Each file's header pins the commit hash the line numbers were taken from:
  `Line numbers as of <sha>`.
- Sections also cite the stable `; Acroloc ...` comment markers so code can be
  re-found after line numbers drift.
- Known gaps / TODOs consolidated at the bottom of each relevant file.
- ASCII only in new text destined for `.src` comments; docs are plain Markdown.

## Method

1. Read the `.src` end to end, in order — a full line-by-line pass of all
   ~3000 lines, not sampling — writing each detail file as its sections are
   encountered.
2. Read `mfunc*.mac` for the macro side of handshakes.
3. Self-review pass: verify every cited `src:NNNN` against the file at the
   pinned commit before committing.
4. Restructure README last, once the detail files exist to link to.

## Maintenance rule

Add one sentence to `CLAUDE.md`: when a PLC change lands, update the affected
`docs/plc-spec/` section (and its pinned hash) as part of the change.

## Not doing (YAGNI)

- No auto-generation tooling or scripts.
- No HTML rendering / published site.
- No per-stage micro-files beyond the table above.
- No rewrite of the acroloc-s10 skill — its references link to these docs.

## Success criteria

- Every stage and every `; Acroloc` addition in the `.src` is covered by
  exactly one detail file.
- A reader can go from README → subsystem file → exact source line for any
  behavior of the machine.
- All line references verified against the pinned commit.
