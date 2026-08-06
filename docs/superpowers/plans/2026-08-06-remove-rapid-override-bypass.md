# Tool-Change Override Restore + RAPID 25% Removal Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Restore CNC12's override control after every tool change, and delete the RAPID 25% button whose PLC logic bypasses CNC12's G74/G84 tapping lockout - the combination that fed a 10-32 tap at 25% and broke it.

**Architecture:** Two independent changes. (1) `mfunc6.mac` gains the `M108 /1/2` that pairs its existing unpaired `M109 /1/2`, restoring override control - and with it CNC12's ability to force feed override to 100% during a tapping cycle. (2) The RAPID 25% feature is removed entirely from the PLC source and the VCP generator, because machine testing proved `SV_PLC_RAPID_FEEDRATE_OVERRIDE` scales G1 as well as G0, making the button both mislabelled and redundant with the stock FEED 25% button that CNC12 does protect.

**Tech Stack:** Centroid CNC12 PLC stage language (`.src`), CNC12 macro language (`.mac`), Python 3 stdlib (VCP generator + its unittest suite), Centroid `mpucomp.exe` via Wine.

**Spec:** `docs/superpowers/specs/2026-08-05-rapid-override-g0-only-design.md`

## Global Constraints

- **Branch:** `feature/rapid-override-g0-only` (already created off `main`).
- **ASCII only.** `.src`, `.mac`, `.cnc`, `.hom` files must be plain 7-bit ASCII. No em dashes, no smart quotes. Verify with `LC_ALL=C grep -n '[^ -~]' <file>`.
- **Never hand-edit generated files.** Everything under `resources/vcp/` (except the vendored stock `Buttons/*` directories predating the generator) is emitted by `tools/vcpgen.py`. Edit the generator and re-run it.
- **plc-spec line pins.** `docs/plc-spec/*.md` pin source line numbers to commit `41f3fd6` via a "Line numbers as of commit 41f3fd6" header. When editing these files, **remove or correct false content only - do not re-baseline the line-number references.** The pin header stays as it is.
- **No automated tests exist for the PLC or macros.** Per `CLAUDE.md`, validation is `./compile.sh` plus machine testing. `tools/vcpgen.py` is the exception - it has `tools/test_vcpgen.py`.
- **Match surrounding style.** Fixed-column alignment for `Name IS Resource`; tag custom lines `; Acroloc`.

## Baseline (captured 2026-08-06 on this branch, before any change)

```
./compile.sh          -> Compilation successful
                         Program size: 5060 tokens (30.8838% of max)
                         Warnings: 190
python3 tools/test_vcpgen.py -> Ran 21 tests ... OK
```

Record the delta against these numbers at every verification step.

## File Structure

| File | Change | Responsibility |
| --- | --- | --- |
| `mfunc6.mac` | Modify (add 1 line before `N1000`) | Tool-change macro; must leave override control as it found it |
| `Centroid-Acroloc-ALLIN1DC.src` | Modify (delete 4 definitions + 8-line logic block) | PLC program; loses the RAPID 25% feature entirely |
| `tools/vcpgen.py` | Modify (delete 1 `BUTTONS` entry + its comment) | VCP generator; single source of truth for the panel |
| `resources/vcp/**` | Regenerate + delete 1 orphaned dir | Emitted panel; must not retain a dead button |
| `docs/plc-spec/atc.md` | Modify | ATC macro spec - quoted macro listing |
| `docs/plc-spec/main-stage.md` | Modify (delete section) | MainStage spec - RAPID 25% section is now false |
| `docs/plc-spec/definitions.md` | Modify (delete 3 rows + 1 inline mention) | Resource lookup table |
| `.claude/skills/acroloc-s10/reference/atc-flow.md` | Modify | Machine skill - ATC flow listing |
| `.claude/skills/acroloc-s10/reference/macros.md` | Modify | Machine skill - macro step list + pairing rule |
| `.claude/skills/centroid-plc-programming/reference/system-variables.md` | Modify (add row) | Records the measured `SV_PLC_RAPID_FEEDRATE_OVERRIDE` finding |
| `docs/superpowers/specs/2026-07-13-retro-vcp-theme-design.md` | Modify (annotate) | Historical spec describing the removed button |

