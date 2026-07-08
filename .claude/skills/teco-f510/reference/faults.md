# F510 Faults, Warnings & Diagnostics

Fault-code lookup for the F510. Sources: §10.1–10.5. Codes are the keypad **LED display**
mnemonics.

## Faults vs. warnings, and how to reset

- **Fault** (§10.2): the drive **trips** — energizes the fault-contact output and coasts the
  motor to stop (some faults allow a selectable stop mode). The code is stored in the fault
  history (Group 12: `12-45`…`12-64`; Group 13: `13-21`…`13-50`).
- **Warning / self-diagnosis** (§10.3): the code **flashes**, the fault contact does **not**
  energize, and the drive keeps running. A self-diagnostic (programming) error blocks a run
  command until the conflicting parameters are fixed. Clears automatically when the condition
  goes away.
- **Reset a fault:** (1) a digital input set to 17 (Fault Reset) via `03-00`…`03-07`, (2) the
  keypad **RESET** key, or (3) power-cycle until the keypad blanks, then re-power. Clear
  history with `13-09`.

## Fault codes — §10.2 (Table 10.2.1)

| Display | Meaning | Common causes | Fixes |
| --- | --- | --- | --- |
| `OC` | **Over-current** — output current > 200% of rated | accel/decel too short; contactor on output; oversized/special motor; short or ground fault | lengthen accel/decel; check/disconnect motor wiring |
| `SC` | **Short circuit** — output short or ground (when `08-23`=1) | motor insulation, wiring damage | check motor & wiring; disconnect motor and test |
| `GF` | **Ground fault** — ground current > 50% of rated (when `08-23`=1) | motor/wiring damage; DCCT sensor defect | replace/check motor; check resistance to ground; reduce carrier |
| `OV` | **Over-voltage** — DC bus > OV level: **410 Vdc** (230 V class) / **820 Vdc** (460 V class); for a 440 V machine with `01-14` < 460 V the level drops to 700 Vdc | decel too short (regen); input voltage too high; PFC caps; excessive braking load; defective braking transistor/resistor; bad speed-search | increase decel; lower input / add AC line reactor; remove PFC cap; add/repair dynamic braking; adjust speed search |
| `UV` | **Under-voltage** — DC bus < UV level: **190 Vdc** (230 V) / **380 Vdc** (460 V) (adjust via `07-13`), or pre-charge contactor not active while running | input too low; input phase loss; accel too short; pre-charge contactor damaged | check input & wiring; increase accel; replace pre-charge contactor / control board |
| `IPL` | **Input phase loss** (when `08-09`=1) | loose input wiring; momentary power loss; input imbalance | check input wiring / supply |
| `OPL` | **Output phase loss** (when `08-10`=1); or motor current < 10% of inverter rated | loose output wiring; motor much smaller than inverter | check output wiring; check motor/inverter rating match |
| `OH1` | **Heatsink over-heat** (3× in 5 min → wait 10 min before reset) | ambient too hot; fan failed; carrier too high; overload | cool the enclosure; replace fan; reduce carrier / load |
| `OL1` | **Motor overload** (protection curve `08-05`=xxx1) | V/F set too high (over-excitation); `02-01` rated current wrong; load too heavy | check V/F curve & `02-01`; reduce load / duty |
| `OL2` | **Inverter overload** (4× in 5 min → wait 4 min) | V/F too high; inverter undersized; load too heavy | check V/F; upsize inverter; reduce load |
| `OT` | **Over-torque** — torque > `08-15` for `08-16` (when `08-14`≠0 arms it) | load too heavy | check `08-15`/`08-16`; reduce load |
| `UT` | **Under-torque** — torque < `08-19` for `08-20` (when `08-18`≠0 arms it) | sudden load loss; belt break | check `08-19`/`08-20`; check load |
| `CE` | **Communication error** — no Modbus traffic for `09-06` time (arms per `09-07`) | link lost / wire broken; host stopped | check connection; check host/PC software |
| `Fb` | **PID feedback loss** — feedback < `10-12` for `10-13` (when `10-11`=2) | feedback wire/sensor broken | check feedback wiring / sensor |
| `StO` | **Safety switch (STO)** — F1/F2 open | run-permissive contact open; `08-30`=1 + input 58 active | check F1/F2 connection |
| `EF1`…`EF6` | **External fault** on S1…S6 (`03-0x`=25, `08-24`=0/1) | external-fault input active | check the wiring / that the input function is intended |
| `CF07` | **Motor-control fault** — SLV cannot run the motor | not auto-tuned; min output freq too low | run auto-tune (`setup.md`); raise `01-08` |
| `Fu` | **Fuse open** — DC-bus fuse blown (230 V ≥ 50 HP, 460 V ≥ 75 HP) | IGBT damaged; output short | check IGBTs / output short; replace inverter |
| `CtEr` | **Input-voltage fault (CT)** | abnormal input voltage / noise; control-board fault | check input signal & control-board voltage |
| `OPr` | **Operator disconnection** — keypad removed while running with `00-02`=0 (`16-09` sets stop vs. fault) | LCD keypad unplugged | reconnect keypad |
| `PtCLS` | **PTC signal loss** — MT open > 10 s | PTC disconnected | check MT–GND connection |

