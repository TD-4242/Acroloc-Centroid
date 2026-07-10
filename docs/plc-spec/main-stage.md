# MainStage: fault, spindle, coolant, gear-decision, and ATC-kickoff reference

One-line purpose: rung-by-rung reference for `MainStage` (STG4) — E-stop/reset, probe
protection, USB MPG, keyboard-event dispatch, fault aggregation, M-code housekeeping, the
Acroloc ATC kickoff — plus the spindle/coolant/gear-decision logic that this doc set
(`definitions.md`, `scan-model.md`) already treats as MainStage's functional territory even
though it is structurally banner-scoped under `JogPanelStage`. See the
[Stage scope note](#stage-scope-note) below before citing line ranges elsewhere.

Line numbers as of commit 41f3fd6

Stage sweep order, timer semantics, and same-scan-vs-next-scan `SET`/`RST` rules are defined
in [scan-model.md](scan-model.md); resource name -> line lookups are in
[definitions.md](definitions.md); boot-time initialization (including the power-up gear
defaults) is in [boot.md](boot.md). None of that is repeated here.

## Stage scope note

`MainStage IS STG4` (src:1196). The literal `MainStage` banner
(src:2641) opens a block that runs through src:2933,
immediately followed by the `ATCStage` (src:2935) and `GearShiftStage`
(src:2985) banners. Per the stage-header convention (bare stage
name between `;===` rules), everything from src:2642 to
src:2933 is structurally `MainStage`'s body.

**However**, the spindle enable/direction, override-knob, coolant, gear-decision, and DAC-ratio
rungs that this file's brief and `definitions.md` attribute to "MainStage" (e.g. `ZeroSpeed_I`
at src:219 is tagged "used by main-stage.md, gear-shift.md") are
physically located at src:2086-2406, inside the
`JogPanelStage` banner block (src:1772-2406) — **not** under the
`MainStage` banner. `scan-model.md`'s own worked example calls src:2307
(`SET GearShiftStage`) "the kickoff rung in MainStage," which is the same attribution used
here. This is not a contradiction in practice: both `MainStage` and `JogPanelStage` are `SET`
once in `InitialStage` (src:1259-1260) and never `RST` anywhere in
the file, so both run every scan for the life of the program — functionally indistinguishable
from a single always-on "main" body. This doc documents the spindle/coolant/gear/fault content
by topic, in two parts below, and calls out the true banner each part lives under. Treat the
"MainStage" framing here as the established documentation convention for this repo, not as a
claim about the literal banner boundary.

## Part 1 — content under the `MainStage` banner (src:2642-2933)

### EStop and reset section (src:2650-2668)

Purpose: debounce the VCP reset button and drive the reset/E-stop memory bits that gate the
rest of the fault section below.

- (src:2651-2653): `SetResetPD_PD` one-shots on `SkinResetKey_M_SV` while `EStopOk_I`;
  `EStopOkPD_PD` one-shots on `EStopOk_I` itself. `ResetSet_M` is a coil driven by
  `SetResetPD_PD XOR ResetSet_M`, gated by `!EStopOkPD_PD` — purpose inferred: this looks like
  a level/edge combination meant to latch "operator pressed reset" only when the E-stop
  circuit wasn't the thing that just changed state, but the exact intent of the XOR-against-
  self idiom is not fully derivable from source alone.
- (src:2656): `EStopOk_M` (memory-bit mirror of the E-stop-ok condition) is a coil: true unless
  `!EStopOk_I || ResetSet_M`.
- (src:2658): while `!EStopOk_M`, drive `SkinResetSet_O` and `SkinResetSet_M_SV` (VCP reset
  indicator outputs).
- (src:2661-2668): message plumbing — `MessageTimer_T` preset to 200 ms (src:2661); on
  `ResetSet_M && EStopOk_I` post `RESET_DETECTED_C` and arm the timer, then clear the timer
  once it expires (src:2662-2663); `ResetArmed_M` latches while reset+ok holds
  (src:2665); once `ResetSet_M` drops while `ResetArmed_M` is still latched, post
  `RESET_CLEARED_C` and, once the timer expires, drop `MessageTimer_T` and
  `ResetArmed_M` (src:2667-2668).

### Probe protection while jogging (src:2670-2756)

