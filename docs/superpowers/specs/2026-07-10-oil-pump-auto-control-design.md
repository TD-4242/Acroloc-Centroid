# Oil Pump (OUT2) Auto-Control Design

- Date: 2026-07-10
- Status: approved design, pending implementation
- Scope: `Centroid-Acroloc-ALLIN1DC.src` (PLC), plus doc sync
- Related: [[spindle-changer-feedhold-design]] (its safety feed-hold also gates this pump; see Interactions)

## Goal

Drive the machine's oil pump on `Lube_O` (OUT2) so it runs **only while a G-code
program is actively executing** and stops the instant the job stops for any reason
(feed-hold, cycle-cancel/reset, E-stop, program end). Replace Centroid's stock
metered way-lube logic, which does not match this behavior.

## Background

On this machine OUT2 (`Lube_O`) is wired to the oil pump. The pump is a
**self-metering, on/off unit**: whenever it has power it runs and delivers oil on
its own internal interval; it has no external metering control. So the PLC's only
job is to gate its power.

Stock CNC12 drives OUT2 with one of two selectable metering schemes, chosen at boot
by Machine Parameter 179 (format `MMMSS`):

- **Method 1** (`SS == 0`, `LubeUsePumpTimersStage`, src 1398-1444): ON while
  `SV_PROGRAM_RUNNING || SV_MDI_MODE`, then keeps running for `MMM` minutes after the
  job stops (an anti-dry-run dwell), off on E-stop.
- **Method 2** (`SS != 0`, `LubeUsePLCTimersStage`, src 1446-1474): pulses the pump
  ON for `SS` seconds every `MMM` minutes of accumulated run time; off most of the time.

Neither method matches the requirement:

| Behavior | Stock M1 | Stock M2 | Required |
|---|---|---|---|
| While a program runs | ON (+ dwell) | brief pulses | **ON continuously** |
| In MDI | ON | accumulates | **OFF** |
| On feed-hold | **stays ON** | accumulates | **OFF** |
| After job stops | runs `MMM` more min | off | **OFF immediately** |
| On E-stop | off | off | **OFF** |
| Metering / P179 | required | required | **not used** |

This machine is currently on the self-metering Method-1 style pump, so the visible
change is: program-only (not MDI), no post-stop dwell, and a new feed-hold cutoff.

## Requirement

The oil pump (OUT2) is ON if and only if a loaded program is actively executing and
not paused. It is OFF in MDI, at idle, during feed-hold, and after any stop.

## Design

### Signal choice

`SV_PROGRAM_RUNNING` is **not** the right trigger: per the CNC12 system-variable
reference it is `1` in MDI mode too, so it cannot express "program only." The correct
combination is:

| Machine state | `SV_MDI_MODE` | `SV_JOB_IN_PROGRESS` | `FeedHoldLED_O` | Pump |
|---|---|---|---|---|
| Idle at main screen | 0 | 0 | 0 | OFF |
| At MDI prompt (idle) | 1 | 0 | 0 | OFF |
| Executing MDI command | 1 | 1 | 0 | OFF |
| **Running a program** | 0 | 1 | 0 | **ON** |
| Program held (feed-hold) | 0 | 1 | 1 | OFF |

- `SV_JOB_IN_PROGRESS` is set while running a job or an MDI command, but not while idle
  at the MDI prompt.
- `!SV_MDI_MODE` subtracts MDI, leaving job-only.
- `!FeedHoldLED_O` is the cutoff on pause: a held job stays "in progress," so this term
  is what actually stops the pump on feed-hold. `FeedHoldLED_O` is the machine's
  feed-hold state (set on hold, cleared on cycle-start).
- Cycle-cancel/reset, program end, and E-stop all end the job, dropping
  `SV_JOB_IN_PROGRESS`.

### Control rung

A single **combinational coil** in `MainStage`, placed with the existing lube-fault
rungs (src ~2890) so all lube logic lives together. Coil form re-evaluates every scan,
so the output cannot latch on -- it drops the same scan any term goes false, which is
exactly the "off on any stop" requirement. This matches house style (`Flood_O`,
`Mist_O` are driven as coils).

```
; Acroloc oil pump: power OUT2 only while a program is actively executing.
; Off in MDI, at idle, on feed-hold, and on any stop (cycle-cancel/reset/E-stop/
; program end). Coil form = no latch, drops the scan any term clears.
IF SV_JOB_IN_PROGRESS && !SV_MDI_MODE && !FeedHoldLED_O && EStopOk_M THEN (Lube_O)
```

