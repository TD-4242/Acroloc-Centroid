# Centroid CNC12 SV_* System Variable Catalog

This catalog covers every `SV_*` name found in the official ALLIN1DC example source files
(`docs/official/_ALLIN1DC/**/*.src`) and the custom Acroloc PLC
(`Centroid-Acroloc-ALLIN1DC.src`). The name list is in `scratchpad/sv-names.txt` (548
entries, built by `grep -rhoE "SV_[A-Z0-9_]+" ...`).

**Source labels used in this document:**
- `manual` — meaning taken directly from Appendix D of the *CNC12 PLC Programming Manual*
  rev 7 (2023), Tables: CNC Software Write-Controlled and PLC Write-Controlled.
- `from code usage` — name appears in PLC source or comments but is absent from Appendix D;
  meaning inferred from context.

**Note on grep artifacts.** The extraction regex `SV_[A-Z0-9_]+` stops at the first
lowercase character. Several mixed-case symbol aliases used in source code therefore produce
short partial captures (e.g. `SV_S` from `SV_Stop`, `SV_PLC_F` from
`SV_PLC_FeedrateKnob_W`). These are documented in the Misc/system section for completeness.

---

## Spindle

| SV_ name | Meaning | Source |
|---|---|---|
| SV_SPINDLE_LOW_RANGE | PLC sets to indicate spindle is in low range. Required for rigid tapping and spindle speed display. Combined with SV_SPINDLE_MID_RANGE to select up to four gear ranges. | manual |
| SV_SPINDLE_MID_RANGE | PLC sets to indicate spindle is in mid range. Required for rigid tapping and spindle speed display. | manual |
| SV_SPINDLE_FAULT | Obsolete — do not use. | manual |
| SV_SPINDLE_METER | F32. Maps to the meter SV (1–16) that corresponds to the spindle axis; set by PLC to a value –100.0 to 100.0 to drive the on-screen spindle load meter. | manual |
| SV_PC_DAC_SPINDLE_SPEED | I32. DAC spindle speed as requested by CNC software (range 0–65535). Read-only for PLC. | manual |
| SV_PC_COMMANDED_SPINDLE_SPEED | F32. Commanded S-word speed with spindle override factored in. Parameters 65–67 for spindle range must still be controlled by the PLC. | manual |
| SV_PC_RIGID_TAP_SPINDLE_OFF | M. CNC software sets this bit to signal that the spindle should be turned off when rigid-tap depth is reached (only needed if Parameter 36 bit 4 is set and turning off the spindle requires more than clearing M3 or M4). | manual |
| SV_PLC_SPINDLE_SPEED | I32. If Parameter 78 is not set to display actual spindle speed, this value is the current spindle speed displayed on-screen. Set by PLC. | manual |
| SV_PLC_SPINDLE_KNOB | I32. Spindle speed override percentage sent to/from the PLC (spindle knob). | manual |
| SV_PLC_FUNCTION_37 | M. PLC sets to trigger Spindle Start. | manual |
| SV_PLC_FUNCTION_38 | M. PLC sets to trigger Spindle Stop. | manual |
| SV_PLC_FUNCTION_98 | M. PLC sets to select Spindle CCW. | manual |
| SV_PLC_FUNCTION_99 | M. PLC sets to select Spindle CW. | manual |
| SV_PLC_FUNCTION_106 | M. PLC sets to increment Spindle Override (+). | manual |
| SV_PLC_FUNCTION_107 | M. PLC sets to decrement Spindle Override (−). | manual |
| SV_PLC_FUNCTION_108 | M. PLC sets to reset Spindle Override to 100%. | manual |

---

## Tool / tool-change

Includes ATC carousel position tracking and all M94/M95 trigger bits.

| SV_ name | Meaning | Source |
|---|---|---|
| SV_TOOL_NUMBER | I32. Set by CNC software as part of a tool change (M107) to indicate the requested tool number. In enhanced ATC mode, this is actually a request for a carousel bin location. | manual |
| SV_ATC_CAROUSEL_POSITION | I32. Sent by CNC software on startup or as part of an enhanced ATC reset; the last known carousel position. | manual |
| SV_ATC_TOOL_IN_SPINDLE | I32. Sent by CNC software on startup (from job file) or enhanced ATC reset; the tool currently in the spindle. | manual |
| SV_PLC_CAROUSEL_POSITION | I32. Set by PLC to report the current carousel bin position back to CNC software. Critical — the carousel must not turn unless software is running. | manual |
| SV_TOOL_AT_PUTBACK | M. Defined in ATC PLC programs (e.g. umbrella ATC) as a message constant (IS 21250) to signal that the tool has returned to its pocket. Used via message display stage. | from code usage |
| SV_SYS_MACRO | I32. Setting to a non-zero value while CNC is at main menu causes CNC software to load and run `plcmacroN.mac` (e.g. `\cncm\system\plcmacro3.mac`). Can be set negative. | manual |
| SV_M94_M95_1 | M. M94/M95 bit 1. Conventionally mapped to M3 (Spindle CW). Set by M94 /1, reset by M95 /1 from G-code. | manual |
| SV_M94_M95_2 | M. M94/M95 bit 2. Conventionally mapped to M4 (Spindle CCW). | manual |
| SV_M94_M95_3 | M. M94/M95 bit 3. Mapped to M8 (Flood Coolant On) — `M8_SV IS SV_M94_M95_3` (src line 1037). | manual |
| SV_M94_M95_4 | M. M94/M95 bit 4. Mapped to M10 (Clamp On) — `M10_SV IS SV_M94_M95_4` (src line 1038). | manual |
| SV_M94_M95_5 | M. M94/M95 bit 5. Mapped to M7 (Mist Coolant) — `M7_SV IS SV_M94_M95_5` (src line 1039). | manual |
| SV_M94_M95_6 | M. M94/M95 bit 6. Unassigned/reserved — blank in manual and not used in this installation (src line 1040). | manual |
| SV_M94_M95_7 | M. M94/M95 bit 7. Unassigned/reserved — blank in manual and not used in this installation (src line 1041). | manual |
| SV_M94_M95_8 | M. M94/M95 bit 8. M6 Tool Change trigger — Acroloc-custom assignment (`M6_SV IS SV_M94_M95_8` at src line 1036); the standard manual leaves bit 8 blank. | from code usage |
| SV_M94_M95_9 | M. M94/M95 bit 9. Custom M-code trigger bit. | from code usage |
| SV_M94_M95_10 | M. M94/M95 bit 10. Custom M-code trigger bit. | from code usage |
| SV_M94_M95_11 | M. M94/M95 bit 11. Custom M-code trigger bit. | from code usage |
| SV_M94_M95_12 | M. M94/M95 bit 12. Custom M-code trigger bit. | from code usage |
| SV_M94_M95_13 | M. M94/M95 bit 13. Custom M-code trigger bit. | from code usage |
| SV_M94_M95_14 | M. M94/M95 bit 14. Custom M-code trigger bit. | from code usage |
| SV_M94_M95_15 | M. M94/M95 bit 15. Custom M-code trigger bit. | from code usage |
| SV_M94_M95_16 | M. M94/M95 bit 16. Custom M-code trigger bit. | from code usage |
| SV_M94_M95_18 | M. M94/M95 bit 18. Custom M-code trigger bit. | from code usage |
| SV_M94_M95_19 | M. M94/M95 bit 19. Custom M-code trigger bit. | from code usage |
| SV_M94_M95_32 | M. M94/M95 bit 32. Custom M-code trigger bit. | from code usage |
| SV_M94_M95_33 | M. M94/M95 bit 33. Custom M-code trigger bit. | from code usage |
| SV_M94_M95_40 | M. M94/M95 bit 40. Custom M-code trigger bit. | from code usage |
| SV_M94_M95_80 | M. M94/M95 bit 80. Custom M-code trigger bit. | from code usage |
| SV_M94_M95_81 | M. M94/M95 bit 81. Custom M-code trigger bit. | from code usage |

---

## Jog / MPG

Includes MPG configuration, jog panel debounce, USB wireless MPG, keyboard jog panel,
absolute position reads, and all PLC function command bits not assigned to Spindle or
Coolant.

### MPG units (three independent MPG groups)

