# PLC resource atlas (definitions)

One-line purpose: canonical name -> resource -> source-line table for every symbol bound in
the definitions half of `Centroid-Acroloc-ALLIN1DC.src`, so `main-stage.md`, `atc.md`,
`gear-shift.md`, `jog-and-mpg.md`, `faults-and-messages.md`, and `parameters.md` can cite a
symbol instead of redefining it.

Line numbers as of commit 41f3fd6

Suffix conventions (`_I`, `_O`, `_M`, `_W`, `_T`, `_SV`, `_C`, stages) are defined once in
[scan-model.md#naming-conventions](scan-model.md#naming-conventions) — not repeated here.
This file covers the definitions block, `Centroid-Acroloc-ALLIN1DC.src` lines 1-1221 (through
the last stage definition, `BadMsgStage IS STG94` at src:1221); `Program Start` begins at
src:1223.

> **Note (2026-07-10, oil-pump auto-control):** the stock lube-metering symbols
> `LubeAccumTime_W`, `Lube_W`, `LubeM_W`, `LubeS_W`, `LubeM_T`, `LubeS_T`,
> `StopRunningPD_PD`, `LubeUsePumpTimersStage`, and `LubeUsePLCTimersStage` were removed
> from the source (Parameter 179 retired; the oil pump is now driven by a `MainStage` coil),
> so their rows are dropped below. Line numbers here remain as of the pinned commit above and
> are not re-baselined for this removal.

## Message-constant encoding

Message constants (`_C`) pack a message *type* and *number* into one integer (the manual's
formula):

```
value = type + 256 * msgNumber
```

`type` is 1 (synchronous) or 2 (asynchronous); `msgNumber` is the entry number in the first
column of `plcmsg.txt`. For example `ATC_Lock_Released_C` (src:202) `IS 44546 ;(2+256*174)`
decodes as **type 2, msgNumber 174** — the "Tool Carousel locked" entry (line 174) in
`plcmsg.txt`. The message *text* is defined in this repo's `plcmsg.txt` (the PLC message file,
keyed by the first-column number) and loaded by CNC12; stock CNC12 system messages live in
CNC12's own message files, which are not tracked here. The comment
following each `_C` definition carries this `(type+256*msgNumber)` breakdown. (`CLAUDE.md`
writes the same formula with reversed field names, `msgNumber + 256*msgFile`, where its
`msgNumber` is this `type` and its `msgFile` is this `msgNumber`; see the
[centroid-plc-programming messages reference](../../.claude/skills/centroid-plc-programming/reference/messages.md).)

## Inputs