Purpose (stated in the source's own header, src:2673-2675): if the mechanical
probe trips while a jog move is active, stop that jog direction and post an error; the
disable persists until the probe clears and no jog key is still held.

- (src:2676): `ProbePD_PD` one-shots on `MechanicalProbe_I && ProbeProtectionEnable_M`.
- (src:2678-2708): on `ProbePD_PD`, for each of the six jog directions currently active
  (`DoAx1PlusJog_SV` .. `DoAx4MinusJog_SV`), latch a matching set of
  `Ax*JogDisabled_M` bits — the disable set for a given tripped direction always includes the
  two X/Y cross-axis directions plus both 4th-axis directions, mirroring the physical
  clearance geometry (purpose inferred: the specific per-direction fan-out pattern reads as
  "block anything that could still be closing on the probe," not spelled out further in
  source). `Ax3MinusJogDisabled_M` is unconditionally set on any `ProbePD_PD`
  (src:2708).
- (src:2711-2718): if `ProbePD_PD` fires while any axis jog request is active and
  `JogProbeFault_M` isn't already latched, one-shot `JogProbeFaultPD_PD`, which then
  `SET JogProbeFault_M`, `SET ErrorFlag_M`, and posts `PROBE_JOG_TRIP_MSG_C`.
- (src:2720-2736): `JogKeyPressed_M` is a coil that goes true while any jog-key/one-shot
  input across all configured jog sources is active (src:2722-2733) — gathered so the
  clear-fault rung (src:2736-2743) can require the operator to have fully released every
  jog key before clearing `JogProbeFault_M` and all the `Ax*JogDisabled_M` latches, once
  `!MechanicalProbe_I`. Gotcha: this rung is the only place that clears the six disable bits
  set at src:2678-2708 — a jog-key stuck "on" (stale I/O, held key) blocks recovery
  indefinitely.
- (src:2745-2751): commented-out logic (src:2747-2750) would have saved/restored the
  fast/slow jog mode across a probe trip while no program is running; only the live
  replacement remains active — `IF MechanicalProbe_I && !SV_PROGRAM_RUNNING &&
  ProbeProtectionEnable_M THEN SET FastSlowLED_O` (src:2751) forces slow-jog mode
  whenever the probe is tripped outside a running program, unconditionally (no restore path
  once probe clears — `FastSlowLED_O` stays SET until something else resets it).

### USB MPG section (src:2757-2814)

Purpose: decode the USB MPG's wheel-scale selector, per-axis jog buttons, macro-request keys,
and axis-zero button into PLC bits/words. Not `; Acroloc`-tagged; stock USB-pendant support.

- (src:2761): `WTB SV_USB_MPG_BUTTON_STATE MpgResetKey_M 13` — word-to-bit decode of the MPG
  button-state word starting at bit `MpgResetKey_M`, width 13.
- (src:2762-2765): `SV_USB_MPG_SCALE_SELECT == 1000`/`10000` select
  `UsbMpgSpinWheelSelect_M` / `UsbMpgFeedWheelSelect_M` (mutually exclusive by construction,
  since the scale value can't equal both).
- (src:2769-2786): reset-then-set idiom (no `ELSE`, per `scan-model.md`) routes
  `UsbMpgJogPlus_M`/`UsbMpgJogMinus_M` to the correct per-axis bit
  (`UsbMpgAxis1JogPlus_M` .. `UsbMpgAxis4JogMinus_M`) based on `SV_USB_MPG_AXIS_SELECT`.
- (src:2788-2795): `MpgSetAxisZero_M` while a given axis is both active and selected fires
  that axis's `SetAxisNPart0_SV` (zero the WCS on that axis) for axes 1-8.
- (src:2797-2810): `SV_SYS_MACRO` request plumbing — one of four `MpgMacroN_M` bits sets
  `SV_SYS_MACRO = N` to ask CNC12 to run `MPGmacroN.mac`; when none of the four is pressed,
  `NoMacroKeyPressedTimer_T` is armed at 100 ms and, once expired, zeroes
  `SV_SYS_MACRO` back to 0 (src:2809-2810) — per the source comment
  (src:2797-2800), CNC12 will not re-run the same macro number twice in a row unless
  it sees a 0 in between, so this timer is what re-arms repeat macro calls.

### Worklight (src:2816-2819)

Purpose: toggle the work light from the Aux7 jog-panel key, forcing it on at power-up.
`Aux7PD_PD` one-shots on `DoAux7Key_SV` (src:2817); `Aux7LED_O` is a coil driven
by `Aux7PD_PD XOR Aux7LED_O`, forced true once at `OnAtPowerUp_M`
(src:2818); `WorkLightOut_O` mirrors `Aux7LED_O` (src:2819).

### Keyboard-event dispatch (src:2821-2839)

Purpose: route a handful of always-live keyboard inputs and decide when to hand off to
`KeyboardEventsStage` for the fuller key-combo handling.

- (src:2823): `Kb_Escape_SV` -> `KbCycleCancel_M`.
- (src:2826): spacebar feed-hold, gated on `AllowKbInput_M && SV_PROGRAM_RUNNING`.
- (src:2828): mirrors `SV_PC_VIRTUAL_JOGPANEL_ACTIVE` into `KbJpActive_M`.
- (src:2831-2834): any modifier key (Ctrl/Shift/Alt) or an active virtual jog panel
  `SET`s `KeyboardEventsStage` for this scan — per `scan-model.md`, since
  `KeyboardEventsStage` (src:1456) appears **earlier** in file order than
  `MainStage`, this `SET` only takes effect on the **next** scan, not the current one.
- (src:2836-2838): posts `KB_JOG_MSG_C` if a modifier + j/f/a/s combo is pressed while
  `!AllowKbInput_M` — purpose inferred: tells the operator keyboard jogging is disabled,
  rather than silently ignoring the combo.

### Fault aggregation (src:2840-2882)

Purpose: the central fault OR-gate — collapse every fault-class memory bit into `SV_STOP`, then
manage recovery once `EStopOk_M` returns.

- (src:2841-2842): `SET SV_STOP` if any of `!EStopOk_M`, `PLCFault_M`, `SV_STALL_ERROR`,
  `SpindleFault_M`, `LubeFault_M`, `AxisFault_M`, `ProbeFault_M`, `OtherFault_M`.
- (src:2844): `SV_STOP` -> `RST SV_MASTER_ENABLE` (kills the servo enable while stopped).
- (src:2846-2851): on `!EStopOk_M`, clear `SV_STALL_ERROR`, `LubeFault_M`, `SpindleFault_M`,
  `OtherFault_M`, `ProbeFault_M`, `ProbeMsgSent_M` — gotcha: this clears fault *latches* the
  moment E-stop is asserted, before the operator has done anything to actually fix the
  condition; the real gate against continuing to run is `SV_STOP` staying set via
  `!EStopOk_M` itself in the OR at src:2841, not these latches.
- (src:2853-2854): `Initialize_T && !LubeOk_I && !SV_PROGRAM_RUNNING` -> `SET LubeFault_M`,
  post `LUBE_FAULT_MSG_C`. Gated on `Initialize_T` (armed once at boot per
  [boot.md](boot.md)) so this doesn't fire during the lube system's own startup window.
- (src:2856): `!LubeOk_I && SV_PROGRAM_RUNNING` posts a lube *warning* (not a fault) —
  running with low lube is allowed but flagged.
- (src:2858-2860): `Initialize_T && !SpindleInverterOk_I` -> `SET SpindleFault_M`, post
  `SPINDLE_FAULT_MSG_C`; separately, `!EStopOk_M && !SpindleInverterOk_I` drives
  `InverterResetOut_O` — purpose inferred: pulses a reset line to the spindle inverter drive
  while E-stopped and the inverter isn't reporting ok.
- (src:2863-2869): debug echoes — `SV_MASTER_ENABLE` -> `MasterEnable_M`;
  `SV_STALL_ERROR` -> `Stall_M` plus captures `StallReason_W`/`StallAxis_W` from the matching
  `SV_STALL_*` system variables; `SV_STOP` -> `Stop_M`; `!SV_STOP` -> `NoFaultOut_O` (external
  "all clear" output).
- (src:2872-2875): `RST SV_STOP` once `EStopOk_M` is true **and** none of `PLCFault_M`,
  `SV_STALL_ERROR`, `SpindleFault_M`, `LubeFault_M`, `AxisFault_M`, `OtherFault_M`,
  `SoftwareNotReady_M`, `PLCExecutorFault_M` are set — this is the single recovery rung for
  the whole fault OR-gate.
- (src:2878-2879): `ErrorFlag_M` auto-clears after `ErrorFlag_T` expires (preset loaded once
  at boot, per [boot.md](boot.md)) — this is the "non-fault error" (as opposed to
  `SV_STOP`-class fault) auto-reset path referenced generically in `CLAUDE.md`.
- (src:2881-2882): `ProbeFault_M && !ProbeMsgSent_M` posts `PROBE_FAULT_MSG_C` once
  (guarded by `ProbeMsgSent_M` so it doesn't re-post every scan while the fault persists —
  though nothing in this excerpt actually sets `ProbeMsgSent_M`; it is presumably set
  elsewhere or is a latent no-op — purpose inferred, not confirmed from this rung group).

### M-code housekeeping and auto spindle/coolant prompts (src:2884-2908)

- (src:2886-2891): outside `SV_PROGRAM_RUNNING`/`SV_MDI_MODE`, reset `M3_SV`, `M4_SV`,
  `M8_SV`, `M7_SV`, `M10_SV` — clears spindle/coolant/clamp M-code latches when leaving a
  running job so they don't persist into manual mode.
- (src:2894-2897): `M3_SV || M4_SV` one-shots `AutoSpindlePD_PD`; if that fires while
  `!SpinAutoModeLED_O` (manual mode is selected), force a feed hold
  (`SET ActivateFeedHold_M`) and post `AUTO_SPINDLE_PROMPT_C` — an auto-mode spindle command
  arriving while the operator is in manual spindle mode pauses the program instead of
  silently ignoring the M-code.
- (src:2899-2902): identical pattern for `M7_SV || M8_SV` vs. `CoolAutoModeLED_O`, posting
  `AUTO_COOLANT_PROMPT_C`.
- (src:2904-2905): `ActivateFeedHold_M` arms `TriggerPause_T` (100 ms) and, once expired,
  clears both the timer and `ActivateFeedHold_M` — a one-shot pulse of the feed-hold request
  rather than a held signal.
- (src:2908): `RST OnAtPowerUp_M` unconditionally — this is where the boot-time
  "still at power-up" latch (set once in `InitialStage`, per [boot.md](boot.md)) finally
  clears, one scan after `MainStage` starts running.

Gotcha: **clamp** (`M10_SV`, driven by `mfunc10.mac`/`mfunc11.mac` via `M94 /4`/`M95 /4`) is
reset here alongside the other M-codes (src:2891), and `ClampEnabled_M IS MEM91`
(src:529) is defined, but no rung anywhere in `MainStage`, `JogPanelStage`, or
elsewhere in this file reads `M10_SV`/`ClampEnabled_M` to drive a `Clamp_O` output —
`mfunc11.mac`'s own header comment lists `Clamp_O IS OUT12` as a PLC variable, but that
definition is not present in `Centroid-Acroloc-ALLIN1DC.src`. Purpose/completeness of the
clamp path could not be confirmed from this source file alone.

## ATC kickoff

Full ATC carousel state-machine detail (position-switch decode, base-16-as-decimal tool ID,
motor/lock outputs) lives in [atc.md](atc.md) — this section only covers the
hand-off rungs inside `MainStage` that arm `ATCStage`.

- **Tool-change entry** (src:2911, tagged "Acroloc tool stage start" at
  src:2910): `IF M6_SV THEN ChangeToTool_W = SV_TOOL_NUMBER, SET ATCStage` — the moment
  `mfunc6.mac` sets `M6_SV`, `MainStage` latches the requested tool number into
  `ChangeToTool_W` and arms `ATCStage`. Because `ATCStage` (STG16, src:1207)
  appears **after** `MainStage` (STG4) in file order, per `scan-model.md` this `SET` takes
  effect **in this same scan** — `ATCStage`'s body runs immediately.
- **Manual carousel unlock** (src:2913-2922, tagged "Acroloc manual tool changes"):
  `ATCManualUnlock_I && ATC_Z_Zero_Release_I && !ATCStage` drives `SET ATCUnlocked_O`
  (src:2914); the mirror, `!ATCManualUnlock_I && !ATCStage`, drives
  `RST ATCUnlocked_O` (src:2915) — the manual unlock button only works while
  `ATCStage` is not already running its own carousel-motion sequence, avoiding a fight over
  `ATCUnlocked_O` between manual and automatic unlock. `ATCManualUnlock_I` also unconditionally
  posts either `ATC_Lock_Not_Released_C` or `ATC_Lock_Released_C`
  (src:2917-2922) via `ShowFaultStage`, purely as an operator status message
  (not a fault gate on its own).
- **Spindle-in-changer feed-hold interlock** (banner src:2959, tagged
  "Acroloc -- Spindle-in-changer feed-hold interlock"). Replaced the old always-on stop block
  on 2026-07-09 (spec
  [2026-07-09-spindle-changer-feedhold-design.md](../superpowers/specs/2026-07-09-spindle-changer-feedhold-design.md)).
  Six rungs, placed **after** the `SpinStart_M` seal-in coil so the per-scan enable-kill holds:
  1. `IF ATC_Z_ClearedToolChanger_I THEN RST ChangerHoldDone_M` — clear the once-per-entry latch
     when Z is clear.
  2. `IF !ATC_Z_ClearedToolChanger_I THEN RST SpindleEnableOut_O` — **unconditional zone-kill**,
     every scan, in *all* modes (program, MDI, manual). Independent of the hold latch, so the
     spindle can never run — or be manually started — while Z is in the changer.
  3. `IF !(SV_PROGRAM_RUNNING || SV_MDI_MODE) THEN` clear all three latches — clean bail-out if
     the program stops mid-hold, so the next run re-confirms zero from scratch.
  4. **Arm** when a program/MDI move enters the zone with the spindle *not* already stopped
     (`!ZeroSpeed_I`): `SET ChangerHoldActive_M, SET ActivateFeedHold_M`, load and start
     `ChangerStopTimer_T = 5000`. If `ZeroSpeed_I` already reads stopped at entry (normal M6 —
     mfunc6 runs `M5` before the park move) this never arms and motion proceeds.
  5. **Resume** the instant zero is confirmed: `IF ChangerHoldActive_M && ZeroSpeed_I THEN`
     `SET DoCycleStart_SV` (a pulse, not a coil — a coil would clobber the stock operator
     cycle-start).
  6. **Timeout -> fault**: `IF ChangerHoldActive_M && ChangerStopTimer_T && !ZeroSpeed_I THEN`
     post `SPINDLE_FAULT_MSG_C`, `SET OtherFault_M`; motion stays held, no auto-resume.

  Timer idiom: a bare timer is true **when expired**, so rung 6 fires only at the 5 s deadline.
  Feed-hold handshake: `ActivateFeedHold_M` (MEM45) is a self-clearing trigger (stock code RSTs
  it ~100 ms after set, src:2937-2938) that SETs `FeedHoldLED_O` (src:1866-1868) driving
  `DoFeedHold_SV`; `DoCycleStart_SV` clears `FeedHoldLED_O` (src:1869-1872) to resume — so the
  interlock deliberately does not RST `ActivateFeedHold_M`. Unlike the block it replaced, this
  one **does** fault on a spindle that never reaches zero. See [atc.md](atc.md) for the
  companion `ATCStage` zero-speed guard.

## Gear decision

Full gear-shift state-machine detail (the coast-dwell sequencing inside `GearShiftStage`,
`STG17`) lives in [gear-shift.md](gear-shift.md). This section summarizes only the
*decision* logic — where `DesiredRange_W` is computed and where the shift is kicked off —
which physically sits inside the `JogPanelStage` banner block (src:1772-2406,
decision rungs at src:2259-2333); see [Stage scope note](#stage-scope-note) for
why it is documented here.

- **Un-overridden speed** (src:2277-2281, comment explains the "why"): the raw commanded
  spindle speed from CNC12 (`SV_PC_COMMANDED_SPINDLE_SPEED`) already includes the operator's
  override-knob percentage (`SV_PLC_SPINDLE_KNOB`, clamped 1-200 by the override section at
  src:2250-2251). `GearBaseSpeed_FW = SV_PC_COMMANDED_SPINDLE_SPEED * 100.0 /
  SV_PLC_SPINDLE_KNOB` backs the knob back out, so sweeping the override across the
  low/high crossover speed mid-cut cannot itself trigger a gear shift.
- **Hysteresis deadband** (src:2283-2289): if `SV_MACHINE_PARAMETER_860 <= 0.0`,
  auto-select is disabled and `DesiredRange_W` just tracks `EngagedRange_W` (no-op, stays
  put). Otherwise, `DesiredRange_W = 4` once `GearBaseSpeed_FW` rises to or above
  `P860 + P861`, and `DesiredRange_W = 1` once it falls to or below `P860 - P861` — `P860` is
  the crossover center, `P861` the hysteresis half-width, so the deadband between the two
  thresholds prevents chatter right at the crossover speed.
- **Effective range tracking** (src:2293): `IF !GearShiftStage THEN SpindleRange_W =
  EngagedRange_W` — while not mid-shift, the ratio/DAC math further down always uses the
  actually-engaged clutch's range, not the desired one.
- **Kickoff rung arming `GearCoast_T`** (src:2300-2307): once
  `DesiredRange_W != EngagedRange_W`, **the spindle is enabled** (`SpindleEnableOut_O` — so the
  machine holds neutral while stopped and engages a gear only on spin-up), and neither
  `GearShiftStage` nor `ATCStage` is already running, load `GearCoast_T` with a default of 1500 ms (src:2300-2301),
  override it from `SV_MACHINE_PARAMETER_862` if that parameter is positive
  (src:2302-2304), then arm the timer and `SET GearShiftStage`
  (src:2305-2307). Per `scan-model.md`'s worked example, because
  `GearShiftStage` (STG17) is swept after this point in the same pass, its Step A rung runs
  in this same scan. The `!ATCStage` guard prevents a gear shift from starting mid tool-change.
- **Range flags and speed ratio** (src:2311-2333): `SpindleRange_W` (1/2/3/4)
  sets `SV_SPINDLE_LOW_RANGE`/`SV_SPINDLE_MID_RANGE` per the truth table in the source
  comment (src:2266-2268) and loads `SpinRangeAdjust_FW` from
  `SV_MACHINE_PARAMETER_65`/`66`/`67`/`33` respectively (range 4/high reads P33, falling back
  to `1.0` if P33 `<= 0`). A negative ratio parameter flips
  `SpinRangeReversed_M` and is negated back to a positive ratio
  (src:2329-2330); the ratio is floored at `0.001` (src:2333) since it is
  later used as a divisor.
- **Both-off lockup backstop** (src:2408-2421, tagged "Acroloc: clutch truth table"):
  the clutch outputs encode gear by a truth table — one on = that gear, **both on = neutral**,
  **both OFF = mechanical LOCKUP** (forbidden). If `!Spindle_Low_gear_O && !Spindle_High_gear_O`
  is ever true, the rung **stops the spindle** (`RST SpindleEnableOut_O`, which zeros the DAC
  via src:2363), commands neutral (`SET` both clutches to release the lockup), sets
  `EngagedRange_W = 0` (out-of-band "gear state unknown"), posts `SPINDLE_FAULT_MSG_C`, and
  sets `OtherFault_M` — which folds into the fault-aggregation OR-gate above (src:2841) and
  asserts `SV_STOP`. Zeroing `EngagedRange_W` guarantees the next valid speed demand forces a
  full re-shift rather than trusting a value that was live when the lockup was
  detected.

Spindle-speed-to-DAC conversion math (src:2335-2394 — min/max clamping,
RPM-per-bit, 12-bit DAC word, and the `WTB` write to `SpinAnalogOutBit0_O`) and the plain
spindle enable/direction/override rungs (src:2131-2258) are stock-shaped logic
with the gear ratio (`SpinRangeAdjust_FW`) factored in at src:2381; they are
not repeated rung-by-rung here since none of it is part of the gear *decision* itself, only
its downstream consumer.

### Coolant (mist/flood) — mfunc7/mfunc8 linkage (src:2086-2127)

- (src:2089-2099): `CoolantAutoManualPD_PD` toggles `CoolAutoModeLED_O` (forced on at
  power-up, src:2091), which is mirrored to CNC12 via `SelectCoolAutoMan_SV`.
- (src:2117-2120) Flood: `Flood_O` is a coil combining a manual-mode toggle
  (`Flood_O XOR (!CoolAutoModeLED_O && CoolantFloodPD_PD)`, i.e. flip on a manual key press)
  with an auto-mode drive (`CoolAutoModeLED_O && M8_SV`, i.e. follow the M8 code exactly),
  ANDed against a kill condition (`!(SV_STOP || CoolantAutoManualPD_PD ||
  (CoolAutoModeLED_O && !M8_SV) || ErrorFlag_M || DoToolCheck_SV)`) — flood is forced off on
  stop/fault/tool-check or the instant the mode is toggled or auto mode has no M8 asserted.
- (src:2124-2127) Mist: identical shape, `Mist_O` against `M7_SV`.
- Both mist and flood are reset as part of the M-code housekeeping rung inside the
  `MainStage` banner (`RST M8_SV, RST M7_SV`, src:2889-2890) when leaving
  `SV_PROGRAM_RUNNING`/`SV_MDI_MODE`, and both drive an `AutoCoolantPD_PD` feed-hold prompt
  from within `MainStage` proper (src:2899-2902, described above) if M7/M8 arrives
  while the operator is in manual coolant mode.

## Verification

Every `(src:NNNN)` citation above was checked against
`Centroid-Acroloc-ALLIN1DC.src` at commit 41f3fd6 with
`sed -n '<line>p'`; the working tree is unchanged since that commit
(`git status` shows no modifications to the `.src` file).