| SV_ name | Meaning | Source |
|---|---|---|
| SV_MPG_1_AXIS_SELECT | I32. Currently selected axis for MPG group 1 (1–8). Change takes effect only when MPG movement is stopped. | manual |
| SV_MPG_1_MULTIPLIER | I32. MPG 1 multiplier value, normally 1, 10, or 100. | manual |
| SV_MPG_1_ENABLED | M. MPG group 1 is enabled; MPU11 will not process motion vectors from PC or allow jogging while set. Change takes effect only when MPG movement is stopped. | manual |
| SV_MPG_1_WINDUP_MODE | M. MPG 1 is in windup mode — moves the total distance commanded by encoder input (typical for x1 and x10; disable for x100). | manual |
| SV_MPG_2_AXIS_SELECT | I32. Currently selected axis for MPG group 2 (1–8). | manual |
| SV_MPG_2_MULTIPLIER | I32. MPG 2 multiplier value, normally 1, 10, or 100. | manual |
| SV_MPG_2_ENABLED | M. MPG group 2 enabled. See SV_MPG_1_ENABLED. | manual |
| SV_MPG_2_WINDUP_MODE | M. MPG 2 windup mode. See SV_MPG_1_WINDUP_MODE. | manual |
| SV_MPG_3_AXIS_SELECT | I32. Currently selected axis for MPG group 3 (1–8). | manual |
| SV_MPG_3_MULTIPLIER | I32. MPG 3 multiplier value, normally 1, 10, or 100. | manual |
| SV_MPG_3_ENABLED | M. MPG group 3 enabled. See SV_MPG_1_ENABLED. | manual |
| SV_MPG_3_WINDUP_MODE | M. MPG 3 windup mode. See SV_MPG_1_WINDUP_MODE. | manual |

### USB wireless MPG

| SV_ name | Meaning | Source |
|---|---|---|
| SV_USB_MPG_POWER | M. Set when the USB wireless MPG is powered on (requires a state change to be detected). | manual |
| SV_USB_MPG_AXIS_SELECT | I32. Wireless USB MPG axis select switch: 0 = Off, 1–6 = selected axis (X, Y, Z, 4th, 5th, 6th). | manual |
| SV_USB_MPG_SCALE_SELECT | I32. Wireless USB MPG scale knob: 1 = x1, 10 = x10, 100 = x100, 1000 = SPIN, 10000 = FEED. | manual |
| SV_USB_MPG_ENCODER_WHEEL | I32. Wireless MPG wheel position — counts up/down without rollover. | manual |
| SV_USB_MPG_BUTTON_STATE | I32. Wireless MPG button states: bit 0 = Reset, 1 = Feed Hold, 2 = Cycle Start, 3 = Jog+, 4 = Jog−, 5 = SPIN Auto/Man, 6 = SPIN On/Off, 7 = Macro 1, 8 = Macro 2, 9 = Macro 3, 10 = Macro 4, 11 = Tool Check, 12 = Set Zero. | manual |

### Jog panel link and debounce

| SV_ name | Meaning | Source |
|---|---|---|
| SV_JOG_LINK_ONLINE | M. 1 = Valid jog panel detected as Jogboard. Set by CNC software. | manual |
| SV_JOG_PANEL_REQUIRED | M. Reflects the "Jog Panel Required" setting in the Control Configuration Menu of CNC software. | manual |
| SV_PC_VIRTUAL_JOGPANEL_ACTIVE | M. Indicates whether keyboard jogging (virtual jog panel) is enabled via ALT-J. | manual |
| SV_JOG_LINK_DEBOUNCE_1 | I32. Jog panel input debounce configuration word 1 (covers first 16 jog link inputs). | manual |
| SV_JOG_LINK_DEBOUNCE_64 | I32. Jog panel input debounce configuration word 64. | manual |
| SV_PLC_DEBOUNCE_ | Partial regex capture from the comment `SV_PLC_DEBOUNCE_ has been deprecated` (inversion/forcing via debounce SVs is no longer supported). Not a standalone SV name. | from code usage |
| SV_PLC_DEBOUNCE_1 | I32. Debounce configuration word for PLC inputs 1–16. Each bit pair configures debounce time for the corresponding input. | manual |
| SV_PLC_DEBOUNCE_2 | I32. Debounce configuration for PLC inputs 17–32. | manual |
| SV_PLC_DEBOUNCE_3 | I32. Debounce configuration for PLC inputs 33–48. | manual |
| SV_PLC_DEBOUNCE_4 | I32. Debounce configuration for PLC inputs 49–64. | manual |
| SV_PLC_DEBOUNCE_60 | I32. Debounce configuration word 60. | manual |
| SV_PLC_DEBOUNCE_61 | I32. Debounce configuration word 61. | manual |
| SV_PLC_DEBOUNCE_62 | I32. Debounce configuration word 62. | manual |
| SV_PLC_DEBOUNCE_64 | I32. Debounce configuration word 64 (last standard word; covers inputs up to slot boundary). | manual |

### Axis absolute position

| SV_ name | Meaning | Source |
|---|---|---|
| SV_MPU11_ABS_POS_1 | I64. Absolute position of axis 2 in encoder counts (same value shown in CNC PID screen as AbsPos). Zero-indexed; index 1 = second physical axis — `_0` exists and is axis 1 (verified on-machine 2026-07-16: the Acroloc VCP DRO reads `_0/_1/_2` for X/Y/Z). Counts are power-up-relative, not homed machine coordinates. | manual + verified |
| SV_MPU11_ABS_POS_7 | I64. Absolute position of axis 8 in encoder counts. | manual |

### PLC function commands (jog panel / cycle control)

The PLC function bits are set by the PLC program to send control commands to CNC software
(cycle start/cancel, jog mode selection, axis jog, feedhold, etc.). All are type M.

| SV_ name | Meaning | Source |
|---|---|---|
| SV_PLC_FUNCTION_0 | Invalid — do not use. | manual |
| SV_PLC_FUNCTION_1 | Cycle Cancel. | manual |
| SV_PLC_FUNCTION_2 | Cycle Start. | manual |
| SV_PLC_FUNCTION_3 | Tool Check. | manual |
| SV_PLC_FUNCTION_4 | Select Single Block. | manual |
| SV_PLC_FUNCTION_5 | Select X1 Jog Increment Mode. | manual |
| SV_PLC_FUNCTION_6 | Select X10 Jog Increment Mode. | manual |
| SV_PLC_FUNCTION_7 | Select X100 Jog Increment Mode. | manual |
| SV_PLC_FUNCTION_8 | Not used (formerly User Jog Inc Mode). | manual |
| SV_PLC_FUNCTION_9 | Select Inc/Cont Jog Mode. | manual |
| SV_PLC_FUNCTION_10 | Select Fast/Slow Jog Mode. | manual |
| SV_PLC_FUNCTION_11 | Select MPG Mode. | manual |
| SV_PLC_FUNCTION_12 | Axis 1 + Jog. | manual |
| SV_PLC_FUNCTION_13 | Axis 1 − Jog. | manual |
| SV_PLC_FUNCTION_14 | Axis 2 + Jog. | manual |
| SV_PLC_FUNCTION_15 | Axis 2 − Jog. | manual |
| SV_PLC_FUNCTION_16 | Axis 3 + Jog. | manual |
| SV_PLC_FUNCTION_17 | Axis 3 − Jog. | manual |
| SV_PLC_FUNCTION_18 | Axis 4 + Jog. | manual |
| SV_PLC_FUNCTION_19 | Axis 4 − Jog. | manual |
| SV_PLC_FUNCTION_20 | Axis 5 + Jog. | manual |
| SV_PLC_FUNCTION_21 | Axis 5 − Jog. | manual |
| SV_PLC_FUNCTION_22 | Axis 6 + Jog. | manual |
| SV_PLC_FUNCTION_23 | Axis 6 − Jog. | manual |
| SV_PLC_FUNCTION_24 | Aux1. | manual |
| SV_PLC_FUNCTION_25 | Aux2. | manual |
| SV_PLC_FUNCTION_26 | Aux3. | manual |
| SV_PLC_FUNCTION_27 | Aux4. | manual |
| SV_PLC_FUNCTION_28 | Aux5. | manual |
| SV_PLC_FUNCTION_29 | Aux6. | manual |
| SV_PLC_FUNCTION_30 | Aux7. | manual |
| SV_PLC_FUNCTION_31 | Aux8. | manual |
| SV_PLC_FUNCTION_32 | Aux9. | manual |
| SV_PLC_FUNCTION_33 | Aux10. | manual |
| SV_PLC_FUNCTION_34 | Select Rapid Override (usage deprecated; prefer the PC_TOGGLE_RAPID_OVERRIDE system variable). | manual |
| SV_PLC_FUNCTION_35 | Select Man or Auto Spindle Mode. | manual |
| SV_PLC_FUNCTION_39 | Aux11. | manual |
| SV_PLC_FUNCTION_40 | Aux12. | manual |
| SV_PLC_FUNCTION_41 | Deprecated — do not use. | manual |
| SV_PLC_FUNCTION_42 | Deprecated — do not use. | manual |
| SV_PLC_FUNCTION_45 | Feed Hold. | manual |
| SV_PLC_FUNCTION_109 | Escape key (sent to the PC). | manual |
| SV_PLC_FUNCTION_114 | Unused. | manual |
| SV_PLC_FUNCTION_115 | Unused. | manual |
| SV_PLC_FUNCTION_116 | Unused. | manual |
| SV_PLC_FUNCTION_117 | Unused. | manual |

---

## Coolant

| SV_ name | Meaning | Source |
|---|---|---|
| SV_PLC_FUNCTION_43 | M. PLC sets to select Coolant Flood. | manual |
| SV_PLC_FUNCTION_44 | M. PLC sets to select Coolant Mist. | manual |
| SV_PLC_FUNCTION_104 | M. PLC sets to toggle Coolant Auto/Manual Mode. | manual |