| Name | Resource | src line | Acroloc? | Meaning / used by |
|---|---|---|---|---|
| `Ax1_MinusLimitOk_I` | INP1 | 208 | | Axis 1 minus limit ok. [main-stage.md](main-stage.md) |
| `Ax1_PlusLimitOk_I` | INP2 | 209 | | Axis 1 plus limit ok. [main-stage.md](main-stage.md) |
| `Ax2_MinusLimitOk_I` | INP3 | 210 | | Axis 2 minus limit ok. [main-stage.md](main-stage.md) |
| `Ax2_PlusLimitOk_I` | INP4 | 211 | | Axis 2 plus limit ok. [main-stage.md](main-stage.md) |
| `Ax3_MinusLimitOk_I` | INP5 | 212 | | Axis 3 minus limit ok. [main-stage.md](main-stage.md) |
| `Ax3_PlusLimitOk_I` | INP6 | 213 | | Axis 3 plus limit ok. [main-stage.md](main-stage.md) |
| `RotaryTableHome_I` | INP7 | 214 | | Rotary table home switch. [main-stage.md](main-stage.md) |
| `DoorClosed_I` | INP8 | 215 | | Door interlock closed. [main-stage.md](main-stage.md) |
| `LubeOk_I` | INP9 | 216 | | Lube ok when closed. [main-stage.md](main-stage.md) |
| `SpindleInverterOk_I` | INP10 | 217 | | Spindle inverter ok when closed. [main-stage.md](main-stage.md) |
| `EStopOk_I` | INP11 | 218 | | E-stop circuit ok. [main-stage.md](main-stage.md) |
| `ZeroSpeed_I` | INP12 | 236 | | Spindle confirmed stopped (F510 VFD zero-speed output; wired and tested). Read by the changer feed-hold interlock and the `ATCStage` carousel guard. [main-stage.md](main-stage.md), [atc.md](atc.md) |
| `ATCManualUnlock_I` | INP24 | 226 | Acroloc | Front-panel manual unlock button. [atc.md](atc.md) |
| `ATCLocked_I` | INP25 | 227 | Acroloc | Piston sensor confirming carousel locked. [atc.md](atc.md) |
| `ATC_Z_ClearedToolChanger_I` | INP26 | 228 | Acroloc | Spindle has entered the tool changer (zero rpm). [atc.md](atc.md) |
| `ATC_Z_Zero_Release_I` | INP27 | 229 | Acroloc | Z axis has cleared the tool ring. [atc.md](atc.md) |
| `ATC_Pos5_I` | INP28 | 230 | Acroloc | Carousel position-switch bit 5 (adds 10, not 16 — base-16-as-decimal encoding). [atc.md](atc.md) |
| `ATC_Pos4_I` | INP29 | 231 | Acroloc | Carousel position-switch bit 4 (adds 8). [atc.md](atc.md) |
| `ATC_Pos3_I` | INP30 | 232 | Acroloc | Carousel position-switch bit 3 (adds 4). [atc.md](atc.md) |
| `ATC_Pos2_I` | INP31 | 233 | Acroloc | Carousel position-switch bit 2 (adds 2). [atc.md](atc.md) |
| `ATC_Pos1_I` | INP32 | 234 | Acroloc | Carousel position-switch bit 1 (adds 1). [atc.md](atc.md) |
| `AnalogIn1Bit0_I` .. `AnalogIn1Bit11_I` | INP241-252 | 237-248 | | 12-bit analog input (spindle speed feedback path). [main-stage.md](main-stage.md) |
| `AnalogIn1Bit12_I` .. `AnalogIn1Bit15_I` | INP253-256 | 249-252 | | Unused high bits of the 12-bit analog word (board provides 16, only 12 wired). [main-stage.md](main-stage.md) |
| `MechanicalProbe_I` | INP769 | 258 | | Mechanical probe input. [main-stage.md](main-stage.md) |
| `DSPProbe_I` | INP770 | 259 | | DSP probe input. [main-stage.md](main-stage.md) |
| `ProbeDetect_I` | INP771 | 260 | | Probe detect. [main-stage.md](main-stage.md) |
| `ProbeAux_I` | INP772 | 261 | | Probe aux input. [main-stage.md](main-stage.md) |
| `MPG_Inc_X_1_I` | INP773 | 262 | | Wireless MPG x1 increment select. [jog-and-mpg.md](jog-and-mpg.md) |
| `MPG_Inc_X_10_I` | INP774 | 263 | | Wireless MPG x10 increment select. [jog-and-mpg.md](jog-and-mpg.md) |
| `MPG_Inc_X_100_I` | INP775 | 264 | | Wireless MPG x100 increment select. [jog-and-mpg.md](jog-and-mpg.md) |
| `MPG_AXIS_1_I` .. `MPG_AXIS_8_I` | INP776-783 | 265-272 | | Wireless MPG axis-select bits. [jog-and-mpg.md](jog-and-mpg.md) |
| `SpinOverPlusKey_I` | INP1057 | 280 | | Jog panel row 1 col 1 — spindle override +. [jog-and-mpg.md](jog-and-mpg.md) |
| `SpinAutoManKey_I` | INP1058 | 281 | | Jog panel row 1 col 2 — spindle auto/man. [jog-and-mpg.md](jog-and-mpg.md) |
| `Aux1Key_I` .. `Aux3Key_I` | INP1059-1061 | 282-284 | | Jog panel row 1 aux keys. [jog-and-mpg.md](jog-and-mpg.md) |
| `SpinOver100Key_I` | INP1062 | 286 | | Jog panel row 2 col 1 — spindle override 100%. [jog-and-mpg.md](jog-and-mpg.md) |
| `SpinCWKey_I` | INP1063 | 287 | | Jog panel row 2 col 2 — spindle CW. [jog-and-mpg.md](jog-and-mpg.md) |
| `Aux4Key_I` .. `Aux6Key_I` | INP1064-1066 | 288-290 | | Jog panel row 2 aux keys. [jog-and-mpg.md](jog-and-mpg.md) |
| `SpinOverMinusKey_I` | INP1067 | 292 | | Jog panel row 3 col 1 — spindle override -. [jog-and-mpg.md](jog-and-mpg.md) |
| `SpinCCWKey_I` | INP1068 | 293 | | Jog panel row 3 col 2 — spindle CCW. [jog-and-mpg.md](jog-and-mpg.md) |
| `Aux7Key_I` .. `Aux9Key_I` | INP1069-1071 | 294-296 | | Jog panel row 3 aux keys. [jog-and-mpg.md](jog-and-mpg.md) |
| `SpinStopKey_I` | INP1072 | 298 | | Jog panel row 4 col 1 — spindle stop. [jog-and-mpg.md](jog-and-mpg.md) |
| `SpinStartKey_I` | INP1073 | 299 | | Jog panel row 4 col 2 — spindle start. [jog-and-mpg.md](jog-and-mpg.md) |
| `Aux10Key_I` .. `Aux12Key_I` | INP1074-1076 | 300-302 | | Jog panel row 4 aux keys. [jog-and-mpg.md](jog-and-mpg.md) |
| `CoolAutoManKey_I` | INP1077 | 304 | | Jog panel row 5 col 1 — coolant auto/man. [jog-and-mpg.md](jog-and-mpg.md) |
| `CoolFloodKey_I` | INP1078 | 305 | | Jog panel row 5 col 2 — flood. [jog-and-mpg.md](jog-and-mpg.md) |
| `CoolMistKey_I` | INP1079 | 306 | | Jog panel row 5 col 3 — mist. [jog-and-mpg.md](jog-and-mpg.md) |
| `Aux13Key_I`, `Aux14Key_I` | INP1080-1081 | 307-308 | | Jog panel row 5 aux keys. [jog-and-mpg.md](jog-and-mpg.md) |
| `IncrContKey_I` | INP1082 | 310 | | Jog panel row 6 col 1 — incremental/continuous. [jog-and-mpg.md](jog-and-mpg.md) |
| `x1JogKey_I`, `x10JogKey_I`, `x100JogKey_I` | INP1083-1085 | 311-313 | | Jog panel row 6 increment selects. [jog-and-mpg.md](jog-and-mpg.md) |
| `MPGKey_I` | INP1086 | 314 | | Jog panel row 6 col 5 — MPG mode select. [jog-and-mpg.md](jog-and-mpg.md) |
| `Ax4PlusJogKey_I` | INP1087 | 316 | | Jog panel row 7 col 1. [jog-and-mpg.md](jog-and-mpg.md) |
| `UnusedR7C2Key_I` | INP1088 | 317 | | Unpopulated jog panel key. [jog-and-mpg.md](jog-and-mpg.md) |
| `Ax2PlusJogKey_I` | INP1089 | 318 | | Jog panel row 7 col 3. [jog-and-mpg.md](jog-and-mpg.md) |
| `UnusedR7C4Key_I` | INP1090 | 319 | | Unpopulated jog panel key. [jog-and-mpg.md](jog-and-mpg.md) |
| `Ax3PlusJogKey_I` | INP1091 | 320 | | Jog panel row 7 col 5. [jog-and-mpg.md](jog-and-mpg.md) |
| `UnusedR8C1Key_I` | INP1092 | 322 | | Unpopulated jog panel key. [jog-and-mpg.md](jog-and-mpg.md) |
| `Ax1MinusJogKey_I` | INP1093 | 323 | | Jog panel row 8 col 2. [jog-and-mpg.md](jog-and-mpg.md) |
| `FastSlowKey_I` | INP1094 | 324 | | Jog panel row 8 col 3 — fast/slow jog. [jog-and-mpg.md](jog-and-mpg.md) |
| `Ax1PlusJogKey_I` | INP1095 | 325 | | Jog panel row 8 col 4. [jog-and-mpg.md](jog-and-mpg.md) |
| `UnusedR8C5Key_I` | INP1096 | 326 | | Unpopulated jog panel key. [jog-and-mpg.md](jog-and-mpg.md) |
| `Ax4MinusJogKey_I` | INP1097 | 328 | | Jog panel row 9 col 1. [jog-and-mpg.md](jog-and-mpg.md) |
| `UnusedR9C2Key_I` | INP1098 | 329 | | Unpopulated jog panel key. [jog-and-mpg.md](jog-and-mpg.md) |
| `Ax2MinusJogKey_I` | INP1099 | 330 | | Jog panel row 9 col 3. [jog-and-mpg.md](jog-and-mpg.md) |
| `UnusedR9C4Key_I` | INP1100 | 331 | | Unpopulated jog panel key. [jog-and-mpg.md](jog-and-mpg.md) |
| `Ax3MinusJogKey_I` | INP1101 | 332 | | Jog panel row 9 col 5. [jog-and-mpg.md](jog-and-mpg.md) |
| `CycleCancelKey_I` | INP1102 | 334 | | Jog panel row 10 col 1. [jog-and-mpg.md](jog-and-mpg.md) |
| `SingleBlockKey_I` | INP1103 | 335 | | Jog panel row 10 col 2. [jog-and-mpg.md](jog-and-mpg.md) |
| `ToolCheckKey_I` | INP1104 | 336 | | Jog panel row 10 col 3. [jog-and-mpg.md](jog-and-mpg.md) |
| `FeedHoldKey_I` | INP1105 | 337 | | Jog panel row 10 col 4. [jog-and-mpg.md](jog-and-mpg.md) |
| `CycleStartKey_I` | INP1106 | 338 | | Jog panel row 10 col 5. [jog-and-mpg.md](jog-and-mpg.md) |
| `Aux15Key_I`, `Aux16Key_I` | INP1110-1111 | 341-342 | | No physical key available. [jog-and-mpg.md](jog-and-mpg.md) |
| `JpFeedOrKnobBit0_I` .. `JpFeedOrKnobBit8_I` | INP1249-1257 | 347-355 | | Feedrate override knob bits 0-8 (current jog panels send only these). [jog-and-mpg.md](jog-and-mpg.md) |
| `JpFeedOrKnobBit9_I` .. `JpFeedOrKnobBit15_I` | INP1258-1264 | 356-362 | | Feedrate override knob bits 9-15, unused. [jog-and-mpg.md](jog-and-mpg.md) |

