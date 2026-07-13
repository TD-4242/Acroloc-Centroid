# PLC Source Formatter (plcfmt) -- Design

**Date:** 2026-07-13
**Status:** Approved (design phase)
**Scope:** A custom formatter that rewrites `Centroid-Acroloc-ALLIN1DC.src` to one
canonical style, with a compile-identical safety gate.

## Problem

`Centroid-Acroloc-ALLIN1DC.src` (~3118 lines) has accumulated formatting drift that no
existing tool can fix. There is no off-the-shelf formatter for the Centroid CNC12 PLC
"stage language" -- it is a proprietary, niche language, and Centroid's own tooling
(PLC Detective) is a live viewer/debugger, not a formatter. Generic config-driven tools
(EditorConfig, etc.) can only enforce language-agnostic whitespace rules and cannot touch
the distinctive drift that matters here.

Measured inconsistencies in the current source:

- **Mixed tabs/spaces:** 40 lines use tabs in an otherwise space-indented file. These are
  concentrated in multi-statement continuation blocks (e.g. the `SV_FORCE_*` assignment
  block), where they make operands fail to line up.
- **Comment spacing:** `;comment` (426 occurrences) vs `; comment` (796) -- no enforced
  winner.
- **`Name IS Resource` alignment:** the `IS` token clusters at column ~32-33 (~690 lines)
  but drifts to columns 30-31 (~160 lines).
- **Keyword case:** `IF` x535 vs `If` x21; `SET` x208 vs `Set` x14; `RST` present. Real,
  autofixable case drift.
- Documented conventions to check but not auto-rewrite: suffix-based **naming**
  (`_I/_O/_M/_W/_T/_SV/_C`) and ASCII-only source.

## Goal

One Python tool, `plcfmt`, that normalizes the `.src` to a single canonical style. Its
correctness rests on a structural fact: the rules only touch **whitespace, comments, and
keyword casing** -- none of which affect the compiled output. A correct reformat therefore
compiles to a **byte-identical `.plc` binary**, and the tool verifies this itself.

Non-goals (v1): formatting the `.mac` macros (different language), auto-renaming symbols,
any change that alters compiled semantics.

## Architecture

A pipeline of small, independent, pure rule functions over the file content. Each rule is
`transform(text) -> text` (or a reporter `inspect(text) -> [finding]`), unit-testable in
isolation, composed in a fixed order.

**I/O contract (line-ending safety):** the file is read as bytes and must be 7-bit ASCII.
Content is split on `\r\n`, transformed, and rejoined with `\r\n`. CRLF is mandatory:
`.gitattributes` pins `eol=crlf` so a checkout "compiles byte-identically to the running
machine binary." The formatter never emits LF.

Two tiers of rules:

- **Autofix rules** rewrite the text.
- **Report-only rules** never rewrite (a rename or an encoding change is semantic); they
  emit findings only.

## Ruleset

Canonical values below. Exact fixed columns (rule 4) are taken as the mode of the existing
dominant style at implementation time; the values in parentheses are the current best
estimate.

| # | Rule | Canonical | Tier | Notes / exceptions |
|---|------|-----------|------|--------------------|
| 1 | Indentation & mid-line tabs | spaces only | fix | no tab characters anywhere |
| 2 | Trailing whitespace | none | fix | strip end-of-line spaces/tabs |
| 3 | Final newline | exactly one, CRLF | fix | no extra trailing blank lines |
| 4 | `Name IS Resource` alignment | `IS` at fixed column (~33) | fix | names longer than the field get exactly one space before `IS` |
| 5 | Comment spacing | `;x` -> `; x` | fix | skip `;----` banner lines (93) and a lone `;`; do NOT alter the whitespace *before* an inline `;` (avoids destroying intentional alignment) |
| 6 | Keyword case | `IF THEN IS SET RST` uppercase | fix | whole-token match only, so substrings like `ResetSet` are never touched. Final keyword list fixed at implementation time |
| 7 | Continuation-line alignment | wrapped operands align under the first action column after `THEN` (wrapped conditions align under the first token after `IF `) | fix | highest-complexity rule; fixes the jagged multi-statement blocks. Compile-identical gate guarantees safety |
| 8 | Suffix naming vs resource | `_I`=INP, `_O`=OUT, `_M`=MEM, `_W`=W, `_T`=T, `_SV`=system var, `_C`=constant | report | cannot safely auto-rename |
| 9 | ASCII-only | 7-bit ASCII | report | matches repo convention; non-ASCII bytes reported with line/column |

Rule ordering matters (e.g. tabs->spaces before column alignment). The composed pipeline is
applied in the numeric order above, with report-only rules run against the final text.

## Safety gate and idempotency

**Compile-identical gate (the trust anchor).** On `--fix`:

1. Compile the original to a temp binary via `compile.sh -o <before.plc>`.
2. Apply the formatter to a working copy.
3. Compile the formatted copy to `<after.plc>`.
4. Assert `md5(before.plc) == md5(after.plc)`.
5. If equal: write the formatted file in place. If not equal: **revert, write nothing, and
   fail loudly** -- a mismatch means a formatter bug changed semantics.

A `--no-verify` escape hatch skips the gate (for environments without the compiler), with a
clear warning printed.

**Idempotency.** The formatter is a fixed point: running it on already-formatted output
produces no further change. This is an explicit test.

## CLI and UX

- `plcfmt.py <file>` -- **default = check mode**: print a unified diff of pending autofix
  changes plus all report-only findings; exit non-zero if anything would change or any
  finding exists; write nothing. CI / pre-commit friendly.
- `plcfmt.py --fix <file>` -- apply autofix rules in place, then run the compile-identical
  gate (unless `--no-verify`).
- `plcfmt.py --check <file>` -- explicit alias for the default.

Default is check (not fix) despite the formatter being autofix-first: on controller source a
dry-run default is the safe choice, and `--fix` is a single flag.

## File structure

- `tools/plcfmt.py` -- CLI entry point plus the rule functions (each rule a small pure
  function; the pipeline composes them).
- `tools/test_plcfmt.py` -- pytest suite: one focused before/after test per rule, an
  idempotency test, and an integration test exercising the compile-identical gate against
  the real `.src`.
- `tools/README.md` -- short usage note.
- `CLAUDE.md` -- one line pointing at the tool under build/deploy tooling.

## Testing strategy

- **Per-rule unit tests:** small before/after string fixtures for rules 1-7; finding-list
  assertions for rules 8-9. Each rule tested in isolation.
- **Idempotency test:** `format(format(x)) == format(x)` on a representative fixture.
- **Compile-identical integration test:** run `--fix` against the real `.src` in a temp
  copy and assert the compiled binary is unchanged (skipped automatically if the compiler /
  Wine is unavailable in the environment).
- **CRLF preservation test:** output bytes still use `\r\n` and end with exactly one.

## Risks and mitigations

- **Rule 7 over-reach:** continuation alignment touches many lines. Mitigation: the
  compile-identical gate proves no semantic change; large diffs are cosmetic only.
- **Keyword-case corrupting a symbol:** mitigated by whole-token matching and, ultimately,
  the compile gate.
- **Environment without the compiler:** `--no-verify` plus a warning; the integration test
  self-skips.
