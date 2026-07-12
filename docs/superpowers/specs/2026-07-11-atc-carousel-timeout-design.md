# ATC Carousel Search Timeout Design

- Date: 2026-07-11
- Status: approved design, pending implementation
- Scope: `Centroid-Acroloc-ALLIN1DC.src` (PLC), plus doc sync
- Backlog item: [docs/backlog.md](../../backlog.md) #1
- Related: [[acroloc-s10]] ATC flow; the spindle-in-changer interlock aborts this shares its exit shape with

## Goal

Bound the carousel tool search so it cannot run forever. Today `ATCStage` starts the
carousel motor and only stops on a position match; if the target tool is never matched, the
motor stays on and the carousel spins indefinitely with no fault. Add a 20-second watchdog
that faults, stops the motor, and relocks the carousel when the search does not complete.

Closes the `;TODO` at `Centroid-Acroloc-ALLIN1DC.src:2926` and puts the already-defined but
unused `ATCSpin_T` (T24) to work.

## Background

`ATCStage` (STG16) runs each scan while set. Simplified current flow:

1. Abort if the spindle is not confirmed stopped (`!ZeroSpeed_I`) -> fault + full cleanup.
2. Abort if Z is not parked at the change position (`!ATC_Z_Zero_Release_I`) -> fault + cleanup.
3. `IF ATCStage && ChangeToTool_W > 0 THEN SET ATCUnlocked_O, SET ATCMotor_O` (start spinning).
4. Track the 5 position switches into `CarouselToolID_W` (base-16-as-decimal, +1/+2/+4/+8/+10).
5. Match: `IF CarouselToolID_W == ChangeToTool_W THEN` stop motor, relock, `RST M6_SV`,
   `RST ATCStage`.

There is **no bound on step 3-5**. Failure modes that spin forever:

- **Jam / motor stall:** the carousel does not move, position switches never change, so
  `CarouselToolID_W` never reaches the target.
- **Broken position switch:** a tool ID never forms correctly, so the target never matches.
- **Invalid / unreachable tool number:** e.g. a requested tool with no pocket; the decoded ID
  never equals the target.

