# Centroid PLC Resource Types Reference

**Sources used:**
- `scratchpad/plc-manual.txt` — extracted text of Centroid CNC PLC Programming Manual rev7 (2022–23); primary source for data-type semantics and macro variable table.
- `docs/official/_ALLIN1DC/_basic/cncm/allin1dc-basic-v6.src` — Centroid stock ALLIN1DC basic PLC, confirming INP/OUT/MEM/W/T/STG addressing forms.
- `Centroid-Acroloc-ALLIN1DC.src` — Acroloc custom PLC, confirming FW/_C/_I/_O/_SV suffix examples.
- `mfunc3.mac`, `mfunc6.mac` — real macros, confirming `#(60000+n)` and M94/M95 access patterns.

This file covers **what resource types exist**, their addressing forms, the naming-suffix convention, and how macros read or trigger PLC resources. It does not duplicate operator or statement syntax — see `reference/syntax.md` for those.

---

## Resource Types

The `IS` keyword in the definition section binds a symbolic name to a hardware or internal resource. The resource type and instance number together fully specify the address. Every type has a fixed range.

> Source: `scratchpad/plc-manual.txt` lines 481–496 (Data Types table)

| Keyword | Type | Instance range | Notes |
|---------|------|----------------|-------|
| `INP` | Physical input bit | INP1–INP1312 | Hardware switch/sensor inputs. Values are snapshot-frozen at the start of each PLC scan; the same input reads the same throughout the scan. |
| `OUT` | Physical output bit | OUT1–OUT1312 | Hardware relay/driver outputs. The output image updates live during the scan; a later line in the same scan sees the value written by an earlier line. |
| `MEM` | Internal memory bit | MEM1–MEM1024 | Pure logic/state bits, not wired to hardware. Update live during the scan. |
| `STG` | Stage bit | STG1–STG256 | `STG1` is SET automatically at startup. Logic inside a stage only executes when the stage bit is SET. |
| `FSTG` | Fast stage bit | FSTG1–FSTG256 | Like STG but executes at 1000 scans/s instead of 50 scans/s. |
| `T` | Timer | T1–T128 | 32-bit millisecond countdown. `T1–T64` available before CNC12 v4.22; `T1–T128` from v4.22. Timer values are snapshot-frozen for the scan, like inputs. |
| `PD` | One-shot (positive differential) | PD1–PD256 | Rising-edge detector. SET for one scan when the condition transitions false→true. |
| `W` | 32-bit signed integer word | W1–W128 | `W1–W88` visible in the PLC Diagnostic screen and accessible as G-code variables. |
| `DW` | 64-bit signed integer | DW1–DW128 | `DW1–DW22` visible in the PLC Diagnostic screen and accessible as G-code variables. |
| `FW` | 32-bit floating-point word | FW1–FW128 | `FW1–FW44` visible in the PLC Diagnostic screen and accessible as G-code variables. |
| `DFW` | 64-bit floating-point | DFW1–DFW128 | `DFW1–DFW22` visible in the PLC Diagnostic screen and accessible as G-code variables. |

### Addressing form

```
Name IS Keyword n
```

`n` is a decimal integer within the range for that type. Examples (all real definition lines):

