# Parameter & Setting Reference

Concrete values: drive current-limit switch settings, recommended servo PID/current/heating
parameters, and the key CNC12 setup parameters touched during install.
Source: install manual Ch5.5, Ch6, and Appendix C (TB288). Parameters are set via
`F1 Setup → F3 Config` (password **137**) unless noted. For the procedures that use these,
see `commissioning.md` and `software-setup.md`.

## Drive current-limit switch settings (Ch5.5)

Switches 1–2 = Axis 1, 3–4 = Axis 2, 5–6 = Axis 3. Set **higher than** the motor's rating.
Black switch: ON = away from PCB. Blue switch: ON = toward PCB. Push gently (plastic levers).

### Standard ALLIN1DC

| Current | Sw1/Sw3/Sw5 (axis +) | Sw2/Sw4/Sw6 (axis +) |
|---|---|---|
| 6 A | OFF | OFF |
| 9 A | OFF | ON |
| 12 A | ON | OFF |
| 15 A | ON | ON |

### Low-Power ALLIN1DC

| Current | Sw1/Sw3/Sw5 | Sw2/Sw4/Sw6 |
|---|---|---|
| 5 A | OFF | OFF |
| 6 A | OFF | ON |
| 7 A | ON | OFF |
| 9 A | ON | ON |

### Common settings for stock Centroid motors

| Motor size | Setting |
|---|---|
| 10 in-lb | 6 A |
| 16 / 17 in-lb | 9 A |
| 29 in-lb | 12 A |
| 40 in-lb | 15 A |

## Current setting for 3rd-party motors (App C / TB288)

Match the motor's constant current rating (or constant stall rating) to a current setting
(switch SW1, §5.5):

| Motor rating | 6 A | 9 A | 12 A | 15 A |
|---|---|---|---|---|
| 3–4 A | **Recommended** | Maximum (overheat risk) | Not recommended | Not recommended |
| 5–6 A | Good | **Recommended** | Maximum | Not recommended |
| 7–8 A | Not recommended | Good | **Recommended** | Maximum |
| 9–10 A | Not recommended | Not recommended | Good | **Recommended** |
| 11–15 A | Not recommended | Not recommended | Not recommended | Good ("AC/DC 30" recommended) |
| 16 A+ | — use "AC/DC 30" or "AC/DC 60" drive — | | | |

*Recommended* = best performance/heat balance. *Good* = good accel/peak torque.
*Maximum* = max accel/peak torque but **motor could overheat**. *Not recommended* = too much
or too little power.

## Servo motor PID parameters (App C)

The ALLIN1DC runs **torque mode only**: set **Parameter 256 = 0** (F3 Parms → F8 Next Table
to P256). Enter Kp/Ki/Kd/Limit in F4 PID → F1 PID Config (per §6.3). Kg/Kv1/Ka/Accel are
filled by autotune. Generic 3rd-party default: **Kp = 1.00, Ki = 0.004, Kd = 3.0**.

### Stock Centroid servo motors

| Name | Model | Current (Sw1) | Kp | Ki | Kd | Limit | Max RPM | Max bus |
|---|---|---|---|---|---|---|---|---|
| Glentek 10 in-lb | GM3320-22 | 6 A | 0.50 | 0.004 | 0.5 | 32,000 | 4,650 | 180 VDC |
| Glentek 16 in-lb | GM3340-30 | 9 A | 1.00 | 0.004 | 2.0 | 32,000 | 3,200 | 180 VDC |
| Redcom 17 in-lb | 82SYXB-17 | 9 A | 0.50 | 0.004 | 1.0 | 32,000 | 2,300 | 120 VDC |
| Glentek 29 in-lb | GM4030-41 | 12 A | 1.00 | 0.004 | 3.0 | 32,000 | 3,500 | 180 VDC |
| Glentek 40 in-lb | GM4050-60 | 15 A | 1.00 | 0.004 | 3.0 | 32,000 | 2,200 | 180 VDC |

### Fanuc retrofit servo motors (all: Kp=1, Ki=0.004, Kd=3.0, Limit=32,000, Max RPM 2,000)

| Family | Name | Model | Current (Sw1) | Max bus |
|---|---|---|---|---|
| Black end caps | Black Cap 00 | A06B-0631-B0xxx | 12 A | see motor nameplate |
| Black end caps | Black Cap 0 | A06B-0613-B0xx | 15 A | see motor nameplate |
| Yellow end caps | Yellow Cap 00M | A06B-0632-Bxxx | 9 A | 50 VDC |
| Yellow end caps | Yellow Cap 0M | A06B-0641-Bxxx | 12 A | 90 VDC |
| Yellow end caps | Yellow Cap 5M | A06B-0642-Bxxx | 15 A | 150 VDC |

