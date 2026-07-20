# Spindle Load Meter - Design

Date: 2026-07-20
Status: approved (brainstorm)

## Goal

Get a real spindle-load signal flowing from the TECO F510 VFD into the Centroid
load meter, and surface that load as a LOAD readout on the retro VCP.

The PLC half already exists: Centroid's stock `LoadMeterStage` (STG6) is present in
`Centroid-Acroloc-ALLIN1DC.src`. This project does not add PLC logic; it (A) defines
the on-machine procedure to make the existing meter read real load, and (B) adds a
generator-only VCP readout of the value the PLC already computes.

## Background: what already exists

Signal path end to end:

```
F510 analog output (AO1/AO2, 0-10V)
  -> wire
  -> ALLIN1DC single 12-bit analog input (INP241 = AnalogIn1Bit0_I)
  -> LoadMeterStage (STG6)
  -> SV_SPINDLE_METER (drives CNC12's built-in load meter)
```

`LoadMeterStage` (src:2636-2645):

```
IF True_M THEN BTW SpindleMeter_W AnalogIn1Bit0_I 16   ; read the 12-bit ADC as a word
IF SpindleMeter_W > 32767 THEN SpindleMeter_W = SpindleMeter_W - 65536  ; sign extend
IF True_M THEN SpindleMeter_W = (SpindleMeter_W * 100) / 2048   ; scale to percent
IF True_M THEN SV_SPINDLE_METER = SpindleMeter_W
```

The stage is gated by machine parameter 57 (src:1372-1373):

```
IF SV_MACHINE_PARAMETER_57 != 0 THEN SET LoadMeterStage
IF SV_MACHINE_PARAMETER_57 == 0 THEN RST LoadMeterStage
```

Key facts:

- `SpindleMeter_W` is **W59**; it already holds the load percent whenever the stage
  runs. This is the value the VCP readout will display. No new PLC word or `.src`
  edit is required for the display.
- The board has ONE analog input. The spindle-speed *command* leaves on the analog
  *output* (`SpinAnalogOutBit0_O` = OUT241..252); the analog *input* (INP241..252) is
  free and is what `LoadMeterStage` reads. No conflict with spindle command.
- With P57 = 0 the stage never runs and `SpindleMeter_W` is stale/zero. Enabling P57
  is the first required step.

## Half A - Commissioning and verification (on-machine, operator-run)

Cannot be scripted from the repo; this is VFD/board config plus wiring. Verify from
the controller inward so the cheapest checks come first.

1. **Enable the stage.** Set machine parameter 57 to a nonzero value in CNC12.
   (0 = meter off.) This alone may explain a dead meter.
2. **Find the display.** With P57 on, CNC12 draws its built-in spindle load meter on
   the run screen, fed by `SV_SPINDLE_METER`. Confirm it appears.
3. **Watch the raw signal live.** Use CNC12's PLC diagnostic screen to watch
   `AnalogIn1Bit0_I` / `SpindleMeter_W` while revving the spindle by hand.
   - Signal moves -> wiring is good; go to step 7 (calibration).
   - Dead flat -> wiring/config problem; continue with steps 4-6.
4. **Trace the wire.** Confirm a physical wire from an F510 analog-output terminal
   (AO1 or AO2) to the ALLIN1DC analog input terminal. If none exists, land one -
   that is the whole problem.
5. **Configure the F510 output** (Group 04, external analog I/O):
   - Signal select: `04-11` (AO1) or `04-16` (AO2) = **4 (output current)** - the
     classic spindle-load proxy, valid in any control mode.
   - Range: 0-10V (the AOs do 0-10V or 4-20mA; the board wants voltage).
   - Gain/bias: `04-12`/`04-13` (AO1) or `04-17`/`04-18` (AO2) for scaling.
   - Note: the F510 manual flags AO1/AO2 as meter-only outputs, which is exactly this
     use.
6. **Configure the board input** for 0-10V per the ALLIN1DC manual (the input
   supports 0-5 / 0-10 / +/-5 / +/-10 V).
7. **Calibrate the scale.** Stock scaling is `SpindleMeter_W = ADC * 100 / 2048`.
   Load the spindle to a known draw and adjust the F510 AO gain (`04-12`/`04-17`) so
   full rated load reads about 100%. This is the one genuinely iterative step.

**Open decision (non-blocking): load signal source.** Default recommendation is
output current (`= 4`). If the F510 runs in SLV/vector mode on this machine, output
power (`5`) or torque (`10`) track mechanical load more faithfully. Switching later
is a VFD-only change; it does not touch the repo.

## Half B - LOAD readout on the retro VCP (generator-only)

- Value source: `SpindleMeter_W` (W59), already populated by `LoadMeterStage`. No
  `.src` edit; a `plc_word` reading W59 is all that is required.
- Placement: row 2, cols 1-3 (currently empty), mirroring the spindle `% / RPM`
  readout at row 2 cols 4-6. Symmetric, spindle-related, displaces nothing.
- Style: match the existing readouts - DSEG7 red 7-segment digits plus a separate
  Arial `%`, over a reused `feedrate_bezel.svg` window, with a static `LOAD` label.
  No new SVG art; pure `tools/vcpgen.py` additions (a readout block in `render_skin`,
  then regenerate the skin).
- The readout reads 0 until Half A is live and P57 is on, so it also serves as the
  at-the-spindle calibration display during Half A step 7.

**Not doing:** a graphical bar/gauge. The VCP has no native bar element; faking one
with segmented image swaps is a lot of machinery for a worse result than a clean
numeric percent. (YAGNI.)

## Deliverables

1. This design doc.
2. Generator change: LOAD readout in `tools/vcpgen.py`; regenerated
   `resources/vcp/skins/acroloc_retro_vcp_skin.vcp`. `tools/test_vcpgen.py` stays
   green. No `./compile.sh` impact (no `.src` edit).
3. Doc cross-reference: where `docs/plc-spec/` describes `LoadMeterStage` / P57
   (boot.md, parameters.md, main-stage.md, definitions.md), note that the retro VCP
   now surfaces `SpindleMeter_W` as a LOAD readout.

## Non-goals

- No PLC logic changes; `LoadMeterStage` is stock and stays as-is.
- No change to the load-meter scaling formula (calibrate via the VFD gain instead).
- No graphical bar/gauge widget.

## Testing / rollout

- `python3 tools/vcpgen.py`; `python3 tools/test_vcpgen.py` (structure checks).
- Copy `resources/vcp/` to the control PC, restart CNC12, confirm the LOAD window
  renders at row 2 cols 1-3.
- Half A is validated on-machine per the procedure above (P57 on, signal live,
  scale calibrated against a known load).
