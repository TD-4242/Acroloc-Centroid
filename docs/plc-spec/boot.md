# Boot stages: watchdog, init, parameter load

One-line purpose: what happens before the machine is ready to run — PLC executor/software
fault handling, the one-scan power-up latch, and the machine-parameter load handshake — in
`WatchDogStage` (STG1), `InitialStage` (STG2), and `LoadParametersStage` (STG10).

Line numbers as of commit 41f3fd6

Stage sweep order, timer semantics, and the same-scan-vs-next-scan `SET`/`RST` rules used
below are defined in [scan-model.md](scan-model.md); resource name -> line lookups are in
[definitions.md](definitions.md). This file does not repeat either.

## Stage definitions

`WatchDogStage IS STG1` (src:1193), `InitialStage IS STG2` (src:1194),
`LoadParametersStage IS STG10` (src:1202). All three are stock Centroid ALLIN1DC stages —
none of the rungs in `WatchDogStage` or `LoadParametersStage` are tagged `; Acroloc`. The
only Acroloc-specific content in this file is the power-up gear-state init inside
`InitialStage` (src:1276-1280), called out below.

`WatchDogStage` is always SET (never explicitly RST anywhere in the program) — it is the
program's entry stage and runs every scan, every scan, for the life of the PLC task.

## WatchDogStage (src:1228-1252)

Purpose: fault-status aggregation for two failure classes CNC12 itself reports to the PLC,
plus the power-up detector that kicks off `InitialStage`.

1. **PLC executor fault** (src:1233-1237): if `SV_PLC_FAULT_STATUS != 0`, latch the fault
   code/address into `PLC_Fault_W`/`PLCFaultAddr_W`, post the executor-fault message, `SET
   PLCExecutorFault_M`, `RST MessageStage` (drop whatever message was showing so the fault
   message takes over), and `SET SV_STOP`. Per the file header comment (src:1231-1232), a
   PLC executor fault can only be cleared by rebooting the MPU11 — there is no in-program
   reset rung for `PLCExecutorFault_M`.
