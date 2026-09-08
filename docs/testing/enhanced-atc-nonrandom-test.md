# Enhanced ATC (non-random, P160 = 1) - On-Machine Test Procedure

Covers the Tool Library bin map, the PLC position report, the bin range guard,
the VCP `TOOL BIN` readout, and F2 ATC Reset. Phases are gated: stop at the first
failing step and record what happened. Rollback is at the end.

Spec: `docs/superpowers/specs/2026-09-06-enhanced-atc-nonrandom-design.md`.

## 0. Record the starting state

- [ ] Machine parameters screen (F1 Setup > F3 Config > F3 Parms): write down the
      current values of **P6, P160, P161, P164**. (Expected before this change:
      P160 = 0.)
- [ ] Tool Library (F1 Setup > F2 Tool > F2 Tool Lib): note that the Bin column
      shows "Bin fields are locked".

## 1. Deploy (control PC)

The CNC12 `cncm` directory on the control PC is a git checkout of this repo, so
deploying is a branch checkout, not a file copy.

- [ ] On the control PC, in the CNC12 `cncm` directory: `git fetch`, then
      `git checkout feature/enhanced-atc-nonrandom` (`git pull` if it was already
      checked out). That brings the `.src`, `mfunc6.mac`, `mfunc18.mac`,
      `plcmsg.txt` and `language.msg` in one step. Note the commit.
- [ ] Compile/reload the `.plc` in CNC12 (expect: compiles, no errors).
- [ ] Set **P6 = 1, P160 = 1, P161 = 12, P164 = 1**. CNC12 warns that enhanced ATC
      needs a matching PLC program: accept.
- [ ] **Reboot CNC12** (P161 is sent to the PLC at power-up; macros and messages
      reload).

## 2. Phase A - handshake and identity loadout

- [ ] Home the machine.
- [ ] Tool Library: the Bin column is now editable and F1 Clear Bin / F2 Clear All
      appear. Set tools 1-12 to bins 1-12, **including the tool that is parked
      under the spindle** (its own bin number, e.g. tool 7 = bin 7). F10 Save.
      Do not try to type 0: CNC12 owns the in-spindle (bin 0) state and only a
      tool change or ATC Reset can set it.
- [ ] Declare the in-spindle tool so CNC12 records its putback. On this
      Z-motion changer "tool 7 in the spindle" and "carousel parked at bin 7"
      are the same physical state, so putback = the parked bin. Try
      **F2 ATC Reset** first: carousel position = the parked bin (type it if the
      default reads 0), tool in spindle = the tool in that bin, putback = that
      bin, confirm Y. Expect the Tool Library to show that tool at bin 0 and
      ALT+K to read the parked bin. (Open question 2 in the spec.)
- [ ] If ATC Reset refuses, record its exact text, then bootstrap with a change:
      if the status window already shows the parked tool (e.g. T7), MDI
      `M6T1` first, restore tool 7's Bin to 7 by hand if CNC12 scrambled it,
      then MDI `M6T7`; the carousel makes one full revolution back to bin 7 and
      CNC12 records tool 7 as in-spindle with putback 7. If the status window
      shows no tool, `M6T7` alone does it.
- [ ] **ALT+K** shows `ATC BIN n` where n is the bin under the spindle.
- [ ] MDI `M6T5` -> carousel indexes to **bin 5**, tool changes normally.
      `TOOL BIN` reads **5**; ALT+K reads 5; the status window shows **T5** after
      the change.
- [ ] Tool Library: tool 5's Bin now reads **0** (in spindle); the previous
      tool's Bin is back to its own number.
- [ ] MDI `M6T5` again -> **nothing happens** (CNC12 skips a change to the tool
      already in the spindle).
- [ ] MDI `M6T12` then `M6T1` -> bins 12 and 1; readout and ALT+K track; Bin
      column tracks (0 for the in-spindle tool, own bin for the rest).
- [ ] Interrupt: MDI `M6T7`, press **Escape** during the carousel move. Then MDI
      anything (e.g. `G4 P1`): CNC12 must prompt that the last tool change did not
      complete; answer **Y**. Check the Bin column and fix it by hand or with F6 ATC
      Reset (section 4) so it matches the carousel.