`ATCSpin_T` (T24) was defined for exactly this ("used to detect fault if unable to find
position") but is never armed or read.

## Requirement

If a tool change does not complete within 20 seconds of starting, `ATCStage` must fault with
`CAROUSEL MOVE TIME OUT`, stop the carousel motor, relock the carousel, clear the change
(`M6_SV`, `ChangeToTool_W`), and exit the stage. A normal change (worst case a full
revolution, under 10 s on this machine) must never trip it.

## Design

### Constants (two new; no `plcmsg.txt` change)

Message 63 `CAROUSEL MOVE TIME OUT` already exists in `plcmsg.txt` (message file 2), so only
constants are added, near the other ATC message constants:

```
CAROUSEL_TIMEOUT_MSG_C          IS 16130 ;(2+256*63) CAROUSEL MOVE TIME OUT
ATC_SPIN_TIMEOUT_MS_C           IS 20000 ; Acroloc carousel search timeout (ms)
```

(`2 + 256*63 = 16130`, matching the file-2 encoding used by the existing ATC constants such
as `ATC_Lock_Released_C = 2+256*174`.)

### Arm the watchdog once, at M6 kickoff (MainStage)

No new memory bit is needed. The timer is armed off the `M6_SV` rising edge, gated so it fires
exactly once per change. Add one rung immediately **before** the existing kickoff rung:

```
; Acroloc: arm the carousel search watchdog once, as the change kicks off
IF M6_SV && !ATCStage THEN ATCSpin_T = ATC_SPIN_TIMEOUT_MS_C, SET ATCSpin_T
IF M6_SV THEN ChangeToTool_W = SV_TOOL_NUMBER, SET ATCStage        ; (existing kickoff)
```

Why this arms exactly once: the arm rung runs before the kickoff sets `ATCStage`, so it reads
`ATCStage` from the prior scan.

- First scan of a change: `M6_SV` true, `ATCStage` still false -> arm fires. The next rung
  sets `ATCStage`.
- Every later scan while searching: `ATCStage` is true -> `!ATCStage` is false -> no re-arm,
  so the timer accumulates instead of resetting each scan.
- A new `M6` (after the previous change cleared `ATCStage` and `M6_SV`) re-arms cleanly.

### Timeout fault rung (ATCStage), after the match rung

```
; Acroloc: carousel never found the tool within ATC_SPIN_TIMEOUT_MS_C -> fault, stop, relock
IF ATCStage && ATCSpin_T THEN
  FaultMsg_W = CAROUSEL_TIMEOUT_MSG_C,
  SET ShowFaultStage,
  SET OtherFault_M,
  RST ATCMotor_O,
  RST ATCUnlocked_O,
  RST M6_SV,
  ChangeToTool_W = 0,
  RST ATCSpin_T,
  RST ATCStage
```

`ATCSpin_T` used bare reads true at expiry. Placing this rung **after** the match rung makes a
genuine match at the buzzer win the tie: if a match occurs the same scan the timer expires, the
match rung runs first and `RST ATCSpin_T` + `RST ATCStage`, so this rung's condition is already
false. The exit shape (fault message, stop motor, relock via `RST ATCUnlocked_O`, clear
`M6_SV`/`ChangeToTool_W`, `RST ATCStage`) mirrors the two existing aborts.

### Cleanup on the other three exits

Add `RST ATCSpin_T` to the action list of each existing `ATCStage` exit so the timer is always
clean (elapsed 0, disarmed) before the next change re-arms:

- the match rung (`CarouselToolID_W == ChangeToTool_W`),
- the `!ZeroSpeed_I` abort,
- the `!ATC_Z_Zero_Release_I` abort.

Because the only arm is at kickoff and every exit disarms, `ATCSpin_T` cannot leak state
between changes, and no `IF !ATCStage` reset is needed (stage rungs do not run while the stage
is clear).

## Failure modes covered

| Failure | Detected because |
|---|---|
| Jam / motor stall (no switch motion) | timer expires; count-based schemes would never trip |
| Broken position switch (ID never forms) | timer expires (no match within 20 s) |
| Invalid / unreachable tool number | timer expires (decoded ID never equals target) |

## Interactions

- **Existing aborts** (`!ZeroSpeed_I`, `!ATC_Z_Zero_Release_I`) still take priority — they run
  earlier in the stage and disarm the timer on exit.
- **Spindle-in-changer interlock / feed-hold:** unaffected. That logic gates spindle enable and
  Z motion; the watchdog only bounds the carousel search once the stage is running with the
  spindle confirmed stopped.
- **Recovery:** after a timeout fault the operator clears the fault (cycle-cancel/reset) and
  re-runs the `M6`; the watchdog re-arms on the new `M6_SV` edge.

## Testing (on-machine)

No automated tests; validate in CNC12 after compiling/loading. Watch `ATCMotor_O` (OUT17),
`ATCSpin_T` (T24), and the message line.

1. **No false trips:** run several `M6` changes to near and far tools (worst case ~full
   revolution). Each completes normally in under 10 s; the watchdog never fires.
2. **Unreachable tool -> timeout:** with no tool in the spindle, command a tool number that has
   no pocket / never decodes (e.g. `M6 T13` on a 12-pocket carousel). Expect: the carousel
   spins, and at ~20 s the change **faults with "CAROUSEL MOVE TIME OUT"**, `ATCMotor_O` -> 0,
   the carousel relocks, and `M6_SV`/`ChangeToTool_W` clear.
3. **Recovery:** clear the fault and run a normal `M6` to a valid tool — it completes, proving
   the watchdog re-armed cleanly after the timeout.

## Docs to update (per CLAUDE.md convention)

- Remove the `;TODO` at `Centroid-Acroloc-ALLIN1DC.src:2926`.
- `CLAUDE.md`: the "carousel has no timeout" caution -> now bounded by the 20 s watchdog (note
  the off-by-one-in-decode risk still matters, but no longer means an infinite spin).
- `docs/plc-spec/atc.md`: update the flow and the "Known gaps" section (no-timeout gap closed).
- `docs/plc-spec/definitions.md`: move `ATCSpin_T` out of "Defined but unused"; add the two new
  constants.
- `.claude/skills/acroloc-s10/reference/atc-flow.md` and `SKILL.md`: update the "no timeout"
  gotcha to describe the watchdog.
- `docs/backlog.md`: mark item #1 done.

## Open questions

None.
