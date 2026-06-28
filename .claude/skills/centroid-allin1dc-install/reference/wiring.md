# Cabinet Wiring Reference

Electrical cabinet installation: layout, input configuration, VM/rectifier, E-stop,
servo motors, current limiting, limit switches, lube, coolant, spindle.
Source: install manual Ch5. **Follow the schematic shipped with your kit.** Additional
schematics: `http://www.centroidcnc.com/downloads/allin1dc/centroid_allin1dc_schematic_set.zip`.
The detailed wiring diagrams (Figs 5.x) are images in the manual — cited here by page.

> **DANGER:** Power off the ALLIN1DC, rectifier, and all hardware before wiring or
> troubleshooting. Let the reservoir capacitor discharge — the rectifier DC output must
> read **< 10 VDC** before you touch wiring.

## Cabinet layout & best practices (5.1)

Suggested layout (Fig p.40): terminal strip in the middle for easy access; capacitor/
bridge rectifier under the ALLIN1DC; step-down transformer and servo power supply at the
bottom; E-stop contactor upper-left.

- **Minimize noise:** keep noisy gear (transformers, contactors) far from low-voltage
  boards — never mount a contactor/transformer directly under the ALLIN1DC. Keep
  high-voltage AC and motor lines away from low-voltage signal lines.
- **Single ground bus bar:** wire incoming chassis (earth) ground to one bus bar; tie all
  doors, supply chassis grounds, equipment grounds to that single point. Do **NOT** use
  multiple ground points (raises noise).