---

### Task 1: Restore override control after a tool change

The core safety fix. `mfunc6.mac:13` issues `M109 /1/2` (disable feed and speed overrides) with no matching re-enable, so after the first M6 in a program CNC12 holds the override frozen and can no longer force it to 100% for a G74/G84 cycle. Stock Centroid pairs them: `docs/official/_ALLIN1DC/_atc/_umbrella/cncm/mfunc6.mac:28` has the `M109 /1/2`, line 94 has `M108 /1/2` immediately before its `N600` exit label.

**Files:**
- Modify: `mfunc6.mac:29-30`
- Modify: `docs/plc-spec/atc.md:41`
- Modify: `.claude/skills/acroloc-s10/reference/atc-flow.md:41`
- Modify: `.claude/skills/acroloc-s10/reference/macros.md:47`

**Interfaces:**
- Consumes: nothing from other tasks.
- Produces: nothing consumed by other tasks. Task 1 is fully independent of Tasks 2 and 3 and may be committed alone.

- [ ] **Step 1: Read the current end of the macro**

Run: `sed -n '10,30p' mfunc6.mac`

Confirm line 13 is `M109 /1/2       ; Disable overrides`, that no `M108` appears anywhere in the file, and that line 30 is `N1000           ; end of program`.

Also run `grep -n "M108" mfunc6.mac` and confirm it prints nothing.

- [ ] **Step 2: Add the pairing M-code before the exit label**

Placement is deliberate: the macro's `IF #4202 || #4201 THEN GOTO 1000` guard on line 11 skips `M109` too, so putting `M108` **before** `N1000` means both codes are skipped together in graph/search mode and the pair stays balanced.

Replace this (`mfunc6.mac:28-30`):

```gcode
M95 /8          ; reset M6_SV to stop tool change stage when done

N1000           ; end of program
```

with:

```gcode
M95 /8          ; reset M6_SV to stop tool change stage when done

M108 /1/2       ; Re-enable overrides (pairs the M109 /1/2 above -- an unpaired
                ; M109 leaves override control off for the rest of the program,
                ; which also disables CNC12's G74/G84 feed-override lockout)

N1000           ; end of program
```

- [ ] **Step 3: Verify the file is still ASCII and the pair is balanced**

Run:
```bash
LC_ALL=C grep -n '[^ -~]' mfunc6.mac; echo "ascii-exit:$?"
grep -c "M109 /1/2" mfunc6.mac
grep -c "M108 /1/2" mfunc6.mac
```

Expected: the first command prints no lines (exit 1 is correct - it means no matches). Both counts print `1`.

- [ ] **Step 4: Update the ATC spec's quoted macro listing**

In `docs/plc-spec/atc.md`, find the fenced `gcode` block containing the line:

```gcode
M95 /8                             ; mfunc6.mac:28 — reset M6_SV ...
```

Add immediately after it, before the block's `N1000` line:

```gcode
M108 /1/2                          ; mfunc6.mac:32 — re-enable overrides
```

Do **not** touch the `Line numbers as of commit 41f3fd6` header or renumber the other annotations - inserting at the end of the macro does not shift lines 11-28.

Note: this file uses em dashes in its annotations. It is Markdown, not controller source, so that is fine - leave the existing ones alone and match them if you add prose.

- [ ] **Step 5: Update the machine skill's ATC flow listing**

In `.claude/skills/acroloc-s10/reference/atc-flow.md`, the fenced `gcode` block near line 41 ends with:

```gcode
M109 /1/2                           ; disable overrides
```

That block shows only the macro's opening. Append a sentence immediately after the closing fence:

```markdown
The macro ends with `M108 /1/2`, re-enabling the overrides that `M109 /1/2`
turned off. The pair must always be balanced: an unpaired `M109` leaves CNC12's
override control disabled for the rest of the program, which also disables the
lockout that normally forces feed override to 100% during a G74/G84 tapping
cycle.
```