---

## Machine parameters

Each machine parameter SV exposes that CNC machine parameter as a 32-bit floating-point
value (F32) read from CNC software settings. The PLC reads these; CNC software owns the
authoritative value. The control-configuration entries are also F32 values set by CNC
software.

### Control configuration

| SV_ name | Meaning | Source |
|---|---|---|
| SV_PC_CONFIG_MIN_SPINDLE_SPEED | F32. Minimum spindle speed from the control configuration (CNC software). | manual |
| SV_PC_CONFIG_MAX_SPINDLE_SPEED | F32. Maximum spindle speed from the control configuration (CNC software). | manual |

### Machine parameters used in source (specific numbers)

| SV_ name | Meaning | Source |
|---|---|---|
| SV_MACHINE_PARAMETER_1 | F32. Jog key configuration bits. Bit patterns control axis jog key inversion and other jog behavior (e.g. bit 1 = invert Ax2 jog keys). | from code usage |
| SV_MACHINE_PARAMETER_19 | F32. MPG modes configuration (selects MPG input mode and behavior). | from code usage |
| SV_MACHINE_PARAMETER_33 | F32. Spindle motor gear ratio 2× (reference uncertain — appears with `??` prefix in Acroloc source comment). | from code usage |
| SV_MACHINE_PARAMETER_39 | F32. Maximum feedrate override percentage limit. The PLC clamps the feedrate knob value to this ceiling. | from code usage |
| SV_MACHINE_PARAMETER_57 | F32. Non-zero enables load meter stage; 0 disables it. | from code usage |
| SV_MACHINE_PARAMETER_65 | F32. Low range gear ratio (e.g. 0.5×). Used to scale SV_PC_COMMANDED_SPINDLE_SPEED when SV_SPINDLE_LOW_RANGE is set. | from code usage |
| SV_MACHINE_PARAMETER_66 | F32. Medium-low range gear ratio. | from code usage |
| SV_MACHINE_PARAMETER_67 | F32. Medium-high range gear ratio. | from code usage |
| SV_MACHINE_PARAMETER_85 | F32. Door interlock configuration. Non-zero values other than 8 trigger a configuration fault in standard PLC programs. | from code usage |
| SV_MACHINE_PARAMETER_146 | F32. Feedhold threshold — sets feedhold when feedrate falls below this value. | from code usage |
| SV_MACHINE_PARAMETER_148 | F32. Miscellaneous jogging options. Bit 1 set = prohibit keyboard jogging. | from code usage |
| SV_MACHINE_PARAMETER_153 | F32. Probe protection: 0 = disabled, non-zero = enabled. | from code usage |
| SV_MACHINE_PARAMETER_161 | F32. Maximum carousel bin location for ATC (umbrella ATC programs). | from code usage |
| SV_MACHINE_PARAMETER_170 | F32. Keyboard jogging enable flags. Bit 0 = allow keyboard input, bit 1 = jog override only, bit 2 = keyboard override only. | from code usage |
| SV_MACHINE_PARAMETER_178 | F32. PLC I/O normally-open / normally-closed settings (active-low vs active-high input polarity). | from code usage |
| SV_MACHINE_PARAMETER_179 | F32. Lube pump settings encoded as MMMSS (minutes × 100 + seconds). | from code usage |
| SV_MACHINE_PARAMETER_218 | F32. MPG type: 0 = wired MPG (MPGStage), non-zero = wireless USB MPG (WirelessMpgStage). | from code usage |
| SV_MACHINE_PARAMETER_219 | F32. VCP (Virtual Control Panel): 0 = no VCP, 1 = start VCP on boot. | from code usage |
| SV_MACHINE_PARAMETER_348 | F32. MPG 1 encoder assignment (15 = onboard encoder, other values = expansion encoder number). | from code usage |
| SV_MACHINE_PARAMETER_351 | F32. MPG 2 encoder assignment. | from code usage |
| SV_MACHINE_PARAMETER_354 | F32. MPG 3 encoder assignment. | from code usage |
| SV_MACHINE_PARAMETER_441 | F32. MPG 1 axis select (axis number 1–8 that MPG 1 controls by default). | from code usage |
| SV_MACHINE_PARAMETER_442 | F32. MPG 2 axis select. | from code usage |
| SV_MACHINE_PARAMETER_443 | F32. MPG 3 axis select. | from code usage |
| SV_MACHINE_PARAMETER_800 | F32. Control type / ATC clamp configuration. 0 = standard (no clamp), 1 = clamp enabled. Also read by VCP to determine key layout. | from code usage |
| SV_MACHINE_PARAMETER_820 | F32. Machine type: 0 = Mill, 1 = Lathe, 2 = Router, 3 = Plasma, 4 = Waterjet, etc. Read by VCP and PLC for axis/mode configuration. | from code usage |
| SV_MACHINE_PARAMETER_900 | F32. PLC ADD (expansion) installed flag. Non-zero indicates PLCADD expansion board is present. | from code usage |
| SV_MACHINE_PARAMETER_901 | F32. Wait-before-braking timer value (application-specific — seen in spindle-brake PLC variant). | from code usage |
| SV_MACHINE_PARAMETER_902 | F32. Brake-on timer value (application-specific — seen in spindle-brake PLC variant). | from code usage |
| SV_MACHINE_PARAMETER_911 | F32. Invert inputs 1–16: written to SV_INVERT_INP1_16_BITS by PLC to invert those inputs via the live I/O screen (ALT-I). Requires SV_ENABLE_IO_OVERRIDE to be SET. | from code usage |
| SV_MACHINE_PARAMETER_912 | F32. Invert inputs 17–32 → SV_INVERT_INP17_32_BITS. | from code usage |
| SV_MACHINE_PARAMETER_913 | F32. Invert inputs 33–48 → SV_INVERT_INP33_48_BITS. | from code usage |
| SV_MACHINE_PARAMETER_914 | F32. Invert inputs 49–64 → SV_INVERT_INP49_64_BITS. | from code usage |
| SV_MACHINE_PARAMETER_915 | F32. Invert inputs 65–80 → SV_INVERT_INP65_80_BITS. | from code usage |
| SV_MACHINE_PARAMETER_916 | F32. Force inputs 1–16 → SV_FORCE_INP1_16_BITS. | from code usage |
| SV_MACHINE_PARAMETER_917 | F32. Force inputs 17–32 → SV_FORCE_INP17_32_BITS. | from code usage |
| SV_MACHINE_PARAMETER_918 | F32. Force inputs 33–48 → SV_FORCE_INP33_48_BITS. | from code usage |
| SV_MACHINE_PARAMETER_919 | F32. Force inputs 49–64 → SV_FORCE_INP49_64_BITS. | from code usage |
| SV_MACHINE_PARAMETER_920 | F32. Force inputs 65–80 → SV_FORCE_INP65_80_BITS. | from code usage |
| SV_MACHINE_PARAMETER_921 | F32. Force outputs 1–16 ON → SV_FORCE_ON_OUT1_16_BITS. | from code usage |
| SV_MACHINE_PARAMETER_922 | F32. Force outputs 17–32 ON → SV_FORCE_ON_OUT17_32_BITS. | from code usage |
| SV_MACHINE_PARAMETER_923 | F32. Force outputs 33–48 ON → SV_FORCE_ON_OUT33_48_BITS. | from code usage |
| SV_MACHINE_PARAMETER_924 | F32. Force outputs 49–64 ON → SV_FORCE_ON_OUT49_64_BITS. | from code usage |
| SV_MACHINE_PARAMETER_925 | F32. Force outputs 65–80 ON → SV_FORCE_ON_OUT65_80_BITS. | from code usage |
| SV_MACHINE_PARAMETER_926 | F32. Force outputs 1–16 OFF → SV_FORCE_OFF_OUT1_16_BITS. | from code usage |
| SV_MACHINE_PARAMETER_927 | F32. Force outputs 17–32 OFF → SV_FORCE_OFF_OUT17_32_BITS. | from code usage |
| SV_MACHINE_PARAMETER_928 | F32. Force outputs 33–48 OFF → SV_FORCE_OFF_OUT33_48_BITS. | from code usage |
| SV_MACHINE_PARAMETER_929 | F32. Force outputs 49–64 OFF → SV_FORCE_OFF_OUT49_64_BITS. | from code usage |
| SV_MACHINE_PARAMETER_930 | F32. Force outputs 65–80 OFF → SV_FORCE_OFF_OUT65_80_BITS. | from code usage |
| SV_MACHINE_PARAMETER_931 | F32. Force MEM bits 1–16 ON → SV_FORCE_ON_MEM1_16_BITS. | from code usage |
| SV_MACHINE_PARAMETER_932 | F32. Force MEM bits 17–32 ON → SV_FORCE_ON_MEM17_32_BITS. | from code usage |
| SV_MACHINE_PARAMETER_933 | F32. Force MEM bits 33–48 ON → SV_FORCE_ON_MEM33_48_BITS. | from code usage |
| SV_MACHINE_PARAMETER_934 | F32. Force MEM bits 49–64 ON → SV_FORCE_ON_MEM49_64_BITS. | from code usage |
| SV_MACHINE_PARAMETER_935 | F32. Force MEM bits 65–80 ON → SV_FORCE_ON_MEM65_80_BITS. | from code usage |
| SV_MACHINE_PARAMETER_936 | F32. Force MEM bits 1–16 OFF → SV_FORCE_OFF_MEM1_16_BITS. | from code usage |
| SV_MACHINE_PARAMETER_937 | F32. Force MEM bits 17–32 OFF → SV_FORCE_OFF_MEM17_32_BITS. | from code usage |
| SV_MACHINE_PARAMETER_938 | F32. Force MEM bits 33–48 OFF → SV_FORCE_OFF_MEM33_48_BITS. | from code usage |
| SV_MACHINE_PARAMETER_939 | F32. Force MEM bits 49–64 OFF → SV_FORCE_OFF_MEM49_64_BITS. | from code usage |
| SV_MACHINE_PARAMETER_940 | F32. Force MEM bits 65–80 OFF → SV_FORCE_OFF_MEM65_80_BITS. | from code usage |
| SV_MACHINE_PARAMETER_950 | F32. Spindle RPM deadband for analog spindle control (application-specific — seen in analog BP-BOSS variant). | from code usage |
| SV_MACHINE_PARAMETER_951 | F32. Low-range deadband adjustment for analog spindle control (application-specific). | from code usage |
| SV_MACHINE_PARAMETER_961 | F32. ATC carousel in/out timer in seconds (0 = default 2000 ms). Used in umbrella ATC programs. | from code usage |
| SV_MACHINE_PARAMETER_962 | F32. ATC orient timer in seconds (0 = default 5000 ms). | from code usage |
| SV_MACHINE_PARAMETER_963 | F32. ATC orient-lost timer in milliseconds (0 = default 100 ms). | from code usage |
| SV_MACHINE_PARAMETER_964 | F32. ATC tool clamp/unclamp timer in seconds (0 = default 2000 ms). | from code usage |
| SV_MACHINE_PARAMETER_965 | F32. ATC carousel tool-to-tool timer in seconds (0 = default 1000 ms). | from code usage |
| SV_MACHINE_PARAMETER_999 | F32. Captured from comment `SV_MACHINE_PARAMETER_1 - SV_MACHINE_PARAMETER_999` (range upper bound reference). Meaning of parameter 999 is not documented in source. | from code usage |

