# ATC Carousel Search Timeout Test (on-machine)

Operator checklist verifying the carousel cannot spin forever: if the target tool is never
found, `ATCStage` faults `CAROUSEL MOVE TIME OUT` within ~20 s and stops/relocks the carousel.

Run after any change to the `ATCStage` search logic, the position-switch decode, or
`ATCSpin_T`. Design spec: `docs/superpowers/specs/2026-07-11-atc-carousel-timeout-design.md`.

## SAFETY

- **No tool in the spindle** for the whole test; keep the pockets you index into empty.
- Stand at the E-stop. The carousel will spin during test 2 — if anything binds, E-stop.

## What to watch (PLC Diagnostics, Alt-I)

| Address | Symbol | Meaning |
|---|---|---|
| OUT17 | `ATCMotor_O` | 1 = carousel motor running |
| OUT18 | `ATCUnlocked_O` | 1 = carousel unlocked (0 = locked) |
| T24 | `ATCSpin_T` | search watchdog (true at 20 s expiry) |
| W72 | `ChangeToTool_W` | target tool (0 = none) |

The watchdog preset is `ATC_SPIN_TIMEOUT_MS_C = 20000` ms.

---

## Tests

1. **No false trips.** Run several `M6` changes to a range of tools, including the farthest
   (worst-case ~full revolution). Each completes normally in well under 20 s; `ATCMotor_O`
   stops on the match and the carousel relocks. The watchdog never fires. Result: ______

2. **Unreachable tool -> timeout.** With no tool in the spindle, command a tool that has no
   pocket / never decodes — e.g. `M6 T13` on a 12-pocket carousel. Expected: the carousel
   spins, and at ~20 s the change **faults with "CAROUSEL MOVE TIME OUT"**, `ATCMotor_O` -> 0,
   the carousel relocks (`ATCUnlocked_O` -> 0), and `M6_SV`/`ChangeToTool_W` clear.
   Result: ______
   *(If commanding an out-of-range tool is undesirable, instead physically hold/stall the
   carousel so no position switch changes, and confirm the same ~20 s fault.)*

3. **Recovery / re-arm.** Clear the fault (cycle-cancel/reset), then run a normal `M6` to a
   valid tool. Expected: it completes normally — proving the watchdog re-armed cleanly after
   the timeout. Result: ______

4. **Multi-switch decode (peak).** Command tools whose codes use several position switches at
   once — e.g. **T7** (Pos1+Pos2+Pos3), **T12** (Pos2+Pos5), **T9** (Pos1+Pos4). Each must land
   on the correct pocket (the peak must read the full multi-bit code, not a single-switch
   partial). Also sweep single-switch tools (**T4**=Pos3, **T8**=Pos4, **T2**=Pos2, **T10**=Pos5)
   from several starting pockets — requesting T4 must drive all the way to 4, never stop on
   5/6/7. Result: ______

5. **Same-tool re-index + clean seating.** Request the tool that is already loaded: the carousel
   must do a **full re-index** (not sit still), and on every stop confirm the carousel **locks
   cleanly on the pocket** (it stops in the all-switches-off gap just past the pocket and the
   lock pin seats it — verify no tool sits a hair past/short). Result: ______

**Pass = normal changes never trip, multi-switch and single-switch tools land on the correct
pocket and seat cleanly, same-tool re-indexes, an unfindable tool faults at ~20 s (motor off +
relocked), and a normal change works again afterward.**

---

## Sign-off

| Item | Value |
|---|---|
| Date / operator | |
| PLC source commit tested | |
| Test 1 (no false trips) pass? | |
| Test 2 (timeout fault) pass? measured time to fault: | |
| Test 3 (recovery) pass? | |
| Anything rough or surprising | |
