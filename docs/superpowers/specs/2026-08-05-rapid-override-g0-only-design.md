# Tool-change override restore + removal of the RAPID 25% bypass

Date: 2026-08-05 (revised 2026-08-06 after machine testing)
Status: approved, machine-verified root cause

## Problem

A 10-32 form tap broke during a G84 tapping cycle in `Titan-4M-Op1-G54.nc`, with
the VCP **RAPID 25%** button latched. The tap block is:

```
M3 S256.0
G84 X1.150 Y-0.338 Z-0.500 F7.987 S256.0 R0.000
```

7.987 ipm / 256 rpm = 0.0312 in/rev = 1/32", the correct 10-32 pitch.

The operator observed an actual feedrate of **~2 ipm** where ~8 was commanded:

```
7.987 * 0.25 = 1.997
```

A 0.25 scale reached the tapping feed. The tap advanced at a quarter of the pitch
it was cutting, and broke.

## Machine test results (2026-08-06)

Two measurements, taken on the machine with no code changes, resolve the
investigation:

1. **With RAPID 25% latched, both G0 and G1 are scaled.**
   `SV_PLC_RAPID_FEEDRATE_OVERRIDE` is **not** rapids-only. It is a global
   velocity scale.
2. **The stock FEED 25% button also slows both G0 and G1.** Expected:
   rapid-override mode is `SET` at power-up by stock logic (`src:2002`), which
   links rapids to the feed override percentage.

Result 1 falsifies the central assumption this feature was built on. Result 2
establishes that RAPID 25% is functionally redundant with FEED 25%.

## Root cause

### D1 - `mfunc6.mac` disables overrides and never restores them

```
mfunc6.mac:13   M109 /1/2       ; Disable overrides
                (no M108 anywhere in the file)
```

Stock Centroid's ATC macro pairs these: `M109 /1/2` at
`docs/official/_ALLIN1DC/_atc/_umbrella/cncm/mfunc6.mac:28` and `M108 /1/2` at
line 94, immediately before its `N600` exit. Ours has never had the re-enable -
`git log -S"M108" -- mfunc6.mac` returns no commits, so it has been missing since
`10e7d68 initial mfunc6.mac commit`.

Effect: after the **first M6** in any program, CNC12 stops accepting
`SV_PLC_FEEDRATE_KNOB` and holds the override at whatever value was current when
`M109` fired. Feed and spindle override are dead for the rest of the run.

This is more serious than a lost convenience. CNC12's documented tapping
protection - "The Feed Rate Override knob will not work during tapping cycles
(G74 and G84)"
(`.claude/skills/centroid-cnc12-operating/reference/operator-panel.md:104`) -
operates through override control. With override control disabled by an
unpaired `M109`, **CNC12 cannot force the override back to 100% for a tapping
cycle.** The missing `M108` disables the very interlock that exists to stop this
failure.

Note the apparent contradiction with `src:1971`, which forces
`FinalFeedOverride_W = 100` whenever the override-control flag is clear. There is
none: the PLC does set its own word to 100 and send it, but CNC12 ignores
`SV_PLC_FEEDRATE_KNOB` entirely while override control is disabled and continues
applying its own last accepted percentage. The PLC's 100 is written and
discarded.

### D2 - the RAPID 25% write bypasses CNC12 entirely

```
src:2009   IF  Rapid25_M THEN SV_PLC_RAPID_FEEDRATE_OVERRIDE = 0.25
src:2010   IF !Rapid25_M THEN SV_PLC_RAPID_FEEDRATE_OVERRIDE = 1.0
```

Written unconditionally, every scan, straight to the MPU11, with no gate on
CNC12's override-control flag - unlike the feed path 40 lines above at
`src:1971`. CNC12 cannot see this scale and cannot lock it out for a tapping
cycle.

Per test result 1 the SV scales G1 as well as G0, so this is a global velocity
cut applied behind CNC12's back. `SV_PLC_RAPID_FEEDRATE_OVERRIDE` appears in
**zero** of the ~20 stock Centroid PLC programs under `docs/official/`; the
rapids-only behaviour asserted at `docs/plc-spec/main-stage.md:350-359` was this
repo's own assumption and is now disproven.

### Why it surfaced now