---

## Misc / system

### System state, faults, and program control

| SV_ name | Meaning | Source |
|---|---|---|
| SV_STOP | M. PLC sets on critical error or E-Stop press to signal CNC software and MPU to prevent axis motion, spindle commands, and ATC changes. PLC resets when E-Stop is released and no other errors exist. Write only once per PLC pass (use a temp variable to aggregate). | manual |
| SV_PROGRAM_RUNNING | M. 1 = MDI mode or a job is in progress. Set by CNC software. | manual |
| SV_MDI_MODE | M. 1 = MDI mode active. Set by CNC software. | manual |
| SV_JOB_IN_PROGRESS | M. Set when CNC software is running a job or an MDI command but NOT while waiting at the MDI prompt. | manual |
| SV_LIMIT_TRIPPED | M. 1 = any configured limit switch is tripped; 0 = none tripped. PLC is not required to take action but may use this for operator messages. | manual |
| SV_PC_SOFTWARE_READY | M. 1 = CNC software is initialized and communicating with MPU normally. 0 = software exited normally or communication fault. PLC typically sets SV_STOP when this is 0. | manual |
| SV_STALL_ERROR | M. 1 = MPU11 detected a stall-class error. PLC should turn off all enables including SV_MASTER_ENABLE. PLC should reset this bit when E-Stop is pushed. Read only once per PLC pass (externally written). | manual |
| SV_STALL_REASON | I32. Set whenever SV_STALL_ERROR is set. Values: 0=No Error, 1=position error, 2=full power without motion, 3=encoder differential error, 4=spindle slave position error, 6=OpticDirect C8 error, 15=scale encoder differential error, 16=encoder quadrature error, 17=scale encoder quadrature error, 18=standoff error, 19=scale position error, 99=master enable turned off. | manual |
| SV_STALL_AXIS | I32. Set whenever SV_STALL_ERROR is set. The axis number (1-based) associated with the stall; 255 if axis is not applicable. | manual |
| SV_PLC_FAULT_STATUS | I32. Bitwise PLC executor fault: 0x00000001=DIV_BY_ZERO, 0x00000002=OUT_OF_BOUNDS, 0x00000004=INVALID_OPCODE. Non-zero triggers SV_STOP. | manual |
| SV_PLC_FAULT_ADDRESS | I32. Address in PLC program where a PLC fault (SV_PLC_FAULT_STATUS) occurred. | manual |
| SV_MASTER_ENABLE | M. PLC sets this bit to turn on the Master Enable to hardware devices (drives and PLCs). PLC clears it on E-Stop or stall. | manual |
| SV_ENABLE_IO_OVERRIDE | M. When set by PLC, CNC software allows inversion and forcing of PLC bits through the live PLC display (ALT-I) via machine parameters 911–939. | manual |
| SV_TRIGGER_PLOT_DUMP | M. Internal debugging: when set, starts a debug dump sent to CNC software which then launches plot.exe. Requires custom-built CNC software to be useful. | manual |

### Axis validity, drive status, and power

