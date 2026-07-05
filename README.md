# Acroloc-Centroid

Centroid **CNC12** PLC program and M-code macros for an **Acroloc** mill retrofitted with a
Centroid **ALLIN1DC** motion controller (MPU11-based).

This repo is the controller-level source: a PLC program written in Centroid's stage/ladder
language, plus the M-function macros that the CNC calls. It is compiled and loaded by the
Centroid CNC12 software (`cncm`) on the Windows control PC — there is no build step in this
repository.

## Files

| File | Purpose |
| --- | --- |
| `Centroid-Acroloc-ALLIN1DC.src` | The PLC program (definitions + stages). Primary file. |
| `plc.map` | Generated symbol→source-line map from the PLC compiler. Do not hand-edit. |
| `mfunc3.mac` / `mfunc4.mac` | Spindle start CW / CCW |
| `mfunc6.mac` | Tool change (M6) — drives the custom Acroloc ATC |
| `mfunc7.mac` / `mfunc8.mac` | Coolant: mist / flood |
| `mfunc10.mac` / `mfunc11.mac` | Clamp on / off |

Custom logic added for this machine is tagged with the comment marker `; Acroloc` throughout
the `.src`.

## Spindle speed & range (transmission) shifting

The Acroloc spindle has a **two-speed transmission** (low / high range). The PLC reads which
range the gearbox is in, reports it to the CNC, and scales the analog speed command so the
displayed/commanded RPM matches the gear that is actually engaged.

### Range selection

The current gear (`SpindleRange_W`) is now tracked from the **clutch outputs the PLC itself
commands** (`EngagedRange_W`; see "Automatic RPM-based gear shifting" below), not from a
sense switch. The stock scheme this replaced read a low-gear sense input and defaulted to
high range as a fail-safe:

```
; stock code, REPLACED by the RPM auto-shift decision block
IF True_M         THEN SpindleRange_W = 4     ; default to HIGH range (fail-safe)
IF SpinLowRange_I THEN SpindleRange_W = 1     ; INP13 active  -> LOW range
```

> The stock inputs `SpinLowRange_I (INP13)`, `SpinMedRange_I (INP14)` and
> `SpinHighRange_I (INP15)` remain defined but are **no longer referenced by any logic** —
> gear position is tracked open-loop from the commanded clutches.

### Range → speed-scaling ratio

`SpindleRange_W` selects a ratio (`SpinRangeAdjust_FW`) and reports the range to CNC12 via the
`SV_SPINDLE_LOW_RANGE` / `SV_SPINDLE_MID_RANGE` flags:

| `SpindleRange_W` | Range | Ratio source (`SpinRangeAdjust_FW`) |
| --- | --- | --- |
| 1 | Low | `SV_MACHINE_PARAMETER_65` |
| 2 | Med-low | `SV_MACHINE_PARAMETER_66` |
| 3 | Med-high | `SV_MACHINE_PARAMETER_67` |
| 4 | High | `1.0` |

A **negative** ratio parameter reverses the motor (sets `SpinRangeReversed_M`) and the
absolute value is used as the real ratio; the ratio is also floored at `0.001` since the code
later divides by it.

### Speed command → DAC output

Each scan the PLC builds the analog spindle command (`MainStage`):

1. Read configured min/max RPM (`SV_PC_CONFIG_MIN/MAX_SPINDLE_SPEED`) and compute
   `RPMPerBit_FW = MaxSpeed / 4095`.
2. Pick the commanded speed:
   - **Auto mode:** `SpinSpeedCommand_FW = SV_PC_COMMANDED_SPINDLE_SPEED` (override already
     factored in by CNC12).
   - **Manual mode:** `MaxSpeed × (SV_PLC_SPINDLE_KNOB / 200) × SpinRangeAdjust_FW`.
   - Spindle disabled (`!SpindleEnableOut_O`) forces `0`.
3. Clamp to `[MinSpeed × ratio, MaxSpeed × ratio]` (low-clamp posts the "min speed" message).
4. Convert to a 12-bit value: `TwelveBitSpeed_FW = SpinSpeedCommand / RPMPerBit`, then
   **divide by `SpinRangeAdjust_FW` to factor in the gear range**.
5. Bound to `0–4095` and write to the analog output (`WTB TwelveBitSpeed_W SpinAnalogOutBit0_O 12`).

The relevant gear-ratio parameters are set in CNC12's machine parameters (Parameter 65 for the
low range on this machine).

### Automatic RPM-based gear shifting

The PLC now **commands** the two-speed transmission automatically from the commanded
spindle RPM (it no longer relies on the `SpinLowRange_I`/INP13 lever sense for selection).

- `MainStage` computes `DesiredRange_W` from the **un-overridden S value**
  (`GearBaseSpeed_FW` = `SV_PC_COMMANDED_SPINDLE_SPEED` with the spindle-override knob
  backed out) versus a crossover machine parameter with a hysteresis deadband
  (Parameter 941 crossover RPM, 942 hysteresis; 941 ≤ 0 disables auto-shift). Sweeping
  the override knob changes speed within the engaged gear but never triggers a shift.
  On this machine low gear covers ~0–1200 RPM and high gear ~1000–3500 RPM, so the
  intended settings are P941 = 1100, P942 = 100 (shift up at ≥ 1200, down at ≤ 1000).
- When the desired gear differs from the engaged gear, the kickoff arms the coast timer
  and `GearShiftStage` (STG17) performs an **open-loop clutch swap**: release both
  clutches (`Spindle_Low_gear_O`/OUT19, `Spindle_High_gear_O`/OUT20), **coast in neutral
  for a fixed dwell** (Parameter 943 ms; 0 → default 1500), then engage the target
  clutch. No exact rev-match is required — during the coast the DAC already commands the
  motor through the new gear's ratio, so the motor side arrives near the right speed
  passively. There is **no fault path**: a dwell always elapses, so a shift always
  completes. There is no post-shift lockout either — back-to-back shifts are paced by
  the coast dwell itself.
