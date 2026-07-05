# RPM Gear-Shift Test Plan (on-machine)

Operator checklist for validating the automatic two-speed gear shifting on the Acroloc
S10. Covers shift boundaries, neutral-coast tuning, and RPM accuracy in each gear.

**Code under test:** `Centroid-Acroloc-ALLIN1DC.src` branch `feat/rpm-gear-shift`
(decision block in `MainStage`, `GearShiftStage`/STG17).
**Gear bands:** low ≈ 0–1200 RPM, high ≈ 1000–3500 RPM. Shift on crossing the boundary:
up-shift at S ≥ 1200, down-shift at S ≤ 1000, hold the current gear in between.

## What to watch

- **Clutch outputs:** `Spindle_Low_gear_O` = OUT19, `Spindle_High_gear_O` = OUT20 — live
  on the CNC12 PLC diagnostic I/O display (Alt-i) or in PLC Detective.
- **Words (PLC Detective watch):** `DesiredRange_W` (W73), `EngagedRange_W` (W74),
  `SpindleRange_W` (W64), `GearBaseSpeed_FW` (FW7). 1 = low, 4 = high.
- **Shift in progress:** `GearShiftStage` (STG17) set; both OUT19 and OUT20 off (neutral).
- **RPM:** CNC12's displayed spindle speed is the *commanded* value
  (`SV_PLC_SPINDLE_SPEED`); use a handheld tachometer on the spindle nose for the
  measured value.

## 0. Setup

- [ ] Load the compiled PLC program; verify CNC12 reports no PLC compile errors.
- [ ] Set machine parameters:

| Parameter | Value | Meaning |
| --- | --- | --- |
| P941 | `1100` | Crossover RPM (set `0` to disable auto-shift for A/B checks) |
| P942 | `100` | Hysteresis half-width → deadband 1000–1200 |
| P943 | `1500` | Neutral coast dwell (ms) — starting value, tuned down in §4 |
| P65 | *(existing)* | Low-gear ratio — verified in §5 |

- [ ] No tool in the spindle for §1–§4; doors/guards per normal practice.

## 1. Power-up default

- [ ] Power-cycle the control. After boot: OUT19 **on**, OUT20 **off**,
      `EngagedRange_W` = 1, `SpindleRange_W` = 1. Result: ______

## 2. First shifts, spindle stopped

The sequence still runs with the spindle off — it coasts the dwell at zero speed and
engages. Watch the outputs, not the noise.

- [ ] MDI `S1300` (no M3). Expect: both outputs drop (neutral), ~1.5 s pause, then
      OUT20 **on** / OUT19 **off**, `EngagedRange_W` = 4. Result: ______
- [ ] MDI `S500`. Expect the mirror shift back to low (OUT19 on). Result: ______
- [ ] During each shift confirm OUT19 and OUT20 are **never on together**. Result: ______

## 3. Shift boundaries (spindle running, no load)

Start in low gear, `M3 S500`, then command each S in order and record the gear
(`EngagedRange_W`) after any shift completes:

| Step | Command | Expected gear | Why | Pass? |
| --- | --- | --- | --- | --- |
| 1 | `S500` | 1 (low) | well below band | ☐ |
| 2 | `S999` | 1 (low) | below deadband, no change | ☐ |
| 3 | `S1100` | 1 (low) | **deadband — must hold low** | ☐ |
| 4 | `S1199` | 1 (low) | still inside deadband | ☐ |
| 5 | `S1200` | 4 (high) | up-shift boundary | ☐ |
| 6 | `S3000` | 4 (high) | inside high band | ☐ |
| 7 | `S1100` | 4 (high) | **deadband — must hold high** | ☐ |
| 8 | `S1001` | 4 (high) | still inside deadband | ☐ |
| 9 | `S1000` | 1 (low) | down-shift boundary | ☐ |

- [ ] Each shift: clean neutral coast, single engagement, no hunting (no repeated
      shift cycles at a steady S). Result: ______

## 4. Coast-dwell tuning (P943)

Goal: tune the 1500 ms starting dwell down as far as engagement quality allows.

For each value: `M3`, then alternate `S500` ↔ `S1300` several times, listening/feeling
for engagement harshness at both the up-shift and the down-shift.

| P943 (ms) | Up-shift (S500→S1300) | Down-shift (S1300→S500) | OK? |
| --- | --- | --- | --- |
| 1500 | | | ☐ |
| 1200 | | | ☐ |
| 1000 | | | ☐ |
| 800 | | | ☐ |
| 600 | | | ☐ |
| 400 | | | ☐ |

- [ ] Chosen value: ______ ms (last clean value with margin; when in doubt go one step
      longer). Note: down-shifts are the harsh direction — the spindle side must slow
      toward the low-gear speed during the coast, so judge mainly on those.

## 5. RPM accuracy per gear (tachometer)

With the override knob at exactly **100%**, command each speed, let it settle, and
record the tachometer reading. Low-gear error scales with the P65 ratio — if low gear
reads proportionally off, adjust P65, not the parameters above.

| Gear | Command | Tach RPM | Error % |
| --- | --- | --- | --- |
| Low | `S200` | | |
| Low | `S600` | | |
| Low | `S1000` | | |
| High | `S1300` | | |
| High | `S2000` | | |
| High | `S3000` | | |
| High | `S3500` | | |

- [ ] Displayed RPM ≈ tach in both gears (ratio correct through the shift). Result: ______

## 6. Override knob must NOT shift

The decision uses the un-overridden S (`GearBaseSpeed_FW`), so the knob may change the
actual RPM across the boundary without causing a shift.

- [ ] `M3 S900` (low). Sweep override 100% → 150% (commanded RPM 1350, above the
      boundary). Expect: RPM rises, **no shift**, OUT19 stays on. Result: ______
- [ ] `M3 S1400` (high). Sweep override 100% → 60% (commanded RPM 840, below the
      boundary). Expect: RPM falls, **no shift**, OUT20 stays on. Result: ______
- [ ] Return override to 100%.

## 7. Interactions

- [ ] **Tool change inhibit:** while in high gear (`S1300`), run an `M6` to a nearby
      tool, and immediately command `S500` while the carousel indexes. Expect: no shift
      until the tool change completes, then a normal shift to low. Result: ______
- [ ] **Auto-shift disable:** set P941 = 0. Command `S500` / `S1300` — expect **no**
      shifts; the machine holds the current gear (this is the documented behavior:
      with auto-shift disabled there is no other gear-selection path). Restore
      P941 = 1100 afterwards. Result: ______

## 8. Sign-off

| Item | Value |
| --- | --- |
| Date / operator | |
| Final P941 / P942 / P943 | |
| P65 (low ratio) | |
| Anything rough or surprising | |