| SV_ name | Meaning | Source |
|---|---|---|
| SV_AXIS_VALID_1 | M. 1 = axis 1 label in Motor Parameters screen allows motion (valid labels: X,Y,Z,A,B,C,U,V,W). | manual |
| SV_AXIS_VALID_2 | M. 1 = axis 2 valid. | manual |
| SV_AXIS_VALID_3 | M. 1 = axis 3 valid. | manual |
| SV_AXIS_VALID_4 | M. 1 = axis 4 valid. | manual |
| SV_AXIS_VALID_5 | M. 1 = axis 5 valid. | manual |
| SV_AXIS_VALID_6 | M. 1 = axis 6 valid. | manual |
| SV_AXIS_VALID_7 | M. 1 = axis 7 valid. | manual |
| SV_AXIS_VALID_8 | M. 1 = axis 8 valid. | manual |
| SV_DRIVE_ONLINE_1 | M. 1 = drive for axis 1 is detected. | manual |
| SV_DRIVE_ONLINE_2 | M. 1 = drive for axis 2 detected. | manual |
| SV_DRIVE_ONLINE_3 | M. 1 = drive for axis 3 detected. | manual |
| SV_DRIVE_ONLINE_4 | M. 1 = drive for axis 4 detected. | manual |
| SV_DRIVE_ONLINE_5 | M. 1 = drive for axis 5 detected. | manual |
| SV_DRIVE_ONLINE_6 | M. 1 = drive for axis 6 detected. | manual |
| SV_DRIVE_ONLINE_7 | M. 1 = drive for axis 7 detected. | manual |
| SV_DRIVE_ONLINE_8 | M. 1 = drive for axis 8 detected. | manual |
| SV_ENABLE_AXIS_ | Partial regex capture from comment `; for SV_ENABLE_AXIS_n` (underscore only, no digit). Refers to the SV_ENABLE_AXIS_1–8 naming pattern. Not a standalone SV name. | from code usage |
| SV_ENABLE_AXIS_1 | M. Obsolete — do not use (was used to enable/disable axis motion). | manual |
| SV_ENABLE_AXIS_2 | M. Obsolete — do not use. | manual |
| SV_ENABLE_AXIS_3 | M. Obsolete — do not use. | manual |
| SV_ENABLE_AXIS_4 | M. Obsolete — do not use. | manual |
| SV_ENABLE_AXIS_5 | M. Obsolete — do not use. | manual |
| SV_ENABLE_AXIS_6 | M. Obsolete — do not use. | manual |
| SV_ENABLE_AXIS_7 | M. Obsolete — do not use. | manual |
| SV_ENABLE_AXIS_8 | M. Obsolete — do not use. | manual |
| SV_PC_POWER_AXIS_1 | M. 1 = axis 1 is powered and holding position. Set by CNC software. Externally written — read only once per PLC pass. | manual |
| SV_PC_POWER_AXIS_2 | M. 1 = axis 2 powered. | manual |
| SV_PC_POWER_AXIS_3 | M. 1 = axis 3 powered. | manual |
| SV_PC_POWER_AXIS_4 | M. 1 = axis 4 powered. | manual |
| SV_PC_POWER_AXIS_5 | M. 1 = axis 5 powered. | manual |
| SV_PC_POWER_AXIS_6 | M. 1 = axis 6 powered. | manual |
| SV_PC_POWER_AXIS_7 | M. 1 = axis 7 powered. | manual |
| SV_PC_POWER_AXIS_8 | M. 1 = axis 8 powered. | manual |
| SV_PC_CYCLONE_STATUS_1 | I32. PLC and drive status bits. Bit 21 = out fiber for PLC OK; bits 0–20 and 22–31 reserved. | manual |
| SV_PC_CYCLONE_STATUS_2 | I32. Fiber-OK status per drive: bit 0 = axis 1 fiber OK, bit 1 = axis 2, …, bit 7 = axis 8; bits 9–31 reserved. PLC checks these to detect fiber4 breaks and trigger drive faults. | manual |
| SV_PC_MINI_PLC_ONLINE | I32. Online status of PLCADD1616 and other expansion PLC modules. Bit 0 = miniPLC1 online, …, bit 15 = miniPLC16 online; bits 16–31 reserved. | manual |
| SV_PLC_BUS_ONLINE | M. 1 = valid MPU11 PLC detected. Checked as part of fiber-checking section of PLC program. | manual |
| SV_X_AXIS_VALID | M. Maps to the numbered AXIS_VALID slot (SV_AXIS_VALID_1–8) for the axis currently labeled X. Convenience alias for axis-label-independent PLC programs. | manual |
| SV_Y_AXIS_VALID | M. Mapped to the numbered AXIS_VALID slot (SV_AXIS_VALID_1–8) for Y-labeled axis. | manual |
| SV_Z_AXIS_VALID | M. Mapped to the numbered AXIS_VALID slot (SV_AXIS_VALID_1–8) for Z-labeled axis. | manual |
| SV_A_AXIS_VALID | M. Mapped to the numbered AXIS_VALID slot (SV_AXIS_VALID_1–8) for A-labeled axis. | manual |
| SV_B_AXIS_VALID | M. Mapped to the numbered AXIS_VALID slot (SV_AXIS_VALID_1–8) for B-labeled axis. | manual |
| SV_C_AXIS_VALID | M. Mapped to the numbered AXIS_VALID slot (SV_AXIS_VALID_1–8) for C-labeled axis. | manual |
| SV_U_AXIS_VALID | M. Mapped to the numbered AXIS_VALID slot (SV_AXIS_VALID_1–8) for U-labeled axis. | manual |
| SV_V_AXIS_VALID | M. Mapped to the numbered AXIS_VALID slot (SV_AXIS_VALID_1–8) for V-labeled axis. | manual |
| SV_W_AXIS_VALID | M. Mapped to the numbered AXIS_VALID slot (SV_AXIS_VALID_1–8) for W-labeled axis. | manual |
| SV_X_AXIS_DRIVE_ONLINE | M. Maps to the numbered DRIVE_ONLINE slot (SV_DRIVE_ONLINE_1–8) for X-labeled axis. | manual |
| SV_Y_AXIS_DRIVE_ONLINE | M. Mapped to the numbered DRIVE_ONLINE slot (SV_DRIVE_ONLINE_1–8) for Y-labeled axis. | manual |
| SV_Z_AXIS_DRIVE_ONLINE | M. Mapped to the numbered DRIVE_ONLINE slot (SV_DRIVE_ONLINE_1–8) for Z-labeled axis. | manual |
| SV_A_AXIS_DRIVE_ONLINE | M. Mapped to the numbered DRIVE_ONLINE slot (SV_DRIVE_ONLINE_1–8) for A-labeled axis. | manual |
| SV_B_AXIS_DRIVE_ONLINE | M. Mapped to the numbered DRIVE_ONLINE slot (SV_DRIVE_ONLINE_1–8) for B-labeled axis. | manual |
| SV_C_AXIS_DRIVE_ONLINE | M. Mapped to the numbered DRIVE_ONLINE slot (SV_DRIVE_ONLINE_1–8) for C-labeled axis. | manual |
| SV_U_AXIS_DRIVE_ONLINE | M. Mapped to the numbered DRIVE_ONLINE slot (SV_DRIVE_ONLINE_1–8) for U-labeled axis. | manual |
| SV_V_AXIS_DRIVE_ONLINE | M. Mapped to the numbered DRIVE_ONLINE slot (SV_DRIVE_ONLINE_1–8) for V-labeled axis. | manual |
| SV_W_AXIS_DRIVE_ONLINE | M. Mapped to the numbered DRIVE_ONLINE slot (SV_DRIVE_ONLINE_1–8) for W-labeled axis. | manual |
| SV_X_AXIS_FIBER_OK | M. Maps to the corresponding bit in SV_PC_CYCLONE_STATUS_2 for the X-labeled axis. | manual |
| SV_Y_AXIS_FIBER_OK | M. Mapped to SV_PC_CYCLONE_STATUS_2 bit for Y-labeled axis. | manual |
| SV_Z_AXIS_FIBER_OK | M. Mapped to SV_PC_CYCLONE_STATUS_2 bit for Z-labeled axis. | manual |
| SV_A_AXIS_FIBER_OK | M. Mapped to SV_PC_CYCLONE_STATUS_2 bit for A-labeled axis. | manual |
| SV_B_AXIS_FIBER_OK | M. Mapped to SV_PC_CYCLONE_STATUS_2 bit for B-labeled axis. | manual |
| SV_C_AXIS_FIBER_OK | M. Mapped to SV_PC_CYCLONE_STATUS_2 bit for C-labeled axis. | manual |
| SV_U_AXIS_FIBER_OK | M. Mapped to SV_PC_CYCLONE_STATUS_2 bit for U-labeled axis. | manual |
| SV_V_AXIS_FIBER_OK | M. Mapped to SV_PC_CYCLONE_STATUS_2 bit for V-labeled axis. | manual |
| SV_W_AXIS_FIBER_OK | M. Mapped to SV_PC_CYCLONE_STATUS_2 bit for W-labeled axis. | manual |
| SV_Z_AXIS_POWERED | M. Maps to the numbered PC_POWER_AXIS slot (SV_PC_POWER_AXIS_1–8) for the Z-labeled axis (1 = Z axis is powered and holding position). Only the Z variant appears in the Acroloc source; equivalent aliases exist for other axes. | manual |

### Override and feedrate

| SV_ name | Meaning | Source |
|---|---|---|
| SV_PLC_FEEDRATE_KNOB | I32. Feedrate knob as the PLC presents it to CNC software. Write only once per PLC pass. | manual |
| SV_PLC_FEEDRATE_OVERRIDE | F32. Feedrate override factor for MPU11 motion control (0–2.0; 1.0 = no change). Must never be negative. Caps at machine-setup maximum. Write only once per PLC pass. | manual |
| SV_PLC_RAPID_FEEDRATE_OVERRIDE | F32. 0–2.0 velocity scale written straight to the MPU11. **Despite the name this is NOT rapids-only — measured on an ALLIN1DC 2026-08-06 to scale G1 feed moves as well as G0 rapids.** CNC12 cannot observe the write, so it bypasses SV_PC_OVERRIDE_CONTROL_FEEDRATE_OVERRIDE and with it the G74/G84 tapping lockout — a tap fed through this scale will break. Used by zero stock Centroid PLCs. There is no system variable exposing motion type, so a PLC-side G0-only gate cannot be built either. | measured |
| SV_PC_FEEDRATE_PERCENTAGE | I32. 0–200% feedrate adjustment sent by CNC software. Only needed when SV_PC_OVERRIDE_CONTROL_FEEDRATE_OVERRIDE is set. Externally written — read once per pass. | manual |
| SV_PC_OVERRIDE_CONTROL_FEEDRATE_OVERRIDE | M. 1 = feedrate override knob is allowed to change axis motion feedrate. Set by CNC software. | manual |
| SV_PC_OVERRIDE_CONTROL_FEEDHOLD | M. 1 = feedhold pauses the G-code program. Set by CNC software. | manual |

### Set axis part zero

| SV_ name | Meaning | Source |
|---|---|---|
| SV_PLC_SET_AXIS_1_PART_ZERO | M. When SET by PLC while not running a job and at main screen, requests CNC software to set Part Zero for axis 1. | manual |
| SV_PLC_SET_AXIS_2_PART_ZERO | M. Set Part Zero for axis 2. | manual |
| SV_PLC_SET_AXIS_3_PART_ZERO | M. Set Part Zero for axis 3. | manual |
| SV_PLC_SET_AXIS_4_PART_ZERO | M. Set Part Zero for axis 4. | manual |
| SV_PLC_SET_AXIS_5_PART_ZERO | M. Set Part Zero for axis 5. | manual |
| SV_PLC_SET_AXIS_6_PART_ZERO | M. Set Part Zero for axis 6. | manual |
| SV_PLC_SET_AXIS_7_PART_ZERO | M. Set Part Zero for axis 7. | manual |
| SV_PLC_SET_AXIS_8_PART_ZERO | M. Set Part Zero for axis 8. | manual |

### I/O inversion and forcing

These word SVs are used in conjunction with `SV_ENABLE_IO_OVERRIDE` and machine parameters
911–939 to allow live I/O overrides from the PLC display (ALT-I).

