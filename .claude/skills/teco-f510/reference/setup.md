# F510 Setup — modes, command sources, motor tuning, accel/decel

How to get the F510 running a motor: pick a control mode, choose where run/speed commands
come from, enter the motor nameplate and auto-tune, and set ramp times. Sources: Group 00/01/
02/17 (§4.2–4.3), Ch 6 (frequency reference), Ch 7 (run/stop), §8.2 (accel/decel), §8.6
(analog output), §6.5 (display unit).

## 1. Control mode — `00-00` (do this first)

| `00-00` | Mode | Use it for |
| --- | --- | --- |
| 0 | **V/F** (scalar) | Simple / multi-motor / when auto-tune isn't possible. Uses the Group 01 V/F curve. |
| 2 | **SLV** (sensorless vector, induction) | Higher torque & speed regulation on one induction motor; needs Group 02 motor data + auto-tune. |
| 5 | **PM SLV** (sensorless vector, PM motor) | Permanent-magnet motors; uses Group 22 PM parameters. |

The mode gates which parameters are active (the manual's per-parameter `V/F / SLV / PM SLV`
columns show `O`/`X`). Set it before entering motor data or tuning.

## 2. Command sources — run and frequency

**Run command — `00-02`** (`00-03` = alternative): `0` keypad · `1` external terminal · `2`
communication (RS-485) · `3` PLC · `4` RTC.
**Frequency command — `00-05`** (`00-06` = alternative): `0` keypad · `1` analog **AI1** ·
`2` terminal UP/DOWN · `3` communication (RS-485) · `6` RTC · `7` AI2 auxiliary.

Common wiring (Ch 6/7 diagrams; terminal detail in `wiring-and-terminals.md`):

- **Analog 0–10 V on AI1** (`00-05` = 1): drive `AI1` from a 0–10 V source referenced to
  `GND`. **This is how an external controller's 0–10 V speed-command output drives the
  F510** (see `SKILL.md` "controller ↔ VFD seam"). A **1–5 kΩ potentiometer/speed-pot** wired
  across `+10V` / `AI1` / `GND` is the manual variant.
- **Analog 4–20 mA on AI2** (`00-05` = 7 for aux, or as master): set hardware switch **`SW2`
  to `I`** for current mode (default is `V`).
- **Keypad** (`00-02`/`00-05` = 0): `RUN`/`STOP` and `▲`/`▼`. **RS-485** (`00-02` = 2,
  `00-05` = 3): see `communication.md`. **External contacts**: 2-wire (maintained switch on
  `S1`) or 3-wire push-buttons (`S1` start / `S2` stop / `S5` FWD-REV, set via a 3-wire
  `13-08` init and `03-05` = 26).
- `00-28` sets the analog **characteristic**: `0` positive (0–10 V/4–20 mA → 0–100%) or
  `1` negative (→ 100–0%). Analog input scaling/bias lives in Group 04.

## 3. Motor nameplate + auto-tuning (SLV / PM SLV)

Enter the nameplate, then auto-tune so the drive measures motor constants. In SLV, always
auto-tune before running in vector control.

**Group 17 — IM auto-tuning** (§4.2 p.121; keypad flow §4.1.2):

| Code | Name | Options / range |
| --- | --- | --- |
| 17-00 | Tune Mode Selection | 0 Rotational · 1 Static · 2 Stator-resistance measurement · 4 Loop tuning · 5 Rotational combo · 6 Static combo |
| 17-01 | Motor Rated Output Power | 0.00–600.00 kW |
| 17-02 | Motor Rated Current | 0.1–1200.0 A |
| 17-03 | Motor Rated Voltage | 200V 50–240 / 400V 100–480 V |
| 17-04 | Motor Rated Frequency | 4.8–400.0 Hz |
| 17-05 | Motor Rated Speed | 0–24000 rpm |
| 17-06 | Number of Motor Poles | 2–16 (even) |
| 17-10 | Automatic Tuning Start | 0 Disable · 1 Enable (then press `RUN`) |
| 17-11 | Error History of Auto-Tuning | 0 none · 1 motor-data · 2 stator-R · 3 leakage · 4 rotor-R · 5 mutual-induction · 7 DT · 8 accel · 9 warning |

**Procedure:** set `00-00` to the vector mode → enter `17-01`…`17-06` from the nameplate →
select `17-00` tune mode → set `17-10` = 1 → press **`RUN`**. On success the computed
constants save into **Group 02** (motor parameters). The whole tune takes ~50 s; the keypad
shows `>>>` / `Atund`. Abort with `STOP`. On a fault the keypad shows the uncompleted message
and an `ATE` code (`faults.md`), and Group 02/17 revert to factory — re-enter and retry.

> **Warning (verbatim §4.1.2):** do **not** use `17-00` = 0 (Rotational) when the load is
> coupled to the motor — the shaft spins during a rotational tune. Use a static tune
> (`17-00` = 1) if the motor cannot free-spin.

(For V/F mode, no auto-tune: set the Group 01 V/F curve — `01-02` max output freq, `01-03`
max output voltage, `01-12` base frequency, `01-13` base output voltage, `01-14` input
voltage — from the motor nameplate.)

## 4. Acceleration / deceleration and S-curve

- **Ramp times** — `00-14`/`00-15` (Accel/Decel Time 1), `00-16`/`00-17` (Time 2),
  `00-21`–`00-24` (Times 3 & 4), each 0.1–6000.0 s. Times are referenced to **maximum
  frequency** and expressed by the three most-significant digits (§8.2). Select among the
  four pairs via multi-function inputs (`03-xx` functions 10/30) or auto-switch at
  `00-25` (Acc/Dec switch-over frequency). Jog uses `00-19`/`00-20`.
- **S-curve** — Group 11: `11-04` (start of accel), `11-05` (end of accel), `11-06` (start of
  decel), `11-07` (end of decel), each 0.00–2.50 s (default 0.20). S-curve softens the knees
  of the ramp to reduce mechanical shock.
- **Note (§8.2):** if accel/decel times are set too short for the load inertia/torque, the
  **stall-prevention / torque-limit** function activates and *stretches* the actual ramp
  beyond the set time. Decel that's too aggressive raises DC-bus voltage — see OV-prevention
  and braking in `braking-and-protection.md`.
- **Stop mode** is `07-09` (0 decel · 1 coast · 2 DC-braking · 3 coast-with-timer); DC
  injection braking is `07-06`/`07-07`/`07-08`. Emergency-stop time is `00-26` (used with
  digital-input function 14).

## 5. Analog output (monitoring) — §8.6

Two analog outputs, **AO1** and **AO2** (0–10 V / 4–20 mA):

- **AO1:** signal select `04-11`, gain `04-12` (0.0–1000.0%), bias `04-13` (−100.0–100.0%).
- **AO2:** signal select `04-16`, gain `04-17`, bias `04-18`.
- `04-11`/`04-16` signal options include: 0 output frequency · 1 frequency command · 2 output
  voltage · 3 DC voltage · 4 output current · 5 output power · 6 motor speed · 10 torque
  command · 21 PID input · 22 PID output · 28 communication-control. Set **gain** so
  10 V/20 mA = 100% of the selected signal and **bias** so 0 V/4 mA = 0%.

## 6. Display unit Hz ↔ rpm — `16-03`

`16-03` = 0 shows Hz (0.01 Hz res); 1 shows %; **2–39 shows rpm** (computed from motor
poles — e.g. set `16-03` = number of poles); 40+ apply decimal-scaling variants for a custom
100% value. Handy when you want the keypad reading in spindle rpm rather than Hz.
