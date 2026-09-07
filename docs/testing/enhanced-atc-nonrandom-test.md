# Enhanced ATC (non-random, P160 = 1) - On-Machine Test Procedure

Covers the Tool Library bin map, the PLC position report, the bin range guard,
the VCP `TOOL BIN` readout, and F6 ATC Reset. Phases are gated: stop at the first
failing step and record what happened. Rollback is at the end.

Spec: `docs/superpowers/specs/2026-09-06-enhanced-atc-nonrandom-design.md`.

## 0. Record the starting state

- [ ] Machine parameters screen (F1 Setup > F3 Config > F3 Parms): write down the
      current values of **P6, P160, P161, P164**. (Expected before this change:
      P160 = 0.)
- [ ] Tool Library (F1 Setup > F2 Tool > F2 Tool Lib): note that the Bin column
      shows "Bin fields are locked".

## 1. Deploy (control PC)

- [ ] Copy `Centroid-Acroloc-ALLIN1DC.src`; compile/reload the `.plc` in CNC12
      (expect: compiles, no errors).
- [ ] Copy `mfunc6.mac` and `mfunc18.mac` into the CNC12 macro directory.
- [ ] Copy `plcmsg.txt` and `language.msg` over the control-PC copies.
- [ ] Set **P6 = 1, P160 = 1, P161 = 12, P164 = 1**. CNC12 warns that enhanced ATC
      needs a matching PLC program: accept.
- [ ] **Reboot CNC12** (P161 is sent to the PLC at power-up; macros and messages
      reload).

## 2. Phase A - handshake and identity loadout

- [ ] Home the machine.
- [ ] Tool Library: the Bin column is now editable and F1 Clear Bin / F2 Clear All
      appear. Set tools 1-12 to bins 1-12 (if CNC12 has not already initialised
      them that way). Set the tool that is physically under the spindle to bin
      **0**. F10 Save.
- [ ] **ALT+K** shows `ATC BIN n` where n is the bin under the spindle (the PLC's
      boot seed from CNC12; may read 0 the first time - that is allowed).
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

## 4. Phase C - manual unlock and F6 ATC Reset

- [ ] Z at the tool-change position (clear). Press the **manual unlock** button
      (`ATCManualUnlock_I`, INP24). `TOOL BIN` drops to **0**; ALT+K reads 0.
- [ ] Hand-spin the carousel **two bins forward**, release the button (relock).
      Note the bin now under the spindle (n) and the tool in it.
- [ ] Tool Library > **F6 ATC Reset**: carousel position = n (the default offered
      will be 0; type n), tool in spindle = the tool in bin n, putback = n. Confirm
      with Y. Expect the message `ATC INITIALIZED` or similar; if CNC12 refuses,
      record the text (open question 2 in the spec) and instead edit the Bin
      column by hand.
- [ ] ALT+K now reads n. The Bin column shows that tool at 0 and the previously
      "in spindle" tool back in its own bin.
- [ ] MDI `M6T<m>` for a tool in another bin -> lands on the right bin, readout
      correct.

## 5. Readout appearance

- [ ] `TOOL BIN` still renders as before next to the spindle readout (this change
      did not touch the VCP).

## 6. Rollback (if any phase fails and the machine is needed)

- [ ] Set **P160 = 0** and P6 back to the value recorded in section 0. Same
      `.plc` stays loaded: `SV_TOOL_NUMBER` is then the tool number, which equals
      the bin for tools 1-12, so `M6T1..T12` keep working. Tools above 12 are
      unavailable until the branch is fixed or reverted.
- [ ] Full rollback: reload the previous `.plc`, `mfunc6.mac`, `plcmsg.txt`,
      `language.msg` from `main`, set P701-P712, P160 = 0.

## Report back

Record, for the spec's open questions: (1) what the unassigned-tool M6 did,
(2) whether F6 ATC Reset worked, (3) any CNC12 complaint about a reported bin
of 0, (4) whether the incomplete-change prompt appeared after the 9067 fault.
