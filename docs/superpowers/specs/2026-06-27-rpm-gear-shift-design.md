# Design: RPM-Based Automatic Gear Shifting (Acroloc 2-speed clutch transmission)

**Date:** 2026-06-27
**Status:** Approved (design phase)
**Target:** `Centroid-Acroloc-ALLIN1DC.src` (the PLC program), spindle/range logic in `MainStage` + a new `GearShiftStage`.

## Purpose

Make the PLC automatically select and engage the correct transmission gear from the
**commanded spindle RPM**, driving the two clutch outputs that are currently defined but
never used (`Spindle_Low_gear_O`/OUT19, `Spindle_High_gear_O`/OUT20). Today the PLC only
*senses* the gear (via `SpinLowRange_I`/INP13) and scales speed; it never commands a shift.

## Machine facts (confirmed with operator)

- The head is a **two-speed transmission with two friction clutches** — one per gear. To
  change gear: release the engaged clutch and engage the other. **The two clutches must
  never be engaged at the same time.**
- A shift **may occur while the spindle is spinning**. The required sequence is:
  **disengage both clutches → let speeds settle → engage the new clutch.**
- **Gear position is not fed back in this design.** The stock definitions include gear
  sense inputs (`SpinLowRange_I`/INP13, `SpinHighRange_I`/INP15 — INP13 was what the stock
  code read for range selection), but this design does not consult them; the engaged gear
  is known only by which clutch output is energized. The system is therefore **open-loop**
  on gear position. (If the INP13 switch proves to be wired and reliable, a one-rung
  sanity check — low commanded, settle elapsed, INP13 not made → fault — is a natural
  future hardening step.)
- **No exact rev-match is required (owner decision):** the shift coasts in neutral for a
  fixed dwell (1–2 s) and then engages. During the coast the DAC already commands the
  motor through the new gear's ratio, so the motor side arrives near the right speed
  passively; `SV_MEASURED_SPINDLE_SPEED` is not used.

## Decisions (from brainstorming)

| Topic | Decision |
| --- | --- |
| Shift trigger | On-the-fly, RPM-driven (may shift while spinning) |
| Shift sequence | Both clutches release → coast a fixed dwell (motor retargeted via DAC ratio) → engage target clutch |
| Crossover source | Dedicated machine parameter + hysteresis deadband |
| Engage gate | Fixed coast dwell (P944 ms, default 1500) — no rev-match, no speed feedback, no fault path |
| Gear feedback | None — open-loop, gear = clutch-output state |
| Power-up default | **Low** range (engage low clutch, `SpindleRange_W = 1`) |

## Non-goals (YAGNI)

- No more than two ranges (the existing 4-range scaffolding in the range block stays, but
  only ranges 1=low and 4=high are driven).
- No closed-loop gear confirmation. The coast dwell + settle lockout are the only
  assurances.
- No change to the M3/M4 spindle start/stop, ATC, or coolant logic beyond the interlocks
  named below.

## Architecture

Two pieces, both tagged `; Acroloc`:

1. **Range-decision block in `MainStage`** (replaces the current
   `IF True_M THEN SpindleRange_W = 4` / `IF SpinLowRange_I THEN SpindleRange_W = 1` pair):
   - Compute `DesiredRange_W` from `SV_PC_COMMANDED_SPINDLE_SPEED`:
     - `commanded >= Crossover + Hysteresis` → high (4)
     - `commanded <= Crossover - Hysteresis` → low (1)
     - inside the deadband → leave `DesiredRange_W` unchanged (no hunting)
   - If `DesiredRange_W != EngagedRange_W` AND not already shifting AND not `ATCStage`
     → `SET GearShiftStage`.
   - When not shifting, `SpindleRange_W = EngagedRange_W` (so the existing
     `SpinRangeAdjust_FW`/DAC math always reflects the engaged gear).

2. **`GearShiftStage`** — a latched state machine (modeled on `ATCStage`) that performs the
   shift across scans:
   - **Step A — Neutral + retarget:** `RST Spindle_Low_gear_O, RST Spindle_High_gear_O`,
     and `SpindleRange_W = DesiredRange_W` so the existing DAC computation
     (`TwelveBitSpeed_FW / SpinRangeAdjust_FW`) re-commands the motor to the new gear's
     speed for the current commanded S (a passive motor-side speed match).
   - **Step B — Coast:** start `GearCoast_T` once on entry (P944 ms; 0 → default 1500) and
     coast in neutral until it expires. No speed feedback is read; a dwell always elapses,
     so there is **no fault path** in the shift.
   - **Step C/D — Engage & complete:** on dwell expiry, `SET` the target clutch only
     (low → `SET Spindle_Low_gear_O`; high → `SET Spindle_High_gear_O`),
     `EngagedRange_W = DesiredRange_W`, start the settle lockout
     (`GearClutchSettle_T` + `GearSettleActive_M`), `RST GearShiftStage`.

### Hard mutual-exclusion interlock

