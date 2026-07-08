# Spindle & transmission

Spindle and two-speed gear transmission of the Acroloc Series 10.

## Transmission

The Acroloc Series 10 has a **two-speed transmission** (low gear / high gear). In this
repo's PLC, the two ranges correspond to the `; Acroloc` outputs `Spindle_Low_gear_O`
(OUT19) and `Spindle_High_gear_O` (OUT20). See the I/O table in
[../SKILL.md](../SKILL.md) for those definitions.

> **Safety interlock:** the low-gear and high-gear outputs must **never** both be
> energized at once. Any future shift logic must release one before engaging the other.

- **Low-gear RPM range:** TBD — confirm with owner
- **High-gear RPM range:** TBD — confirm with owner
- **Maximum spindle RPM:** TBD — confirm with owner
- **Shift mechanism (manual lever / pneumatic / electric):** TBD — confirm with owner

## Spindle

- **Spindle taper (e.g. NMTB/CAT/BT 30/40/50):** TBD — confirm with owner
- **Drawbar (power vs. manual) and retention-knob / pull-stud style:** TBD — confirm with owner
- **Spindle motor horsepower and type (DC / AC / vector):** TBD — confirm with owner
- **Spindle-motor VFD:** the motor is driven by a **TECO-Westinghouse F510** inverter. For
  VFD configuration, RS-485 Modbus config backup/restore, parameters, motor auto-tuning,
  braking, and fault codes, see the [teco-f510](../../teco-f510/SKILL.md) skill (a generic
  F510 reference). Keep **this-machine** settings — motor base RPM, decel time, gear ratios —
  here, not in that skill.
