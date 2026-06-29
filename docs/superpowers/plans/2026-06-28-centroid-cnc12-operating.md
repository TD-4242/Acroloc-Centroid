# centroid-cnc12-operating Skill Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the in-repo `centroid-cnc12-operating` skill — a `SKILL.md` router plus five `reference/*.md` files capturing how to operate CNC12, transcribed faithfully from the operator manual (Ch 1–7).

**Architecture:** This is a documentation-extraction task, not a code task. Each reference file is built by reading a fixed PDF page range and transcribing the textual content (keystrokes, softkey paths, field names, menu values, procedures) into Markdown that mirrors the manual's structure. Because there is no test runner, the per-task quality gate is a **verification step**: a grep that must return no machine-specific (Acroloc) terms, plus a spot-check that softkey paths and manual page citations are present. The `SKILL.md` router is built last because its router table and "essentials" reference the finished files.

**Tech Stack:** Markdown only. Source PDF: `/home/bwarner/centroid-cnc12-mill-operator-manual.pdf` (54.5 MB, 506 pages). Read with the Read tool's `pages` parameter, **max 20 pages per call**.

## Global Constraints

- **Source PDF:** `/home/bwarner/centroid-cnc12-mill-operator-manual.pdf`. Read only the page ranges listed per task. Max 20 pages per Read call.
- **Page mapping:** document page N = **PDF page N+1**. Cite the *document* page number in the text (what the reader sees), e.g. "(p.42)".
- **Generic only:** zero machine-specific content. No references to Acroloc, this repo's I/O map, the ATC carousel, clutch outputs, or gear-shift work. The verification grep `-iE "acroloc|carousel|atcstage|gearshift|clutch"` must return nothing.
- **Domain boundary:** operating the control only. For G/M-code language defer to `centroid-cnc12-gmcodes`; for Intercon/probing/digitizing defer to `centroid-cnc12-intercon-probing`; for configuration/parameters/errors defer to `centroid-cnc12-config`. Name these siblings; do not include their content.
- **Fidelity:** transcribe keystrokes, softkey paths (`F1 Setup → F3 Config`), field names, and menu values verbatim. Screenshots are cited by document page number, never reproduced.
- **Skill location:** `.claude/skills/centroid-cnc12-operating/`.
- **Style:** match the existing `.claude/skills/centroid-allin1dc-install/` skill — a top-of-file one-line purpose + `Source:` line citing chapters, `##` sections per manual topic, Markdown tables for value/key maps, `>` blocks for DANGER/WARNING/NOTICE callouts.
- **Commits:** end every commit message with `Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>`.
- **Branch:** work on `skill/centroid-cnc12-operating` (already created; the design spec is already committed there).

---

### Task 1: `reference/interface.md` (Ch 1 + Ch 3)

**Files:**
- Create: `.claude/skills/centroid-cnc12-operating/reference/interface.md`
- Source: PDF pages **11–18** (Ch 1, doc 10–17) and **41–48** (Ch 3, doc 40–47)

**Interfaces:**
- Produces: the canonical description of the screen layout and the F1–F10 main-screen menu map. Tasks 3–5 cross-reference softkey paths that originate here (e.g. `F1 Setup`, `F4 Run`, `F7 Utility`). `SKILL.md` (Task 6) summarizes this file in its "essentials".

- [ ] **Step 1: Read the source pages**

Read PDF pages 11–18, then 41–48 (two Read calls). Identify every numbered subsection.

- [ ] **Step 2: Write the reference file**

Create `.claude/skills/centroid-cnc12-operating/reference/interface.md`. Open with a one-line purpose and a `Source: operator manual Ch 1, Ch 3.` line. Transcribe, as `##` sections:

- **From Ch 1:** DRO Display (1.1); Distance-to-Go DRO (1.2); Status Window (1.3); Message Window (1.4); Options Window (1.5); User Window (1.6); Conventions (1.7 — keystroke/softkey notation used throughout the manual); Machine Home (1.8); Mill M- and G-codes (1.9 — capture as a brief *index/overview* only, then point to `centroid-cnc12-gmcodes` for the language reference); How to Unlock Software Features or Unlock Your Control (1.10); Centroid API (1.11); CNC12 with multiple displays (1.12).
- **From Ch 3:** one `## F1–F10 main-screen menu map` section with a table: each row = F-key, menu name, one-line purpose, and (for menus owned by sibling skills) a "see X skill" note. Rows: F1 Setup (3.1), F2 Load Job (3.2), F3 MDI (3.3), F4 Run (3.4), F5 CAM (3.5), F6 Edit (3.6), F7 Utility (3.7), F8 Graph (3.8), F9 Digitize (3.9 → note `centroid-cnc12-intercon-probing`), F10 Shutdown (3.10). Then a short subsection per F-key expanding the manual's description.