## Outputs

| Name | Resource | src line | Acroloc? | Meaning / used by |
|---|---|---|---|---|
| `NoFaultOut_O` | OUT1 | 368 | | "No fault" indicator, SPST. [main-stage.md](main-stage.md) |
| `Lube_O` | OUT2 | 369 | | Oil pump, SPST — driven by the `MainStage` oil-pump coil. [main-stage.md](main-stage.md) |
| `FloodValve_O` | OUT3 | 370 | Acroloc | Flood valve — opens the coolant pump to the workspace nozzles; SPST. [main-stage.md](main-stage.md) |
| `CoolantPump_O` | OUT4 | 371 | Acroloc | Coolant pump — pressurizes coolant (+valve = flood nozzles, no valve = cleaning hose); SPST. [main-stage.md](main-stage.md) |
| `InverterResetOut_O` | OUT5 | 372 | | Spindle inverter reset, SPST. [main-stage.md](main-stage.md) |
| `WorkLightOut_O` | OUT6 | 373 | | Work light, SPST. [main-stage.md](main-stage.md) |
| `SpindleEnableOut_O` | OUT7 | 374 | | Spindle enable, SPST. [main-stage.md](main-stage.md) |
| `SpindleDirectionOut_O` | OUT8 | 375 | | Spindle direction, SPDT. [main-stage.md](main-stage.md) |
| `ZBrakeRelease_O` | OUT9 | 376 | | Z brake release, SPDT. [main-stage.md](main-stage.md) |
| `ATCMotor_O` | OUT17 | 382 | Acroloc | Spins the tool carousel. [atc.md](atc.md) |
| `ATCUnlocked_O` | OUT18 | 383 | Acroloc | Unlocks the tool carousel. [atc.md](atc.md) |
| `Spindle_Low_gear_O` | OUT19 | 384 | Acroloc | Low-gear clutch; high gear must be released first. [gear-shift.md](gear-shift.md) |
| `Spindle_High_gear_O` | OUT20 | 385 | Acroloc | High-gear clutch; low gear must be released first. [gear-shift.md](gear-shift.md) |
| `SpinAnalogOutBit0_O` .. `SpinAnalogOutBit11_O` | OUT241-252 | 390-401 | | 12-bit analog spindle-speed output (0-10VDC). [main-stage.md](main-stage.md) |
| `MPG_LED_OUT_O` | OUT769 | 403 | | Wireless MPG LED. [jog-and-mpg.md](jog-and-mpg.md) |
| `SpinOverPlusLED_O` .. `Aux3LED_O` | OUT1057-1061 | 413-417 | | Jog panel row 1 LEDs. [jog-and-mpg.md](jog-and-mpg.md) |
| `SpinOver100LED_O` .. `Aux6LED_O` | OUT1062-1066 | 419-423 | | Jog panel row 2 LEDs. [jog-and-mpg.md](jog-and-mpg.md) |
| `SpinOverMinusLED_O` .. `Aux9LED_O` | OUT1067-1071 | 425-429 | | Jog panel row 3 LEDs. [jog-and-mpg.md](jog-and-mpg.md) |
| `SpinStopLED_O` .. `Aux12LED_O` | OUT1072-1076 | 431-435 | | Jog panel row 4 LEDs. [jog-and-mpg.md](jog-and-mpg.md) |
| `CoolAutoModeLED_O` .. `Aux14LED_O` | OUT1077-1081 | 437-441 | | Jog panel row 5 LEDs. [jog-and-mpg.md](jog-and-mpg.md) |
| `IncrContLED_O` .. `MPGLED_O` | OUT1082-1086 | 443-447 | | Jog panel row 6 LEDs. [jog-and-mpg.md](jog-and-mpg.md) |
| `Ax4PlusJogLED_O` .. `Ax3PlusJogLED_O` | OUT1087-1091 | 449-453 | | Jog panel row 7 LEDs. [jog-and-mpg.md](jog-and-mpg.md) |
| `UnusedR8C1LED_O` .. `UnusedR8C5LED_O` | OUT1092-1096 | 455-459 | | Jog panel row 8 LEDs. [jog-and-mpg.md](jog-and-mpg.md) |
| `Ax4MinusJogLED_O` .. `Ax3MinusJogLED_O` | OUT1097-1101 | 461-465 | | Jog panel row 9 LEDs. [jog-and-mpg.md](jog-and-mpg.md) |
| `CycleCancelLED_O`, `SingleBlockLED_O`, `ToolCheckLED_O`, `FeedHoldLED_O` | OUT1102-1105 | 467-470 | | Jog panel row 10 LEDs. [jog-and-mpg.md](jog-and-mpg.md) |
| `SkinResetSet_O` | OUT1107 | 473 | | VCP 2.0 reset button LED. [jog-and-mpg.md](jog-and-mpg.md) |
| `FeedOver100LED_O` .. `FeedOver25LED_O` | OUT1137-1140 | 474-477 | | VCP 2.0 feed override LEDs. [jog-and-mpg.md](jog-and-mpg.md) |

## Memory bits

