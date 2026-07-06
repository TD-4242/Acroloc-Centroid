# Faults, comm health, and the operator message pipeline

One-line purpose: reference for the drive/fiber/PLC-bus/MiniPLC communication-health checks
(`CheckCycloneStatusStage`, `MiniPLCErrorStage`), the fault-bit -> message-word -> on-screen
display pipeline (`MessageStage`, `ShowFaultStage`, `ShowErrorStage`, `ShowInfoStage`,
`BadMsgStage`), and how the fault bits documented here feed the central OR-gate in
`main-stage.md`'s [Fault aggregation](main-stage.md#fault-aggregation-src2840-2882) section.

Line numbers as of commit 41f3fd6

Stage sweep order and timer semantics are defined in
[scan-model.md](scan-model.md); resource name -> line lookups (including the
`value = msgNumber + 256 * msgFile` message-constant encoding rule) are in
[definitions.md](definitions.md#message-constant-encoding). Neither is repeated here.

## Scope note

This file does not re-document `MainStage`'s fault OR-gate rung group
(src:2840-2882, `SET SV_STOP` on any fault bit, and the single recovery
rung) — that is covered in main-stage.md under
[Fault aggregation](main-stage.md#fault-aggregation-src2840-2882). This file covers the *producers* that
set those fault bits (comm-health checks) and the *consumer* pipeline that turns
`FaultMsg_W`/`ErrorMsg_W`/`InfoMsg_W` into an on-screen operator message.

## `CheckCycloneStatusStage` (STG8, src:1200, banner src:2491-2493)

Purpose (source comment, src:2494-2496): polls drive/fiber communication
health. Deliberately run only a few times a second (see re-arm mechanism below), not every
scan, because reading the Cyclone status is comparatively slow.

- **Per-axis drive-online check** (src:2501-2509): for each configured axis
  (`SV_n_AXIS_VALID`, X/Y/Z/A/B/C/U/V/W), if the axis is valid but
  `!SV_n_AXIS_DRIVE_ONLINE`, post an axis-specific `*_INFLT_C` fault message and
  `SET DriveComFltIn_M` — "incoming" fault, the drive isn't reporting online at all.
- **Per-axis fiber-ok check** (src:2512-2529): for each valid, *online* axis,
  if `!SV_n_AXIS_FIBER_OK` while `SV_MASTER_ENABLE` is on, post a `*_OUTFLT_C` message and
  `SET DriveComFltOut_M` — "outgoing" fault, distinguished from the incoming case by requiring
  the drive to already be online; gated on `SV_MASTER_ENABLE` so a fiber glitch isn't flagged
  while the axis isn't even supposed to be enabled.
- (src:2531): `!EStopOk_M` clears both `DriveComFltIn_M`/`DriveComFltOut_M` — same
  clear-fault-latch-on-E-stop pattern noted as a gotcha in main-stage.md's fault-aggregation
  section (main-stage.md, src:2846-2851): the latch is cleared the instant
  E-stop is asserted, not when the underlying condition is actually fixed.
- (src:2532): either drive-comm fault bit -> `SET AxisFault_M`, which folds into the
  `SV_STOP` OR-gate (main-stage.md, src:2841).
- **PLC bus fiber checks** (src:2535-2549): decodes `SV_PC_CYCLONE_STATUS_1`
  via `BITTST` into `PLCBusExtDevEn_M`/`JogPanelOnline_M` (src:2535-2537);
  `!SV_PLC_BUS_ONLINE` posts `PLC_INFLT_C` and `SET PLCFault_M`
  (src:2540-2541); PLC bus online but the output-enable handshake not
  reflected (`PLCBus_Oe_M && !PLCBusExtDevEn_M`) posts `PLC_OUTFLT_C`
  (src:2544-2545); the clear rung (src:2548-2549) requires bus online,
  ext-dev-enable confirmed, *and* `!EStopOk_M` — an inverted-looking gate, but per the pattern
  elsewhere in this file, `!EStopOk_M` here doubles as "we are currently faulted/stopped,"
  i.e. this is the recovery path taken while stopped, not a require-E-stop-asserted rung.
- **JogBoard link checks** (src:2551-2558): `SV_JOG_LINK_ONLINE` ->
  `JogLinkOk_M`; if the jog panel is required (`JogPanelRequired_M`, a machine-config bit) and
  the link isn't ok, or the link is ok but the panel isn't reporting online
  (`!JogPanelOnline_M`), post `JOGBOARD_INFLT_C`/`JOGBOARD_OUTFLT_C` and `SET OtherFault_M` —
  note this folds into `OtherFault_M`, not `AxisFault_M`, since it's a panel-link problem, not
  a drive problem.
- **MiniPLC comm-status handoff** (src:2560-2563): latches
  `MiniPLCStatus_W`/`P900Value_W` from `SV_PC_MINI_PLC_ONLINE`/`SV_MACHINE_PARAMETER_900`;
  if they differ, `SET MiniPLCErrorStage` — because `MiniPLCErrorStage` (STG9,
  src:1201) is swept immediately after this stage in file order, per
  `scan-model.md` this `SET` takes effect **in this same scan**.
- (src:2565): `RST CheckCycloneStatusStage` unconditionally at the end of its own body — this
  stage always disarms itself the scan after it runs; see re-arm mechanism below.

### Re-arm mechanism (throttling the poll rate)

`CheckCycloneStatusStage` is not swept every scan despite being `SET`/`RST` within itself —
it is re-armed from `AxesEnableStage` (src:2601-2603, banner src:2601-2603):
`IF True_M THEN SET CycloneStatus_T` arms a timer every scan, and
`IF CycloneStatus_T THEN SET CheckCycloneStatusStage, RST CycloneStatus_T`
(src:2616-2617) only re-`SET`s the Cyclone-status stage once that timer
expires, then immediately disarms the timer so it starts counting again — a
timer-gated self-limiting poll loop, matching the "only called a few times per second"
comment at the top of `CheckCycloneStatusStage`. `AxesEnableStage` also has its own
axis-fault clear rung (src:2609-2610, posts `AXIS_FLT_CLR_C` once
`AxisFault_M` is set but neither comm-fault bit is, while `!EStopOk_M`) and gates
`SV_MASTER_ENABLE` on the absence of both drive-comm fault bits
(src:2620) — the comment there (src:2621-2626) is explicit that
stall/other-fault-driven `SV_MASTER_ENABLE` resets happen later, in `MainStage`'s
fault-aggregation section.

## `MiniPLCErrorStage` (STG9, src:1201, banner src:2567-2569)

Purpose: decode which of up to 8 MiniPLC boards the machine config expects
(`P900Value_W`, from `SV_MACHINE_PARAMETER_900`) against which are actually reporting online
(`MiniPLCStatus_W`, from `SV_PC_MINI_PLC_ONLINE`), per-board.

- (src:2570-2571): `WTB` decodes both words into 8 per-board bits each —
  `MiniPLCExpectedN_M` (config says board N should exist) and `MiniPLCOkN_M` (board N is
  reporting online).
- (src:2573-2588): for each of the 8 boards, expected-but-not-ok posts a
  board-specific `MINI_PLC_N_FLT_MSG_C` and `SET OtherFault_M` — same fault bit as the
  JogBoard-link case above, folding into the same `SV_STOP` path.
- (src:2590-2597): the reverse case — a board reporting ok that the config didn't expect —
  posts a `MINI_PLC_N_WARNING_C` *info* message, not a fault; an extra/misconfigured board is
  flagged but doesn't stop the machine.
- (src:2599): `RST MiniPLCErrorStage` unconditionally — this stage runs once per activation
  (re-armed only when `CheckCycloneStatusStage` detects a status/expected mismatch, per the
  handoff rung above) and disarms itself the same way `CheckCycloneStatusStage` does.

## `OtherFault_M` as the catch-all fault bit

`OtherFault_M IS MEM57` (definitions.md, src:506) is the fault-class memory bit
for anything that doesn't have its own dedicated bit (`AxisFault_M`, `SpindleFault_M`,
`LubeFault_M`, `ProbeFault_M`, `PLCFault_M`). Producers seen across this file and
main-stage.md: JogBoard link/online failures (src:2554,
src:2558), MiniPLC board mismatches (src:2574-2588), and the
ATC clutch double-engagement interlock (main-stage.md, src:2396-2405).
`OtherFault_M` participates in the same central OR-gate as every other fault bit
(main-stage.md, `SV_STOP` rung at src:2841) and the same blanket recovery rung
(main-stage.md, src:2872-2875) — it has no separate clear/recovery path of its
own in this file; clearing it requires the aggregate recovery conditions in main-stage.md to
all hold simultaneously.

## Fault bits

Summary table of the fault-class memory bits that feed `MainStage`'s `SV_STOP` OR-gate
(main-stage.md, src:2840-2882). "Producer" cites where each bit is set; "Recovery"
cites the dedicated clear rung if one exists, otherwise "aggregate" (cleared only by
main-stage.md's blanket recovery rung, src:2872-2875).

| Bit | Definition | Producer(s) | Recovery |
|---|---|---|---|
| `PLCFault_M` | MEM50, definitions.md src:499 | PLC bus fiber in/out faults (src:2540-2545) | Dedicated clear rung, src:2548-2549 |
| `AxisFault_M` | MEM51, definitions.md src:500 | `DriveComFltIn_M`/`DriveComFltOut_M` (src:2532) | Dedicated clear rung, `AxesEnableStage` src:2609-2610 |
| `SpindleFault_M` | (see definitions.md) | Spindle-inverter-not-ok at boot-armed `Initialize_T` (main-stage.md, src:2858-2860); ATC clutch double-engagement (main-stage.md, src:2396-2405) | Aggregate only |
| `LubeFault_M` | (see definitions.md) | Lube-not-ok while not running, gated on `Initialize_T` (main-stage.md, src:2853-2854) | Aggregate only |
| `ProbeFault_M` | (see definitions.md) | Probe-tripped-while-jogging (main-stage.md, src:2711-2718) | Aggregate only (message-sent guard `ProbeMsgSent_M` per main-stage.md's own noted gotcha, src:2881-2882) |
| `OtherFault_M` | MEM57, definitions.md src:506 | JogBoard link/online (src:2553-2558), MiniPLC board mismatch (src:2573-2588), ATC clutch interlock (main-stage.md, src:2396-2405) | Aggregate only |
| `SV_STALL_ERROR` | CNC12 system variable, not a PLC-defined bit | Set by CNC12's own servo-stall detection, outside this file | Aggregate only |
| `SoftwareNotReady_M` / `PLCExecutorFault_M` | (see definitions.md) | Set during `WatchDogStage`/`InitialStage` boot sequencing (boot.md) | Checked only in the aggregate recovery rung (main-stage.md, src:2872-2875); not part of the `SET SV_STOP` OR itself |

`!EStopOk_M` is not a fault-class memory bit but participates identically in the `SV_STOP`
OR-gate (main-stage.md, src:2841) and, uniquely, is the condition that clears
several of the *other* fault latches the instant it goes true (main-stage.md,
src:2846-2851) — see the gotcha called out there and echoed at
src:2531 above for `DriveComFltIn_M`/`DriveComFltOut_M`.

## `SafetySwitchInterruptStage` (STG62, src:1215, banner src:3018-3020)

Purpose (inferred from the rungs, no source comment): watches the enclosure door/safety
switch (`DoorClosed_I`) and posts one of two distinct fault messages depending on whether the
door opens while the spindle is trying to run versus while a job is already in progress.
Armed once at boot from `InitialStage` (`SET SafetySwitchInterruptStage`, boot.md src:1263)
and never explicitly `RST` anywhere in this file — unlike every other stage documented in this
file, it stays `SET` (swept every scan) for the life of the PLC program rather than
self-disarming.

- (src:3021) `IF DoorClosed_I THEN (SafetySwitch_M)` — `SafetySwitch_M IS MEM29`
  (definitions.md, src:486) directly mirrors the door-closed input; there is no
  latch here; the bit follows the switch live, every scan.
- **Spindle-start interlock** (src:3022-3023): if the door is open
  (`!SafetySwitch_M`) at the moment a spindle start is requested — from the panel
  (`SpinStart_M`), the keyboard (`KbSpinStart_M`), or an M3/M4 program command (`M3_SV`/
  `M4_SV`) — post `SAFETY_SWITCH_SPINDLE_MSG` (definitions.md src:177, `23809 = 1+256*93`) and
  `SET ErrorFlag_M`. This is the "you tried to start the spindle with the door open" case.
- **Job-in-progress interlock** (src:3025-3028): `SafetySwitchToolCheck_M`
  (`MEM30`, definitions.md src:487) is forced `SET` whenever no job is running
  (`!SV_JOB_IN_PROGRESS`, src:3025) — this is a "door was already open before/between jobs,
  don't fault on it" arm-once-per-job-start guard. Once a job *is* in progress
  (`SV_JOB_IN_PROGRESS`), if the door opens (`!SafetySwitch_M`) and the check hasn't already
  latched (`!SafetySwitchToolCheck_M`) and the spindle isn't currently commanded on
  (`!(M3_SV || M4_SV)`), post `SAFETY_SWITCH_OPEN_MSG` (definitions.md src:176,
  `23553 = 1+256*92`), `SET ErrorFlag_M`, and `SET SafetySwitchToolCheck_M` in the same rung —
  this is the "door opened mid-job" case, distinct from the spindle-start case above, and the
  `SET SafetySwitchToolCheck_M` here immediately prevents the rung from re-firing every scan
  the door stays open (it only fires once per open-door event).
  - Gotcha: the `!(M3_SV || M4_SV)` guard means this rung is specifically for the
    door-open-while-*not*-spinning-and-mid-job case; if the spindle is running
    (`M3_SV`/`M4_SV` true) when the door opens mid-job, this particular rung does not fire —
    that scenario is presumably expected to be caught elsewhere (e.g. a physical door
    interlock that kills spindle power, or the spindle-start rung above catching the next
    M3/M4) since nothing in this stage posts a message for "door open while spindle already
    running mid-job."
- (src:3030) `IF SafetySwitch_M THEN RST SafetySwitchToolCheck_M` — once the door closes again
  (`SafetySwitch_M` true), the tool-check latch is cleared, re-arming the mid-job
  door-open detection for the next time the door opens.
- Both message paths only `SET ErrorFlag_M` (an *error*-severity message per
  `MessageStage`'s dispatch above), not a fault-class bit — a safety-switch trip does not
  itself add to the `SV_STOP` OR-gate documented in main-stage.md's
  [Fault aggregation](main-stage.md#fault-aggregation-src2840-2882) section; whatever machine-level
  interlock actually stops the spindle when the door opens is external to this rung group
  (purpose inferred; not shown in this stage).

## Message pipeline: `FaultMsg_W` / `ErrorMsg_W` / `InfoMsg_W` -> on-screen display

Three severity-tiered message words (`FaultMsg_W IS W51`, `ErrorMsg_W IS W52`,
`InfoMsg_W IS W53` — definitions.md, src:1068-1070) carry a message
constant encoded per definitions.md's `value = msgNumber + 256 * msgFile` rule
(definitions.md#message-constant-encoding). Any rung anywhere in the file (both this file's
comm-fault producers and main-stage.md's spindle/lube/probe/coolant-prompt rungs) can write
one of these words directly — there's no queueing; the newest write since the word was last
cleared wins.

### `MessageStage` (STG90, src:1217, banner src:3032-3034)

Purpose: priority dispatch — fault beats error beats info. `IF FaultMsg_W != 0 THEN SET
ShowFaultStage` (src:3035); `ErrorMsg_W` is only dispatched to `ShowErrorStage`
if `FaultMsg_W == 0` (src:3036); `InfoMsg_W` only dispatched to `ShowInfoStage`
if both higher words are 0 (src:3037). A fault message pending therefore
suppresses error/info display entirely until it clears.

### `ShowFaultStage` (STG91, src:1218, banner src:3039-3041)

- (src:3042-3043): validates the message constant's low byte (`% 256`) is 1 or
  2 — per definitions.md's encoding, msgFile is expected to be small and the low byte
  (`msgNumber`) is expected to be 1 or 2 for a *fault*-class message specifically; anything
  else `JMP BadMsgStage` (below) rather than displaying a malformed constant.
- (src:3044): `MSG FaultMsg_W` — the actual display call to CNC12's message
  system, which looks up the (file, number) pair per `CLAUDE.md`'s convention (message text
  itself lives in CNC12's message files, not this repo).
- (src:3045-3047): a fault message only self-clears once `!EStopOk_M` — i.e.
  the operator must clear the E-stop/reset condition before the fault message and
  `ShowFaultStage` itself reset; on clear it also posts `MSG_CLEARED_MSG_C` as an info message
  and `RST ShowFaultStage`. Gotcha: this is the *only* place `FaultMsg_W` is zeroed — a fault
  message therefore stays latched on screen (and keeps `MessageStage` re-dispatching to
  `ShowFaultStage` every scan, since `FaultMsg_W != 0` is unconditional) until `EStopOk_M`
  recovers, independent of whether the underlying fault condition that set it is still true.

### `ShowErrorStage` (STG92, src:1219, banner src:3049-3051)

- (src:3052-3053): same low-byte 1-or-2 validation, `JMP BadMsgStage` on failure.
- (src:3054): `MSG ErrorMsg_W, SET MsgClear_T` — displays and arms a shared clear timer
  (`MsgClear_T IS T1`, definitions.md src:1173) in the same rung.
- (src:3055-3057): once `MsgClear_T` expires, zero `ErrorMsg_W`, drop the
  timer, and `RST ShowErrorStage` — unlike `ShowFaultStage`, this is a timed auto-clear, not
  gated on any operator action.

### `ShowInfoStage` (STG93, src:1220, banner src:3059-3061)

- (src:3062-3067): structurally identical to `ShowErrorStage` — same
  low-byte validation, same `MSG` + `SET MsgClear_T` display rung, same
  timed auto-clear via the same shared `MsgClear_T`. Gotcha: `ShowErrorStage` and
  `ShowInfoStage` share the single timer `MsgClear_T` — since `MessageStage`'s dispatch
  (src:3035-3037) guarantees at most one of the two is active at a time (an
  error pending suppresses info dispatch), this sharing is safe in practice but would not be
  if that priority ordering were ever relaxed.

### `BadMsgStage` (banner src:3069-3071)

Purpose: fallback target when any of the three Show*Stage validations fail. Unconditionally
zeroes all three message words and posts `BAD_MESSAGE_MSG_C` as an info message
(src:3072-3075), then `RST BadMsgStage` — a malformed message constant is
replaced with a generic "bad message" notice rather than attempting to display garbage.

## Verification

Every `(src:NNNN)` citation above was checked against `Centroid-Acroloc-ALLIN1DC.src` at
commit 41f3fd6 with `sed -n '<line>p'`; the working tree is unchanged since that commit
(`git status` shows no modifications to the `.src` file).