Cite document page numbers for any screenshot referenced.

- [ ] **Step 3: Verify**

```bash
grep -riE "acroloc|carousel|atcstage|gearshift|clutch" .claude/skills/centroid-cnc12-operating/reference/interface.md
```
Expected: no output (exit 1). Then confirm by eye: the F1–F10 table has all ten rows, the Machine Home and Conventions sections are present, and 1.9 defers to the gmcodes skill rather than listing G-codes.

- [ ] **Step 4: Commit**

```bash
git add .claude/skills/centroid-cnc12-operating/reference/interface.md
git commit -m "feat(skill): add interface reference for centroid-cnc12-operating

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

### Task 2: `reference/operator-panel.md` (Ch 2)

**Files:**
- Create: `.claude/skills/centroid-cnc12-operating/reference/operator-panel.md`
- Source: PDF pages **19–40** (Ch 2, doc 18–39)

**Interfaces:**
- Consumes: keystroke/softkey notation conventions defined in `interface.md` (Task 1).
- Produces: the jog/MPG/VCP/keyboard-shortcut reference. `SKILL.md` (Task 6) lists it in the router.

- [ ] **Step 1: Read the source pages**

Read PDF pages 19–38, then 39–40 (two Read calls — the range exceeds 20 pages).

- [ ] **Step 2: Write the reference file**

Create `.claude/skills/centroid-cnc12-operating/reference/operator-panel.md` with a one-line purpose and `Source: operator manual Ch 2.`. Transcribe as `##`/`###` sections, preserving the manual's button names verbatim:

- Axis Jog Buttons (2.1); Slow/Fast (2.2); Inc/Cont (2.3); x1, x10, x100 (2.4); MPG (2.5); Single Block (2.6); Cycle Start (2.7); Feed Rate Override (2.8); Feed Hold (2.9); Tool Check (2.10); Cycle Cancel (2.11); Emergency Stop (2.12); Spindle CW/CCW (2.13); Spindle Speed +/100%/− (2.14–2.16); Spindle Auto/Man (2.17); Spin Start/Stop (2.18–2.19); Coolant Auto/Manual (2.20); Coolant Flood (2.21); Coolant Mist (2.22); Auxiliary Function Keys AUX1–AUX12 (2.23); Notes About Operator Panels (2.24).
- **VCP Introduction (2.25)** — the Virtual Control Panel.
- **Keyboard Jog Panel (2.26)** — capture the full key map as a table.
- **MDI and the Keyboard Jog Panel (2.27)**.
- **Keyboard Shortcut Keys (2.28)** — capture as a table (key → action).

- [ ] **Step 3: Verify**

```bash
grep -riE "acroloc|carousel|atcstage|gearshift|clutch" .claude/skills/centroid-cnc12-operating/reference/operator-panel.md
```
Expected: no output. Spot-check: the Keyboard Jog Panel (2.26) and Keyboard Shortcut Keys (2.28) are rendered as tables, and all spindle/coolant/feed-override controls are present.

- [ ] **Step 4: Commit**

```bash
git add .claude/skills/centroid-cnc12-operating/reference/operator-panel.md
git commit -m "feat(skill): add operator-panel reference for centroid-cnc12-operating

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

### Task 3: `reference/part-setup.md` (Ch 4)

**Files:**
- Create: `.claude/skills/centroid-cnc12-operating/reference/part-setup.md`
- Source: PDF pages **49–59** (Ch 4, doc 48–58)

**Interfaces:**
- Consumes: `F1 Setup` softkey path defined in `interface.md` (Task 1).
- Produces: the part-setup / WCS / CSR / TWCS reference. Listed in the `SKILL.md` router (Task 6).

- [ ] **Step 1: Read the source pages**

Read PDF pages 49–59 (one Read call, 11 pages).

- [ ] **Step 2: Write the reference file**

Create `.claude/skills/centroid-cnc12-operating/reference/part-setup.md` with a one-line purpose and `Source: operator manual Ch 4.`. Transcribe as `##` sections:

