# Spindle-in-Changer Safety Test (on-machine)

Operator checklist verifying the **single most important ATC safety property**:

> **The spindle must never be turning — not spinning, not coasting — when Z is inside the
> tool changer.**

Run this after any change to `mfunc6.mac`, the MainStage changer interlock, or the ATC/spindle
wiring. It is deliberately paranoid: it tests every protection layer independently so that if one
fails, you find out here and not with a tool spinning in the carousel.

---

## SAFETY FIRST

- **No tool in the spindle** for the whole test. Keep the carousel pockets you index into empty.
- **Stand at the E-stop / feed-hold.** Several steps deliberately command the spindle and drive Z
  toward the changer. If Z moves toward the changer while the spindle is still turning, **E-stop
  immediately** — that is the exact failure this test exists to catch.
- Doors/guards per normal practice.
- Do one dry read-through of each step before doing it. Know the expected result before you press
  Cycle Start.

## Protection layers under test

| # | Layer | Where | Protects |
|---|-------|-------|----------|
| L1 | **M6 macro spindle-stop wait** (`M101 /50012`) | `mfunc6.mac` | The tool change itself — Z will not leave for the change position until `ZeroSpeed_I` confirms a stop |
| L2 | **MainStage feed-hold interlock** | `.src` `MainStage` | **Direct** programmed/MDI `G53` moves into the zone (a program bug, a hand-typed `G53 Z0`). Does **not** see M6 macro moves — that's L1's job |
| L3 | **Unconditional zone-kill** | `.src` `MainStage` | Drops the spindle enable whenever Z is in the changer, in **all** modes incl. manual — no spindle start with Z parked, no re-spin inside |
| L4 | **ATCStage zero-speed guard** | `.src` `ATCStage` | The carousel will not index unless `ZeroSpeed_I` confirms a stop |

All four ride on one sensor — `ZeroSpeed_I` (INP12). **Section 0 verifies it first; nothing else
is trustworthy until it passes.**

## What to watch (PLC Diagnostics, Alt-I)

| Address | Symbol | Meaning |
|---|---|---|
| INP12 | `ZeroSpeed_I` | **1 = spindle confirmed stopped**, 0 = spinning/coasting |
| INP26 | `ATC_Z_ClearedToolChanger_I` | **1 = Z clear of changer**, 0 = Z in changer (danger) |
| INP27 | `ATC_Z_Zero_Release_I` | 1 = Z at the high tool-change position |
| OUT7  | `SpindleEnableOut_O` | spindle enable command (0 = spindle commanded off) |
| OUT1104 | `FeedHoldLED_O` | feed hold active |
| MEM448 | `ChangerHoldActive_M` | interlock feed-hold armed & waiting for zero |
| T23 | `ChangerStopTimer_T` | interlock 5 s timeout |

If the temporary `; DEBUG` messages are loaded, they echo three of these to the message line
(*"spindle in changer zone"*, *"Z cleared tool ring"*, *"changer feed-hold armed"*). Remove them
before merge (`grep -rn "DEBUG" Centroid-Acroloc-ALLIN1DC.src plcmsg.txt`).

---

## 0. Sensor sanity — `ZeroSpeed_I` polarity (do this first)

Everything depends on INP12 reading the spindle correctly. Z clear of the changer, no tool.

- [ ] Spindle **stopped** (`M5`): INP12 reads **1 / TRUE**. Result: ______
- [ ] Spindle **running** (`M3 S500`, Z safely clear): INP12 reads **0 / FALSE**. Result: ______
- [ ] `M5`, watch the spindle coast down: INP12 stays **0** while coasting and flips to **1**
      only once the spindle is truly stopped (not early). Result: ______

**If any of these is wrong, STOP.** An inverted or early/late INP12 defeats L1, L2, and L4 at
once. Fix the wiring / input inversion (P911 bit for INP12) before continuing.

---

## 1. Normal M6 with the spindle spinning (L1 — the main case)

This is the failure that motivated the fix: command the spindle, then a tool change.

- [ ] `G53 Z-4` (Z clear of changer). `M3 S2000`. Let it reach speed.
- [ ] `M6 T2`. **Watch Z.** Expected: Z **does not move toward the changer**; the macro holds on
      the spindle-stop wait (message *"waiting for input #12 (M101)"*), spindle coasting.
      INP12 = 0, Z stationary. Result: ______
- [ ] When the spindle reaches zero (INP12 -> 1), the wait releases and **only then** does Z rapid
      to the change position. At no point is Z moving into the changer with INP12 = 0.
      Result: ______
- [ ] Repeat from a higher speed if your spindle allows (longer coast = longer, more visible
      hold). Result: ______

**Pass = Z never crosses into the changer (INP26 -> 0) until INP12 = 1.** Any Z motion toward the
changer while INP12 = 0 is a **FAIL — E-stop.**

---

## 2. Normal M6 with the spindle already stopped (no spurious wait)

- [ ] Spindle stopped (`M5`), Z clear. `M6 T3`. Expected: **no wait** — the macro parks Z
      immediately (INP12 already 1). No hang on "waiting for input #12". Result: ______

---

## 3. Direct move into the changer (L2 — the general-case net)

