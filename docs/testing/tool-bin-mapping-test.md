# Tool-to-Bin Mapping - On-Machine Test Procedure

Covers the fixed tool->bin map (`P160 = 0`, parameters P701-P712), the retro VCP
`TOOL BIN` readout, and the manual-unlock bin reset.

## 0. Deploy (control PC)

- [ ] Copy `Centroid-Acroloc-ALLIN1DC.src`, compile/reload the `.plc` in CNC12
      (expect: compiles, no new errors).
- [ ] Copy `mfunc6.mac` into the CNC12 macro directory.
- [ ] Copy `resources/vcp/` (skin + images) to the control PC.
- [ ] Restart CNC12 (required to reload the skin and macros).

## 1. Setup

- [ ] Machine parameter **160 = 0** (custom flow; NOT enhanced ATC).
- [ ] Set **P701-P712 = the tool number physically loaded in bins 1-12**.
      Start 1:1 for a baseline: `P701=1, P702=2, ... P712=12`.
      Empty bin = leave `0`.
- [ ] Confirm the retro VCP shows a **`TOOL BIN`** window (top-left, row 2,
      left of the spindle %/RPM readout).

## 2. Identity-map sanity (baseline)

With P701..P712 = 1..12:

- [ ] MDI `M6T5` -> carousel indexes to **bin 5**, tool changes normally.
- [ ] **No pop-up** appears (no Escape needed).
- [ ] `TOOL BIN` reads **5** after the change.
- [ ] Repeat `M6T1` and `M6T12` -> bins 1 and 12, readout tracks.

## 3. The actual feature: a remapped / >12 tool

- [ ] Set **P705 = 31** (bin 5 now "holds" tool 31). (Live edit - no reboot.)
- [ ] MDI `M6T31` -> carousel indexes to **bin 5**; `TOOL BIN` reads **5**.
- [ ] Set it back: **P705 = 5**.
- [ ] (If you have a real >12 tool loaded, set its `P70b` and try `M6T<that>`.)

## 4. Unmapped tool (fault path)

- [ ] Pick a tool number that is in **no** P70x (e.g. `M6T99`).
- [ ] Expect: carousel spins, then **`CAROUSEL MOVE TIME OUT`** fault at ~20 s;
      motor stops, carousel relocks. `TOOL BIN` shows `99`.

## 5. Manual unlock = bin becomes UNKNOWN

- [ ] With Z at the tool-change position (clear), press the **manual unlock**
      button (`ATCManualUnlock_I`, INP24).
- [ ] `TOOL BIN` should drop to **0** (unknown) - it does NOT track hand rotation.
- [ ] Hand-spin the carousel a few bins forward/back, re-lock.
- [ ] Do a known `M6T<n>` -> it still finds the right bin (absolute-switch
      search) and `TOOL BIN` shows the new bin.
- [ ] Note: the **active tool** in CNC12 is NOT auto-cleared (PLC can't at
      P160=0) - re-set the current tool in CNC12 after a manual swap.

## 6. Readout appearance (report back for tuning)

- [ ] Does `TOOL BIN` read as `TOOL BIN <n>` with good spacing?
- [ ] DSEG7 digits rendering (not substituted)? Color/size OK next to the
      spindle readout?
- [ ] If spacing is off: note whether the label or number needs to move; the
      knobs are `BIN_ELEMENTS` marginright in `tools/vcpgen.py` (label 55,
      number 18).

## Report back
- Which steps passed / failed, any fault text, and how the `TOOL BIN` window
  looks (a photo helps for margin tuning).