A single guarantee line, evaluated every scan **after** all gear logic, forces a safe state
if both outputs are ever asserted together:
`IF Spindle_Low_gear_O && Spindle_High_gear_O THEN RST Spindle_Low_gear_O, RST Spindle_High_gear_O, EngagedRange_W = 0, <post fault>`.
The two clutch outputs are mutually exclusive at all times. `EngagedRange_W = 0` marks the
gear state unknown (we forced neutral), so the next valid demand re-triggers a full shift
instead of trusting a stale engaged value — without it the machine would run in neutral
forever after a fault reset, since the kickoff needs `DesiredRange_W != EngagedRange_W`.

### Power-up / init

In the init/parameter-load path, command **low** as the deterministic default:
`SET Spindle_Low_gear_O, RST Spindle_High_gear_O, EngagedRange_W = 1, SpindleRange_W = 1`.

## New symbols (tagged `; Acroloc`)

Names are fixed here; concrete resource/parameter numbers are assigned during planning and
**must be verified free** against `plc.map` / the CNC12 parameter map before use.

| Symbol | Kind | Role |
| --- | --- | --- |
| `GearShiftStage` | `STG` | The shift state machine |
| `DesiredRange_W` | `W` | Gear wanted by RPM logic (1 low / 4 high; 0 = unknown after a both-clutch fault) |
| `EngagedRange_W` | `W` | Gear currently engaged (open-loop; tracks the energized clutch) |
| `GearCoast_T` | `T` | Neutral coast dwell before engaging |
| `GearClutchSettle_T` | `T` | Post-engage settle / re-shift lockout dwell |
| `GearCoastStarted_M` | `MEM` | Coast timer armed once per shift |
| `GearSettleActive_M` | `MEM` | Settle lockout latch (blocks a re-shift until the dwell expires) |
| Crossover RPM | `SV_MACHINE_PARAMETER_941` | Low/high changeover speed (≤ 0 disables auto-shift) |
| Hysteresis RPM | `SV_MACHINE_PARAMETER_942` | Deadband half-width around crossover |
| Coast dwell | `SV_MACHINE_PARAMETER_944` | Neutral coast time in ms (0 → default 1500). P943 is reserved (was rev-match tolerance; unused) |
| Clutch settle dwell | `SV_MACHINE_PARAMETER_945` | Settle/lockout time in ms (0 → default 500) |

The both-clutch fault reuses the stock `SPINDLE_FAULT_MSG_C` message rather than a new
`_C` constant. Reused existing symbols: `SpindleRange_W` (W64), `SpinRangeAdjust_FW` (FW1),
`SV_PC_COMMANDED_SPINDLE_SPEED`, `Spindle_Low_gear_O` (OUT19), `Spindle_High_gear_O`
(OUT20).

## Faults & edge cases

- **The shift sequence itself has no fault path.** A coast dwell always elapses, so a
  shift always completes; a wrong dwell length shows up as a rough engagement to tune
  (P944), not a fault.
- **Both clutches asserted:** the interlock above forces neutral + fault and marks
  `EngagedRange_W = 0` so the next demand re-shifts.
- **Shift requested during a tool change:** inhibited while `ATCStage` is set; the gear
  decision waits until the ATC sequence completes.
- **Spindle disabled / stopped when a shift is wanted:** the sequence still runs — it
  coasts the dwell at zero speed and engages. (A threshold-crossing S-word while the
  spindle is off costs one dwell, never a fault.)
- **Hunting near the threshold:** prevented by the hysteresis deadband.
- **Known, accepted:** `SV_PC_COMMANDED_SPINDLE_SPEED` includes the spindle-override knob,
  so sweeping the override across the crossover mid-cut triggers a shift (neutral drop
  under load). If this proves disruptive in practice, derive the decision from the
  un-overridden S value or debounce the desire before kicking a shift.

## Why a fixed coast dwell (not a rev-match)

An earlier revision gated the engage on `SV_MEASURED_SPINDLE_SPEED` being within a
tolerance of the commanded speed, with a timeout → fault. That was dropped (owner
decision): it depended on unverified feedback semantics (motor-side vs spindle-side
encoder — a spindle-side encoder just coasts while decoupled and can never match a higher
target; sign in M4/reverse was also unverified) and it hard-faulted in reachable states
(e.g. a threshold-crossing S-word while the spindle is stopped). The coast dwell needs no
feedback at all: the motor is passively retargeted through the new ratio during the coast,
and the friction clutches absorb the residual mismatch. Tune P944 (1–2 s) on the machine.

## Success criteria

- Commanding an S below the crossover engages **low** (only OUT19 on); commanding above
  engages **high** (only OUT20 on); both never on together.
- A change in commanded S that crosses the threshold (± hysteresis) triggers
  neutral → coast dwell → engage, with the spindle ending at the commanded RPM in the new
  gear.
- `SpindleRange_W`/`SpinRangeAdjust_FW` and the DAC always match the engaged clutch.
- Power-up leaves the low clutch engaged and `SpindleRange_W = 1`.
- All new code is tagged `; Acroloc`; the mutual-exclusion interlock is present.