- [ ] **Step 6: Update the macro reference's step list**

In `.claude/skills/acroloc-s10/reference/macros.md`, the numbered list starting near line 45 reads:

```markdown
2. `M109 /1/2` — disables feed and speed overrides
```

Change that entry to:

```markdown
2. `M109 /1/2` — disables feed and speed overrides. **Always paired with
   `M108 /1/2` at the end of the macro.** An unpaired `M109` leaves override
   control off for the remainder of the program, which also disables CNC12's
   lockout that forces feed override to 100% during G74/G84 tapping cycles — a
   tap fed at a reduced override will break.
```

- [ ] **Step 7: Commit**

```bash
git add mfunc6.mac docs/plc-spec/atc.md \
        .claude/skills/acroloc-s10/reference/atc-flow.md \
        .claude/skills/acroloc-s10/reference/macros.md
git commit -m "fix(mfunc6): pair M109 /1/2 with M108 /1/2 to restore override control

mfunc6.mac issued M109 /1/2 (disable feed and speed overrides) with no
matching re-enable, so after the first M6 in a program CNC12 held the
override frozen at whatever value was current and stopped accepting
SV_PLC_FEEDRATE_KNOB.

This is not only a lost convenience. CNC12's tapping protection - the
feed override knob being locked out during G74/G84 - operates through
override control. An unpaired M109 disables the interlock that exists to
stop a tap being fed at a reduced override, which is how a 10-32 form tap
came to be driven at 25% of its programmed 7.987 ipm and broke.

Stock Centroid pairs them the same way:
docs/official/_ALLIN1DC/_atc/_umbrella/cncm/mfunc6.mac:28 and :94.

Placed before N1000 so the graph/search guard on line 11 skips both codes
together and the pair stays balanced.

Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>"
```

---

### Task 2: Remove the RAPID 25% PLC logic and its definitions

Machine testing on 2026-08-06 established that `SV_PLC_RAPID_FEEDRATE_OVERRIDE` scales **G1 as well as G0** - it is a global velocity scale, not a rapids-only one - and that it is written unconditionally every scan, straight to the MPU11, where CNC12 cannot see it and cannot lock it out for a tapping cycle. The stock FEED 25% button produces the same slowdown on both G0 and G1 while routing through CNC12, so removing this button costs no capability.

Leaving `SV_PLC_RAPID_FEEDRATE_OVERRIDE` entirely unwritten restores the MPU default of 1.0, so no residual scale can survive.

**Files:**
- Modify: `Centroid-Acroloc-ALLIN1DC.src` - delete lines 2003-2010 and definitions at 494, 528, 1037, 1214
- Modify: `docs/plc-spec/main-stage.md:349-359`
- Modify: `docs/plc-spec/definitions.md:151,181,305,336`
- Modify: `.claude/skills/centroid-plc-programming/reference/system-variables.md`

**Interfaces:**
- Consumes: nothing from Task 1.
- Produces: the four resources `OUT1133`, `MEM58`, `PD59`, `SV_SKIN_EVENT_82` become free for reuse. Task 3 removes the VCP button that generated `SV_SKIN_EVENT_82`; Tasks 2 and 3 are independent but both must land before the panel and PLC agree.

- [ ] **Step 1: Capture the baseline compile**

Run: `./compile.sh 2>&1 | tail -4`

Expected, matching the recorded baseline:
```
Compilation successful
Program size: 5060 tokens (30.8838% of max)
Warnings: 190
```

Write the three numbers down. If they differ from the baseline above, stop - the tree is not in the expected state.

- [ ] **Step 2: Confirm the four resources are referenced nowhere else**

Run:
```bash
grep -n "OUT1133\|MEM58\|PD59\|SV_SKIN_EVENT_82" Centroid-Acroloc-ALLIN1DC.src
grep -n "RapidOverLED_O\|Rapid25_M\|Rapid25PD_PD\|SkinRapid25_M_SV" Centroid-Acroloc-ALLIN1DC.src
```

Expected: the first prints exactly the four definition lines (494, 528, 1037, 1214). The second prints those four plus lines 2006-2010. Nothing else.