D1 alone was inconvenient - you could not adjust override after a tool change.
RAPID 25% was added in `b90529c` (#19). Only once both existed could a global 25%
scale be active while CNC12's tapping interlock was disabled.

## Evidence: the job that worked vs the job that broke

| | `Titan-3M-FirstOP-G54.nc` (worked) | `Titan-4M-Op1-G54.nc` (broke) |
| --- | --- | --- |
| M6 tool changes | 6 | 9 |
| G84 blocks | 6 | 3 |
| Tap spindle | `S128.0` | `S256.0` |
| Tap feed | `F3.994` | `F7.987` |
| in/rev | 0.0312 (1/32", correct) | 0.0312 (1/32", correct) |
| Tool before tap | T7 chamfer, `S3499.6` | T7 chamfer, `S3499.6` |
| G-code vocabulary, tapping block structure | identical | identical |

Both command the correct pitch. The only material difference is that 4M taps at
double the spindle speed and double the feed. The surviving explanation for 3M
being unharmed is operator-side state - what the override was actually sitting at
when each run's first `M109` fired - which is not recoverable from the files and
does not change the fix.

### Hypotheses falsified during investigation

Recorded so they are not re-explored:

- **Gear-range crossover.** S128 vs S256 might have straddled the two-speed
  transmission crossover. They do not: `P860 = 800`, `P861 = 100`
  (`docs/testing/rpm-gear-shift-test-plan.md:34`), so both taps ran in **low**
  range.
- **"Earlier tapping jobs had no tool change."** 3M has 6 M6 and 6 G84 blocks, so
  the missing `M108` was equally in play in the clean run.
- **Rapid-override mode being an Acroloc addition.** `src:1998-2002` is
  byte-identical to stock `allin1dc-umbrella-v7.src:1770-1774`, including the
  power-up `SET`.

## Requirement, and why it cannot be met

The stated requirement was a button cutting **G0 only**, never touching G1.

**No mechanism in this controller can deliver that.** The complete survey:

| Mechanism | Verdict |
| --- | --- |
| `SV_PLC_RAPID_FEEDRATE_OVERRIDE` | Measured to scale G1. Fails. |
| `SV_PC_TOGGLE_RAPID_OVERRIDE` | Mode toggle, no percentage; links rapids to the feed override %. Fails. |
| Machine parameters (Max Rate) | PLC cannot write them - all 82 `SV_MACHINE_PARAMETER` uses in our source are comparisons, never assignments. Operator-menu only (`F2 Mach -> F1 Jog`). Not button-driveable. |
| `SV_VELOCITY_RATIO` | Present in `mpucomp.exe`, used by zero stock PLCs, absent from all documentation. Unknown semantics. |
| PLC-side gating on motion type | Not constructible - no system variable exposes whether the current move is a G0 or a G1. |

`SV_VELOCITY_RATIO` is deliberately **not** proposed. Shipping behaviour based on
an undocumented velocity system variable is exactly the mistake that broke the
tap.

The closest available behaviour is the existing FEED 25% button, which per test
result 2 already slows both G0 and G1 - the same effect RAPID 25% produced, but
routed through CNC12 where the tapping lockout can protect it.

## Design

Two files change. The RAPID 25% feature is removed rather than repaired.

### C1 - `mfunc6.mac`: restore overrides

Add `M108 /1/2` immediately before the `N1000` label, mirroring stock.

Placement before the label is deliberate: the macro's
`IF #4202 || #4201 THEN GOTO 1000` graph/search guard skips `M109` too, so both
codes are skipped together and the pair stays balanced.

This is the core safety fix. It restores override control, and with it CNC12's
ability to lock the feed override to 100% during a G74/G84 cycle.

### C2 - remove the RAPID 25% button and its PLC logic

Justification: per test 1 it is a global velocity cut, not a rapids-only cut, so
it does not do what its label claims; per test 2 it is redundant with FEED 25%,
which achieves the same result under CNC12's supervision. Its only distinguishing
property is that it bypasses the tapping interlock. Removing it costs no
capability and closes the bypass completely.

Remove:

- `src:2004-2011` - the comment block, `Rapid25PD_PD` one-shot, `Rapid25_M`
  toggle, both `SV_PLC_RAPID_FEEDRATE_OVERRIDE` writes, and the `RapidOverLED_O`
  coil.
- Definitions that become unused: `RapidOverLED_O` (`src:494`), `Rapid25_M`
  (`src:528`), `SkinRapid25_M_SV` (`src:1038`), `Rapid25PD_PD` (`src:1214`).
- The `rapid_over` entry in `tools/vcpgen.py` (~line 518) and its emitted button.
  **Regenerate** `resources/vcp/` by running the generator; never hand-edit
  emitted files.

Leaving `SV_PLC_RAPID_FEEDRATE_OVERRIDE` entirely unwritten restores the MPU
default of 1.0. No residual scale can survive.

Removing the latch also retires the "no reset path" defect (`Rapid25_M`, MEM58,
had no power-up clear) without needing separate logic.

The grid cell at row 11 / col 5 is left empty. Re-flowing the button layout is
not part of this change.

## Verification

- `./compile.sh` after each `.src` edit; report the error/warning delta.
- `python3 tools/test_vcpgen.py` after the generator change.
- Confirm the fingerprint `(program_words, C2, C4)` reflects the intended
  removal; the `.plc` md5 is non-deterministic and is not a valid check.
- `.mac` and `.src` edits stay plain 7-bit ASCII.

### Machine tests after loading

1. **M108 regression.** Run a program containing an M6, then confirm the feed
   override buttons respond after the tool change. Verifies C1.
2. **Tapping lockout.** With FEED 25% latched, run a G84 in scrap. The feedrate
   must **not** drop to 25% - CNC12 should hold it at 100% for the cycle. This is
   the test that proves the original failure can no longer occur. It could not
   have passed before C1.
3. **No residual scale.** Confirm G0 and G1 both run at 100% with no override
   selected, i.e. nothing is still writing a rapid scale.

## Documentation updates

- `docs/plc-spec/main-stage.md:350-359` - delete the "RAPID 25% rapids-only
  override" section. Record in its place, or in
  `.claude/skills/centroid-plc-programming/reference/system-variables.md`, the
  measured finding that `SV_PLC_RAPID_FEEDRATE_OVERRIDE` scales **all** motion
  and bypasses CNC12's override control, so it is not usable for a rapids-only
  cut.
- `docs/plc-spec/definitions.md:181` - remove the `Rapid25_M` row; remove the
  other three retired definitions.
- `docs/plc-spec/atc.md:41` and
  `.claude/skills/acroloc-s10/reference/atc-flow.md:41` - both show the
  `M109 /1/2` line; add `M108 /1/2`.
- `.claude/skills/acroloc-s10/reference/macros.md:47` - document that
  `M109 /1/2` must always be paired with `M108 /1/2`, and why: an unpaired
  `M109` disables CNC12's tapping override lockout for the rest of the program.
- `docs/superpowers/specs/2026-07-13-retro-vcp-theme-design.md:48` - describes
  the RAPID 25% button as a rapids-only cut. Annotate as removed and superseded
  by this spec.
- **Do not re-baseline the plc-spec line pins.** `docs/plc-spec/*.md` pin source
  line numbers to commit `41f3fd6` via a "Line numbers as of commit 41f3fd6"
  header. Established practice in this repo is to remove or correct false
  *content* when editing these files and leave the line-number references and
  the pin header alone. An earlier draft of this spec called for re-pinning to
  the implementing commit; that was wrong and is retracted.

## Out of scope

- The `SelectRapidOverride_SV` / `SV_PLC_FUNCTION_34` legacy F9 and Ctrl-R toggle
  at `src:1998-2002`. It is stock, byte-identical to the vendor source, and is
  what makes FEED 25% affect rapids - the behaviour we are now relying on.
  `system-variables.md:182` notes the SV is deprecated in favour of
  `SV_PC_TOGGLE_RAPID_OVERRIDE`; migrating it is separate work.
- Investigating `SV_VELOCITY_RATIO` as a future genuine G0-only mechanism. Worth
  a bench probe someday; not part of a fix for a broken-tap incident.

- **The stock `rapidrate_*` button family (found 2026-08-06 during
  implementation).** Centroid's button library ships
  `resources/vcp/Buttons/rapidrate_25|50|75|100` on skin events **114-117** with
  LEDs **OUT1141-1144** - a discrete rapid-rate override cluster wholly separate
  from the feedrate family (events 53/111/112/113, LEDs OUT1137-1140). A
  `rapid_feed` toggle button swaps a `feed_group` for a `rapid_group`, implying
  the stock panel intends one cluster to be shown at a time.

  This is the strongest remaining candidate for a genuine G0-only 25% cut and
  should be probed before concluding the requirement is impossible. Two caveats
  found so far:

  - **No stock ALLIN1DC PLC implements them.** Events 114-117 appear in stock
    sources only as unnamed placeholders (`;   IS SV_SKIN_EVENT_114`), and
    OUT1141-1144 appear in none of them.
  - If the events are PLC-side rather than consumed natively by CNC12, a handler
    would have nothing to write except `SV_PLC_RAPID_FEEDRATE_OVERRIDE` - the
    same global-scale SV measured here - and would inherit this same defect.

  The probe is cheap: add `rapidrate_25` to the panel with no PLC handler at all
  and press it. If rapids change, CNC12 consumes the event natively and this is
  the mechanism we want. If nothing happens, the event is PLC-side and the
  requirement remains unachievable.
- Re-flowing the VCP button grid to fill the vacated cell.
- The absent `M8` before the tapping section in `Titan-4M-Op1-G54.nc` (a form tap
  running dry) and its `M99` rather than `M30` ending. CAM post-processor
  concerns, not controller ones.
