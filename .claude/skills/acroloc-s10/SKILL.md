---
name: acroloc-s10
description: Use for facts about this machine — an Acroloc Series 10 vertical mill retrofitted with a Centroid ALLIN1DC (MPU11) controller — including its axis travels and usable envelope, spindle and two-speed transmission, work envelope and table, and automatic tool changer (ATC) capacity and tooling limits; ALSO use when editing or understanding this repo's Centroid-Acroloc-ALLIN1DC.src or mfunc*.mac, especially the custom ATC carousel, tool-change M6 flow, spindle gear-range logic, or any code tagged "; Acroloc". Points to centroid-plc-programming for PLC language reference.
---

# Acroloc Series 10 (this machine)

## Machine orientation

This repo is the PLC program and M-code macros for an **Acroloc mill retrofitted with a
Centroid ALLIN1DC (MPU11) motion controller**. The machine is not a software application
you build on this machine — it runs on the Windows control PC under CNC12. See
[README.md](../../README.md) and [CLAUDE.md](../../CLAUDE.md) for background, build/deploy
instructions, and PLC architecture overview.

This machine is an **Acroloc Series 10** vertical mill. Its physical capabilities and
specifications are documented in the machine-fact reference files below (axes & travel,
spindle & transmission, ATC & tooling, work envelope & table). The **automatic tool
changer (ATC)** — a carousel indexer grafted onto Centroid's stock ALLIN1DC mill PLC — is
one subsystem; its control implementation lives in this repo's PLC source and macros.
Every custom code addition is tagged `; Acroloc` in `Centroid-Acroloc-ALLIN1DC.src`. Use
that marker to locate all custom code:

```bash
grep -n "; Acroloc" Centroid-Acroloc-ALLIN1DC.src
```

For PLC language syntax and resource-addressing rules, see the
[centroid-plc-programming](../centroid-plc-programming/SKILL.md) skill.

---

## Machine reference (by subsystem)

Each subsystem of this machine has its own reference file. Confirmed facts are recorded;
unconfirmed values are marked `TBD — confirm with owner` (the machine owner is the source
of truth — no specifications are guessed).

| Subsystem | Reference | Covers |
|-----------|-----------|--------|
| Axes & travel | [reference/axes-and-travel.md](reference/axes-and-travel.md) | X/Y/Z travel, usable Z envelope, rapids/feeds, ways, accuracy, home, limit-switch wiring & direction-reversal (Error 411 current-inhibit trap) |
| Spindle & transmission | [reference/spindle-transmission.md](reference/spindle-transmission.md) | Two-speed gear ranges, max RPM, shift mechanism, taper, drawbar, motor |
| ATC & tooling | [reference/atc.md](reference/atc.md) | Carousel capacity (12), tool numbering, tool size/weight limits, retention, air |
| Work envelope & table | [reference/work-envelope-and-table.md](reference/work-envelope-and-table.md) | Table size, T-slots, max workpiece weight, footprint, machine weight |

**Adding a new subsystem over time:** create `reference/<feature>.md` (one subsystem,
self-contained), add one row to the table above, fill known values, and leave anything
unconfirmed as `TBD — confirm with owner`.

---

## Custom I/O & variables at a glance

All entries below are `; Acroloc`-tagged definitions in `Centroid-Acroloc-ALLIN1DC.src`.

### Inputs

| Symbol | Resource | Role |
|--------|----------|------|
| `ATCManualUnlock_I` | INP24 | Front-panel button — unlocks carousel by hand (only when Z is clear and `ATCStage` is not running) |
| `ATCLocked_I` | INP25 | Piston sensor confirming carousel is locked |
| `ATC_Z_ClearedToolChanger_I` | INP26 | **TRUE = Z clear of the tool changer** (spindle may run); **FALSE = spindle in changer** (danger zone). Drives the feed-hold interlock's zone-kill |
| `ATC_Z_Zero_Release_I` | INP27 | Z axis has cleared the tool ring (Z parked high) |
| `ATC_Pos5_I` | INP28 | Carousel position switch — contributes **+10** to `CurrentToolBin_W` (not +16; see encoding note) |
| `ATC_Pos4_I` | INP29 | Carousel position switch — contributes +8 |
| `ATC_Pos3_I` | INP30 | Carousel position switch — contributes +4 |
| `ATC_Pos2_I` | INP31 | Carousel position switch — contributes +2 |
| `ATC_Pos1_I` | INP32 | Carousel position switch — contributes +1 |

