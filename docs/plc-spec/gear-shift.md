# Gear-shift: RPM-based automatic two-speed clutch selection

One-line purpose: line-referenced spec of the Acroloc RPM-based automatic gear-range
selection — the decision logic that computes `DesiredRange_W` and kicks off a shift (see
[main-stage.md#gear-decision](main-stage.md#gear-decision) for the summary; physically inside
the `JogPanelStage` banner block, src:2277-2307), the mutual-exclusion clutch interlock
(src:2396-2405), and the `GearShiftStage` (STG17, src:2985-3016) open-loop
neutral-coast-engage state machine that actually throws the clutches.

Line numbers as of commit 41f3fd6

Background (design intent, not source-of-truth for this file):
[2026-06-27-rpm-gear-shift-design.md](../superpowers/specs/2026-06-27-rpm-gear-shift-design.md),
[rpm-gear-shift-test-plan.md](../testing/rpm-gear-shift-test-plan.md). Power-up gear defaults
are in [boot.md#power-up-defaults](boot.md#power-up-defaults); resource name -> line lookups
are in [definitions.md](definitions.md); stage sweep order and timer semantics are in
[scan-model.md](scan-model.md).

## Why this replaces the stock scheme

Stock ALLIN1DC PLC logic here would read an input switch or M-function to pick a fixed gear
range (1-4) and default to high range as a fail-safe (comment, src:2270-2272). This
machine replaces that entirely with RPM-based auto-selection driven off the commanded spindle
speed, and — unlike the stock fail-safe — **powers up in LOW range**, not high (see
[boot.md#power-up-defaults](boot.md#power-up-defaults)).

## Decision logic (src:2270-2307, `JogPanelStage` banner block)

### Un-overridden speed (src:2277-2281)

`SV_PC_COMMANDED_SPINDLE_SPEED` already has the operator's override-knob percentage
(`SV_PLC_SPINDLE_KNOB`) baked in. `SV_PLC_SPINDLE_KNOB` is clamped to 1-200 a few rungs earlier
in the same override section (src:2250-2251) before this rung ever reads it, so the
division below can't blow up or be fed an out-of-range knob value.

```
GearBaseSpeed_FW (src:1107) = SV_PC_COMMANDED_SPINDLE_SPEED * 100.0 / SV_PLC_SPINDLE_KNOB
```

(src:2281). Backing the knob percentage back out gives the *un-overridden* commanded
S value. Per the source comment (src:2277-2280): sweeping the override knob across the
low/high crossover speed mid-cut must not itself trigger a gear shift (that would drop the
spindle into neutral under load) — only a change in the underlying programmed S does.

### Hysteresis deadband (src:2283-2289)

- (src:2283): `IF SV_MACHINE_PARAMETER_860 <= 0.0 THEN DesiredRange_W = EngagedRange_W` —
  auto-select is disabled outright; `DesiredRange_W` is simply pinned to whatever is currently
  engaged, so nothing downstream ever sees a range mismatch and no shift is ever kicked off.
- (src:2284-2286): otherwise, once `GearBaseSpeed_FW >= P860 + P861`, `DesiredRange_W = 4`
  (high).
- (src:2287-2289): once `GearBaseSpeed_FW <= P860 - P861`, `DesiredRange_W = 1` (low).
- Between `P860 - P861` and `P860 + P861`, neither condition fires and `DesiredRange_W`
  simply holds its last value — this is the deadband that prevents chatter right at the
  crossover speed. `P860` is the crossover center, `P861` the hysteresis half-width.

### Effective range tracking (src:2293)

`IF !GearShiftStage THEN SpindleRange_W = EngagedRange_W` — while no shift is in progress,
the range used by the ratio/DAC math further down (src:2311-2394, not repeated here;
see [main-stage.md#gear-decision](main-stage.md#gear-decision)) always reflects the actually
engaged clutch, not the desired one. `GearShiftStage` itself overrides `SpindleRange_W` during
a shift (Step A, below).

### Kickoff rung (src:2296-2307)

```
IF (DesiredRange_W != EngagedRange_W) && !GearShiftStage && !ATCStage && SpindleEnableOut_O THEN
  GearCoast_T = 1500
IF (DesiredRange_W != EngagedRange_W) && !GearShiftStage && !ATCStage && SpindleEnableOut_O &&
   (SV_MACHINE_PARAMETER_862 > 0) THEN
  GearCoast_T = SV_MACHINE_PARAMETER_862
IF (DesiredRange_W != EngagedRange_W) && !GearShiftStage && !ATCStage && SpindleEnableOut_O THEN
  SET GearCoast_T,
  SET GearShiftStage
```

Guard: fires only when the desired gear differs from the engaged gear, **the spindle is
enabled** (`SpindleEnableOut_O` — so the machine holds **neutral** while the spindle is
stopped, e.g. at power-up, and engages a gear only on spin-up), no shift is already running,
and `ATCStage` is not active (the last guard prevents a gear shift from starting mid
tool-change).

- **Timer load, default then override** (src:2300-2304): `GearCoast_T` is
  unconditionally loaded with `1500` (ms) first, then immediately overwritten with
  `SV_MACHINE_PARAMETER_862` if that parameter is `> 0`. Net effect: `P862 <= 0` (including the
  factory-zero state) uses the 1500 ms default; a positive `P862` overrides it. This is the
  same "0 disables / positive overrides" idiom used for `P860`, just with a different sentinel
  meaning (here `<= 0` means "use default," not "disable").
- **One-shot by construction** (src:2305-2307, and the source comment at
  src:2296-2299): `SET GearCoast_T` arms the timer and `SET GearShiftStage` arms the
  state machine, both in the same rung as the guard. Once `GearShiftStage` is SET, the guard's
  own `!GearShiftStage` term goes false on the next scan, so the rung cannot re-fire or re-load
  the timer mid-shift — it fires exactly once per shift. The timer itself keeps counting
  regardless of which stage armed it, so this same-scan hand-off is safe.
- **Same-scan hand-off**: `GearShiftStage` (STG17, src:2985) is swept **after** this
  kickoff rung in file order (per [scan-model.md](scan-model.md)'s SET/RST-takes-effect-
  same-scan-if-later rule), so Step A below runs in the very scan the shift is kicked off.

## Both-off lockup backstop (src:2408-2421)

**Clutch truth table (corrected 2026-07-08, owner):** `Spindle_Low_gear_O` (OUT19) and
`Spindle_High_gear_O` (OUT20) do **not** encode "one gear each, mutually exclusive." Exactly
one on = that gear; **both on = neutral** (freewheel); **both OFF = mechanical LOCKUP** — the
belts fight and jam. The forbidden state is *both off*, and the `GearShiftStage` sequence
below is written so that at least one clutch is always energized (both-off is never
commanded). This rung is the backstop for any other path that could produce it:

```
IF !Spindle_Low_gear_O && !Spindle_High_gear_O THEN
  RST SpindleEnableOut_O,
  SET Spindle_Low_gear_O,
  SET Spindle_High_gear_O,
  EngagedRange_W = 0,
  FaultMsg_W = SPINDLE_FAULT_MSG_C,
  SET ShowFaultStage,
  SET OtherFault_M
```

If both clutch outputs are ever read off, the rung **stops the spindle immediately** —
`RST SpindleEnableOut_O` drops spindle enable, and the earlier `IF !SpindleEnableOut_O THEN
SpinSpeedCommand_FW = 0.0` rung (src:2363) forces the DAC to zero — and **commands neutral**
(`SET` both clutches) to release the lockup. It sets `EngagedRange_W = 0` (out-of-band "gear
state unknown"), posts `SPINDLE_FAULT_MSG_C`, and sets `OtherFault_M`, which folds into the
fault-aggregation OR-gate (src:2841, see [main-stage.md](main-stage.md)) and asserts
`SV_STOP`. Zeroing `EngagedRange_W` guarantees the next valid speed demand forces a full
re-shift rather than trusting a stale value.

## `GearShiftStage` (STG17, src:2985-3016)

Banner comment (src:2987-3000) states the design directly: an **open-loop**
two-clutch shift driven by `DesiredRange_W` (1=low, 4=high). Sequence: engage BOTH clutches
(**neutral = both on**) -> coast for a fixed dwell -> release the non-target clutch (leaving
the target engaged). No exact rev-match is required — during the coast, the DAC already
commands the motor through the *new* gear's ratio (Step A retargets `SpindleRange_W`), so the
motor side drifts toward the right speed passively while the spindle side freewheels. **At
least one clutch is energized at every step — both-off (lockup) is never commanded.** There
is no gear-position or speed feedback anywhere in this sequence, and no in-sequence fault path
— a dwell always elapses, so a shift always completes (the separate both-off backstop above
catches the forbidden lockup state). The coast timer
`GearCoast_T` is loaded and armed by the kickoff rung above, in the same scan this stage is SET.

### Step A: neutral (both clutches ON) + retarget (src:3011-3015, every scan while shifting)

```
IF GearShiftStage THEN
  SET Spindle_Low_gear_O,
  SET Spindle_High_gear_O,
  SpindleRange_W = DesiredRange_W
```

Runs every scan for the entire duration of the shift (not just once on entry): both clutches
held **energized** (neutral = both on), and `SpindleRange_W` is retargeted to the *desired* range so the DAC
ratio math downstream (src:2311-2394) immediately starts commanding the motor through
the new gear's ratio — this is what lets the motor speed drift toward the post-shift target
during the coast, per the banner comment.

### Step B: engage + finish (src:3005-3016)

```
IF GearShiftStage && GearCoast_T && (DesiredRange_W == 1) THEN
  SET Spindle_Low_gear_O,
  RST Spindle_High_gear_O
IF GearShiftStage && GearCoast_T && (DesiredRange_W == 4) THEN
  SET Spindle_High_gear_O,
  RST Spindle_Low_gear_O
IF GearShiftStage && GearCoast_T THEN
  EngagedRange_W = DesiredRange_W,
  RST GearCoast_T,
  RST GearShiftStage
```

(src:3007-3016). Per the comment directly above (src:3005-3006): a bare timer
name evaluates true once it reaches its set point — `GearCoast_T` here means "the coast dwell
has fully elapsed," not "the timer was just armed" (which would be the `== 0` case). Once the
dwell elapses:

- Exactly one of the two range-specific rungs fires (mutually exclusive by construction on
  `DesiredRange_W == 1` vs. `== 4`), engaging the target clutch and releasing the other —
  since Step A held both released every scan up to and including this one, there is no scan
  where the new clutch is SET while the old one is still SET.
- The finishing rung unconditionally records `EngagedRange_W = DesiredRange_W`, then
  `RST GearCoast_T` and `RST GearShiftStage` — ending the shift. Once `GearShiftStage` is RST,
  Step A stops running, `SpindleRange_W = EngagedRange_W` (src:2293) resumes tracking
  the now-current engaged range (which equals `DesiredRange_W`, so no glitch), and the kickoff
  rung's `!GearShiftStage` guard re-arms for the next shift.

### ATC inhibit

The kickoff rung's `!ATCStage` guard (src:2300, 2302, 2305) is the only interlock
between gear-shifting and tool-changing: a gear shift cannot be *started* while `ATCStage` is
running. Nothing in `GearShiftStage` itself checks `ATCStage` — if a shift is already mid-coast
when `M6_SV` arms `ATCStage` (src:2911, see [main-stage.md#atc-kickoff](main-stage.md)),
the shift is allowed to run to completion concurrently with the tool change; only a *new*
shift request is blocked while the carousel is moving.

## Parameters

| Parameter | Meaning | Disable/default sentinel | Intended value |
|---|---|---|---|
| `SV_MACHINE_PARAMETER_860` (P860) | Low/high crossover speed (center of the hysteresis band), compared against `GearBaseSpeed_FW` | `<= 0.0` disables auto-shift entirely (`DesiredRange_W` just tracks `EngagedRange_W`) | 800 (RPM) |
| `SV_MACHINE_PARAMETER_861` (P861) | Hysteresis half-width around `P860` | no disable sentinel — always added/subtracted from `P860` | 100 (RPM) |
| `SV_MACHINE_PARAMETER_862` (P862) | Coast dwell override, ms | `<= 0` (including factory-zero) falls back to the hard-coded 1500 ms default | 1500, tuned down on the actual machine |

Sources for intended values: the design spec
([2026-06-27-rpm-gear-shift-design.md](../superpowers/specs/2026-06-27-rpm-gear-shift-design.md),
"P860 = 800, P861 = 100," "Coast dwell ... default 1500; tune down on the machine") — these
are the owner's stated tuning targets, not something the `.src` itself encodes (the `.src` only
encodes the *default-if-unset* value for `P862`, and no default at all for `P860`/`P861` since
`P860 <= 0` disables rather than defaulting).

## Open-loop caveats

- **No rev-match, no feedback.** The entire sequence is time-based: neutral for a fixed dwell,
  then engage. There is no encoder/tach check that the motor and spindle sides are actually
  near-synchronized before `Spindle_Low_gear_O`/`Spindle_High_gear_O` is SET. Shift quality
  depends entirely on `P862` being tuned so the dwell is long enough for the motor to coast to
  roughly the new range's speed, given the machine's own inertia/friction — too short an
  interval engages the clutch far off-speed; the design/test-plan documents linked above are
  where that tuning guidance lives, not this file.
- **No failure detection.** Per the banner comment, there's deliberately no fault path in
  `GearShiftStage` — a shift always "completes" once the dwell elapses, whether or not the
  clutch actually engaged mechanically (e.g., a stuck or failed clutch solenoid). The both-off
  lockup backstop (src:2414-2421) catches the forbidden *both-outputs-off* (lockup) state and
  stops the spindle; it does not verify that a commanded clutch physically engaged when at
  least one output is on.
- **Concurrent-with-ATC risk window.** As noted under ATC inhibit above, a shift already in
  progress is not aborted or paused when `ATCStage` starts — only new shifts are blocked. If the
  coast dwell is still running when the carousel begins moving, the spindle sits in neutral
  (or freshly engaged) with `SpindleRange_W` mid-transition while the tool change proceeds; the
  `.src` does not document (and this file does not assert) any specific hazard from that overlap
  beyond what's stated here.

## Verification

Every `(src:NNNN)` citation above was checked against `Centroid-Acroloc-ALLIN1DC.src` at commit
41f3fd6 with `sed -n '<line>p'`; the working tree is unchanged since that commit (`git status`
shows no modifications to the `.src` file).
