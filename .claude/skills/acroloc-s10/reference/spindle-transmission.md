# Spindle & transmission

Spindle and two-speed gear transmission of the Acroloc Series 10.

## Transmission

The Acroloc Series 10 has a **two-speed transmission** (low gear / high gear). In this
repo's PLC, the two ranges correspond to the `; Acroloc` outputs `Spindle_Low_gear_O`
(OUT19) and `Spindle_High_gear_O` (OUT20). See the I/O table in
[../SKILL.md](../SKILL.md) for those definitions.

> **Safety interlock:** the low-gear and high-gear outputs must **never** both be
> energized at once. Any future shift logic must release one before engaging the other.

- **Low-gear RPM range:** ~0–1200 RPM (owner, 2026-07-05)
- **High-gear RPM range:** ~1000–3500 RPM (owner, 2026-07-05)
- **Maximum spindle RPM:** ~3500 RPM (high gear)
- **Shift mechanism:** two friction clutches, one per gear, driven by OUT19/OUT20; the
  PLC shifts automatically from commanded RPM (crossover P941 = 1100 ± P942 = 100,
  neutral coast dwell P943) — see the "Automatic RPM-based gear shifting" section of
  the repo `README.md`.

## Spindle

- **Spindle taper (e.g. NMTB/CAT/BT 30/40/50):** TBD — confirm with owner
- **Drawbar (power vs. manual) and retention-knob / pull-stud style:** TBD — confirm with owner
- **Spindle motor horsepower and type (DC / AC / vector):** TBD — confirm with owner
