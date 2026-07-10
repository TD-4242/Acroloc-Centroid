# F510 Parameters

Faithful capture of the F510 parameter set from the manual's parameter tables (§4.2;
detailed prose in §4.3). This file is the **atlas** plus the **key parameters for a spindle
drive**. Deep dives live in the sibling files: RS-485 in `communication.md`, motor/mode/tune
in `setup.md`, braking/OV/protection in `braking-and-protection.md`.

## How to read a parameter

Parameters are addressed `GG-CC` (group-code), e.g. `00-00`. Each row in the manual gives
**Code | Name | Setting Range | Default | Unit | Control-Mode applicability (V/F, SLV, PM
SLV) | Attribute**. In the control-mode columns, `O` = available, `X` = not available in that
mode. The `Attribute` column carries footnote flags (e.g. `*2` = cannot be changed during
run) — see the manual's footnote legend when it matters. Edit via the keypad (Parameter Group
mode) or over RS-485 (`communication.md`). `KVA` in a default means the default scales with
the inverter rating.

## Parameter groups (atlas) — §4.2

| Group | Name |
| --- | --- |
| 00 | Basic Parameters |
| 01 | V/F Control Parameters |
| 02 | IM Motor Parameters |
| 03 | External Digital Input and Output Parameters |
| 04 | External Analog Input and Output Parameters |
| 05 | Multi-Speed Parameters |
| 06 | Automatic Program Operation Parameters |
| 07 | Start / Stop Parameters |
| 08 | Protection Parameters |
| 09 | Communication Parameters |
| 10 | PID Parameters |
| 11 | Auxiliary Parameters |
| 12 | Monitoring Parameters |
| 13 | Maintenance Parameters |
| 14 | PLC Setting Parameters |
| 15 | PLC Monitoring Parameters |
| 16 | LCD Parameters |
| 17 | IM Motor Automatic Tuning Parameters |
| 18 | Slip Compensation Parameters |
| 19 | Reserved |
| 20 | Speed Control Parameters |
| 21 | Torque Control Parameters |
| 22 | PM Motor Parameters |
| 23 | Pump & HVAC |
| 24 | 1 to 8 Pump Card Function Group |

**Out of scope for this skill** (pointer only — see §4.2/§4.3 in the manual): Group 10 (PID),
Group 23/24 (Pump & HVAC), Group 05/06 (multi-speed / auto-program), Group 14/15 (internal
PLC). Group 20/21/22 are covered only where a spindle in SLV/PM-SLV needs them.

## Group 00 — Basic (control mode, command sources, limits, accel/decel) — §4.2 p.76-79

| Code | Name | Range / options | Default |
| --- | --- | --- | --- |
| 00-00 | Control Mode | 0 V/F · 2 SLV · 5 PM SLV | 0 |
| 00-01 | Motor Rotation Direction | 0 Forward · 1 Reverse | 0 |
| 00-02 | Main Run Command Source | 0 Keypad · 1 External terminal · 2 Communication (RS-485) · 3 PLC · 4 RTC | 1 |
| 00-03 | Alternative Run Command Source | (same options as 00-02) | 0 |
| 00-04 | Language (LCD) | 0 English · 1 Simp. Chinese · 2 Trad. Chinese · 3 Turkish | 0 |
| 00-05 | Main Frequency Command Source | 0 Keypad · 1 Analog AI1 · 2 Terminal UP/DOWN · 3 Communication (RS-485) · 6 RTC · 7 AI2 Aux | 1 |
| 00-06 | Alternative Frequency Command Source | (same options as 00-05) | 0 |
| 00-07 | Main & Alternative Frequency Modes | 0 Main · 1 Main + Alternative | 0 |
| 00-08 | Communication Frequency Command Range | 0.00–400.00 Hz | 0.00 |
| 00-09 | Communication Frequency Memory | 0 don't save on power-off · 1 save | 0 |
| 00-12 | Upper Limit Frequency | 0.1–109.0 % | 100.0 |
| 00-13 | Lower Limit Frequency | 0.0–109.0 % | 0.0 |
| 00-14 | Acceleration Time 1 | 0.1–6000.0 s | (KVA) |
| 00-15 | Deceleration Time 1 | 0.1–6000.0 s | (KVA) |
| 00-16 | Acceleration Time 2 | 0.1–6000.0 s | (KVA) |
| 00-17 | Deceleration Time 2 | 0.1–6000.0 s | (KVA) |
| 00-21..00-24 | Acceleration/Deceleration Time 3 & 4 | 0.1–6000.0 s | (KVA) |
| 00-25 | Switch-over Frequency of Acc/Dec Time 1↔4 | 0.0–400.0 Hz | 0.0 |
| 00-26 | Emergency Stop Time | 0.1–6000.0 s | 5.0 |
| 00-28 | Main Freq Command Characteristic | 0 positive (0-10V/4-20mA → 0-100%) · 1 negative (→ 100-0%) | 0 |
| 00-32 | Application Selection Presets | 0 General · 1 Water pump · 2 Conveyor · 3 Exhaust fan · 4 HVAC · 5 Compressor | 0 |
| 00-33 | Modified Parameters (LCD) | 0 Enable · 1 Disable | 0 |
| 00-41..00-56 | User Parameters 0–15 (LCD; set 13-06=1 to enable) | 01-00 … 24-06 | — |

