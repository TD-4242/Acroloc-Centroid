# Jog and MPG: handwheel, jog-panel, and jog-key subsystems

One-line purpose: reference for the operator jog/MPG path — hardwired MPG (`MPGStage`),
wireless/USB MPG (`WirelessMpgStage`), the jog-panel key decode and override math
(`JogPanelStage`, jog/MPG-specific rung groups only), and the four configuration-selected
axis-mapping stages (`JogKeysNormalStage`, `JogKeysInvert2Stage`, `JogKeysSwappedStage`,
`JogKeysSwapAndInvert2Stage`). This is almost entirely stock Centroid logic — documented at
rung-group level, not rung-by-rung.

Line numbers as of commit 41f3fd6

Stage sweep order and timer semantics are defined in
[scan-model.md](scan-model.md); resource name -> line lookups are in
[definitions.md](definitions.md). Neither is repeated here.

## Scope note — boundary with main-stage.md

`JogPanelStage` (src:1195, banner at src:1771-1773) is a single
banner-scoped block running src:1774-2406. `main-stage.md` already documents the back half of
that block — spindle enable/direction/override, gear-decision, spindle-speed-to-DAC math,
and coolant (mist/flood) — because those rungs are conceptually part of "MainStage" per this
doc set's established convention (see main-stage.md's own
[Stage scope note](main-stage.md#stage-scope-note)). Concretely, **main-stage.md owns
src:2086-2405** (coolant at src:2086-2127, plain spindle
enable/direction/override at src:2131-2258, gear decision at
src:2259-2333, DAC conversion at src:2335-2394, clutch
interlock at src:2396-2405).

**This file owns src:1774-2085** (jog-panel key decode, feedrate-override
math, cycle-start/cancel, axis-3/4/5/6 jogging, Aux-key dispatch) plus `MPGStage`
(src:1647-1682), `WirelessMpgStage` (src:1683-1770), and the four
`JogKeys*Stage` axis-mapping stages (src:2407-2490). Where a rung
group below needs a fault/coolant/gear concept, it links to main-stage.md rather than
re-explaining it.

## `MPGStage` (STG7, src:1199) — hardwired MPG (src:1647-1682)

Purpose: read the hardwired handwheel's axis-select DIP/parameter mapping and multiplier
switch into the `SV_MPG_*` system variables CNC12 consumes.

- (src:1654-1656): `HandWheel_M && !MPG_M` (i.e. not using the jog-panel's own MPG mode)
  maps `SV_MPG_1/2/3_AXIS_SELECT` from `SV_MACHINE_PARAMETER_441/442/443` — three encoder
  inputs, each independently mapped to a machine axis by parameter.
- (src:1659-1665): `SV_MPG_1_ENABLED`/`2`/`3` are driven true whenever `MPGLED_O` (MPG mode
  selected) is on and either a hardwired MPG-axis input is active or the corresponding axis
  select is nonzero.
- (src:1667-1671): `MPG_AXIS_n_I` inputs (1-5) directly load `SV_MPG_1_AXIS_SELECT = n`.
- (src:1674-1681): the x1/x10/x100 LEDs (shared with the jog panel, set in `JogPanelStage`
  below) drive `SV_MPG_1/2/3_MULTIPLIER`; below x10, "windup mode" is disabled on all three
  MPG channels (`SV_MPG_n_WINDUP_MODE`) — purpose inferred: windup (accumulating handwheel
  counts while a move is still catching up) is only wanted at coarser multipliers.
- `MPGStage` and `WirelessMpgStage` are mutually exclusive by machine-parameter selection —
  see [InitialStage config select](#config-select-in-initialstage) below.

## `WirelessMpgStage` (STG60, src:1214) — USB/wireless MPG (src:1683-1770)

Purpose: the USB pendant equivalent of `MPGStage`, adding active-axis masking, a
scale-selector knob, and per-axis "selected" flags consumed by macro `SetAxis` logic.

- (src:1689-1690): `UsbMpgActiveAxes_W = SV_MACHINE_PARAMETER_218` is decoded via `WTB` into
  8 per-axis `UsbMpgAxisNActive_M` bits — which axes the USB pendant is allowed to jog.
- (src:1694-1698): edge-detects a knob change (`UsbAxisKnobChanged_M`) by comparing the
  live `SV_USB_MPG_AXIS_SELECT` against a monitor word latched every scan; separately mirrors
  `SV_USB_MPG_SCALE_SELECT` into `UsbScaleMonitor_W`.
- (src:1701-1708): if the scale knob reads an invalid value (`> 100`, reserved for
  hardwired-MPG passthrough) or the selected axis isn't in the active-axis mask, force
  `SV_MPG_1_AXIS_SELECT = 0` and zero the monitor — guards against jogging an axis the
  machine config doesn't expose to the pendant.
- (src:1711): `UsbMpgOn_M` gates on `SV_USB_MPG_POWER` (pendant physically present/powered)
  and a valid axis+scale selection.
- (src:1714-1738): per-axis `SV_MPG_1_AXIS_SELECT = n` for n=1-8, each gated on the matching
  `UsbMpgAxisNActive_M`; falls back to axis 0 (no axis) if the monitor is 0.
- (src:1742-1759): same handwheel-axis-mapping, MPG-enable, multiplier, and windup-mode
  rungs as `MPGStage` above, but ORed with `UsbMpgOn_M` so either the hardwired or wireless
  path can drive the same `SV_MPG_*` variables.
- (src:1762-1769): `UsbMpgAxisNSelected_M` (n=1-8) mirrors which axis the USB knob currently
  points at, independent of whether that axis is jogging — consumed by a macro (not in this
  repo) for `SetAxis`-style zero/display logic per `CLAUDE.md`'s macro-variable convention.

### Config select in InitialStage

`SV_MACHINE_PARAMETER_218 == 0` selects `MPGStage` (`RST WirelessMpgStage`);
`> 0` selects `WirelessMpgStage` (`RST MPGStage`) — src:1299-1300, in
`LoadParametersStage` (documented in [boot.md](boot.md)), not repeated here.

## `JogPanelStage` (STG3, src:1195) — jog-and-MPG rung groups (src:1774-2085)

Purpose: decode the physical jog-panel keys (and their keyboard/skin/USB-MPG equivalents)
into the `SV_*` request bits CNC12 reads each scan, plus the feedrate-override knob math.

- **MPG on/off and lockout** (src:1774-1793): `MpgPD_PD` one-shots the MPG key;
  `MPGManOffFlag_M` tracks "operator explicitly turned MPG off" so re-enabling `SV_MPG_1_ENABLED`
  elsewhere doesn't silently re-light `MPGLED_O`. `MpgZAxisLocked_M` (src:1789-1793)
  locks out x100 on whichever axis is configured as "Z" per `SV_MACHINE_PARAMETER_820` — a
  safety rail against a x100 jog on the long/critical axis.
- **x1/x10/x100 select** (src:1795-1815): three parallel rungs, each combining the
  physical key, keyboard toggle, skin button, and the matching USB-MPG scale-knob position;
  x100 additionally requires `!MpgZAxisLocked_M`. Reset-then-set idiom (no `ELSE`) per
  `scan-model.md`.
- **Incremental/continuous and fast/slow jog mode** (src:1817-1830): same
  key+keyboard+skin+USB-knob pattern; `FastSlowLED_O` is also forced on by
  `MainStage`'s probe-protection rung (main-stage.md, src:2751) as a
  separate safety override, independent of the panel key here.
- **Single-block mode** (src:1832-1837): toggled only while `!SV_PROGRAM_RUNNING`
  (can't flip single-block mid-cycle); mirrors to `SelectSingleBlock_SV`.
- **Tool check** (src:1839-1843): gated on `EStopOk_M`; fires `DoToolCheck_SV`.
- **Feed hold** (src:1845-1856): `FeedHoldPD_PD` from key/keyboard/MPG/skin, or
  `ActivateFeedHold_M` (set by `MainStage`'s auto-spindle/coolant-prompt rungs, main-stage.md
  src:2894-2905), or the feed-override dropping below `SV_MACHINE_PARAMETER_146`
  all latch `FeedHoldLED_O`; cleared on cycle start/cancel/tool-check or the override
  recovering above P146. `PrevFeedOverride_W` is snapshotted every scan (src:1856) purely to
  detect that recovery edge next scan.
- **Feedrate override math** (src:1858-2027, extensively commented in-source): reads the
  jog-panel's 8-bit override knob via `BTW` (src:1898-1899), scales 0-255 to
  0-200% (src:1904), then arbitrates between the knob and keyboard/skin
  increment-by-1% requests (`KbOverride_W`, src:1921-1973) and the USB-MPG
  feed wheel (src:1951-1959) to produce `FinalFeedOverride_W`, clamped to
  `SV_MACHINE_PARAMETER_39` (src:1980-1995) and forced to 100% if
  `SV_PC_OVERRIDE_CONTROL_FEEDRATE_OVERRIDE` is off (src:2006). Sent to CNC12 as
  `SV_PLC_FEEDRATE_KNOB` (src:2012) and echoed back through
  `SV_PC_FEEDRATE_PERCENTAGE` -> `SV_PLC_FEEDRATE_OVERRIDE` (src:2027) per the
  7-step protocol spelled out in the source comment (src:1861-1889). LED rungs
  (src:2015-2018) just mirror the four quick-select percentages.
- **Rapid override, cycle start/cancel** (src:2029-2040): `F9PD_PD`/keyboard toggle
  drive `SelectRapidOverride_SV`; cycle cancel ORs the physical key, keyboard, MPG reset key,
  skin button, and `ErrorFlag_M` (any latched error also cancels the cycle); cycle start ORs
  the equivalent four sources.
- **Axis 3/4/5/6 jogging and Aux keys** (src:2042-2084): axis-1/2 jogging is deliberately
  *not* here — the comment at src:2042-2043 notes it lives in the
  configuration-specific `JogKeys*Stage` stages below, because axis-1/2 mapping depends on
  invert/swap configuration while axes 3+ don't. Each axis-3/4/5/6 rung ORs
  physical-key/keyboard/USB-MPG-jog/skin sources, gated off when in zero-feed incremental
  mode (`IncrContLED_O && FinalFeedOverride_W == 0`). Aux1-16 (src:2062-2077)
  are a flat OR of key/keyboard/skin per aux button, undifferentiated dispatch bits consumed
  elsewhere (e.g. worklight in main-stage.md src:2816-2819 reads `DoAux7Key_SV`).
  src:2078-2084 mirror the LED states above into `SV_Select*` status bits CNC12
  reads for its own display.

## `JogKeysNormalStage` / `JogKeysInvert2Stage` / `JogKeysSwappedStage` / `JogKeysSwapAndInvert2Stage`

STG26-29 (src:1210-1213), banners at src:2407-2490. Purpose: the
axis-1/2 jog-key -> `DoAxNPlusJog_SV`/`DoAxNMinusJog_SV` mapping, replicated four times with
the physical direction remapped per the invert/swap configuration selected once at boot.

- **Which stage is active** is decided in `LoadParametersStage` (src:1365-1371,
  documented in [boot.md](boot.md)): `InvertXJogKeys_M` (bit 1 of `JogKeyCfg_W`) and
  `SwapAxes_M` combine into exactly one of the four stages being `SET`, the other three
  `RST` — mutually exclusive, decided once and not re-evaluated per scan.
- Each stage's rungs (e.g. `JogKeysNormalStage` src:2415-2426) are
  structurally identical: four rungs mapping axis-1-plus/minus and axis-2-plus/minus key
  sources (physical key, keyboard, USB-MPG jog, skin button, plus the two "combo" skin
  buttons `SkinJogAx1Ax2Plus_M`/`SkinJogAx1PlusAx2Minus_M` for simultaneous diagonal jogging)
  to `DoAx1PlusJog_SV`/`DoAx1MinusJog_SV`/`DoAx2PlusJog_SV`/`DoAx2MinusJog_SV`, each gated by
  its own `AxNDirDisabled_M` bit (set by `MainStage`'s probe-protection rung, main-stage.md
  src:2678-2708) and the zero-feed incremental-mode lockout.
- **What differs between the four stages** is only which physical key source feeds which
  `DoAxNJog_SV` output and which `AxNDirDisabled_M` bit gates it — compare
  `JogKeysNormalStage` (src:2415-2426, X+ key -> axis-1-plus) against
  `JogKeysInvert2Stage` (src:2436-2447, axis-2 keys swap their plus/minus
  mapping relative to Normal) against `JogKeysSwappedStage` (src:2457-2468,
  axis-1 and axis-2 key sources trade places entirely) against
  `JogKeysSwapAndInvert2Stage` (src:2478-2489, swapped *and* axis-2
  inverted) — the in-source ASCII diagrams above each banner (e.g. src:2410-2414)
  show the resulting physical jog-panel-to-machine-axis orientation for each configuration.
  This is a config-time wiring choice, not runtime logic worth tracing rung-by-rung beyond
  that pattern.

## Verification

Every `(src:NNNN)` citation above was checked against `Centroid-Acroloc-ALLIN1DC.src` at
commit 41f3fd6 with `sed -n '<line>p'`; the working tree is unchanged since that commit
(`git status` shows no modifications to the `.src` file).
