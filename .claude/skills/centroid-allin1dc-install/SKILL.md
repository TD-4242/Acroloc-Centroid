---
name: centroid-allin1dc-install
description: Use when installing, wiring, commissioning, tuning, or troubleshooting a Centroid ALLIN1DC (MPU11) CNC controller — covers board hardware/I-O and LED states, cabinet wiring (input voltage SIPs, VM/rectifier, E-stop, servo motors, current limiting, limits, lube/coolant/spindle), CNC12 software install & bench test, final commissioning (encoder/motor/spindle setup, DRO calibration, homing, feedrate/accel tuning, backlash, travel limits), recommended servo PID/current/heating parameters, and symptom→fix troubleshooting. Reference is the official ALLIN1DC Installation Manual; it is generic (not specific to any one machine).
---

# Centroid ALLIN1DC Install & Commissioning

## When to use / when not

Use this skill for **hardware installation and commissioning** of a Centroid **ALLIN1DC**
(MPU11-based) CNC controller: board capabilities and I/O, cabinet wiring, CNC12 software
install and bench testing, motor/spindle/DRO commissioning and tuning, parameter values,
and troubleshooting. It is a faithful, generic capture of the official **ALLIN1DC
Installation Manual** (CNC12 v5.08+, rev22) — not specific to any one machine.

**Do not use this skill** for PLC **stage-language** (`.src`) or **M-code macro**
(`mfunc*.mac`) authoring/debugging — that is the `centroid-plc-programming` skill. This
skill covers wiring and software *configuration*, not PLC program logic.

## Essentials

The **ALLIN1DC** is a complete motion-control solution on one board: a built-in **3-axis DC
servo drive** (expandable to 6 via DC1 drives), **6 encoder inputs**, a **16-in / 9-relay-out
PLC**, and **analog spindle control** — running Centroid **CNC12** on a Windows PC over
shielded Ethernet.

Recommended install order (and where each lives below):

1. **Bench test the hardware first** — before installing in the machine and before applying
   high voltage. (`hardware.md` → `software-setup.md`)
2. **Install CNC12 + a PLC program**, configure the Ethernet adapter, run the bench test.
   (`software-setup.md`)
3. **Wire the electrical cabinet** following the shipped schematic. (`wiring.md`)
4. **Final software commissioning**: motor/spindle setup, DRO calibration, homing, and
   feedrate/accel/backlash/travel-limit tuning. (`commissioning.md`)
5. Look up **concrete values** in `parameters.md`; diagnose faults in `troubleshooting.md`.

> Two cautions that recur throughout: installing the **wrong input SIP** for the voltage in
> use **damages** the board; and the bench test **must** precede applying high voltage to the
> servo drive.

## Reference router

| Reference file | Look here when… |
|---|---|
| `reference/hardware.md` | You need board capabilities, I/O counts, what's-included part numbers, **encoder requirements/pinout/voltage levels**, or the **LED states** and their nominal values |
| `reference/wiring.md` | You're wiring the cabinet: input voltage **SIPs** & sourcing/sinking, **VM/rectifier** sizing, **E-stop**, servo motors, **current limiting**, limit switches, lube/coolant pumps, or the **spindle** (direct vs. VFD, default spindle I/O map) |
| `reference/software-setup.md` | You're installing **CNC12**, configuring the Ethernet adapter/IP, importing a license, disabling fault logic for the **bench test**, or running the spindle/encoder bench tests |
| `reference/commissioning.md` | You're doing **final software config**: encoder confirm, motor/spindle setup, DRO coarse/fine calibration, homing, max-feedrate & acceleration tuning, backlash comp, software travel limits, deadstart, system test |
| `reference/parameters.md` | You need a **concrete value**: current-limit switch settings, recommended servo **PID/current/heating** parameters (stock Centroid & Fanuc), or the CNC12 setup parameter numbers (P256, P300–315, P34/35/78, P65–67, etc.) |
| `reference/troubleshooting.md` | You have a **symptom**: dead/abnormal LEDs, LED1 error codes, run-away motors, comm/encoder/jog-panel errors, or accuracy problems — with the matching Tech-Bulletin pointers |

## Visual content & schematics

The manual's wiring diagrams and the **Appendix D circuit schematic set** (20 sheets) are
images; the reference files describe them and cite the manual **page number** rather than
reproducing pictures. Get the full schematic set here:
`http://www.centroidcnc.com/downloads/allin1dc/centroid_allin1dc_schematic_set.zip`.

Appendix D sheet index: 1 Title · 2 110VAC Direct Rectification · 3 110VAC Stepdown ·
4 220VAC Stepdown · 5 110VAC Power Rectification · 6 220/440VAC Power Rectification ·
7 Inverter · 8 1-Phase Flood · 9 3-Phase Flood · 10 1-to-3-Phase Flood · 11 2nd E-Stop ·
12 Cables · 13 Operators Panel · 14 Limit Switch · 15 Lube Pump · 16 Mister · 17 PLCADD1616 ·
18 Spindle Contactor · 19 Braking Motor · 20 4th-Axis DC1.

## Useful resources (from the manual)

- Centroid product manuals: `http://www.centroidcnc.com/centroid_diy/centroid_manuals.html`
- All Centroid schematics (search "allin1dc"): `https://www.centroidcnc.com/centroid_diy/schematics/pbrowse.php`
- Tech Bulletins browser: `http://www.centroidcnc.com/centroid_diy/tech_bulletins/browse.php`
  (individual bulletins: `http://www.centroidcnc.com/dealersupport/tech_bulletins/uploads/<N>.pdf`)
- Community forum: `https://centroidcncforum.com`
- Centroid CNC Technical Support — YouTube channel
- *martyscncgarage* — "Centroid All in One DC Control - Knee Mill Retrofit" YouTube series
- ALLIN1DC product page: `https://shopcentroidcnc.com/allin1dc-cnc-controller/`