| SV_ name | Meaning | Source |
|---|---|---|
| SV_INVERT_INP1_16_BITS | I32. Lower 16 bits invert inputs 1–16 (LSB = INP1, MSB = INP16). | manual |
| SV_INVERT_INP17_32_BITS | I32. Lower 16 bits invert inputs 17–32. | manual |
| SV_INVERT_INP33_48_BITS | I32. Lower 16 bits invert inputs 33–48. | manual |
| SV_INVERT_INP49_64_BITS | I32. Lower 16 bits invert inputs 49–64. | manual |
| SV_INVERT_INP65_80_BITS | I32. Lower 16 bits invert inputs 65–80. | manual |
| SV_FORCE_INP1_16_BITS | I32. Lower 16 bits force state of inputs 1–16. Bit forces ON if the corresponding INVERT_INP bit is clear; forces OFF if set. | manual |
| SV_FORCE_INP17_32_BITS | I32. Force state of inputs 17–32. | manual |
| SV_FORCE_INP33_48_BITS | I32. Force state of inputs 33–48. | manual |
| SV_FORCE_INP49_64_BITS | I32. Force state of inputs 49–64. | manual |
| SV_FORCE_INP65_80_BITS | I32. Force state of inputs 65–80. | manual |
| SV_FORCE_ON_OUT1_16_BITS | I32. Lower 16 bits force ON outputs 1–16 (the corresponding FORCE_OFF_OUT bit must be clear). | manual |
| SV_FORCE_ON_OUT17_32_BITS | I32. Force ON outputs 17–32. | manual |
| SV_FORCE_ON_OUT33_48_BITS | I32. Force ON outputs 33–48. | manual |
| SV_FORCE_ON_OUT49_64_BITS | I32. Force ON outputs 49–64. | manual |
| SV_FORCE_ON_OUT65_80_BITS | I32. Force ON outputs 65–80. | manual |
| SV_FORCE_OFF_OUT1_16_BITS | I32. Lower 16 bits force OFF outputs 1–16 (the corresponding FORCE_ON_OUT bit must be clear). | manual |
| SV_FORCE_OFF_OUT17_32_BITS | I32. Force OFF outputs 17–32. | manual |
| SV_FORCE_OFF_OUT33_48_BITS | I32. Force OFF outputs 33–48. | manual |
| SV_FORCE_OFF_OUT49_64_BITS | I32. Force OFF outputs 49–64. | manual |
| SV_FORCE_OFF_OUT65_80_BITS | I32. Force OFF outputs 65–80. | manual |
| SV_FORCE_ON_MEM1_16_BITS | I32. Lower 16 bits force ON memory bits 1–16 (the corresponding FORCE_OFF_MEM bit must be clear). Forced state applied between PLC passes — PLC can still change the bit during execution. | manual |
| SV_FORCE_ON_MEM17_32_BITS | I32. Force ON MEM bits 17–32. | manual |
| SV_FORCE_ON_MEM33_48_BITS | I32. Force ON MEM bits 33–48. | manual |
| SV_FORCE_ON_MEM49_64_BITS | I32. Force ON MEM bits 49–64. | manual |
| SV_FORCE_ON_MEM65_80_BITS | I32. Force ON MEM bits 65–80. | manual |
| SV_FORCE_OFF_MEM1_16_BITS | I32. Lower 16 bits force OFF memory bits 1–16 (the corresponding FORCE_ON_MEM bit must be clear). | manual |
| SV_FORCE_OFF_MEM17_32_BITS | I32. Force OFF MEM bits 17–32. | manual |
| SV_FORCE_OFF_MEM33_48_BITS | I32. Force OFF MEM bits 33–48. | manual |
| SV_FORCE_OFF_MEM49_64_BITS | I32. Force OFF MEM bits 49–64. | manual |
| SV_FORCE_OFF_MEM65_80_BITS | I32. Force OFF MEM bits 65–80. | manual |

### Meters and misc

| SV_ name | Meaning | Source |
|---|---|---|
| SV_METER_5 | F32. Meter 5 value (–100.0 to 100.0) for display in CNC software DRO. Set by PLC. | manual |
| SV_PC_FUNCTION_1 | Appears only in a source comment `; 4. PC Keyboard Keypress: SV_PC_FUNCTION_1 - SV_PC_FUNCTION_127` used as a range label for PC-side function key events. This is NOT the same as SV_PLC_FUNCTION_1. Not documented in Appendix D; likely refers to the range of keyboard-key or skin-event SVs. | from code usage |
| SV_PC_FUNCTION_127 | Appears only in the same comment as SV_PC_FUNCTION_1 (upper bound of PC function range reference). | from code usage |
| SV_S | Partial regex capture from `SV_Stop` (mixed-case alias for SV_STOP used in some source files; the `[A-Z0-9_]+` regex stops at the lowercase `t`). Refers to SV_STOP. | from code usage |
| SV_PLC_F | Partial regex capture from mixed-case aliases `SV_PLC_FeedrateKnob_W` / `SV_PLC_Feedrate_Knob` (older-style names for SV_PLC_FEEDRATE_KNOB). Regex stops at lowercase `e`. | from code usage |
| SV_PC_K | Partial regex capture from `SV_PC_Keyboard_Key_1` appearing in a commented-out definition (`;    Kb_Escape    IS SV_PC_Keyboard_Key_1`). Regex stops at lowercase `e`. Refers to the numbered keyboard-key-state SVs. | from code usage |

### PC keyboard key state

Each keyboard key state variable is type M (1 = that key is currently pressed, 0 = not
pressed). Set by CNC software. See Appendix C of the PLC programming manual for the
key-number to physical-key mapping.

The following 96 numbers appear in the source (gaps at 17, 51, 59, 69, 70, 93, 97, 98
indicate those keys are not referenced in the available PLC programs):

