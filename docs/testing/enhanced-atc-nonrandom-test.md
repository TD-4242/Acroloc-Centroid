# Enhanced ATC (non-random, P160 = 1) - End-to-End On-Machine Validation

Validates the whole feature on branch `feature/enhanced-atc-nonrandom` (PR #26):
the Tool Library bin map, the PLC position report and putback timing, the bin
range guard, the hand-moved carousel interlock, F2 ATC Reset, the VCP
`TOOL XX  BIN XX` readout, and a real job. Phases are gated: stop at the first
failing step and record what happened. Rollback is at the end.

Spec: `docs/superpowers/specs/2026-09-06-enhanced-atc-nonrandom-design.md`.
Interactive run sheet (saves ticks and notes):
https://claude.ai/code/artifact/1ce7c36a-f16a-4c58-bb9d-1dec04c4d3d8

Things learned on 2026-09-07/08 that this procedure now assumes:
- Bin 0 is a state ("in the spindle"), not a place; the Bin column refuses 0.
  Only a completed M6 or F2 ATC Reset sets it. On this Z-motion changer the
  in-spindle tool is the one parked under the spindle, so putback = parked bin.
- CNC12 has no "empty spindle": `M6T0` and a reset with tool 0 are refused.
- CNC12 skips an M6 for the tool the status window says is loaded; the skip is
  decided by that status tool, not by the library. Recovery after a hand move is
  therefore the **ATC RESET** button (or MPG macro 4), which runs `M20`: a change
  to whichever of the dummy tools 199/200 is not currently loaded.
- `mfunc6.mac` must dwell `G4 P2` after the match and write `G10 P700` only
  after `M95 /8`; both were found the hard way (wrong putback bins).
- ATC Reset is **F2** in the Tool Library (cursor in the Bin column).

## 0. Starting state

- [ ] Parameters (F1 Setup > F3 Config > F3 Parms): record **P6, P160, P161,
      P164**. Expected on this machine now: 1, 1, 12, 1.
- [ ] Control PC, cncm directory: `git pull` on `feature/enhanced-atc-nonrandom`;
      record the commit (must be 98275e0 or later: the boot-message fix and the
      Phase E test program).
- [ ] Compile/reload the `.plc` (expect: no errors). Restart CNC12 (macros, the
      skin and the P700 label reload).
- [ ] After the restart, before anything else: the VCP row-2 bezel reads
      `TOOL 0  BIN 0` (boot latch: nothing verified).

## 1. Phase A - bootstrap and identity loadout

- [ ] Home the machine.
- [ ] Tool Library: every tool that is physically in the carousel gets its own
      bin, **including the tool parked under the spindle**. Tools not in the
      carousel: F1 Clear Bin (dashes). F10 Save. Do not type 0.
- [ ] Cursor in the Bin column, **F2 ATC Reset**: carousel position = the parked
      bin (type it if the default reads 0), tool in spindle = the tool in that
      bin, putback = that bin, **Y**.
- [ ] Status window shows that tool; Tool Library shows it at bin **0**; ALT+K
      reads the parked bin; VCP reads `TOOL <tool>  BIN <bin>`.
- [ ] MDI `M3 S500`: the spindle runs (the reset cleared the boot latch). `M5`.
- [ ] MDI `M6T5`: carousel indexes to bin 5; VCP `TOOL 5  BIN 5`; ALT+K 5;
      status T5; Tool Library: tool 5 at 0, the previous tool back in its own bin.
- [ ] MDI `M6T5` again: nothing happens (same tool is skipped).
- [ ] MDI `M6T12` then `M6T1`: bins 12 and 1; readouts, ALT+K and the Bin column
      all track.

## 2. Phase B - the feature and the soak

- [ ] Tool Library: tool 2 -> dashes. Tool **15** -> bin **2**. F10 Save.
- [ ] MDI `M6T15`: carousel to bin 2; VCP `TOOL 15  BIN 2`; status T15; tool 15
      at bin 0 in the library.
- [ ] MDI `M6T1`: tool 15's Bin returns to **2**.
- [ ] **Soak (putback timing):** ten changes in any order across bins 1-12 and
      tool 15, checking the Bin column after each. Every tool must always show
      its own bin (or 0 while loaded). Record the count of wrong bins.
- [ ] **Unassigned tool (Q1):** MDI `M6T2` (tool 2 has dashes). Record which:
      CNC12 refuses with its own message (text); PLC faults
      `9067 ATC BIN OUT OF RANGE` and the MDI is cancelled; or the carousel moves
      (to which bin).
- [ ] If the PLC faulted: MDI `G4 P1`. Does CNC12 prompt that the last tool change
      did not complete (**Q4**)? Answer Y.
- [ ] Restore: tool 15 -> dashes (or its real bin), tool 2 -> bin 2. F10 Save.

## 3. Phase C - hand-moved carousel interlock and recovery

- [ ] Note the loaded tool (status window), call it L, and its bin.
- [ ] Z at the tool-change position. Press the manual unlock, hand-spin the
      carousel **two bins forward**, release. VCP `TOOL 0  BIN 0`; ALT+K 0. Note
      the bin now under the spindle (n) and the tool in it (tool n).
- [ ] MDI `M3 S500`: refused, message
      `9068 CAROUSEL MOVED BY HAND - ATC RESET OR TOOL CHANGE`, MDI cancelled, no
      E-stop needed.
- [ ] MDI `M6T<L>`: CNC12 skips it (status still L). MDI `M3 S500`: **still
      refused**. Record that both were refused (this is the hole the interlock
      closes).
- [ ] Status message: `175 CAROUSEL MOVED - PRESS ATC RESET` appeared on the
      message line the moment the carousel was moved (not only after a refused
      spindle start).
- [ ] The **ATC RESET button is lit red** while the reset is owed.
- [ ] **Recovery by the ATC RESET button** (needs tools 199+200 sharing a bin,
      zero H/D offsets): press it. Z parks, the carousel searches to the dummy
      bin, the button goes dark, `176 ATC POSITION RE-ESTABLISHED` appears, and
      `M3 S500` runs. Status shows T200.
- [ ] **Second reset in a row** (the 2026-09-09 bug): hand-spin again and press
      ATC RESET again. It must work, changing to **T199** this time, not be
      silently skipped.
- [ ] Same again from **wireless MPG macro button 4**.
- [ ] Recovery by reset instead: cursor in the Bin column, **F2 ATC Reset**:
      position n, tool in spindle = tool n, putback n, **Y**.
- [ ] Status shows tool n; VCP `TOOL n  BIN n`; ALT+K n. MDI `M3 S500` runs. `M5`.
- [ ] **Tool Library, tool L's Bin: its own bin, or 0?** Record it. (Open item
      from 2026-09-08: does the reset restore the previous tool or leave a
      phantom at 0.) If 0, set it to its bin by hand.