> `00-02`/`00-05` option **2 = "Communication Control (RS-485)"** is how the drive is run and
> speed-commanded over Modbus — see `communication.md`. Accel/decel time selection, S-curve,
> and jog are detailed in `setup.md`.

## Group 02 — IM Motor nameplate — §4.2 p.79-80

Enter these from the motor nameplate before auto-tuning (`setup.md`). `X` in a mode column
means that field is not used in that control mode.

| Code | Name | Range | Default | Modes |
| --- | --- | --- | --- | --- |
| 02-01 | Rated Current | V/F 10–200% of inverter rated; SLV 25–200% | (KVA) A | V/F,SLV |
| 02-03 | Rated Rotation Speed | 0–60000 rpm | (KVA) | V/F,SLV |
| 02-04 | Rated Voltage | 200V 50.0–240.0 / 400V 100.0–480.0 V | 230/400 | V/F,SLV |
| 02-05 | Rated Power | 0.01–600.00 kW | (KVA) | V/F,SLV |
| 02-06 | Rated Frequency | 4.8–400.0 Hz | 50/60 | V/F,SLV |
| 02-07 | Poles | 2–16 (even) | 4 | V/F,SLV |
| 02-09 | Excitation Current | 15.0–70.0 % | (KVA) | SLV |
| 02-15 | Resistance between Wires | 0.001–60.000 Ω | (KVA) | V/F,SLV |
| 02-33 | Leakage Inductance Ratio | 0.1–15.0 % | (KVA) | SLV |
| 02-34 | Slip Frequency | 0.10–20.00 Hz | (KVA) | SLV |

(Group 01 V/F-curve parameters — `01-02` Max Output Frequency, `01-03` Max Output Voltage,
`01-12` Base Frequency, `01-13` Base Output Voltage, `01-14` Input Voltage — matter in V/F
mode; see `setup.md`.)

## Group 07 — Start / Stop (stop mode, restart, DC braking) — §4.2 p.83-84

| Code | Name | Range / options | Default |
| --- | --- | --- | --- |
| 07-00 | Momentary Power-Loss / Fault Restart | 0 Disable · 1 Enable | 0 |
| 07-01 | Fault Auto-Restart Time | 0–7200 s | 0 |
| 07-02 | Number of Fault Auto-Restart Attempts | 0–10 | 0 |
| 07-04 | Direct Start at Power-On | 0 direct start if run cmd present · 1 no direct start | 1 |
| 07-05 | Automatic Start Delay at Power-Up | 1.0–300.0 s | 3.5 |
| 07-06 | DC Injection Braking Start Frequency | 0.0–10.0 Hz | 0.5 |
| 07-07 | DC Injection Braking Current | 0–100 % | 50 |
| 07-08 | DC Injection Braking Time at Stop | 0.00–10.00 s | 0.50 |
| 07-09 | **Stop Mode Selection** | 0 Decelerate to stop · 1 Coast to stop · 2 DC braking stop · 3 Coast to stop with timer | 0 |
| 07-13 | Low-Voltage Detection Level | 200V 150–300 / 400V 300–600 V | 190/380 |
| 07-16 | DC Injection Braking Time at Start | 0.00–100.00 s | 0.00 |