```
Ax1_MinusLimitOk              IS INP1          ; allin1dc-basic-v6.src, line 168
EStopOk                       IS INP11         ; allin1dc-basic-v6.src, line 178
Lube                          IS OUT2          ; allin1dc-basic-v6.src, line 317
SpinAutoModeLED               IS OUT1058       ; allin1dc-basic-v6.src, line 362
PLCExecutorFault_M            IS MEM1          ; allin1dc-basic-v6.src, line 424
SoftwareNotReady_M            IS MEM2          ; allin1dc-basic-v6.src, line 425
WatchDogStage                 IS STG1          ; allin1dc-basic-v6.src, line 1001
MainStage                     IS STG4          ; allin1dc-basic-v6.src, line 1004
LubeAccumTime_W               IS W1            ; allin1dc-basic-v6.src, line 902
FeedrateKnob_W                IS W3            ; allin1dc-basic-v6.src, line 904
MsgClear_T                    IS T1            ; allin1dc-basic-v6.src, line 987
ATCMotor_O                    IS OUT17         ; Centroid-Acroloc-ALLIN1DC.src, line 382
ATC_Pos1_I                    IS INP32         ; Centroid-Acroloc-ALLIN1DC.src, line 234
SpinRangeAdjust_FW            IS FW1           ; Centroid-Acroloc-ALLIN1DC.src, line 1095
CarouselToolID_W              IS W71           ; Centroid-Acroloc-ALLIN1DC.src, line 1087
```

### System Variables (SV)

System Variables are predefined names built into CNC12. They are not numbered like INP/OUT — they are referenced directly by their full `SV_` name. Two classes:

- **CNC-to-PLC** (`SV_PC_*`): written by CNC software, read by the PLC.
- **PLC-to-CNC** (`SV_PLC_*`): written by the PLC, read by CNC software.

A system variable may be a bit type (used like INP/OUT) or a word type (used like W). The `M94`/`M95` bits are bit-type SVs named `SV_M94_M95_1` through `SV_M94_M95_128`.

> Source: `scratchpad/plc-manual.txt` lines 700–707

### Constants

Constants are numeric literals (integers, floats, or arithmetic expressions) bound with `IS`. They have no resource type — they are compile-time substitutions.

> Source: `scratchpad/plc-manual.txt` lines 527–537

```
MIN_FROR_PCT_C                  IS 1          ; Centroid-Acroloc-ALLIN1DC.src, line 126
ASYNC_MSG_CLEAR_C               IS 2          ; Centroid-Acroloc-ALLIN1DC.src, line 127
PLC_EXECUTOR_FLT_MSG_C          IS 257        ; Centroid-Acroloc-ALLIN1DC.src, line 128
```

Message constants encode as `value = msgNumber + 256 * msgFile`. The message text lives in CNC12's message files, not in the PLC source.

---

## Naming-Suffix Convention

Centroid's style guide (and the convention used in all stock and Acroloc sources) appends a short suffix to variable names to communicate the resource type without searching the definitions. This is a convention only — the compiler is case-insensitive and does not enforce it.

> Source: `scratchpad/plc-manual.txt` lines 384–404 (naming-convention table); confirmed by real definitions in `allin1dc-basic-v6.src` and `Centroid-Acroloc-ALLIN1DC.src`.

| Suffix | Resource type | Example |
|--------|---------------|---------|
| `_I` | `INP` — physical input bit | `ATC_Pos1_I IS INP32` (Centroid-Acroloc-ALLIN1DC.src, line 234) |
| `_O` | `OUT` — physical output bit | `ATCMotor_O IS OUT17` (Centroid-Acroloc-ALLIN1DC.src, line 382) |
| `_M` | `MEM` — memory bit | `SoftwareNotReady_M IS MEM2` (allin1dc-basic-v6.src, line 425) |
| `_W` | `W` — 32-bit integer word | `CarouselToolID_W IS W71` (Centroid-Acroloc-ALLIN1DC.src, line 1087) |
| `_FW` | `FW` — 32-bit floating-point word | `SpinRangeAdjust_FW IS FW1` (Centroid-Acroloc-ALLIN1DC.src, line 1095) |
| `_T` | `T` — timer | `MsgClear_T IS T1` (allin1dc-basic-v6.src, line 987) |
| `_SV` | System Variable | `M6_SV IS SV_M94_M95_8` (Centroid-Acroloc-ALLIN1DC.src, line 1036) |
| `_C` | Constant | `MIN_FROR_PCT_C IS 1` (Centroid-Acroloc-ALLIN1DC.src, line 126) |

