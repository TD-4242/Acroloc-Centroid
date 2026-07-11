# Oil Pump (OUT2) Auto-Control Test (on-machine)

Operator checklist verifying the oil pump on `Lube_O` (OUT2) runs **only while a G-code
program is actively executing** and stops the instant the job stops for any reason.

Run this after any change to the `MainStage` oil-pump coil or the OUT2 wiring. Design spec:
`docs/superpowers/specs/2026-07-10-oil-pump-auto-control-design.md`.

## What drives it

A single combinational coil in `MainStage`:

```
IF SV_JOB_IN_PROGRESS && !SV_MDI_MODE && !FeedHoldLED_O && EStopOk_M THEN (Lube_O)
```

On only while a loaded program runs; off in MDI, at idle, on feed-hold, and on any stop
(cycle-cancel/reset, E-stop, program end). This replaced the retired Parameter-179
lube-timer stages.

## What to watch (PLC Diagnostics, Alt-I)

| Address | Symbol | Meaning |
|---|---|---|
| OUT2 | `Lube_O` | **1 = oil pump powered**, 0 = off |
| INP9 | `LubeOk_I` | lube pressure/level ok when closed |
| OUT1104 | `FeedHoldLED_O` | feed-hold active |

> Note: the lube pump meters on its **own internal interval** while powered. "OUT2 = 1"
> means the pump has power, not that it is delivering an oil shot this instant.

---

## Tests

1. **Idle at main screen.** No program, not in MDI. Expect `Lube_O` (OUT2) = **0**.
   Result: ______

2. **MDI, no run.** Enter MDI and sit at the prompt: OUT2 = **0**. Run an MDI move
   (e.g. `G53 Z-1`): OUT2 **stays 0** through the MDI move. Result: ______

3. **Program run.** Run a short program. Expect OUT2 = **1** for the whole run, returning
   to **0** at program end (M30/M2). Result: ______

4. **Feed-hold mid-program.** With a program running (OUT2 = 1), press feed-hold: OUT2 ->
   **0** and `FeedHoldLED_O` = 1. Press cycle-start: OUT2 -> **1** as the program resumes.
   Result: ______

5. **Cycle-cancel/reset mid-program.** With a program running, cycle-cancel (reset): OUT2 ->
   **0** and stays 0. Result: ______

6. **E-stop mid-program.** With a program running, press E-stop: OUT2 -> **0**.
   Result: ______

7. **Manual jog / MPG.** Jog the axes by hand / MPG (no program): OUT2 = **0** throughout.
   Result: ______

8. **Lube-fault path intact.** With a program running and `LubeOk_I` (INP9) open
   (or simulated open), confirm the `LUBE WARNING` message still posts — the fault
   monitoring is unchanged by this feature. Result: ______

**Pass = OUT2 follows the table exactly:** on only during an executing program, off in every
other state including feed-hold.

---

## Sign-off

| Item | Value |
|---|---|
| Date / operator | |
| PLC source commit tested | |
| Tests 1-8 all pass? | |
| Any state where OUT2 was on when it should be off (which test)? | |
| Anything rough or surprising | |