| Name | Resource | src line | Acroloc? | Meaning / used by |
|---|---|---|---|---|
| `PLCExecutorFault_M` | MEM1 | 482 | | PLC executor fault latch. [faults-and-messages.md](faults-and-messages.md) |
| `SoftwareNotReady_M` | MEM2 | 483 | | 0 = okay, 1 = CNC11 not running/ready. [faults-and-messages.md](faults-and-messages.md) |
| `MPGManOffFlag_M` | MEM3 | 484 | | MPG manual-off flag. [jog-and-mpg.md](jog-and-mpg.md) |
| `SafetySwitch_M` | MEM29 | 486 | | Safety switch (door interlock) state. [main-stage.md](main-stage.md) |
| `SafetySwitchToolCheck_M` | MEM30 | 487 | | Safety switch tool-check state. [main-stage.md](main-stage.md) |
| `MasterEnable_M` | MEM40 | 489 | | Echo of `SV_MASTER_ENABLE`. [main-stage.md](main-stage.md) |
| `PLCBus_Oe_M` | MEM41 | 490 | | 1 = okay, 0 = incoming PLC fiber problem. [faults-and-messages.md](faults-and-messages.md) |
| `PLCBusExtDevEn_M` | MEM42 | 491 | | 1 = okay, 0 = PLC reports bad output fiber. [faults-and-messages.md](faults-and-messages.md) |
| `JogLinkOk_M` | MEM43 | 492 | | 1 = okay, 0 = incoming jog panel data problem. [faults-and-messages.md](faults-and-messages.md) |
| `JogPanelOnline_M` | MEM44 | 493 | | 1 = okay, 0 = JogBoard reports bad connection. [faults-and-messages.md](faults-and-messages.md) |
| `ActivateFeedHold_M` | MEM45 | 494 | | 0 = idle, 1 = trigger feed hold on. [main-stage.md](main-stage.md) |
| `ErrorFlag_M` | MEM46 | 495 | | 0 = okay, 1 = error (not a fault). [faults-and-messages.md](faults-and-messages.md) |
| `Stop_M` | MEM47 | 496 | | Echo of `SV_STOP`. [main-stage.md](main-stage.md) |
| `Stall_M` | MEM48 | 497 | | Echo of `SV_STALL_ERROR`. [main-stage.md](main-stage.md) |
| `LubeFault_M` | MEM49 | 498 | | 0 = okay, 1 = `Lube_O` fault. [faults-and-messages.md](faults-and-messages.md) |
| `PLCFault_M` | MEM50 | 499 | | 0 = okay, 1 = PLC fault. [faults-and-messages.md](faults-and-messages.md) |
| `AxisFault_M` | MEM51 | 500 | | 0 = okay, 1 = drive or drive-fiber problem. [faults-and-messages.md](faults-and-messages.md) |
| `DriveComFltIn_M` | MEM52 | 501 | | 0 = okay, 1 = incoming drive fiber problem. [faults-and-messages.md](faults-and-messages.md) |
| `DriveComFltOut_M` | MEM53 | 502 | | 0 = okay, 1 = outgoing drive fiber problem. [faults-and-messages.md](faults-and-messages.md) |
| `ProbeFault_M` | MEM54 | 503 | | 0 = okay, 1 = tried to start spindle w/probe. [faults-and-messages.md](faults-and-messages.md) |
| `JogProbeFault_M` | MEM55 | 504 | | 0 = okay, 1 = tripped probe while jogging. [faults-and-messages.md](faults-and-messages.md) |
| `SpindleFault_M` | MEM56 | 505 | | 0 = okay, 1 = spindle drive fault. [faults-and-messages.md](faults-and-messages.md) |
| `OtherFault_M` | MEM57 | 506 | | Other fault catch-all. [faults-and-messages.md](faults-and-messages.md) |
| `ProbeMsgSent_M` | MEM78 | 517 | | Probe message sent latch. [faults-and-messages.md](faults-and-messages.md) |
| `True_M` | MEM81 | 518 | | Always-true bit. [scan-model.md](scan-model.md) |
| `SpinRangeReversed_M` | MEM82 | 519 | | Set when `SpinRangeAdjust_FW` is negative (reversed range ratio). [main-stage.md](main-stage.md) |
| `SpindleDirection_M` | MEM83 | 520 | | Commanded spindle direction. [main-stage.md](main-stage.md) |
| `SpindlePause_M` | MEM84 | 521 | | Spindle pause flag. [main-stage.md](main-stage.md) |
| `LimitTripped_M` | MEM85 | 522 | | A travel limit tripped. [main-stage.md](main-stage.md) |
| `SpinStart_M` | MEM86 | 523 | | Spindle start request. [main-stage.md](main-stage.md) |
| `SpinStop_M` | MEM87 | 524 | | Spindle stop request. [main-stage.md](main-stage.md) |
| `BadCfg_M` | MEM88 | 526 | | Bad configuration flag. [faults-and-messages.md](faults-and-messages.md) |
| `UpdatingConfig_M` | MEM89 | 527 | | Configuration update in progress. [parameters.md](parameters.md) |
| `ConfigFaultTrigger_M` | MEM90 | 528 | | Configuration fault trigger. [faults-and-messages.md](faults-and-messages.md) |
| `ClampEnabled_M` | MEM91 | 529 | | Clamp enabled (M10). [main-stage.md](main-stage.md) |
| `KbJpActive_M` | MEM100 | 531 | | aka `SV_PC_VIRTUAL_JOGPANEL_ACTIVE`. [jog-and-mpg.md](jog-and-mpg.md) |
| `DisableKbInput_M` | MEM101 | 532 | | If 1, disable keyboard jogging. [jog-and-mpg.md](jog-and-mpg.md) |
| `AllowKbInput_M` | MEM102 | 533 | | If 1, allow keyboard jogging. [jog-and-mpg.md](jog-and-mpg.md) |
| `JogOverOnly_M` | MEM103 | 534 | | Jog-override-only mode. [jog-and-mpg.md](jog-and-mpg.md) |
| `KbOverOnly_M` | MEM104 | 535 | | Keyboard-override-only mode. [jog-and-mpg.md](jog-and-mpg.md) |
| `UsingFeedrateKnob_M` | MEM105 | 536 | | Feedrate knob currently in use. [jog-and-mpg.md](jog-and-mpg.md) |
| `WaitingForSleepTimer_M` | MEM106 | 537 | | Waiting on `SleepTimer_T`. [scan-model.md](scan-model.md) |
| `JogPanelRequired_M` | MEM107 | 538 | | Jog panel required flag. [jog-and-mpg.md](jog-and-mpg.md) |
| `UsingVirtualOverride_M` | MEM108 | 539 | | Virtual override in use. [jog-and-mpg.md](jog-and-mpg.md) |
| `X1_M`, `X10_M`, `X100_M` | MEM111-113 | 541-543 | | Jog increment selection. [jog-and-mpg.md](jog-and-mpg.md) |
| `MiniPLCOk1_M` .. `MiniPLCOk8_M` | MEM121-128 | 546-553 | | Mini-PLC (expansion) comm ok, 8 bits. [faults-and-messages.md](faults-and-messages.md) |
| `MiniPLCExpected1_M` .. `MiniPLCExpected8_M` | MEM137-144 | 556-563 | | Mini-PLC expected-present config, 8 bits. [faults-and-messages.md](faults-and-messages.md) |
| `Ax1PlusJogDisabled_M` .. `Ax8MinusJogDisabled_M` | MEM150-164 | 565-579 | | Per-axis, per-direction jog disable flags. [jog-and-mpg.md](jog-and-mpg.md) |
| `OnAtPowerUp_M` | MEM200 | 581 | | Power-up state flag. [main-stage.md](main-stage.md) |
| `EstopOk_M` | MEM201 | 582 | | E-stop ok latch. [main-stage.md](main-stage.md) |
| `ResetArmed_M` | MEM202 | 583 | | Reset armed flag. [main-stage.md](main-stage.md) |
| `ResetSet_M` | MEM203 | 584 | | Reset set flag. [main-stage.md](main-stage.md) |
| `LastProbeMode_M` | MEM210 | 586 | | Last probe mode. [main-stage.md](main-stage.md) |
| `JogModeSaved_M` | MEM211 | 587 | | Saved jog mode. [jog-and-mpg.md](jog-and-mpg.md) |
| `JogKeyPressed_M` | MEM212 | 588 | | A jog key is currently pressed. [jog-and-mpg.md](jog-and-mpg.md) |
| `ProbeProtectionEnable_M` | MEM213 | 589 | | Probe protection enabled (parameter 153). [parameters.md](parameters.md) |
| `InvertXJogKeys_M` | MEM214 | 590 | | Invert axis-2 jog keys (parameter 1). [parameters.md](parameters.md) |
| `SwapAxes_M` | MEM215 | 591 | | Swap axis-1/axis-2 jog keys (parameter 1). [parameters.md](parameters.md) |
| `MPG_M` | MEM216 | 592 | | MPG mode active. [jog-and-mpg.md](jog-and-mpg.md) |
| `HandWheel_M` | MEM217 | 593 | | Handwheel active. [jog-and-mpg.md](jog-and-mpg.md) |
| `MpgResetKey_M` .. `MpgSetAxisZero_M` | MEM230-242 | 598-610 | | Wired MPG key/function bits. [jog-and-mpg.md](jog-and-mpg.md) |
| `UsbMpgAxis1Active_M` .. `UsbMpgAxis8Active_M` | MEM243-250 | 612-619 | | Wireless MPG per-axis active bits. [jog-and-mpg.md](jog-and-mpg.md) |
| `UsbMpgSpinOnOffPressed_M` .. `UsbMpgAxis8JogMinus_M` | MEM254-285 | 622-653 | | Wireless MPG glue logic (spin on/off, axis select/jog). [jog-and-mpg.md](jog-and-mpg.md) |
| `UsbMpgOn_M` | MEM286 | 654 | | Wireless MPG powered on. [jog-and-mpg.md](jog-and-mpg.md) |
| `UsbAxisKnobChanged_M` | MEM287 | 655 | | Wireless MPG axis knob changed. [jog-and-mpg.md](jog-and-mpg.md) |
| `MpgX100LockOut_M` | MEM288 | 656 | | Z-axis x100 lockout (parameter 19). [parameters.md](parameters.md) |
| `MpgZAxisLocked_M` | MEM289 | 657 | | Z-axis MPG locked. [jog-and-mpg.md](jog-and-mpg.md) |
| `KbCycleStart_M` .. `KbAux16Key_M` | MEM400-447 (see note; excludes the two out-of-sequence bindings listed next) | 660-707 | | Keyboard jog/function key latches. [jog-and-mpg.md](jog-and-mpg.md) |
| `KbFeedOver100_M` | MEM450 | 668 | | Keyboard feed override 100% — "ctrl" + "\\" (bound out of numeric sequence inside the Kb block). [jog-and-mpg.md](jog-and-mpg.md) |
| `KbMistOnOff_M` | MEM451 | 698 | | Keyboard mist on/off — "ctrl" + "k" (bound out of numeric sequence inside the Kb block). [jog-and-mpg.md](jog-and-mpg.md) |
| `InToolSelect_M` | MEM443 | 710 | Acroloc | 0 = false, 1 = true — carousel currently accumulating a position ID. [atc.md](atc.md) |
| `ToolSelected_M` | MEM444 | 711 | Acroloc | 0 = false, 1 = true — carousel has matched the target tool. [atc.md](atc.md) |
| `ChangerHoldActive_M` | MEM448 | 729 | Acroloc | Latched while feed is held and the interlock waits for `ZeroSpeed_I`. [main-stage.md](main-stage.md) |
| `ChangerHoldDone_M` | MEM449 | 730 | Acroloc | Once-per-entry latch (set on resume *and* on fault); blocks re-arming until Z clears the changer. [main-stage.md](main-stage.md) |

