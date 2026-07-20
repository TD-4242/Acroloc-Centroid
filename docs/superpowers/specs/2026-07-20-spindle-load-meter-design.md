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

## Half B - LOAD bar + readout on the retro VCP

A segmented bar-graph load meter, plus a small numeric percent, at row 2 cols 1-3 -
mirroring the spindle `% / RPM` readout at row 2 cols 4-6 (currently empty,
displaces nothing).

### The faked bar (DSEG7 repunit trick)

The VCP has no native bar/gauge element, but a row of DSEG7 `1` glyphs reads as a
segmented bar-graph meter and stays entirely text-based (no image-swap machinery).
A `plc_word` renders an integer's value, so the PLC computes a **repunit** (1, 11,
111, ...) whose digit count is the number of lit segments.

- **Resolution: 10 segments, one per 10% load.** A PLC `W` is a 32-bit integer
  (max 2,147,483,647), so a single word holds at most ten `1`s
  (`1111111111` = 1.11e9, fits; eleven would overflow). Ten segments = one word, so
  10%/segment is the natural single-word choice.
- **New PLC word `LoadBar_W`**, built by a threshold ladder placed inside
  `LoadMeterStage` right after `SpindleMeter_W` is scaled (so it only updates when
  the meter is enabled), tagged `; Acroloc`:

  ```
  IF True_M THEN LoadBar_W = 0
  IF SpindleMeter_W >= 10  THEN LoadBar_W = 1
  IF SpindleMeter_W >= 20  THEN LoadBar_W = 11
  IF SpindleMeter_W >= 30  THEN LoadBar_W = 111
  ... (ascending; each rung overwrites the lower)
  IF SpindleMeter_W >= 100 THEN LoadBar_W = 1111111111
  ```

- **Static dim track** behind the bar: a free `<text>` of ten dim `1`s so the empty
  portion of the meter is visible (the full `[ 1 1 1 1 1           ]` frame). The
  live `LoadBar_W` `plc_word` renders bright, left-aligned, over the track.

### Numeric percent

Alongside the bar, a small numeric percent reading `SpindleMeter_W` (W59, already
populated by `LoadMeterStage`) with a `%` - same DSEG7 + Arial `%` style as the
existing feedrate/RPM readouts.

### Style and placement

- DSEG7 red 7-segment glyphs, over a reused `feedrate_bezel.svg` window, with a
  static `LOAD` label. No new SVG art.
- The bar and numeric both read 0 until Half A is live and P57 is on, so they double
  as the at-the-spindle calibration display during Half A step 7.

### Known visual risk (on-machine tuning)

DSEG7's `1` is the two right-hand segments of a full-width cell, so the ticks render
gappy (a picket-fence bar, not a solid fill). Whether that reads well - and the
inter-tick spacing / font size - can only be judged on the control PC; there is no
local VCP renderer. Tune font size / margins on-machine, consistent with how the
other DSEG7 readouts were dialed in.

## Deliverables

1. This design doc.
2. PLC change: new word `LoadBar_W` + the threshold ladder inside `LoadMeterStage`,
   tagged `; Acroloc`. Verified with `./compile.sh` (report token/warning delta).
3. Generator change: LOAD bar + numeric readout in `tools/vcpgen.py`; regenerated
   `resources/vcp/skins/acroloc_retro_vcp_skin.vcp`. `tools/test_vcpgen.py` stays
   green.
4. Doc updates: add `LoadBar_W` and the ladder to `docs/plc-spec/` where
   `LoadMeterStage` / P57 are described (definitions.md, main-stage.md, parameters.md,
   boot.md), and note that the retro VCP surfaces the load bar + `SpindleMeter_W`.

## Non-goals

- No change to the stock `LoadMeterStage` read/scale rungs; the only PLC addition is
  the `LoadBar_W` ladder feeding the VCP bar.
- No change to the load-meter scaling formula (calibrate via the VFD gain instead).
- No native graphical bar/gauge widget and no image-swap bar; the bar is the DSEG7
  repunit trick only.
- No finer than 10-segment (10%) resolution; a 20-segment (5%) two-word version was
  considered and deferred as not worth the extra PLC logic.

## Testing / rollout

- `./compile.sh` after the `.src` edit (token/warning delta reported).
- `python3 tools/vcpgen.py`; `python3 tools/test_vcpgen.py` (structure checks).
- Copy `resources/vcp/` to the control PC, restart CNC12, confirm the LOAD bar +
  numeric render at row 2 cols 1-3; tune DSEG7 tick spacing/size on-machine.
- Half A is validated on-machine per the procedure above (P57 on, signal live,
  scale calibrated against a known load), with the new bar as the calibration
  display.
