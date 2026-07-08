# Design: `teco-f510` knowledge-base skill

**Date:** 2026-07-08
**Status:** Approved (design phase)
**Source:** `docs/official/teco-f510-instruction-manual.pdf` — TECO-Westinghouse F510
Inverter Instruction Manual, doc TECO-F510IM Ver 01, 2017.12 (438 pages). The PDF is
**moved** into `docs/official/` from `~/F510_instruction_manual.pdf` as part of this work,
alongside the existing Centroid manuals, so citations resolve for anyone in the repo.

## Purpose

Create an in-repo skill that captures a **focused** knowledge base for the
TECO-Westinghouse **F510 variable-frequency drive (VFD)** — the inverter that drives this
machine's spindle motor — so the model can answer F510 configuration, wiring, control-mode,
parameter, Modbus-communication, motor/auto-tune, accel-decel, braking, and fault questions
without re-reading the 438-page PDF each time.

It is a **generic device reference** (faithful but distilled capture of the vendor manual),
mirroring the existing `centroid-allin1dc-install` and `centroid-plc-programming` skills.
It is complementary to:

- `centroid-allin1dc-install` — the Centroid controller's hardware/wiring/commissioning,
  including its **analog-spindle-output** side.
- `centroid-plc-programming` — PLC stage-language and M-code macros (spindle/gear logic).
- `acroloc-s10` — **this machine's** specific spindle facts, gear ratios, and base RPM.

The new skill covers a **distinct domain**: the VFD itself.

### The seam to document explicitly

The ALLIN1DC sends a **0–10 V analog** speed command (its DAC output) to the F510; the F510
converts that command into three-phase motor drive. That 0–10 V (and optional RS-485) link
is the boundary between this skill (VFD side) and `centroid-allin1dc-install` (controller
side). `SKILL.md` states this seam so the model routes correctly.

## Decisions (from brainstorming)

| Topic | Decision |
| --- | --- |
| Scope / framing | **Generic device reference.** Faithful, portable capture of the F510 manual; no machine-specific settings. `acroloc-s10` cross-links to it; this-machine F510 values (motor base ~1750, decel time, etc.) stay in `acroloc-s10`. |
| Depth | **Focused knowledge base.** Distill the high-value areas for a mill spindle; cite PDF page ranges for everything else. Skip HVAC/pump/PID groups, dimension tables, and 800 HP derating curves — name them and cite the page rather than transcribe. |
| Domain boundary | The VFD only. Controller-side analog output → `centroid-allin1dc-install`; PLC spindle/gear logic → `centroid-plc-programming`; machine-specific spindle facts → `acroloc-s10`. |
| PDF handling | Move `~/F510_instruction_manual.pdf` → `docs/official/teco-f510-instruction-manual.pdf`. |
| Citation style | By section/parameter — e.g. `§4.3 Grp 09`, param `09-01`, `Ch 11.1` — with PDF page ranges where a deep dive helps. Mirrors the install skill. |
| Fidelity | Concrete values captured faithfully (parameter numbers, ranges, defaults, fault codes, terminal names). Machine-specific values excluded. |
| Name / location | `teco-f510`, in-repo `.claude/skills/teco-f510/`, parallel to the other skills. |

## Non-goals (YAGNI)

- No machine-specific settings or cross-links to the Acroloc retrofit inside this skill
  (those live in `acroloc-s10`, which points here).
- No coverage of the HVAC/pump/PID/compressor parameter groups (23/24, PID group 10),
  dimension/derating tables, or fieldbus option cards beyond a one-line pointer — cite the
  page instead of transcribing.
- No reproduction of wiring diagrams as ASCII art — describe and cite the page.
- No PLC stage-language, M-code, or controller-side analog-output content (other skills).

## Architecture

A `SKILL.md` router plus six focused `reference/*.md` files, mirroring the shape of the
existing `centroid-allin1dc-install` skill.

### `SKILL.md`

- **Frontmatter:** `name: teco-f510`, plus a `description` that triggers on F510 VFD
  configuration / wiring / control-mode / parameter / Modbus / motor-auto-tune / accel-decel
  / braking / fault questions, and that names "VFD/inverter/drive" for discovery. States it
  is generic to the F510 (machine-specific settings are in `acroloc-s10`).