Notes:
- Stages conventionally use no suffix: the name itself ends with `Stage` (e.g., `InitialStage`, `ATCStage`). The manual notes "Alternatively use STG" but the stock PLC programs universally use CamelCase with `Stage` in the name.
- The `_DW`, `_DFW`, `_PD` suffixes are less common but follow the same pattern when used (e.g., `BigCounter_DW` from the manual's naming table, line 390).
- Inputs and Outputs that are not in the Acroloc custom code often omit the suffix entirely (e.g., `Lube IS OUT2`, `EStopOk IS INP11`) — this is the stock Centroid style for I/O that is self-describing.

---

## Macro ↔ PLC Access

G-code macro files (`mfuncN.mac`) can read PLC resource state and trigger PLC actions through two mechanisms.

### Reading PLC resource state from a macro

The CNC12 macro variable space exposes PLC resource states as read-only variables at fixed offsets. These are confirmed in the manual's G/M-code variable table:

> Source: `scratchpad/plc-manual.txt` lines 6810–6829 (Appendix F)

| PLC resource | Macro variable | Example |
|--------------|----------------|---------|
| INP n | `#(50000 + n)` | INP1 → `#50001` |
| OUT n | `#(60000 + n)` | OUT1058 → `#61058` |
| MEM n | `#(70000 + n)` | MEM1 → `#70001` |
| T n (status bit) | `#(90000 + n)` | T1 → `#90001` |
| STG n (status bit) | `#(93000 + n)` | STG16 → `#93016` |
| W n | `#(96000 + n)` | W1 → `#96001` (W1–W44 only) |
| FW n | `#(98000 + n)` | FW1 → `#98001` (FW1–FW44 only) |

**Confirmed real usage** — `mfunc3.mac`:

```
; SpindleAutoManualLED		IS OUT1058	(#61058)     ; mfunc3.mac, line 15 (comment)
IF #61058 THEN GOTO 1000         ;skip the check if AutoSpindle is on   ; mfunc3.mac, line 28
IF !#61058 THEN M225 #140 "Please Select Auto Spindle To Continue!"      ; mfunc3.mac, line 32
```

This output is `OUT1058` — `SpinAutoModeLED_O` in `Centroid-Acroloc-ALLIN1DC.src` line 414, and `SpinAutoModeLED` (no suffix) in `allin1dc-basic-v6.src` line 362. `60000 + 1058 = 61058`. The macro reads the output state as `#61058`.

Stage status bits are also used: `mfunc6.mac` line 25 uses `M100 /93016` (wait for `#93016` to clear), where `93000 + 16 = 93016` = `ATCStage IS STG16`.

### Triggering PLC actions from a macro (M94/M95)

`M94 /n` sets bit n of the `SV_M94_M95_*` system variable group; `M95 /n` resets it. The PLC program reads these bits as named SVs (e.g., `M6_SV IS SV_M94_M95_8`). This is the standard mechanism for a macro to request that the PLC take an action and for the PLC to signal completion back to the macro.

**Confirmed real lines** — `mfunc6.mac`:

```
M94 /8          ; Set M6_SV to start tool change stage   ; mfunc6.mac, line 23
M95 /8          ; reset M6_SV to stop tool change stage when done  ; mfunc6.mac, line 26
```

On the PLC side (`Centroid-Acroloc-ALLIN1DC.src`, line 1036):

```
M6_SV                            IS SV_M94_M95_8 ; Acroloc Tool change request
```

Bits 1–128 are available; the macro uses the decimal bit number after `/`. The same bit number is used on both ends: `M94 /8` sets `SV_M94_M95_8`, which the PLC reads as `M6_SV`.

> Source pattern: `scratchpad/plc-manual.txt` lines 3051–3054 (Using M94/M95 Bits); real usage confirmed from `mfunc6.mac` and `Centroid-Acroloc-ALLIN1DC.src`.