- **Snubbers on every contactor/relay coil** — Centroid Quencharc PART# **1819**
  (Tech Bulletin **#206**).
- Wire ducts ≥2" from boards; keep all wiring under **6 ft**; neat horizontal/vertical
  runs only (never diagonal); leave slack; use DIN rails and PVC ducts; **label
  everything** to match the schematic; don't lose the schematic.

### Minimum wire gauge (AWG, multi-stranded copper)

| Configuration | VM+, VM− | Motor |
|---|---|---|
| Low-power ALLIN1DC | 16 | 18 |
| ALLIN1DC w/ Centroid single-phase rectifier (PN 12726) | 14 | 16 |
| ALLIN1DC w/ Centroid two-phase rectifier (PN 10767) | 12 | 14 |

Spade-terminal crimp colors: **Red = 18–22 ga**, **Blue = 14–16 ga**. Use a crimper
(not cutters) and a stripper that doesn't nick strands (Tech Bulletin **#78**).

## Configuring input voltage — SIPs (5.2)

Inputs run at **5, 12, or 24 VDC**, set by swapping the **SIP** (single inline package)
resistor. The last three digits of the SIP part number give the resistance: first two
digits = value, last digit = number of trailing zeros (e.g. `…-102` = 10 + 2 zeros =
1000 Ω). **Ships with 2.2 K SIPs installed for 24 VDC.**

| Voltage | Centroid SIP PN | SIP value (marking) |
|---|---|---|
| 5 VDC | 3950 | 470 Ω (471) |
| 12 VDC | 4152 | 1 K Ω (102) |
| 24 VDC | 1548 | 2.2 K Ω (222) |

Each SIP controls a group of four inputs (silkscreen SIP1–SIP4, Fig 5.2.2):

| Input group | SIP |
|---|---|
| Inputs 13–16 | SIP1 |
| Inputs 9–12 | SIP2 |
| Inputs 5–8 | SIP3 |
| Inputs 1–4 | SIP4 |

> **Installing the wrong SIP for the voltage in use will DAMAGE the ALLIN1DC.** With the
> default PLC program, **Spindle Fault, E-Stop Input, and Lube Fault must all run off the
> same input voltage** (inputs 9–12).

### Sourcing vs sinking (5.2, Fig 5.2.3)

Inputs are grouped in fours sharing a common. Both modes use an external 5/12/24 VDC
supply (the ALLIN1DC drive supply may be used; SIP must match the voltage).

- **Sourcing:** inputs connect to power; supply **negative** → common.
- **Sinking:** inputs connect to ground; supply **positive** → common. *(24 VDC to the
  input commons with inputs pulled down to 24 VDC COM is the standard configuration.)*

## Wiring VM / rectifier (5.3, Tech Bulletin #286)

VM is the DC voltage from the rectifier (a "cap board": AC→DC with a large reservoir
capacitor), fed through the E-stop contactor into VM+/VM− on the ALLIN1DC. The board
PWMs this to the motors. **VM must not exceed the rated voltage of any motor it drives.**

`Rectified DC output = 1.414 × AC input` (110 VAC → ~156 VDC; 220 VAC → ~311 VDC).
`AC input needed = Rectified DC output / 1.414`.

| Rectifier PN | PCB name | Input | Output |
|---|---|---|---|
| 12726 (10537 w/ transformer) | CAPBRDLO | 125 VAC max, single phase | 180 VDC max (≈155 VDC typ @ 110 VAC) |
| 10767 (10010 w/ transformer) | CAPBRDHI | 240 VAC max, two phase | 180 VDC max (≈155 VDC typ @ 220 VAC) |

Both VM+ and VM− route through the E-stop contactor. Centroid recommends the
Schneider/Telemecanique **LC1DT40B7A** E-stop contactor (PART# **14374**, 24 VAC coil,
includes snubber). Read the motor nameplate "Rated Voltage" (e.g. 180 VDC); if unknown,
use the motor model's datasheet.

## Wiring servo motors (5.4, Tech Bulletin #155)

> **Do not power the motors until instructed. Do not mechanically connect motors to the
> machine until told. A bad servo motor will damage the ALLIN1DC** — check motors first.

1. Motor disconnected: confirm **>100 MΩ** between motor chassis and motor power terminals.
2. Confirm **>100 MΩ** between ALLIN1DC chassis and its motor power terminals.
3. Wire motor power to the ALLIN1DC (Fig 5.4.1, p.47); connect the motor cable shield to
   either ALLIN1DC shield terminal.
4. Motors connected: confirm **continuity** between motor chassis and ALLIN1DC chassis
   with a DVM. *(An ungrounded servo motor is an electrocution hazard.)*
5. **Never remove the brushes** from a DC motor.
6. Connect each encoder to the matching input: **Encoder 1 ↔ Axis 1**, etc. Encoders
   **4, 5, 6** are for accessories (extra drives like a DC1, extra encoders, custom MPGs).

## Setting current limiting (5.5)

A switch bank limits max current to each servo motor (set **higher** than the motor's
rating for best performance). Located behind the cover (hole provided), Fig 5.5.1.
Switch styles: **black** — ON is *away* from PCB, OFF *toward*; **blue** — ON *toward*
PCB, OFF *away*. **Push gently — the plastic levers snap off easily.** Switches 1–2 set
Axis 1, 3–4 Axis 2, 5–6 Axis 3. The full ON/OFF setting tables are in `parameters.md`.

## Wiring E-stop (5.6, Tech Bulletin #286)

> E-stop must be wired **normally closed** (closed = operational). NO wiring is dangerous
> (a broken wire won't stop the machine) and lets noise cause spurious faults.

- **Switch:** DPST, normally closed, twist-to-release (e.g. Centroid PART# **14534**).
- **Input 11** (header H1): route in series with all E-stop switches so the PLC knows when
  E-stop is tripped. **SIP1 sets input 11's voltage (5/12/24 V) — wrong SIP DAMAGES the
  board.**
- **Output 1 (drive-fault relay):** route the E-stop contactor in series with output 1 and
  all E-stop switches, so any trip removes power from the contactor. Relay rated **10 A @
  125 VAC** or **5 A @ 30 VDC**; use the lowest practical voltage — Centroid recommends
  **24 VAC**. If extra axes are added via DC1, wire all drive-fault relays in series with
  output 1 so all drives stop together.
- Both VM− and VM+ through the E-stop contactor; snubber (PART# 1819) on the coil.

**Test:** power up → CNC12 → F10 → `alt+I` real-time I/O → invert input 11 with
`ctrl+alt+i` → apply AC to contactor → toggle E-stop: input 11 green when released, red
when pressed.

## Wiring limit switches (5.7)

> All limit-switch inputs **must be normally closed**. SIPs must match the device voltage
> or the board is DAMAGED. Proximity sensors **must be 3-wire** (NPN/PNP) — 2-wire sensors
> won't work reliably.

- Limit-switch defeaters **SW4**: point **DOWN** if black, **UP** if blue, to use the
  switches. (24 VDC to the input commons, inputs pulled down to 24 VDC COM, is standard.)
- Wiring per Fig 5.7.2 (p.52). Inputs 1–8 are the limit/home group.
- **Test:** power up → CNC12 → `alt+I` → invert each limit input (1–8) with `ctrl+alt+i`
  → green when clear, red when tripped.

## Wiring lube pump (5.8)

Default PLC: **output 2** controls the lube pump (110 VAC); **input 9** is the low-lube
alarm, which raises a **"405 Low lube"** alarm that inhibits starting a new job until
refilled and cleared. Output relay rated **5 A DC / 10 A AC** — use a contactor for
larger pumps. (Wiring Fig p.54.)

Lube-pump types: **mechanical cam** (reliable, remembers run time across power cycles);
**electronic** ("lube first" over-lubes, "lube last" may starve small jobs);
**direct-controlled** via the PLC/software — **best for reliable, even lubrication**
(Tech Bulletin #171, operator-manual Parameter 179).

**Enable:** `alt+I` → invert input 9 with `ctrl+alt+i` → green when pump has lube, red on
low-lube alarm.

## Wiring coolant pump (5.9)

Default PLC: **output 3** = coolant **flood** pump, **output 4** = coolant **mist** pump.
Larger pumps need a contactor (Flood Contactor PART# **3959**) — output relay is only
5 A DC / 10 A AC. Use a snubber (PART# 1819) on the coil and a **thermal overload
protector** (opens if the pump stalls, e.g. chips). Sample 3-phase flood circuit:
Fig 5.9.1 (p.55).

## Wiring spindle (5.10, Tech Bulletin #123 for rigid tapping)

> Test the spindle during bench test before wiring it in the cabinet.

Two methods:

1. **3-phase direct to an induction motor** (Fig 5.10.1, p.57) — cheapest, but CNC12
   **cannot control spindle speed** (speed set mechanically, e.g. pulleys/gears).
2. **Spindle controller (inverter / AC drive / VFD)** (Fig 5.10.2, p.58) — Centroid does
   **not** sell controllers; recommends Delta VFDs, Automation Direct GS2/GS3, Yaskawa VS
   (Varispeed). The integrator is responsible for VFD support.

Default-PLC spindle I/O:

| ALLIN1DC I/O | Function | ALLIN1DC I/O | Function |
|---|---|---|---|
| OUT 5 | Spindle fault reset | OUT 8 NO (normally open) | Spindle reverse |
| OUT 7 | Spindle enable | DAC OUT | Spindle speed |
| OUT 8 NC (normally closed) | Spindle forward | ADC IN | Spindle load |
| IN 10 | Spindle fault | OUT 10 | Spindle cooling fan |

> Inputs 9–12 SIP must match the voltage in use, or the board is DAMAGED. Spindle Fault,
> E-Stop Input, and Lube Fault all run off the same input voltage under the default PLC.

A thermal overload protector wired in series with the spindle enable lets both the
ALLIN1DC and the protector stop the spindle. Snubber (PART# 1819) on every contactor coil.
For rigid tapping, connect a spindle encoder (per §2.3 requirements) — set up last, after
the spindle is working (beyond this manual; see CNC12 operator manual + TB123).
