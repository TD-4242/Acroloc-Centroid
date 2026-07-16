# Head-elevator scale + Z re-sync — design

Date: 2026-07-16
Status: draft for owner review

## Problem

The Acroloc's CNC Z axis is the Bridgeport-style quill (8 in travel, ~6 in usable).
A separate motorized elevator moves the entire head up and down as a coarse adjustment.
The elevator has no feedback, so any head move destroys the part Z zero — yet head moves
are routinely needed because probes are much longer than cutters and the usable quill
envelope is only 4–6 in.

Goal: move the head between operations **without losing part Z zero**, like a knee-scale
DRO sum on a manual Bridgeport.

## Decision summary

CNC12 cannot sum two feedback devices into one axis — the Z servo loop closes on exactly
one device. Instead:

**Mount a linear scale on the head, wire it to a spare ALLIN1DC encoder input, and add a
"Z RE-SYNC" VCP button that shifts every work-coordinate Z by the measured head movement.**

Workflow: touch off part Z → press RE-SYNC (latches head position) → move head → press
RE-SYNC again (applies the delta) → keep machining. Part zero survives to scale accuracy.

Rejected alternatives:
- *Scale as Z position feedback (true summing / dual loop)* — the servo would fight every
  head move (following error / quill compensation limited by quill travel), and the scale
  would have to span both mechanical stacks. Unsafe and impractical.
- *Standalone DRO + manual entry* — reintroduces operator transcription error.

Why the correction lands in the WCS Z values and nowhere else: tool height offsets measure
tool-to-spindle-nose (head-independent), and machine coordinates / `G53 Z0` tool-change
position ride on the quill stack (also head-independent). Only the part-relative frame
moves with the head.

## Hardware

- **Scale:** linear glass (or magnetic) scale mounted along the head elevator travel.
  - Length: at least the full elevator travel — **TBD, measure elevator travel** (owner).
  - Resolution: 5 um (0.0002 in) or finer; standard DRO glass scales qualify.
  - Output: quadrature. **Differential (RS-422 style A/A-/B/B-) preferred.** ALLIN1DC
    encoder signal levels: low <= 0.5 V, high >= 3.0 V. A single-ended-TTL scale needs its
    output type verified or an RS-422 line-driver converter added.
  - Power: +5 V supplied by the board (DB-9 pin 9).
- **Input:** ALLIN1DC encoder input **4** (inputs 1–3 are the X/Y/Z servos; 4–6 are free —
  the wireless MPG is USB and uses none).
- **Wiring:** DB-9 per the install manual (pin 2 = common, 3/6 = Z-/Z+, 4/7 = A-/A+,
  5/8 = B-/B+, 9 = +5 V out). Ground the cable shield at the board end (ungrounded shield
  causes encoder errors).

## Control configuration — the verification gate

Target configuration: map encoder input 4 to **axis slot 4** as an encoder-only axis (no
drive — the ALLIN1DC has only 3). Then:

- Macros read the head's absolute counts directly at `#23804` (abs_position, axis 4) and
  the configured counts-per-unit at `#22904`.
- The PLC reads the same value as `SV_MPU11_ABS_POS_3`.

**Open item (gate before buying the scale):** confirm CNC12 accepts an axis-4 definition
with an encoder but no servo drive, without faulting. Bench-test with any spare quadrature
encoder plugged into input 4: configure axis 4, turn it by hand, watch `#23804` / the PID
AbsPos display. If CNC12 objects, ask the Centroid forum for the sanctioned "DRO-only
axis / scale input" configuration before proceeding.

Fallback plumbing if the macro-side variable does not populate but the PLC SV does: PLC
mirrors `SV_MPU11_ABS_POS_3` into `HeadAbs_FW` (FW17) and the macro reads `#98017`
(FW1–44 are macro-readable at `#98001–98044`).

## PLC changes (small, all `; Acroloc`-tagged)

In the existing MainStage rung group that mirrors `SV_MPU11_ABS_POS_0/1/2` into
`AbsX/Y/Z_FW`:

- `HeadAbs_FW IS FW17` — per-scan mirror of `SV_MPU11_ABS_POS_3` (head scale counts).
- `HeadPos_FW IS FW18` — head position in **inches since power-up**, computed as
  `HeadAbs_FW / <counts-per-inch constant>`, for a VCP "HEAD" readout next to the existing
  X/Y/Z machine-coordinate display (vcpgen data-display, same pattern as `MachZ_FW`).

No stage changes, no interlock changes. The elevator motor stays electrically independent.

## Re-sync macro + VCP button

