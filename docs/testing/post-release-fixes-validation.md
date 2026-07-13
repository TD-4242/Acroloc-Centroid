# Post-Release Fixes — On-Machine Validation

Run this checklist **once the `post-release-fixes` PLC is compiled and loaded** in CNC12 on
the control PC. It walks every change in the PR that has an observable on-machine effect, with
a procedure and expected result for each. The two biggest items (ATC timeout, coolant) have
their own detailed sheets — this is the master pass; do the referenced sheets where noted.

## Before you start

- **No tool in the spindle** for the ATC tests; keep the carousel pockets you index into empty.
- **Stand at the E-stop / feed-hold.** The ATC and coolant steps command real motion/flow.
- Have **PLC Diagnostics (Alt-I)** open to watch outputs, and the **message line** visible.
- Home the machine after loading.

Watch list (Alt-I):

| Address | Symbol | Meaning |
|---|---|---|
| OUT17 | `ATCMotor_O` | carousel motor |
| OUT18 | `ATCUnlocked_O` | carousel unlocked (0 = locked) |
| OUT4 | `CoolantPump_O` | coolant pump |
| OUT3 | `FloodValve_O` | flood valve |
| OUT1080 | `Aux13LED_O` | Aux13 function |
| T24 | `ATCSpin_T` | carousel search watchdog (20 s) |

---

## 0. Compile and load

- [ ] Load `Centroid-Acroloc-ALLIN1DC.src` in CNC12's PLC compiler on the control PC.
- [ ] **0 compile errors** (warnings are expected — the local `./compile.sh` reports 190).
- [ ] PLC loads and the machine comes up normally (homes, no fault storm). Result: ______

---

## 1. ATC carousel search timeout  (see `atc-timeout-test.md` for the full sheet)

Bounds the carousel so it can't spin forever if the tool is never found.

- [ ] **No false trips:** with no tool in the spindle, run `M6` to a few valid tools
      (near and far). Each completes normally in well under 20 s; the watchdog never fires.
      Result: ______
- [ ] **Timeout fault:** command an unreachable tool — `M6 T13` on the 12-pocket carousel
      (or physically stall the carousel). Expect at ~20 s: **`CAROUSEL MOVE TIME OUT`**,
      `ATCMotor_O` -> 0, carousel relocks (`ATCUnlocked_O` -> 0), `M6` cleared. Result: ______
- [ ] **Recovery:** clear the fault, run a normal `M6` — completes (watchdog re-armed).
      Result: ______

---

## 2. Tool change no longer fires Aux13  (MEM444 fix)

Previously a completed tool change set a bit shared with `KbAux13Key_M`, spuriously firing
Aux13.

- [ ] Run a normal `M6` tool change to a valid tool. Watch `Aux13LED_O` (OUT1080) / whatever
      Aux13 drives on this machine. Expect: **Aux13 does NOT activate** at the end of the
      change. Result: ______
- [ ] Confirm Aux13 still works on its own: press `Ctrl+1` (or the Aux13 panel key) and verify
      Aux13 activates as normal. Result: ______

---

## 3. "Tool Carousel locked" message is correct  (ATC_Lock_Released_C fix)

The message value was garbled (posted a bad/blank message); corrected to `44546`.

- [ ] With Z clear of the changer and no ATC running, press and hold the **front-panel manual
      unlock button** (`ATCManualUnlock_I`, INP24): message line shows **"Tool Carousel not
      locked."** Result: ______
- [ ] Release the button: message line shows **"Tool Carousel locked."** (readable text, not
      blank/garbage). Result: ______

---

## 4. No leftover DEBUG messages  (DEBUG tracing removed)

- [ ] Run a normal `M6` and (if practical) drive Z into the changer with the spindle stopping,
      watching the message line. Expect: **none** of the old debug strings appear —
      *"DEBUG spindle in changer zone"*, *"DEBUG Z cleared tool ring"*, *"DEBUG changer
      feed-hold armed"*. Result: ______

---

## 5. Coolant pump / flood valve  (see `coolant-pump-valve-test.md` for the full sheet)

OUT4 is the pump, OUT3 the flood valve. **This is the fix that makes flood actually flow.**

- [ ] **Flood button:** `CoolantPump_O` (OUT4) **and** `FloodValve_O` (OUT3) both on; coolant
      runs at the workspace nozzles (pump audibly runs, valve opens). Result: ______
- [ ] **Wash/"mist" button:** OUT4 on, OUT3 off; the cleaning hose pressurizes, no nozzle flow.
      Result: ______
- [ ] **Switch flood <-> wash:** the pump stays running while the valve toggles. The buttons are
      independent (not mutually exclusive) — both LEDs may be lit at once; dropping flood leaves
      the pump on. Result: ______
- [ ] **Coolant off:** both OUT4 and OUT3 drop. Result: ______
- [ ] **Auto-coolant (MDI):** `M8` -> flood (pump+valve), `M7` -> wash (pump only), `M9` -> off.
      Result: ______
- [ ] **Stop:** with coolant on, E-stop / `SV_STOP` drops both outputs. Result: ______

---

## 6. Regression — unchanged behavior still works

The gear-sense input removal and the spelling/casing fixes are non-functional; confirm nothing
regressed:

- [ ] **Gear shift:** the RPM-based auto shift still changes low<->high at the crossover as
      before (removed inputs were unused). Result: ______
- [ ] **Spindle-in-changer feed-hold interlock:** unchanged from the prior release — a
      spinning spindle driven toward the changer still holds until zero speed
      (spot-check per `spindle-changer-safety-test.md` if desired). Result: ______
- [ ] **Oil pump (OUT2):** runs only while a program executes, off on stop (unchanged).
      Result: ______

---

## Sign-off

| Item | Value |
|---|---|
| Date / operator | |
| PLC source commit tested | |
| Section 0 (compile/load) pass? | |
| Sections 1-5 all pass? | |
| Did flood coolant flow at the nozzles (5)? | |
| Any spurious Aux13 on a tool change (2)? | |
| Regressions found (6)? | |
| Anything rough or surprising | |
