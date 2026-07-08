# F510 Wiring & Terminals

Power terminals, control/user terminals, the RS-485 port, model numbering, and key specs.
Sources: §2.1–2.2 (model/nameplate), §3.9 (control terminals), §3.10 (power terminals),
§3.11 (power block diagram), §3.18–3.19 (specs). Wiring diagrams are images — described here
and cited by section; not reproduced.

## Model numbering — §2.1–2.2

`F510-<V><rating>-<op><in>`:
- `<V>` voltage class: **2** = 230 V, **4** = 460 V.
- `<rating>` motor HP, three digits: `001` = 1 HP … `800` = 800 HP (e.g. `010` = 10 HP).
- `<op>` operator/keypad: **H** = LED, **C** = LCD.
- `<in>` input phase: **3** = 3-phase.

Example: `F510-4010-C3` = 460 V, 10 HP, LCD keypad, 3-phase. The nameplate also lists INPUT
(e.g. `AC 3PH 380-480V 50/60Hz 18.2A`) and OUTPUT (`AC 3PH 380-480V 0-400Hz 17.5A`) ratings
and the enclosure (IP20 / NEMA1). Verify the nameplate matches the motor before wiring
(§2.1).

## Power terminals — §3.10

| Terminal | Function |
| --- | --- |
| `R/L1`, `S/L2`, `T/L3` | **Input** power supply (three-phase). For single-phase input use `R/L1` and `S/L3`. |
| `U/T1`, `V/T2`, `W/T3` | **Output** to motor. |
| `B1/P`, `B2` | External **braking resistor** across `B1/P`–`B2` (on frames with a built-in braking transistor). |
| `⊕/P`, `⊖/N` | **DC bus**: `B1/P`–`⊖` (or `⊕`–`⊖`) is the DC supply / braking-unit connection. |
| `E` (⏚) | Protective **ground**. |

- **Danger (§1.1):** never connect input power to `U/T1`, `V/T2`, `W/T3` — it destroys the
  inverter. Never connect a braking resistor directly across `P(+)`/`N(-)` (§1.2).
- **Built-in braking transistor:** small frames only — §3.10 note says 400 V ≤ 25 HP
  (18.5 kW) and below; §11.1 states 230 V ≤ 30 HP / 460 V ≤ 40 HP (IP20). Confirm for the
  exact model. Larger frames need an external braking unit (`braking-and-protection.md`).
- **DC reactor:** before connecting one, remove the factory jumper between `⊕1` and `⊕2`.
- **Terminal screw size** scales with frame: ~M4 (1–10 HP) → M6 → M8 → M10 → **M12** (largest
  400 V frames). Torque per §3.6.

## Control / user terminals — §3.9

The control terminal block (same terminals across frame sizes, different physical layout):
top row `(S+) (S-) S1 S3 S5 24V +10V MT GND GND AI1 AI2`; bottom row
`E 24VG S2 S4 S6 F1 F2 PO PI AO1 AO2 E`; relay terminals `R1A/R1B/R1C`, `R2A/R2C`, `R3A/R3C`.

| Terminal | Function | Signal level |
| --- | --- | --- |
| `S1` | Multi-function digital input — default **2-wire Forward Run/Stop** | 24 VDC opto-isolated, ≤8 mA, ≤30 Vdc, Zin 9.03 kΩ |
| `S2` | Multi-function digital input — default **2-wire Reverse Run/Stop** | " |
| `S3`,`S4`,`S5` | Multi-function digital inputs — default multi-speed cmd 1/2/3 | " |
| `S6` | Multi-function digital input — default **Fault Reset** | " |
| `24V` | Digital-signal **SOURCE** (SW3 = source mode) | ±15%, ≤250 mA total |
| `24VG` | Digital-signal **common / SINK** (SW3 = sink mode) | " |
| `+10V` | Reference supply for an external **speed pot** | ±5%, ≤20 mA |
| `MT` | Motor-temperature (PTC) input | 1330 Ω range, 550 Ω return |
| `AI1` | Multi-function **analog input**, speed reference — **0–10 V** | Zin 20 kΩ, 12-bit |
| `AI2` | Multi-function analog input — **0–10 V or 4–20 mA** (hardware switch **SW2** V/I) | 20 kΩ (V) / 250 Ω (I), 12-bit |
| `GND` | Analog signal ground | — |
| `AO1`,`AO2` | Multi-function **analog outputs** (0–10 V / 4–20 mA), meter signals | ≤2 mA (see `setup.md` §5) |
| `PO` | Pulse output, open-collector | ≤32 kHz, load 2.2 kΩ |
| `PI` | Pulse command input | L 0–0.5 V / H 4–13.2 V, ≤32 kHz, Zin 3.89 kΩ |
| `R1A/R1B/R1C` | Relay 1 output — A/B/C contacts, multi-function (Group 03) | 250 Vac / 30 Vdc, 10 mA–1 A |
| `R2A/R2C`, `R3A/R3C` | Relay 2 / 3 outputs, same rating & function set | " |
| `F1` | **Run-Permissive** input (On = allow run, Off = stop). Factory jumper `F1`–`F2` must be removed to use an external safety contact. | 24 Vdc, 8 mA, pull-up |
| `F2` | Safety-command common | 24 V ground |
| `S(+)`, `S(-)` | **RS-485 / Modbus** differential (port CN6) | differential in/out |
| `E (G)` | Shield / earth ground | — |

**Cautions (§3.9):** `+10V` max 20 mA; `AO1`/`AO2` are **meter outputs — do not use for
feedback control**; the control-board `24V` and `10V` are for **internal use only** — do not
power external devices from them. Digital-input source vs. sink is chosen with **SW3**; `AI2`
voltage vs. current with **SW2**.

## RS-485 port

The `S(+)`/`S(-)` pair is the RS-485 Modbus port on connector **CN6** (RJ45-style). Full
protocol, Group 09 setup, and config backup/restore are in `communication.md`.

## Key specifications — §2.2 / §3.18

- **Classes:** 230 V (3-phase 200–240 V +10/−15%, 50/60 Hz) and 460 V (3-phase 380–480 V
  +10/−15%).
- **Ratings:** 230 V 1–175 HP (0.75–130 kW); 460 V up to 800 HP (600 kW). Output frequency
  0–400 Hz. Applied-motor kW and rated input/output current per model are in the §2.2
  model table; the full electrical spec table is §3.18 (short-circuit rating, overload
  capacity, etc.) — consult it for a specific frame rather than transcribed here.
- **Enclosure:** IP00 / IP20 / NEMA1 depending on frame.

## Diagrams (cited, not reproduced)

- General wiring diagram: §3.8. Control-circuit wiring: §3.17.
- Power-section block diagrams (rectifier → DC bus → IGBT bridge → U/V/W): §3.11.
- Terminal-block physical layouts and screw sizes: §3.9 (control) / §3.10 (power).
- **Skipped (pointer only):** dimension drawings §3.22, carrier/temperature derating
  §3.20–3.21.
