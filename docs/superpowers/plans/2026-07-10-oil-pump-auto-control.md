# Oil Pump (OUT2) Auto-Control Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Drive the oil pump on `Lube_O` (OUT2) so it runs only while a G-code program is actively executing and stops the instant the job stops for any reason (feed-hold, cycle-cancel/reset, E-stop, program end), replacing Centroid's stock metered way-lube logic.

**Architecture:** Delete the two stock lube-metering stages and their Parameter-179 boot plumbing, then drive OUT2 from a single combinational coil in `MainStage` conditioned on `SV_JOB_IN_PROGRESS && !SV_MDI_MODE && !FeedHoldLED_O && EStopOk_M`. The independent lube-**fault** monitoring (`LubeOk_I` -> `LubeFault_M` -> messages) is left untouched.

**Tech Stack:** Centroid CNC12 / MPU11 PLC stage language (`Centroid-Acroloc-ALLIN1DC.src`). The only in-repo verification is the local compiler `./compile.sh` (MPUCOMP via wine) — syntax/lint only. Real behavior is validated on the machine/simulator by the owner (off-repo); the implementer cannot do it and must not claim it was done.

**Design spec:** `docs/superpowers/specs/2026-07-10-oil-pump-auto-control-design.md`

## Global Constraints

- **ASCII only.** `.src`/`.mac`/`.map` must be plain 7-bit ASCII — no em dashes, smart quotes, or non-ASCII. (Docs `.md` may be UTF-8 but keep them ASCII here to match the source.)
- **`.src` is CRLF.** `.gitattributes` sets `text eol=crlf` for the source; the Edit tool inserts LF. After editing the `.src`, renormalize line endings with `sed -i 's/\r*$/\r/' Centroid-Acroloc-ALLIN1DC.src` and confirm `git diff` shows content-only changes (no whole-file CRLF churn).
- **Tag custom code `; Acroloc`.** Match the surrounding fixed-column style.
- **Compile gate:** `./compile.sh` must report `Compilation successful` with **0 errors**. Baseline before any change: 4880 tokens, **195 warnings**. Removing dead code and adding one coil that references existing symbols should not add warnings (expect <= 195); investigate any *new* warning.
- **Doc line-number pins:** the `docs/plc-spec/` files anchor line numbers to a pinned commit ("Line numbers as of commit 41f3fd6") and the repo does **not** re-baseline them on every edit (PR #12 did not). Fix now-false prose/content; do **not** regenerate unrelated `src:` line numbers or bump pins.
- **Commit only when asked** is the user's standing rule. Each task ends with a commit **step**, but confirm with the user before actually committing/pushing if they have not pre-authorized it.

---

### Task 1: Replace stock lube metering with the oil-pump coil (PLC source)

**Files:**
- Modify: `Centroid-Acroloc-ALLIN1DC.src` (definitions block, `LoadParametersStage`, the two lube stages, and `MainStage`)

**Interfaces:**
- Consumes (all pre-existing system/definitions symbols): `SV_JOB_IN_PROGRESS`, `SV_MDI_MODE`, `FeedHoldLED_O` (OUT1104), `EStopOk_M` (MEM), `Lube_O` (OUT2).
- Produces: OUT2 driven solely by the new coil. Retires `LubeUsePumpTimersStage`, `LubeUsePLCTimersStage`, `LubeM_T`, `LubeS_T`, `Lube_W`, `LubeM_W`, `LubeS_W`, `LubeAccumTime_W`, `StopRunningPD_PD`, and Parameter 179's PLC effect.

- [ ] **Step 1: Confirm clean baseline.**

Run: `./compile.sh`
Expected: `Compilation successful`, `Program size: 4880 tokens`, `Warnings: 195`.

- [ ] **Step 2: Delete the dead resource definitions.**

Delete these nine definition lines (each is a unique full line; remove the whole line):

```
LubeAccumTime_W                 IS W1
Lube_W                          IS W61
LubeM_W                         IS W62
LubeS_W                         IS W63
StopRunningPD_PD                 IS PD35
LubeM_T                         IS T13
LubeS_T                         IS T14
LubeUsePumpTimersStage          IS STG13
LubeUsePLCTimersStage           IS STG14
```

Leave `Lube_O IS OUT2`, `LubeOk_I IS INP9`, `LubeFault_M IS MEM49`, and the `LUBE_FAULT_MSG_C`/`LUBE_WARNING_MSG_C` constants in place — they are still used by the fault path.

- [ ] **Step 3: Delete the Parameter-179 boot load rung** in `LoadParametersStage`.

Remove this rung and its comment header (the two comment lines directly above it that read `; Load lube pump times from P179 ...`):

```
; Load lube pump times from P179 and convert to milliseconds.
IF True_M THEN Lube_W = SV_MACHINE_PARAMETER_179,
             LubeM_W = (Lube_W / 100) * 60000,
             LubeS_W = (Lube_W % 100) * 1000
```

Also delete the large explanatory comment block above it that documents "METHOD 1 / METHOD 2 ... Machine Parameter 179" (the lines beginning `; There are two methods of control for the lube pump ...` down to the blank line before `;Set MPG Settings`). Keep `;Set MPG Settings` and everything after it.

- [ ] **Step 4: Delete the method-select rungs** further down in `LoadParametersStage`:

```
; Set the appropriate stage according to method of control
IF LubeS_W == 0 THEN SET LubeUsePumpTimersStage, RST LubeUsePLCTimersStage
IF LubeS_W != 0 THEN SET LubeUsePLCTimersStage, RST LubeUsePumpTimersStage
```

- [ ] **Step 5: Delete the two lube stage bodies in full.**

Delete the entire contiguous region containing both stages — from the `;===...` separator line immediately above `                        LubeUsePumpTimersStage` through the last rung of `LubeUsePLCTimersStage`:

```
IF LubeS_T || !EStopOk_M THEN RST Lube_O, RST LubeS_T
```

That block spans the `LubeUsePumpTimersStage` banner + its METHOD 1 comment block + its three rungs (`IF (SV_PROGRAM_RUNNING || SV_MDI_MODE) THEN SET Lube_O, RST LubeM_T` ...), and the `LubeUsePLCTimersStage` banner + its METHOD 2 comment block + its rungs. The next stage banner, `KeyboardEventsStage`, and everything after it must remain untouched. After deletion there should be **zero** remaining references to any symbol removed in Step 2 (verified in Step 7).

- [ ] **Step 6: Add the oil-pump coil in `MainStage`.**

Locate the lube-fault rungs in `MainStage` and insert the coil immediately after the `LUBE_WARNING` rung. Replace:

```
IF !LubeOk_I && SV_PROGRAM_RUNNING THEN InfoMsg_W = LUBE_WARNING_MSG_C

IF Initialize_T && !SpindleInverterOk_I
```

with:

```
IF !LubeOk_I && SV_PROGRAM_RUNNING THEN InfoMsg_W = LUBE_WARNING_MSG_C

; Acroloc oil pump: power OUT2 only while a G-code program is actively
; executing. Off in MDI, at idle, on feed-hold, and on any stop
; (cycle-cancel/reset, E-stop, program end). Coil form = no latch: OUT2
; drops the same scan any term clears. EStopOk_M term mirrors the stock
; E-stop cutoff. Replaces the retired Parameter-179 lube-timer stages.
IF SV_JOB_IN_PROGRESS && !SV_MDI_MODE && !FeedHoldLED_O && EStopOk_M THEN (Lube_O)

IF Initialize_T && !SpindleInverterOk_I
```

- [ ] **Step 7: Renormalize line endings and confirm no dangling references.**

Run:
```bash
sed -i 's/\r*$/\r/' Centroid-Acroloc-ALLIN1DC.src
for s in LubeUsePumpTimersStage LubeUsePLCTimersStage LubeM_T LubeS_T Lube_W LubeM_W LubeS_W LubeAccumTime_W StopRunningPD_PD SV_MACHINE_PARAMETER_179; do
  echo "=== $s ==="; grep -n "\b$s\b" Centroid-Acroloc-ALLIN1DC.src || echo "(none — good)"
done
```
Expected: every symbol reports `(none — good)`. Any remaining hit is a leftover reference — fix before continuing.

- [ ] **Step 8: Compile.**

Run: `./compile.sh`
Expected: `Compilation successful`, **0 errors**, `Warnings: <= 195`. Token count drops below 4880 (dead code removed). If a *new* warning appears, investigate (likely a missed reference from Steps 2-5).

- [ ] **Step 9: Confirm the diff is content-only (no CRLF churn).**

Run: `git diff --stat Centroid-Acroloc-ALLIN1DC.src` and `git diff Centroid-Acroloc-ALLIN1DC.src | grep -c '^[-+]'`
Expected: the stat shows a modest number of changed lines (roughly ~90 deletions, ~7 insertions), **not** the whole file. Eyeball `git diff` to confirm only the intended lube regions and the new coil changed.

- [ ] **Step 10: Commit.**

```bash
git add Centroid-Acroloc-ALLIN1DC.src
git commit -m "feat(plc): oil pump runs only while a program executes (OUT2)

Replace stock Parameter-179 lube-metering stages with a single combinational
coil driving Lube_O (OUT2): on only while SV_JOB_IN_PROGRESS and not in MDI,
feed-hold, or E-stop. Removes LubeUsePumpTimersStage/LubeUsePLCTimersStage and
their dead timers/words; P179 no longer read. Lube-fault monitoring untouched.

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

**Operator gate (off-repo, MUST precede machine use):** load the compiled `.src` in CNC12 on the control PC, confirm a clean compile, and run the on-machine test checklist (Task 3 / spec Testing section). The implementer cannot perform this and must not claim it was done.

---

### Task 2: Sync affected documentation

**Files:**
- Modify: `docs/plc-spec/boot.md`, `docs/plc-spec/parameters.md`, `docs/plc-spec/definitions.md`, `docs/plc-spec/scan-model.md`, `docs/plc-spec/main-stage.md`

**Scope note:** Fix only content made false by Task 1. Do **not** regenerate unrelated `src:` line numbers or bump the "Line numbers as of commit 41f3fd6" pins — matching the repo's established practice (PR #12 changed source + `main-stage.md` prose without re-baselining).

- [ ] **Step 1: `boot.md` — remove the lube-timing description.**

Delete the bullet describing the Parameter-179 lube load and method selection (the `**Lube pump timing** (src:1294-1296)...` bullet through the `LubeUsePLCTimersStage for pumps the PLC must time itself.` line) and replace with:

```markdown
- **Oil pump:** no longer timed at boot. Parameter 179 is retired (not read by the
  PLC). The pump on `Lube_O` (OUT2) is driven by the oil-pump coil in `MainStage`
  (`SV_JOB_IN_PROGRESS && !SV_MDI_MODE && !FeedHoldLED_O && EStopOk_M`); see
  [main-stage.md](main-stage.md).
```

In the summary sentence that lists boot-selected stages ("...lube, MPG, jog-key, and load-meter stages."), remove `lube, ` so it reads "...MPG, jog-key, and load-meter stages."

- [ ] **Step 2: `parameters.md` — retire the P179 row.**

Change the P179 table row so its meaning and notes read that it is **retired / no longer read by the PLC** (oil pump now driven by the `MainStage` oil-pump coil), rather than "Lube-pump timing ... selects pump-timer method." Keep the row present (parameter numbers are a stable reference) but mark it retired.

- [ ] **Step 3: `definitions.md` — remove the deleted-symbol rows.**

Delete the atlas rows for the nine removed symbols: `LubeAccumTime_W`, `Lube_W`, `LubeM_W`, `LubeS_W`, `LubeM_T`, `LubeS_T`, `LubeUsePumpTimersStage`, `LubeUsePLCTimersStage`, and `StopRunningPD_PD` (search the file for each; some are in the words/timers/stages/pulse tables). Update the `Lube_O` row note from "Lube pump, SPST." to "Oil pump, SPST — driven by the `MainStage` oil-pump coil." Leave `LubeOk_I`, `LubeFault_M`, and the two `LUBE_*_MSG_C` rows. Add one line under the file's intro noting the lube-metering symbols were removed by the oil-pump auto-control change (2026-07-10) so a reader knows why they are absent.

- [ ] **Step 4: `scan-model.md` — replace the retired-timer example.**

The timer-semantics example currently uses `LubeM_T` (now removed). Replace it with a surviving timer that shows the same preset-then-`SET`-arms / true-when-expired pattern — use `TriggerPause_T` from `MainStage` (`IF ActivateFeedHold_M THEN TriggerPause_T=100, SET TriggerPause_T` then `IF TriggerPause_T THEN RST TriggerPause_T, RST ActivateFeedHold_M`). Keep the teaching point identical; just swap the symbol and rung text. Do not chase exact line numbers (pin convention).

- [ ] **Step 5: `main-stage.md` — document the oil-pump coil.**

In the coolant/spindle/output-coil area of the MainStage reference, add a short bullet: the oil pump `Lube_O` (OUT2) is driven by a combinational coil `SV_JOB_IN_PROGRESS && !SV_MDI_MODE && !FeedHoldLED_O && EStopOk_M` — on only while a program actively runs, off in MDI/idle/feed-hold/stop; it replaced the retired Parameter-179 lube-timer stages. Note the interaction: the spindle-in-changer interlock's own feed-hold (via `FeedHoldLED_O`) also parks the pump, which is intended. The existing lube-**fault** bullets stay as-is.

- [ ] **Step 6: Commit.**

```bash
git add docs/plc-spec/boot.md docs/plc-spec/parameters.md docs/plc-spec/definitions.md docs/plc-spec/scan-model.md docs/plc-spec/main-stage.md
git commit -m "docs: sync plc-spec to oil-pump auto-control (retire P179 lube metering)

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

### Task 3: On-machine test checklist

**Files:**
- Create: `docs/testing/oil-pump-test.md`

**Interfaces:** consumes nothing in code; mirrors the spec's Testing section into the repo's `docs/testing/` checklist pattern (parity with `spindle-changer-safety-test.md`).

- [ ] **Step 1: Write the checklist.**

Create `docs/testing/oil-pump-test.md` with an operator checklist watching OUT2 (`Lube_O`) in PLC Diagnostics (Alt-I), covering exactly the spec's eight cases:

1. Idle at main screen -> OUT2 = 0.
2. At MDI prompt -> OUT2 = 0; run an MDI move (`G53 Z-1`) -> OUT2 stays 0.
3. Run a short program -> OUT2 = 1 for the whole run, returns to 0 at program end.
4. Mid-program feed-hold -> OUT2 -> 0 on hold; cycle-start -> OUT2 = 1.
5. Mid-program cycle-cancel/reset -> OUT2 -> 0 and stays 0.
6. Mid-program E-stop -> OUT2 -> 0.
7. Manual jog / MPG -> OUT2 = 0.
8. Lube-fault path intact: program running with `LubeOk_I` (INP9) open still posts `LUBE WARNING`.

Include a short sign-off table (date/operator, PLC source commit tested, pass/fail per item, notes).

- [ ] **Step 2: Commit.**

```bash
git add docs/testing/oil-pump-test.md
git commit -m "docs(testing): oil-pump auto-control on-machine checklist

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

## Self-Review

- **Spec coverage:** control rung (Task 1 Step 6), full removal of metering + P179 (Task 1 Steps 2-5), preserved fault path (Task 1 Steps 2/6 leave it), doc sync incl. retired-P179 and interaction note (Task 2), testing (Task 3). All spec sections mapped.
- **Placeholder scan:** none — exact strings/commands given; the one judgment step (scan-model timer swap) names the concrete replacement (`TriggerPause_T`).
- **Type/name consistency:** the coil condition `SV_JOB_IN_PROGRESS && !SV_MDI_MODE && !FeedHoldLED_O && EStopOk_M` and the removed-symbol list are identical across spec, Task 1, and Task 2.
