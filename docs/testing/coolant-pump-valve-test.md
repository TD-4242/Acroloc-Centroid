# Coolant Pump / Flood-Valve Test (on-machine)

Verifies the coolant outputs match the real plumbing: OUT4 (`CoolantPump_O`) is the pump,
OUT3 (`FloodValve_O`) is the flood valve. Flood = pump + valve; wash/"mist" = pump only.

Run after any change to the coolant rungs. Design spec:
`docs/superpowers/specs/2026-07-12-coolant-pump-valve-fix-design.md`.

## What to watch (PLC Diagnostics, Alt-I)

| Address | Symbol | Meaning |
|---|---|---|
| OUT4 | `CoolantPump_O` | 1 = coolant pump running |
| OUT3 | `FloodValve_O` | 1 = flood valve open (coolant to workspace nozzles) |
| OUT1078 | `CoolFloodLED_O` | flood mode selected |
| OUT1079 | `CoolMistLED_O` | wash/"mist" mode selected |

CNC12's coolant indicator shows Flood / Mist / Off (the wash mode still reads "Mist").

---

## Tests

1. **Flood (manual).** Press the flood button. Expect: `CoolantPump_O` (OUT4) **and**
   `FloodValve_O` (OUT3) both -> 1; coolant runs at the workspace nozzles (pump audibly runs,
   valve opens). Result: ______

2. **Wash / "mist" (manual).** Press the mist button. Expect: `CoolantPump_O` -> 1,
   `FloodValve_O` -> 0; the cleaning hose pressurizes, no nozzle flow. Result: ______

3. **Switch flood <-> wash.** From flood, press wash (and back). Expect: the pump (OUT4)
   stays running the whole time while the valve (OUT3) toggles; only one of the two mode LEDs
   is lit at a time (mutually exclusive). Result: ______

4. **Coolant off.** Turn the active mode off. Expect: `CoolantPump_O` and `FloodValve_O`
   both -> 0. Result: ______

5. **Auto-coolant (MDI).** Select auto-coolant, then in MDI: `M8` -> flood (OUT4+OUT3 on),
   `M7` -> wash (OUT4 on, OUT3 off), `M9` -> both off. Result: ______

6. **Fault/stop.** With coolant on, press E-stop (or trigger `SV_STOP`). Expect: both OUT4
   and OUT3 drop immediately. Result: ______

**Pass = flood runs the pump and opens the valve, wash runs the pump only, switching keeps
the pump on, and off/stop drops both.**

---

## Sign-off

| Item | Value |
|---|---|
| Date / operator | |
| PLC source commit tested | |
| Tests 1-6 all pass? | |
| Did flood actually flow at the nozzles? | |
| Anything rough or surprising | |
