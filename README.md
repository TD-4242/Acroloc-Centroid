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
| `plc.map` | Generated symbol→source-line map from the PLC compiler. Do not hand-edit. |
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
  encoding and the known no-carousel-timeout gap.
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
neutral-coast-then-engage clutch swap with no rev-match or position feedback. Power-up engages
low range. Full line-referenced detail (decision logic, DAC-ratio math, clutch interlock, the
`GearShiftStage` state machine, and the P860/P861/P862 parameter table) is in
[`docs/plc-spec/gear-shift.md`](docs/plc-spec/gear-shift.md); on-machine verification steps
(shift boundaries, coast-dwell tuning, RPM accuracy) are in
[`docs/testing/rpm-gear-shift-test-plan.md`](docs/testing/rpm-gear-shift-test-plan.md).

## Automatic tool changer (ATC)

The Acroloc uses a **rotary carousel** tool changer. A tool change spans three places:
`mfunc6.mac` (the M6 macro), the ATC kickoff/safety logic in `MainStage`, and the `ATCStage`
(STG16) state machine that decodes the 5 carousel position switches (base-16 encoded as
decimal) and indexes to the requested tool. All of this is custom work tagged `; Acroloc`.
Full line-referenced detail — the three-piece flow, the I/O table, the carousel position
encoding, manual unlock, and the known no-carousel-timeout gap — is in
[`docs/plc-spec/atc.md`](docs/plc-spec/atc.md).