Note: `MEM444` is bound to two different names in source — `KbAux13Key_M` (src:704, "ctrl"+"1")
and `ToolSelected_M` (src:711, Acroloc ATC tool-matched flag). This is a real address
collision in `Centroid-Acroloc-ALLIN1DC.src`, not a transcription artifact of this doc; verify
with `sed -n '704p;711p' Centroid-Acroloc-ALLIN1DC.src`. Anything touching keyboard Aux-13 or
the ATC tool-select flag should be aware both features write/read the same bit.

## Words

| Name | Resource | src line | Acroloc? | Meaning / used by |
|---|---|---|---|---|
| `KbOverride_W` | W2 | 1047 | | Keyboard feed override value. [jog-and-mpg.md](jog-and-mpg.md) |
| `FeedrateKnob_W` | W3 | 1048 | | Feedrate override knob value. [jog-and-mpg.md](jog-and-mpg.md) |
| `FinalFeedOverride_W` | W4 | 1049 | | Final feed override sent to CNC. [jog-and-mpg.md](jog-and-mpg.md) |
| `Last_FeedrateKnob_W` | W5 | 1051 | | Previous feedrate knob value. [jog-and-mpg.md](jog-and-mpg.md) |
| `CycloneStatus_W` | W6 | 1052 | | Cyclone (drive) status word. [faults-and-messages.md](faults-and-messages.md) |
| `TwelveBitSpeed_W` | W7 | 1053 | | 12-bit spindle speed DAC value. [main-stage.md](main-stage.md) |
| `UsbAxisMonitor_W` | W34 | 1055 | | Wireless MPG axis monitor. [jog-and-mpg.md](jog-and-mpg.md) |
| `UsbScaleMonitor_W` | W35 | 1056 | | Wireless MPG scale monitor. [jog-and-mpg.md](jog-and-mpg.md) |
| `UsbJog_W` | W36 | 1057 | | Wireless MPG jog value. [jog-and-mpg.md](jog-and-mpg.md) |
| `JogKeyCfg_W` | W37 | 1058 | | Jog key configuration word. [jog-and-mpg.md](jog-and-mpg.md) |
| `UsbButtonMonitor_W` | W38 | 1059 | | Wireless MPG button monitor. [jog-and-mpg.md](jog-and-mpg.md) |
| `UsbWheelCurrent_W` | W39 | 1060 | | Wireless MPG wheel current value. [jog-and-mpg.md](jog-and-mpg.md) |
| `UsbWheelLast_W` | W40 | 1061 | | Wireless MPG wheel last value. [jog-and-mpg.md](jog-and-mpg.md) |
| `UsbWheelDelta_W` | W41 | 1062 | | Wireless MPG wheel delta. [jog-and-mpg.md](jog-and-mpg.md) |
| `UsbMpgActiveAxes_W` | W42 | 1063 | | Wireless MPG active-axes bitmask. [jog-and-mpg.md](jog-and-mpg.md) |
| `DefaultJogging_W` | W43 | 1064 | | Default jogging mode word. [jog-and-mpg.md](jog-and-mpg.md) |
| `StallReason_W` | W44 | 1065 | | Stall reason code. [faults-and-messages.md](faults-and-messages.md) |
| `StallAxis_W` | W45 | 1066 | | Stalled axis number. [faults-and-messages.md](faults-and-messages.md) |
| `FaultMsg_W` | W51 | 1068 | | Fault message constant to display. [faults-and-messages.md](faults-and-messages.md) |
| `ErrorMsg_W` | W52 | 1069 | | Error message constant to display. [faults-and-messages.md](faults-and-messages.md) |
| `InfoMsg_W` | W53 | 1070 | | Info message constant to display. [faults-and-messages.md](faults-and-messages.md) |
| `PLC_Fault_W` | W54 | 1071 | | Raw `SV_PLC_FAULT_STATUS` snapshot. [faults-and-messages.md](faults-and-messages.md) |
| `PLCFaultAddr_W` | W55 | 1072 | | Raw `SV_PLC_FAULT_ADDRESS` snapshot. [faults-and-messages.md](faults-and-messages.md) |
| `SpindleMeter_W` | W59 | 1074 | | Spindle load meter value. [main-stage.md](main-stage.md) |
| `SpindleRange_W` | W64 | 1079 | | 1 = low ... 4 = high, range reported to CNC. [gear-shift.md](gear-shift.md) |
| `DesiredRange_W` | W73 | 1080 | Acroloc | Gear wanted by RPM logic (1 = low, 4 = high). [gear-shift.md](gear-shift.md) |
| `EngagedRange_W` | W74 | 1081 | Acroloc | Gear currently engaged (open-loop, tracks clutch outputs; 0 = unknown/forced-neutral, see src:2397-2402). [gear-shift.md](gear-shift.md) |
| `PrevFeedOverride_W` | W65 | 1086 | | Previous feed override value. [jog-and-mpg.md](jog-and-mpg.md) |
| `P148Value_W` | W66 | 1087 | | Cached `SV_MACHINE_PARAMETER_148`. [parameters.md](parameters.md) |
| `P146Value_W` | W67 | 1088 | | Cached `SV_MACHINE_PARAMETER_146`. [parameters.md](parameters.md) |
| `P170Value_W` | W68 | 1089 | | Cached `SV_MACHINE_PARAMETER_170`. [parameters.md](parameters.md) |
| `P900Value_W` | W69 | 1090 | | Cached `SV_MACHINE_PARAMETER_900`. [parameters.md](parameters.md) |
| `MiniPLCStatus_W` | W70 | 1091 | | Mini-PLC status word. [faults-and-messages.md](faults-and-messages.md) |
| `CarouselToolID_W` | W71 | 1093 | Acroloc | Per-group **peak** of the position-switch sum = the settled tool ID (base-16 encoded as decimal across the 5 switches); compared to `ChangeToTool_W`. [atc.md](atc.md) |
| `ChangeToTool_W` | W72 | 1094 | Acroloc | Target tool ID latched from `M6`. [atc.md](atc.md) |
| `InstToolID_W` | W75 | 1113 | Acroloc | Instantaneous position-switch sum, rebuilt each scan; its per-group peak is latched into `CarouselToolID_W`. [atc.md](atc.md) |
| `SpinOverride_W` | W76 | 1114 | Acroloc | Mirror of `SV_PLC_SPINDLE_KNOB` (spindle override %), refreshed every scan so the VCP's seven-segment SPIN % readout can display it as `plc_word` 76. [main-stage.md](main-stage.md) |
| `PValue_W` | W92 | 1096 | | Scratch parameter value. [parameters.md](parameters.md) |