## Warning / self-diagnosis codes — §10.3 (Table 10.3.1)

Flashing; drive keeps running.

| Display | Meaning |
| --- | --- |
| `OU`/`OV` (flash) | Over-voltage warning (DC bus near the OV level) |
| `UU`/`UV` (flash) | Under-voltage warning |
| `OH2` (flash) | Inverter over-heat warning (multi-function digital input func 32) |
| `Ot` (flash) | Over-torque warning |
| `ut` (flash) | Under-torque warning |
| `bb1`…`bb6` (flash) | External **base-block** on S1…S6 (output gated off, motor coasts) |
| `OL1` / `OL2` | Motor / inverter overload (as warning) |
| `CE` (flash) | Communication error warning (when `09-07`=3) |
| `CLb` | Over-current protection level B reached (reduce load / duty) |
| `retry` (flash) | Auto-restart pending until `07-01` delay expires (`07-01`/`07-02` > 0) |
| `ES` | External emergency-stop input active (digital-input func 14) |
| `StP0` | Zero-speed stop warning — freq command below `01-08` and DC brake disabled |
| `WRE` | Operator writing error — keypad can't write to inverter (firmware/KVA/model mismatch) |
| `VRYE` | Operator verifying error — keypad data ≠ inverter data |
| `RDP` | Operator read prohibited — set `16-08`=1 to allow keypad→inverter backup |
| `EF` | Repeat run command — FWD and REV both present (one-direction machine) |
| `CF00`/`CF01` | LCD-keypad comm fault (>5 s / >2 s no keypad↔inverter comm) |
| `CF20` | Double-communication error — both PROFIBUS and MODBUS selected; pick one |

## Auto-tuning errors — §10.4 (IM motor, display `AtErr`, detail in `17-11`)

| Code | Meaning | Fix |
| --- | --- | --- |
| ATE01 | Motor data input error / output current ≠ rated | check `17-00`…`17-09`; check inverter capacity |
| ATE02 | Stator (R1) resistance tuning error | check tuning data; check motor connection; disconnect load |
| ATE03 | Leakage-inductance tuning error | " |
| ATE04 | Rotor (R2) resistance tuning error | " |
| ATE05 | Mutual-inductance (Lm) tuning error | " |
| ATE06 | Motor encoder error | check rated current; check PG-card grounding |
| ATE07 | Dead-time compensation detection error | check tuning data / connection |
| ATE08 | Motor acceleration error (rotational tune only) | increase `00-14`; disconnect load |
| ATE09 | Other (no-load current > 70% rated; torque ref > 100%) | check tuning data / connection |

## PM-motor auto-tuning errors — §10.5 (display `IPErr`, detail in `22-18`)

`01` magnetic-pole alignment failure · `05` circuit-tuning timeout · `06` encoder error ·
`07` other tuning error · `09` current out of range · `11` parameter-tuning timeout (check
`22-11` not set too low). Fixes: check `22-02` motor data, inverter capacity, and motor
connection.

## Out-of-scope faults (pointer only)

Pump/HVAC faults `LOPbt`/`HIPbt` (low/high flow), `LPbFt`/`OPbFt` (low/high pressure),
`LSCFt` (low suction), `FbLSS` (PID feedback signal loss), and `OL4` (air-compressor
overload) belong to the Pump/HVAC feature (Group 23/24) — see §10.2–10.3 and Group 23 in the
manual if that feature is enabled.
