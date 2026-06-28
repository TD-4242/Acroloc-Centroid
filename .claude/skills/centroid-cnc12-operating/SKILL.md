---
name: centroid-cnc12-operating
description: Use when operating Centroid CNC12 mill software: jogging axes, using the operator panel/MPG/VCP, navigating the F1–F10 softkey menus, setting part zero (WCS), managing tool offsets/library, loading and running jobs, canceling or resuming a job, run-time graphics, power feed, and the Utility menu. NOT for G/M-code language reference, Intercon conversational programming, probing/digitizing, or software configuration/parameters/error codes.
---

# Centroid CNC12 Mill Operating

## When to use / when not

Use this skill for **day-to-day operation** of Centroid **CNC12** mill software: navigating the
main-screen menus (F1–F10), jogging and operating the machine via the operator panel, MPG, or
Virtual Control Panel (VCP), setting part zeros and work coordinate systems, managing the tool
offset and tool library, and loading, running, canceling, or resuming jobs. The reference is the
official **CNC12 Milling Machine Operators Manual** (CNC12 V.5.4+) — generic across all
supported controllers (Acorn, AcornSix, Hickory, Oak, Allin1DC, MPU11, M400, M39).

**Do not use this skill for:**
- **G/M-code language** (syntax, parameters, modal groups, canned cycles) — use `centroid-cnc12-gmcodes`
- **Intercon** conversational programming, **probing**, or **digitizing** — use `centroid-cnc12-intercon-probing`
- **Software configuration**, machine parameters, or error/status codes — use `centroid-cnc12-config`
- **PLC stage-language** (`.src`) or **M-code macro** (`mfunc*.mac`) authoring — use `centroid-plc-programming`

> Note: `centroid-cnc12-gmcodes`, `centroid-cnc12-intercon-probing`, and `centroid-cnc12-config`
> are sibling skills that may not exist yet; route to them when they become available.

## Essentials

The CNC12 main screen has five key areas:

- **DRO** — real-time axis position display with load meters (bars) beneath each axis label.
  A **Distance-to-Go** sub-display below the DRO shows remaining travel for the current move
  (toggle with **Ctrl+D**).
- **Status Window** — shows the active job filename, tool number, feed-rate override, spindle
  speed, and feed-hold state. While a job runs, also shows Part Count, Part #, and Part Time.
- **Message Window** — newest messages at the bottom; scroll with arrow keys. The lowest
  (prompt) line shows control prompts (e.g., "Press CYCLE START to start job" on power-up).
- **Options Window** — the active F-key softkey choices for the current screen. Pressing a
  function key selects that option.
- **User Window** — context-sensitive area: G-code lines during a job run; data-entry fields
  for part zeros, tool library, and digitizing/probing.

**Machine home** must be set at startup before running any job. On machines with home/limit
switches, press **CYCLE START** to auto-home (runs `c:\cncm\cncm.hom`). On machines without
switches, jog each axis to the home position manually, then press **CYCLE START**.

**F1–F10 main-screen menu map:**

| F-key | Menu | Purpose |
|---|---|---|
| **F1** | Setup | Part zeros, tool offsets, config, feed settings |
| **F2** | Load Job | Load a job file from disk |
| **F3** | MDI | Run a single G/M-code line immediately |
| **F4** | Run | Start, search, resume, and control job execution |
| **F5** | CAM | Open Intercon conversational programmer |
| **F6** | Edit | Open the current job in a G-code text editor |
| **F7** | Utility | Backup/restore, options, diagnostics, file management |
| **F8** | Graph | Graph the toolpath of the loaded program |
| **F9** | Digitize | Touch-probe digitizing (purchased option only) |
| **F10** | Shut Down | Park, power off, or exit the control software |

## Reference router

| Reference file | Use when the question is about |
|---|---|
| `reference/interface.md` | screen layout, DRO, conventions, machine home, the F1–F10 menu map |
| `reference/operator-panel.md` | jogging, MPG, spindle/coolant/feed controls, VCP, keyboard jog & shortcuts |
| `reference/part-setup.md` | part zero, WCS, coordinate-system rotation, transformed WCS |
| `reference/tool-setup.md` | offset library, tool library, tool-life management, laser setup |
| `reference/running-jobs.md` | running, canceling, resuming jobs; run-time graphics; power feed; utility menu |

## Useful resources (from the manual)

- Latest operator manual (PDF): `https://www.centroidcnc.com/centroid_diy/downloads/operator_manuals/centroid-cnc12-mill-operator-manual.pdf`
- All Centroid CNC manuals: `www.centroidcnc.com/centroid_diy/centroid_manuals.html`
- Community forum (free CNC technical support): `https://centroidcncforum.com/`
