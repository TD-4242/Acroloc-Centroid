# ALLIN1DC Hardware Reference

Board capabilities, I/O, encoder requirements, and LED states.
Source: install manual Ch1 (What's Included) and Ch2.2–2.4. Manual pages cited as
`p.N` are the document's printed "Page N of 88".

## What the ALLIN1DC is

A complete motion-control solution on one board: a built-in **3-axis DC servo drive**
plus a full **PLC**. Combines Centroid's Digital DC Servo drive, MPU11 DSP CNC motion
control CPU, integrated PLC, and spindle control.

- **Axes:** 3 axes built in; expandable to **6 axes** via DC1 single-axis drives
  (up to three DC1's). LED1 shows the drive-bus order; a unit with no DC1 attached
  always shows `1`.
- **Encoder inputs:** **6** encoder/scale inputs (DB-9). Direct feedback to both the
  motion CPU and the DC servo drive for closed-loop control. Spare inputs can be used
  for a spindle encoder (rigid tapping, constant surface speed), scales, or dual MPGs.
- **PLC I/O:** 16 inputs / 9 fused relay outputs preconfigured for typical machine-tool
  use. Inputs are user-configurable for voltage and polarity.
- **Spindle:** analog spindle output, user-selectable 0–5, 0–10, ±5, ±10 VDC; 4 range
  analog input.
- **Servo drive:** 20–180 VDC, 6–15 A per axis (continuous). User-selectable per-axis
  current limit: 6, 9, 12, or 15 A.
- **Software:** runs Centroid CNC12 Mill or Lathe on a Windows PC, connected by
  shielded Ethernet.
- **Expansion:** up to 4 I/O expansion boards in any combination (up to ~80 IN / 73 OUT),
  e.g. PLCADD1616 (16 IN / 16 relay OUT), Add4AD4DA (4 D→A out / 4 A→D in),
  PLCADD6464 (64 IN / 64 open-collector OUT).

## What's included (Ch1) — part numbers

| # | Item | Part No. |
|---|---|---|
| 1 | ALLIN1DC | 11144 |
| 2 | DC Logic Power Cable | 13106 |
| 3 | Meanwell RQ-65D power supply | 7820 |
| 4 | Twenty-position terminal block | 3450 |
| 5 | Ten-position terminal block (×2) | 3904 |
| 6 | Seven-position terminal block | 2611 |
| 7 | 24 V SIPS (×4) | 4152 |
| 8 | 5 V SIPS (×4) | 3956 |
| 9 | 24 crimp pins (jog panel + probe connector) | 5511 |
| 10 | Ten-pin probe connector | 5918 |
| 11 | 26 crimp pins (MPG connector) | 5983 |
| 12 | Twelve-pin jog panel connector | 5919 |
| 13 | Twenty-four-pin MPG connector | 5984 |

Listed quantities are the **minimum** per parts bag.

### Crimpers & prebuilt cables (Ch1.2)

- **Crimp pin 5511** (jog panel + probe cables): TE Connectivity *PRO-CRIMPER III
  91387-1 w/ die 91387-2 (26–22 AWG)* or *91388-1 w/ die 91388-2 (22–18 AWG)*.
- **Crimp pin 5983** (MPG cables): JST *YRS-245*.
- Prebuilt cables from Centroid: `#11211` 6' probe cable, `#11086` up-to-20' MPG cable,
  `#11029` up-to-20' jog-panel cable, `#10830` up-to-16' DC encoder cable (DB9 to flat).

## Bench-test setup (Ch2.1–2.2)

**Always bench-test BEFORE installing in a machine, and BEFORE applying high voltage to
the servo drive.** Applying high voltage to an improperly configured system can cause
permanent hardware damage and physical harm.

- **Location:** large, well-lit bench near outlets. Surface must **NOT** be metal or hold
  metal shavings. Avoid fabric/anti-static-mat surfaces (ESD risk to powered boards).
  **Wood is the ideal bench surface.** Plastic is acceptable but a static risk.
- **Needed:** a PC (or Centroid console with CNC12 preinstalled) meeting Tech Bulletin
  **#273** specs, a small screwdriver set, a digital multimeter.
- **Configure the PC** per **TB309** before connecting.
- **Power:** connect the DC Logic Power cable to the Mean Well supply, plug into **H1**
  on the ALLIN1DC. Splice a 110 V cord to the supply's AC input — **Live→L, Neutral→N,
  Ground→ground**.
- **Ethernet:** use a **shielded** cable (metal clip around the RJ-45). Centroid
  recommends StarTech snagless **S45PATCH25BL** (Tech Bulletin **#251**). An unshielded
  cable causes intermittent PC data-receive errors from noise.
- **Logic power supply rail colors** (Fig 2.2.2): +5V red, COM black, Gnd green,
  +V2 (+12 V) yellow, −V4 (−12 V) blue.

## Encoder requirements (Ch2.3)

- ALLIN1DC uses **DC incremental quadrature encoders**. Connect starting at **encoder 1
  for the first axis**. Do **not** connect motor power wires during bench test.
- **Cables:** twisted-pair **shielded**; shield must be grounded to the DB-9 metal shell
  (Fig 2.3.1). Ungrounded shield causes encoder errors in software.
- **Output:** **RS422 differential** quadrature with A, B, Z channels. Centroid recommends
  **2000–10,000 line** encoders. 2000 lines = 8000 counts/rev.
- **Choosing an encoder — target ≥20,000 encoder counts/inch.**
  `Encoder lines × 4 × ballscrew turns/inch = counts/inch`.
  - Knee mills (~5 turns/inch): 2000-line works (2000×4×5 = 40,000 counts/inch).
  - Routers w/ rack-and-pinion (~1 turn/inch): need ≥5000-line (5000×4×1 = 20,000).

### Encoder voltage levels

| Characteristic | Min | Typ | Max | Unit |
|---|---|---|---|---|
| Encoder channel low level | 0.0 | 0.3 | 0.5 | V |
| Encoder channel high level | 3.0 | 3.5 | 5.0 | V |

### Encoder DB-9 pinout (MPU11 encoder connector, solder side — Fig 2.3.2)

| Pin | Signal |
|---|---|
| 1 | Not used |
| 2 | Common (ground) |
| 3 | Z− |
| 4 | A− |
| 5 | B− |
| 6 | Z+ |
| 7 | A+ |
| 8 | B+ |
| 9 | +5 V |

`+5 V` on pin 9 is an **output** provided by the ALLIN1DC.

## LED states (Ch2.4)

Wait ~30 s after power-up before checking LEDs. One group sits behind the limit-switch
header (Fig 2.4.1); two more are in the top corner by the analog section (Fig 2.4.2).
All should reach their nominal state below; if not, see Appendix C / `troubleshooting.md`.

| LED | Function | Nominal state |
|---|---|---|
| +12V Analog | +12 V to analog circuitry | Solid green |
| −12V Analog | −12 V to analog circuitry | Solid green |
| +3.3V | +3.3 V power | Solid green |
| +5.0V | +5.0 V power | Solid green |
| +12.0V | +12 V power | Solid green |
| −12.0V | −12 V power | Solid green |
| FPGA OK | FPGA working | Solid green |
| DSP OK | DSP working | Solid green |
| DSP Debug | Multiple functions (see Appendix C) | Flashing 1×/second |
| PLC OK | PLC working | Solid green |
| Drive Fault | Drive-fault relay status | On after software comm established and all faults cleared |

### LED1 seven-segment display

Wait ~15–30 s after start-up. A **solid number, no decimal point** = the unit's
**drive-bus order** (Fig 2.4.3). A unit with no DC1 attached always shows `1`. A number
**flashing with a decimal point** = an error (Fig 2.4.4). A blinking `4` means it isn't
seeing limit switches (expected on the bench before they're wired; toggle them with
SW4, Fig 2.4.5 — black switch goes up→down to disable, blue down→up). The full LED1
error table is in `troubleshooting.md`.
