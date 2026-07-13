# Acroloc S10 PLC — Backlog

Post-release "tune and enhance" task list. Knock these out one at a time; each gets its own
brainstorm -> spec -> plan -> implement cycle (or a quick PR for housekeeping items). Ordered
by suggested priority. Update the status boxes as we go.

Legend: `[ ]` todo, `[~]` in progress, `[x]` done.

## Robustness / safety

- [x] **Coolant pump / flood-valve plumbing fix.** OUT4 is the coolant pump (`Mist_O` ->
  `CoolantPump_O`) and OUT3 is the flood valve (`Flood_O` -> `FloodValve_O`). The stock
  mutually-exclusive logic left flood opening the valve with the pump **off** — no nozzle
  flow. Now derived from the selected mode: flood = pump + valve, wash/"mist" = pump only;
  panel flood/wash made mutually exclusive. *Shipped on `post-release-fixes`.*

- [x] **ATC carousel search timeout.** Bound the carousel search so a jam, broken position
  switch, or invalid tool number can't spin the carousel forever. Arm `ATCSpin_T` (T24) at M6
  kickoff; fault (`CAROUSEL MOVE TIME OUT`, msg 63) + stop + relock after 20 s.
  Closed the `;TODO` and put the unused `ATCSpin_T` to work.
  *Status: implemented on branch `atc-carousel-timeout` (spec + plan 2026-07-11); pending
  on-machine validation via `docs/testing/atc-timeout-test.md`.*

- [x] **Fix MEM444 double-binding.** `ToolSelected_M` and `KbAux13Key_M` both bound `MEM444`.
  Confirmed active bug: `KbAux13Key_M` is read at src:1996 to fire Aux13, while
  `ToolSelected_M` is SET on every completed tool change — so a tool change spuriously fired
  Aux13. Moved `ToolSelected_M` to the free `MEM452`; the compiler's duplicate-binding warning
  cleared (194 -> 193). *Shipped on `post-release-fixes`.*

- [x] **Fix `ATC_Lock_Released_C` message value.** Was `IS 45546 ;(2+256*174)`, but
  `2+256*174 = 44546` — the old value was off by 1000 and did not decode to a valid file-2
  message, so the "Tool Carousel locked" message (msg 174, used at src:2864) posted a
  bad/blank message. Corrected `45546` -> `44546` (source + the definitions.md references).
  *Shipped on `post-release-fixes`.*

## Housekeeping / cleanup

- [x] **Strip leftover DEBUG changer-safety tracing.** Removed the temporary `; DEBUG`
  messages from the spindle-in-changer work: 3 constants + comment + 3 rungs in
  `Centroid-Acroloc-ALLIN1DC.src` and 3 lines in `plcmsg.txt`. Compiles clean (0 errors,
  193 warnings). *Shipped on `post-release-fixes`.*

- [ ] **Re-baseline `docs/plc-spec/` line-number pins.** (Post-merge task.) The specs anchor
  `src:NNNN` refs to "Line numbers as of commit 41f3fd6" across 9 docs (~505 refs total), now
  several commits stale. Do one careful pass **after `post-release-fixes` merges**, pinned to
  the resulting `main` commit — doing it mid-PR would pin to an unmerged (squash-discarded)
  commit and be immediately re-shifted. Mechanical; regenerate refs + bump each doc's pin.

- [x] **Decide on the mill-manual PDF.** `docs/official/centroid-cnc12-mill-operator-manual.pdf`
  (~57 MB) added to `.gitignore` as a local-only reference (the other tracked
  `docs/official/*.pdf` manuals are unaffected). *Shipped on `post-release-fixes`.*

## Enhancements (code)

- [x] **Closed-loop gear-position confirmation — WON'T DO.** Not feasible on this machine (the
  gear-sense inputs aren't wired and won't be). The shift stays intentionally open-loop. Cleaned
  up the remnants: removed the unused `SpinLowRange_I`/`SpinMedRange_I`/`SpinHighRange_I`
  (INP13-15) symbols (a source comment records the hardware fact), cleared 3 unused-input
  warnings (193 -> 190), and updated the docs to frame open-loop as by-design. *`post-release-fixes`.*

## Tuning (on-machine, mostly parameters)

- [x] **Spindle RPM accuracy + gear-shift smoothness — working as-is.** Owner confirms
  commanded-vs-actual RPM and gear-shift behavior are working great in the current tune
  (P863 ~2.0, CfgMin, shift coast/dwell). No changes needed; closed. *2026-07-12.*

## Documentation (machine facts — confirm with owner)

- [ ] **Fill acroloc-s10 machine-fact TBDs.** The machine reference files still carry
  `TBD — confirm with owner` for: axes (rapids/feeds, ways, accuracy, home positions), spindle
  (RPM per range, max RPM, taper, drawbar/retention, motor HP), ATC (tool size/weight limits,
  retention-knob type, air pressure), and work envelope/table (table size, T-slots, max
  workpiece weight, footprint/weight). Fill as the owner supplies real numbers.