2. **Software-not-ready** (src:1240-1243): if the PC-side CNC12 software isn't reporting
   ready (`!SV_PC_SOFTWARE_READY`) and there's no executor fault already in play, `SET
   SoftwareNotReady_M`, `SET SV_STOP`, and load the software-exit message text into
   `FaultMsg_W`. This is the "PC software isn't running/connected" case, distinct from a PLC
   executor crash.
3. **Message-cleared bookkeeping** (src:1245): once `FaultMsg_W` holds the specific sentinel
   value `9985` and `SV_STOP` is no longer asserted, `FaultMsg_W` is reset to the generic
   "message cleared" constant — purpose inferred: this looks like tidy-up so a stale
   fault-message word doesn't keep showing 9985 after the stop condition that produced it
   has cleared, but the significance of literal `9985` specifically (vs. a named constant)
   is not derivable from source here.
4. **Software-ready clear** (src:1247-1248): once both `SV_PC_SOFTWARE_READY` is true and
   there's no executor fault, `RST SoftwareNotReady_M` — the mirror of rung 2.
5. **Power-up detector** (src:1250-1252): `IF !True_M THEN SET InitialStage`. `True_M` is a
   memory bit that is only ever `SET` inside `InitialStage` itself (src:1257) and is never
   `RST` anywhere in the file, so it reads false exactly once: the very first scan after the
   MPU11 boots (or the PLC program is (re)loaded), before any stage has run. That single
   false scan is what makes `InitialStage` a "run once at power-up" stage — see next
   section.

## InitialStage (src:1255-1281)

Purpose: the one-time power-up latch — arms every other stage that must start SET, zeroes
fault/message state, loads a handful of timer presets, and (Acroloc-specific) forces the
spindle gear state to a known value before anything else in the program can act on it.

The entire stage is a single rung gated by `IF 1==1` (src:1257) — i.e. it always fires while
the stage is SET, with no conditional logic; the guarding is done entirely by
`WatchDogStage`'s `SET InitialStage` / this rung's own `RST InitialStage` at the end
(src:1281), which together bound it to exactly one scan.

Because `WatchDogStage` (STG1) sits before `InitialStage` (STG2) in file order, and
`WatchDogStage`'s `SET InitialStage` rung runs before the sweep reaches STG2, `InitialStage`
executes **in the same scan** it is set — see [scan-model.md](scan-model.md) for why same-file-order
`SET` takes effect immediately rather than on the next scan.

Rung-by-rung (src:1257-1281), grouped by effect:

- `SET True_M` (src:1257) — flips the power-up detector so `WatchDogStage` will not re-fire
  `SET InitialStage` on subsequent scans. This is the guard against `InitialStage` running
  more than once per power-up.
- `SET OnAtPowerUp_M` (src:1258) — purpose inferred: a latch other stages can test to know
  "we are still in the power-up scan/window"; no consumer of this bit is visible in the
  boot-stage bodies themselves.
- Stage arm-up: `SET AxesEnableStage`, `SET MainStage`, `SET JogPanelStage`, `SET
  LoadParametersStage` (src:1259, 1260, 1261, 1262), `SET SafetySwitchInterruptStage`
  (src:1263), `SET MessageStage` (src:1271) — these are the stages that must be running from
  scan 1 onward; none of them self-arm, so if `InitialStage` didn't set them the program
  would do nothing.
- `SET PLCBus_Oe_M` (src:1264) — purpose inferred: enables the PLC bus output driver
  (output-enable bit); not otherwise explained in this block.
- Fault/comm-flag clear: `RST DriveComFltIn_M`, `RST DriveComFltOut_M`, `RST PLCFault_M`
  (src:1265-1267) — clears drive-communication and generic PLC fault latches left over from
  a prior session so boot starts clean.
- `CycloneStatus_T = 300` (src:1268) — loads (but per [scan-model.md](scan-model.md) naming,
  does not by itself arm) the Cyclone-drive-status timer preset to 300 ms.
- `FaultMsg_W = MSG_CLEARED_MSG_C` (src:1269), `RST BadMsgStage` (src:1270) — starts the
  message system in the "no fault" state.
- Timer preset loads: `Initialize_T = 1000, SET Initialize_T` (src:1272 — this one is both
  loaded *and* explicitly armed, unlike the others here), `ErrorFlag_T = 1000` (src:1273),
  `MsgClear_T = 1000` (src:1274), `StopSpinBeforATC_T = 1000` (src:1275) — four timers preset
  to 1000 ms; only `Initialize_T` is armed (`SET`) in this same rung, so it is the one
  timer guaranteed to actually be running immediately after power-up. `StopSpinBeforATC_T`
  is the Acroloc ATC spindle-stopped-before-carousel-motion timer described in the
  repo-level ATC flow — see [atc.md](atc.md) for where it is armed and read.
- **Acroloc power-up gear defaults** (src:1276-1280), all tagged `; Acroloc`:
  `SET Spindle_Low_gear_O`, `SET Spindle_High_gear_O` (both on = **neutral**),
  `EngagedRange_W = 0` (gear unknown), `DesiredRange_W = 0`, `SpindleRange_W = 1`. See
  [Power-up defaults](#power-up-defaults) below.
- `RST InitialStage` (src:1281) — the last clause of the rung; ends the stage so it does not
  run again next scan (`True_M` being set is what stops `WatchDogStage` from re-arming it,
  but this `RST` is what actually stops `InitialStage`'s own body from running a second
  time even if something else re-armed it).

## Power-up defaults

Acroloc gear-shift state is force-initialized to **neutral** (both clutches on) with the gear
**unknown** on every power-up, inside `InitialStage`'s single rung (src:1276-1280):

```
SET Spindle_Low_gear_O,   ; Acroloc power-up = NEUTRAL (both clutches on)  (src:1276)
SET Spindle_High_gear_O,  ; Acroloc                                         (src:1277)
EngagedRange_W = 0,       ; Acroloc gear unknown -> first spin-up engages   (src:1278)
DesiredRange_W = 0,       ; Acroloc                                         (src:1279)
SpindleRange_W = 1,       ; Acroloc safe default ratio until first engage   (src:1280)
```

This runs unconditionally, once, on the first scan after MPU11 boot or PLC (re)load (see
[InitialStage](#initialstage-src1255-1281) above). The effect: both clutch outputs are driven
on (**neutral / freewheel** — the safe startup state, since both-off is a mechanical lockup
and committing a single gear before the spindle even runs is undesirable), and `EngagedRange_W
= 0` marks the gear **unknown**. Because the shift kickoff (in `MainStage`) is gated on the
spindle being enabled and on `DesiredRange_W != EngagedRange_W`, the machine **holds neutral
while the spindle is stopped** and engages the correct gear on the first spin-up: the RPM
decision sets `DesiredRange_W` to 1 or 4, which differs from the unknown `0`, so a shift
fires. `SpindleRange_W = 1` is only a safe default for the ratio/DAC math while neutral (the
spindle is off then); `GearShiftStage` retargets it during the shift.

## LoadParametersStage (src:1284-1376)

Purpose: on every scan (gated by `True_M`, which is permanently true after the first scan —
see `WatchDogStage` above — so in practice this runs every scan once `InitialStage` has
fired), re-read a set of CNC12 machine parameters (`SV_MACHINE_PARAMETER_n`) and derive the
PLC-side words/memory bits/stage selections that depend on them. This is not a one-shot
load — it's a live handshake: because it re-reads every scan, a parameter changed in CNC12
setup takes effect within one scan without a PLC reload. Nothing in this stage is
`; Acroloc`-tagged.

Grouped by function:

- **Lube pump timing** (src:1294-1296): `Lube_W = SV_MACHINE_PARAMETER_179`, then decoded
  per the file's own comment block (src:1286-1291) as `MMMSS` (minutes*100 + seconds) into
  `LubeM_W` (minutes -> ms) and `LubeS_W` (seconds -> ms). Two lube-control methods are then
  selected by whether `LubeS_W == 0` (src:1309-1310): `LubeUsePumpTimersStage` for pumps with
  their own internal timer, `LubeUsePLCTimersStage` for pumps the PLC must time itself.
- **MPG/handwheel setup** (src:1299-1306): parameter 218 selects wired MPG
  (`MPGStage`) vs. wireless MPG (`WirelessMpgStage`) (src:1299-1300). Parameter 348 (or 351/354)
  sets `MPG_M`/`HandWheel_M` presence flags (src:1301-1304). Parameter 19's bit 1 is tested
  into `MpgX100LockOut_M` via `BITTST` (src:1305-1306).
- **Jogging option parameters** (src:1312-1314, 1348-1354, 1364-1371): parameters 146
  (feed-hold threshold), 148 (misc jogging options), 170 (keyboard jogging enable), and 1
  (jog key orientation) are loaded into `P146Value_W`/`P148Value_W`/`P170Value_W`/
  `JogKeyCfg_W` and decoded bit-by-bit with `BITTST` into `DisableKbInput_M`,
  `AllowKbInput_M`, `JogOverOnly_M`, `KbOverOnly_M`, `InvertXJogKeys_M`, `SwapAxes_M`.
  `DisableKbInput_M` overrides `AllowKbInput_M` (src:1353) and `JogOverOnly_M` overrides
  `KbOverOnly_M` (src:1354) when both would otherwise be set. The invert/swap combination
  selects exactly one of the four `JogKeysNormalStage` / `JogKeysInvert2Stage` /
  `JogKeysSwappedStage` / `JogKeysSwapAndInvert2Stage` stages (src:1368-1371).
- **I/O force/invert override** (src:1316-1346): a single rung gated on `True_M` sets
  `SV_ENABLE_IO_OVERRIDE` and copies fifteen `SV_MACHINE_PARAMETER_9xx` values into the
  corresponding `SV_INVERT_*`/`SV_FORCE_ON_*`/`SV_FORCE_OFF_*` system variables, covering
  input inversion, and forced-on/forced-off overrides for inputs, outputs, and memory bits
  across all four 16-bit banks. This is a stock CNC12 debug/commissioning facility, not
  Acroloc-specific.
- **Load meter enable** (src:1357-1358): parameter 57 nonzero enables `LoadMeterStage`.
- **Jog panel required flag** (src:1361): mirrors `SV_JOG_PANEL_REQUIRED` into
  `JogPanelRequired_M`.
- **Probe protection** (src:1373-1375): parameter 153 nonzero sets
  `ProbeProtectionEnable_M`.

None of these parameter-driven selections touch the Acroloc gear-shift or ATC state —
`LoadParametersStage` has no `; Acroloc` markers and its stage-selection rungs only target
lube, MPG, jog-key, and load-meter stages.
