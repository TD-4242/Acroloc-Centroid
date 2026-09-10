# Enhanced ATC, non-random mode (P160 = 1): tool->bin map in the Tool Library - Design

Date: 2026-09-06
Status: implemented on branch; on-machine: Phases A and B pass (bootstrap, arbitrary tool->bin, putback round-trip over 10 changes, 2026-09-08); Phase C (hand-move interlock) and Q1/Q3/Q4 pending
Branch: `feature/enhanced-atc-nonrandom` (worktree `.worktrees/enhanced-atc-nonrandom`, from `main`)
Supersedes: `2026-07-22-tool-bin-mapping-design.md` (the P701-P712 PLC map) once verified on-machine

## Why this exists (correction of the July finding)

The July 2026 tool-bin-mapping spec ruled out CNC12's non-random enhanced ATC
mode with the line "Non-random (P160=1) forces tool == bin" and shipped a PLC-side
map in machine parameters P701-P712 instead. Re-checking the record on 2026-09-06:

- That line entered the spec in commit `190f737` as an inference from the example
  configs in `docs/official` ("tool number IS the pocket"). The only on-machine
  trials recorded anywhere were at **P160 = 2 (random)**: M6 was silent until the
  PLC reported `SV_PLC_CAROUSEL_POSITION` (handshake added in `6dda176`), and then
  `M6T5` rewrote tool 1's bin to 5, which is random mode's documented behaviour.
  P160 = 1 was never set on the machine.
- Centroid's own documentation says the opposite of the inference. Operator manual
  15.4.118 (Parameter 160, p.355): "An M107 command sends the bin number for the
  specified tool number, not the tool number itself" and "The tool library allows
  editing of the bin fields to specify which carousel bin number the tools are
  stored in." The ATC3 umbrella operating instructions (a P160 = 1 product): "Any of
  the 200 tools can be specified as belonging to one of the carousel bins ... More
  than one tool can be specified as belonging in the same bin."
