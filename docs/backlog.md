# Acroloc S10 PLC — Backlog

Post-release "tune and enhance" task list. Knock these out one at a time; each gets its own
brainstorm -> spec -> plan -> implement cycle (or a quick PR for housekeeping items). Ordered
by suggested priority. Update the status boxes as we go.

Legend: `[ ]` todo, `[~]` in progress, `[x]` done.

## Robustness / safety

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

- [ ] **Re-baseline `docs/plc-spec/` line-number pins.** The specs anchor `src:NNNN` refs to
  "Line numbers as of commit 41f3fd6," now several commits stale (oil-pump + this backlog's work
  will add more drift). Do a periodic pass: regenerate line refs and bump the pinned commit on
  each plc-spec doc. Mechanical; batch it after a few code changes land, not per-change.

- [ ] **Decide on the mill-manual PDF.** `docs/official/centroid-cnc12-mill-operator-manual.pdf`
  (~57 MB) sits untracked. Choose: commit via Git LFS, add to `.gitignore`, or leave as a local
  reference. Repo hygiene.

## Enhancements (code)

- [ ] **Closed-loop gear-position confirmation.** The two-speed shift (`GearShiftStage`,
  OUT19/OUT20) is currently open-loop — it commands a clutch and assumes it engaged. The stock
  gear-sense inputs `SpinLowRange_I`/`SpinMedRange_I`/`SpinHighRange_I` (INP13-15) are defined but
  unused (reserved for exactly this). Wire them in to confirm the commanded gear actually
  engaged and fault/retry if not. Needs the inputs physically wired + owner confirmation of the
  sense scheme.

## Tuning (on-machine, mostly parameters)

- [ ] **Spindle RPM accuracy + gear-shift smoothness.** Validate/tune commanded-vs-actual RPM per
  range, the high-gear ratio (P863, ~2.0), CfgMin, and shift coast/dwell behavior. More
  on-machine validation than code; may surface small logic tweaks.

## Documentation (machine facts — confirm with owner)

- [ ] **Fill acroloc-s10 machine-fact TBDs.** The machine reference files still carry
  `TBD — confirm with owner` for: axes (rapids/feeds, ways, accuracy, home positions), spindle
  (RPM per range, max RPM, taper, drawbar/retention, motor HP), ATC (tool size/weight limits,
  retention-knob type, air pressure), and work envelope/table (table size, T-slots, max
  workpiece weight, footprint/weight). Fill as the owner supplies real numbers.
