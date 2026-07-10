# Spindle & transmission

Spindle and two-speed gear transmission of the Acroloc Series 10.

## Transmission

The Acroloc Series 10 has a **two-speed transmission** (low gear / high gear). In this
repo's PLC, the two ranges correspond to the `; Acroloc` outputs `Spindle_Low_gear_O`
(OUT19) and `Spindle_High_gear_O` (OUT20). See the I/O table in
[../SKILL.md](../SKILL.md) for those definitions.

> **Safety interlock (corrected 2026-07-08, owner):** the two clutch outputs encode gear by a
> truth table, **not** simple mutual exclusion — exactly one on = that gear; **both on =
> neutral** (freewheel); **both OFF = mechanical LOCKUP** (the belts fight and jam). At least
> one output must be energized at all times; **never command both off**. If both are ever
> read off, the PLC drops spindle enable (stops the spindle) and commands neutral (both on) to
> release the lockup.

- **Low-gear RPM range:** ~0–1200 RPM (owner, 2026-07-05)
- **High-gear RPM range:** ~1000–3500 RPM (owner, 2026-07-05)
- **Maximum spindle RPM:** ~3500 RPM (high gear)
- **Gear ratios (owner, 2026-07-08):** low = **0.5** (motor→spindle), high = **2.0**. In the PLC
  DAC math these are `SpinRangeAdjust_FW`: low reads **P65 = 0.5** (`SpindleRange_W == 1`), high
  reads **P33 = 2.0** (`SpindleRange_W == 4`, falls back to 1.0 if P33 unset). These drop in as
  the true physical ratios only because CNC12's **max spindle speed is set to the motor base
  (~1750 RPM)**, not the high-gear max — so `CfgMaxSpeed x ratio` yields 875 (low) / 3500 (high).
- **Shift mechanism:** two friction clutches, one per gear, driven by OUT19/OUT20; the
  PLC shifts automatically from commanded RPM (crossover P860 = 800 ± P861 = 100,
  neutral coast dwell P862) — see the "Automatic RPM-based gear shifting" section of
  the repo `README.md`.

## Spindle

- **Spindle taper (e.g. NMTB/CAT/BT 30/40/50):** TBD — confirm with owner
- **Drawbar (power vs. manual) and retention-knob / pull-stud style:** TBD — confirm with owner
- **Spindle motor horsepower and type (DC / AC / vector):** TBD — confirm with owner
- **Spindle-motor VFD:** the motor is driven by a **TECO-Westinghouse F510** inverter. For
  VFD configuration, RS-485 Modbus config backup/restore, parameters, motor auto-tuning,
  braking, and fault codes, see the [teco-f510](../../teco-f510/SKILL.md) skill (a generic
  F510 reference). Keep **this-machine** settings — motor base RPM, decel time, gear ratios —
  here, not in that skill.
