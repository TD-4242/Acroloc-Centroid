# Official ALLIN1DC Example Projects

When implementing a feature, find the closest official example here and crib its proven
pattern rather than inventing from scratch.

All paths are relative to the repository root. Source files are under
`docs/official/_ALLIN1DC/`.

## Standard builds

| Path | What it demonstrates |
|---|---|
| `docs/official/_ALLIN1DC/_basic/cncm/allin1dc-basic-v6.src` | Baseline ALLIN1DC mill PLC with keyboard jog; the canonical reference starting point for any new build (CNC11 3.12+) |
| `docs/official/_ALLIN1DC/_basicVCPMpgBeta/cncm/allin1dc-basic-mill-skin2.src` | Basic mill PLC extended with VCP (virtual control panel) and wireless MPG support (CNC12 4.09r10+, beta) |
| `docs/official/_ALLIN1DC/_BOSSVCPMpgBeta/cncm/allin1dc-BOSS-mill-skin2.src` | BOSS-variant mill PLC with VCP and wireless MPG; uses P800 control-type parameter to set VCP key layout/labelling |

## ATC builds

| Path | What it demonstrates |
|---|---|
| `docs/official/_ALLIN1DC/_atc/_umbrella/cncm/allin1dc-umbrella-v7.src` | 16/16 umbrella ATC with spindle orient (M19), carousel in/out (M80/M81), throwaway count on reversal, spindle load meter, and Z-brake release (CNC11 3.14+) |
| `docs/official/_ALLIN1DC/_atc/_umbrella_no_throw_away_std_io/cncm/A1DC-umb-stdio-no-throwaway.src` | 16/16 umbrella ATC with standardized I/O and no throwaway count on carousel reversal; simpler state machine than the v7 umbrella (CNC11 3.16+) |

## Custom builds

| Path | What it demonstrates |
|---|---|
| `docs/official/_ALLIN1DC/_custom/_allin1dc-basic_3rd_axis_brake/cncm/allin1dc-basic_3rd_axis_brake.src` | Basic mill PLC with OUT9 driven as a 3rd-axis electromagnetic brake output; shows brake-release pattern around axis motion |
| `docs/official/_ALLIN1DC/_custom/allin1dc-basic-v2-with_remote_start/cncm/allin1dc-basic-v2-with_remote_start.src` | Basic mill PLC with INP13 wired as a remote cycle-start input; demonstrates external-trigger → `SV_CYCLE_START` pattern |
| `docs/official/_ALLIN1DC/_custom/_allin1dc-basic-w-lowrange-reverse/cncm/allin1dc-basic-w-lowrange-reverse.src` | Basic mill PLC with low-range spindle speed and VFD reverse-direction support; shows 12-bit DAC spindle control with range switching |
| `docs/official/_ALLIN1DC/_custom/_allin1dc-msc_handbrake-mill/cncm/allin1dc-msc_handbrake-mill.src` | MSC mill PLC that stops and prevents the spindle whenever the handbrake (INP13, NC-wired, inverted via P178 bit 3) is engaged |
| `docs/official/_ALLIN1DC/_custom/_allin1dc-spindle-brake/cncm/allin1dc-spindle-brake-v2.src` | Standard basic PLC with spindle-brake logic on AUX3; `BrakeMode_M` tracks brake state and AUX3 is forced ON at power-up (CNC11 3.16+) |
| `docs/official/_ALLIN1DC/_custom/_bp-boss-allin1dc-analog/cncm/allin1dc-bp-boss-analog-v3.src` | Bridgeport BOSS mill PLC with analog spindle speed control (pot + speed-up/down solenoids via aux outputs) and spindle brake release |
| `docs/official/_ALLIN1DC/_custom/_bp-boss-allin1dc/cncm/allin1dc-bp-boss-v4.src` | Bridgeport BOSS mill PLC with standardized I/O schematic; digital-only spindle control, no analog pot; updated I/O mapping Oct 2017 |
| `docs/official/_ALLIN1DC/_custom/_cptools/cncm/allin1dc-cptools-mill.src` | CP Tools mill PLC with timed spindle brake: P901 = ms delay after spindle off before engaging, P902 = brake hold duration |
| `docs/official/_ALLIN1DC/_custom/_dm45-allin1dc/cncm/dm45-allin1dc.src` | DM45 drillmill PLC; based on the low-range/reverse variant — demonstrates machine-specific customization of the lowrange-reverse base |
| `docs/official/_ALLIN1DC/_custom/_forest-scientific-atc-router/cncm/allin1dc-forest-scientific-atc-router.src` | Forest Scientific router PLC with rack-mount ATC tool changer (keyboard jog + tool-change stage); different ATC topology from the umbrella |
| `docs/official/_ALLIN1DC/_custom/_k100075/cncm/k100075.src` | K100075 custom build: basic mill PLC with 12-bit DAC spindle speed output and multi-range spindle control |
| `docs/official/_ALLIN1DC/_custom/_k100113/cncm/horizontal/k100113-horizontal.src` | K100113 horizontal mill: dual-spindle output mapping (Spindle1=OUT6/OUT9, Spindle2=OUT7/OUT8), RotaryTableHome on INP7, cross-axis jog-disable on probe fault |
| `docs/official/_ALLIN1DC/_custom/_k100113/cncm/k100113-vertical.src` | K100113 vertical mill — top-level copy (duplicate of the `vertical/` subdir copy below); vertical spindle output mapping (Spindle2=OUT6, Spindle1=OUT7), no RotaryTableHome |
| `docs/official/_ALLIN1DC/_custom/_k100113/cncm/vertical/k100113-vertical.src` | K100113 vertical mill — canonical copy stored in `vertical/` subdirectory for deployment; identical logic to the top-level copy above |
| `docs/official/_ALLIN1DC/_custom/_k100242/cncm/allin1dc-K100242.src` | K100242 custom build: two independent air-spindle outputs controlled by Aux keys and M-codes M13/M23 (auxSpin1 on/off) and M14/M24 (auxSpin2 on/off) |
| `docs/official/_ALLIN1DC/_custom/_k100374/cncm/allin1dc-100374.src` | K100374 custom build: adds spindle speed-up/down relay outputs, drawbar output, and spindle brake to the standard basic mill PLC |
