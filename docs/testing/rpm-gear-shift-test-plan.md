# RPM Gear-Shift Test Plan (on-machine)

Operator checklist for validating the automatic two-speed gear shifting on the Acroloc
S10. Covers shift boundaries, neutral-coast tuning, and RPM accuracy in each gear.

**Code under test:** `Centroid-Acroloc-ALLIN1DC.src` branch `feat/rpm-gear-shift`
(decision block in `MainStage`, `GearShiftStage`/STG17).
**Gear bands:** high ≈ 3500 RPM max; low-gear top ≈ 875 RPM (1750 × P65 0.5) — the earlier
owner note of ~1200 is to be confirmed by tachometer in §5. **Crossover P860 = 800 ± P861 = 100:**
up-shift at S ≥ 900, down-shift at S ≤ 700, hold the current gear in between.

## What to watch

- **Clutch outputs:** `Spindle_Low_gear_O` = OUT19, `Spindle_High_gear_O` = OUT20 — live
  on the CNC12 PLC diagnostic I/O display (Alt-i) or in PLC Detective.
  **Truth table (owner, 2026-07-08):** exactly one on = that gear (OUT19 = low, OUT20 = high);
  **both on = neutral** (freewheel); **both OFF = mechanical LOCKUP** (belts jam) — this state
  is forbidden and, if it occurs, the PLC stops the spindle and forces neutral. At least one
  output must be ON at all times.
- **Words (PLC Detective watch):** `DesiredRange_W` (W73), `EngagedRange_W` (W74),
  `SpindleRange_W` (W64), `GearBaseSpeed_FW` (FW7). 1 = low, 4 = high.
- **Shift in progress:** `GearShiftStage` (STG17) set; both OUT19 and OUT20 **ON** (neutral).
- **RPM:** CNC12's displayed spindle speed is the *commanded* value
  (`SV_PLC_SPINDLE_SPEED`); use a handheld tachometer on the spindle nose for the
  measured value.

## 0. Setup

- [ ] Load the compiled PLC program; verify CNC12 reports no PLC compile errors.
- [ ] Set machine parameters:

| Parameter | Value | Meaning |
| --- | --- | --- |
| P860 | `800` | Crossover RPM (set `0` to disable auto-shift for A/B checks) |
| P861 | `100` | Hysteresis half-width → deadband 700–900 |
| P862 | `1500` | Neutral coast dwell (ms) — starting value, tuned down in §4 |
| P65 | `0.5` | Low-gear ratio (existing) — verified in §5 |
| P33 | `2.0` | High-gear ratio (now read by PLC) — verified in §5. **If left 0, high gear falls back to 1.0** |
| CNC12 max spindle speed | motor base (~`1750`) | **Prerequisite** for P65/P33 to be the true physical ratios (0.5 / 2.0). If this is set to the high-gear max (3500) instead, P33 must NOT be 2.0 — see gear-shift spec. |

- [ ] No tool in the spindle for §1–§4; doors/guards per normal practice.
- [ ] **Over-speed check:** confirm P33 is set before running high gear — an unset P33 (0) uses the 1.0 fallback, not 2.0, so high-gear RPM will read low, not high.

## 1. Power-up default (neutral)

- [ ] Power-cycle the control. After boot: **both OUT19 and OUT20 ON** (neutral),
      `EngagedRange_W` = 0 (gear unknown), spindle stopped. The machine holds neutral —
      no gear engages — until the spindle is run. Result: ______

## 2. Engage on spin-up (from neutral)

Shifts only fire while the **spindle is enabled** (`SpindleEnableOut_O`); with the spindle
stopped the machine holds neutral and does **not** shift. The gear engages on spin-up, going
through neutral.

- [ ] Spindle stopped, MDI `S1300` (no M3). Expect: **no shift** — stays neutral (both
      outputs ON), `EngagedRange_W` = 0. Result: ______
- [ ] `M3 S600` (low range). Expect: shift fires — hold neutral (both ON) ~1.5 s while the
      motor spins up, then **OUT19 on / OUT20 off** (low engaged), `EngagedRange_W` = 1,
      spindle settles at 600. Result: ______
- [ ] `M5`, then `M3 S2000` (high range). Expect: neutral (both ON) while the motor spins
      up, then **OUT20 on / OUT19 off** (high engaged), `EngagedRange_W` = 4. Result: ______
- [ ] During every shift confirm **at least one clutch output is ON at all times** — both ON
      during the neutral coast; **both OFF (lockup) must NEVER occur**. Result: ______

## 3. Shift boundaries (spindle running, no load)

From neutral, `M3 S500` (first run engages **low**), then command each S in order and record
the gear (`EngagedRange_W`) after any shift completes:

| Step | Command | Expected gear | Why | Pass? |
| --- | --- | --- | --- | --- |
| 1 | `S500` | 1 (low) | well below band | ☐ |
| 2 | `S699` | 1 (low) | just below deadband, no change | ☐ |
| 3 | `S800` | 1 (low) | **deadband center — must hold low** | ☐ |
| 4 | `S899` | 1 (low) | still inside deadband | ☐ |
| 5 | `S900` | 4 (high) | up-shift boundary | ☐ |
| 6 | `S3000` | 4 (high) | inside high band | ☐ |
| 7 | `S800` | 4 (high) | **deadband — must hold high** | ☐ |
| 8 | `S701` | 4 (high) | still inside deadband | ☐ |
| 9 | `S700` | 1 (low) | down-shift boundary | ☐ |

- [ ] Each shift: clean neutral coast, single engagement, no hunting (no repeated
      shift cycles at a steady S). Result: ______

## 4. Coast-dwell tuning (P862)

Goal: tune the 1500 ms starting dwell down as far as engagement quality allows.

For each value: `M3`, then alternate `S500` ↔ `S1300` several times, listening/feeling
for engagement harshness at both the up-shift and the down-shift.

| P862 (ms) | Up-shift (S500→S1300) | Down-shift (S1300→S500) | OK? |
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
| Low | `S850` | | |
| High | `S1300` | | |
| High | `S2000` | | |
| High | `S3000` | | |
| High | `S3500` | | |

- [ ] Displayed RPM ≈ tach in both gears (ratio correct through the shift). Result: ______

## 6. Override knob must NOT shift

The decision uses the un-overridden S (`GearBaseSpeed_FW`), so the knob may change the
actual RPM across the boundary without causing a shift.

- [ ] `M3 S500` (low). Sweep override 100% → 200% (overridden RPM 1000, above the
      up-shift boundary). Expect: RPM rises, **no shift**, OUT19 stays on. Result: ______
- [ ] `M3 S1400` (high). Sweep override 100% → 40% (overridden RPM 560, below the
      down-shift boundary). Expect: RPM falls, **no shift**, OUT20 stays on. Result: ______
- [ ] Return override to 100%.

## 7. Interactions

- [ ] **Tool change inhibit:** while in high gear (`S1300`), run an `M6` to a nearby
      tool, and immediately command `S500` while the carousel indexes. Expect: no shift
      until the tool change completes, then a normal shift to low. Result: ______
- [ ] **Auto-shift disable:** set P860 = 0. Command `S500` / `S1300` — expect **no gear
      changes**; it holds the engaged gear, and from neutral (power-up) engages **low** on
      spin-up so the spindle still drives (no manual high-gear selection with auto-shift off).
      Restore P860 = 800 afterwards. Result: ______

## 8. Sign-off

| Item | Value |
| --- | --- |
| Date / operator | |
| Final P860 / P861 / P862 | |
| P65 (low ratio) | |
| Anything rough or surprising | |
