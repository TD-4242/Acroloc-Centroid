# Troubleshooting Reference

Symptom → cause → fix for the ALLIN1DC, plus LED diagnostics.
Source: install manual Appendix B and Ch2.4. LED locations/nominal states are in
`hardware.md`. Many entries point to a Centroid Tech Bulletin (TB) for depth.

## Status LED troubleshooting (App B)

| Symptom | Possible cause | Corrective action |
|---|---|---|
| All status LEDs out | Logic power not applied | Measure AC into the logic supply and DC out of it; check logic-power wiring |
| Some (not all) power LEDs out (+3.3/+5.0/+12.0/−12.0 V) | Power-supply failure or wiring problem | Check the supply and wiring |
| Analog +12.0 V or −12.0 V LED out | Loss of power to the analog section | If the other LEDs are lit, the analog section is likely damaged — return for repair |
| FPGA OK not lit | Not ready / internal fault | Wait for run mode; if it never enters run mode after start-up, hardware failure likely — return for repair |
| DSP OK not lit | Booting up | Wait for hardware detection / run mode |
| DSP Debug flashing fast | Detecting hardware | Wait for it to finish and enter run mode |
| DSP Debug flashing 1×/sec | Using MPU11 drive protocols | None (normal) |
| DSP Debug flashing 2×/sec | Using legacy drive protocols | Internal fault — return for repair |
| Drive Fault LED out | Drive-fault relay open: can't talk to PC, or a drive fault was detected (see §4.1, 5.3, 5.6) | Toggle an input (e.g. E-stop); if the PC doesn't see it, it's a comm error. If it does, press MDI and check the status menu for errors |
| PLC OK out | Motion-control processor hasn't booted | Restart CNC12, wait for the main screen; if still out, return for repair |
| LED1 flashing a number with a decimal point | Error code | See LED1 table below |

## LED1 seven-segment display (Ch2.4 / App B)

A solid number (no decimal) = drive-bus order (1 if no DC1). A flashing number **with a
decimal point** = an error:

| Error # | Meaning | Cause | Corrective action |
|---|---|---|---|
| 1 | Power failure (Rev 100315 and earlier only) | Logic supply out of spec | Check power-supply wiring; replace supply |
| 2 | 15 A not available | Current switches set to 15 A on a Low-Power ALLIN1DC lacking the FETs — drops back to 12 A | Select ≤12 A, or use a regular ALLIN1DC |
| 3 | Null error | Self-adjust detected too large a current-feedback offset; usually a current-sensor failure | Return the drive for repair |
| 4 | Limit tripped | Any limit switch is tripped | Move off the limit, check limit wiring, or use the limit-defeat switch if a limit isn't required |
| Single dash (−) / other unusual behavior | Logic problem | Board logic not starting correctly | Check logic power, or contact Centroid Support for an RMA |

## Misc troubleshooting (App B)

| Symptom | Possible cause | Corrective action |
|---|---|---|
| 3-wire sensor input doesn't work | Voltage drop across the sensor too high | Reduce the voltage drop across the sensor |
| "Full Power Without Motion" when commanding a move | CNC12 can't see the encoder move when the motor is told to move | Confirm the right encoder is on the right axis; check axis/encoder assignment (P300–315); check for blown fuses; check for reversed motor polarity / encoders counting the wrong way; check encoder wiring |

## General problems → Tech Bulletins (App B)

- **Motor doesn't move, no error/fault** → TB285
- **No VM at the drive terminals when E-stop is released** → TB286
- **Encoders not counting / DRO not updating** → TB281

## Software errors → Tech Bulletins (App B)

- **"Jog Panel Communication Fault"** → TB282
- **"Quadrature errors" / "Differential Encoder errors"** → TB280
- **"Error Initializing MPU 11"** → TB279, TB309
- **"PC Data Receive Errors"** → TB270 (often an unshielded Ethernet cable — see `hardware.md`)
- **"Timeout: MPU11 not responding"** → wrong Ethernet port; set the adapter to IP
  **10.168.41.1 / 255.255.255.0** (see `software-setup.md`)

## Accuracy problems (App B)

DRO accuracy issues → recalibrate per §6.5 (coarse) and §6.9 (fine); see `commissioning.md`.

## Run-away motor ("SV_ Stall Error", motor "takes off")

The control isn't seeing proper encoder signals — bad encoder config, or **reversed motor
power leads** (control commands one direction while the encoder reports the other). Check
encoder wiring/assignment and motor polarity (§6.3, see `commissioning.md`).