**Do not confuse `Rapid25PD_PD` (PD59, being deleted) with `RapidOverPD_PD` (PD19, at src:1178).** `RapidOverPD_PD` is stock, drives the F9 / Ctrl-R `SelectRapidOverride_SV` toggle at src:1999-2000, and **must stay**.

- [ ] **Step 3: Delete the logic block**

Delete `Centroid-Acroloc-ALLIN1DC.src:2003-2010` in full, including the blank line 2002 that separated it from the stock rung above. The block to remove is exactly:

```
; Acroloc: VCP RAPID 25% button - rapids-only cut. While latched, rapid (G0)
; moves run at 25% via SV_PLC_RAPID_FEEDRATE_OVERRIDE (a 0.0-2.0 scale like
; SV_PLC_FEEDRATE_OVERRIDE above); the feedrate override is untouched.
IF SkinRapid25_M_SV THEN (Rapid25PD_PD)
IF (Rapid25_M ^ Rapid25PD_PD) THEN (Rapid25_M)
IF Rapid25_M THEN SV_PLC_RAPID_FEEDRATE_OVERRIDE = 0.25
IF !Rapid25_M THEN SV_PLC_RAPID_FEEDRATE_OVERRIDE = 1.0
IF Rapid25_M THEN (RapidOverLED_O)
```

After deletion, `IF OnAtPowerUp_M THEN SET SelectRapidOverride_SV` (the stock rung formerly at 2001) must be followed by one blank line and then `IF (CycleCancelKey_I || KbCycleCancel_M || MpgResetKey_M || SkinCycleCancel_M_SV) || ErrorFlag_M`.

- [ ] **Step 4: Delete the four definitions**

Delete these four whole lines. Line numbers shift as you go - delete from the bottom up, or match on text.

```
RapidOverLED_O                  IS OUT1133 ; Acroloc VCP RAPID 25% button LED (stock rapid_over LED number)
Rapid25_M                       IS MEM58  ; Acroloc latched by the VCP RAPID 25% button; rapids cut to 25% while set
SkinRapid25_M_SV                IS SV_SKIN_EVENT_82 ; Acroloc VCP RAPID 25% button (stock rapid_over event number)
Rapid25PD_PD                    IS PD59 ; Acroloc one-shot for the VCP RAPID 25% toggle
```

- [ ] **Step 5: Verify nothing survives, and the file is still ASCII**

Run:
```bash
grep -n "Rapid25\|RapidOverLED_O\|SV_PLC_RAPID_FEEDRATE_OVERRIDE\|OUT1133\|MEM58\|PD59\|SV_SKIN_EVENT_82" Centroid-Acroloc-ALLIN1DC.src
grep -c "RapidOverPD_PD" Centroid-Acroloc-ALLIN1DC.src
LC_ALL=C grep -n '[^ -~]' Centroid-Acroloc-ALLIN1DC.src
```

Expected: the first prints nothing. The second prints `3` (the stock PD19 definition and its two uses, untouched). The third prints nothing.

- [ ] **Step 6: Compile and report the delta**

Run: `./compile.sh 2>&1 | tail -4`

Expected: `Compilation successful`, **program size strictly below 5060 tokens**, and warnings at or below 190. Report the exact delta as "5060 -> N tokens, 190 -> M warnings".

If the program size did not drop, the logic block was not actually removed. If errors appear, the most likely cause is deleting a definition that is still referenced - re-run Step 5's first grep.

Note: this change deliberately alters the compiled program, so the plcfmt fingerprint `(program_words, C2, C4)` is **expected to change**. The fingerprint gate applies only to formatting-only edits.

- [ ] **Step 7: Delete the now-false main-stage spec section**

In `docs/plc-spec/main-stage.md`, delete the entire section beginning at line 349:

```markdown
### RAPID 25% rapids-only override (Acroloc, src:1976-1980)
```

through to just before the next `###` heading (`### Coolant (mist/flood) — mfunc7/mfunc8 linkage`). The whole section describes behaviour that has been removed and that was factually wrong besides.

