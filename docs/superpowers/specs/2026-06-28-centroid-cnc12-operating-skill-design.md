# Design: `centroid-cnc12-operating` knowledge-base skill

**Date:** 2026-06-28
**Status:** Approved (design phase)
**Source:** `centroid-cnc12-mill-operator-manual.pdf` — Centroid CNC12 Milling Machine
Operators Manual, CNC12 V5.4+, © 2025 (506 pages). Covers all Centroid controllers
(Acorn, AcornSix, Hickory, Oak, Allin1DC, MPU11, M400, M39).

## Purpose

Create a skill that captures **how to operate CNC12** (the control software an operator
runs on the Windows PC) from the official operator manual, so the model can answer
operating questions — panel/jog, screen navigation, part setup, tool setup, and running
jobs — without re-reading the 506-page PDF each time.

## Context: this is sub-project A of a four-skill decomposition

The operator manual is too large and spans too many distinct domains for a single skill.
It is decomposed into four skills, each built through its own design → spec → plan →
implementation cycle. This spec covers **only skill A**.

| # | Skill | Chapters | Domain |
| --- | --- | --- | --- |
| **A** | **`centroid-cnc12-operating`** | **1–7** | **Operating the control (this spec)** |
| B | `centroid-cnc12-gmcodes` | 11–14 | G-code / M-function / macro language + generic ATC M-codes |
| C | `centroid-cnc12-intercon-probing` | 8–10 | Intercon conversational programming, probing, digitizing |
| D | `centroid-cnc12-config` | 15, 16, 18 | Configuration, parameters, PID, smoothing, errors, glossaries |

These complement the three skills already on `main`:

- `centroid-plc-programming` — PLC stage-language (`.src`) and `mfunc*.mac` macros.
- `acroloc-atc` — this machine's custom ATC.
- `centroid-allin1dc-install` — hardware install, wiring, commissioning, parameters,
  troubleshooting.

## Decisions (from brainstorming)

| Topic | Decision |
| --- | --- |
| Primary uses | Operating CNC12 day-to-day: operator panel/jog/MPG/VCP, main-screen menus, part setup, tool setup, running/resuming jobs, utility menu |
| Decomposition | One of four sibling skills; build order A → (B/C/D as chosen later). This spec is skill A only |
| Scope boundary | **Generic only, no machine-specific references.** A faithful, portable capture of the vendor manual; zero references to this repo's Acroloc I/O map, ATC, or gear-shift work |
| Domain boundary | Operating only (Ch 1–7). G/M-code language → skill B; Intercon/probing/digitizing → skill C; configuration/parameters/errors → skill D. `SKILL.md` points to those siblings by name but adds none of their content |
| Visual content | Capture all *textual* content faithfully (keystrokes, softkey paths, field names, menu values, procedures). CNC12 screenshots are images in the manual — cite the **manual page number**, do not reproduce |
| Fidelity | Keystrokes, softkey paths (`F1 Setup → …`), field names, and menu values transcribed verbatim. Extracted page-by-page from the PDF |
| Location | In-repo `.claude/skills/centroid-cnc12-operating/`, parallel to the other skills |

## Non-goals (YAGNI)

- No G-code / M-function / macro language reference — that is skill B.
- No Intercon, probing, or digitizing content — that is skill C.
- No configuration/parameter tables, PID, smoothing, or error-message reference — skill D.
- No machine-specific annotations or cross-links to the Acroloc retrofit.
- No reproduction of CNC12 screenshots — cite page numbers instead.

## Architecture

A `SKILL.md` router plus five focused `reference/*.md` files, mirroring the shape of the
existing `centroid-allin1dc-install` skill.

### `SKILL.md`

- **Frontmatter:** `name: centroid-cnc12-operating`, plus a `description` that triggers on
  operating questions (how to jog / use the operator panel or MPG / navigate the F-key
  menus / set up a part or tool / run, cancel, or resume a job) and explicitly **not** on
  G/M-code, Intercon/probing, or parameter/config questions.
- **When to use / when not:** use for operating the control. Do **not** use for the G/M-code
  language (→ `centroid-cnc12-gmcodes`), Intercon/probing/digitizing
  (→ `centroid-cnc12-intercon-probing`), or configuration/parameters/errors
  (→ `centroid-cnc12-config`); these siblings may not exist yet but are named for routing.
- **Essentials:** a brief orientation (the DRO/status/message windows, the F1–F10
  main-screen layout, machine home) and a pointer to the reference router.
- **Reference router table:** one row per reference file (below).
- **Useful resources:** the URLs from the manual's "Additional Resources" chapter (Ch 17) —
  product manuals, forum, tech support — captured verbatim.

### Reference files

| File | Source chapters | Contents |
| --- | --- | --- |
| `reference/interface.md` | Ch 1, Ch 3 | DRO & distance-to-go, status/message/options/user windows, conventions, machine home, M/G-code overview, unlocking software features, Centroid API, multi-display; the **F1–F10 main-screen menu map** (navigation hub) |
| `reference/operator-panel.md` | Ch 2 | Axis jog buttons, slow/fast, inc/cont, x1/x10/x100, MPG, single block, cycle start, feed-rate override, feed hold, tool check, cycle cancel, E-stop, spindle controls, coolant controls, aux function keys, VCP, keyboard jog panel, MDI from the keyboard, keyboard shortcut keys |
| `reference/part-setup.md` | Ch 4 | Part-setup operation description & examples, Work Coordinate Systems (WCS) configuration, Coordinate System Rotation (CSR), Transformed WCS (TWCS) |
| `reference/tool-setup.md` | Ch 5 | Offset library, tool library, tool-life management menu, laser setup |
| `reference/running-jobs.md` | Ch 6, Ch 7 | Active job run screen with G-code display, run-time graphics screen, canceling a job, resuming a canceled job, run menu, power feed, communications stress test, the utility menu |

## Data flow / how it's used

Model encounters a CNC12 operating question → `SKILL.md` description triggers the skill →
router table points to the relevant `reference/*.md` → the model reads that one file for
verbatim keystrokes/paths/procedures, falling back to the cited manual page number for any
screenshot. Cross-domain questions are routed to the named sibling skill instead.

## Construction method

Extract the PDF page-by-page (max 20 pages per Read call; the file is 54.5 MB) and
transcribe textual content faithfully into the reference files. Each reference file is
built from its mapped chapters. Screenshots are noted with their manual page number.

## Success criteria

- A new `centroid-cnc12-operating` skill exists in-repo with `SKILL.md` + five
  `reference/*.md` files.
- `SKILL.md` description reliably triggers on operating questions and routes correctly, and
  declines (points to a sibling skill) for G/M-code, Intercon/probing, and config/parameter
  questions.
- Keystrokes, softkey paths, field names, and menu values are captured verbatim and
  traceable to a manual page.
- No machine-specific (Acroloc) content appears anywhere in the skill.
- CNC12 screenshots are referenced by manual page number, not reproduced.
- The skill style and structure match the existing `centroid-allin1dc-install` skill.
