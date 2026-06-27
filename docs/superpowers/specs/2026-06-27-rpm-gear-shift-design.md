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
  **disengage both clutches → adjust motor speed → engage the new clutch.**
- **There is no gear-position feedback input.** The engaged gear is known only by which
  clutch output is energized. The system is therefore **open-loop** on gear position.
  `SpinLowRange_I` (INP13) is **not** used for selection in this design.
- Speed feedback `SV_MEASURED_SPINDLE_SPEED` (RPM) is available and is used to rev-match
  before engaging.

## Decisions (from brainstorming)

| Topic | Decision |
| --- | --- |
| Shift trigger | On-the-fly, RPM-driven (may shift while spinning) |
| Shift sequence | Both clutches release → adjust motor speed → engage target clutch |
| Crossover source | Dedicated machine parameter + hysteresis deadband |
| Rev-match gate | Wait until `SV_MEASURED_SPINDLE_SPEED` is within tolerance of target, then engage; timeout fallback |
| Gear feedback | None — open-loop, gear = clutch-output state |
| Power-up default | **Low** range (engage low clutch, `SpindleRange_W = 1`) |

## Non-goals (YAGNI)

- No more than two ranges (the existing 4-range scaffolding in the range block stays, but
  only ranges 1=low and 4=high are driven).
- No closed-loop gear confirmation (no position sensor exists). The settle dwell + rev-match
  are the only assurances.
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
   - **Step A — Neutral:** `RST Spindle_Low_gear_O, RST Spindle_High_gear_O`.
   - **Step B — Rev-match command:** `SpindleRange_W = DesiredRange_W` so the existing DAC
     computation (`TwelveBitSpeed_FW / SpinRangeAdjust_FW`) re-commands the motor to the new
     gear's speed for the current commanded S.
   - **Step C — Wait for match:** when `|SV_MEASURED_SPINDLE_SPEED - target| <= Tolerance`,
     proceed. A rev-match timeout timer bounds this (see Faults).
   - **Step D — Engage:** `SET` the target clutch only (low → `SET Spindle_Low_gear_O`;
     high → `SET Spindle_High_gear_O`), start the clutch-settle timer.
   - **Step E — Complete:** on settle expiry, `EngagedRange_W = DesiredRange_W`,
     `RST GearShiftStage`.

### Hard mutual-exclusion interlock

A single guarantee line, evaluated every scan **after** all gear logic, forces a safe state
if both outputs are ever asserted together:
`IF Spindle_Low_gear_O && Spindle_High_gear_O THEN RST Spindle_Low_gear_O, RST Spindle_High_gear_O, <post fault>`.
The two clutch outputs are mutually exclusive at all times.

### Power-up / init

In the init/parameter-load path, command **low** as the deterministic default:
`SET Spindle_Low_gear_O, RST Spindle_High_gear_O, EngagedRange_W = 1, SpindleRange_W = 1`.

## New symbols (tagged `; Acroloc`)

Names are fixed here; concrete resource/parameter numbers are assigned during planning and
**must be verified free** against `plc.map` / the CNC12 parameter map before use.

| Symbol | Kind | Role |
| --- | --- | --- |
| `GearShiftStage` | `STG` | The shift state machine |
| `DesiredRange_W` | `W` | Gear wanted by RPM logic (1 low / 4 high) |
| `EngagedRange_W` | `W` | Gear currently engaged (open-loop; tracks the energized clutch) |
| `GearRevMatch_T` | `T` | Rev-match wait timeout |
| `GearClutchSettle_T` | `T` | Post-engage clutch settle dwell |
| `GearShiftFault_C` | `_C` | Operator message: shift timed out / both-clutch fault |
| Crossover RPM | `SV_MACHINE_PARAMETER_n` | Low/high changeover speed |
| Hysteresis RPM | `SV_MACHINE_PARAMETER_n` | Deadband half-width around crossover |
| Rev-match tolerance | `SV_MACHINE_PARAMETER_n` | Allowed `|measured-target|` to engage |
| Rev-match timeout | `SV_MACHINE_PARAMETER_n` | Max wait in Step C |
| Clutch settle dwell | `SV_MACHINE_PARAMETER_n` | Step D dwell |

Reused existing symbols: `SpindleRange_W` (W64), `SpinRangeAdjust_FW` (FW1),
`SV_PC_COMMANDED_SPINDLE_SPEED`, `SV_MEASURED_SPINDLE_SPEED`, `Spindle_Low_gear_O` (OUT19),
`Spindle_High_gear_O` (OUT20), `SpindleEnableOut_O` (OUT7), `ZeroSpeed_I` (INP12).

## Faults & edge cases

- **Rev-match timeout (Step C):** if `SV_MEASURED_SPINDLE_SPEED` never reaches tolerance
  before `GearRevMatch_T` expires → **post `GearShiftFault_C`, leave both clutches released
  (neutral), drop `SpindleEnableOut_O`**, and hold (do not slam a clutch at a mismatched
  speed). Operator clears by stopping/resetting. (Confirm this policy on review.)
- **Both clutches asserted:** the interlock above forces neutral + fault.
- **Shift requested during a tool change:** inhibited while `ATCStage` is set; the gear
  decision waits until the ATC sequence completes.
- **Spindle disabled / stopped when a shift is wanted:** the sequence still runs; with the
  motor at/near zero, Step C is satisfied quickly and the target clutch engages.
- **Hunting near the threshold:** prevented by the hysteresis deadband.

## Key assumption / primary risk to validate on the machine

Step C waits on `SV_MEASURED_SPINDLE_SPEED` **while both clutches are disengaged**. This
assumes that feedback reflects the **motor** side (which is being re-commanded), not a
spindle-side encoder that would merely coast while decoupled. **If the feedback is
spindle-side, Step C cannot rev-match** and must fall back to a fixed dwell timer
(`GearClutchSettle_T`-style) before engaging. Validate which side the feedback measures
before trusting Step C; the implementation should make the fixed-dwell fallback easy to
select.

## Success criteria

- Commanding an S below the crossover engages **low** (only OUT19 on); commanding above
  engages **high** (only OUT20 on); both never on together.
- A change in commanded S that crosses the threshold (± hysteresis) triggers
  neutral → rev-match → engage, with the spindle ending at the commanded RPM in the new gear.
- `SpindleRange_W`/`SpinRangeAdjust_FW` and the DAC always match the engaged clutch.
- Power-up leaves the low clutch engaged and `SpindleRange_W = 1`.
- A rev-match that never converges faults cleanly into neutral rather than engaging.
- All new code is tagged `; Acroloc`; the mutual-exclusion interlock is present.
