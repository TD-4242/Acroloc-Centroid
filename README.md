# Acroloc-Centroid

Centroid **CNC12** PLC program and M-code macros for an **Acroloc** mill retrofitted with a
Centroid **ALLIN1DC** motion controller (MPU11-based).

This repo is the controller-level source: a PLC program written in Centroid's stage/ladder
language, plus the M-function macros that the CNC calls. It is compiled and loaded by the
Centroid CNC12 software (`cncm`) on the Windows control PC — there is no build step in this
repository.

## Files

| File | Purpose |
| --- | --- |
| `Centroid-Acroloc-ALLIN1DC.src` | The PLC program (definitions + stages). Primary file. |
| `mfunc3.mac` / `mfunc4.mac` | Spindle start CW / CCW |
| `mfunc6.mac` | Tool change (M6) — drives the custom Acroloc ATC |
| `mfunc7.mac` / `mfunc8.mac` | Coolant: mist / flood |
| `mfunc10.mac` / `mfunc11.mac` | Clamp on / off |

Custom logic added for this machine is tagged with the comment marker `; Acroloc` throughout
the `.src`.

## PLC subsystems

A full line-referenced specification of the PLC program lives in `docs/plc-spec/`, split into
one file per subsystem. Start with the scan model and the definitions atlas — every other file
cites them instead of repeating naming/timing rules.

- [`docs/plc-spec/scan-model.md`](docs/plc-spec/scan-model.md) — how the `.src` actually
  executes each scan: stage sweep order, same-scan-vs-next-scan `SET`/`RST` timing, timer
  semantics, and write-conflict resolution. Read this first.
- [`docs/plc-spec/definitions.md`](docs/plc-spec/definitions.md) — the resource atlas: every
  symbol in the definitions block (`_I`/`_O`/`_M`/`_W`/`_T`/`_SV`/`_C`/stage) mapped to its
  source line, plus the message-constant encoding rule.
- [`docs/plc-spec/boot.md`](docs/plc-spec/boot.md) — what happens before the machine is ready
  to run: `WatchDogStage`, `InitialStage`'s one-scan power-up latch (including the Acroloc
  power-up gear defaults), and the `LoadParametersStage` parameter-load handshake.
- [`docs/plc-spec/main-stage.md`](docs/plc-spec/main-stage.md) — `MainStage` (STG4): E-stop/
  reset, probe protection, fault aggregation, M-code housekeeping, the ATC kickoff/safety
  rungs, and the spindle/coolant/gear-decision logic structurally nested under it.
- [`docs/plc-spec/atc.md`](docs/plc-spec/atc.md) — the custom Acroloc automatic tool changer:
  `mfunc6.mac`'s macro orchestration, the `MainStage` kickoff/safety rungs, and the `ATCStage`
  (STG16) carousel-indexing state machine, including the base-16-as-decimal position-switch
  encoding and the 20 s carousel-search watchdog.
- [`docs/plc-spec/gear-shift.md`](docs/plc-spec/gear-shift.md) — the custom RPM-based automatic
  two-speed clutch selection: the `DesiredRange_W` decision logic, the mutual-exclusion clutch
  interlock, and the `GearShiftStage` (STG17) open-loop neutral-coast-engage sequence.
- [`docs/plc-spec/jog-and-mpg.md`](docs/plc-spec/jog-and-mpg.md) — the operator jog/MPG path:
  hardwired MPG, wireless/USB MPG, jog-panel key decode/override math, and the four
  configuration-selected axis-mapping stages.
- [`docs/plc-spec/faults-and-messages.md`](docs/plc-spec/faults-and-messages.md) — drive/
  fiber/PLC-bus/MiniPLC communication-health checks and the fault-bit -> message-word ->
  on-screen operator message pipeline.
- [`docs/plc-spec/parameters.md`](docs/plc-spec/parameters.md) — every
  `SV_MACHINE_PARAMETER_n` the `.src` reads, in one table, each row citing the reading rung and
  the subsystem file that documents it.

## Spindle speed & range (transmission) shifting

The Acroloc spindle has a **two-speed transmission** (low / high range). The current gear is
tracked from the clutch outputs the PLC itself commands (not a sense switch), and the PLC
automatically shifts range based on the commanded spindle RPM — an open-loop, timed
neutral-coast-then-engage clutch swap with no rev-match or position feedback. Power-up leaves
the transmission in **neutral** (both clutches energized — both *off* would be a mechanical
lockup); the gear is unknown until the first spin-up engages one. Full line-referenced detail
(decision logic, DAC-ratio math, clutch interlock, the `GearShiftStage` state machine, and the
P860–P863 parameter table) is in
[`docs/plc-spec/gear-shift.md`](docs/plc-spec/gear-shift.md); on-machine verification steps
(shift boundaries, coast-dwell tuning, RPM accuracy) are in
[`docs/testing/rpm-gear-shift-test-plan.md`](docs/testing/rpm-gear-shift-test-plan.md).

## Automatic tool changer (ATC)

The Acroloc uses a **rotary carousel** tool changer. It is a **Z-motion mechanical** changer,
not a modern arm type: at machine Z0 the spindle is empty (the tool rests in the carousel), the
tool locks to the spindle at about Z -1.5", and the spindle may spin by about Z -1.75/-2". A
tool change spans three places: `mfunc6.mac` (the M6 macro), the ATC kickoff/safety logic in
`MainStage`, and the `ATCStage` (STG16) state machine that decodes the 5 carousel position
switches (a **bin/position** ID, base-16 encoded as decimal) and indexes to the requested
tool's bin. A 20 s watchdog faults the search if the bin is never found. All of this is custom
work tagged `; Acroloc`.

**Tool-to-bin mapping.** Tool numbers are decoupled from bins, so a tool numbered above the 12
physical bins can be used: machine parameters **P701-P712** hold the tool loaded in bins 1-12,
and `MainStage` translates the requested tool to its bin. The map is fixed and operator-owned
(CNC12's own enhanced-ATC modes are deliberately not used — `P160 = 0`). See
[`docs/superpowers/specs/2026-07-22-tool-bin-mapping-design.md`](docs/superpowers/specs/2026-07-22-tool-bin-mapping-design.md)
and the on-machine procedure in
[`docs/testing/tool-bin-mapping-test.md`](docs/testing/tool-bin-mapping-test.md).

Full line-referenced detail — the three-piece flow, the I/O table, the carousel position
encoding, and manual unlock — is in [`docs/plc-spec/atc.md`](docs/plc-spec/atc.md) (pinned to
an older commit; see its banner) and, for the current flow, the `acroloc-s10` skill's
[`reference/atc-flow.md`](.claude/skills/acroloc-s10/reference/atc-flow.md).

## Operator panel (VCP) and control-PC files

The on-screen operator panel is a generated retro theme: edit
[`tools/vcpgen.py`](tools/vcpgen.py) and re-run it — never hand-edit the emitted
`resources/vcp/` files (`python3 tools/test_vcpgen.py` checks the output).

Several CNC12 files on the control PC are customized for this machine and tracked here
(`language.msg` parameter labels, `plcmsg.txt` operator messages, `cncm.hom` homing). A CNC12
upgrade can overwrite them — see
[`docs/control-pc-customizations.md`](docs/control-pc-customizations.md) for what is
customized and how to restore it.
