# PLC Specification Documentation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** A comprehensive, line-referenced specification of `Centroid-Acroloc-ALLIN1DC.src`, as per-subsystem files in `docs/plc-spec/` linked from `README.md`.

**Architecture:** Nine detail files under `docs/plc-spec/`, each covering one subsystem with `src:NNNN` references pinned to a commit hash; README restructured last into the hub that links to them. No tooling — hand-written Markdown grounded in a full end-to-end read of the source.

**Tech Stack:** Markdown, git, grep. Spec: `docs/superpowers/specs/2026-07-05-plc-spec-doc-design.md`.

## Global Constraints

- Source of truth: `Centroid-Acroloc-ALLIN1DC.src` (~3000 lines) and `mfunc*.mac` at the pinned commit. Never trust memory or other docs over the source; read the actual lines before describing them.
- Every code reference written as `` `Name` (src:NNNN) ``; each detail file's header carries `Line numbers as of commit <sha>` where `<sha>` = `git rev-parse --short HEAD` at the time the file is written (all files should end up pinned to the same sha; if an intermediate commit touches the `.src`, re-pin).
- Cite the stable `; Acroloc` comment markers alongside line numbers wherever they exist.
- Do not edit `Centroid-Acroloc-ALLIN1DC.src`, `plc.map`, or any `.mac` file — this is a documentation-only effort.
- Exclude `docs/official/` from all `git add` commands (`git add -A ':!docs/official'` or add paths explicitly).
- Known gaps / `;TODO`s consolidated at the bottom of each relevant detail file.
- Commit trailer on every commit: `Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>`.
- "Test" for this plan = verification commands: grep-check that every cited line number matches the quoted symbol/text at the pinned commit, and that every relative link resolves.

---

### Task 1: Scaffold + scan-model.md

**Files:**
- Create: `docs/plc-spec/scan-model.md`

**Interfaces:**
- Produces: `docs/plc-spec/` directory and the execution-model file every later file links to as `scan-model.md`. Section anchors later files may cite: `#stage-sweep`, `#timers`, `#snapshot-semantics`, `#last-write-wins`.

- [ ] **Step 1: Pin the commit and confirm source size**

Run: `git rev-parse --short HEAD && wc -l Centroid-Acroloc-ALLIN1DC.src`
Record the sha — it goes in every file header as `Line numbers as of commit <sha>`.

- [ ] **Step 2: Write `docs/plc-spec/scan-model.md`**

Header: title, one-line purpose, `Line numbers as of commit <sha>`.
Sections (each grounded in observable source constructs, with at least one example line reference from the `.src`):
- `## Stage sweep` — flat scan of `STG`-numbered stages top to bottom; a stage's rungs run only while the stage is SET; `SET`/`RST Stage` take effect for the *next* time that stage is reached (a stage SET by an earlier stage in file order runs the same scan — cite MainStage STG4 setting GearShiftStage STG17 as the example).
- `## Snapshot semantics` — INPUTs and timer booleans are frozen per scan; a timer armed this scan reads false this scan.
- `## Timers` — count UP; `T = value` loads the preset, `SET T` arms, bare `T` is true at expiry, `RST T` zeroes. Cite one stock timer and one Acroloc timer (`GearCoast_T`).
- `## Last write wins` — multiple writes to the same output in one scan: the last rung in file order wins; no ELSE construct exists.
- `## Naming conventions` — the `_I/_O/_M/_W/_FW/_T/_SV/_C` suffix scheme (mirror CLAUDE.md, but with line examples).

- [ ] **Step 3: Verify line refs**

For every `(src:NNNN)` cited: `sed -n 'NNNNp' Centroid-Acroloc-ALLIN1DC.src` and confirm the line contains the named symbol. Fix any misses.

- [ ] **Step 4: Commit**

```bash
git add docs/plc-spec/scan-model.md
git commit -m "docs(plc-spec): scan/execution model reference"
```

### Task 2: definitions.md (resource atlas)

**Files:**
- Create: `docs/plc-spec/definitions.md`
- Read: `Centroid-Acroloc-ALLIN1DC.src` lines 1–~1212 (all definitions through the stage definitions)