### Float words (FW)

| Name | Resource | src line | Acroloc? | Meaning / used by |
|---|---|---|---|---|
| `SpinRangeAdjust_FW` | FW1 | 1101 | | Spindle range ratio (from `SV_MACHINE_PARAMETER_65/66/67`, or 1.0). [main-stage.md](main-stage.md) |
| `RPMPerBit_FW` | FW2 | 1102 | | RPM-per-DAC-bit scale factor. [main-stage.md](main-stage.md) |
| `CfgMinSpeed_FW` | FW3 | 1103 | | Configured minimum spindle speed. [main-stage.md](main-stage.md) |
| `CfgMaxSpeed_FW` | FW4 | 1104 | | Configured maximum spindle speed. [main-stage.md](main-stage.md) |
| `TwelveBitSpeed_FW` | FW5 | 1105 | | 12-bit DAC speed value, float form. [main-stage.md](main-stage.md) |
| `SpinSpeedCommand_FW` | FW6 | 1106 | | Commanded spindle speed, clamped to min/max. [main-stage.md](main-stage.md) |
| `GearBaseSpeed_FW` | FW7 | 1107 | Acroloc | Un-overridden commanded S (override knob backed out); drives gear-shift crossover decision. [gear-shift.md](gear-shift.md) |

### One-shot bits (PD)

Pulse-detect (one-shot) bits, `PD1`-`PD58`, defined at src:1112-1166. None are tagged
`; Acroloc`; they belong to stock jog-panel/keyboard/coolant/spindle edge-detection logic
(`IncrContPD_PD`, `SlowFastPD_PD`, `MpgPD_PD`, ... `SkinFeedOverPlusPD_PD`). See
[jog-and-mpg.md](jog-and-mpg.md) and [main-stage.md](main-stage.md) for their consuming
logic; not itemized row-by-row here since none carry Acroloc-specific meaning or cross-file
significance beyond "one-shot edge of the same-named key/event".

## Timers