`&& EStopOk_M` is redundant with the job ending on E-stop but is included to match the
stock code's explicit E-stop cutoff (`!EStopOk_M THEN RST Lube_O`) and as cheap
insurance for a pump output. The rung is placed after `EStopOk_M` is computed in
`MainStage` so it reads the current-scan value.

### Removals (full clean removal of the stock metering)

All of the following are used only by the metering machinery (verified by full-source
symbol search) and are deleted:

- Boot rungs in `LoadParametersStage`: P179 load (src 1315-1317), method-select
  (src 1330-1331).
- Stage bodies and their header comment blocks: `LubeUsePumpTimersStage`
  (src 1398-1444) and `LubeUsePLCTimersStage` (src 1446-1474).
- Stage definitions: `LubeUsePumpTimersStage IS STG13`, `LubeUsePLCTimersStage IS STG14`
  (src 1226-1227).
- Dead resource definitions: `LubeM_T` (T13), `LubeS_T` (T14), `Lube_W` (W61),
  `LubeM_W` (W62), `LubeS_W` (W63), `LubeAccumTime_W` (W1), `StopRunningPD_PD` (PD35).

**Machine Parameter 179 is retired** -- it no longer has any effect in this PLC.

### Preserved (untouched)

- `Lube_O` (OUT2) definition.
- The lube-**fault** chain, which never drove OUT2: `LubeOk_I` (INP9) ->
  `LubeFault_M` (MEM49) -> `LUBE_FAULT_MSG_C` / `LUBE_WARNING_MSG_C` and its
  inclusion in fault aggregation (`SV_STOP`). Oil pressure/level protection is
  unchanged.

## Interactions

- **Spindle-in-changer feed-hold interlock** ([[spindle-changer-feedhold-design]]):
  when that interlock asserts its safety feed-hold it sets `FeedHoldLED_O`, so the oil
  pump turns OFF during the hold and resumes when the interlock releases. This is
  correct and desirable (the job is paused).
- **Tool change (M6)**: `mfunc6.mac` runs as part of the job, so `SV_JOB_IN_PROGRESS`
  stays set and `SV_MDI_MODE` stays clear -- the pump stays ON through a normal tool
  change (unless a feed-hold is asserted). Acceptable.
- **Jogging / MPG**: not a job, pump stays OFF. This is intended (program-only per the
  owner's requirement).

## Recorded tradeoffs

- **Short-job under-lube.** Because the pump meters on its own interval, cutting power
  at every stop means a program that ends before the pump reaches its interval may not
  deliver an oil shot that run. This is exactly the scenario the stock Method-1 dwell
  (comments at src 1419-1440) existed to mitigate. Dropped intentionally in favor of
  strict "off whenever the job stops." Accepted by the machine owner.
- **P179 retired.** Any value previously set in Parameter 179 becomes inert. Noted so a
  future reader is not surprised that the parameter has no effect.

## Testing (on-machine)

No automated tests exist; validate on the machine after compiling/loading in CNC12.
Watch OUT2 (`Lube_O`) in PLC Diagnostics (Alt-I).

1. Idle at main screen: OUT2 = 0.
2. Enter MDI, sit at prompt: OUT2 = 0. Run an MDI move (e.g. `G53 Z-1`): OUT2 stays 0
   during the MDI move.
3. Run a short program: OUT2 = 1 for the whole run, returns to 0 at program end.
4. Mid-program feed-hold: OUT2 -> 0 on hold; cycle-start resumes -> OUT2 = 1.
5. Mid-program cycle-cancel/reset: OUT2 -> 0 and stays 0.
6. Mid-program E-stop: OUT2 -> 0.
7. Manual jog / MPG: OUT2 = 0.
8. Confirm the lube-fault path still works: with a program running and `LubeOk_I`
   (INP9) open, the `LUBE WARNING` message still appears (fault monitoring intact).

## Docs to update (per CLAUDE.md convention)

- `docs/plc-spec/` sections covering the boot/param load and MainStage lube logic
  (and their pinned commit hashes): the `LoadParametersStage` P179 note, the lube
  drive in `main-stage.md`, and the removed resource defs in `definitions.md`.
- Any lube mention in the `acroloc-s10` skill / `README.md` if present.

## Open questions

None.