Leave the file's `Line numbers as of commit 41f3fd6` header alone and do not renumber other sections.

- [ ] **Step 8: Delete the definitions-table rows**

In `docs/plc-spec/definitions.md`, delete these three whole table rows:

- Line 151, the `` `RapidOverLED_O` `` row
- Line 181, the `` `Rapid25_M` `` row
- Line 336, the `` `SkinRapid25_M_SV` `` row

Then fix the running prose at lines 303-307. It currently reads (the `...` is literal in the document, not an abbreviation here):

```markdown
Pulse-detect (one-shot) bits, `PD1`-`PD59`, defined at src:1112-1166. All but one belong to
stock jog-panel/keyboard/coolant/spindle edge-detection logic (`IncrContPD_PD`,
`SlowFastPD_PD`, `MpgPD_PD`, ... `SkinFeedOverPlusPD_PD`); `Rapid25PD_PD` (PD59, src:1201)
is the Acroloc one-shot edge of the VCP RAPID 25% button event. See
```

Replace those four lines with:

```markdown
Pulse-detect (one-shot) bits, `PD1`-`PD58`, defined at src:1112-1166. All belong to
stock jog-panel/keyboard/coolant/spindle edge-detection logic (`IncrContPD_PD`,
`SlowFastPD_PD`, `MpgPD_PD`, ... `SkinFeedOverPlusPD_PD`). See
```

Three edits are folded in there: the range drops to `PD58` now that PD59 is free, "All but one belong to" becomes "All belong to", and the `Rapid25PD_PD` clause and its sentence are gone. Leave the following line (`[jog-and-mpg.md](jog-and-mpg.md) and [main-stage.md](main-stage.md) for their consuming ...`) untouched.

- [ ] **Step 9: Record the measured finding in the PLC system-variable reference**

This is the durable lesson: the SV's name is misleading and cost a tap.

In `.claude/skills/centroid-plc-programming/reference/system-variables.md`, the feedrate group sits at lines 390-393. The table is three columns: `| NAME | Description. | source |`. Insert a new row **immediately after line 391** (`SV_PLC_FEEDRATE_OVERRIDE`), so it sits beside the sibling it is most likely to be confused with:

```markdown
| SV_PLC_RAPID_FEEDRATE_OVERRIDE | F32. 0–2.0 velocity scale written straight to the MPU11. **Despite the name this is NOT rapids-only — measured on this ALLIN1DC 2026-08-06 to scale G1 feed moves as well as G0 rapids.** CNC12 cannot observe the write, so it bypasses SV_PC_OVERRIDE_CONTROL_FEEDRATE_OVERRIDE and with it the G74/G84 tapping lockout — a tap fed through this scale will break. Used by zero stock Centroid PLCs. There is no system variable exposing motion type, so a PLC-side G0-only gate cannot be built either. | measured |
```

The surrounding rows use en dashes (`–`) in ranges like `0–2.0`; this is Markdown documentation, not controller source, so the ASCII-only rule does not apply here. Match the neighbours.

- [ ] **Step 10: Commit**

```bash
git add Centroid-Acroloc-ALLIN1DC.src docs/plc-spec/main-stage.md \
        docs/plc-spec/definitions.md \
        .claude/skills/centroid-plc-programming/reference/system-variables.md
git commit -m "fix(plc): remove RAPID 25% - the SV scales G1, bypassing CNC12

Machine testing 2026-08-06: with RAPID 25% latched, both G0 and G1 are
scaled. SV_PLC_RAPID_FEEDRATE_OVERRIDE is a global velocity scale, not
the rapids-only one this feature assumed. It was written unconditionally
every scan straight to the MPU11, where CNC12 cannot see it and cannot
lock it out for a G74/G84 cycle.

The stock FEED 25% button produces the same slowdown on both G0 and G1
(rapid-override mode is SET at power-up by stock logic, src:2001) while
routing through CNC12, where the tapping lockout protects it. So this
button was mislabelled, redundant, and the only path bypassing the
interlock. Removing it costs no capability.

Leaving the SV entirely unwritten restores the MPU default of 1.0.

Frees OUT1133, MEM58, PD59, SV_SKIN_EVENT_82. Retires the Rapid25_M
latch and with it its missing-power-up-reset defect. RapidOverPD_PD
(PD19) is stock and untouched.

Records the measured SV behaviour in the centroid-plc-programming
reference so the trap is not re-entered.

Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>"
```

