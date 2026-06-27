# M-Code Macro Quick Reference

M-code macros live in the repo root as `mfuncN.mac`. CNC12 executes `mfuncN.mac` when the
part program issues `MN`. For the mechanics of how macros read PLC outputs (`#(60000+n)`) and
assert/deassert PLC bits (`M94 /bit`, `M95 /bit`), see the general skill's
[resource-addressing reference](../../centroid-plc-programming/reference/resources.md).

## Macro summary

| Macro      | Fires on | What it does |
|------------|----------|--------------|
| `mfunc3`   | M3       | Clears CCW (`M95 /2`), sets CW (`M94 /1`); loops displaying "Please Select Auto Spindle To Continue!" until `SpindleAutoManualLED` (`OUT1058`, `#61058`) is asserted |
| `mfunc4`   | M4       | Clears CW (`M95 /1`), sets CCW (`M94 /2`); same auto-spindle loop as M3 |
| `mfunc6`   | M6       | Drives the full ATC tool-change sequence — see [atc-flow.md](./atc-flow.md) |
| `mfunc7`   | M7       | Clears flood (`M95 /3`), sets mist (`M94 /5`); loops displaying "Please Select Auto Coolant To Continue!" until `CoolantAutoManualLED` (`OUT1077`, `#61077`) is asserted |
| `mfunc8`   | M8       | Clears mist (`M95 /5`), sets flood (`M94 /3`); same auto-coolant loop as M7 |
| `mfunc10`  | M10      | Sets clamp on (`M94 /4`) |
| `mfunc11`  | M11      | Clears clamp (`M95 /4`) |

## Shared guard — preserve when editing

All seven macros skip execution in graph/search mode using the following guard at the top of
the file, and they all terminate at the `N1000` label:

```
IF #4201 || #4202 THEN GOTO 1000   ;Skip macro if graphing or searching
...
N1000
```

**Always preserve this guard and the `N1000` label when editing any macro.** CNC12's
graphic/search mode will otherwise execute side-effectful hardware commands during dry runs.

### mfunc6 guard note

`mfunc6.mac` uses reversed operand order (`IF #4202 || #4201`) and omits the inline comment
— functionally identical to the other six macros, but visually different. Do not "correct"
the order; the logic is fine as written.

## mfunc6 key steps (abbreviated)

The full flow is in [atc-flow.md](./atc-flow.md). The macro's sequence is:

1. `IF #50001` — prevents lookahead buffering during the tool change
2. `M109 /1/2` — disables feed and speed overrides
3. `S0` / `M5` / `M9` — zero spindle speed, stop spindle, turn off coolant
4. `G53 Z0` — retract Z to machine home (tool-change position)
5. `M107` — send target tool number to PLC
6. `M94 /8` — assert `M6_SV` (bit 8) to trigger `ATCStage` in the PLC
7. `M100 /93016` — block until `ATCStage` (STG16) resets (carousel cycle complete)
8. `M95 /8` — deassert `M6_SV` to close out the tool-change handshake
