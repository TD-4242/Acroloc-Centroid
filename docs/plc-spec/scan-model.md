# PLC scan/execution model

One-line purpose: how `Centroid-Acroloc-ALLIN1DC.src` actually executes each scan — stage
sweep order, snapshot timing, timer semantics, and write-conflict resolution — so every
other file in `docs/plc-spec/` can cite behavior instead of re-deriving it.

Line numbers as of commit 41f3fd6

## Stage sweep

The program is a flat list of `STG`-numbered stages, defined once (e.g. `MainStage IS STG4`,
(src:1196); `GearShiftStage IS STG17 ; Acroloc RPM gear-shift state
machine` (src:1208)) and then swept top to bottom, once per scan,
in file order. A stage's rungs execute only while that stage is currently SET; `SET
Stage`/`RST Stage` do not take effect retroactively within the scan that issues them — they
change whether the stage's rungs run starting the *next* time the sweep reaches that stage.

Because the sweep is in file order, a stage that appears earlier in the file can `SET` a
stage that appears later, and that later stage's rungs will run **in that same scan**
(the sweep hasn't passed it yet). The reverse is not true: a stage later in the file that
sets an earlier one only takes effect on the *next* scan.

Example: `MainStage` (STG4) is the kickoff rung for the gear-shift sequence. It loads and
arms `GearCoast_T` and then `SET GearShiftStage` (src:2307), inside the block commented
"so a shift always completes ... the coast timer GearCoast_T is loaded and armed by the
kickoff rung in MainStage, in the same scan this stage is SET" (src:2995).
`GearShiftStage` itself is `STG17`
(src:1208), which is swept after `MainStage`'s `STG4` in the same
pass, so `GearShiftStage`'s Step A rung (src:2999) runs in that
very scan, not the next one.

## Snapshot semantics

`INP` inputs and timer boolean states are frozen at the start of the scan (or at least before
stage logic reads them) — a rung that arms a timer this scan reads that same timer's bare
(expired) state as false this scan, because "true" only becomes visible once the timer
reaches its preset on a later scan. This is called out directly in the gear-shift comment:
"A bare timer is true once it reaches its set point, so `GearCoast_T` below fires when the
coast dwell has fully elapsed (NOT == 0, which would mean 'just armed')"
(src:3004-3005, timer read at
(src:3007)). In other words, `SET GearCoast_T` in
`MainStage` (src:2306) does not make `GearCoast_T` read true in
that scan or the next — only once the preset interval has actually elapsed.

## Timers

Timers count up from zero to a preset. The idiom is: assign the preset with `T = value`,
then `SET T` to arm/start it counting; while counting, the bare timer name (`T` used as a
boolean) reads false, and it reads true once the elapsed count reaches the preset; `RST T`
zeroes the elapsed count and stops it.

Stock example — `LubeM_T IS T13` (src:1180):
- (src:1422): `IF !(SV_PROGRAM_RUNNING || SV_MDI_MODE) THEN
  LubeM_T = LubeM_W, SET LubeM_T` — loads the preset from `LubeM_W` and arms it.
- (src:1423): `IF LubeM_T || !EStopOk_M THEN RST Lube_O` — reads
  the bare timer (true at expiry) to gate an output.
- (src:1421): `RST LubeM_T` — zeroes it when the program is running.

Acroloc example — `GearCoast_T IS T25 ; Acroloc gear-shift coast dwell (neutral) before
engage` (src:1189):
- (src:2301, 2304): `GearCoast_T = 1500` (default) or `GearCoast_T =
  SV_MACHINE_PARAMETER_943` (configured) loads the preset.
- (src:2306): `SET GearCoast_T` arms it, in `MainStage`, the same
  scan `GearShiftStage` is set.
- (src:3007): `IF GearShiftStage && GearCoast_T && (DesiredRange_W
  == 1) THEN ...` reads the bare (expired) timer to gate clutch engagement.
- (src:3015): `RST GearCoast_T` zeroes it once the shift finishes.

## Last write wins

There is no `ELSE` construct in this language. When multiple rungs in the same scan write the
same bit, the last rung in file order to execute determines its final value for the scan —
earlier writes to the same target are simply overwritten, not combined.

Example — `Spindle_Low_gear_O` and `Spindle_High_gear_O` in `GearShiftStage`:
- (src:2999): Step A unconditionally does `RST
  Spindle_Low_gear_O, RST Spindle_High_gear_O` every scan the stage is set (open the clutches
  to neutral).
- (src:3008): Step B conditionally does `SET Spindle_Low_gear_O,
  RST Spindle_High_gear_O` once `GearCoast_T` has expired and `DesiredRange_W == 1`.

Both rungs write `Spindle_Low_gear_O` in the same scan when the coast timer expires; because
Step B's rung runs after Step A's in file order, its `SET` is the value that sticks for that
scan — Step A's earlier `RST` is overwritten, not evaluated as a fallback "else" branch.

## Naming conventions

Suffix encodes the underlying resource type, bound with `Name IS Resource`:

- `_I` = input bit (`INP`) — `ZeroSpeed_I IS INP12` (src:219).
- `_O` = output bit (`OUT`) — `ATCMotor_O IS OUT17 ; Acroloc spin tool carousel`
  (src:382).
- `_M` = memory bit (`MEM`) — `SafetySwitch_M IS MEM29`
  (src:486).
- `_W` = 32-bit word (`W`) — `ChangeToTool_W IS W72 ; Acroloc`
  (src:1094).
- `_FW` = floating-point word — `RPMPerBit_FW IS FW2`
  (src:1102).
- `_T` = timer (`T`) — `GearCoast_T IS T25 ; Acroloc gear-shift coast dwell (neutral) before
  engage` (src:1189).
- `_SV` = CNC system variable — `DoCycleCancel_SV IS SV_PLC_FUNCTION_1`
  (src:770).
- `_C` = integer constant, message constants encode as `value = msgNumber + 256*msgFile` —
  `ATC_Lock_Released_C IS 45546;(2+256*174) Tool Carousel locked.`
  (src:202).

Stages use no suffix and are declared `IS STGn` — e.g. `MainStage IS STG4`
(src:1196).