## Group 08 — Protection (highlights) — §4.2 p.95-99

Full detail (stall prevention voltages, torque detection, overheat) is in
`braking-and-protection.md`. Highlights:

| Code | Name | Range / options | Default |
| --- | --- | --- | --- |
| 08-00 | Stall Prevention Function | bitfield: enable/disable in accel / decel / operation | 0000b |
| 08-01 | Stall Prevention Level in Acceleration | 20–200 % | 120 |
| 08-02 | Stall Prevention Level in Deceleration | 200V 330–410 / 400V 660–820 V | 385 / 770 |
| 08-03 | Stall Prevention Level in Operation | 30–200 % | 120 |
| 08-05 | Motor Overload Protection (OL1) selection | bitfield: enable/disable, cold/hot start, std/special motor | 0001b |
| 08-08 | Automatic Voltage Regulation (AVR) | 0 Enable · 1 Disable | 0 |
| 08-09 | Input Phase-Loss Protection | 0 Disable · 1 Enable | 0 |
| 08-10 | Output Phase-Loss Protection | 0 Disable · 1 Enable | 0 |
| 08-13..08-16 | Over-Torque Detection (select / operation / level / time) | — | 0 / 0 / 150% / 0.1s |
| 08-17..08-20 | Low-Torque Detection (select / operation / level / time) | — | 0 / 0 / 30% / 0.1s |
| 08-23 | Ground Fault (GF) Selection | 0 Disable · 1 Enable | 0 |
| 08-35 | Motor-Overheat Fault Selection (PTC) | 0 Disable · 1 Decel to stop · 2 Coast to stop | 0 |
| 08-37 | Fan Control Function | 0 Start at operation · 1 Permanent · 2 Start at high temp | 0 |

## Group 09 — Communication — §4.2 p.100

Detailed in `communication.md`. Note (verbatim): **"Parameters in group 09 are not affected
by a parameter initialization (13-08)."** Core rows: `09-00` station address (1–31, def 1),
`09-01` mode (0 MODBUS · 1 BACNET · 2 METASYS · 3 Pump-parallel · 4 PROFIBUS; def 0),
`09-02` baud (0:1200 … 4:19200 … 5:38400; def 4), `09-03` stop bits, `09-04` parity,
`09-05` data bits (0:8, 1:7).

## Group 11 — Auxiliary (accel/decel shaping, carrier, OV-prevention) — §4.2 p.102-107

Detailed where used: S-curve and carrier in `setup.md`; OV-prevention (`11-38`..`11-42`) in
`braking-and-protection.md`. Highlights: `11-00` direction lock, `11-01` carrier frequency,
`11-04`..`11-07` S-curve times (start/end of accel/decel), `11-08`..`11-11` jump frequencies,
`11-40` OV-prevention selection, `11-54` clear cumulative energy.

## Group 13 — Maintenance (rating, lock, password, restore) — §4.2 p.111-113

| Code | Name | Range / options | Default |
| --- | --- | --- | --- |
| 13-00 | Inverter Rating Selection | 00H–FFH | — |
| 13-01 | Software Version | 0.00–9.99 | — |
| 13-02 | Clear Cumulative Operation Hours | 0 disable · 1 clear | 0 |
| 13-06 | **Parameters Locked** | 0 params outside 13-06 & main freq 05-01 read-only · 1 only user params enabled · 2 all params writable | 2 |
| 13-07 | **Parameter Password** | 00000–65534 | 00000 |
| 13-08 | **Restore Factory Setting** | 0 no init · 2/3 2-/3-wire 220-440V 60Hz · … · 8 PLC init · 9/10 230/460V 60Hz · 11-16 230/400V 50/60Hz (see manual for full list) | 0 |
| 13-09 | Fault History Clearance | 0 no · 1 clear | 0 |
| 13-11 | C/B CPLD Version | 0.00–9.99 | — |
| 13-14 | Fault Storage Selection | 0 don't save auto-restart faults · 1 save | 1 |
| 13-21..13-50 | Previous Fault Messages 1–30 (read-only history) | — | — |

> There is **no keypad parameter-copy/clone function** in Group 13 (or Group 16). Use RS-485
> for config backup/restore — see `communication.md`.