**Interfaces:**
- Consumes: `scan-model.md` (link for suffix conventions).
- Produces: canonical name→resource→line tables that every later file links to instead of redefining symbols. Anchors: `#inputs`, `#outputs`, `#memory-bits`, `#words`, `#timers`, `#system-variables`, `#constants`, `#stages`.

- [ ] **Step 1: Read the definitions half of the source, in order** (Read tool, chunks of ~400 lines, lines 1 through the stage definitions ~1212). Note every `IS` binding, its comment, and whether it carries `; Acroloc`.

- [ ] **Step 2: Write `docs/plc-spec/definitions.md`**

One section per resource class, each a table: `Name | Resource | src line | Acroloc? | Meaning / used by`. "Used by" is a subsystem-file link, not prose (e.g. `[atc.md](atc.md)`). Include:
- the message-constant encoding rule (`value = msgNumber + 256*msgFile`) explained once with the `ATC_Lock_Released_C` example;
- a short "defined but unused" list (e.g. `ATCSpin_T`, `SpinLowRange_I`) — verify unused via `grep -n <name>` showing only the definition line;
- stages table mapping every `IS STGn` to its detail file.

- [ ] **Step 3: Verify**

Spot-check is not enough here: for each table, script-check every row, e.g. extract `(src:NNNN)` + name pairs and confirm with `sed -n 'NNNNp'`. Also `grep -c "; Acroloc"` in the definitions range and confirm every hit appears in a table.

- [ ] **Step 4: Commit**

```bash
git add docs/plc-spec/definitions.md
git commit -m "docs(plc-spec): definitions resource atlas"
```

### Task 3: boot.md

**Files:**
- Create: `docs/plc-spec/boot.md`
- Read: the `WatchDogStage`, `InitialStage`, `LoadParametersStage` bodies (find with `grep -n "WatchDogStage\|InitialStage\|LoadParametersStage" Centroid-Acroloc-ALLIN1DC.src`)

**Interfaces:**
- Consumes: `definitions.md` tables, `scan-model.md`.
- Produces: `boot.md` with anchor `#power-up-defaults` (gear-shift file links to the low-gear init).

- [ ] **Step 1: Read the three stage bodies end to end.**

- [ ] **Step 2: Write `docs/plc-spec/boot.md`** — per stage: what it does, why it exists (watchdog heartbeat, one-scan init, parameter load handshake), rung-by-rung notes for anything non-obvious, line refs. Explicitly document the Acroloc power-up defaults (low clutch out, `EngagedRange_W = DesiredRange_W = SpindleRange_W = 1`) and timer preset loads.

- [ ] **Step 3: Verify line refs** (same `sed -n` check as Task 1 Step 3).

- [ ] **Step 4: Commit**

```bash
git add docs/plc-spec/boot.md
git commit -m "docs(plc-spec): boot stages (watchdog, init, parameter load)"
```

### Task 4: main-stage.md

**Files:**
- Create: `docs/plc-spec/main-stage.md`
- Read: the entire `MainStage` (STG4) body — the largest stage; read it fully, in order, no sampling.

**Interfaces:**
- Consumes: `definitions.md`, `scan-model.md`, `boot.md`.
- Produces: `main-stage.md` with anchors `#gear-decision` and `#atc-kickoff` (linked from `gear-shift.md` / `atc.md`).

- [ ] **Step 1: Read the MainStage body end to end**, marking rung-group boundaries (blank lines / comment banners).

- [ ] **Step 2: Write `docs/plc-spec/main-stage.md`** — one section per rung group, in file order, each with: what it does, why, line range, gotchas. Must cover at minimum: fault aggregation; spindle enable/direction; spindle speed/DAC ratio math and `SpindleRange_W`; override-knob clamp; coolant (mist/flood, mfunc7/8 linkage); clamp (mfunc10/11); the Acroloc gear-shift decision block (`GearBaseSpeed_FW`, hysteresis vs P941±P942, kickoff rung arming `GearCoast_T`) as a summary linking to `gear-shift.md`; the mutual-exclusion clutch interlock; the ATC kickoff + `StopSpinBeforeATC_T` spindle-stop safety + manual carousel unlock as a summary linking to `atc.md`. Where a rung group's *why* is unknowable from source, say "purpose inferred" — do not invent rationale.

