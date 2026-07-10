# Axes & travel

Per-axis travel, usable envelope, and motion characteristics of the Acroloc Series 10.

## Travel limits

| Axis | Travel |
|------|--------|
| X | 31.5 in |
| Y | 16 in |
| Z | 8 in (see usable-envelope note) |

## Usable Z envelope

Although Z has 8 in of total travel, only about **6 in** is useful for machining — the
range from **Z −2 to Z −8**. Heavy machining should be done as close to **Z −2** as
possible (maximum rigidity / minimum spindle extension).

## Motion characteristics

- **Rapid traverse rates (per axis):** TBD — confirm with owner
- **Maximum programmed feedrate:** TBD — confirm with owner
- **Ways / guide type (box ways vs. linear rail):** TBD — confirm with owner
- **Ballscrew vs. acme / drive type:** TBD — confirm with owner
- **Positioning accuracy / repeatability:** TBD — confirm with owner
- **Home / reference positions (per axis):** Home switches share the limit-switch inputs
  (report Home columns match the Limit columns) — see *Limit switches & direction reversal*
  below. Home offsets/positions: TBD — confirm with owner

> Travel limits in the CNC12 control are set as software limits during commissioning; see
> the `centroid-allin1dc-install` skill for the travel-limit setup procedure.

## Limit switches & direction reversal (the 411 current-inhibit trap)

The ALLIN1DC's first six inputs (**INP1–INP6**) are **hardware current-inhibits**, hard-wired
per axis and per *native* motor direction. They act **below** the PLC and CNC12
configuration — you cannot remap them in software, and the current-inhibit happens in the
board hardware, not the PLC scan.

| Input | Inhibits motor current on… | PLC symbol (`Centroid-Acroloc-ALLIN1DC.src`) |
|-------|----------------------------|----------------------------------------------|
| INP1 / INP2 | Axis 1 (X) native − / + | `Ax1_MinusLimitOk_I` / `Ax1_PlusLimitOk_I` |
| INP3 / INP4 | Axis 2 (Y) native − / + | `Ax2_MinusLimitOk_I` / `Ax2_PlusLimitOk_I` |
| INP5 / INP6 | Axis 3 (Z) native − / + | `Ax3_MinusLimitOk_I` / `Ax3_PlusLimitOk_I` |

Odd input = native-minus inhibit, even = native-plus. When one goes open (its NC limit
switch trips), the board **refuses to apply current** to that motor in that native
direction, no matter what CNC12 commands.

The `Ax*_*LimitOk_I` symbols name each input by the board's **native** direction — which is
correct. They are not referenced anywhere in the stage logic (the inhibit is a hardware
function), but they still label the inputs. The subtlety: on a **direction-reversed** axis,
native − is logical +, so the *physical* switch wired to (e.g.) `Ax3_MinusLimitOk_I` (INP5)
is the **Z+** travel switch. Read the names as native-direction and confirm physical wiring
against the Motor Parameters limit-input numbers.

### The direction-reversal swap rule

If an axis has **Direction Reversal = Yes** (Machine Config → Motor Parameters), its
*logical* `+` is the board's *native* `−`. So on a reversed axis you must **both**:

1. Wire the physical **+** limit switch to the **odd** (native-minus) input and the **−**
   switch to the **even** input; **and**
2. Swap that axis's limit-input numbers in the Motor Parameters table to match.

Get it wrong and tripping the limit inhibits current in the exact direction you need to
retract → **Error 411 "full power without motion"** when backing off (CNC12 commands the
move, the board blocks the current, the encoder never moves — a following-error, hence
"full power"). The other, permitted jog direction drives *into* the stop.

### Current confirmed config (report 0008DC111213, 2026-07-05)

| Axis | Label | Dir Reversed | Limit inputs (− / +) | Notes |
|------|-------|--------------|----------------------|-------|
| 1 | X | No  | 1 / 2 (natural) | not reversed → natural order, correct |
| 2 | Y | Yes | 4 / 3 (swapped)  | the 2026-07-05 report caught it at 3/4 as a **deliberate test**; since corrected |
| 3 | Z | Yes | 6 / 5 (swapped)  | **physical + switch on INP5**, − switch on INP6 — correct for the reversal |

> This machine's own commissioning thread documents the exact fix (same MPU11 serial
> **0008DC111213**): Centroid forum, *"Can't move off limit per instructions in installation
> manual"* — <https://centroidcncforum.com/viewtopic.php?p=91597>. Diagnosis by Centroid
> reseller **cncsnw**: "INP1–INP6 are current inhibits for their respective axes and
> directions … entirely independent of the software and configuration." See also the
> `centroid-allin1dc-install` skill (limit-switch wiring §5.7; troubleshooting → "Full Power
> Without Motion").