### Outputs

| Symbol | Resource | Role |
|--------|----------|------|
| `ATCMotor_O` | OUT17 | Spin the tool carousel |
| `ATCUnlocked_O` | OUT18 | Unlock carousel piston (SET=unlock, RST=lock) |
| `Spindle_Low_gear_O` | OUT19 | Clutch output, driven by power-up + `GearShiftStage`. Truth table: one on = that gear, both on = neutral, **both OFF = LOCKUP** (forbidden) |
| `Spindle_High_gear_O` | OUT20 | Clutch output (see OUT19); **at least one clutch must be ON at all times** |

### Memory bit

| Symbol | Resource | Role |
|--------|----------|------|
| `InBinDecode_M` | MEM443 | Gating flag: set while any position switch is asserted during motor run; cleared when all switches drop |

### System variable

| Symbol | Resource | Role |
|--------|----------|------|
| `M6_SV` | SV_M94_M95_8 | Tool-change request — asserted by `M94 /8` in `mfunc6.mac`, cleared on ATC completion |

### Words

| Symbol | Resource | Role |
|--------|----------|------|
| `CurrentToolBin_W` | W71 | Current carousel **bin** ID, decoded from the 5 position switches during motor run; compared to `TargetToolBin_W` each scan |
| `TargetToolBin_W` | W72 | Target carousel **bin** for the change: the bin whose loaded tool == `SV_TOOL_NUMBER` (via the P701–712 map), or 99 if the tool is in no bin |
| `TargetToolBinDisp_W` | W8 | Macro-readable copy of `TargetToolBin_W` (`#96008`) for the `mfunc6` console message |
| `ToolInBin1_W`..`ToolInBin12_W` | W78–W89 | Tool number loaded in bins 1–12, cached from machine parameters **P701–712** at `LoadParametersStage` (re-read each scan) |

---

## Task playbooks

### 1. Edit tool-change logic

The M6 flow spans three cooperating places — read all three before changing anything:

1. **`mfunc6.mac`** — G-code orchestrator: stops spindle/coolant, parks Z, asserts `M6_SV`, waits for `ATCStage` to reset, then deasserts `M6_SV`. It drives no ATC hardware directly.
2. **`MainStage`** (STG4) — on `M6_SV`, maps the requested tool to its bin (`TargetToolBin_W` = the bin whose loaded tool == `SV_TOOL_NUMBER`, from the P701–712 map; `99` if unmapped) and `SET ATCStage`. Separately, the **spindle-in-changer feed-hold interlock** (not gated on `M6_SV`) keeps the spindle off whenever Z is in the changer zone, and for any program/MDI move entering with the spindle turning it holds feed until `ZeroSpeed_I` (INP12) confirms a stop — `ChangerStopTimer_T` (T23) faults at a 5 s timeout.
3. **`ATCStage`** (STG16) — unlocks carousel (`ATCUnlocked_O`), starts motor (`ATCMotor_O`), accumulates `CurrentToolBin_W` from position switches, and stops/relocks when the ID matches `TargetToolBin_W`.

Full state-machine details, timing, and exact PLC snippets: **[reference/atc-flow.md](reference/atc-flow.md)**.

**Critical gotchas:**
- **20 s search watchdog.** `ATCSpin_T` (T24) is armed at M6 kickoff; if the target tool is never matched within `ATC_SPIN_TIMEOUT_MS_C` (20000 ms), `ATCStage` faults `CAROUSEL MOVE TIME OUT` (msg 63) and stops/relocks the carousel. Any edit to the accumulator lines (`+1 / +2 / +4 / +8 / +10`) or to `InBinDecode_M` gating must still be tested with care — a decode error now faults at 20 s rather than spinning forever.
- **`ATC_Pos5_I` adds +10, not +16.** Carousel bins use base-16 encoded as decimal. Changing Pos5 to +16 breaks bins 10–15 (they will never match).
- **Tool→bin map lives in the PLC (P160=0), not CNC12.** `P701–712` = the tool loaded in bins 1–12; `MainStage` translates `SV_TOOL_NUMBER`→bin. CNC12's enhanced-ATC modes were ruled out on-machine (random reshuffles the map, non-random forces tool==bin). See [reference/atc-flow.md](reference/atc-flow.md#tool-to-bin-map-p701712--how-m6t-reaches-a-bin).