- [ ] **Step 3: Verify line refs** (`sed -n` check for every citation).

- [ ] **Step 4: Commit**

```bash
git add docs/plc-spec/main-stage.md
git commit -m "docs(plc-spec): MainStage rung-group reference"
```

### Task 5: atc.md

**Files:**
- Create: `docs/plc-spec/atc.md`
- Read: `ATCStage` (STG16) body, `mfunc6.mac`, and the MainStage ATC blocks; also `.claude/skills/acroloc-s10/reference/atc-flow.md` (prior art to link, not duplicate)
- Modify: `.claude/skills/acroloc-s10/reference/atc-flow.md` (add a pointer to `docs/plc-spec/atc.md` as the line-referenced spec)

**Interfaces:**
- Consumes: `main-stage.md#atc-kickoff`, `definitions.md`.
- Produces: `atc.md` — the authoritative line-referenced ATC spec.

- [ ] **Step 1: Read `ATCStage` and `mfunc6.mac` end to end.**

- [ ] **Step 2: Write `docs/plc-spec/atc.md`** covering: the three-piece flow (macro → MainStage kickoff/safety → ATCStage) with the M94/M95 `/8`, `M107`, `M100 /93016` handshake spelled out; entry safety re-checks; carousel start; `InToolSelect_M` gating and the 5-switch base-16-as-decimal decode (+1/+2/+4/+8/+10) with the tool table; the unconditional match compare and its mid-accumulation timing sensitivity; match/exit sequence. Known gaps section: no carousel timeout (`;TODO`, unused `ATCSpin_T`). Every rung quoted gets a line ref.