- The two clutch outputs are **mutually exclusive** (a safety interlock forces neutral if
  both are ever energized, and marks the gear unknown so the next demand re-shifts).
  Power-up engages **low** range.

> **Open-loop caveat:** there is no gear-position or speed feedback in the shift sequence;
> the engaged gear is tracked in `EngagedRange_W` from the clutch-output state, and the
> coast dwell is the only confirmation that a shift completed.

On-machine verification steps (shift boundaries, coast-dwell tuning, RPM accuracy) are in
[`docs/testing/rpm-gear-shift-test-plan.md`](docs/testing/rpm-gear-shift-test-plan.md).

## Automatic tool changer (ATC)

The Acroloc uses a **rotary carousel** tool changer. A tool change spans three places:
`mfunc6.mac` (the M6 macro), the ATC kickoff/safety logic in `MainStage`, and the
`ATCStage` (STG16) state machine that actually indexes the carousel. All of this is custom
work tagged `; Acroloc`.

### I/O and variables

| Symbol | Resource | Role |
| --- | --- | --- |
| `M6_SV` | `SV_M94_M95_8` | Tool-change request flag (set by `M94 /8`) |
| `ChangeToTool_W` | `W72` | Target tool number for this change |
| `CarouselToolID_W` | `W71` | Tool currently passing the spindle (decoded live) |
| `ATCMotor_O` | `OUT17` | Spins the tool carousel |
| `ATCUnlocked_O` | `OUT18` | Releases the carousel lock |
| `ATC_Pos1_I`..`ATC_Pos5_I` | `INP32`..`INP28` | 5 carousel position switches |
| `ATC_Z_ClearedToolChanger_I` | `INP26` | Spindle/Z has entered the tool changer |
| `ATC_Z_Zero_Release_I` | `INP27` | Z axis has cleared the tool ring (parked) |
| `ATCManualUnlock_I` | `INP24` | Manual unlock button on the front of the machine |
| `ZeroSpeed_I` | `INP12` | Spindle at zero RPM |
| `StopSpinBeforeATC_T` | timer | Spindle-stop timeout guard |

### Tool change flow

1. **`mfunc6.mac` (M6):** stops the spindle (`S0 M5`) and coolant (`M9`), moves Z to the
   tool-change position with `G53 Z0`, sends the requested tool number with `M107`, then
   sets `M6_SV` via `M94 /8` to start the change and resets it with `M95 /8` once `ATCStage`
   clears. Like every macro here it skips in graph/search mode
   (`IF #4201 || #4202 THEN GOTO 1000`) and ends at `N1000`.

2. **`MainStage` kickoff & safety:** on `M6_SV` it latches the target
   (`ChangeToTool_W = SV_TOOL_NUMBER`) and `SET ATCStage`. Before the carousel may move it
   enforces:
   - **Spindle stopped** — if the spindle isn't at `ZeroSpeed_I` it drops
     `SpindleEnableOut_O` and starts `StopSpinBeforeATC_T`; if the timer expires before zero
     speed it raises `SPINDLE_FAULT_MSG_C` and aborts (`RST ATCStage`).
   - **Z parked** — `ATCStage` also checks `ATC_Z_Zero_Release_I`; if Z hasn't cleared the
     tool ring it raises `ATC_Spindle_Not_Parked_C` and aborts.

3. **`ATCStage` indexing:** once safe and `ChangeToTool_W > 0`, it unlocks and spins the
   carousel (`SET ATCUnlocked_O, SET ATCMotor_O`) and decodes the position switches as each
   tool passes.

### Carousel position encoding

Tool IDs are encoded across the 5 position switches as **base-16 written in decimal**. While
the carousel turns, the PLC accumulates `CarouselToolID_W` from whichever switches are active,
then resets to look for the next tool when all switches read 0:

```
ATC_Pos1_I -> +1
ATC_Pos2_I -> +2
ATC_Pos3_I -> +4
ATC_Pos4_I -> +8
ATC_Pos5_I -> +10   ; note: 10, NOT 16 — base-16 encoded as decimal
```

| Tool | Switches (1-2-3-4-5) | Tool | Switches | Tool | Switches |
| --- | --- | --- | --- | --- | --- |
| T1 | `* . . . .` | T5 | `* . * . .` | T9  | `* . . * .` |
| T2 | `. * . . .` | T6 | `. * * . .` | T10 | `. . . . *` |
| T3 | `* * . . .` | T7 | `* * * . .` | T11 | `* . . . *` |
| T4 | `. . * . .` | T8 | `. . . * .` | T12 | `. * . . *` |

When `CarouselToolID_W == ChangeToTool_W`, the PLC stops and relocks the carousel
(`RST ATCMotor_O, RST ATCUnlocked_O`), clears the request (`RST M6_SV`), and ends the change
(`RST ATCStage`).

### Manual unlock

Outside of a tool change, the front-panel `ATCManualUnlock_I` button releases the carousel
lock (`SET ATCUnlocked_O`) provided Z is parked (`ATC_Z_Zero_Release_I`), and posts
`ATC_Lock_Released_C` / `ATC_Lock_Not_Released_C` status messages.

### ⚠️ No carousel timeout

`ATCStage` has no timeout protecting the carousel itself (see the `;TODO` in the source). If
the requested tool is never matched — e.g. an off-by-one in the position decode or a failed
switch — `ATCMotor_O` keeps spinning indefinitely. Take care when editing the match/exit
conditions.
