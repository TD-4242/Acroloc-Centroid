# RAPID 25% G0-only override + tool-change override restore

Date: 2026-08-05
Status: approved, pending machine verification (see "Test plan")

## Problem

A 10-32 form tap broke during a G84 tapping cycle in `Titan-4M-Op1-G54.nc`. The
operator had the VCP **RAPID 25%** button latched. The tap block is:

```
M3 S256.0
G84 X1.150 Y-0.338 Z-0.500 F7.987 S256.0 R0.000
```

7.987 ipm / 256 rpm = 0.0312 in/rev = 1/32", the correct 10-32 pitch. Any scaling
of the Z feed that does not equally scale the spindle desynchronises the tap. At
25% the tap is driven four times slower than the thread it is cutting.

The operator reported the CNC12 feedrate override reading 25%, and that other
programs did not show the behaviour.

## Root cause

Three independent defects compound. Only the first is certain to be causal; the
second is certainly a defect but its contribution is unproven; the third is a
latent hazard.

### D1 - `mfunc6.mac` disables overrides and never restores them

```
mfunc6.mac:13   M109 /1/2       ; Disable overrides
                (no M108 anywhere in the file)
```

Stock Centroid's ATC macro pairs these: `M109 /1/2` at
`docs/official/_ALLIN1DC/_atc/_umbrella/cncm/mfunc6.mac:28` and `M108 /1/2` at
line 94, immediately before its `N600` exit label. Ours has never had the
re-enable - `git log -S"M108" -- mfunc6.mac` returns no commits, so it has been
missing since `10e7d68 initial mfunc6.mac commit`.

Effect: after the **first M6** in any program, CNC12 stops accepting
`SV_PLC_FEEDRATE_KNOB` and holds the override at whatever value was current when
`M109` fired. Feed and spindle override are dead for the rest of the run. If the
override was at 25% at that moment, it is frozen at 25% with no way to back it
out. `Titan-4M-Op1-G54.nc` performs 8 tool changes before reaching the tap.

Note the apparent contradiction with `src:1971`, which forces
`FinalFeedOverride_W = 100` whenever the override-control flag is clear. There is
none: the PLC does set its own word to 100 and sends it, but CNC12 ignores
`SV_PLC_FEEDRATE_KNOB` entirely while override control is disabled and continues
applying its own last accepted percentage. The PLC's 100 is written and
discarded.

This matches the reported DRO reading of 25% exactly and explains why other
programs did not show it.

### D2 - the RAPID 25% write bypasses CNC12 entirely

```
src:2009   IF  Rapid25_M THEN SV_PLC_RAPID_FEEDRATE_OVERRIDE = 0.25
src:2010   IF !Rapid25_M THEN SV_PLC_RAPID_FEEDRATE_OVERRIDE = 1.0
```

Written unconditionally, every scan, straight to the MPU11. The feed path 40
lines above honours CNC12's lockout flag:

```
src:1971   IF !SV_PC_OVERRIDE_CONTROL_FEEDRATE_OVERRIDE THEN FinalFeedOverride_W = 100
```

