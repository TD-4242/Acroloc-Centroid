---
name: teco-f510
description: Use when configuring, wiring, tuning, reading/backing-up parameters from, or troubleshooting a TECO-Westinghouse F510 variable-frequency drive (VFD / inverter) — the drive that runs a machine's spindle or motor. Covers control modes (V/F, SLV, PM SLV), the 24 parameter groups and key spindle parameters, RS-485 Modbus config download/upload, motor nameplate entry & auto-tuning, accel/decel & S-curve, braking resistor / OV-prevention, power/control/RS-485 terminals, and fault codes. Generic to the F510 — this-machine settings live in the acroloc-s10 skill. Source: official F510 Instruction Manual.
---

# TECO-Westinghouse F510 VFD

## When to use / when not

Use this skill for the **F510 variable-frequency drive** itself: control-mode selection,
parameter meaning and values, RS-485 Modbus communication and config backup/restore, motor
setup and auto-tuning, accel/decel and S-curve, braking-resistor / over-voltage handling,
power/control/RS-485 terminals, and fault codes. It is a faithful, **generic** capture of the
official **F510 Instruction Manual** (doc TECO-F510IM Ver 01, 2017.12) — not specific to any
one machine.

**Do not use this skill** for:
- the Centroid controller's **analog-spindle-output** side or cabinet wiring → that is
  `centroid-allin1dc-install`;
- PLC **stage-language** (`.src`) or **M-code** spindle/gear logic →
  `centroid-plc-programming`;
- **this machine's** spindle facts, gear ratios, or base RPM → `acroloc-s10`.

## Essentials

The **F510** is a general-purpose **variable-frequency drive** for three-phase **induction**
motors (and permanent-magnet motors in PM mode). It comes in a **230 V class** (1–175 HP,
0.75–130 kW) and a **460 V class** (up to 800 HP / 600 kW). It takes three-phase line power in
and synthesizes variable-frequency three-phase output to the motor. (Cover; §1.1; §3.18.)

**Model numbering** (§2.1–2.2): `F510-<V><rating>-<op><in>` — `<V>` = `2` (230 V) or `4`
(460 V); `<rating>` = motor HP as three digits (`001`=1 HP … `800`=800 HP); `<op>` = `H`
(LED keypad) or `C` (LCD keypad); `<in>` = `3` (3-phase). Example: `F510-4010-C3` = 460 V,
10 HP, LCD keypad, 3-phase.

**Control modes** (parameter `00-00`, §4.3): `0` = **V/F** (scalar), `2` = **SLV**
(sensorless vector, induction motor), `5` = **PM SLV** (sensorless vector, PM motor). Choose
the mode first — it gates which parameter groups apply.

**Keypad** (§4.1): an LCD keypad (LED keypad optional) with `RUN`/`STOP`, `▲`/`▼`,
`FWD/REV`, `DSP/FUN`, `◄/RESET`, and `READ/ENTER` keys. `DSP/FUN` switches between **Monitor
mode** (view frequency/current/status) and **Parameter Group mode** (read/edit parameters);
**Auto-tuning** is its own keypad flow. There is **no** parameter copy/clone function on the
base keypad — config transfer is via RS-485 (see `communication.md`).

### The controller ↔ VFD seam

The Centroid controller sends a **0–10 V analog** speed command (its DAC output) to the F510;
the F510 converts that command into three-phase motor drive. That 0–10 V link (and optional
RS-485) is the boundary between this skill (**VFD side**) and `centroid-allin1dc-install`
(**controller side**). Speed-scaling and gear math on the controller side live in
`centroid-plc-programming` / `acroloc-s10`; this skill covers how the F510 receives and acts
on the command.

## Reference router

| Reference file | Look here when… |
|---|---|
| `reference/parameters.md` | You need the **parameter-group atlas** (all 24 groups) or the key spindle parameters: control mode (`00-00`), run/frequency command sources, protection (Grp 08), accel/decel & carrier (Grp 11), or maintenance/restore/password (Grp 13) |
| `reference/communication.md` | You're using **RS-485 Modbus**: Group 09 setup (address/baud/format), the register addressing, how to **download/back up the full config to a PC** and write it back, or the `12-42` RS-485 error code |
| `reference/setup.md` | You're getting the drive to **run a motor**: control-mode selection, run/frequency command sources, **motor nameplate entry & auto-tuning** (Grp 17 → Grp 02), accel/decel & S-curve, analog-output setup |
| `reference/braking-and-protection.md` | You need **braking resistor / braking unit** sizing and terminals, **OV-prevention** modes/thresholds, deceleration/regen behavior, or the Group 08 protection parameters |
| `reference/wiring-and-terminals.md` | You're wiring the drive: **power terminals** (R/S/T, U/V/W, P/N), **control terminals** (digital in, analog AI1/AI2, relays R1–R3), **RS-485** terminals, model numbering, and key specs |
| `reference/faults.md` | You have a **fault or warning code**: the fault/warning tables (cause → action), auto-tuning error codes, and common symptom→fix |

## Diagrams & skipped content

Wiring diagrams, block diagrams, and dimension drawings are images; the reference files
describe them and cite the manual **section / PDF page** rather than reproducing them. Areas
outside a spindle-drive scope are pointed to by section, not transcribed: **PID** (Grp 10),
**Pump & HVAC** (Grp 23–24), dimension tables (§3.22), derating curves (§3.20–3.21), and
fieldbus **communication option cards** (§11.6).

Source & updates: TECO-Westinghouse (`www.tecowestinghouse.com`); always confirm against the
latest edition of the F510 Instruction Manual for the drive in hand.