## 3. Phase B - the feature: arbitrary tool -> bin, and an unassigned tool

- [ ] Tool Library: tool 2 -> F1 Clear Bin (dashes). Tool **31** -> Bin **2**.
      F10 Save.
- [ ] MDI `M6T31` -> carousel indexes to **bin 2**; `TOOL BIN` reads 2; status
      shows T31; tool 31's Bin reads 0.
- [ ] MDI `M6T1` -> tool 31's Bin returns to **2** (not 0, not another bin).
- [ ] Unassigned tool: MDI `M6T2` (tool 2 has dashes). Record exactly what
      happens - one of:
      - CNC12 refuses the M6 with its own message (record the text), or
      - the PLC faults **`9067 ATC BIN OUT OF RANGE`** immediately, the job
        cancels, and the next MDI prompts about the incomplete change (answer Y), or
      - the carousel moves to some bin (record which; this means M107 sent a
        number in 1..12 for an unassigned tool and the guard needs a follow-up).
- [ ] Restore: tool 31 -> dashes, tool 2 -> Bin 2, F10 Save.

## 4. Phase C - hand-moved carousel interlock and F2 ATC Reset

- [ ] **Boot latch:** after the reboot in section 1 (or any power cycle), MDI
      `M3 S500` before any tool change or ATC Reset -> the spindle must NOT
      start; message `9068 CAROUSEL MOVED BY HAND - ATC RESET OR TOOL CHANGE`
      and the MDI is cancelled (no E-stop needed). Then an M6 to a different
      tool, or ATC Reset, and `M3 S500` runs.
- [ ] Z at the tool-change position (clear). Press the **manual unlock** button
      (`ATCManualUnlock_I`, INP24) and hand-spin the carousel **two bins
      forward**, release the button (relock). `TOOL BIN` drops to **0**; ALT+K
      reads 0. Note the bin now under the spindle (n) and the tool in it.
- [ ] MDI `M3 S500` -> refused with 9068 and cancelled. MDI `M6T<the tool CNC12
      still shows as loaded>` -> CNC12 skips it; `M3 S500` is still refused.
      This is the hole the interlock closes: record that both were refused.
- [ ] Tool Library > **F2 ATC Reset**: carousel position = n (the default offered
      will be 0; type n), tool in spindle = the tool in bin n, putback = n. Confirm
      with Y. Expect the message `ATC INITIALIZED` or similar; if CNC12 refuses,
      record the text (open question 2 in the spec) and instead edit the Bin
      column by hand.
- [ ] ALT+K now reads n. The Bin column shows that tool at 0 and the previously
      "in spindle" tool back in its own bin.
- [ ] MDI `M6T<m>` for a tool in another bin -> lands on the right bin, readout
      correct, and `M3 S500` now runs (latch cleared by the match).
- [ ] Repeat the hand-spin, then recover with an M6 to a different tool instead
      of ATC Reset: the change runs, the latch clears, the spindle runs. Check the
      Bin column: the previously loaded tool must be back in its own bin.

## 5. Readout appearance (`TOOL XX  BIN XX`)

- [ ] After a completed change the row-2 bezel reads `TOOL <tool>  BIN <bin>`
      (e.g. `TOOL 15  BIN 2`). After a hand move or a boot both read 0 until an
      M6 or ATC Reset; after ATC Reset `TOOL` shows the declared tool.
- [ ] Spacing: the four elements should not overlap; report what it looks like
      so the margins in `BIN_ELEMENTS` (`tools/vcpgen.py`) can be tuned.

## 6. Rollback (if any phase fails and the machine is needed)

- [ ] Set **P160 = 0** and P6 back to the value recorded in section 0. Same
      `.plc` stays loaded: `SV_TOOL_NUMBER` is then the tool number, which equals
      the bin for tools 1-12, so `M6T1..T12` keep working. Tools above 12 are
      unavailable until the branch is fixed or reverted.
- [ ] Full rollback: on the control PC `git checkout main`, reload the `.plc`,
      set P701-P712, P160 = 0.

## Report back

Record, for the spec's open questions: (1) what the unassigned-tool M6 did,
(2) whether F2 ATC Reset worked, (3) any CNC12 complaint about a reported bin
of 0, (4) whether the incomplete-change prompt appeared after the 9067 fault.