---

### Task 3: Remove the RAPID 25% button from the VCP

The panel button must go with the logic, or it becomes a dead control that silently does nothing. `tools/vcpgen.py` is the single source of truth - it emits the skin grid, the button XML, and the SVGs.

**Critical:** the generator only ever creates and overwrites (`os.makedirs(..., exist_ok=True)`); it **never deletes stale output**. Removing the entry from `BUTTONS` will drop the button from the regenerated skin, but the previously emitted `resources/vcp/Buttons/retro_rapid_over/` directory will be orphaned and must be removed by hand.

**Files:**
- Modify: `tools/vcpgen.py:517-519`
- Regenerate: `resources/vcp/skins/acroloc_retro_vcp_skin.vcp` and button output
- Delete: `resources/vcp/Buttons/retro_rapid_over/`
- Modify: `docs/superpowers/specs/2026-07-13-retro-vcp-theme-design.md:48`

**Interfaces:**
- Consumes: nothing. Independent of Tasks 1 and 2, though it should land with Task 2 so the panel and PLC agree.
- Produces: grid cell row 11 / column 5 becomes empty.

- [ ] **Step 1: Capture the baseline generator test run**

Run: `python3 tools/test_vcpgen.py 2>&1 | tail -4`

Expected: `Ran 21 tests` ... `OK`.

Also run `grep -n -i "rapid" tools/test_vcpgen.py` and confirm it prints nothing - no test asserts on this button, so the suite needs no changes.

- [ ] **Step 2: Confirm which emitted artifacts are generated vs vendored**

Run:
```bash
git log --oneline -1 -- resources/vcp/Buttons/rapid_over/
git log --oneline -1 -- resources/vcp/Buttons/retro_rapid_over/
grep -n "retro_rapid_over" resources/vcp/skins/acroloc_retro_vcp_skin.vcp
```

Expected: `rapid_over/` traces to `908df70 add resources` - that is **vendored stock Centroid content, leave it alone**. `retro_rapid_over/` traces to `b90529c` - that is **our generated output, to be deleted**. The skin has exactly one reference, at line 369.

`resources/vcp/Buttons/rapid_over_legacy/` and `resources/vcp/skins/servo_mill_vcp_rapid_skin.vcp` are also vendored stock. Do not touch either.

- [ ] **Step 3: Delete the generator's button entry**

In `tools/vcpgen.py`, delete these three lines (the two-line comment and the entry), currently at 517-519:

```python
    # rapids-only 25% cut; stock rapid_over xml = skin event 82 + LED
    # OUT1133, both handled by the PLC's Rapid25_M latch
    dict(name='rapid_over', row=11, col=5, lines=['RAPID', '25%']),
```

Leave the surrounding `cycle_start` and `cycle_cancel` entries untouched.

- [ ] **Step 4: Regenerate the panel**

Run: `python3 tools/vcpgen.py`

- [ ] **Step 5: Remove the orphaned generated directory**

The generator does not clean up after itself, so do it explicitly:

```bash
git rm -r resources/vcp/Buttons/retro_rapid_over/
```

- [ ] **Step 6: Verify the button is gone from every generated artifact**

Run:
```bash
grep -rn "retro_rapid_over" resources/vcp/ ; echo "grep-exit:$?"
ls resources/vcp/Buttons/ | grep -i rapid
git status --short resources/vcp/
```

Expected: the first grep prints nothing (exit 1). The `ls` prints only the vendored `rapid_over` and `rapid_over_legacy` - **not** `retro_rapid_over`. `git status` shows the skin file modified and the `retro_rapid_over/` files deleted.

- [ ] **Step 7: Run the generator test suite**

Run: `python3 tools/test_vcpgen.py 2>&1 | tail -4`