- Operation Description (4.1) — the F1 Setup → F1 Part workflow, the fields and what each does.
- Part Setup Examples (4.2) — capture each worked example's steps verbatim.
- Work Coordinate Systems (WCS) Configuration (4.3) — G54–G59 etc. as it relates to *setup* (not the G-code definition, which is gmcodes); the configuration screen and fields.
- Coordinate System Rotation (CSR) (4.4).
- Transformed WCS (TWCS=Yes) (4.5).

- [ ] **Step 3: Verify**

```bash
grep -riE "acroloc|carousel|atcstage|gearshift|clutch" .claude/skills/centroid-cnc12-operating/reference/part-setup.md
```
Expected: no output. Spot-check: WCS, CSR, and TWCS each have a section, and the F1 Setup → F1 Part path matches `interface.md`.

- [ ] **Step 4: Commit**

```bash
git add .claude/skills/centroid-cnc12-operating/reference/part-setup.md
git commit -m "feat(skill): add part-setup reference for centroid-cnc12-operating

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

### Task 4: `reference/tool-setup.md` (Ch 5)

**Files:**
- Create: `.claude/skills/centroid-cnc12-operating/reference/tool-setup.md`
- Source: PDF pages **60–77** (Ch 5, doc 59–76)

**Interfaces:**
- Consumes: `F1 Setup` softkey path from `interface.md` (Task 1).
- Produces: the offset-library / tool-library / tool-life / laser-setup reference. Listed in the `SKILL.md` router (Task 6).

- [ ] **Step 1: Read the source pages**

Read PDF pages 60–77 in two Read calls (e.g. 60–76 then 77, or 60–69 then 70–77).

- [ ] **Step 2: Write the reference file**

Create `.claude/skills/centroid-cnc12-operating/reference/tool-setup.md` with a one-line purpose and `Source: operator manual Ch 5.`. Transcribe as `##` sections:

- Offset Library (5.1) — the offsets table screen, fields, how to set tool length/diameter offsets.
- Tool Library (5.2).
- Tool Life Management Menu (5.3).
- Laser Setup (5.4) — the operator-facing setup steps (cite page numbers for diagrams/screenshots).

- [ ] **Step 3: Verify**

```bash
grep -riE "acroloc|carousel|atcstage|gearshift|clutch" .claude/skills/centroid-cnc12-operating/reference/tool-setup.md
```
Expected: no output. Spot-check: all four sections present; offset vs tool library distinction is clear.

- [ ] **Step 4: Commit**

```bash
git add .claude/skills/centroid-cnc12-operating/reference/tool-setup.md
git commit -m "feat(skill): add tool-setup reference for centroid-cnc12-operating

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

### Task 5: `reference/running-jobs.md` (Ch 6 + Ch 7)

**Files:**
- Create: `.claude/skills/centroid-cnc12-operating/reference/running-jobs.md`
- Source: PDF pages **78–83** (Ch 6, doc 77–82) and **84–86** (Ch 7, doc 83–85)

**Interfaces:**
- Consumes: `F4 Run` and `F7 Utility` softkey paths from `interface.md` (Task 1).
- Produces: the run / graphics / cancel-resume / utility-menu reference. Listed in the `SKILL.md` router (Task 6).

- [ ] **Step 1: Read the source pages**

Read PDF pages 78–86 (one Read call, 9 pages).

- [ ] **Step 2: Write the reference file**

Create `.claude/skills/centroid-cnc12-operating/reference/running-jobs.md` with a one-line purpose and `Source: operator manual Ch 6, Ch 7.`. Transcribe as `##` sections:

- Active Job Run Screen with G-code Display (6.1).
- Run-time Graphics Screen (6.2).
- Canceling a Job in Progress (6.3).
- Resuming a Canceled Job (6.4) — capture the resume procedure step-by-step.
- Run Menu (6.5).
- Power Feed (6.6).
- Communications Stress Test (6.7).
- **The Utility Menu (Ch 7)** — one `## Utility menu (F7)` section enumerating the utility softkeys and what each does; for any item that is purely configuration/diagnostics owned by skill D, name it and defer.