- [ ] MDI `M6T<L>`: now searches (status named tool n), lands on L's bin.
- [ ] Repeat the hand-spin (two bins). Recover this time with an M6 to a
      **different** tool: it searches, the latch clears, `M3 S500` runs, and the
      Bin column shows the previously loaded tool back in its own bin.
- [ ] **Boot latch:** power-cycle CNC12. VCP `TOOL 0  BIN 0`. MDI `M3 S500`:
      refused with 9068. MDI `M6T<a different tool>`: searches. `M3 S500` runs.

## 4. Phase D - readout

- [ ] After a change: `TOOL <tool>  BIN <bin>`. After a hand move or boot: both 0.
      After ATC Reset: the declared tool **and** bin.
- [ ] Spacing: nothing overlaps or runs off the bezel. Describe it so the margins
      in `BIN_ELEMENTS` (`tools/vcpgen.py`) can be tuned.

## 5. Phase E - a real job, end to end

- [ ] Load `docs/testing/atc-toolchange-test.cnc` (it is in the cncm checkout
      after the pull). Its header lists the preconditions: homed, ATC RESET
      dark, spindle in AUTO, tools 1-12 in bins 1-12, tool 15 given a bin.
      Every Z move is G53 and never below Z-4.000; there is no XY motion.
- [ ] Run it from the start. Every change lands on its own bin and the VCP
      tracks it; the repeated `T5 M6` is skipped with no carousel motion and
      the spindle still starts; the job ends with tool 1 loaded and every
      other tool back in its own bin.
- [ ] Run it again without touching anything: same result. Its first change
      is to tool 1, already loaded, so it is skipped and the spindle must still
      start, since the position is verified.

## 6. Rollback (if the machine is needed)

- [ ] Quick: P160 = 0, P6 back to its recorded value, same `.plc`: `M6T1..T12`
      keep working (tool number = bin at the identity loadout); tools above 12
      are unavailable.
- [ ] Full: control PC `git checkout main`, reload the `.plc`, set P701-P712,
      P160 = 0. **Only while this branch is unmerged** — `main` still carries the
      P701-P712 map today. Once this merges, the equivalent is checking out the
      last commit before the merge (or reverting it); the P701 map is not coming
      back to `main`.

## Report back

Record: (Q1) what the unassigned-tool M6 did; (Q4) whether the incomplete-change
prompt appeared; the soak's wrong-bin count; what ATC Reset did to the
previously loaded tool's bin; the readout spacing; and whether the real job ran
clean twice.