Motors larger than Black Cap 0 / Yellow Cap 5M need an AC/DC30 for full accel/torque. Mixed
Fanuc motors must all run at the same bus voltage. **Max-RPM parameters (P357–364) are
reference only — limit drive speed with the max jog rate (F2 Mach → F1 Jog → Max Rate), not
these.**

## Servo heating/cooling parameters (App C)

Run a max-feedrate/accel test program, then measure motor surface temperature and adjust.
If a motor occasionally overheats, adjust feedrate/accel; if it consistently overheats, drop
the current limit one setting (SW1).

- **P21–24** (axes 1–4): heating coefficients (higher = estimates hotter under load).
- **P25–28** (axes 1–4): cooling coefficients (higher = estimates faster cool-down).
- **P20** (all axes): ambient shop temp on a hot day — default **72°F / 22°C**.
- **P29** (all axes): "motor overheat warning" temp — default **150°F / 65°C**.
- **P30** (all axes): temp at which CNC12 stops the machine — default **180°F / 82°C**.

Suggested Centroid-motor values:

| | 16/17 in-lb (Sw1=9) | 29 in-lb (Sw1=12) | 29 in-lb (Sw1=15) | 40 in-lb (Sw1=15) |
|---|---|---|---|---|
| P21–24 | 0.028 | 0.02 | 0.027 | 0.03 |
| P25–28 | 0.68 | 0.68 | 0.68 | 0.68 |
| P20 | 72/22 | 72/22 | 72/22 | 72/22 |
| P29 | 150/65 | 150/65 | 150/65 | 150/65 |
| P30 | 180/82 | 180/82 | 180/82 | 180/82 |

## Axis / encoder / motor setup parameters

- **P300–307** — Drive Bus assignment (axis → drive-bus channel). 3-axis mill: P300=1, P301=2,
  P302=3. **Unused axes must be 0** or errors occur.
- **P308–315** — MPU11 encoder-channel assignment. 3-axis mill: P308=1, P309=2, P310=3.
  Unused encoder axes can be left as-is.
- **Encoder counts/rev** (F2 Mach → F2 Motor, per axis) = line count × 4 (2000-line = 8000;
  5000-line = 20,000; 10,000-line = 40,000).
- **Dir Rev / Lash Comp / Motor revs-per-inch (mm/rev)** — per-axis fields in F2 Mach → F2
  Motor (set during §6.3, §6.5/6.9, §6.10).
- **Max Rate / Travel(−) / Travel(+) / Deadstart** — Jog Parameters (F2 Mach → F1 Jog),
  §6.7, §6.11, §6.12. Both Travel limits = 0 disables travel limits; one non-zero enables both.

## Spindle parameters

- **Max spindle (high range)** / **Min spindle (high range)** — Control Configuration
  (F1 Contrl). 0–500000 RPM. Programmed S is output to the PLC as a percentage of max.
- **Analog spindle output:** 0 to +10 VDC, scaled to 0–max RPM (default max 3000 → S1500 =
  +5 V, S1000 = +3.33 V). **DAC dip switches for 0–10 V operation: 1=Up, 2=Down, 3=Up,
  4=Down, 5=Up.**
- **P34** — spindle encoder counts/rev (line × 4); negate if it counts backward.
- **P35** — spindle encoder axis number (**6**).
- **P78** — spindle speed display & operations (**1**).
- **P65 / P66 / P67** — gear ratios for low / medium-low / medium-high range, relative to
  high range (e.g. low turns 1/10 of high → P65 = 0.1; negative for a back gear). The PLC
  signals the active range via INP63/INP64:

  | | High | Medium-High | Medium-Low | Low |
  |---|---|---|---|---|
  | INP63 | 0 | 1 | 1 | 0 |
  | INP64 | 0 | 0 | 1 | 1 |

## Wireless MPG parameters (≥ Pro license)

- **#218** = 15 (4-axis mill/router), 7 (3-axis mill/router), 3 (lathe).
- **#348** = 15 (MPG on).
- **#350** = 100 (100 steps/rev).

Restart CNC12 after changing. Other relevant: operator-manual **Parameter 179** for
direct-controlled lube-pump timing.