- The Bin column is editable at any P160 != 0 (operator manual, Tool Library p.64:
  "If enhanced ATC features are not on, the cursor cannot be moved into the bin
  column"), not only at P160 = 2 as the first draft said.

So non-random mode is the vendor-native way to keep this machine's **fixed,
arbitrary** tool->bin map in Tool Setup instead of in extra parameters. This spec
is a try-it-and-see: the design is complete, but several behaviours can only be
confirmed on the machine (see "Open questions").

## Goal

The operator assigns tools to carousel bins in the CNC12 Tool Library
(F1 Setup > F2 Tool > F2 Tool Lib, Bin column), including tools numbered above
12. `M6T##` indexes the carousel to that tool's bin and the tool snaps in as Z
retracts through the ring, exactly as today. Machine parameters P701-P712 are no
longer used.

## Non-goals

- Random-mode pre-fetch (`Tnn M107` while machining). This carousel cannot move
  with a tool engaged.
- Intercon integration (P162 / M17 spindle orient). Not used on this machine.
- A dual-mode PLC that reads P160 and keeps the P701 map as a fallback. Rollback
  is P160 = 0 with the same build (see "Rollback").
- Any VCP change beyond the `TOOL XX  BIN XX` readout (section 10) and the
  ATC RESET button (section 7b).

## Vendor behaviour this design relies on

From the CNC12 Mill Operator Manual (`docs/official/centroid-cnc12-mill-operator-manual.pdf`,
15.4.118-15.4.122 and Tool Library p.64), the CNC12 PLC Programming Manual
(`docs/official/centroid_plc_programming_manual.pdf`, system-variable tables), and
the ATC3 Umbrella Operating Instructions
(https://www.centroidcnc.com/downloads/Umbrella_ATC3_Operating_Instructions.pdf):

- **P160 = 1** = non-random (carousel) enhanced ATC. **P161** = number of bins,
  "sent to the PLC subsystem on power up" (reboot after changing it). **P6 = 1**
  = ATC installed; with P6 and P160 both non-zero the on-screen tool (#4203)
  updates when M6 finishes. **P164 = 1** adds F2 ATC Reset to the tool library
  menu.
- **M107 sends the bin** of the requested tool into `SV_TOOL_NUMBER`. "In the case
  of enhanced ATC operation this is actually a request for a carousel bin location."
- **End of M6 bookkeeping (non-random):** the previous tool's bin field is restored
  from its putback field; the new tool in the spindle gets bin = 0 and putback =
  the current carousel position as reported by the PLC. The M6 start sets an ATC
  error flag in the job file; a normal M6 end clears it; if it stays set, the next
  job or MDI start prompts the operator to clear it with Y.
- **A tool change is not performed if the requested tool is already in the
  spindle.**
- **Position report:** "The current ATC carousel position is constantly monitored"
  from the PLC's `SV_PLC_CAROUSEL_POSITION` and saved to `cncm.job` on change. At
  startup and on an enhanced-ATC reset CNC12 sends `SV_ATC_CAROUSEL_POSITION` and
  `SV_ATC_TOOL_IN_SPINDLE` to the PLC. "It is critical that the carousel not be
  allowed to turn unless CNC software is running."
- **ATC Reset (F2, P164 = 1):** prompts for carousel position (default = the PLC's
  reported value), tool in spindle, and that tool's putback bin; then runs M18
  ("used by the ATC Reset feature in CNC software to set the carousel position and
  putback bin"). The manual says the feature "only works with ATC3 PLC programs",
  which this design reads as "the PLC must handle M18".
- Tool Library Bin column: 1..P161 = assigned bin, 0 = in the spindle, dashes (-1)
  = unassigned. Several tools may share a bin.

## How this maps onto the Acroloc's Z-motion changer

At Z0 the spindle is physically empty and the tool sits in the bin under the
spindle; Z descending picks it up, Z rising to Z0 puts it back in the **same**
bin, because the carousel cannot move while Z is in the ring
(`ATC_Z_ClearedToolChanger_I` interlock). "Tool in the spindle" in CNC12's model
therefore means "the tool in the bin under the spindle", and non-random putback
(each tool returns to its own bin) is exactly this machine's mechanics. No
put-back move logic is needed, unlike the umbrella example's two-move dance.

**Bin 0 is a state, not a place.** CNC12 marks the in-spindle tool as bin 0 and
remembers its origin in the putback field. On this machine the in-spindle tool is
the one in the bin parked under the spindle, so its putback is always the parked
bin, which is what the PLC reports. The Bin column will not accept 0 by hand:
the in-spindle state is set only by a completed M6 or by F2 ATC Reset. That makes
the first-time bootstrap a required step: assign every tool its own bin (the
parked tool included), then declare the parked tool as in-spindle via ATC Reset
(position, tool, putback all = the parked bin) or, failing that, by running one
M6 to it so CNC12 records the putback from the position report. Without a
recorded putback, the next change would restore that tool's bin from an unset
field. (Found on-machine 2026-09-07 at Phase A; the earlier draft of the test
procedure wrongly said to type 0.)

**The hand-moved carousel is the one real mismatch, and it is enforced, not
documented.** At Z0 the carousel is free to be turned by hand to add, swap or
remove tools. CNC12 cannot see that, still believes its old tool is in the
spindle, and will even skip an M6 for that tool, so a program could drop Z onto
whatever bin was left under the spindle with the wrong length offset. Owner's rule
(2026-09-08): CNC12 only knows a bin after it has put the tool there; after a hand
move, or a boot, assume the tool was put away and nothing is in the spindle. The
carousel parks in the all-switches-off gap, so the parked bin cannot be read at
rest, but any move is detectable (a switch asserting while the motor is off). The
PLC therefore latches `CarouselMovedByHand_M` (MEM454) on that, and at power-up,
reports position 0, holds spindle enable off, and cancels any program or MDI that
tries to start the spindle with `9068 CAROUSEL MOVED BY HAND - ATC RESET OR TOOL
CHANGE` (via `ErrorFlag_M`, so no E-stop is needed). Only an `ATCStage` match
(motor-driven absolute search) or M18 (ATC Reset) clears it. See Design section 7a.

## Design

### 1. Machine parameters (control PC)

| Parameter | Value | Why |
|---|---|---|
| P6 | 1 | ATC installed; on-screen tool updates after M6 (ATC3 doc, operator manual FAQ 16) |
| P160 | 1 | non-random enhanced ATC |
| P161 | 12 | bins; also the PLC's range guard limit; reboot after setting |
| P164 | 1 | F2 ATC Reset in the tool library |
| P162 | 0 (unchanged) | no Intercon M17 |
| P701-P712 | unused | labels revert to stock (see 6) |

The test plan records the machine's current P6 before changing it.

### 2. PLC definitions (`Centroid-Acroloc-ALLIN1DC.src`, all tagged `; Acroloc`)

Removed:
- `ToolInBin1_W .. ToolInBin12_W` (W78-W89) and their `LoadParametersStage` reads.

Added:
- `ReportedToolBin_W IS W78` - the settled carousel bin reported to CNC12.
- `MaxToolBins_W IS W79` - P161, read every scan in `LoadParametersStage` like the
  other cached parameters.
- `M18_SV IS SV_M94_M95_18` - ATC Reset request (bit 18 is free).
- `ATC_BIN_RANGE_MSG_C IS 17154 ; (2+256*67)` - "ATC BIN OUT OF RANGE" fault.
  Slot 67 is the first free fault slot in `plcmsg.txt` (60-66 and 70-73 are
  taken) and is bound to nothing in the source.

Kept: `CurrentToolBin_W` (W71), `TargetToolBin_W` (W72), `TargetToolBinDisp_W`
(W8), `InstBinID_W` (W75), `InBinDecode_M`, `ToolSelected_M`, `ATCSpin_T`.

### 3. Boot seed (`InitialStage`)

`CurrentToolBin_W = SV_ATC_CAROUSEL_POSITION` alongside the other power-up
initialisation, as the umbrella example does (umbrella src:1198). CNC12 persists
the last reported position in `cncm.job` and hands it back at startup. A stale
seed (carousel hand-spun with power off) is corrected by the next M6's
absolute-switch search, and by ATC Reset for CNC12's own bookkeeping.

### 4. M6 kickoff (`MainStage`)

Replaces the P701 translation block. `SV_TOOL_NUMBER` is now the **bin**.

```
; Acroloc: once per change - arm the watchdog, clear the stale bin (unchanged)
IF M6_SV && !ATCStage THEN ATCSpin_T = ATC_SPIN_TIMEOUT_MS_C, SET ATCSpin_T, CurrentToolBin_W = 0

; Acroloc -- enhanced ATC (P160=1): CNC12 sends the BIN for the requested tool.
; Guard it: anything outside 1..P161 (an unassigned tool, a bad library, P161
; unset) faults here and never starts the carousel.
IF M6_SV && !ATCStage && (SV_TOOL_NUMBER < 1 || SV_TOOL_NUMBER > MaxToolBins_W) THEN
  FaultMsg_W = ATC_BIN_RANGE_MSG_C,
  SET ShowFaultStage,
  SET OtherFault_M,
  RST M6_SV,
  TargetToolBinDisp_W = SV_TOOL_NUMBER
IF M6_SV && !ATCStage THEN
  TargetToolBin_W = SV_TOOL_NUMBER,
  TargetToolBinDisp_W = SV_TOOL_NUMBER,
  SET ATCStage
```

The guard rung runs before the kickoff rung and resets `M6_SV`, so the kickoff
rung does not fire on a bad bin. The "99 = unreachable bin" convention is gone;
the fault is immediate instead of a 20 s timeout. `TargetToolBinDisp_W` still
shows the operator what was asked for. The `G4 P1` dwell after `M94 /8` in
`mfunc6.mac` gives the 9xxx fault time to cancel the job before the macro could
otherwise run on to `M95 /8` and let CNC12 record the change as complete; this
is the same mechanism the existing spindle-not-stopped fault relies on.

### 5. Position report (`MainStage`, after the kickoff block, outside `ATCStage`)

```
; Acroloc -- enhanced ATC handshake: report the SETTLED carousel bin to CNC12.
; Latched only while no change is running, so mid-spin partial sums never reach
; CNC12. CNC12 records this value as the new tool's putback bin at the end of M6,
; so it must be right the moment ATCStage clears -- and it is: the match rung
; leaves CurrentToolBin_W = the matched bin, and every abort path zeroes it.
IF !ATCStage THEN ReportedToolBin_W = CurrentToolBin_W
IF True_M THEN SV_PLC_CAROUSEL_POSITION = ReportedToolBin_W
```

0 is reported honestly whenever the bin is unknown (after a manual unlock, after
a fault, before the first change at a stale seed). CNC12 saves the change to
`cncm.job`; that is expected.

Timing: `mfunc6.mac` waits on `M100 /93016` for `ATCStage` to clear, then
`M95 /8`, then ends. The report refreshes on the scan after `ATCStage` clears,
well before the macro ends and CNC12 does its end-of-M6 bookkeeping.

### 6. Abort paths zero the known bin (`ATCStage`)

The three fault rungs (spindle not stopped, spindle not parked, carousel timeout)
each gain `CurrentToolBin_W = 0`. A change aborted mid-decode would otherwise
leave a partial peak (for example 4 from a lone Pos3) that the report would hand
to CNC12 as a real position. The match rung is unchanged.

A 9xxx fault message sets `OtherFault_M`, which cancels the running job or MDI,
so `mfunc6.mac` never reaches `M95 /8` and CNC12's ATC error flag stays set. The
next job or MDI start then prompts the operator. This is the vendor's documented
recovery path and is verified on-machine (Phase A step 5).

### 7. ATC Reset (`MainStage`)

```
; Acroloc -- enhanced ATC reset (F2 in the tool library, P164=1) runs M18 after
; CNC12 has sent the operator-entered carousel position. Re-seed from it.
IF M18_SV && !ATCStage THEN CurrentToolBin_W = SV_ATC_CAROUSEL_POSITION
```

New `mfunc18.mac`, modelled on the umbrella example: graph/search guard,
`M94 /18`, `G4 P1`, `M95 /18`, `N1000`. The umbrella's M18 forces position 1
because its F6 Init assumes tool 1 in bin 1; this machine re-derives position by
absolute switches, so the seed from CNC12 is enough.

### 7a. Hand-moved carousel interlock (`MainStage`, after the changer interlock)

```plc
IF (ATC_Pos1_I || ATC_Pos2_I || ATC_Pos3_I || ATC_Pos4_I || ATC_Pos5_I) && !ATCMotor_O THEN
  SET CarouselMovedByHand_M, CurrentToolBin_W = 0, TargetToolBinDisp_W = 0
IF CarouselMovedByHand_M THEN RST SpindleEnableOut_O
IF CarouselMovedByHand_M && (SV_PROGRAM_RUNNING || SV_MDI_MODE) &&
   (SpinStart_M || M3_SV || M4_SV) && !ErrorFlag_M THEN
  FaultMsg_W = ATC_HAND_MOVED_MSG_C, SET ShowFaultStage, SET ErrorFlag_M
```

Plus `SET CarouselMovedByHand_M` in `InitialStage`, `RST CarouselMovedByHand_M` in
the `ATCStage` match rung and in the M18 rung, and `plcmsg.txt` slot 68. Design
choices: detection is on the switches, not the unlock button, so it catches a
carousel moved by any means; the stop is a job cancel, not a feed hold, because
resuming after a skipped M6 would cut with the wrong tool; `ErrorFlag_M` is used
rather than `OtherFault_M` so recovery is ATC Reset or an M6, not an E-stop
cycle. Operating cost: after every boot, one ATC Reset or one M6 to a different
tool before the spindle will run.

### 7b. Hand-move recovery: the ATC RESET button (added 2026-09-09)

The recovery is one button. CNC12 decides whether to skip an M6 from the tool
its status window names, which is read-only to the PLC and to macros, so after a
hand move a change back to that tool is silently ignored. **Tools 199 and 200**
are dummies the operator maps to the **same** bin in the Tool Library (H and D
offsets 0; sharing a bin is explicitly allowed by CNC12 and keeps the carousel
parking in one place). `M20` (`mfunc20.mac`) reads `#4203`, the tool CNC12
believes is loaded, and changes to whichever dummy is *not* it. That change
always runs: the carousel search proves the position, the interlock clears, and
CNC12's own end-of-M6 bookkeeping puts the previously loaded tool back in its
bin. Follow it with a real `T## M6`.

Two dummies, not one: after a reset the loaded tool **is** the dummy, so reusing
it would be skipped and a second reset would silently do nothing (found
on-machine 2026-09-09). Alternating makes every reset work. `M20` is bound in
two places, each a one-liner so the logic has a single home:
- the **ATC RESET** button on the retro VCP (row 11, column 6, under TOOL CHECK);
- **wireless MPG macro button 4**, via `system/plcmacro4.mac`
  (`MpgMacro4_M` -> `SV_SYS_MACRO = 4` was already in the stock PLC).

Because the carousel moves, both only fire from the main CNC12 menu. The
`G53 Z0` park at the head of `mfunc6.mac` costs nothing here: the PLC only
grants the manual unlock at Z zero (`ATCManualUnlock_I && ATC_Z_Zero_Release_I`),
so after a hand move Z is already there, and machine zero is the safe direction
for Z in any case. While CNC12 believes a dummy is loaded, whatever sits in that
bin is physically under the spindle; the next real tool change corrects it,
which is why the offsets are zero.

**Status messages**, so the operator is told when it happens rather than when a
spindle start is refused: `175 CAROUSEL MOVED - PRESS ATC RESET` is posted once
when the position becomes unverified (a hand move, or power-up) and
`176 ATC POSITION RE-ESTABLISHED` once when a search or an ATC Reset proves it
again. Both are async (type 2) so neither halts a job, and the alternating
numbers satisfy CNC12's refusal to re-send the same number twice in a row.
`HandMoveMsgShown_M` (MEM455) latches which of the two is owed.

They post on **`FaultMsg_W`**, not `InfoMsg_W`. Found on-machine 2026-09-09: the
carousel lock echo (`IF ATCManualUnlock_I THEN FaultMsg_W = ...` /
`IF !ATCManualUnlock_I THEN FaultMsg_W = ...`) has one rung true on every scan,
so `FaultMsg_W` is never 0 and `MessageStage` never routes to the info or error
channels at all. These rungs therefore sit after the echo, and hold it off for
3 s (`HandMoveMsgHold_M` MEM456, `HandMoveMsgHold_T` T27) so the message can be
read. The **persistent** cue is the ATC RESET button itself, which swaps
graphics on MEM454 (`<plc_memory>`) and lights red while a reset is owed; the
message is only the transient announcement.

### 8. Macros

- `mfunc6.mac`: two additions, both order-critical. **`G4 P2` between
  `M100 /93016` and `M95 /8`:** CNC12 records the new tool's putback from the
  carousel position it *last observed* on its own monitoring schedule, not from
  a read at the instant the M6 ends. Without the dwell this macro ended within
  about 100 ms of the match and the putback intermittently kept the previous
  tool's bin (on-machine 2026-09-08: some tools right, some wrong over a run of
  changes; 10 of 10 correct with the dwell). The umbrella example never hits
  this because its carousel settles seconds before its macro ends. **`G10 P700
  R[#4120]` after `M95 /8`:** hands the PLC the requested tool number for the VCP
  `TOOL` readout; it must not run mid-M6 (section 10). The graph/search guard
  and `N1000` pattern stay.
- `mfunc18.mac`: new, as above.
- `mfunc20.mac`: new. `M20` = the ATC reset action (7b); the one source of truth,
  called by both the VCP button and the MPG macro.
- `system/plcmacro4.mac`: new. Wireless MPG macro button 4 -> `M20`.
  The repo root is the live `cncm` directory, so `.gitignore` un-ignores
  `/system/plcmacro*.mac` specifically.

### 9. Control-PC files (tracked in this repo)

- `plcmsg.txt`: add `67  9067 ATC BIN OUT OF RANGE` after the slot-66 line.
- `language.msg`: P701-P712 `@P70n_LABEL` / `_L` lines return to the stock
  "Reserved for Enduser/Integrator custom PLC and Macro use" text; P700 gets the
  label "ATC: tool number of the last M6 (mfunc6 G10)".
- `docs/control-pc-customizations.md`: drop the P701-P712 label set; add the
  P6/P160/P161/P164 settings and the Tool Library Bin column as the map's home.

### 10. VCP: `TOOL XX  BIN XX` readout (added 2026-09-08)

The row-2 bezel now packs two readouts like the spindle bezel does. `BIN` is
`TargetToolBinDisp_W` (plc_word 8), the bin CNC12 asked for. `TOOL` is a new
word `ToolInSpindleDisp_W` (W80, plc_word 80): the **verified** tool under the
spindle. The PLC gets the tool number the only way CNC12 offers at P160 = 1:
`mfunc6.mac` writes `G10 P700 R[#4120]` **after `M95 /8`** (P700 is the
parameter Centroid reserves for macro-to-PLC use; labelled in `language.msg`),
and a `MainStage` rung tracks `SV_MACHINE_PARAMETER_700` into W80 while
`ToolSelected_M` says a change has completed since the last kickoff, hand move
or ATC Reset. **The G10 must not run mid-M6:** placed right after M107 it made
CNC12 commit the tool library early and record the new tool's putback from the
carousel position before the move (on-machine 2026-09-08, tool 15 ended up in
the previous tool's bin). The M18 rung sets W80 from `SV_ATC_TOOL_IN_SPINDLE` after an
ATC Reset, and the hand-move interlock forces it to 0 whenever nothing is
verified, so `TOOL 0` always means "the spindle will refuse to start".
Margins in `BIN_ELEMENTS` (`tools/vcpgen.py`) are a first guess; tune on-machine.

## Operator workflow

- **Assign a tool to a bin:** Tool Library, Bin column, type the bin (1-12),
  F10 Save. A tool not in the carousel gets dashes (F1 Clear Bin). Several tools
  may share a bin when the physical tool is swapped by hand between jobs.
- **Tool change:** `M6T##` as before. CNC12 skips it if that tool is already in
  the spindle.
- **After a hand-spin at Z clear (manual unlock):** Tool Library > F2 ATC Reset.
  Enter the carousel position now under the spindle, the tool number that is in
  that bin, and that same bin as its putback. This replaces today's "re-set the
  current tool in CNC12" note.
- **After an interrupted M6** (E-stop, Escape, a fault): CNC12 prompts at the next
  start; answer Y, then check the Bin column matches the carousel, using ATC
  Reset if not.

## Behaviour changes to accept

- **No same-tool safety spin.** The July design re-indexed even for the same
  tool, guarding against an undeclared hand swap. CNC12 now skips that M6. The
  guard moves into the PLC: the hand-moved carousel interlock (7a) refuses the
  spindle until the position is re-established, so the skipped M6 fails safe.
- **One re-index or ATC Reset after every boot** before the spindle will start
  (the boot latch).
- **Unassigned tool faults immediately** ("ATC BIN OUT OF RANGE") instead of
  spinning for 20 s to `CAROUSEL MOVE TIME OUT`. The 20 s watchdog stays for a
  bin that exists but is never matched.
- **CNC12 writes `cncm.job` whenever the reported bin changes.** Harmless; noted
  so nobody chases the disk activity.

## Verification (on-machine, owner-run) and rollback

Full procedure in `docs/testing/enhanced-atc-nonrandom-test.md` (replaces
`tool-bin-mapping-test.md`). Phases, each gated on the previous:

**Phase A - handshake and identity loadout.** Load the `.plc`, `mfunc6.mac`,
`mfunc18.mac`, `plcmsg.txt`, `language.msg`; set P6/P160/P161/P164; reboot.
Bin column now editable; set tools 1-12 to bins 1-12. `M6T5` indexes to bin 5,
ALT+K shows ATC BIN 5, `TOOL BIN` reads 5, tool display shows T5 after the
change, tool 5's Bin field reads 0 and tool 1's (the previous tool) is back to 1.
`M6T5` again does nothing (skipped). Interrupt a change with Escape and confirm
the error prompt at the next MDI, answer Y.

**Phase B - the feature.** Tool 31 assigned bin 2 (tool 2 cleared to dashes):
`M6T31` indexes to bin 2. Then `M6T1` returns tool 31's Bin to 2, not to 0 or
some other bin. A tool with dashes: record what M107 sends and that the PLC
faults "ATC BIN OUT OF RANGE" (or that CNC12 refuses the M6 itself).

**Phase C - reset.** Manual unlock, hand-spin two bins, relock: `TOOL BIN`
reads 0, ALT+K reads 0. F2 ATC Reset with the true position: ALT+K matches, the
Bin column matches the carousel, and the next `M6T<n>` lands correctly.

The "ATC BIN OUT OF RANGE" fault in Phase B doubles as the check that a PLC
fault mid-M6 cancels the job and leaves CNC12's error flag set (open question
4): the next MDI must prompt. The 20 s timeout path is unchanged code apart from
zeroing the bin, and is not re-tested; forcing it would need P161 raised, which
makes CNC12 re-initialise the tool library.

**Rollback.** Set P160 = 0 (and P6 back to its recorded value) with the same
build loaded. `SV_TOOL_NUMBER` is then the tool number, which equals the bin for
tools 1-12 at the identity loadout, so the machine keeps working while the
question is investigated. Full rollback is `git revert` and a reload of the
previous `.plc`.

## Open questions (settled on-machine, then recorded in the test plan and docs)

1. What M107 sends for a tool whose Bin is dashes: -1, 0, the tool number, or a
   CNC12-side error. The guard covers -1, 0 and >12; a tool number <= 12 would
   slip through as a bin. Phase B decides whether extra handling is needed.
2. **Answered on-machine 2026-09-08: F2 ATC Reset works with this PLC.** With
   the carousel parked at bin 7, entering position 7, tool 7, putback 7 was
   accepted; the Tool Library then showed tool 7 at bin 0 and the changer ran.
   The M6 bootstrap in the test procedure stays only as a fallback.
   Also verified the same day: tool 15 assigned to bin 2 in the Tool Library,
   `M6T15` indexed the carousel to bin 2 and the library showed tool 15 at bin 0;
   after the next change tool 15's Bin returned to 2, so the putback recorded from
   the PLC's position report round-trips correctly.
3. Whether a reported 0 upsets CNC12 (the umbrella never reports 0). If it does,
   report the last known good bin and leave 0 to the VCP readout only.
   **Related, answered 2026-09-08:** CNC12 samples the reported position
   asynchronously; the putback is only right if the new position has been
   visible for a while before the M6 ends. Hence the `G4 P2` in `mfunc6.mac`.
4. Whether the ATC error flag is actually left set when `OtherFault_M` cancels
   the job mid-M6.

## Documentation to update (same change, current-state only)

- `CLAUDE.md`: ATC flow step 2 and the custom I/O word list (W78-W89 become W78,
  W79); the "CNC12's own enhanced-ATC modes are deliberately unused" sentence.
- `README.md`: the P701 mention.
- `docs/plc-spec/`: `atc.md` (kickoff, handshake, reset, faults), `main-stage.md`,
  `boot.md` (seed), `definitions.md`, `parameters.md` (P6/P160/P161/P164, drop
  P701-712), `faults-and-messages.md` (new message). Pinned `src:` line
  references stay as they are; new lines get none.
- `.claude/skills/acroloc-s10/`: `SKILL.md`, `reference/atc.md`,
  `reference/atc-flow.md`, `reference/macros.md` (mfunc18).
- `.claude/skills/centroid-plc-programming/reference/system-variables.md`: mark
  the `SV_ATC_*` / `SV_PLC_CAROUSEL_POSITION` rows as used by this program.
- `docs/control-pc-customizations.md`, `plcmsg.txt`, `language.msg` as in 9.
- `docs/testing/enhanced-atc-nonrandom-test.md` new; `tool-bin-mapping-test.md`
  deleted.
- `docs/superpowers/specs/2026-07-22-tool-bin-mapping-design.md`: revision-history
  note that the non-random claim was an inference and that this spec supersedes
  it (historical specs may be annotated).
- The PR #22 artifact (Tool-to-Bin Mapping page): replace "The road not taken"
  with the corrected finding and point at this design.