- [ ] **Step 3: Add pointer in `atc-flow.md`** — one line under the source-grounding blockquote: `For the fully line-referenced specification see ../../../../docs/plc-spec/atc.md.` (verify the relative path resolves from that file's location).

- [ ] **Step 4: Verify line refs and the relative link.**

- [ ] **Step 5: Commit**

```bash
git add docs/plc-spec/atc.md .claude/skills/acroloc-s10/reference/atc-flow.md
git commit -m "docs(plc-spec): ATC tool-change specification"
```

### Task 6: gear-shift.md

**Files:**
- Create: `docs/plc-spec/gear-shift.md`
- Read: MainStage gear decision block + `GearShiftStage` (STG17) body; `docs/superpowers/specs/2026-06-27-rpm-gear-shift-design.md`; `docs/testing/rpm-gear-shift-test-plan.md`

**Interfaces:**
- Consumes: `main-stage.md#gear-decision`, `definitions.md`, `boot.md#power-up-defaults`.
- Produces: `gear-shift.md` — line-referenced spec of the shipped shift logic.

- [ ] **Step 1: Read the decision block and stage body at the pinned commit** (do not describe from the design spec — the spec records intent; this file records what the source does).

- [ ] **Step 2: Write `docs/plc-spec/gear-shift.md`**: decision (un-overridden S computation, knob clamp dependency, P941±P942 hysteresis, P941≤0 disable rung); kickoff (timer load default 1500 / P943 override, one-shot-by-construction arming); Step A neutral+retarget; Step B engage/finish; mutual-exclusion interlock and `EngagedRange_W = 0` fault semantics; ATC inhibit; power-up default; parameters table (P941/P942/P943 with intended values 1100/100/1500-tuned); open-loop caveats. Link the test plan and the design spec as background.

- [ ] **Step 3: Verify line refs.**

- [ ] **Step 4: Commit**

```bash
git add docs/plc-spec/gear-shift.md
git commit -m "docs(plc-spec): RPM gear-shift specification"
```

### Task 7: jog-and-mpg.md + faults-and-messages.md

**Files:**
- Create: `docs/plc-spec/jog-and-mpg.md`
- Create: `docs/plc-spec/faults-and-messages.md`
- Read: `JogPanelStage`, `MPGStage`, `WirelessMpgStage`, `JogKeys*Stage` bodies; `CheckCycloneStatusStage`, `MiniPLCErrorStage`, `Show*Stage`, `MessageStage` bodies

**Interfaces:**
- Consumes: `definitions.md` (message-constant encoding), `scan-model.md`.
- Produces: the two remaining stage-coverage files; `faults-and-messages.md` anchor `#fault-bits` (linked from `main-stage.md` fault aggregation).

- [ ] **Step 1: Read the jog/MPG stage bodies end to end.** These are mostly stock Centroid; document at rung-*group* level (what each stage handles, key interlocks, line ranges) rather than rung-by-rung — depth goes where the custom code is.

- [ ] **Step 2: Write `docs/plc-spec/jog-and-mpg.md`.**

- [ ] **Step 3: Read the fault/comm/message stage bodies end to end.**

- [ ] **Step 4: Write `docs/plc-spec/faults-and-messages.md`**: Cyclone/fiber comm fault detection, MiniPLC error handling, fault bit → `FaultMsg_W` → Show*/MessageStage display flow, message-constant decode (link definitions.md), how `OtherFault_M` gates operation.

- [ ] **Step 5: Verify line refs in both files.**

- [ ] **Step 6: Commit**

```bash
git add docs/plc-spec/jog-and-mpg.md docs/plc-spec/faults-and-messages.md
git commit -m "docs(plc-spec): jog/MPG and fault/message subsystems"
```

### Task 8: parameters.md

**Files:**
- Create: `docs/plc-spec/parameters.md`

**Interfaces:**
- Consumes: every prior file (parameters cross-link to the subsystem that reads them).
- Produces: single machine-parameter table.

- [ ] **Step 1: Find every parameter read**: `grep -n "SV_MACHINE_PARAMETER" Centroid-Acroloc-ALLIN1DC.src` — list each distinct parameter number and its reading rung(s).

- [ ] **Step 2: Write `docs/plc-spec/parameters.md`**: table `Param | Meaning | Read at (src:NNNN) | Subsystem | Value semantics / intended value`. Include P941/P942/P943 (intended 1100/100/1500-tuned), P65 (low-gear ratio, if read by the PLC — if it's CNC12-side only, say so), and every stock parameter the grep surfaces.

- [ ] **Step 3: Verify** every grep hit appears in the table and every line ref checks out.

- [ ] **Step 4: Commit**

```bash
git add docs/plc-spec/parameters.md
git commit -m "docs(plc-spec): machine parameter reference"
```

### Task 9: README hub restructure + CLAUDE.md rule + coverage check

**Files:**
- Modify: `README.md`
- Modify: `CLAUDE.md`
- Read: all nine `docs/plc-spec/*.md`

**Interfaces:**
- Consumes: all detail files.
- Produces: README "PLC subsystems" hub section; CLAUDE.md maintenance rule.

- [ ] **Step 1: Restructure README**: add a `## PLC subsystems` section — one short paragraph per subsystem (what it is, in a sentence or two) linking to its `docs/plc-spec/` file, ordered: scan model, definitions, boot, MainStage, ATC, gear shift, jog/MPG, faults/messages, parameters. Trim the existing ATC and gear-shift deep-dive prose to summaries that link out; do not delete information that exists nowhere else — move it into the relevant detail file instead.

- [ ] **Step 2: Add the CLAUDE.md maintenance rule** — one sentence in the conventions section: `When changing the PLC source, update the affected docs/plc-spec/ section(s) and their pinned commit hash as part of the change.`

- [ ] **Step 3: Coverage check (spec success criteria)**:
- Every `IS STGn` stage in the source is covered by exactly one detail file (compare the definitions.md stages table against the files).
- Every `; Acroloc` hit in the source (`grep -n "; Acroloc"`) is described somewhere in `docs/plc-spec/` — script the cross-check, don't eyeball.
- Every relative link in README and all detail files resolves (check each target path exists).

- [ ] **Step 4: Commit**

```bash
git add README.md CLAUDE.md
git commit -m "docs: README PLC-subsystem hub + plc-spec maintenance rule"
```
