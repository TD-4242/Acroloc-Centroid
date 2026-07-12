# Coolant Pump / Flood-Valve Fix Design

- Date: 2026-07-12
- Status: implemented on `post-release-fixes` (PR #15); on-machine validation outstanding
- Scope: `Centroid-Acroloc-ALLIN1DC.src` (PLC coolant logic + defs), plus doc sync
- Branch: `post-release-fixes` (part of the post-release rollup, PR #15)
- Related: [[acroloc-s10]] coolant macros (`mfunc7.mac`/`mfunc8.mac`)

## Goal

Make the two coolant outputs match this machine's real plumbing so that **flood coolant
actually flows**. Today flood opens a valve but never runs the pump, so no coolant reaches
the nozzles.

## Background

Stock CNC12 treats OUT3 (`Flood_O`) and OUT4 (`Mist_O`) as two independent coolant modes,
and the macros make them mutually exclusive (`M8` sets OUT3 / clears OUT4; `M7` sets OUT4 /
clears OUT3).

This machine's actual plumbing:

- **OUT4 (`Mist_O`) is the coolant pump** — it pressurizes the coolant system.
- **OUT3 (`Flood_O`) is the flood valve** — it routes the pump's output to the workspace
  nozzles. With the valve closed, the pressurized coolant is available at the cleaning hose.

So the useful states are:

| Pump (OUT4) | Valve (OUT3) | Result |
|---|---|---|
| ON | OPEN | Flood coolant at the nozzles |
| ON | CLOSED | Cleaning hose pressurized (wash) |
| OFF | any | Nothing |

**The bug:** because the stock modes are mutually exclusive, flood mode (`M8` / flood button)
drives OUT3=1, OUT4=0 -- valve open, **pump off, no flow**. And "mist" mode (`M7`, OUT4=1,
OUT3=0) is really the cleaning-hose/wash mode (pump on, valve closed).

## Corrected behavior

Two mutually-exclusive coolant modes, selected by the panel buttons, `M8`/`M7`, or
auto-coolant in a program:

- **Flood** (`M8` / flood button) -> pump **and** valve.
- **Wash/hose** (`M7` / the current "mist" button) -> pump only.

The physical outputs are **derived from the selected mode**:

- `OUT3` (flood valve) = flood mode.
- `OUT4` (coolant pump) = flood mode **OR** wash mode.

Off (coolant-off / deselecting the active mode) turns both off. Flood and wash are mutually
exclusive (the valve is either open or closed while the pump runs).

## Design

### Renames (hardware accuracy)

- `Mist_O` (OUT4) -> `CoolantPump_O`, comment: coolant pump; pressurizes the system
  (with valve = flood, without valve = cleaning hose).
- `Flood_O` (OUT3) -> `FloodValve_O`, comment: flood valve; opens the pump to the workspace
  nozzles.
- Update the `M8_SV`/`M7_SV` definition comments (`;(Flood_O On)` -> flood mode = pump+valve;
  `;(Mist_O)` -> mist/wash mode = pump only).

The `Flood`/`Mist` **mode** names (LEDs, `M7`/`M8`, `SelectCoolant*_SV`) are kept: CNC12's
built-in coolant indicator only knows Flood/Mist/Off, so the wash mode shows as "Mist"
on-screen regardless of internal naming.

### Decouple mode selection from the outputs

The two existing coolant rungs keep **selecting the mode** (driving the LEDs and reporting
`SelectCoolant*_SV` to CNC12) but no longer drive the physical outputs. The XOR toggle now
references the mode LED instead of the output:

Flood rung becomes:

```
IF ((CoolFloodLED_O ^ (!CoolAutoModeLED_O && CoolantFloodPD_PD)) ||
   CoolAutoModeLED_O && M8_SV) &&
   !(SV_STOP || CoolantAutoManualPD_PD || CoolAutoModeLED_O && !M8_SV || ErrorFlag_M || DoToolCheck_SV)
  THEN (CoolFloodLED_O), (SelectCoolantFlood_SV)
```

Mist/wash rung becomes (same shape, `CoolMistLED_O` / `M7_SV`):

```
IF ((CoolMistLED_O ^ (!CoolAutoModeLED_O && CoolantMistPD_PD)) ||
   CoolAutoModeLED_O && M7_SV) &&
   !(SV_STOP || CoolantAutoManualPD_PD || CoolAutoModeLED_O && !M7_SV || ErrorFlag_M || DoToolCheck_SV)
  THEN (CoolMistLED_O), (SelectCoolantMist_SV)
```

`Flood_O`/`Mist_O` are removed from these coil lists (the only change to the rung bodies is
the XOR reference and dropping the output coil). Because `Flood_O`/`CoolFloodLED_O` were
always driven identically before, referencing the LED is behavior-preserving for the mode
state.

### Derive the physical outputs from the mode

Two new coil rungs, placed after the toggle + mutual-exclusion rungs so they read the settled
mode state:

```
; Acroloc: drive the coolant hardware from the selected mode.
IF CoolFloodLED_O THEN (FloodValve_O)                    ; OUT3 opens only in flood mode
IF CoolFloodLED_O || CoolMistLED_O THEN (CoolantPump_O)  ; OUT4 pump runs in either mode
```

Because the mode LEDs are already gated off by `SV_STOP` / errors / tool-check in the toggle
rungs, the derived outputs inherit that gating -- no separate output gating needed. These are
the **only** drivers of `FloodValve_O`/`CoolantPump_O` (no double-drive).

### Mutual exclusion on the panel

The `M7`/`M8` macros already clear the opposite mode. Add the same for the panel buttons so
both LEDs cannot light at once (manual mode only, matching the toggle gate):

```
; Acroloc: flood and wash are mutually exclusive (valve open XOR closed)
IF !CoolAutoModeLED_O && CoolantFloodPD_PD THEN RST CoolMistLED_O   ; flood press clears wash
IF !CoolAutoModeLED_O && CoolantMistPD_PD  THEN RST CoolFloodLED_O  ; wash press clears flood
```

Placed after both toggle rungs (so the just-set LED wins) and before the derivation rungs.
A press that turns its own mode off also clears the other -> both off, which is correct.

### Unchanged

- `mfunc7.mac` / `mfunc8.mac` -- they already select opposite modes via `M94`/`M95` on the
  flood/mist bits; the fix is entirely in the PLC output derivation.
- CNC12's coolant indicator (Flood / Mist / Off).

## Testing (on-machine)

No automated tests; validate in CNC12 after compiling/loading. Watch OUT3 (`FloodValve_O`)
and OUT4 (`CoolantPump_O`) in PLC Diagnostics (Alt-I).

1. **Flood button (manual):** OUT4 and OUT3 both -> 1; coolant runs at the workspace nozzles
   (pump audibly runs, valve opens). Result: ______
2. **Wash/"mist" button:** OUT4 -> 1, OUT3 -> 0; the cleaning hose pressurizes, no nozzle
   flow. Result: ______
3. **Switch flood <-> wash:** the pump (OUT4) stays running while the valve (OUT3) toggles;
   only one LED lit at a time. Result: ______
4. **Coolant off:** OUT4 and OUT3 both -> 0. Result: ______
5. **Auto-coolant in MDI:** with auto-coolant selected, `M8` -> flood (pump+valve), `M7` ->
   wash (pump only), `M9` -> off. Result: ______
6. **Fault/stop:** with coolant on, an E-stop / `SV_STOP` drops both outputs. Result: ______

## Docs to update

- `docs/plc-spec/main-stage.md` -- the coolant coil description (Flood/Mist coils) -> mode
  LEDs + derived pump/valve outputs.
- `docs/plc-spec/definitions.md` -- rename the `Flood_O`/`Mist_O` rows to
  `FloodValve_O`/`CoolantPump_O` with the corrected roles.
- `.claude/skills/acroloc-s10/` -- if the coolant outputs/macros are described, note the
  pump/valve reality and the flood = pump+valve rule.
- `docs/backlog.md` -- add this as a completed item.

## Open questions

None.