- **When to use / when not:** use for F510 config, wiring, control modes, parameters, Modbus
  comms, motor/auto-tune, accel/decel, braking, faults. Do **not** use for the controller's
  analog-output side (`centroid-allin1dc-install`), PLC spindle/gear logic
  (`centroid-plc-programming`), or this machine's spindle facts (`acroloc-s10`).
- **Essentials:** what the F510 is (three-phase induction/PM VFD, 230 V / 460 V classes),
  model numbering, the **three control modes** (V/F, SLV sensorless vector, PM SLV), keypad
  basics (LCD keys, monitor/programming/auto-tune menu structure), and the **0–10 V analog +
  RS-485** interface seam to the ALLIN1DC.
- **Reference router table:** one row per reference file (below).

### Reference files

| File | Source (manual) | Contents |
| --- | --- | --- |
| `reference/parameters.md` | §4.2–4.3 | Atlas of all 24 parameter groups (named) + distilled key params for a mill spindle: Grp 00 (control mode, run/freq command source, communication freq), Grp 02 (IM motor), Grp 08 (protection), Grp 11 (accel/decel, carrier, OV-prevention, S-curve), Grp 13 (maintenance: rating, password/lock, restore-factory), Grp 17 (IM auto-tuning). Parameter format: code, name, range, default, control-mode applicability. |
| `reference/communication.md` | Grp 09, §6.3, §7.3, §11.6 | **RS-485 Modbus RTU**: Grp 09 setup (station address, baud, data format), register addressing convention (`NN-MM` → register), how to **read/download the full config to a PC** (USB-RS485 adapter + Modbus master) and write/clone it back, the RS-485 error-code monitor (12-42), and a note that the base LCD keypad has no numbered parameter-copy function. |
| `reference/setup.md` | Ch 5–8, Grp 17 | Control-mode selection (V/F / SLV / PM SLV), frequency-reference and run-command sources (keypad / analog AI1-AI2 / RS-485 / terminal), motor nameplate entry and auto-tuning procedure, accel/decel time and S-curve, analog-output setup. |
| `reference/braking-and-protection.md` | §11.1, Grp 08/11 | Braking-resistor / braking-unit selection and terminals (P/N), OV-prevention modes and thresholds, deceleration behavior and regen, and the protection parameters (Grp 08). |
| `reference/wiring-and-terminals.md` | Ch 3 | Power terminals (R/S/T, U/V/W, P(+)/N(−) braking), control terminals (digital inputs, analog AI1/AI2, relay outputs R1–R3), RS-485 terminals, model numbering and key specs. Diagrams cited by page, not reproduced. |
| `reference/faults.md` | Ch 10 | Fault-code and warning tables (cause → action), auto-tuning error codes, PM-motor auto-tuning errors, self-diagnosis, symptom→fix. |

## Data flow / how it's used

Model encounters an F510 VFD question → `SKILL.md` description triggers the skill → the
router table points to the relevant `reference/*.md` → the model reads that one file for
faithful values and procedures, falling back to the cited manual section/page for any
diagram or skipped detail. Machine-specific follow-ups route to `acroloc-s10`.

## Construction method

Extract the PDF in ≤20-page Read calls (the file is 12.6 MB). Build each reference file from
its mapped sections, transcribing concrete values (parameter numbers, ranges, defaults,
fault codes, terminal names) faithfully and citing section/parameter (+ page range where
useful). Skipped areas (HVAC/pump/PID, dimensions, derating, fieldbus cards) get a one-line
pointer with a page cite, not a transcription.

## Success criteria

- A new `teco-f510` skill exists in-repo with `SKILL.md` + six `reference/*.md` files.
- `SKILL.md` description reliably triggers on F510 config/wiring/control-mode/parameter/
  Modbus/auto-tune/accel-decel/braking/fault questions and routes correctly.
- The **RS-485 Modbus config-download/upload** procedure is concrete and actionable
  (Grp 09 setup + register addressing + PC-side method).
- Parameter numbers, ranges, defaults, terminal names, and fault codes are captured
  faithfully and traceable to a manual section/page.
- The ALLIN1DC ↔ F510 **0–10 V analog + RS-485 seam** is stated so the model routes VFD vs.
  controller questions correctly.
- No machine-specific (Acroloc) values appear anywhere in the skill.
- `acroloc-s10`'s spindle-transmission reference is updated to point at this skill for VFD
  detail (single cross-link; no duplicated content).
- The `teco-f510-instruction-manual.pdf` lives in `docs/official/`.
- The skill style and structure match the existing `centroid-allin1dc-install` skill.