| SV_ name | Meaning | Source |
|---|---|---|
| SV_PC_KEYBOARD_KEY_1 | M. Key 1 pressed state. | manual |
| SV_PC_KEYBOARD_KEY_2 | M. Key 2 pressed state. | manual |
| SV_PC_KEYBOARD_KEY_3 | M. Key 3 pressed state. | manual |
| SV_PC_KEYBOARD_KEY_4 | M. Key 4 pressed state. | manual |
| SV_PC_KEYBOARD_KEY_5 | M. Key 5 pressed state. | manual |
| SV_PC_KEYBOARD_KEY_6 | M. Key 6 pressed state. | manual |
| SV_PC_KEYBOARD_KEY_7 | M. Key 7 pressed state. | manual |
| SV_PC_KEYBOARD_KEY_8 | M. Key 8 pressed state. | manual |
| SV_PC_KEYBOARD_KEY_9 | M. Key 9 pressed state. | manual |
| SV_PC_KEYBOARD_KEY_10 | M. Key 10 pressed state. | manual |
| SV_PC_KEYBOARD_KEY_11 | M. Key 11 pressed state. | manual |
| SV_PC_KEYBOARD_KEY_12 | M. Key 12 pressed state. | manual |
| SV_PC_KEYBOARD_KEY_13 | M. Key 13 pressed state. | manual |
| SV_PC_KEYBOARD_KEY_14 | M. Key 14 pressed state. | manual |
| SV_PC_KEYBOARD_KEY_15 | M. Key 15 pressed state. | manual |
| SV_PC_KEYBOARD_KEY_16 | M. Key 16 pressed state. | manual |
| SV_PC_KEYBOARD_KEY_18 | M. Key 18 pressed state. | manual |
| SV_PC_KEYBOARD_KEY_19 | M. Key 19 pressed state. | manual |
| SV_PC_KEYBOARD_KEY_20 | M. Key 20 pressed state. | manual |
| SV_PC_KEYBOARD_KEY_21 | M. Key 21 pressed state. | manual |
| SV_PC_KEYBOARD_KEY_22 | M. Key 22 pressed state. | manual |
| SV_PC_KEYBOARD_KEY_23 | M. Key 23 pressed state. | manual |
| SV_PC_KEYBOARD_KEY_24 | M. Key 24 pressed state. | manual |
| SV_PC_KEYBOARD_KEY_25 | M. Key 25 pressed state. | manual |
| SV_PC_KEYBOARD_KEY_26 | M. Key 26 pressed state. | manual |
| SV_PC_KEYBOARD_KEY_27 | M. Key 27 pressed state. | manual |
| SV_PC_KEYBOARD_KEY_28 | M. Key 28 pressed state. | manual |
| SV_PC_KEYBOARD_KEY_29 | M. Key 29 pressed state. | manual |
| SV_PC_KEYBOARD_KEY_30 | M. Key 30 pressed state. | manual |
| SV_PC_KEYBOARD_KEY_31 | M. Key 31 pressed state. | manual |
| SV_PC_KEYBOARD_KEY_32 | M. Key 32 pressed state. | manual |
| SV_PC_KEYBOARD_KEY_33 | M. Key 33 pressed state. | manual |
| SV_PC_KEYBOARD_KEY_34 | M. Key 34 pressed state. | manual |
| SV_PC_KEYBOARD_KEY_35 | M. Key 35 pressed state. | manual |
| SV_PC_KEYBOARD_KEY_36 | M. Key 36 pressed state. | manual |
| SV_PC_KEYBOARD_KEY_37 | M. Key 37 pressed state. | manual |
| SV_PC_KEYBOARD_KEY_38 | M. Key 38 pressed state. | manual |
| SV_PC_KEYBOARD_KEY_39 | M. Key 39 pressed state. | manual |
| SV_PC_KEYBOARD_KEY_40 | M. Key 40 pressed state. | manual |
| SV_PC_KEYBOARD_KEY_41 | M. Key 41 pressed state. | manual |
| SV_PC_KEYBOARD_KEY_42 | M. Key 42 pressed state. | manual |
| SV_PC_KEYBOARD_KEY_43 | M. Key 43 pressed state. | manual |
| SV_PC_KEYBOARD_KEY_44 | M. Key 44 pressed state. | manual |
| SV_PC_KEYBOARD_KEY_45 | M. Key 45 pressed state. | manual |
| SV_PC_KEYBOARD_KEY_46 | M. Key 46 pressed state. | manual |
| SV_PC_KEYBOARD_KEY_47 | M. Key 47 pressed state. | manual |
| SV_PC_KEYBOARD_KEY_48 | M. Key 48 pressed state. | manual |
| SV_PC_KEYBOARD_KEY_49 | M. Key 49 pressed state. | manual |
| SV_PC_KEYBOARD_KEY_50 | M. Key 50 pressed state. | manual |
| SV_PC_KEYBOARD_KEY_52 | M. Key 52 pressed state. | manual |
| SV_PC_KEYBOARD_KEY_53 | M. Key 53 pressed state. | manual |
| SV_PC_KEYBOARD_KEY_54 | M. Key 54 pressed state. | manual |
| SV_PC_KEYBOARD_KEY_55 | M. Key 55 pressed state. | manual |
| SV_PC_KEYBOARD_KEY_56 | M. Key 56 pressed state. | manual |
| SV_PC_KEYBOARD_KEY_57 | M. Key 57 pressed state. | manual |
| SV_PC_KEYBOARD_KEY_58 | M. Key 58 pressed state. | manual |
| SV_PC_KEYBOARD_KEY_60 | M. Key 60 pressed state. | manual |
| SV_PC_KEYBOARD_KEY_61 | M. Key 61 pressed state. | manual |
| SV_PC_KEYBOARD_KEY_62 | M. Key 62 pressed state. | manual |
| SV_PC_KEYBOARD_KEY_63 | M. Key 63 pressed state. | manual |
| SV_PC_KEYBOARD_KEY_64 | M. Key 64 pressed state. | manual |
| SV_PC_KEYBOARD_KEY_65 | M. Key 65 pressed state. | manual |
| SV_PC_KEYBOARD_KEY_66 | M. Key 66 pressed state. | manual |
| SV_PC_KEYBOARD_KEY_67 | M. Key 67 pressed state. | manual |
| SV_PC_KEYBOARD_KEY_68 | M. Key 68 pressed state. | manual |
| SV_PC_KEYBOARD_KEY_71 | M. Key 71 pressed state. | manual |
| SV_PC_KEYBOARD_KEY_72 | M. Key 72 pressed state. | manual |
| SV_PC_KEYBOARD_KEY_73 | M. Key 73 pressed state. | manual |
| SV_PC_KEYBOARD_KEY_74 | M. Key 74 pressed state. | manual |
| SV_PC_KEYBOARD_KEY_75 | M. Key 75 pressed state. | manual |
| SV_PC_KEYBOARD_KEY_76 | M. Key 76 pressed state. | manual |
| SV_PC_KEYBOARD_KEY_77 | M. Key 77 pressed state. | manual |
| SV_PC_KEYBOARD_KEY_78 | M. Key 78 pressed state. | manual |
| SV_PC_KEYBOARD_KEY_79 | M. Key 79 pressed state. | manual |
| SV_PC_KEYBOARD_KEY_80 | M. Key 80 pressed state. | manual |
| SV_PC_KEYBOARD_KEY_81 | M. Key 81 pressed state. | manual |
| SV_PC_KEYBOARD_KEY_82 | M. Key 82 pressed state. | manual |
| SV_PC_KEYBOARD_KEY_83 | M. Key 83 pressed state. | manual |
| SV_PC_KEYBOARD_KEY_84 | M. Key 84 pressed state. | manual |
| SV_PC_KEYBOARD_KEY_85 | M. Key 85 pressed state. | manual |
| SV_PC_KEYBOARD_KEY_86 | M. Key 86 pressed state. | manual |
| SV_PC_KEYBOARD_KEY_87 | M. Key 87 pressed state. | manual |
| SV_PC_KEYBOARD_KEY_88 | M. Key 88 pressed state. | manual |
| SV_PC_KEYBOARD_KEY_89 | M. Key 89 pressed state. | manual |
| SV_PC_KEYBOARD_KEY_90 | M. Key 90 pressed state. | manual |
| SV_PC_KEYBOARD_KEY_91 | M. Key 91 pressed state. | manual |
| SV_PC_KEYBOARD_KEY_92 | M. Key 92 pressed state. | manual |
| SV_PC_KEYBOARD_KEY_94 | M. Key 94 pressed state. | manual |
| SV_PC_KEYBOARD_KEY_95 | M. Key 95 pressed state. | manual |
| SV_PC_KEYBOARD_KEY_96 | M. Key 96 pressed state. | manual |
| SV_PC_KEYBOARD_KEY_99 | M. Key 99 pressed state. | manual |
| SV_PC_KEYBOARD_KEY_100 | M. Key 100 pressed state. | manual |
| SV_PC_KEYBOARD_KEY_101 | M. Key 101 pressed state. | manual |
| SV_PC_KEYBOARD_KEY_102 | M. Key 102 pressed state. | manual |
| SV_PC_KEYBOARD_KEY_103 | M. Key 103 pressed state. | manual |
| SV_PC_KEYBOARD_KEY_104 | M. Key 104 pressed state. | manual |

### Skin events (CNC skinning API)

Each skin event variable is type M. Skinning applications (e.g. Centroid Virtual Control
Panel — VCP) SET or RST these via the CNC Skinning API. The PLC program reads them to
detect operator input from virtual panels.

Convention (VCP, not Appendix D): SV_SKIN_EVENT_1–50 map to the fifty keys on a hardware
jog panel by VCP convention (SV_SKIN_EVENT_1 = Spindle+, left-to-right/top-to-bottom,
SV_SKIN_EVENT_50 = CYCLE_START). This key-to-event-number mapping is a VCP application
convention, not documented in Appendix D of the PLC manual.

All 128 entries (SV_SKIN_EVENT_1 through SV_SKIN_EVENT_128) are present in the source.