A dedicated macro (VCP macro button via the retro skin generator; exact trigger per the
centroid-vcp button wiring — an unused mfunc number is the fallback). Logic:

```
IF #4201 || #4202 THEN GOTO 1000        ; graph/search guard (repo convention)
IF #29001 == 0 THEN GOTO 500            ; no valid latch this CNC12 session
; delta_inches = (#23804 - #29000) / <counts_per_inch>
; wcs_shift = -delta_inches            ; head UP moves part zero DOWN in machine coords
; #2701 = #2701 + wcs_shift            ; WCS#1 Z  (axis-3 values, #2701..#2718, R/W)
; ... repeat for #2702..#2718 ...
; operator message: "HEAD RE-SYNC: Z offsets shifted by <wcs_shift>"
N500
; #29000 = #23804                       ; latch current head counts
; #29001 = 1                            ; latch valid
; (first press after startup latches only, shifts nothing)
N1000
```

Key choices:

- **Latch lives in `#29000/#29001`** (user variables that reset when CNC12 exits). This is
  deliberate: scale counts also reset with the MPU11, so a stale latch can never survive a
  restart. After any CNC12 restart the first RE-SYNC press only latches, and part Z zero
  must be re-established — the failure mode is "must re-touch-off," never "silently wrong."
  Nonvolatile `#150–159` are explicitly NOT used for this reason.
- **All 18 WCS Z values shift together** so every fixture stays true, and the operation is
  idempotent (delta is measured from the latch, then the latch is updated).
- **Sign convention** (`wcs_shift = -delta`) assumes head-up = positive scale counts;
  the actual sign is fixed during calibration (below).
- **Active-WCS refresh:** after writing `#2701–#2718`, the macro re-selects the current
  WCS (re-issues the active G54–G59 code from `#4014`) so the DRO immediately reflects
  the shift — verify during testing whether this is required or automatic.

## Calibration & sign

1. Determine counts-per-inch: command nothing; crank the head a distance measured with a
   dial indicator; read the count change (5 um scale => 5080 counts/in at 4x quadrature —
   verify against the indicator, not the datasheet).
2. Determine sign: verify head-up direction against count direction; set the macro's sign
   so a head-up move shifts WCS Z negative (part zero farther from spindle nose).
3. Bake both into the macro as named constants with comments.

## Safety & failure modes

- **Forgot to re-sync:** Z is wrong by the full head move — inch-scale and obvious. The
  VCP HEAD readout makes the drift visible. Procedure: RE-SYNC is part of every head move.
- **CNC12 restart / power cycle:** latch is invalid by design; first press latches only
  and says so. Re-establish part Z zero.
- **Scale fault / noise:** re-sync accuracy equals scale accuracy; the HEAD readout can be
  sanity-checked against any known head move.
- **No interlock changes:** spindle-in-changer feed-hold, ATC watchdog, gear-shift logic
  untouched.
- **Future (out of scope):** PLC latches head counts at CYCLE START and warns/feed-holds
  if the head moves mid-job (pure-PLC, no macro involvement — cheap to add later).

## Testing

1. **Bench gate (before scale purchase):** spare encoder into input 4, axis-4 config,
   verify `#23804` (or fallback `SV_MPU11_ABS_POS_3` -> `#98017`) tracks rotation.
2. **Calibration:** counts/inch and sign vs dial indicator (above).
3. **End-to-end:** set part Z zero on a reference block; RE-SYNC; move head ~1 in;
   RE-SYNC; re-measure the block — Z error within scale tolerance (< 0.001 in).
4. **Restart case:** restart CNC12; press RE-SYNC; confirm "latched, no shift" behavior.
5. **Repeat-press case:** press RE-SYNC twice without moving the head; second press must
   shift by ~0.
6. `./compile.sh` after PLC edits (repo rule); `python3 tools/test_vcpgen.py` after VCP
   generator edits.

## Documentation to update with the implementation

- `.claude/skills/acroloc-s10/reference/head-elevator.md` — new subsystem file (elevator
  travel TBD -> measured value, scale model, counts/inch, sign) + row in the SKILL.md table.
- `docs/plc-spec/definitions.md` and `main-stage.md` — FW17/FW18 mirrors, pinned commit.
- `docs/plc-spec/` new section or macros doc for the re-sync macro.

## Open items

1. **Axis-4 encoder-only bench test** — gates everything; do first.
2. Elevator travel length (owner measures) -> scale length to order.
3. Scale model selection (differential output preferred; else line driver).
4. VCP button placement on the retro skin + exact trigger mechanism (macro button vs
   mfunc) per centroid-vcp.