- [ ] **Step 3: Verify**

```bash
grep -riE "acroloc|carousel|atcstage|gearshift|clutch" .claude/skills/centroid-cnc12-operating/reference/running-jobs.md
```
Expected: no output. Spot-check: the resume-a-canceled-job procedure is present and stepwise; the utility-menu section enumerates softkeys.

- [ ] **Step 4: Commit**

```bash
git add .claude/skills/centroid-cnc12-operating/reference/running-jobs.md
git commit -m "feat(skill): add running-jobs reference for centroid-cnc12-operating

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

### Task 6: `SKILL.md` router

**Files:**
- Create: `.claude/skills/centroid-cnc12-operating/SKILL.md`
- Source: the five reference files (Tasks 1–5) + PDF pages for Ch 17 (Additional Resources) if needed for the resources footer (doc 446 → PDF 447).

**Interfaces:**
- Consumes: the five `reference/*.md` files and the `interface.md` F1–F10 map.
- Produces: the skill entry point. This completes the skill.

- [ ] **Step 1: Read the model skill**

Read `.claude/skills/centroid-allin1dc-install/SKILL.md` to match its frontmatter shape, section order, and router-table style.

- [ ] **Step 2: Write SKILL.md**

Create `.claude/skills/centroid-cnc12-operating/SKILL.md` with:

- **Frontmatter:** `name: centroid-cnc12-operating` and a `description` that triggers on operating questions (jogging, operator panel/MPG/VCP, the F-key menus, part setup, tool setup, running/canceling/resuming a job) and explicitly states it is NOT for G/M-code language, Intercon/probing/digitizing, or configuration/parameters/errors.
- **When to use / when not:** route G/M-code → `centroid-cnc12-gmcodes`; Intercon/probing/digitizing → `centroid-cnc12-intercon-probing`; config/parameters/errors → `centroid-cnc12-config` (note these siblings may not exist yet). Also note `.src`/macro work → `centroid-plc-programming`.
- **Essentials:** a short orientation — DRO/status/message windows, the F1–F10 layout, machine home — summarized from `interface.md`.
- **Reference router table:** five rows, one per reference file, each with a one-line "use this when…".

  | Reference | Use when the question is about |
  | --- | --- |
  | `reference/interface.md` | screen layout, DRO, conventions, machine home, the F1–F10 menu map |
  | `reference/operator-panel.md` | jogging, MPG, spindle/coolant/feed controls, VCP, keyboard jog & shortcuts |
  | `reference/part-setup.md` | part zero, WCS, coordinate-system rotation, transformed WCS |
  | `reference/tool-setup.md` | offset library, tool library, tool-life management, laser setup |
  | `reference/running-jobs.md` | running, canceling, resuming jobs; run-time graphics; power feed; utility menu |

- **Useful resources:** the URLs from the manual (forum `https://centroidcnc.com`, the operator-manual download URL on the cover page, `https://centroidcncforum.com/`) captured verbatim.

- [ ] **Step 3: Verify**

```bash
grep -riE "acroloc|carousel|atcstage|gearshift|clutch" .claude/skills/centroid-cnc12-operating/SKILL.md
ls .claude/skills/centroid-cnc12-operating/reference/
```
Expected: grep no output; `ls` shows exactly `interface.md`, `operator-panel.md`, `part-setup.md`, `running-jobs.md`, `tool-setup.md`. Confirm frontmatter has `name:` and `description:`, and the router table has all five rows.

- [ ] **Step 4: Commit**

```bash
git add .claude/skills/centroid-cnc12-operating/SKILL.md
git commit -m "feat(skill): add SKILL.md router for centroid-cnc12-operating

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

## Final verification (after Task 6)

- [ ] Whole-skill grep is clean:

```bash
grep -riE "acroloc|carousel|atcstage|gearshift|clutch" .claude/skills/centroid-cnc12-operating/
```
Expected: no output.

- [ ] Structure check:

```bash
find .claude/skills/centroid-cnc12-operating -type f | sort
```
Expected: `SKILL.md` plus the five `reference/*.md` files.

- [ ] Spot-check that each reference file cites at least one document page number and uses the `F1 Setup → …` softkey-path style consistent with `interface.md`.
