# Spindle Speed Calibration — data collection

Purpose: gather the numbers needed to fix (a) the ~1.5× speed-scaling error (actual spindle
RPM ≈ 1.5 × commanded S), (b) the minimum-speed clamp that creates the high-gear "dead zone,"
and (c) the too-early gear shift. Fill in every blank; the analysis needs the actual numbers,
not estimates.

You'll need: the RPM gauge on the spindle, the CNC12 **PLC Diagnostics** screen (to read the
`FW`/`W` values live), and the CNC12 **machine-parameter** and **Control-Configuration**
screens. No tool in the spindle; guards per normal practice.

**How to read a PLC value:** on the PLC Diagnostics / PLC Detective screen, watch these
addresses:
- `FW7` = `GearBaseSpeed_FW` (crossover input)
- `FW6` = `SpinSpeedCommand_FW` (spindle-speed command after clamps)
- `W64` = `SpindleRange_W`, `W74` = `EngagedRange_W` (1 = low, 4 = high, 0 = neutral)
- the 12-bit DAC value sent to the VFD (`TwelveBitSpeed_W`) if it's visible

For each S command: type it in MDI, let the spindle settle, then read the RPM gauge and the
values. Keep the **spindle override at 100%** the whole time unless a step says otherwise.

---

## 0. Record the current configuration (once, before sweeping)

| Item | Where to read it | Value |
| --- | --- | --- |
| CNC12 **max** spindle RPM (`CfgMax`) | Control Config → spindle | 3500 ______ |
| CNC12 **min** spindle RPM (`CfgMin`) | Control Config → spindle | 1000 ______ |
| `P860` crossover | machine parameters | 800 ______ |
| `P861` hysteresis | machine parameters | 100 ______ |
| `P65` low-gear ratio | machine parameters | .5 ______ |
| `P33` high-gear ratio | machine parameters | 2.0 ______ |
| Spindle override % during test | operator panel | 100 |
| F510 **max output frequency** (`01-02`) | VFD keypad | 90hz ______ Hz |
| F510 **base frequency** (`01-12`) | VFD keypad | 60hz ______ Hz |
| Motor nameplate **base RPM** and **rated Hz** | motor plate | 1755 ______ rpm / 60 ______ Hz |
| Spindle RPM when the **motor is at its max** (10 V / full command), if known | — | ~2200 ______ |

---

## 1. Low-gear sweep (force low gear)

Set **`P860 = 5000`** (a crossover so high it never up-shifts → the drive stays in low gear
for every S below). `M3`, then command each S, let it settle, and record.

| Command | RPM gauge | `FW7` GearBase | `FW6` SpinCmd | DAC (12-bit) | `W74` Engaged | "min speed" msg? |
| --- | --- | --- | --- | --- | --- | --- |
| `S50`  | 390 ____ | ____ | ____ | ____ | ____ |  N |
| `S100` | 390 ____ | ____ | ____ | ____ | ____ |  N |
| `S200` | 390 ____ | ____ | ____ | ____ | ____ |  N |
| `S300` | 470 ____ | ____ | ____ | ____ | ____ |  N |
| `S400` | 625 ____ | ____ | ____ | ____ | ____ |  N |
| `S600` | 938 ____ | ____ | ____ | ____ | ____ |  N |
| `S800` | 1250 ____ | ____ | ____ | ____ | ____ |  N |
| `S1000`| 1367 ____ | ____ | ____ | ____ | ____ |  N |
| `S1200`| 1367 ____ | ____ | ____ | ____ | ____ |  N |

- [ ] Note the S at which the RPM gauge **stops being flat** and starts climbing (the low-gear
      floor / min-speed release): S ≈ s50 ______ , RPM at the floor ≈ 390 ______
- [ ] Note the **highest** RPM low gear reaches before it stops climbing (motor maxed): S ≈
      s1000 _____ , RPM ≈ 1367 ______  ← this is the top of low gear.

`M5` when done.

---

## 2. High-gear sweep (force high gear)

Set **`P860 = 1`** (crossover so low it up-shifts immediately → stays in high gear). `M3`,
then command each S and record.

> ⚠ Stop the sweep if the RPM gauge reaches the spindle's **max rated RPM** — do not
> over-speed it. Given the ~1.5× scaling, that may happen well before S3500.

| Command | RPM gauge | `FW7` GearBase | `FW6` SpinCmd | DAC (12-bit) | `W74` Engaged | "min speed" msg? |
| --- | --- | --- | --- | --- | --- | --- |
| `S100` | 1514 ____ | ____ | ____ | ____ | ____ |  N |
| `S300` | 1514 ____ | ____ | ____ | ____ | ____ |  N |
| `S500` | 1514 ____ | ____ | ____ | ____ | ____ |  N |
| `S700` | 1514 ____ | ____ | ____ | ____ | ____ |  N |
| `S900` | 1514 ____ | ____ | ____ | ____ | ____ |  N |
| `S1000`| 1514 ____ | ____ | ____ | ____ | ____ |  N |
| `S1100`| 1667 ____ | ____ | ____ | ____ | ____ |  N |
| `S1200`| 1818 ____ | ____ | ____ | ____ | ____ |  N |
| `S1500`| 2275 ____ | ____ | ____ | ____ | ____ |  N |
| `S2000`| 3029 ____ | ____ | ____ | ____ | ____ |  N (watch max RPM) |

- [ ] Note the S at which high gear **stops being flat** and starts climbing (the high-gear
      floor / min-speed release): S ≈ s100 ______ , RPM at the floor ≈ 1514 ______
- [ ] Note the **highest** safe RPM reached and at what S: S ≈ 2200 _____ , RPM ≈ 3500 _____

`M5` when done.

---

## 3. Crossover points (diagnose the early shift)

Set `P860` back to the **intended** value and record it here: `P860` = ______ , `P861` =
______ . `M3`, then sweep S **upward** in small steps and note exactly where it shifts to high;
then sweep **down** and note where it shifts back to low. Record `FW7` (GearBase) right at each
shift.

|                         | S at shift | `FW7` GearBase at the shift | RPM just before shift | RPM just after |
| --- | --- | --- | --- | --- |
| **Up-shift** (low→high) | s450 ____ | ____ | ____ | ____ |
| **Down-shift** (high→low) | s350 ____ | ____ | ____ | ____ |

- [ ] Key question: at the up-shift, does **`FW7` equal the commanded S**, or is it larger?
      (If `FW7` ≈ commanded S but it still shifts too early, `P860` is set lower than we think.
      If `FW7` ≫ commanded S, the crossover input is being mis-scaled.)
 I can't seem to see FW7 easily 
---

## 4. Restore

- [x ] Set `P860` back to the intended crossover value (record it): ______
- [x ] Confirm normal power-up: both clutches on (neutral), `EngagedRange_W` = 0.

---

## What this data determines

- **Sections 1 & 2 slope** (RPM ÷ commanded S in the non-flat region) → the true `CfgMax`
  correction so commanded S = actual RPM.
- **Sections 1 & 2 floors** (flat RPM + the S where they release) → the true `CfgMin`, hence
  how far to lower it to remove the dead zone.
- **Section 1 top of low gear** vs **Section 2 floor of high gear** → whether the two gears
  actually **overlap**, and therefore where the crossover can live.
- **Section 3** → whether the early shift is a wrong `P860` value or a scaled crossover input.