Expected: `Ran 21 tests` ... `OK`, unchanged from baseline. If a test now fails, it asserted on the total button count or the grid layout - read the failure and report it rather than editing the test to pass.

- [ ] **Step 8: Annotate the superseded VCP theme spec**

`docs/superpowers/specs/2026-07-13-retro-vcp-theme-design.md:48` describes the button as a rapids-only cut, which is now known false. That file is a historical design record, so annotate rather than rewrite. Change the row-11 table cell so the RAPID 25% clause reads:

```markdown
RAPID 25% toggle (11,5) — **REMOVED 2026-08-06**, see
`2026-08-05-rapid-override-g0-only-design.md`: `SV_PLC_RAPID_FEEDRATE_OVERRIDE`
was measured to scale G1 as well as G0 and to bypass CNC12's G74/G84 override
lockout; the cell is now empty
```

- [ ] **Step 9: Commit**

```bash
git add tools/vcpgen.py resources/vcp \
        docs/superpowers/specs/2026-07-13-retro-vcp-theme-design.md
git commit -m "fix(vcp): remove the RAPID 25% button from the panel

Follows the PLC-side removal. Leaving the button on the panel with its
logic gone would give the operator a dead control.

Deletes the rapid_over entry from tools/vcpgen.py and regenerates
resources/vcp. The generator only creates and overwrites - it never
deletes stale output - so the orphaned emitted directory
Buttons/retro_rapid_over/ is removed explicitly.

The vendored stock Buttons/rapid_over/, Buttons/rapid_over_legacy/ and
skins/servo_mill_vcp_rapid_skin.vcp are untouched.

Grid cell row 11 column 5 is left empty; re-flowing the layout is out of
scope. The stock FEED 25% button on the bottom row already produces the
same slowdown on G0 and G1, under CNC12's supervision.

Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>"
```

---

## Final verification before loading on the machine

- [ ] **Whole-tree checks**

```bash
./compile.sh 2>&1 | tail -4
python3 tools/test_vcpgen.py 2>&1 | tail -3
LC_ALL=C grep -n '[^ -~]' Centroid-Acroloc-ALLIN1DC.src mfunc6.mac; echo "ascii-exit:$?"
grep -rn "Rapid25\|retro_rapid_over\|RapidOverLED_O" \
     Centroid-Acroloc-ALLIN1DC.src tools/vcpgen.py resources/vcp docs/plc-spec
git log --oneline main..HEAD
```

Expected: compile successful with program size below 5060 tokens; 21 tests OK; no non-ASCII lines; the final grep prints nothing; three commits on the branch.

## Machine tests after loading

These cannot be run on the dev box. They are the acceptance criteria.

- [ ] **1. M108 regression (verifies Task 1).** Run any program containing an `M6`. After the tool change completes, press the FEED 25% / 50% / 100% buttons and confirm the override responds. Before this fix it would have been frozen.

- [ ] **2. Tapping lockout (the test that proves the failure cannot recur).** With FEED 25% latched, run a G84 tapping cycle in scrap. The actual feedrate must **not** drop to 25% - CNC12 should hold it at 100% for the duration of the cycle. This test could not have passed before Task 1, because the unpaired `M109` had disabled the override control the lockout works through.

- [ ] **3. No residual scale.** With no override selected, confirm G0 and G1 both run at full commanded rate - nothing is still writing a rapid scale to the MPU.

- [ ] **4. Panel sanity.** Confirm the VCP loads, row 11 column 5 is empty, and no button is missing or misplaced. A VCP that fails to load usually means a skin references a button directory that no longer exists.

## Out of scope

Carried from the spec; do not let these creep in:

- `SelectRapidOverride_SV` / `SV_PLC_FUNCTION_34` at src:1998-2001. It is byte-identical to stock and is what makes FEED 25% affect rapids - the behaviour we now rely on.
- Probing `SV_VELOCITY_RATIO` as a possible true G0-only mechanism.
- Re-flowing the VCP grid to fill the vacated cell.
- The missing `M8` before the tapping section and the `M99` ending in `Titan-4M-Op1-G54.nc` - CAM post-processor concerns.