That is the flag CNC12 clears during G74/G84 tapping cycles (see
`.claude/skills/centroid-cnc12-operating/reference/operator-panel.md:104`: "The
Feed Rate Override knob will not work during tapping cycles (G74 and G84)"). The
rapid write has no equivalent gate, so the tapping lockout cannot reach it.

`SV_PLC_RAPID_FEEDRATE_OVERRIDE` appears in **zero** of the ~20 stock Centroid
PLC programs under `docs/official/`. Its rapids-only behaviour is an assumption
this repo made, asserted as fact at `docs/plc-spec/main-stage.md:350-359`, and
never verified against the firmware.

### D3 - `Rapid25_M` has no reset path

`Rapid25_M` (MEM58) is a toggle latch with no power-up clear. Nothing ever
returns it to a known state.

### Why it surfaced now

D1 alone was merely inconvenient - you could not adjust override after a tool
change. The RAPID 25% button was added in `b90529c` (#19), which is when the
symptom appeared.

Two readings of that timing remain open, and **test 1 discriminates between
them**:

- If the SV is rapids-only, D1 is the sole cause: the operator's feed override
  was at 25% when the first `M109` froze it, and the RAPID 25% button was
  coincidental. The G0-only feature already works as intended.
- If the SV leaks into G1, D2 is the cause and D1 is what removed the operator's
  ability to recover, in which case the feature cannot meet the requirement.

Either way D1, D2 and D3 are defects and are fixed by this design. What test 1
determines is whether the RAPID 25% feature survives.

## Requirement

The RAPID 25% button must cut **G0 rapid moves only** and must never affect G1
feed moves.

## Mechanism survey

The complete set of rapid/override levers in `mpucomp.exe`:

| System variable | Kind | Meets "G0 only, fixed 25%"? |
| --- | --- | --- |
| `SV_PLC_RAPID_FEEDRATE_OVERRIDE` | rapid-specific percentage (0.0-2.0 scale) | Only candidate |
| `SV_PC_TOGGLE_RAPID_OVERRIDE` | mode toggle bit, no percentage | No - enabling it makes rapids follow the **feed** override percentage, so 25% rapids requires 25% G1 |
| `SV_PLC_FEEDRATE_OVERRIDE` / `_KNOB` | feed percentage | No - applies to G1 by definition |
| `SV_PC_OVERRIDE_CONTROL_FEEDRATE_OVERRIDE` | enable/lockout flag | Not a percentage; used here as a guard |

`SV_PLC_RAPID_FEEDRATE_OVERRIDE` is the only rapid-specific percentage the
controller exposes. There is no fallback mechanism.

A PLC-side G0-only gate (assert 0.25 only while a rapid is executing) was
considered and rejected as **not constructible**: no system variable exposes
motion type, so the PLC cannot tell a G0 from a G1. The G0-only guarantee must
come from the firmware's handling of the SV or not at all - which is why the
test plan gates this work.

## Design

Two files change.

### C1 - `mfunc6.mac`: restore overrides

Add `M108 /1/2` immediately before the `N1000` label, mirroring stock.

Placement before the label is deliberate. The macro's
`IF #4202 || #4201 THEN GOTO 1000` graph/search guard skips `M109` as well, so
both codes are skipped together and the enable/disable pair stays balanced.

### C2 - `src:2009-2010`: guard the rapid write

Gate both writes on CNC12's override-control flag, matching the feed path:

```
IF  Rapid25_M && SV_PC_OVERRIDE_CONTROL_FEEDRATE_OVERRIDE
    THEN SV_PLC_RAPID_FEEDRATE_OVERRIDE = 0.25
IF !Rapid25_M || !SV_PC_OVERRIDE_CONTROL_FEEDRATE_OVERRIDE
    THEN SV_PLC_RAPID_FEEDRATE_OVERRIDE = 1.0
```

The two conditions are exact complements, so the SV is written exactly once per
scan, preserving the existing structure.

This is defence in depth, not the fix. If the SV is genuinely rapids-only this
changes nothing observable. If it does leak into G1, this makes it structurally
impossible for the leak to occur during a tapping cycle, which is the case that
destroys tooling. Cost is one condition per rung.

Side effect, accepted: during a tool change `M109` clears the flag, so rapids run
at 100% for the duration of the change. This matches stock behaviour.

`RapidOverLED_O` (`src:2011`) continues to follow `Rapid25_M` alone. The LED
reports operator intent - the mode is still armed - rather than the instantaneous
applied value, so it does not flicker through every tapping cycle.

### C3 - `Rapid25_M` power-up clear

Add `Rapid25_M` to a power-up reset, alongside the existing `OnAtPowerUp_M`
(MEM200) rungs in the same region:

```
IF OnAtPowerUp_M THEN RST Rapid25_M
```

**No cycle-start clear.** A 25% rapid cut is precisely what an operator wants
armed during a first proveout run of a new program; clearing it at cycle start
would remove the feature's primary use case in order to defend against a latched
button being forgotten. `RapidOverLED_O` is the defence against that. This was
raised explicitly during design and the trade was accepted.

## Test plan

C2 makes the tapping case safe, but does not establish that the feature meets
the G0-only requirement. That requires the machine. **Test 1 gates the rest of
this work.**

1. **G1 leak test** (MDI, no tool, no workpiece). Latch RAPID 25%, run
   `G1 X1. F10.`, read the actual feedrate. Unlatch and repeat. 10 ipm in both
   cases means the SV is rapids-only and the feature meets the requirement.
   Anything lower means it scales G1 and the feature cannot meet the requirement
   as designed - **stop and reassess**; there is no alternative mechanism to fall
   back to.
2. **G0 effect test.** `G0 X1.` latched vs unlatched. Confirms the cut has an
   effect at all.
3. **Lockout test.** With RAPID 25% latched, observe
   `SV_PC_OVERRIDE_CONTROL_FEEDRATE_OVERRIDE` in PLC Detective through a G84 in
   scrap. Confirms C2's guard has a signal to act on, i.e. that CNC12 really does
   clear the flag during tapping.
4. **M108 regression.** Run a program containing an M6, then confirm the feed
   override buttons still respond after the tool change. Verifies C1.

Test 4 can be run independently of tests 1-3; C1 is a defect fix that stands on
its own regardless of the outcome of test 1.

## Verification

- `./compile.sh` after each `.src` edit; report the error/warning delta.
- Confirm the change is program-identical where expected via the plcfmt
  fingerprint `(program_words, C2, C4)`; the `.plc` md5 is non-deterministic.
- `.mac` and `.src` edits must stay plain 7-bit ASCII.

## Documentation updates

- `docs/plc-spec/main-stage.md:350-359` - the section currently asserts
  rapids-only behaviour as established fact. Rewrite to state the guard, and
  record the test 1 result as the basis for the rapids-only claim. Re-pin line
  numbers to the implementing commit.
- `docs/plc-spec/atc.md:41` - shows the `M109 /1/2` line; add `M108 /1/2`.
- `.claude/skills/acroloc-s10/reference/atc-flow.md:41` - same.
- `.claude/skills/acroloc-s10/reference/macros.md:47` - describes `M109 /1/2`
  disabling overrides; document the pairing requirement with `M108 /1/2`.

## Out of scope

- The `SelectRapidOverride_SV` / `SV_PLC_FUNCTION_34` legacy F9 and Ctrl-R toggle
  at `src:1998-2002`, which is set at power-up and links rapids to the feed
  override knob. It is untouched here. `system-variables.md:182` notes the SV is
  deprecated in favour of `SV_PC_TOGGLE_RAPID_OVERRIDE`; migrating it is separate
  work.
- The absent `M8` before the tapping section in `Titan-4M-Op1-G54.nc` (a form tap
  running dry). A CAM post-processor concern, not a controller one.
- `Titan-4M-Op1-G54.nc` terminating with `M99` rather than `M30`.
