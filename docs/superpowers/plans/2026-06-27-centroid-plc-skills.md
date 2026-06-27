# Centroid PLC Skills Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build two in-repo Claude Code skills — a reusable `centroid-plc-programming` reference and a machine-specific `acroloc-atc` navigator — so Claude has instant, source-grounded reference when working on this Centroid CNC12 / MPU11 PLC program and its M-code macros.

**Architecture:** Skill files are markdown (`SKILL.md` + `reference/*.md`) under `.claude/skills/`. The general skill's facts are extracted from `docs/official/centroid_plc_programming_manual.pdf` and cross-checked against the bundled example `.src`/`.sym` files. The machine skill links to `README.md`/`CLAUDE.md`/the general skill instead of duplicating prose.

**Tech Stack:** Markdown with YAML frontmatter (Claude Code skill format). `pdftotext` for PDF extraction; `grep`/`find` for cross-checking; the Read tool's `pages` param for PDF tables/figures. No build or test runner exists in this repo.

## Global Constraints

- **No automated tests exist.** "Verify" = fact-check claims against the PDF manual and example `.src`/`.sym` files, plus frontmatter/format lint. Never claim a fact came from the manual without having read the relevant page or grepped the extraction.
- **Skill frontmatter is mandatory** on every `SKILL.md`: YAML block with `name` (must equal the skill's directory name, kebab-case) and `description` (one line, written in third person describing *when* to use the skill). Keep `description` under ~500 chars.
- **No duplication** of `README.md` / `CLAUDE.md` prose anywhere in the skills — link to them instead.
- **Accuracy over completeness.** Do not invent system-variable names, values, or operators from memory. If a fact cannot be confirmed in the PDF or example code, omit it or mark it explicitly as unverified.
- **Match source naming verbatim.** Symbol names (`SV_*`, resource keywords) must match the casing used in the example `.src`/`.sym` files.
- All work happens on branch `skill/centroid-plc-skills` (already created). Commit after each task.
- Both skills live under `.claude/skills/` in this repo.

---

## File Structure

Created files:

```
.claude/skills/
  centroid-plc-programming/
    SKILL.md
    reference/
      syntax.md
      resources.md
      system-variables.md
      messages.md
      examples-index.md
  acroloc-atc/
    SKILL.md
    reference/
      atc-flow.md
      macros.md
```

Scratch (not committed): `scratchpad/plc-manual.txt` — full `pdftotext` extraction of the programming manual, used as a grep-able source while writing the general skill.

---

## Task 1: Scaffold both skills with valid frontmatter

**Files:**
- Create: `.claude/skills/centroid-plc-programming/SKILL.md`
- Create: `.claude/skills/acroloc-atc/SKILL.md`

**Interfaces:**
- Produces: two skill directories and `SKILL.md` files with final frontmatter. The `name`/`description` strings defined here are referenced by no other task but must remain stable. Bodies are placeholder-free stubs that later tasks (7, 10) finalize.

- [ ] **Step 1: Create the directory tree**

```bash
cd /home/bwarner/github/Acroloc-Centroid
mkdir -p .claude/skills/centroid-plc-programming/reference
mkdir -p .claude/skills/acroloc-atc/reference
```

- [ ] **Step 2: Write `centroid-plc-programming/SKILL.md` stub with final frontmatter**

```markdown
---
name: centroid-plc-programming
description: Use when writing, reading, or debugging Centroid CNC12 / MPU11 (ALLIN1DC) PLC stage-language source (.src) or M-code macros (mfunc*.mac) — covers stage/ladder syntax, resource types (INP/OUT/MEM/W/T/STG), the SV_* system-variable catalog, operator-message encoding, and an index of official example PLC projects to crib from.
---

# Centroid PLC Programming

> Reference skill. The router and language essentials are filled in by Task 7.

## Reference files

- `reference/syntax.md` — statement forms, operators, scan/stage model
- `reference/resources.md` — resource types, addressing, macro↔PLC access
- `reference/system-variables.md` — SV_* catalog
- `reference/messages.md` — operator-message constant encoding
- `reference/examples-index.md` — index of official example projects
```

- [ ] **Step 3: Write `acroloc-atc/SKILL.md` stub with final frontmatter**

```markdown
---
name: acroloc-atc
description: Use when editing or understanding this repo's Centroid-Acroloc-ALLIN1DC.src or mfunc*.mac — especially the custom Acroloc automatic tool changer (carousel), tool-change M6 flow, spindle two-speed range logic, or any code tagged "; Acroloc". Points to the general centroid-plc-programming skill for language reference.
---

# Acroloc ATC (this machine)

> Machine navigator. Orientation, custom-I/O table, and task playbooks are filled in by Task 10.

## Reference files

- `reference/atc-flow.md` — the M6 tool-change state machine and carousel encoding
- `reference/macros.md` — mfunc*.mac quick reference
```

- [ ] **Step 4: Verify frontmatter is well-formed and `name` matches directory**

```bash
for f in .claude/skills/centroid-plc-programming/SKILL.md .claude/skills/acroloc-atc/SKILL.md; do
  echo "== $f =="
  awk 'NR==1&&$0!="---"{print "FAIL: no opening ---"; exit} /^---$/{c++} c==1&&/^name:/{print} c==1&&/^description:/{print "has description"} c==2{exit}' "$f"
done
```
Expected: each file prints a `name:` line whose value equals its parent directory name, and `has description`.

- [ ] **Step 5: Commit**

```bash
git add .claude/skills/
git commit -m "feat: scaffold centroid-plc-programming and acroloc-atc skills"
```

---

## Task 2: Extract the programming manual to grep-able text

**Files:**
- Create: `scratchpad/plc-manual.txt` (NOT committed)

**Interfaces:**
- Produces: `scratchpad/plc-manual.txt`, the plain-text extraction every later general-skill task greps against. Path is referenced by Tasks 3–6.

- [ ] **Step 1: Extract the PDF to text**

```bash
cd /home/bwarner/github/Acroloc-Centroid
pdftotext -layout docs/official/centroid_plc_programming_manual.pdf scratchpad/plc-manual.txt
wc -l scratchpad/plc-manual.txt
```
Expected: a multi-thousand-line text file (non-zero line count).

- [ ] **Step 2: Sanity-check the extraction is readable, not garbled**

```bash
grep -n -i -m1 "stage" scratchpad/plc-manual.txt
grep -n -i -m1 "system variable" scratchpad/plc-manual.txt
```
Expected: both return matching line numbers with legible surrounding text. If output is garbled, fall back to reading the PDF directly with the Read tool's `pages` param in later tasks and note it.

- [ ] **Step 3: No commit** (scratch file only). Proceed to Task 3.

---

## Task 3: Write `reference/syntax.md`

**Files:**
- Create: `.claude/skills/centroid-plc-programming/reference/syntax.md`
- Source: `scratchpad/plc-manual.txt`; cross-check `docs/official/_ALLIN1DC/_basic/cncm/allin1dc-basic-v6.src`

**Interfaces:**
- Consumes: `scratchpad/plc-manual.txt` (Task 2).
- Produces: `reference/syntax.md` documenting statement forms and operators. Task 7's inline "language essentials" summarizes this; keep terminology consistent (`stage`, `scan`, `SET`/`RST`).

- [ ] **Step 1: Gather the syntax facts from the manual**

```bash
grep -n -i -E "IF|THEN|\bSET\b|\bRST\b|operator|stage|scan|true|false" scratchpad/plc-manual.txt | head -80
```
Then read the relevant PDF pages for any table that didn't extract cleanly:
Use the Read tool on `docs/official/centroid_plc_programming_manual.pdf` with the `pages` range covering the syntax/operators chapter identified above.

- [ ] **Step 2: Confirm each operator/keyword against real code**

```bash
grep -n -E "IF .* THEN|SET |RST |&&|\|\||!" docs/official/_ALLIN1DC/_basic/cncm/allin1dc-basic-v6.src | head -40
```
Expected: the operators you plan to document actually appear in working source. Drop any you cannot confirm in either the manual or example code.

- [ ] **Step 3: Write `reference/syntax.md`**

Required sections (fill from Steps 1–2, do not invent):
- **Execution model** — the program is a flat per-scan sweep of `STG`-numbered stages; a stage's logic runs only while the stage is SET; stages enable/disable each other with `SET`/`RST`.
- **Statement forms** — `Name IS Resource` binding; `IF <condition> THEN <action>, <action>, ...`; assignment to words; bare actions.
- **Operators** — logical (`&&`, `||`, `!`), relational/comparison, and arithmetic actually documented/used. One row per operator: symbol, meaning, example line copied from source.
- **Conditions vs. actions** — what may appear before vs. after `THEN`.
- **Comments** — `;` to end of line; the fixed-column comment style convention.

Every code example must be a real line cited from the manual or an example `.src` (note which).

- [ ] **Step 4: Verify no placeholders and every claimed operator is grep-confirmable**

```bash
grep -n -i -E "TODO|TBD|FIXME|\.\.\." .claude/skills/centroid-plc-programming/reference/syntax.md || echo "clean"
```
Expected: `clean`. Manually confirm each operator row has a real example.

- [ ] **Step 5: Commit**

```bash
git add .claude/skills/centroid-plc-programming/reference/syntax.md
git commit -m "docs(skill): add Centroid PLC syntax reference"
```

---

## Task 4: Write `reference/resources.md`

**Files:**
- Create: `.claude/skills/centroid-plc-programming/reference/resources.md`
- Source: `scratchpad/plc-manual.txt`; cross-check any example `.src` definitions section and `mfunc*.mac` in repo root.

**Interfaces:**
- Consumes: `scratchpad/plc-manual.txt` (Task 2).
- Produces: `reference/resources.md`. Defines the suffix convention reused by `acroloc-atc` (Task 10) and the macro↔PLC access rules used in `acroloc-atc/reference/macros.md` (Task 9).

- [ ] **Step 1: Gather resource-type facts**

```bash
grep -n -i -E "\bINP\b|\bOUT\b|\bMEM\b|\bSTG\b|timer|\bWORD\b|resource| IS " scratchpad/plc-manual.txt | head -80
```
Read the resource-types chapter pages with the Read tool if tables are garbled.

- [ ] **Step 2: Confirm addressing against real definitions**

```bash
grep -n -E " IS (INP|OUT|MEM|W|T|STG|FW)[0-9]" docs/official/_ALLIN1DC/_basic/cncm/allin1dc-basic-v6.src | head -30
grep -n -E "#\(60000|M94 |M95 " /home/bwarner/github/Acroloc-Centroid/mfunc6.mac
```
Expected: resource keywords and the macro access patterns appear in real code.

- [ ] **Step 3: Write `reference/resources.md`**

Required sections (fill from Steps 1–2):
- **Resource types table** — `INP` (input bit), `OUT` (output bit), `MEM` (memory bit), `W` (32-bit word), `T` (timer), `STG` (stage), `FW` (float word) — keyword, what it is, addressing form (`INP32`, `W71`, `STG16`, …).
- **Naming-suffix convention** — `_I/_O/_M/_W/_T/_SV/_C` and what each maps to. State this is a Centroid convention seen across the example sources.
- **Macro ↔ PLC access** — read a PLC `OUT`/`MEM` bit `n` from a macro as `#(60000 + n)` (e.g. `OUT1058` → `#61058`); trigger M-functions with `M94 /bit` (set) and `M95 /bit` (reset). Cite the real lines from `mfunc6.mac`.

- [ ] **Step 4: Verify**

```bash
grep -n -i -E "TODO|TBD|FIXME|\.\.\." .claude/skills/centroid-plc-programming/reference/resources.md || echo "clean"
```
Expected: `clean`.

- [ ] **Step 5: Commit**

```bash
git add .claude/skills/centroid-plc-programming/reference/resources.md
git commit -m "docs(skill): add Centroid PLC resource-types reference"
```

---

## Task 5: Write `reference/system-variables.md`

**Files:**
- Create: `.claude/skills/centroid-plc-programming/reference/system-variables.md`
- Source: `scratchpad/plc-manual.txt`; cross-check `.sym` files and example `.src`.

**Interfaces:**
- Consumes: `scratchpad/plc-manual.txt` (Task 2).
- Produces: `reference/system-variables.md` — the `SV_*` catalog. Names must match what the example code uses verbatim.

- [ ] **Step 1: Enumerate SV_* names actually used in real code**

```bash
cd /home/bwarner/github/Acroloc-Centroid
grep -rhoE "SV_[A-Z0-9_]+" docs/official/_ALLIN1DC --include=*.src | sort -u > scratchpad/sv-names.txt
grep -hoE "SV_[A-Z0-9_]+" Centroid-Acroloc-ALLIN1DC.src | sort -u >> scratchpad/sv-names.txt
sort -u -o scratchpad/sv-names.txt scratchpad/sv-names.txt
wc -l scratchpad/sv-names.txt
```
Expected: a deduplicated list of every `SV_*` name that appears in working source.

- [ ] **Step 2: Pull each variable's documented meaning from the manual**

```bash
while read sv; do echo "== $sv =="; grep -n -m1 -i "$sv" scratchpad/plc-manual.txt; done < scratchpad/sv-names.txt | head -120
```
For variables found in the manual, capture the documented meaning. For variables used in code but absent from the manual, infer the role from usage context and mark them `(from code usage)`.

- [ ] **Step 3: Write `reference/system-variables.md`**

Group the catalog by function with a table per group: **Spindle**, **Tool / tool-change** (incl. `SV_M94_M95_*` flags), **Jog / MPG**, **Coolant**, **Machine parameters** (`SV_MACHINE_PARAMETER_*`, `SV_PC_CONFIG_*`), **Misc/system**. Columns: `SV_ name` | meaning | source (`manual` / `from code usage`). Only include names present in `scratchpad/sv-names.txt`.

- [ ] **Step 4: Verify every catalog entry exists in real source**

```bash
grep -oE "SV_[A-Z0-9_]+" .claude/skills/centroid-plc-programming/reference/system-variables.md | sort -u > scratchpad/sv-in-doc.txt
comm -23 scratchpad/sv-in-doc.txt scratchpad/sv-names.txt
```
Expected: **empty output** (no documented variable is absent from real source — i.e. nothing invented). Also run the placeholder grep:
```bash
grep -n -i -E "TODO|TBD|FIXME" .claude/skills/centroid-plc-programming/reference/system-variables.md || echo "clean"
```
Expected: `clean`.

- [ ] **Step 5: Commit**

```bash
git add .claude/skills/centroid-plc-programming/reference/system-variables.md
git commit -m "docs(skill): add Centroid SV_* system-variable catalog"
```

---

## Task 6: Write `reference/messages.md` and `reference/examples-index.md`

**Files:**
- Create: `.claude/skills/centroid-plc-programming/reference/messages.md`
- Create: `.claude/skills/centroid-plc-programming/reference/examples-index.md`
- Source: `scratchpad/plc-manual.txt`; example `plcmsg.txt` files; example `.src` header comments.

**Interfaces:**
- Consumes: `scratchpad/plc-manual.txt` (Task 2).
- Produces: both reference files. `examples-index.md` paths are linked from `SKILL.md` (Task 7).

- [ ] **Step 1: Confirm the message-constant encoding**

```bash
cd /home/bwarner/github/Acroloc-Centroid
grep -n -i -E "256 *\*|msgfile|message file|plcmsg" scratchpad/plc-manual.txt | head
grep -n -E "_C IS [0-9]+ *;\(" Centroid-Acroloc-ALLIN1DC.src | head
head -20 docs/official/_ALLIN1DC/_basic/cncm/plcmsg.txt
```
Expected: confirms `value = msgNumber + 256 * msgFile` and shows the `plcmsg.txt` line format.

- [ ] **Step 2: Write `reference/messages.md`**

Sections: the encoding formula with the worked example `ATC_Lock_Released_C IS 45546 ;(2+256*174)` → message #2 in file 174; the `plcmsg.txt` format (one entry per line, keyed by file+number); and how a `_C` constant is referenced in stage logic to post an operator message. Cite real lines.

- [ ] **Step 3: Gather one-line summaries for every example project**

```bash
for f in $(find docs/official/_ALLIN1DC -name '*.src' | sort); do
  echo "=== $f ==="; sed -n '1,30p' "$f" | grep -i -E "purpose|atc|umbrella|swingarm|brake|reverse|remote|spindle|router|boss|dm45|handbrake|throwaway"
done
```
Expected: each project's header reveals what it demonstrates.

- [ ] **Step 4: Write `reference/examples-index.md`**

A table: **path** (relative, clickable) | **what it demonstrates** (one line). Cover every `.src` found by `find docs/official/_ALLIN1DC -name '*.src'` — basic, basicVCPMpgBeta, BOSSVCPMpgBeta, umbrella ATC, umbrella no-throwaway, 3rd-axis brake, remote start, low-range reverse, MSC handbrake, spindle brake, bp-boss (+analog), cptools, dm45, forest-scientific ATC router, and the k100075/k100113(h+v)/k100242/k100374 custom builds. Add a one-line lead-in: "When implementing a feature, find the closest official example here and crib its proven pattern."

- [ ] **Step 5: Verify coverage and no placeholders**

```bash
# every src path present in the index?
for f in $(find docs/official/_ALLIN1DC -name '*.src' | sort); do
  grep -q "$f" .claude/skills/centroid-plc-programming/reference/examples-index.md || echo "MISSING: $f"
done
grep -n -i -E "TODO|TBD|FIXME" .claude/skills/centroid-plc-programming/reference/messages.md .claude/skills/centroid-plc-programming/reference/examples-index.md || echo "clean"
```
Expected: no `MISSING:` lines; `clean`.

- [ ] **Step 6: Commit**

```bash
git add .claude/skills/centroid-plc-programming/reference/messages.md .claude/skills/centroid-plc-programming/reference/examples-index.md
git commit -m "docs(skill): add message-encoding and example-project index references"
```

---

## Task 7: Finalize `centroid-plc-programming/SKILL.md`

**Files:**
- Modify: `.claude/skills/centroid-plc-programming/SKILL.md`

**Interfaces:**
- Consumes: all five `reference/*.md` files (Tasks 3–6) — their filenames and section names.
- Produces: the finished general-skill entry point.

- [ ] **Step 1: Replace the stub body (keep frontmatter from Task 1)**

Write the body with these sections:
- **When to use / when not** — use for any Centroid CNC12 / MPU11 stage-language work; for *this machine's* specifics defer to the `acroloc-atc` skill.
- **Language essentials (inline)** — a tight summary of the scan/stage model, `Name IS Resource`, and `IF <cond> THEN SET/RST <stage>, ...`, consistent with `reference/syntax.md`. ~8–12 lines, no new facts beyond the reference files.
- **Reference router** — a table mapping each `reference/*.md` to "look here when…". One row per file (syntax, resources, system-variables, messages, examples-index).

- [ ] **Step 2: Verify all referenced files exist and links resolve**

```bash
cd /home/bwarner/github/Acroloc-Centroid/.claude/skills/centroid-plc-programming
for ref in reference/syntax.md reference/resources.md reference/system-variables.md reference/messages.md reference/examples-index.md; do
  grep -q "$ref" SKILL.md && test -f "$ref" && echo "OK $ref" || echo "BROKEN $ref"
done
```
Expected: five `OK` lines.

- [ ] **Step 3: Commit**

```bash
git add .claude/skills/centroid-plc-programming/SKILL.md
git commit -m "docs(skill): finalize centroid-plc-programming SKILL.md router"
```

---

## Task 8: Write `acroloc-atc/reference/atc-flow.md`

**Files:**
- Create: `.claude/skills/acroloc-atc/reference/atc-flow.md`
- Source: `Centroid-Acroloc-ALLIN1DC.src`, `mfunc6.mac`, `README.md` (for cross-check only — do not copy prose).

**Interfaces:**
- Produces: the tool-change walkthrough referenced by `acroloc-atc/SKILL.md` (Task 10).

- [ ] **Step 1: Re-read the live source for the three flow locations**

```bash
cd /home/bwarner/github/Acroloc-Centroid
grep -n "; Acroloc" Centroid-Acroloc-ALLIN1DC.src | head -60
grep -n -E "ATCStage|M6_SV|ChangeToTool_W|CarouselToolID_W|ATC_Pos[1-5]_I|ATCMotor_O|ATCUnlocked_O|StopSpinBeforeATC_T|ZeroSpeed_I|ATC_Z_" Centroid-Acroloc-ALLIN1DC.src
```
Read the surrounding lines of `MainStage` and `ATCStage` with the Read tool to get exact behavior and current line numbers.

- [ ] **Step 2: Write `reference/atc-flow.md`**

Sections (grounded in the live `.src`/`.mac`, not the README):
- **Three places the change lives** — `mfunc6.mac` (M6 macro: `S0 M5`, `M9`, `G53 Z0`, `M107`, `M94 /8` … `M95 /8`), `MainStage` kickoff + safety (latch `ChangeToTool_W`, `SET ATCStage`, spindle-stopped via `ZeroSpeed_I`/`StopSpinBeforeATC_T`, Z-parked checks), `ATCStage` (STG16) carousel indexing.
- **Carousel position encoding** — the base-16-written-in-decimal table (`Pos1=+1, Pos2=+2, Pos3=+4, Pos4=+8, Pos5=+10` — note +10 not +16), and how `CarouselToolID_W` accumulates and resets between tools.
- **Match/exit** — on `CarouselToolID_W == ChangeToTool_W`: stop + relock (`RST ATCMotor_O`, `RST ATCUnlocked_O`), `RST M6_SV`, `RST ATCStage`.
- **⚠️ Known gaps** — no carousel timeout (`;TODO` in `ATCStage`): an off-by-one in the decode spins forever; and transmission shift outputs `Spindle_Low_gear_O`/`Spindle_High_gear_O` (`OUT19`/`OUT20`) are defined but never driven.

Reference stages by name (and `; Acroloc` marker), not by hard line numbers, since lines drift.

- [ ] **Step 3: Verify the documented symbols still exist in source**

```bash
for sym in ATCStage M6_SV ChangeToTool_W CarouselToolID_W ATCMotor_O ATCUnlocked_O Spindle_Low_gear_O Spindle_High_gear_O; do
  grep -q "$sym" Centroid-Acroloc-ALLIN1DC.src && echo "OK $sym" || echo "MISSING $sym"
done
grep -n -i -E "TODO|TBD|FIXME" .claude/skills/acroloc-atc/reference/atc-flow.md || echo "clean"
```
Expected: all `OK`; `clean` (the word "TODO" only appears when quoting the source `;TODO` — if so, that match is acceptable; confirm it is the quoted gap note).

- [ ] **Step 4: Commit**

```bash
git add .claude/skills/acroloc-atc/reference/atc-flow.md
git commit -m "docs(skill): add Acroloc ATC tool-change flow reference"
```

---

## Task 9: Write `acroloc-atc/reference/macros.md`

**Files:**
- Create: `.claude/skills/acroloc-atc/reference/macros.md`
- Source: `mfunc3/4/6/7/8/10/11.mac` in repo root.

**Interfaces:**
- Consumes: the macro↔PLC access rules from `centroid-plc-programming/reference/resources.md` (Task 4).
- Produces: the macro quick-reference linked from `acroloc-atc/SKILL.md` (Task 10).

- [ ] **Step 1: Read each macro and its guard**

```bash
cd /home/bwarner/github/Acroloc-Centroid
for m in mfunc3 mfunc4 mfunc6 mfunc7 mfunc8 mfunc10 mfunc11; do
  echo "=== $m.mac ==="; cat "$m.mac"
done | grep -n -E "M9[45]|#420[12]|N1000|GOTO 1000|;|S0|M107|G53" | head -80
```

- [ ] **Step 2: Write `reference/macros.md`**

A table: **macro** | **fires on** | **what it does** (one line). Rows: `mfunc3` spindle CW, `mfunc4` spindle CCW, `mfunc6` M6 tool change (drives the ATC — see `reference/atc-flow.md`), `mfunc7` mist coolant, `mfunc8` flood coolant, `mfunc10` clamp on, `mfunc11` clamp off. Then a **shared guard** note: every macro skips in graph/search mode with `IF #4201 || #4202 THEN GOTO 1000` and ends at `N1000` — preserve this when editing. Link macro↔PLC mechanics to the general skill's `resources.md`.

- [ ] **Step 3: Verify the guard claim holds for every macro**

```bash
for m in mfunc3 mfunc4 mfunc6 mfunc7 mfunc8 mfunc10 mfunc11; do
  grep -q "4201" "$m.mac" && grep -q "1000" "$m.mac" && echo "OK $m" || echo "CHECK $m"
done
grep -n -i -E "TODO|TBD|FIXME" .claude/skills/acroloc-atc/reference/macros.md || echo "clean"
```
Expected: `OK` for each macro that uses the guard; if any prints `CHECK`, read that macro and document its actual guard rather than the generic pattern. `clean` for placeholders.

- [ ] **Step 4: Commit**

```bash
git add .claude/skills/acroloc-atc/reference/macros.md
git commit -m "docs(skill): add Acroloc M-code macro quick reference"
```

---

## Task 10: Finalize `acroloc-atc/SKILL.md`

**Files:**
- Modify: `.claude/skills/acroloc-atc/SKILL.md`
- Source: `Centroid-Acroloc-ALLIN1DC.src` (custom I/O definitions), `README.md`, `CLAUDE.md`.

**Interfaces:**
- Consumes: `reference/atc-flow.md` (Task 8), `reference/macros.md` (Task 9), and the `centroid-plc-programming` skill.
- Produces: the finished machine-skill entry point.

- [ ] **Step 1: Pull the exact custom-I/O definitions for the at-a-glance table**

```bash
cd /home/bwarner/github/Acroloc-Centroid
grep -nE " IS (INP|OUT|W|T)[0-9]+ *;.*Acroloc" Centroid-Acroloc-ALLIN1DC.src
grep -nE "M6_SV|ChangeToTool_W|CarouselToolID_W|ATCMotor_O|ATCUnlocked_O|ATC_Pos|ATC_Z_|ATCManualUnlock_I|ZeroSpeed_I|Spindle_(Low|High)_gear_O" Centroid-Acroloc-ALLIN1DC.src
```

- [ ] **Step 2: Replace the stub body (keep frontmatter from Task 1)**

Write the body with these sections:
- **Machine orientation** — Acroloc mill retrofit on a Centroid ALLIN1DC (MPU11); the custom ATC is the heart; all custom code is tagged `; Acroloc`.
- **Custom I/O & variables at a glance** — a compact table of the `; Acroloc` inputs/outputs/words/timers (symbol | resource | role), built from Step 1.
- **Task playbooks** — short numbered recipes:
  - *Edit tool-change logic*: read `mfunc6.mac`, `MainStage` kickoff/safety, and `ATCStage`; see `reference/atc-flow.md`; mind the no-timeout and `Pos5=+10` decode gotchas.
  - *Edit spindle range/shift*: see `README.md` "Spindle speed & range" — note `OUT19`/`OUT20` are not yet driven.
  - *Add/change a macro*: see `reference/macros.md`; preserve the graph/search guard.
  - *Find custom code*: `grep -n "; Acroloc" Centroid-Acroloc-ALLIN1DC.src`; resolve symbols via `plc.map`/`.sym` but don't trust stale line numbers.
- **See also** — links to `reference/atc-flow.md`, `reference/macros.md`, the `centroid-plc-programming` skill, and `README.md`/`CLAUDE.md` (link, do not duplicate).

- [ ] **Step 3: Verify links resolve and no README prose was copied**

```bash
cd /home/bwarner/github/Acroloc-Centroid/.claude/skills/acroloc-atc
for ref in reference/atc-flow.md reference/macros.md; do
  grep -q "$ref" SKILL.md && test -f "$ref" && echo "OK $ref" || echo "BROKEN $ref"
done
grep -qi "centroid-plc-programming" SKILL.md && echo "OK general-link" || echo "MISSING general-link"
```
Expected: two `OK` ref lines and `OK general-link`. Manually confirm no multi-sentence block is copied verbatim from `README.md`.

- [ ] **Step 4: Commit**

```bash
git add .claude/skills/acroloc-atc/SKILL.md
git commit -m "docs(skill): finalize acroloc-atc SKILL.md with I/O table and playbooks"
```

---

## Task 11: Final validation across both skills

**Files:**
- Verify only (no new files). May fix issues found in any earlier file.

**Interfaces:**
- Consumes: every file from Tasks 1–10.

- [ ] **Step 1: Frontmatter lint — both SKILL.md have valid name/description, name == dir**

```bash
cd /home/bwarner/github/Acroloc-Centroid
for d in centroid-plc-programming acroloc-atc; do
  f=".claude/skills/$d/SKILL.md"
  head -1 "$f" | grep -qx -- "---" && echo "$d: opening ok" || echo "$d: BAD opening"
  grep -qE "^name: $d$" "$f" && echo "$d: name ok" || echo "$d: BAD name"
  grep -qE "^description: .+" "$f" && echo "$d: description ok" || echo "$d: BAD description"
done
```
Expected: `opening ok`, `name ok`, `description ok` for both.

- [ ] **Step 2: No placeholders anywhere in the skills**

```bash
grep -rniE "TODO|TBD|FIXME|XXX|placeholder|fill in" .claude/skills/ | grep -v ";TODO" || echo "clean"
```
Expected: `clean` (the only allowed `TODO` is a quoted `;TODO` from the PLC source in `atc-flow.md`).

- [ ] **Step 3: Spot-check facts against sources (success criteria)**

Pick 5 `SV_*` entries from `system-variables.md` and confirm each in real source:
```bash
for sv in $(grep -oE "SV_[A-Z0-9_]+" .claude/skills/centroid-plc-programming/reference/system-variables.md | sort -u | head -5); do
  grep -rqE "$sv" docs/official Centroid-Acroloc-ALLIN1DC.src && echo "OK $sv" || echo "UNVERIFIED $sv"
done
```
Expected: 5 `OK` lines. Then manually confirm 3 syntax facts in `syntax.md` against `scratchpad/plc-manual.txt` or an example `.src`, and that the carousel encoding table in `atc-flow.md` matches `Centroid-Acroloc-ALLIN1DC.src`.

- [ ] **Step 4: Confirm scratch file was not committed**

```bash
git ls-files | grep -E "scratchpad|plc-manual.txt" && echo "ERROR: scratch tracked" || echo "scratch clean"
git status --short
```
Expected: `scratch clean`; working tree clean after prior commits.

- [ ] **Step 5: Final commit if any fixes were made**

```bash
git add -A .claude/skills/
git commit -m "docs(skill): final validation fixes for Centroid PLC skills" || echo "nothing to commit"
```

---

## Self-Review (completed by plan author)

- **Spec coverage:** Two skills (Tasks 1–11), KB depth = core language + indexed examples (Tasks 3–6), both in-repo (Task 1 paths), PDF+example sourcing (Tasks 2, 5). Machine skill links not duplicates (Tasks 8/10 verification). All spec success criteria mapped to Task 11. ✓
- **Placeholder scan:** No `TBD`/`TODO` left as instructions; the only tolerated `TODO` is the quoted PLC `;TODO`, explicitly handled in Tasks 8 & 11. ✓
- **Type/name consistency:** Skill `name`s (`centroid-plc-programming`, `acroloc-atc`) and reference filenames are identical everywhere they appear; symbol names match the source. ✓
