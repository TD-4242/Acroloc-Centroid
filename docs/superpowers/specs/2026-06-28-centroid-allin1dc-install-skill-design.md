# Design: `centroid-allin1dc-install` knowledge-base skill

**Date:** 2026-06-28
**Status:** Approved (design phase)
**Source:** `centroid_allin1dc_install_manual.pdf` — Centroid ALLIN1DC CNC Control
Installation Manual, CNC12 v5.08+, rev22 (88 content pages).

## Purpose

Create a third in-repo skill that captures the **ALLIN1DC installation and
commissioning** knowledge base from the official install manual, so the model can
answer wiring, hardware, software-configuration, tuning, parameter, and
troubleshooting questions without re-reading the 88-page PDF each time.

This skill is complementary to the two existing skills (which live on the
`skill/centroid-plc-skills` branch / PR #1):

- `centroid-plc-programming` — PLC stage-language (`.src`) and M-code macros.
- `acroloc-atc` — this machine's custom ATC.

The new skill covers a **distinct domain**: hardware install, cabinet wiring,
software setup, motor/spindle commissioning, parameters, and troubleshooting.

## Decisions (from brainstorming)

| Topic | Decision |
| --- | --- |
| Primary uses | All four: wiring/hardware reference, commissioning & tuning, parameter reference, troubleshooting |
| Scope boundary | **Generic only, no machine-specific references.** A faithful, portable capture of the vendor manual; zero references to this repo's Acroloc I/O map, clutch outputs, or gear-shift work |
| Domain boundary | Install/commissioning only. PLC stage-language and M-codes stay in `centroid-plc-programming`; `SKILL.md` points there but adds no machine content |
| Visual content | Capture all *textual* content faithfully (procedures, value tables, terminal/pin assignments, LED meanings, parameter values). For wiring diagrams and the Appendix D schematic set, describe what each shows and cite the **manual page number** + the external schematic-ZIP URL — no embedded images |
| Fidelity | Concrete values verbatim (parameter numbers, voltages, current limits, LED states). Extracted page-by-page from the PDF |
| Location | In-repo `.claude/skills/centroid-allin1dc-install/`, parallel to the other two skills |

## Non-goals (YAGNI)

- No reproduction of circuit schematics as ASCII art — cite page numbers and the
  schematic-ZIP URL instead.
- No machine-specific annotations or cross-links to the Acroloc retrofit.
- No coverage of PLC stage-language or M-code macros (separate skill).
- No re-statement of CNC12 operator-software usage beyond what the install
  manual covers for commissioning.

## Architecture

A `SKILL.md` router plus six focused `reference/*.md` files, mirroring the shape of
the existing `centroid-plc-programming` skill.

### `SKILL.md`

- **Frontmatter:** `name: centroid-allin1dc-install`, plus a `description` that
  triggers on ALLIN1DC install/wiring/commissioning/tuning/parameter/troubleshooting
  questions.
- **When to use / when not:** use for hardware install, cabinet wiring, software
  setup, motor/spindle commissioning, parameters, troubleshooting. Do **not** use
  for `.src`/macro work — that's `centroid-plc-programming`.
- **Essentials:** a brief board overview (what the ALLIN1DC is: built-in 3-axis DC
  servo drive, 16 IN / 9 relay OUT PLC, 6 encoder inputs, analog spindle control;
  expandable to 6 axes) and the recommended commissioning order (install → bench
  test → cabinet wiring → final software config).
- **Reference router table:** one row per reference file (below).
- **Useful resources:** the URLs from the manual's "Useful Resources" page
  (product manuals, schematic-set ZIP, schematic browser, YouTube channel, retrofit
  video series, community forum, tech bulletins, shop) — captured verbatim.

### Reference files

| File | Source chapters | Contents |
| --- | --- | --- |
| `reference/hardware.md` | Ch1, Ch2.2–2.4 | Board capabilities, I/O counts, encoder inputs & requirements, expansion boards, power supply options, **ALLIN1DC LED states** |
| `reference/wiring.md` | Ch5 | Cabinet layout, configuring input voltage/polarity, VM wiring, servo-motor wiring, current limiting, E-stop, limit switches, lube pump, coolant pump, spindle wiring |
| `reference/software-setup.md` | Ch3, Ch4, App A | Windows preinstall requirements & Windows 10 config, CNC12 install, CNC12 software configuration, bench-test procedure |
| `reference/commissioning.md` | Ch6 | Confirm encoder comm, motor software setup, spindle setup, coarse/fine DRO position, homing, tuning max feedrate, manual accel tuning, backlash comp, software travel limits, deadstart, system test |
| `reference/parameters.md` | App C, Ch5.5, Ch6 | Concrete parameter numbers + recommended values: servo-motor compatibility & recommended parameters, current-limit settings, spindle/range config, key setup parameters |
| `reference/troubleshooting.md` | App B, Ch2.4 | Symptom→cause→fix table, LED diagnostics, common bench-test failures |

## Data flow / how it's used

Model encounters an ALLIN1DC install/wiring/tuning/parameter/troubleshooting
question → `SKILL.md` description triggers the skill → router table points to the
relevant `reference/*.md` → the model reads that one file for verbatim values and
procedures, falling back to the cited manual page number for any diagram.

## Construction method

Extract the PDF page-by-page (max 20 pages per Read call; the file is 30.8 MB) and
transcribe textual content faithfully into the reference files. Each reference file
is built from its mapped chapters. Diagrams are noted with their manual page number.

## Success criteria

- A new `centroid-allin1dc-install` skill exists in-repo with `SKILL.md` + six
  `reference/*.md` files.
- `SKILL.md` description reliably triggers on install/wiring/commissioning/parameter/
  troubleshooting questions and routes correctly.
- Parameter values, voltages, current limits, and LED states are captured verbatim
  and traceable to a manual page.
- No machine-specific (Acroloc) content appears anywhere in the skill.
- Wiring diagrams and the Appendix D schematic set are referenced by manual page
  number + the schematic-ZIP URL, not reproduced.
- The skill style and structure match the existing `centroid-plc-programming` skill.