### 2. Edit spindle range/shift logic

`Spindle_Low_gear_O` (OUT19) and `Spindle_High_gear_O` (OUT20) are the two-speed transmission's clutch outputs, now driven by RPM-based automatic shifting (`GearShiftStage`/STG17 + the MainStage decision block). See [reference/spindle-transmission.md](reference/spindle-transmission.md) and [../../docs/plc-spec/gear-shift.md](../../docs/plc-spec/gear-shift.md).

**Clutch truth table (owner, 2026-07-08) — get this right, it's a safety interlock:** exactly one output on = that gear; **both on = neutral** (freewheel); **both OFF = mechanical LOCKUP** (belts jam). At least one output must be energized at all times; both-off is never commanded, and a both-off backstop rung stops the spindle and forces neutral if it ever occurs. The old "each gear output must release the other" / "never both energized" model was **wrong** (both-on is the safe neutral, both-off is the hazard).

### 3. Add or change an M-code macro

See **[reference/macros.md](reference/macros.md)** for the full macro table and PLC variable addressing rules.

Key requirement: **always preserve the graph/search guard** and the `N1000` label:
```gcode
IF #4201 || #4202 THEN GOTO 1000   ;Skip macro if graphing or searching
...
N1000
```
Without this guard, CNC12 will execute hardware commands during dry-run/graphic mode. The `mfunc6.mac` guard uses reversed operand order (`#4202 || #4201`) — leave it as-is; the logic is identical.

### 4. Find and navigate custom code

Locate all custom additions by tag:
```bash
grep -n "; Acroloc" Centroid-Acroloc-ALLIN1DC.src
```

Resolve a symbol to its resource or usage:
```bash
grep -n "SymbolName" Centroid-Acroloc-ALLIN1DC.src
```

`plc.map` and `.sym` can resolve symbols to resource addresses, but their **line numbers go stale** after any edit to the `.src` — never rely on them for source navigation. Recompile to refresh them.

### 5. Edit the VCP / operator panel

This machine's on-screen operator panel (jog keys, spindle/coolant, custom buttons like
`coolant_pump`) is the Centroid VCP under `resources/vcp/`. For the skin/button format and
how-to -- moving/creating buttons, graphics and LED states, wiring a button to a
function/macro/PLC bit, big buttons, live PLC-word displays, and why the VCP will not load --
use the **[centroid-vcp](../centroid-vcp/SKILL.md)** skill. This machine's active skin is the
generated retro theme `acroloc_retro_vcp_skin` -- the skin and all `retro_*` buttons are
emitted by `tools/vcpgen.py` (edit the generator + `BUTTONS` table, run it, check with
`python3 tools/test_vcpgen.py`; never hand-edit the emitted files). The stock
`servo_mill_vcp_skin` remains selectable as a fallback. Custom buttons and the PLC bits they
drive are documented here and in the PLC source; the format knowledge (including the
field-learned Svg2Xaml SVG limits) is generic and lives in `centroid-vcp`.

---

## See also

- [reference/atc-flow.md](reference/atc-flow.md) — M6 tool-change state machine, carousel encoding table, and known gaps
- [reference/macros.md](reference/macros.md) — mfunc*.mac quick reference
- [reference/axes-and-travel.md](reference/axes-and-travel.md) — axis travels and usable envelope
- [reference/spindle-transmission.md](reference/spindle-transmission.md) — spindle and two-speed transmission
- [reference/atc.md](reference/atc.md) — ATC capacity and tooling limits
- [reference/work-envelope-and-table.md](reference/work-envelope-and-table.md) — table and machine envelope
- [centroid-plc-programming](../centroid-plc-programming/SKILL.md) — PLC language syntax, resource addressing, stage mechanics
- [centroid-vcp](../centroid-vcp/SKILL.md) — VCP skin/button authoring (format + how-to for the operator panel)
- [README.md](../../README.md) — machine overview, file descriptions, build/deploy
- [CLAUDE.md](../../CLAUDE.md) — PLC architecture, ATC flow summary, coding conventions
