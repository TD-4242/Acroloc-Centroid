---
name: centroid-plc-programming
description: Use when writing, reading, or debugging Centroid CNC12 / MPU11 (ALLIN1DC) PLC stage-language source (.src) or M-code macros (mfunc*.mac) — covers stage/ladder syntax, resource types (INP/OUT/MEM/W/T/STG), the SV_* system-variable catalog, operator-message encoding, and an index of official example PLC projects to crib from.
---

# Centroid PLC Programming

## When to use / when not

Use this skill for any work involving Centroid CNC12 / MPU11 (ALLIN1DC) PLC stage-language source (`.src`) or M-code macros (`mfunc*.mac`): reading existing programs, writing new stages, debugging logic, looking up resource addresses, or finding system-variable names.

**Do not use this skill** for questions specific to this machine's ATC wiring, carousel position encoding, or the custom M6 tool-change flow — those details live in the `acroloc-atc` skill.

## Language essentials

The PLC source file has two halves. The **definition section** (top) uses `Name IS Resource` to bind symbolic names to hardware resources at compile time — no runtime cost:

```
EStopOk    IS INP11
Lube       IS OUT2
MainStage  IS STG4
```

The **stage section** (bottom) is a flat list of `STGn`-numbered stages. On every **scan** the executor sweeps all stages top to bottom and runs only the logic inside stages that are currently SET; RST stages are skipped entirely. Regular stages (`STG`) run at 50 scans/second; fast stages (`FSTG`) run at 1000 scans/second. Hardware input values are snapshot-frozen at the start of each scan; memory bits, outputs, and stage bits update live during the scan.

Every executable line begins with `IF`. Multiple actions follow `THEN`, comma-separated. Stages enable and disable each other with `SET` and `RST`:

```
IF M6_SV THEN SET ATCStage, RST MainStage
```

There is no `ELSE` keyword — complement a condition with a second `IF` on the next line. Bit-type variables (e.g. `INP`, `OUT`, `MEM`, `STG`, plus `FSTG`/`PD`/SV bits) are used directly as conditions. Words (`W`) require a relational operator (`==`, `!=`, `>`, etc.) — a bare Word in a condition is a compiler error. Timers (`T`) may be used directly (true when the timer has expired) or with a relational expression to test elapsed time in ms.

## Reference router

| Reference file | Look here when… |
|---|---|
| `reference/syntax.md` | You need statement syntax: `IF`/`THEN`, `SET`/`RST`/`JMP`, operator precedence, the output-coil `()` form, comment style, or stage/section header conventions |
| `reference/resources.md` | You need a resource type (INP/OUT/MEM/W/T/STG/FW/PD), its address range, the naming-suffix convention (`_I`/`_O`/`_M`/`_W`/`_T`/`_SV`/`_C`), or the macro↔PLC variable offsets (`#(60000+n)`, `M94`/`M95`) |
| `reference/system-variables.md` | You need to look up or verify an `SV_*` system-variable name, its direction (CNC-to-PLC vs. PLC-to-CNC), or its data type |
| `reference/messages.md` | You need to encode or decode an operator-message constant (`value = type + 256 × msgNumber`), understand `plcmsg.txt` format, or send/clear a message from stage logic |
| `reference/examples-index.md` | You want to crib a proven pattern from an official Centroid example project (ATC, jog, spindle, brake, remote start, etc.) |
