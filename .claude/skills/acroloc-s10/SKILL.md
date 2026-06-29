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

## Custom I/O & variables at a glance

All entries below are `; Acroloc`-tagged definitions in `Centroid-Acroloc-ALLIN1DC.src`.

### Inputs

| Symbol | Resource | Role |
|--------|----------|------|
| `ATCManualUnlock_I` | INP24 | Front-panel button — unlocks carousel by hand (only when Z is clear and `ATCStage` is not running) |
| `ATCLocked_I` | INP25 | Piston sensor confirming carousel is locked |
| `ATC_Z_ClearedToolChanger_I` | INP26 | Spindle has entered the tool changer (at zero RPM zone) |
| `ATC_Z_Zero_Release_I` | INP27 | Z axis has cleared the tool ring (Z parked high) |
| `ATC_Pos5_I` | INP28 | Carousel position switch — contributes **+10** to `CarouselToolID_W` (not +16; see encoding note) |
| `ATC_Pos4_I` | INP29 | Carousel position switch — contributes +8 |
| `ATC_Pos3_I` | INP30 | Carousel position switch — contributes +4 |
| `ATC_Pos2_I` | INP31 | Carousel position switch — contributes +2 |
| `ATC_Pos1_I` | INP32 | Carousel position switch — contributes +1 |

### Outputs

| Symbol | Resource | Role |
|--------|----------|------|
| `ATCMotor_O` | OUT17 | Spin the tool carousel |
| `ATCUnlocked_O` | OUT18 | Unlock carousel piston (SET=unlock, RST=lock) |
| `Spindle_Low_gear_O` | OUT19 | Spindle low-gear shift (defined but **not yet driven** by any stage) |
| `Spindle_High_gear_O` | OUT20 | Spindle high-gear shift (defined but **not yet driven** by any stage) |

### Memory bit

| Symbol | Resource | Role |
|--------|----------|------|
| `InToolSelect_M` | MEM443 | Gating flag: set while any position switch is asserted during motor run; cleared when all switches drop |

### System variable

| Symbol | Resource | Role |
|--------|----------|------|
| `M6_SV` | SV_M94_M95_8 | Tool-change request — asserted by `M94 /8` in `mfunc6.mac`, cleared on ATC completion |

### Words

| Symbol | Resource | Role |
|--------|----------|------|
| `CarouselToolID_W` | W71 | Accumulates current carousel position ID during motor run; compared to target each scan |
| `ChangeToTool_W` | W72 | Target tool number latched from `SV_TOOL_NUMBER` when `M6_SV` fires |

---

## Task playbooks

### 1. Edit tool-change logic

The M6 flow spans three cooperating places — read all three before changing anything:

1. **`mfunc6.mac`** — G-code orchestrator: stops spindle/coolant, parks Z, asserts `M6_SV`, waits for `ATCStage` to reset, then deasserts `M6_SV`. It drives no ATC hardware directly.
2. **`MainStage`** (STG4) — latches `ChangeToTool_W = SV_TOOL_NUMBER` and `SET ATCStage` when `M6_SV` fires; enforces spindle-stop safety via `StopSpinBeforeATC_T` (T23) and `ZeroSpeed_I` (INP12) before the carousel may move.
3. **`ATCStage`** (STG16) — unlocks carousel (`ATCUnlocked_O`), starts motor (`ATCMotor_O`), accumulates `CarouselToolID_W` from position switches, and stops/relocks when the ID matches `ChangeToTool_W`.

Full state-machine details, timing, and exact PLC snippets: **[reference/atc-flow.md](reference/atc-flow.md)**.

**Critical gotchas:**
- **No timeout.** `ATCSpin_T` (T24) is defined but never started or checked — if the target tool is never found, the carousel spins indefinitely. Any edit to the accumulator lines (`+1 / +2 / +4 / +8 / +10`) or to `InToolSelect_M` gating must be tested with care.
- **`ATC_Pos5_I` adds +10, not +16.** Tool numbers use base-16 encoded as decimal. Changing Pos5 to +16 breaks tools 10–15 (they will never match).

### 2. Edit spindle range/shift logic

`Spindle_Low_gear_O` (OUT19) and `Spindle_High_gear_O` (OUT20) are defined with `; Acroloc` markers but appear only in the definitions section — they are never SET, RST, or referenced in any stage or macro. The Acroloc's two-speed transmission shift is not yet automated.

For background on spindle speed and range, see the "Spindle speed & range" section in [README.md](../../README.md). Any implementation must also add interlock logic (each gear output must release the other before engaging).

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

---

## See also

- [reference/atc-flow.md](reference/atc-flow.md) — M6 tool-change state machine, carousel encoding table, and known gaps
- [reference/macros.md](reference/macros.md) — mfunc*.mac quick reference
- [centroid-plc-programming](../centroid-plc-programming/SKILL.md) — PLC language syntax, resource addressing, stage mechanics
- [README.md](../../README.md) — machine overview, file descriptions, build/deploy
- [CLAUDE.md](../../CLAUDE.md) — PLC architecture, ATC flow summary, coding conventions
