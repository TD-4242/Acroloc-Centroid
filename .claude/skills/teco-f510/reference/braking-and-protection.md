# F510 Braking & Protection

Dynamic braking (resistor / braking unit), over-voltage prevention, and the protection
parameters. Relevant to any decel-heavy or high-inertia load. Sources: §11.1, Group 11
(OV-prevention), Group 08 (§4.2 p.95-99).

## Dynamic braking — resistor & braking unit (§11.1)

When a motor decelerates faster than it can coast, it regenerates energy back into the DC
bus; a braking resistor dumps that energy as heat so the bus voltage doesn't trip
over-voltage. Two hardware tiers:

- **Built-in braking transistor** — inverters rated **230 V ≤ 30 HP** / **460 V ≤ 40 HP**
  (IP20) have the transistor built in. For braking torque, connect an **external braking
  resistor** across terminals **`B1`/`P`** and **`B2`**.
- **External braking unit** — for **230 V > 40 HP** / **460 V > 50 HP** (IP20), add an
  external **braking unit** (TECO `JNTBU-230` for 230 V / `JNTBU-430` for 460 V) connected to
  the inverter's **`⊕`/`P`** and **`⊖`/`N`** DC terminals, plus a braking resistor across the
  unit's **`B`-`P0`** terminals.

**Sizing** comes from **Table 11.1** (§11.1) by inverter voltage/HP: it lists the braking-unit
model & quantity, the resistor part number / spec (W/Ω) / quantity, resistor dimensions,
braking torque (% / %ED duty), and the **minimum resistance** (Ω and W) allowed on a single
unit. Representative rows:

| Inverter | Built-in? | Resistor (part / spec) | Braking unit | Min. resistance |
| --- | --- | --- | --- | --- |
| 230 V 5 HP | yes | JNBR-390W40 (390 W / 40 Ω) | — | 25 Ω / 680 W |
| 230 V 10 HP | yes | JNBR-780W20 (780 W / 20 Ω) | — | 18 Ω / 900 W |
| 230 V 40 HP | no | JNBR-3KW10 ×2 | JNTBU-230 ×2 | — |
| 460 V 10 HP | yes | JNBR-800W100 (800 W / 100 Ω) | — | 43 Ω / 1600 W |
| 460 V 50 HP | no | JNBR-4R8KW32 ×2 | JNTBU-430 ×2 | 11 Ω / 3000 W |

> Do **not** go below the minimum resistance for the model (over-current on the braking
> transistor). Duty is quoted as **%ED** (typically 10% ED). Keep space and cooling around
> the inverter/unit/resistor. **Never connect a resistor directly across the DC terminals
> `P(+)`/`N(-)`** (§1.2) — it goes on `B1`/`B2` (built-in) or on the braking unit.

## Over-voltage (OV) prevention — Group 11

Instead of (or alongside) a resistor, the drive can **stretch the deceleration** when the DC
bus climbs, to avoid an OV trip:

| Code | Name | Range / options | Default |
| --- | --- | --- | --- |
| 11-40 | OV-Prevention Selection | 0 Disable · 1 Mode 1 · 2 Mode 2 · 3 Mode 3 | 0 |
| 11-38 | Deceleration Start Voltage of OV Prevention | 200V 200–400 / 400V 400–800 V | 300 / 700 |
| 11-39 | Deceleration Stop Voltage of OV Prevention | 200V 300–400 / 400V 600–800 V | 350 / 750 |
| 11-36 | Frequency Gain of OV Prevention | 0.000–1.000 | 0.050 |
| 11-37 | Frequency Limit of OV Prevention | 0.00–400.00 Hz | 5.00 |
| 11-41 | Reference-Frequency-Loss Detection | 0 decel to stop · 1 run at `11-42` level | 0 |
| 11-42 | Reference-Frequency-Loss Level | 0.0–100.0 % | 80.0 |

> Trade-off: OV-prevention lets you decelerate **without** a resistor, but the actual decel
> time stretches (the drive holds off dumping bus energy). A braking resistor gives fast,
> repeatable decel at the cost of heat in the resistor. Choose per how hard/often you brake.

## Protection parameters — Group 08

### Stall prevention (also the decel OV clamp)

| Code | Name | Range / options | Default |
| --- | --- | --- | --- |
| 08-00 | Stall Prevention Function | bitfield: enable/disable in accel / decel / operation; decel by time 1 or 2 | 0000b |
| 08-01 | Stall Prevention Level in Acceleration | 20–200 % | 120 |
| 08-02 | Stall Prevention Level in Deceleration | 200V 330–410 / 400V 660–820 V (DC-bus) | 385 / 770 |
| 08-03 | Stall Prevention Level in Operation | 30–200 % | 120 |
| 08-21 | Limit of Stall Prevention over Base Speed | 1–100 % | 50 |
| 08-22 | Stall Prevention Detection Time in Operation | 2–100 ms | 100 |

### Motor & inverter protection

| Code | Name | Range / options | Default |
| --- | --- | --- | --- |
| 08-05 | Motor Overload Protection (OL1) | bitfield: enable/disable · cold/hot start · standard/special motor | 0001b |
| 08-06 | OL1 Start-up Mode | 0 stop after overload · 1 continue | 0 |
| 08-08 | Automatic Voltage Regulation (AVR) | 0 Enable · 1 Disable | 0 |
| 08-09 | Input Phase-Loss Protection | 0 Disable · 1 Enable | 0 |
| 08-10 | Output Phase-Loss Protection | 0 Disable · 1 Enable | 0 |
| 08-13..08-16 | Over-Torque Detection | select (0/1/2) · operation (0/1/2) · level 0–300% · time 0.0–10.0 s | 0 / 0 / 150% / 0.1 s |
| 08-17..08-20 | Low-Torque Detection | select · operation · level 0–300% · time | 0 / 0 / 30% / 0.1 s |
| 08-23 | Ground Fault (GF) Selection | 0 Disable · 1 Enable | 0 |
| 08-24 / 08-25 | External Fault operation / detection | 0 decel·1 coast·2 continue / 0 immediate·1 during run | 0 / 0 |
| 08-35 | Motor-Overheat (PTC) Fault Selection | 0 Disable · 1 Decel to stop · 2 Coast to stop | 0 |
| 08-36 | PTC Input-Filter Time Coefficient | 0.00–5.00 s | 2 |
| 08-37 | Fan Control Function | 0 start at operation · 1 permanent · 2 start at high temp | 0 |
| 08-42 / 08-43 | PTC Trip / Reset Level | 0.1–10.0 V | 0.7 / 0.3 |

> Note (§4.2): inverter models 2060 / 4100 and above (IP20) do not have the heatsink-temp /
> fan functions referenced by some Group 08 entries. When a protection trips, the drive shows
> a fault code — see `faults.md`.