| Name | Resource | src line | Acroloc? | Meaning / used by |
|---|---|---|---|---|
| `MsgClear_T` | T1 | 1173 | | Message-clear timer. [faults-and-messages.md](faults-and-messages.md) |
| `SleepTimer_T` | T2 | 1174 | | Sleep timer. [scan-model.md](scan-model.md) |
| `CycloneStatus_T` | T3 | 1175 | | Cyclone status poll timer. [faults-and-messages.md](faults-and-messages.md) |
| `Initialize_T` | T4 | 1176 | | Initialization timer. [boot.md](boot.md) |
| `ErrorFlag_T` | T5 | 1177 | | Error-flag timer. [faults-and-messages.md](faults-and-messages.md) |
| `TriggerPause_T` | T6 | 1178 | | Trigger-pause timer. [main-stage.md](main-stage.md) |
| `SkinFeedOverTimer_T` | T15 | 1182 | | Skin feed-override timer. [jog-and-mpg.md](jog-and-mpg.md) |
| `OverrideMsgTimer_T` | T16 | 1183 | | Override message timer. [faults-and-messages.md](faults-and-messages.md) |
| `MessageTimer_T` | T17 | 1184 | | Message display timer. [faults-and-messages.md](faults-and-messages.md) |
| `NoMacroKeyPressedTimer_T` | T18 | 1185 | | No-macro-key-pressed timer (WMPG macro key reset delay). [jog-and-mpg.md](jog-and-mpg.md) |
| `ChangerStopTimer_T` | T23 | 1206 | Acroloc | 5 s timeout backstop for the spindle-in-changer feed-hold interlock; faults if the spindle never reaches zero. Renamed from `StopSpinBeforATC_T` (which was dead — armed, never read). Set point assigned at arm time, not at boot. [main-stage.md](main-stage.md), [atc.md](atc.md) |
| `ATCSpin_T` | T24 | 1188 | Acroloc | Carousel search watchdog: armed at M6 kickoff (`= ATC_SPIN_TIMEOUT_MS_C`, 20 s); if the tool is never matched, `ATCStage` faults `CAROUSEL MOVE TIME OUT`. [atc.md](atc.md#search-timeout) |
| `GearCoast_T` | T25 | 1189 | Acroloc | Gear-shift coast dwell (neutral) before engaging the new gear; loaded from `SV_MACHINE_PARAMETER_943` or a 1500ms default. [gear-shift.md](gear-shift.md) |

## System variables

| Name | Resource | src line | Acroloc? | Meaning / used by |
|---|---|---|---|---|
| `DoCycleCancel_SV` .. `DoAux16Key_SV` | `SV_PLC_FUNCTION_1`-`_117` | 770-822 | | Jog-panel function outputs (cycle cancel/start, jog, aux keys, spindle/coolant/feed-override commands). [jog-and-mpg.md](jog-and-mpg.md) |
| `Kb_a_SV` .. `Kb_Backslash_SV` | `SV_PC_KEYBOARD_KEY_*` | 845-940 | | PC keyboard keypress identifiers. [jog-and-mpg.md](jog-and-mpg.md) |
| `SkinSpinOverPlus_M_SV` .. `SkinFeedOver25_SV` | `SV_SKIN_EVENT_1`-`_113` | 945-1017 | | VCP/skin on-screen button events (mirrors jog panel layout). [jog-and-mpg.md](jog-and-mpg.md) |
| `SetAxis1Part0_SV` .. `SetAxis8Part0_SV` | `SV_PLC_SET_AXIS_n_PART_ZERO` | 1021-1028 | | Set-part-zero commands per axis. [jog-and-mpg.md](jog-and-mpg.md) |
| `M3_SV` | `SV_M94_M95_1` | 1034 | | Spindle CW M-function trigger. [main-stage.md](main-stage.md) |
| `M4_SV` | `SV_M94_M95_2` | 1035 | | Spindle CCW M-function trigger. [main-stage.md](main-stage.md) |
| `M6_SV` | `SV_M94_M95_8` | 1036 | Acroloc | Tool-change request (M6). [atc.md](atc.md) |
| `M8_SV` | `SV_M94_M95_3` | 1037 | | Flood-on M-function trigger. [main-stage.md](main-stage.md) |
| `M10_SV` | `SV_M94_M95_4` | 1038 | | Clamp M-function trigger. [main-stage.md](main-stage.md) |
| `M7_SV` | `SV_M94_M95_5` | 1039 | | Mist M-function trigger. [main-stage.md](main-stage.md) |

`SV_M94_M95_6` and `SV_M94_M95_7` (src:1040-1041) are commented placeholders with no
identifier bound — no name to cite.

## Constants

| Name | Resource | src line | Acroloc? | Meaning / used by |
|---|---|---|---|---|
| `MIN_FROR_PCT_C` | 1 | 126 | | Minimum allowed feedrate override percentage. [parameters.md](parameters.md) |
| `ASYNC_MSG_CLEAR_C` | 2 (2+256*0) | 127 | | Async message clear. [faults-and-messages.md](faults-and-messages.md) |
| `PLC_EXECUTOR_FLT_MSG_C` | 257 (1+256*1) | 128 | | PLC executor fault message. [faults-and-messages.md](faults-and-messages.md) |
| `AXIS_FLT_CLR_C` | 770 (2+256*3) | 129 | | Axis fault cleared message. [faults-and-messages.md](faults-and-messages.md) |
| `KB_JOG_MSG_C` | 1026 (2+256*4) | 130 | | Keyboard jog message. [jog-and-mpg.md](jog-and-mpg.md) |
| `X_AXIS_INFLT_C` .. `W_AXIS_INFLT_C` | 1282-3330 (2+256*5..13) | 132-140 | | Per-axis incoming-fiber-fault messages (X,Y,Z,A,B,C,U,V,W). [faults-and-messages.md](faults-and-messages.md) |
| `X_AXIS_OUTFLT_C` .. `W_AXIS_OUTFLT_C` | 3586-5634 (2+256*14..22) | 142-150 | | Per-axis outgoing-fiber-fault messages. [faults-and-messages.md](faults-and-messages.md) |
| `PLC_INFLT_C` | 5890 (2+256*23) | 152 | | PLC incoming fiber fault. [faults-and-messages.md](faults-and-messages.md) |
| `PLC_OUTFLT_C` | 6146 (2+256*24) | 153 | | PLC outgoing fiber fault. [faults-and-messages.md](faults-and-messages.md) |
| `PLC_FLT_CLR_C` | 6401 (1+256*25) | 154 | | PLC fault cleared. [faults-and-messages.md](faults-and-messages.md) |
| `LUBE_FAULT_MSG_C` | 6657 (1+256*26) | 156 | | Lube fault message. [faults-and-messages.md](faults-and-messages.md) |
| `PROBE_JOG_TRIP_MSG_C` | 6914 (2+256*27) | 157 | | Probe jog trip message. [faults-and-messages.md](faults-and-messages.md) |
| `SPINDLE_FAULT_MSG_C` | 7169 (1+256*28) | 158 | | Spindle fault message. [faults-and-messages.md](faults-and-messages.md) |
| `JOGBOARD_INFLT_C` | 7425 (1+256*29) | 159 | | Jog board incoming fault message. [faults-and-messages.md](faults-and-messages.md) |
| `JOGBOARD_OUTFLT_C` | 7681 (1+256*30) | 160 | | Jog board outgoing fault message. [faults-and-messages.md](faults-and-messages.md) |
| `PROBE_FAULT_MSG_C` | 7937 (1+256*31) | 161 | | Probe fault message. [faults-and-messages.md](faults-and-messages.md) |
| `RESET_CLEARED_C` | 8194 (2+256*32) | 163 | | Reset cleared message. [faults-and-messages.md](faults-and-messages.md) |
| `RESET_DETECTED_C` | 8449 (1+256*33) | 164 | | Reset detected message. [faults-and-messages.md](faults-and-messages.md) |
| `AUTO_COOL_MSG_C` | 8705 (1+256*34) | 166 | | Auto-coolant message. [faults-and-messages.md](faults-and-messages.md) |
| `MAN_COOL_MSG_C` | 8962 (2+256*35) | 167 | | Manual-coolant message. [faults-and-messages.md](faults-and-messages.md) |
| `LUBE_WARNING_MSG_C` | 9217 (1+256*36) | 168 | | Lube warning message. [faults-and-messages.md](faults-and-messages.md) |
| `AUTO_SPINDLE_PROMPT_C` | 9474 (2+256*37) | 169 | | Auto-spindle prompt message. [faults-and-messages.md](faults-and-messages.md) |
| `AUTO_COOLANT_PROMPT_C` | 9730 (2+256*38) | 170 | | Auto-coolant prompt message. [faults-and-messages.md](faults-and-messages.md) |
| `SOFTWARE_EXIT_MSG_C` | 9985 (1+256*39) | 171 | | Software-exit message. [faults-and-messages.md](faults-and-messages.md) |
| `MIN_SPEED_MSG_C` | 10242 (2+256*40) | 172 | | Minimum-speed message. [faults-and-messages.md](faults-and-messages.md) |
| `RAPID_OVERRIDE_ENABLED_C` | 10498 (2+256*41) | 173 | | Rapid override enabled message. [jog-and-mpg.md](jog-and-mpg.md) |
| `RAPID_OVERRIDE_DISABLED_C` | 10754 (2+256*42) | 174 | | Rapid override disabled message. [jog-and-mpg.md](jog-and-mpg.md) |
| `SAFETY_SWITCH_OPEN_MSG` | 23553 (1+256*92) | 176 | | Safety switch open message. [faults-and-messages.md](faults-and-messages.md) |
| `SAFETY_SWITCH_SPINDLE_MSG` | 23809 (1+256*93) | 177 | | Safety switch spindle message. [faults-and-messages.md](faults-and-messages.md) |
| `MSG_CLEARED_MSG_C` | 25345 (1+256*99) | 179 | | Message cleared. [faults-and-messages.md](faults-and-messages.md) |
| `BAD_MESSAGE_MSG_C` | 25602 (2+256*100) | 180 | | Bad message. [faults-and-messages.md](faults-and-messages.md) |
| `MINI_PLC_1_FLT_MSG_C` .. `MINI_PLC_8_FLT_MSG_C` | 39169-40961 (1+256*153..160) | 182-189 | | Per-mini-PLC fault messages. [faults-and-messages.md](faults-and-messages.md) |
| `MINI_PLC_1_WARNING_C` .. `MINI_PLC_8_WARNING_C` | 41218-43010 (2+256*161..168) | 190-197 | | Per-mini-PLC warning messages. [faults-and-messages.md](faults-and-messages.md) |
| `ATC_Spindle_Not_Parked_C` | 44034 (2+256*172) | 200 | Acroloc | "Spindle not parked. Z Axis not tool change position." [atc.md](atc.md) |
| `ATC_Lock_Not_Released_C` | 44290 (2+256*173) | 201 | Acroloc | "Tool Carousel not locked." [atc.md](atc.md) |
| `ATC_Lock_Released_C` | 44546 (2+256*174) | 202 | Acroloc | "Tool Carousel locked." — see message-encoding example above. [atc.md](atc.md) |
| `CAROUSEL_TIMEOUT_MSG_C` | 16130 (2+256*63) | 211 | Acroloc | "CAROUSEL MOVE TIME OUT" — carousel search-timeout fault (reuses stock message 63). [atc.md](atc.md) |
| `ATC_SPIN_TIMEOUT_MS_C` | 20000 | 212 | Acroloc | Carousel search timeout, ms (armed into `ATCSpin_T`). [atc.md](atc.md) |

## Stages

| Stage name | Resource | src line | Acroloc? | Detail file |
|---|---|---|---|---|
| `WatchDogStage` | STG1 | 1193 | | [boot.md](boot.md) |
| `InitialStage` | STG2 | 1194 | | [boot.md](boot.md) |
| `JogPanelStage` | STG3 | 1195 | | [jog-and-mpg.md](jog-and-mpg.md) |
| `MainStage` | STG4 | 1196 | | [main-stage.md](main-stage.md) |
| `AxesEnableStage` | STG5 | 1197 | | [faults-and-messages.md](faults-and-messages.md) |
| `LoadMeterStage` | STG6 | 1198 | | [boot.md](boot.md) |
| `MPGStage` | STG7 | 1199 | | [jog-and-mpg.md](jog-and-mpg.md) |
| `CheckCycloneStatusStage` | STG8 | 1200 | | [faults-and-messages.md](faults-and-messages.md) |
| `MiniPLCErrorStage` | STG9 | 1201 | | [faults-and-messages.md](faults-and-messages.md) |
| `LoadParametersStage` | STG10 | 1202 | | [boot.md](boot.md) |
| `KeyboardEventsStage` | STG11 | 1203 | | [main-stage.md](main-stage.md) |
| `ATCStage` | STG16 | 1207 | Acroloc | [atc.md](atc.md) |
| `GearShiftStage` | STG17 | 1208 | Acroloc | [gear-shift.md](gear-shift.md) |
| `JogKeysNormalStage` | STG26 | 1210 | | [jog-and-mpg.md](jog-and-mpg.md) |
| `JogKeysInvert2Stage` | STG27 | 1211 | | [jog-and-mpg.md](jog-and-mpg.md) |
| `JogKeysSwappedStage` | STG28 | 1212 | | [jog-and-mpg.md](jog-and-mpg.md) |
| `JogKeysSwapAndInvert2Stage` | STG29 | 1213 | | [jog-and-mpg.md](jog-and-mpg.md) |
| `WirelessMpgStage` | STG60 | 1214 | | [jog-and-mpg.md](jog-and-mpg.md) |
| `SafetySwitchInterruptStage` | STG62 | 1215 | | [faults-and-messages.md](faults-and-messages.md) |
| `MessageStage` | STG90 | 1217 | | [faults-and-messages.md](faults-and-messages.md) |
| `ShowFaultStage` | STG91 | 1218 | | [faults-and-messages.md](faults-and-messages.md) |
| `ShowErrorStage` | STG92 | 1219 | | [faults-and-messages.md](faults-and-messages.md) |
| `ShowInfoStage` | STG93 | 1220 | | [faults-and-messages.md](faults-and-messages.md) |
| `BadMsgStage` | STG94 | 1221 | | [faults-and-messages.md](faults-and-messages.md) |

## Defined but unused

None currently. The former stock gear-sense inputs `SpinLowRange_I` / `SpinMedRange_I` /
`SpinHighRange_I` (INP13-15) were **removed** — the two-speed shift is intentionally
open-loop and closed-loop gear confirmation is not planned; a source comment at the old
definition site records that INP13-15 are the (unwired) gear-sense inputs. `ATCSpin_T`
(`T24`) is now armed at M6 kickoff and read as the carousel search watchdog; see
[atc.md](atc.md#search-timeout).
