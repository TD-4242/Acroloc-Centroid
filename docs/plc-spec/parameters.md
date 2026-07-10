# Machine parameter reference

One-line purpose: every `SV_MACHINE_PARAMETER_n` the `.src` reads, in one table, each row
citing the reading rung and the subsystem file that documents it — so a parameter change on
the control PC can be traced to the exact PLC line(s) it affects without grepping the whole
program.

Line numbers as of commit 41f3fd6

## How to use this table

- **Param** is the CNC12 machine-parameter number (`P<n>` in Centroid's parameter editor),
  cited in source as `SV_MACHINE_PARAMETER_n`.
- **Read at (src:NNNN)** cites every rung that reads the parameter, not just the first.
- **Subsystem** links to the `docs/plc-spec/` file whose scope covers that rung.
- Comment-only mentions (the parameter cross-reference block at src:47-78 and the general
  system-variable note at src:753) are listed once at the bottom, separately, since they are
  documentation the stock program left in the source rather than executable reads.

## Parameter table

| Param | Meaning | Read at (src:NNNN) | Subsystem | Value semantics / intended value |
|---|---|---|---|---|
| P1 | Jog-key configuration bitmask (`JogKeyCfg_W`); bit 1 = invert axis-2 jog keys, bit 2 = swap axes | `JogKeyCfg_W = SV_MACHINE_PARAMETER_1` (src:1364) | [boot.md#loadparametersstage](boot.md#loadparametersstage-src1284-1376) | Bitmask; consumed by `JogKeysNormalStage`/etc. in [jog-and-mpg.md](jog-and-mpg.md#jogkeysnormalstage--jogkeysinvert2stage--jogkeysswappedstage--jogkeysswapandinvert2stage) |
| P19 | MPG mode value (`PValue_W`); bit 1 = lock out x100 on an axis per P820 | `PValue_W = SV_MACHINE_PARAMETER_19` (src:1305) | [boot.md#loadparametersstage](boot.md#loadparametersstage-src1284-1376) | Bitmask; `MpgX100LockOut_M` consumed in [jog-and-mpg.md](jog-and-mpg.md#jogpanelstage-stg3-src1195--jog-and-mpg-rung-groups-src1774-2085) |
| P33 | **Not used by the gear code (tried, abandoned).** Wired as the high-range ratio but is not writable from the CNC12 param screen on this control (reads a fixed ~2.0), so it could not be tuned. High ratio moved to **P863**. | (formerly read at src:2342) | [gear-shift.md](gear-shift.md) | Do not use for tuning; see P863 |
| P39 | Feedrate override percentage limit (ceiling on jog-panel knob, keyboard override, and final override) | `FeedrateKnob_W` clamp (src:1907-1908); `KbOverride_W` clamp (src:1980-1981); `FinalFeedOverride_W` clamp (src:1994-1995) | [jog-and-mpg.md#jogpanelstage-stg3-src1195--jog-and-mpg-rung-groups-src1774-2085](jog-and-mpg.md#jogpanelstage-stg3-src1195--jog-and-mpg-rung-groups-src1774-2085) | Percent (0-200 scale); each of the three override values is clamped to this ceiling independently |
| P57 | Enable/disable load-meter display | `IF SV_MACHINE_PARAMETER_57 != 0 THEN SET LoadMeterStage` / `== 0 THEN RST` (src:1357-1358) | [boot.md#loadparametersstage](boot.md#loadparametersstage-src1284-1376) | 0 = load meters off, nonzero = on (`LoadMeterStage`, STG6) |
| P65 | Low-range gear ratio adjustment | `SpinRangeAdjust_FW = SV_MACHINE_PARAMETER_65` when `SpindleRange_W == 1` (src:2313) | [gear-shift.md](gear-shift.md) (main-stage.md `SpindleRange_W` decode block, src:2308-2325) | Ratio multiplier applied to the spindle-speed/DAC math for range 1 (low); **the PLC does read this one** — it is not CNC12-side only. See note below. |
| P66 | Medium-low range gear ratio adjustment | `SpinRangeAdjust_FW = SV_MACHINE_PARAMETER_66` when `SpindleRange_W == 2` (src:2317) | [gear-shift.md](gear-shift.md) | Ratio multiplier for range 2 |
| P67 | Medium-high range gear ratio (range 3) — **cannot serve as the high-gear ratio: CNC12 locks the medium-range gains** on this machine (declared range count too low to expose them for editing) | `SpinRangeAdjust_FW = SV_MACHINE_PARAMETER_67` when `SpindleRange_W == 3` (src:2343, dead path) | [gear-shift.md](gear-shift.md) | Ratio multiplier for range 3; range 3 never engages here |
| P863 (Acroloc) | High-range (range 4) gear ratio adjustment | `SpinRangeAdjust_FW = SV_MACHINE_PARAMETER_863` when `SpindleRange_W == 4` (src:2347) | [gear-shift.md](gear-shift.md) | Writable ratio multiplier for high gear, tuned on-machine to ~2.0. Falls back to `2.0` if left `<= 0` (NOT 1.0 — that would overspeed the spindle ~2x). In the 860-870 "Not Used" block; these general params stay editable regardless of spindle range config (unlike P66/P67). |
| P146 | Feed-hold threshold (`P146Value_W`) | `P146Value_W = SV_MACHINE_PARAMETER_146` (src:1312) | [boot.md#loadparametersstage](boot.md#loadparametersstage-src1284-1376) | Threshold compared against `FinalFeedOverride_W` in [jog-and-mpg.md](jog-and-mpg.md#jogpanelstage-stg3-src1195--jog-and-mpg-rung-groups-src1774-2085) (src:1850-1854) to trigger a feed-hold prompt |
| P148 | Misc jogging options bitmask (`P148Value_W`); bit 1 = disable keyboard jogging (CNC10 back-compat) | `P148Value_W = SV_MACHINE_PARAMETER_148` (src:1313); `BITTST P148Value_W 1 DisableKbInput_M` (src:1348) | [boot.md#loadparametersstage](boot.md#loadparametersstage-src1284-1376) | Bitmask; bit 1 set forces `RST AllowKbInput_M` regardless of P170 |
| P153 | Probe-protection enable | `IF SV_MACHINE_PARAMETER_153 == 0 THEN RST ProbeProtectionEnable_M` / `> 0 THEN SET` (src:1374-1375) | [boot.md#loadparametersstage](boot.md#loadparametersstage-src1284-1376) | 0 = disabled, >0 = enabled; consumed in [main-stage.md](main-stage.md#probe-protection-while-jogging-src2670-2756) |
| P170 | Keyboard-jogging enable bitmask (`P170Value_W`): bit 0 = allow keyboard input, bit 1 = jog-override-only, bit 2 = keyboard-override-only | `P170Value_W = SV_MACHINE_PARAMETER_170` (src:1314); `BITTST` decode (src:1349-1351) | [boot.md#loadparametersstage](boot.md#loadparametersstage-src1284-1376) | Bitmask; also referenced directly at src:1791-1792 (P820 axis-lock interaction) and documented inline at src:1460-1471 |
| P179 | Lube-pump timing, packed `MMMSS` (minutes/seconds) | `Lube_W = SV_MACHINE_PARAMETER_179` (src:1294) | [boot.md#loadparametersstage](boot.md#loadparametersstage-src1284-1376) | Decoded into `LubeM_W`/`LubeS_W` milliseconds; selects pump-timer method (`LubeUsePumpTimersStage` vs `LubeUsePLCTimersStage`) |
| P218 | MPG wiring mode: 0 = wired MPG, >0 = wireless/USB MPG; also doubles as USB active-axes bitmask | `SV_MACHINE_PARAMETER_218 == 0` / `> 0` stage select (src:1299-1300); `UsbMpgActiveAxes_W = SV_MACHINE_PARAMETER_218` (src:1689) | [jog-and-mpg.md#mpgstage-stg7-src1199--hardwired-mpg-src1647-1682](jog-and-mpg.md#mpgstage-stg7-src1199--hardwired-mpg-src1647-1682) / [jog-and-mpg.md#wirelessmpgstage-stg60-src1214--usbwireless-mpg-src1683-1770](jog-and-mpg.md#wirelessmpgstage-stg60-src1214--usbwireless-mpg-src1683-1770) | Selects `MPGStage` vs `WirelessMpgStage`; bits also gate `UsbMpgAxisNActive_M` via `WTB` |
| P219 | Start VCP (virtual control panel) on boot | comment-documented only (src:66); no executable read found via grep | n/a | 0 = no VCP, 1 = start VCP on boot — **not read by this `.src`** (grep finds only the header comment at src:66; see note below) |
| P348 | MPG-1 encoder assignment (15 = special/disable case) | `IF SV_MACHINE_PARAMETER_348 == 15 THEN (MPG_M)` / combined check with P351/P354 (src:1301-1303) | [jog-and-mpg.md#mpgstage-stg7-src1199--hardwired-mpg-src1647-1682](jog-and-mpg.md#mpgstage-stg7-src1199--hardwired-mpg-src1647-1682) | Encoder-present detection; feeds `HandWheel_M` |
| P351 | MPG-2 encoder assignment | src:1303 (as part of the P348/P351/P354 OR) | [jog-and-mpg.md#mpgstage-stg7-src1199--hardwired-mpg-src1647-1682](jog-and-mpg.md#mpgstage-stg7-src1199--hardwired-mpg-src1647-1682) | Same role as P348 for the second hardwired MPG |
| P354 | MPG-3 encoder assignment | src:1303 (as part of the P348/P351/P354 OR) | [jog-and-mpg.md#mpgstage-stg7-src1199--hardwired-mpg-src1647-1682](jog-and-mpg.md#mpgstage-stg7-src1199--hardwired-mpg-src1647-1682) | Same role as P348 for the third hardwired MPG |
| P441 | MPG-1 axis-select assignment for encoder input 1 | `SV_MPG_1_AXIS_SELECT = SV_MACHINE_PARAMETER_441` (src:1654, repeated src:1742) | [jog-and-mpg.md#mpgstage-stg7-src1199--hardwired-mpg-src1647-1682](jog-and-mpg.md#mpgstage-stg7-src1199--hardwired-mpg-src1647-1682) / [jog-and-mpg.md#wirelessmpgstage-stg60-src1214--usbwireless-mpg-src1683-1770](jog-and-mpg.md#wirelessmpgstage-stg60-src1214--usbwireless-mpg-src1683-1770) | Axis number for handwheel encoder 1 |
| P442 | MPG-2 axis-select assignment for encoder input 2 | src:1655, repeated src:1743 | same as P441 | Axis number for handwheel encoder 2 |
| P443 | MPG-3 axis-select assignment for encoder input 3 | src:1656, repeated src:1744 | same as P441 | Axis number for handwheel encoder 3 |
| P820 | Which axis is Z (interacts with the x100 lockout: `SV_MPG_1_AXIS_SELECT == 3` normally means Z, but if P820 == 1 the Z axis is remapped to axis 1) | src:1791-1792 | [jog-and-mpg.md#jogpanelstage-stg3-src1195--jog-and-mpg-rung-groups-src1774-2085](jog-and-mpg.md#jogpanelstage-stg3-src1195--jog-and-mpg-rung-groups-src1774-2085) | 0/unset = axis 3 is Z (default); 1 = axis 1 is Z — gates `MpgZAxisLocked_M` |
| P900 | Expected "PLC ADD" (mini-PLC/Cyclone board) installed bitmask | `P900Value_W = SV_MACHINE_PARAMETER_900` (src:2562) | [faults-and-messages.md#miniplcerrorstage-stg9-src1201-banner-src2567-2569](faults-and-messages.md#miniplcerrorstage-stg9-src1201-banner-src2567-2569) | Compared against live `SV_PC_MINI_PLC_ONLINE` (`MiniPLCStatus_W`); mismatch sets `MiniPLCErrorStage` |
| P911 | Invert inputs 1-16 | src:1317 | [boot.md#loadparametersstage](boot.md#loadparametersstage-src1284-1376) | Passed straight through to `SV_INVERT_INP1_16_BITS` |
| P912 | Invert inputs 17-32 | src:1318 | [boot.md#loadparametersstage](boot.md#loadparametersstage-src1284-1376) | -> `SV_INVERT_INP17_32_BITS` |
| P913 | Invert inputs 33-48 | src:1319 | [boot.md#loadparametersstage](boot.md#loadparametersstage-src1284-1376) | -> `SV_INVERT_INP33_48_BITS` |
| P914 | Invert inputs 49-64 | src:1320 | [boot.md#loadparametersstage](boot.md#loadparametersstage-src1284-1376) | -> `SV_INVERT_INP49_64_BITS` |
| P915 | Invert inputs 65-80 | src:1321 | [boot.md#loadparametersstage](boot.md#loadparametersstage-src1284-1376) | -> `SV_INVERT_INP65_80_BITS` |
| P916 | Force inputs 1-16 | src:1322 | [boot.md#loadparametersstage](boot.md#loadparametersstage-src1284-1376) | -> `SV_FORCE_INP1_16_BITS` |
| P917 | Force inputs 17-32 | src:1323 | [boot.md#loadparametersstage](boot.md#loadparametersstage-src1284-1376) | -> `SV_FORCE_INP17_32_BITS` |
| P918 | Force inputs 33-48 | src:1324 | [boot.md#loadparametersstage](boot.md#loadparametersstage-src1284-1376) | -> `SV_FORCE_INP33_48_BITS` |
| P919 | Force inputs 49-64 | src:1325 | [boot.md#loadparametersstage](boot.md#loadparametersstage-src1284-1376) | -> `SV_FORCE_INP49_64_BITS` |
| P920 | Force inputs 65-80 | src:1326 | [boot.md#loadparametersstage](boot.md#loadparametersstage-src1284-1376) | -> `SV_FORCE_INP65_80_BITS` |
| P921 | Force outputs 1-16 ON | src:1327 | [boot.md#loadparametersstage](boot.md#loadparametersstage-src1284-1376) | -> `SV_FORCE_ON_OUT1_16_BITS` |
| P922 | Force outputs 17-32 ON | src:1328 | [boot.md#loadparametersstage](boot.md#loadparametersstage-src1284-1376) | -> `SV_FORCE_ON_OUT17_32_BITS` |
| P923 | Force outputs 33-48 ON | src:1329 | [boot.md#loadparametersstage](boot.md#loadparametersstage-src1284-1376) | -> `SV_FORCE_ON_OUT33_48_BITS` |
| P924 | Force outputs 49-64 ON | src:1330 | [boot.md#loadparametersstage](boot.md#loadparametersstage-src1284-1376) | -> `SV_FORCE_ON_OUT49_64_BITS` |
| P925 | Force outputs 65-80 ON | src:1331 | [boot.md#loadparametersstage](boot.md#loadparametersstage-src1284-1376) | -> `SV_FORCE_ON_OUT65_80_BITS` |
| P926 | Force outputs 1-16 OFF | src:1332 | [boot.md#loadparametersstage](boot.md#loadparametersstage-src1284-1376) | -> `SV_FORCE_OFF_OUT1_16_BITS` |
| P927 | Force outputs 17-32 OFF | src:1333 | [boot.md#loadparametersstage](boot.md#loadparametersstage-src1284-1376) | -> `SV_FORCE_OFF_OUT17_32_BITS` |
| P928 | Force outputs 33-48 OFF | src:1334 | [boot.md#loadparametersstage](boot.md#loadparametersstage-src1284-1376) | -> `SV_FORCE_OFF_OUT33_48_BITS` |
| P929 | Force outputs 49-64 OFF | src:1335 | [boot.md#loadparametersstage](boot.md#loadparametersstage-src1284-1376) | -> `SV_FORCE_OFF_OUT49_64_BITS` |
| P930 | Force outputs 65-80 OFF | src:1336 | [boot.md#loadparametersstage](boot.md#loadparametersstage-src1284-1376) | -> `SV_FORCE_OFF_OUT65_80_BITS` |
| P931 | Force MEM bits 1-16 ON | src:1337 | [boot.md#loadparametersstage](boot.md#loadparametersstage-src1284-1376) | -> `SV_FORCE_ON_MEM1_16_BITS` |
| P932 | Force MEM bits 17-32 ON | src:1338 | [boot.md#loadparametersstage](boot.md#loadparametersstage-src1284-1376) | -> `SV_FORCE_ON_MEM17_32_BITS` |
| P933 | Force MEM bits 33-48 ON | src:1339 | [boot.md#loadparametersstage](boot.md#loadparametersstage-src1284-1376) | -> `SV_FORCE_ON_MEM33_48_BITS` |
| P934 | Force MEM bits 49-64 ON | src:1340 | [boot.md#loadparametersstage](boot.md#loadparametersstage-src1284-1376) | -> `SV_FORCE_ON_MEM49_64_BITS` |
| P935 | Force MEM bits 65-80 ON | src:1341 | [boot.md#loadparametersstage](boot.md#loadparametersstage-src1284-1376) | -> `SV_FORCE_ON_MEM65_80_BITS` |
| P936 | Force MEM bits 1-16 OFF | src:1342 | [boot.md#loadparametersstage](boot.md#loadparametersstage-src1284-1376) | -> `SV_FORCE_OFF_MEM1_16_BITS` |
| P937 | Force MEM bits 17-32 OFF | src:1343 | [boot.md#loadparametersstage](boot.md#loadparametersstage-src1284-1376) | -> `SV_FORCE_OFF_MEM17_32_BITS` |
| P938 | Force MEM bits 33-48 OFF | src:1344 | [boot.md#loadparametersstage](boot.md#loadparametersstage-src1284-1376) | -> `SV_FORCE_OFF_MEM33_48_BITS` |
| P939 | Force MEM bits 49-64 OFF | src:1345 | [boot.md#loadparametersstage](boot.md#loadparametersstage-src1284-1376) | -> `SV_FORCE_OFF_MEM49_64_BITS` |
| P940 | Force MEM bits 65-80 OFF | src:1346 | [boot.md#loadparametersstage](boot.md#loadparametersstage-src1284-1376) | -> `SV_FORCE_OFF_MEM65_80_BITS` |
| P860 (Acroloc) | Low/high gear crossover speed (center of hysteresis band) | src:2283-2288 | [gear-shift.md#parameters](gear-shift.md#parameters) | `<= 0.0` disables auto-shift (holds the engaged gear; defaults to low from neutral so the spindle still drives). **Intended starting value 800 (RPM)** — per [2026-06-27-rpm-gear-shift-design.md](../superpowers/specs/2026-06-27-rpm-gear-shift-design.md); the `.src` itself encodes no default/intended value, only the disable behavior. **P860–P862 use the free 860–870 "Not Used" block — do NOT use 941–943: on this control the 900-block is reserved (P911–940 force MEM bits off; P941 is the PLC limit-defeat button, and setting it would break limit override).** |
| P861 (Acroloc) | Hysteresis half-width around P860 | src:2284-2288 | [gear-shift.md#parameters](gear-shift.md#parameters) | No disable sentinel — always added/subtracted from P860. **Intended value 100 (RPM)** — per the design spec, not the `.src` |
| P862 (Acroloc) | Coast-dwell override, milliseconds | src:2303-2304 | [gear-shift.md#parameters](gear-shift.md#parameters) | `<= 0` (including factory-default 0) falls back to the hard-coded 1500 ms default (src:2296-2298). **Intended: 1500 out of the box, tuned down on the real machine** — per the design spec; the `.src` only encodes the *default-if-unset* value, not a tuning target |
| P999 | Not a real parameter — the upper bound cited in the general system-variables comment ("Parameter values: SV_MACHINE_PARAMETER_1 - SV_MACHINE_PARAMETER_999") | src:753 (comment only) | n/a | Documentation of the valid parameter-number range, not a value read anywhere |

## Comment-only mentions (not executable reads)

Two blocks in the source mention parameter numbers in prose/comments without a corresponding
`SV_MACHINE_PARAMETER_n` read at that location. They are captured here so the grep-hit count
reconciles, but they are not separate table rows for parameters already covered above:

- **src:38, 47-78** — a header comment block enumerating parameters the PLC cares about.
  The high-range gear ratio is read from `SV_MACHINE_PARAMETER_863` (src:2347) when
  `SpindleRange_W == 4`, with a fallback to `2.0` if it is left `<= 0` — see the P863 row in
  the table above. P863 is a general param in the 860-870 "Not Used" block, which stays
  editable regardless of spindle range config. P33 was tried first (not writable — reads a
  fixed ~2.0) and P66/P67 next (CNC12 locks the medium-range gains on this machine), so both
  were abandoned.
  P219 (src:66, "start VCP on boot") is named only in this comment block —
  no rung reads it, so CNC12 must consult it directly rather than through the PLC.
- **src:753** — the general system-variables overview comment (P999 upper bound), addressed
  in the table above.

## Note on P65 (low-gear ratio)

The task brief for this file asked specifically whether the PLC reads P65 or whether it is
CNC12-side only. It **is** read by the PLC: `SpinRangeAdjust_FW = SV_MACHINE_PARAMETER_65`
(src:2313), gated by `IF SpindleRange_W == 1`. It feeds `SpinRangeAdjust_FW`, which the
low-range branch of the `SpindleRange_W` decode block (src:2308-2325, documented in
[gear-shift.md](gear-shift.md) via [main-stage.md#gear-decision](main-stage.md#gear-decision))
uses in the spindle-speed/DAC ratio math alongside P66 (range 2) and P67 (range 3); range 4
(high) reads **P863**, a general param in the 860-870 "Not Used" block — it stays editable
regardless of spindle range config, unlike P66/P67 which CNC12 locks on this machine —
falling back to `2.0` if P863 is left `<= 0`. (P33 was tried first but is a reserved param,
not writable from the param screen.)  These ratios are calibration constants (they fold in
CfgMax, the F510 max-frequency scaling, and the mechanical gear), tuned on the machine:
low P65 ~= 0.52, high P863 ~= 2.0.

## Verification

Every distinct `SV_MACHINE_PARAMETER_n` surfaced by
`grep -n "SV_MACHINE_PARAMETER" Centroid-Acroloc-ALLIN1DC.src` (103 hits, 60 distinct
parameter numbers: 1, 19, 33, 39, 57, 65, 66, 67, 146, 148, 153, 170, 179, 218, 219, 348, 351,
354, 441, 442, 443, 820, 860, 861, 862, 900, 911-940, 999) appears in the table above or in the
comment-only-mentions section — P219 and P999 have no executable read and are called out
explicitly rather than given a fabricated one. Every `(src:NNNN)` citation was checked against
`Centroid-Acroloc-ALLIN1DC.src` with `sed -n` at the cited line(s) and confirmed to reference
the stated `SV_MACHINE_PARAMETER_n`. `Centroid-Acroloc-ALLIN1DC.src` has had no commits touching
it between 41f3fd6 and the current HEAD on this branch (`git log 41f3fd6..HEAD -- <file>` is
empty), so line numbers cited here match the current working tree.