L1 only covers the M6 macro. This checks the PLC interlock that guards a **direct** move — a
program or a hand-typed `G53`. **Hand on feed-hold/E-stop.**

- [ ] `G53 Z-4`, `M3 S2000`, up to speed. Then hand-type **`G53 Z0`** in MDI (a direct move, not
      an M6). Expected: as Z enters the zone (INP26 -> 0) the interlock **feed-holds** —
      `ChangerHoldActive_M` (MEM448) = 1, `FeedHoldLED_O` = 1, Z stops — spindle commanded off,
      and motion **auto-resumes** once INP12 -> 1. Result: ______
- [ ] If instead Z drives straight through without pausing (MEM448 never sets): the interlock does
      **not** net direct moves either — record this; the interlock needs rework and L1 is your
      only protection. **E-stop if the spindle is still turning near the changer.** Result: ______

> Note: it is a known, on-machine-confirmed limitation that the interlock does **not** arm for the
> M6 macro's own `G53` (macro moves don't assert `SV_PROGRAM_RUNNING`/`SV_MDI_MODE`). This step is
> specifically about a *direct* move, which is a different code path.

---

## 4. Unconditional zone-kill, all modes (L3)

The spindle enable must be dropped **any** time Z is in the changer, regardless of mode.

- [ ] Park Z at the change position (`G53 Z0`, spindle already stopped) so INP26 = 0. In **manual**
      mode, press the jog-panel spindle-start (or MDI `M3 S500`). Expected: spindle **does not
      start** — `SpindleEnableOut_O` (OUT7) stays 0. Result: ______
- [ ] With Z parked in the changer and the spindle off, confirm OUT7 = 0 every scan (zone-kill is
      unconditional, not a one-shot). Result: ______

---

## 5. Carousel guard (L4 — belt and suspenders)

Confirms the carousel refuses to index against a turning spindle even if L1/L2/L3 were bypassed.
Because it is hard to reach `ATCStage` with the spindle spinning without defeating the layers
above, simulate the sensor instead:

- [ ] Spindle **stopped**, no tool. Force/simulate INP12 = 0 (e.g. temporarily disconnect the
      ZeroSpeed sensor lead, or force the input off in PLC diagnostics), then run `M6 T4`.
      Expected: the carousel **does not turn**; the change **aborts with a fault**
      (`SPINDLE_FAULT_MSG_C`), the motor output stays off, the carousel relocks, and `M6_SV`
      clears. Result: ______
- [ ] Restore INP12 (reconnect / un-force). Confirm a normal `M6` works again. Result: ______

---

## 6. Stuck-spindle / dead-sensor behavior (fail-safe)

What happens when the spindle never reports zero — the case that must **never** proceed.

> **Do NOT software-force INP12 to test the macro (L1).** A software input force reaches the PLC
> scan but does **not** reach a macro's `M100`/`M101` wait — they read different paths — so
> forcing INP12 off makes the diagnostic screen show 0 while the macro's `M101 /50012` sails
> right through. That is a **test artifact**, not the machine's real behavior (with a genuinely
> spinning spindle the raw input reads 0 and the wait holds every time — see §1). The only valid
> way to test a dead sensor for the macro is to change the **actual input**: physically
> disconnect the ZeroSpeed lead.

- [ ] **Fail-safe direction (do this first).** With the spindle **stopped**, physically
      disconnect the ZeroSpeed sensor lead and read INP12. It **must** read **0** ("not
      stopped"). If a disconnected/dead sensor reads **1** ("stopped"), STOP — a broken wire will
      let a spinning spindle into the changer; this is a wiring / F510-output fix (the "at zero"
      condition must be energize-to-permit), not a code fix. Result: ______
- [ ] **Macro hang (L1), sensor physically disconnected.** With the lead still disconnected,
      `M3 S1000`, `M6 T5`. Expected: the M6 macro **holds indefinitely** on "waiting for input
      #12" and Z **never** moves to the change position. (Safe hang — recover with
      feed-hold/cancel/E-stop.) Result: ______
- [ ] **Interlock timeout (L2), PLC-side.** L2/L3/L4 are PLC-side and *do* honor a software force,
      so a forced INP12 = 0 is valid here: hand-type `G53 Z0` in MDI with INP12 forced 0 — the
      interlock holds and, at 5 s, faults (`ChangerStopTimer_T` expiry -> `SPINDLE_FAULT_MSG_C`),
      motion stays held. Result: ______
- [ ] Reconnect the sensor / clear the force. Confirm a normal `M6` works again. Result: ______

---

## 7. Normal resume after a change

- [ ] After a completed `M6`, when Z leaves the changer (INP26 -> 1) with a modal `M3`/`M4` still
      active, the spindle restarts at its commanded RPM. A program `M5` (as inside M6) keeps it
      off. Result: ______

---

## Sign-off

| Item | Value |
|---|---|
| Date / operator | |
| PLC source commit / `mfunc6.mac` version tested | |
| Section 0 (sensor) pass? | |
| Any Z-toward-changer-while-spinning event (which section)? | |
| Debug messages still loaded? (remove before merge) | |
| Interlock arms for direct moves (Section 3)? yes / no | |
| Anything rough or surprising | |