| SV_ name | Meaning | Source |
|---|---|---|
| SV_SKIN_EVENT_1 | M. Skinning event bit 1. By VCP convention: Spindle+ key on virtual jog panel (VCP convention, not Appendix D). | from code usage |
| SV_SKIN_EVENT_2 | M. Skinning event bit 2. | manual |
| SV_SKIN_EVENT_3 | M. Skinning event bit 3. | manual |
| SV_SKIN_EVENT_4 | M. Skinning event bit 4. | manual |
| SV_SKIN_EVENT_5 | M. Skinning event bit 5. | manual |
| SV_SKIN_EVENT_6 | M. Skinning event bit 6. | manual |
| SV_SKIN_EVENT_7 | M. Skinning event bit 7. | manual |
| SV_SKIN_EVENT_8 | M. Skinning event bit 8. | manual |
| SV_SKIN_EVENT_9 | M. Skinning event bit 9. | manual |
| SV_SKIN_EVENT_10 | M. Skinning event bit 10. | manual |
| SV_SKIN_EVENT_11 | M. Skinning event bit 11. | manual |
| SV_SKIN_EVENT_12 | M. Skinning event bit 12. | manual |
| SV_SKIN_EVENT_13 | M. Skinning event bit 13. | manual |
| SV_SKIN_EVENT_14 | M. Skinning event bit 14. | manual |
| SV_SKIN_EVENT_15 | M. Skinning event bit 15. | manual |
| SV_SKIN_EVENT_16 | M. Skinning event bit 16. | manual |
| SV_SKIN_EVENT_17 | M. Skinning event bit 17. | manual |
| SV_SKIN_EVENT_18 | M. Skinning event bit 18. | manual |
| SV_SKIN_EVENT_19 | M. Skinning event bit 19. | manual |
| SV_SKIN_EVENT_20 | M. Skinning event bit 20. | manual |
| SV_SKIN_EVENT_21 | M. Skinning event bit 21. | manual |
| SV_SKIN_EVENT_22 | M. Skinning event bit 22. | manual |
| SV_SKIN_EVENT_23 | M. Skinning event bit 23. | manual |
| SV_SKIN_EVENT_24 | M. Skinning event bit 24. | manual |
| SV_SKIN_EVENT_25 | M. Skinning event bit 25. | manual |
| SV_SKIN_EVENT_26 | M. Skinning event bit 26. | manual |
| SV_SKIN_EVENT_27 | M. Skinning event bit 27. | manual |
| SV_SKIN_EVENT_28 | M. Skinning event bit 28. | manual |
| SV_SKIN_EVENT_29 | M. Skinning event bit 29. | manual |
| SV_SKIN_EVENT_30 | M. Skinning event bit 30. | manual |
| SV_SKIN_EVENT_31 | M. Skinning event bit 31. | manual |
| SV_SKIN_EVENT_32 | M. Skinning event bit 32. | manual |
| SV_SKIN_EVENT_33 | M. Skinning event bit 33. | manual |
| SV_SKIN_EVENT_34 | M. Skinning event bit 34. | manual |
| SV_SKIN_EVENT_35 | M. Skinning event bit 35. | manual |
| SV_SKIN_EVENT_36 | M. Skinning event bit 36. | manual |
| SV_SKIN_EVENT_37 | M. Skinning event bit 37. | manual |
| SV_SKIN_EVENT_38 | M. Skinning event bit 38. | manual |
| SV_SKIN_EVENT_39 | M. Skinning event bit 39. | manual |
| SV_SKIN_EVENT_40 | M. Skinning event bit 40. | manual |
| SV_SKIN_EVENT_41 | M. Skinning event bit 41. | manual |
| SV_SKIN_EVENT_42 | M. Skinning event bit 42. | manual |
| SV_SKIN_EVENT_43 | M. Skinning event bit 43. | manual |
| SV_SKIN_EVENT_44 | M. Skinning event bit 44. | manual |
| SV_SKIN_EVENT_45 | M. Skinning event bit 45. | manual |
| SV_SKIN_EVENT_46 | M. Skinning event bit 46. | manual |
| SV_SKIN_EVENT_47 | M. Skinning event bit 47. | manual |
| SV_SKIN_EVENT_48 | M. Skinning event bit 48. | manual |
| SV_SKIN_EVENT_49 | M. Skinning event bit 49. | manual |
| SV_SKIN_EVENT_50 | M. Skinning event bit 50. By VCP convention: CYCLE_START key on virtual jog panel (VCP convention, not Appendix D). | from code usage |
| SV_SKIN_EVENT_51 | M. Skinning event bit 51. | manual |
| SV_SKIN_EVENT_52 | M. Skinning event bit 52. | manual |
| SV_SKIN_EVENT_53 | M. Skinning event bit 53. | manual |
| SV_SKIN_EVENT_54 | M. Skinning event bit 54. | manual |
| SV_SKIN_EVENT_55 | M. Skinning event bit 55. | manual |
| SV_SKIN_EVENT_56 | M. Skinning event bit 56. | manual |
| SV_SKIN_EVENT_57 | M. Skinning event bit 57. | manual |
| SV_SKIN_EVENT_58 | M. Skinning event bit 58. | manual |
| SV_SKIN_EVENT_59 | M. Skinning event bit 59. | manual |
| SV_SKIN_EVENT_60 | M. Skinning event bit 60. | manual |
| SV_SKIN_EVENT_61 | M. Skinning event bit 61. | manual |
| SV_SKIN_EVENT_62 | M. Skinning event bit 62. | manual |
| SV_SKIN_EVENT_63 | M. Skinning event bit 63. | manual |
| SV_SKIN_EVENT_64 | M. Skinning event bit 64. | manual |
| SV_SKIN_EVENT_65 | M. Skinning event bit 65. | manual |
| SV_SKIN_EVENT_66 | M. Skinning event bit 66. | manual |
| SV_SKIN_EVENT_67 | M. Skinning event bit 67. | manual |
| SV_SKIN_EVENT_68 | M. Skinning event bit 68. | manual |
| SV_SKIN_EVENT_69 | M. Skinning event bit 69. | manual |
| SV_SKIN_EVENT_70 | M. Skinning event bit 70. | manual |
| SV_SKIN_EVENT_71 | M. Skinning event bit 71. | manual |
| SV_SKIN_EVENT_72 | M. Skinning event bit 72. | manual |
| SV_SKIN_EVENT_73 | M. Skinning event bit 73. | manual |
| SV_SKIN_EVENT_74 | M. Skinning event bit 74. | manual |
| SV_SKIN_EVENT_75 | M. Skinning event bit 75. | manual |
| SV_SKIN_EVENT_76 | M. Skinning event bit 76. | manual |
| SV_SKIN_EVENT_77 | M. Skinning event bit 77. | manual |
| SV_SKIN_EVENT_78 | M. Skinning event bit 78. | manual |
| SV_SKIN_EVENT_79 | M. Skinning event bit 79. | manual |
| SV_SKIN_EVENT_80 | M. Skinning event bit 80. | manual |
| SV_SKIN_EVENT_81 | M. Skinning event bit 81. | manual |
| SV_SKIN_EVENT_82 | M. Skinning event bit 82. | manual |
| SV_SKIN_EVENT_83 | M. Skinning event bit 83. | manual |
| SV_SKIN_EVENT_84 | M. Skinning event bit 84. | manual |
| SV_SKIN_EVENT_85 | M. Skinning event bit 85. | manual |
| SV_SKIN_EVENT_86 | M. Skinning event bit 86. | manual |
| SV_SKIN_EVENT_87 | M. Skinning event bit 87. | manual |
| SV_SKIN_EVENT_88 | M. Skinning event bit 88. | manual |
| SV_SKIN_EVENT_89 | M. Skinning event bit 89. | manual |
| SV_SKIN_EVENT_90 | M. Skinning event bit 90. | manual |
| SV_SKIN_EVENT_91 | M. Skinning event bit 91. | manual |
| SV_SKIN_EVENT_92 | M. Skinning event bit 92. | manual |
| SV_SKIN_EVENT_93 | M. Skinning event bit 93. | manual |
| SV_SKIN_EVENT_94 | M. Skinning event bit 94. | manual |
| SV_SKIN_EVENT_95 | M. Skinning event bit 95. | manual |
| SV_SKIN_EVENT_96 | M. Skinning event bit 96. | manual |
| SV_SKIN_EVENT_97 | M. Skinning event bit 97. | manual |
| SV_SKIN_EVENT_98 | M. Skinning event bit 98. | manual |
| SV_SKIN_EVENT_99 | M. Skinning event bit 99. | manual |
| SV_SKIN_EVENT_100 | M. Skinning event bit 100. | manual |
| SV_SKIN_EVENT_101 | M. Skinning event bit 101. | manual |
| SV_SKIN_EVENT_102 | M. Skinning event bit 102. | manual |
| SV_SKIN_EVENT_103 | M. Skinning event bit 103. | manual |
| SV_SKIN_EVENT_104 | M. Skinning event bit 104. | manual |
| SV_SKIN_EVENT_105 | M. Skinning event bit 105. | manual |
| SV_SKIN_EVENT_106 | M. Skinning event bit 106. | manual |
| SV_SKIN_EVENT_107 | M. Skinning event bit 107. | manual |
| SV_SKIN_EVENT_108 | M. Skinning event bit 108. | manual |
| SV_SKIN_EVENT_109 | M. Skinning event bit 109. | manual |
| SV_SKIN_EVENT_110 | M. Skinning event bit 110. | manual |
| SV_SKIN_EVENT_111 | M. Skinning event bit 111. | manual |
| SV_SKIN_EVENT_112 | M. Skinning event bit 112. | manual |
| SV_SKIN_EVENT_113 | M. Skinning event bit 113. | manual |
| SV_SKIN_EVENT_114 | M. Skinning event bit 114. | manual |
| SV_SKIN_EVENT_115 | M. Skinning event bit 115. | manual |
| SV_SKIN_EVENT_116 | M. Skinning event bit 116. | manual |
| SV_SKIN_EVENT_117 | M. Skinning event bit 117. | manual |
| SV_SKIN_EVENT_118 | M. Skinning event bit 118. | manual |
| SV_SKIN_EVENT_119 | M. Skinning event bit 119. | manual |
| SV_SKIN_EVENT_120 | M. Skinning event bit 120. | manual |
| SV_SKIN_EVENT_121 | M. Skinning event bit 121. | manual |
| SV_SKIN_EVENT_122 | M. Skinning event bit 122. | manual |
| SV_SKIN_EVENT_123 | M. Skinning event bit 123. | manual |
| SV_SKIN_EVENT_124 | M. Skinning event bit 124. | manual |
| SV_SKIN_EVENT_125 | M. Skinning event bit 125. | manual |
| SV_SKIN_EVENT_126 | M. Skinning event bit 126. | manual |
| SV_SKIN_EVENT_127 | M. Skinning event bit 127. | manual |
| SV_SKIN_EVENT_128 | M. Skinning event bit 128. | manual |
