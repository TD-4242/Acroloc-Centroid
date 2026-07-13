# PLC Source Formatter (plcfmt) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build `tools/plcfmt.py`, a Python formatter that rewrites `Centroid-Acroloc-ALLIN1DC.src` to one canonical style, verified by a compile-identical safety gate.

**Architecture:** A pipeline of small, pure rule functions over the file content (each unit-testable in isolation), composed in a fixed order. Autofix rules rewrite text; report-only rules (naming, non-ASCII) emit findings. On `--fix`, a compile-identical gate proves the reformat did not change the compiled `.plc` binary before the change is kept.

**Tech Stack:** Python 3 standard library only (no third-party runtime deps). Tests use pytest. The compile gate shells out to the repo's existing `./compile.sh`.

## Global Constraints

- **ASCII-only.** The `.src` must remain 7-bit ASCII; the formatter reads bytes and refuses non-ASCII input. Plan docs and code in this repo are also plain ASCII (use `--`, straight quotes).
- **CRLF preserved.** `.gitattributes` pins `eol=crlf`. The formatter splits on `\r\n` and rejoins with `\r\n`, ending in exactly one `\r\n`. Never emit LF.
- **Compile-identical guarantee.** Rules only touch whitespace, comments, and keyword casing -- never the compiled output. `--fix` must verify the compiled binary is byte-identical, or revert.
- **Scope: `.src` only.** The `.mac` macros are a different language and are out of scope.
- **Default mode is check** (dry-run). `--fix` applies; `--no-verify` skips the compile gate.
- **Canonical values:** `IS` at column 33 (name field width 31); comment `;x` -> `; x`; keywords `IF THEN IS SET RST` uppercase; no tabs; single trailing newline.
- **Target file constant:** `SRC = "Centroid-Acroloc-ALLIN1DC.src"` (repo root); compiler wrapper `./compile.sh`.

---

### Task 1: Scaffold module, I/O contract, CLI skeleton, shared helpers

**Files:**
- Create: `tools/plcfmt.py`
- Create: `tools/test_plcfmt.py`

**Interfaces:**
- Produces: `read_src(path) -> str` (bytes -> assert ASCII -> decode); `split_comment(line) -> (code, comment)`; `format_text(text) -> str` (no-op for now, returns CRLF-normalized text); `main(argv) -> int`.

- [ ] **Step 1: Write the failing tests**

```python
# tools/test_plcfmt.py
import plcfmt

def test_split_comment_basic():
    assert plcfmt.split_comment("IF a THEN b  ; c") == ("IF a THEN b  ", "; c")
    assert plcfmt.split_comment("no comment here") == ("no comment here", "")
    assert plcfmt.split_comment(";banner") == ("", ";banner")

def test_format_text_preserves_crlf_and_single_final_newline():
    src = "line1\r\nline2\r\n"
    out = plcfmt.format_text(src)
    assert out.endswith("\r\n")
    assert "\n" not in out.replace("\r\n", "")   # only CRLF, no lone LF
    assert out == "line1\r\nline2\r\n"

def test_format_text_strips_trailing_blank_lines_to_one_newline():
    assert plcfmt.format_text("a\r\n\r\n\r\n") == "a\r\n"
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd tools && python3 -m pytest test_plcfmt.py -v`
Expected: FAIL (module has no such functions yet). If pytest missing: `pip install pytest`.

- [ ] **Step 3: Write minimal implementation**

```python
#!/usr/bin/env python3
"""plcfmt -- canonical formatter for Centroid CNC12 PLC source (.src).

Rewrites Centroid-Acroloc-ALLIN1DC.src to one style. Rules touch only
whitespace, comments, and keyword casing, so a correct reformat compiles to a
byte-identical .plc; --fix verifies this via ./compile.sh before keeping it.
"""
import argparse
import sys

SRC = "Centroid-Acroloc-ALLIN1DC.src"


def read_src(path):
    """Read a .src file as bytes, assert 7-bit ASCII, return decoded text."""
    with open(path, "rb") as f:
        data = f.read()
    bad = [i for i, b in enumerate(data) if b > 0x7F]
    if bad:
        raise ValueError("non-ASCII byte(s) at offset(s): %s" % bad[:10])
    return data.decode("ascii")


def split_comment(line):
    """Split a line at its first ';'. Returns (code, comment_incl_semicolon)."""
    i = line.find(";")
    if i == -1:
        return line, ""
    return line[:i], line[i:]


def format_text(text):
    """Apply the canonical formatting pipeline. No-op transform for now."""
    lines = text.split("\r\n")
    # (rules inserted by later tasks, in order)
    lines = [l.rstrip() for l in lines]          # Rule 2: trailing whitespace
    while lines and lines[-1] == "":             # Rule 3: single final newline
        lines.pop()
    return "\r\n".join(lines) + "\r\n"


def main(argv=None):
    p = argparse.ArgumentParser(description="Format Centroid PLC .src source.")
    p.add_argument("file", nargs="?", default=SRC)
    g = p.add_mutually_exclusive_group()
    g.add_argument("--fix", action="store_true", help="rewrite the file in place")
    g.add_argument("--check", action="store_true", help="dry-run (default)")
    p.add_argument("--no-verify", action="store_true",
                   help="skip the compile-identical gate on --fix")
    args = p.parse_args(argv)

    original = read_src(args.file)
    formatted = format_text(original)
    # check/fix wiring added in Task 8-9
    if args.fix:
        with open(args.file, "wb") as f:
            f.write(formatted.encode("ascii"))
        return 0
    sys.stdout.write("would reformat\n" if formatted != original else "unchanged\n")
    return 0 if formatted == original else 1


if __name__ == "__main__":
    raise SystemExit(main())
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd tools && python3 -m pytest test_plcfmt.py -v`
Expected: PASS (3 tests).

- [ ] **Step 5: Commit**

```bash
git add tools/plcfmt.py tools/test_plcfmt.py
git commit -m "feat(plcfmt): scaffold formatter I/O, helpers, CLI skeleton"
```

---

### Task 2: Rule 1 (tabs -> spaces)

**Files:**
- Modify: `tools/plcfmt.py`
- Test: `tools/test_plcfmt.py`

**Interfaces:**
- Produces: tabs removed inside `format_text` (via `str.expandtabs(8)` as the first transform).

- [ ] **Step 1: Write the failing test**

```python
def test_tabs_expanded_to_spaces():
    out = plcfmt.format_text("\tSV_X = 1\r\n")
    assert "\t" not in out
    assert out == "        SV_X = 1\r\n"   # tab at col 1 -> 8 spaces
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd tools && python3 -m pytest test_plcfmt.py::test_tabs_expanded_to_spaces -v`
Expected: FAIL (tab still present).

- [ ] **Step 3: Implement**

In `format_text`, insert as the FIRST transform (before the trailing-whitespace step):

```python
    lines = [l.expandtabs(8) for l in lines]      # Rule 1: no tab characters
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd tools && python3 -m pytest test_plcfmt.py -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add tools/plcfmt.py tools/test_plcfmt.py
git commit -m "feat(plcfmt): rule 1 -- expand tabs to spaces"
```

---

### Task 3: Rule 4 (`Name IS Resource` alignment)

**Files:**
- Modify: `tools/plcfmt.py`
- Test: `tools/test_plcfmt.py`

**Interfaces:**
- Produces: `align_is(line) -> str`, applied per line in `format_text` after Rule 1.

- [ ] **Step 1: Write the failing tests**

```python
def test_align_is_pads_short_name_to_column_33():
    out = plcfmt.align_is("Foo_C IS 1    ;note")
    # name in 31-wide field, then " IS ", so IS starts at column 33 (1-based)
    assert out == "Foo_C" + " " * 26 + " IS 1    ;note"
    assert out.index("IS ") == 32   # 0-based index 32 == column 33

def test_align_is_long_name_gets_single_space():
    long = "A_Really_Long_Symbol_Name_Over_31c_M"
    out = plcfmt.align_is(long + "   IS MEM5")
    assert out == long + " IS MEM5"

def test_align_is_uppercases_the_keyword():
    assert plcfmt.align_is("Foo_M is MEM1").endswith(" IS MEM1")

def test_align_is_ignores_logic_lines():
    line = "IF True_M THEN SET Foo"
    assert plcfmt.align_is(line) == line
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd tools && python3 -m pytest test_plcfmt.py -k align_is -v`
Expected: FAIL (no `align_is`).

- [ ] **Step 3: Implement**

Add near the top (after imports add `import re`) and define:

```python
NAME_FIELD = 31   # name left-justified in 31 cols; " IS " -> IS at column 33
_KEYWORDS = ("IF", "THEN", "SET", "RST")
_IS_DEF = re.compile(r"^([A-Za-z_]\w*)\s+IS\s+(.*)$", re.IGNORECASE)


def align_is(line):
    """Rule 4: canonically align a `Name IS Resource` definition line."""
    m = _IS_DEF.match(line)
    if not m:
        return line
    name, rest = m.group(1), m.group(2)
    if name.upper() in _KEYWORDS:        # not a definition (e.g. 'IF ... IS ...')
        return line
    return "{0:<{1}} IS {2}".format(name, NAME_FIELD, rest)
```

Insert into `format_text` right after the Rule 1 line:

```python
    lines = [align_is(l) for l in lines]          # Rule 4: IS-column alignment
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd tools && python3 -m pytest test_plcfmt.py -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add tools/plcfmt.py tools/test_plcfmt.py
git commit -m "feat(plcfmt): rule 4 -- align Name IS Resource to column 33"
```

---

### Task 4: Rule 5 (comment spacing)

**Files:**
- Modify: `tools/plcfmt.py`
- Test: `tools/test_plcfmt.py`

**Interfaces:**
- Produces: `fix_comment_space(line) -> str`, applied per line after Rule 4.

- [ ] **Step 1: Write the failing tests**

```python
def test_comment_space_inserted():
    assert plcfmt.fix_comment_space("IS 1 ;note") == "IS 1 ; note"
    assert plcfmt.fix_comment_space("Foo IS 2  ;(2+256*0)") == "Foo IS 2  ; (2+256*0)"

def test_comment_space_leaves_banners_and_blank():
    assert plcfmt.fix_comment_space(";----------") == ";----------"
    assert plcfmt.fix_comment_space(";==== X ====") == ";==== X ===="
    assert plcfmt.fix_comment_space(";") == ";"

def test_comment_space_does_not_touch_pre_semicolon_gap():
    # trailing gap before ';' preserved (inline alignment untouched)
    assert plcfmt.fix_comment_space("SET Foo    ;go") == "SET Foo    ; go"
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd tools && python3 -m pytest test_plcfmt.py -k comment_space -v`
Expected: FAIL.

- [ ] **Step 3: Implement**

```python
def fix_comment_space(line):
    """Rule 5: ensure exactly one space after ';', except banners and blanks."""
    code, comment = split_comment(line)
    if not comment:
        return line
    after = comment[1:]
    if after and after[0] not in " -=*":     # skip banners (-,=,*) and lone ';'
        comment = "; " + after
    return code + comment
```

Insert into `format_text` after the Rule 4 line:

```python
    lines = [fix_comment_space(l) for l in lines]  # Rule 5: comment spacing
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd tools && python3 -m pytest test_plcfmt.py -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add tools/plcfmt.py tools/test_plcfmt.py
git commit -m "feat(plcfmt): rule 5 -- normalize comment spacing"
```

---

### Task 5: Rule 6 (keyword case)

**Files:**
- Modify: `tools/plcfmt.py`
- Test: `tools/test_plcfmt.py`

**Interfaces:**
- Produces: `fix_keyword_case(line) -> str`, applied per line after Rule 5.

- [ ] **Step 1: Write the failing tests**

```python
def test_keyword_case_uppercases_code_only():
    assert plcfmt.fix_keyword_case("if a then set b") == "IF a THEN SET b"

def test_keyword_case_does_not_touch_comments():
    assert plcfmt.fix_keyword_case("SET b  ; this is if then set") == \
        "SET b  ; this is if then set"

def test_keyword_case_whole_token_only():
    # substrings of longer identifiers are never changed
    assert plcfmt.fix_keyword_case("RST ResetSet") == "RST ResetSet"
    assert plcfmt.fix_keyword_case("SET Ifget_M") == "SET Ifget_M"
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd tools && python3 -m pytest test_plcfmt.py -k keyword_case -v`
Expected: FAIL.

- [ ] **Step 3: Implement**

```python
_KW_RE = re.compile(r"\b(?:IF|THEN|SET|RST|IS)\b", re.IGNORECASE)


def fix_keyword_case(line):
    """Rule 6: uppercase reserved keywords in the code portion only."""
    code, comment = split_comment(line)
    code = _KW_RE.sub(lambda m: m.group(0).upper(), code)
    return code + comment
```

Insert into `format_text` after the Rule 5 line:

```python
    lines = [fix_keyword_case(l) for l in lines]   # Rule 6: keyword case
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd tools && python3 -m pytest test_plcfmt.py -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add tools/plcfmt.py tools/test_plcfmt.py
git commit -m "feat(plcfmt): rule 6 -- uppercase reserved keywords in code"
```

---

### Task 6: Rule 7 (continuation-line alignment)

**Files:**
- Modify: `tools/plcfmt.py`
- Test: `tools/test_plcfmt.py`

**Interfaces:**
- Consumes: `split_comment`.
- Produces: `align_continuations(lines) -> list`, applied over the full line list after Rule 6.

Behavior: for a statement opening with `IF ...`, re-indent its continuation lines. If
`THEN` is on the opening line, continuation actions align to the column where the opening
line's action begins (just after `THEN `). If the condition wraps (no `THEN` yet),
continuation lines align to the column just after `IF ` on the opening line. A statement
continues while (a) `THEN` has not yet appeared, or (b) the current code line ends with a
continuation operator (`,`, `||`, `&&`). A safety cap of 40 lines prevents runaway.

- [ ] **Step 1: Write the failing tests**

```python
def test_continuation_comma_block_aligns_under_action():
    src = ("IF True_M THEN AAA = 1,\r\n"
           "\t BBB = 2,\r\n"
           "         CCC = 3\r\n")
    # action column on opening line: after "IF True_M THEN " = 15 chars -> col 16
    out = plcfmt.format_text(src)
    lines = out.split("\r\n")
    assert lines[0] == "IF True_M THEN AAA = 1,"
    assert lines[1] == " " * 15 + "BBB = 2,"
    assert lines[2] == " " * 15 + "CCC = 3"

def test_wrapped_condition_aligns_under_if():
    src = ("IF (A) ||\r\n"
           "\tB\r\n"
           "  THEN (X_M)\r\n")
    out = plcfmt.format_text(src)
    lines = out.split("\r\n")
    assert lines[0] == "IF (A) ||"
    assert lines[1] == "   B"          # after "IF " = 3 columns
    assert lines[2] == "   THEN (X_M)"

def test_continuation_preserves_inline_comment_gap():
    src = ("IF True_M THEN AAA = 1,  ; first\r\n"
           "\tBBB = 2  ; second\r\n")
    out = plcfmt.format_text(src)
    lines = out.split("\r\n")
    assert lines[1] == " " * 15 + "BBB = 2  ; second"

def test_non_if_lines_unchanged_by_continuation():
    src = "SET Foo\r\nRST Bar\r\n"
    assert plcfmt.format_text(src) == src
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd tools && python3 -m pytest test_plcfmt.py -k continuation -v`
Expected: FAIL (no `align_continuations`).

- [ ] **Step 3: Implement**

```python
_OPEN_IF = re.compile(r"^\s*IF\b")
_AFTER_THEN = re.compile(r"\bTHEN\b[ ]*")
_AFTER_IF = re.compile(r"^(\s*)IF[ ]+")


def _code(line):
    return split_comment(line)[0]


def _ends_continue(line):
    c = _code(line).rstrip()
    return c.endswith(",") or c.endswith("||") or c.endswith("&&")


def _target_col(open_line):
    code = _code(open_line)
    mt = _AFTER_THEN.search(code)
    if mt and code[mt.end():].strip():        # action present after THEN
        return mt.end()
    mi = _AFTER_IF.match(code)                 # wrapped condition -> under IF
    return mi.end() if mi else 0


def align_continuations(lines):
    """Rule 7: re-indent continuation lines of multi-line IF statements."""
    out = []
    i, n = 0, len(lines)
    while i < n:
        if not _OPEN_IF.match(_code(lines[i])):
            out.append(lines[i])
            i += 1
            continue
        start = i
        seen_then = "THEN" in _code(lines[start])
        k = start
        while k + 1 < n and (k - start) < 40:
            if not seen_then:
                k += 1
                if "THEN" in _code(lines[k]):
                    seen_then = True
                continue
            if _ends_continue(lines[k]):
                k += 1
            else:
                break
        target = _target_col(lines[start])
        out.append(lines[start])
        for g in range(start + 1, k + 1):
            left, comment = split_comment(lines[g])
            out.append(" " * target + left.lstrip(" ") + comment)
        i = k + 1
    return out
```

Insert into `format_text` after the Rule 6 line (BEFORE the trailing-whitespace step):

```python
    lines = align_continuations(lines)             # Rule 7: continuation align
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd tools && python3 -m pytest test_plcfmt.py -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add tools/plcfmt.py tools/test_plcfmt.py
git commit -m "feat(plcfmt): rule 7 -- align multi-line statement continuations"
```

---

### Task 7: Rules 8-9 (report-only: suffix naming, non-ASCII)

**Files:**
- Modify: `tools/plcfmt.py`
- Test: `tools/test_plcfmt.py`

**Interfaces:**
- Produces: `report_findings(text) -> list` of `(lineno, rule, message)` tuples. Non-ASCII is
  detected at read time by `read_src`; this reporter re-scans decoded text for defensive
  reporting and covers suffix-naming.

- [ ] **Step 1: Write the failing tests**

```python
def test_naming_report_flags_suffix_mismatch():
    text = "GoodOne_I IS INP5\r\nBadName_M IS INP6\r\n"
    findings = plcfmt.report_findings(text)
    msgs = [(ln, msg) for (ln, rule, msg) in findings if rule == "naming"]
    assert len(msgs) == 1
    assert msgs[0][0] == 2                # BadName_M on line 2
    assert "_I" in msgs[0][1]             # expects _I for INP

def test_naming_report_ignores_alias_and_stage():
    text = "Foo_M IS Bar_M\r\nMainStage IS STG4\r\n"
    naming = [f for f in plcfmt.report_findings(text) if f[1] == "naming"]
    assert naming == []
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd tools && python3 -m pytest test_plcfmt.py -k naming -v`
Expected: FAIL.

- [ ] **Step 3: Implement**

```python
# resource-token prefix -> required name suffix
_SUFFIX = [
    (re.compile(r"^INP\d+$"), "_I"),
    (re.compile(r"^OUT\d+$"), "_O"),
    (re.compile(r"^MEM\d+$"), "_M"),
    (re.compile(r"^W\d+$"), "_W"),
    (re.compile(r"^T\d+$"), "_T"),
    (re.compile(r"^SV_"), "_SV"),
    (re.compile(r"^-?\d+$"), "_C"),        # integer literal -> constant
]


def report_findings(text):
    """Rules 8-9: return [(lineno, rule, message)] -- naming + non-ASCII."""
    findings = []
    for idx, line in enumerate(text.split("\r\n"), start=1):
        for col, ch in enumerate(line, start=1):
            if ord(ch) > 0x7F:
                findings.append((idx, "ascii", "non-ASCII at column %d" % col))
        m = _IS_DEF.match(line)
        if not m:
            continue
        name, rest = m.group(1), split_comment(m.group(2))[0].strip()
        if name.upper() in _KEYWORDS:
            continue
        if rest.startswith("STG"):         # stages use ...Stage, not a suffix
            continue
        for pat, suffix in _SUFFIX:
            if pat.match(rest):
                if not name.endswith(suffix):
                    findings.append(
                        (idx, "naming",
                         "name '%s' bound to %s should end with %s"
                         % (name, rest, suffix)))
                break
        # resource that is another symbol (alias) matches no pattern -> skip
    return findings
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd tools && python3 -m pytest test_plcfmt.py -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add tools/plcfmt.py tools/test_plcfmt.py
git commit -m "feat(plcfmt): rules 8-9 -- report suffix-naming and non-ASCII"
```

---

### Task 8: CLI check/fix output, diff, exit codes, idempotency

**Files:**
- Modify: `tools/plcfmt.py`
- Test: `tools/test_plcfmt.py`

**Interfaces:**
- Consumes: `format_text`, `report_findings`.
- Produces: `run(path, fix, verify) -> int`; `main` delegates to it. Check mode prints a
  unified diff plus findings and exits 1 if anything would change or any finding exists.

- [ ] **Step 1: Write the failing tests**

```python
import difflib, os

def test_idempotent(tmp_path):
    sample = ("if True_M then AAA = 1,\r\n"
              "\tBBB = 2\r\n"
              "Foo_C IS 1 ;x\r\n")
    once = plcfmt.format_text(sample)
    twice = plcfmt.format_text(once)
    assert once == twice

def test_run_check_returns_1_when_changes_needed(tmp_path, capsys):
    f = tmp_path / "x.src"
    f.write_bytes(b"if a then b\r\n")
    rc = plcfmt.run(str(f), fix=False, verify=False)
    assert rc == 1
    assert f.read_bytes() == b"if a then b\r\n"     # check writes nothing

def test_run_fix_writes_and_returns_0(tmp_path):
    f = tmp_path / "x.src"
    f.write_bytes(b"if a then b\r\n")
    rc = plcfmt.run(str(f), fix=True, verify=False)
    assert rc == 0
    assert f.read_bytes() == b"IF a THEN b\r\n"
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd tools && python3 -m pytest test_plcfmt.py -k "idempotent or run_" -v`
Expected: FAIL (no `run`).

- [ ] **Step 3: Implement**

Add `import difflib` at the top. Replace the check/fix block in `main` with a `run` function:

```python
def run(path, fix, verify):
    original = read_src(path)
    formatted = format_text(original)
    findings = report_findings(formatted)
    changed = formatted != original

    if fix:
        if changed:
            if verify:
                verify_compile_identical(path, original, formatted)  # Task 9
            else:
                with open(path, "wb") as f:
                    f.write(formatted.encode("ascii"))
        for ln, rule, msg in findings:
            sys.stderr.write("%s:%d: [%s] %s\n" % (path, ln, rule, msg))
        return 0

    # check mode
    if changed:
        diff = difflib.unified_diff(
            original.splitlines(True), formatted.splitlines(True),
            fromfile=path, tofile=path + " (formatted)")
        sys.stdout.writelines(diff)
    for ln, rule, msg in findings:
        sys.stderr.write("%s:%d: [%s] %s\n" % (path, ln, rule, msg))
    return 1 if (changed or findings) else 0


def verify_compile_identical(path, original, formatted):
    """Placeholder until Task 9 -- write without the compile gate."""
    with open(path, "wb") as f:
        f.write(formatted.encode("ascii"))
```

Replace the body of `main` after arg parsing with:

```python
    return run(args.file, fix=args.fix, verify=not args.no_verify)
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd tools && python3 -m pytest test_plcfmt.py -v`
Expected: PASS (all tests to date).

- [ ] **Step 5: Commit**

```bash
git add tools/plcfmt.py tools/test_plcfmt.py
git commit -m "feat(plcfmt): CLI check/fix output, diff, exit codes"
```

---

### Task 9: Compile-identical safety gate + integration test on the real .src

**Files:**
- Modify: `tools/plcfmt.py`
- Test: `tools/test_plcfmt.py`

**Interfaces:**
- Produces: real `verify_compile_identical(path, original, formatted)` that compiles before
  and after via `./compile.sh -o`, compares md5, and reverts on mismatch.

- [ ] **Step 1: Write the failing/integration tests**

```python
import hashlib, shutil, subprocess

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def _compiler_available():
    if not os.path.exists(os.path.join(REPO, "compile.sh")):
        return False
    try:
        subprocess.run(["bash", "-c", "command -v wine || [ \"$OS\" = Windows_NT ]"],
                       cwd=REPO, check=True, capture_output=True)
        return os.path.exists(os.path.join(REPO, "mpucomp.exe"))
    except Exception:
        return False

import pytest

@pytest.mark.skipif(not _compiler_available(), reason="compiler/wine unavailable")
def test_real_src_reformats_compile_identical(tmp_path):
    real = os.path.join(REPO, plcfmt.SRC)
    work = shutil.copytree(REPO, tmp_path / "repo",
                           ignore=shutil.ignore_patterns(".git"))
    target = os.path.join(work, plcfmt.SRC)
    original = plcfmt.read_src(target)
    formatted = plcfmt.format_text(original)
    # should not raise (compile-identical); writes formatted in place
    plcfmt.verify_compile_identical(target, original, formatted)
    assert plcfmt.read_src(target) == formatted

@pytest.mark.skipif(not _compiler_available(), reason="compiler/wine unavailable")
def test_gate_reverts_on_semantic_change(tmp_path):
    # inject a fake formatter that changes a bit number -> binary differs -> revert
    work = shutil.copytree(REPO, tmp_path / "repo",
                           ignore=shutil.ignore_patterns(".git"))
    target = os.path.join(work, plcfmt.SRC)
    original = plcfmt.read_src(target)
    broken = original.replace("INP1 ", "INP7 ", 1)
    with pytest.raises(RuntimeError):
        plcfmt.verify_compile_identical(target, original, broken)
    assert plcfmt.read_src(target) == original      # reverted
```

- [ ] **Step 2: Run tests to verify current behavior**

Run: `cd tools && python3 -m pytest test_plcfmt.py -k "compile_identical or gate_reverts" -v`
Expected: FAIL if a compiler is available (placeholder gate does not verify); SKIP if not.

- [ ] **Step 3: Implement the real gate**

```python
import hashlib
import subprocess
import tempfile


def _md5(path):
    h = hashlib.md5()
    with open(path, "rb") as f:
        h.update(f.read())
    return h.hexdigest()


def _compile(cwd, out_plc):
    subprocess.run(["./compile.sh", "-o", out_plc],
                   cwd=cwd, check=True, capture_output=True)


def verify_compile_identical(path, original, formatted):
    """Compile before/after; write formatted only if the .plc is byte-identical.

    On mismatch, restore the original bytes and raise RuntimeError.
    """
    cwd = os.path.dirname(os.path.abspath(path)) or "."
    with tempfile.TemporaryDirectory() as td:
        before = os.path.join(td, "before.plc")
        after = os.path.join(td, "after.plc")
        _compile(cwd, before)                       # original is on disk now
        with open(path, "wb") as f:                 # write candidate
            f.write(formatted.encode("ascii"))
        try:
            _compile(cwd, after)
        except subprocess.CalledProcessError:
            with open(path, "wb") as f:             # candidate did not compile
                f.write(original.encode("ascii"))
            raise RuntimeError("formatted source failed to compile; reverted")
        if _md5(before) != _md5(after):
            with open(path, "wb") as f:             # semantics changed
                f.write(original.encode("ascii"))
            raise RuntimeError("compiled binary changed; reverted (formatter bug)")
```

Add `import os` at the top if not already present.

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd tools && python3 -m pytest test_plcfmt.py -v`
Expected: PASS (integration tests PASS if a compiler is available, else SKIP).

- [ ] **Step 5: Manual end-to-end check against the real source**

```bash
cd /home/bwarner/github/Acroloc-Centroid
python3 tools/plcfmt.py            # check mode: shows the diff it would make
python3 tools/plcfmt.py --fix      # applies + runs the compile-identical gate
./compile.sh                       # confirm it still compiles cleanly
git diff --stat                    # review the reformat
```

Expected: `--fix` exits 0 (gate passed); `compile.sh` reports no new errors/warnings.

- [ ] **Step 6: Commit**

```bash
git add tools/plcfmt.py tools/test_plcfmt.py
git commit -m "feat(plcfmt): compile-identical safety gate + integration tests"
```

---

### Task 10: Docs

**Files:**
- Create: `tools/README.md`
- Modify: `CLAUDE.md`

**Interfaces:** none (documentation only).

- [ ] **Step 1: Write `tools/README.md`**

```markdown
# tools/plcfmt.py -- Centroid PLC source formatter

Rewrites `Centroid-Acroloc-ALLIN1DC.src` to one canonical style: no tabs, single
trailing newline, `Name IS Resource` aligned to column 33, `; ` comment spacing,
uppercase `IF/THEN/IS/SET/RST`, and aligned multi-line statement continuations.
Suffix-naming and non-ASCII issues are reported (never auto-changed).

## Usage

    python3 tools/plcfmt.py            # check (dry run): print diff + findings, exit 1 if changes needed
    python3 tools/plcfmt.py --fix      # apply, then verify the compiled .plc is byte-identical
    python3 tools/plcfmt.py --fix --no-verify   # apply without the compile gate

## Safety

`--fix` compiles the source before and after via `./compile.sh` and keeps the change
only if the compiled binary is byte-identical. If it differs (or fails to compile),
the original is restored and the tool errors out. CRLF line endings are preserved.

## Tests

    cd tools && python3 -m pytest test_plcfmt.py -v

The compile-identical integration tests self-skip when the compiler/Wine is unavailable.
```

- [ ] **Step 2: Add a line to `CLAUDE.md`**

Under the "Build / deploy" section, after the `compile.sh` description, add:

```markdown
- `tools/plcfmt.py` reformats the `.src` to canonical style (`--fix`), guarded by a
  compile-identical check. See `tools/README.md`. Run `./compile.sh` after `--fix`.
```

- [ ] **Step 3: Verify ASCII cleanliness**

Run: `grep -rncP '[^\x00-\x7F]' tools/README.md CLAUDE.md tools/plcfmt.py`
Expected: all `0`.

- [ ] **Step 4: Commit**

```bash
git add tools/README.md CLAUDE.md
git commit -m "docs(plcfmt): usage README and CLAUDE.md pointer"
```

---

## Self-Review

- **Spec coverage:** Rules 1-9 each map to a task (1->T2, 2/3->T1, 4->T3, 5->T4, 6->T5,
  7->T6, 8/9->T7). Architecture pipeline -> T1/T8. Safety gate -> T9. CLI/default-check ->
  T8. File structure/docs -> T1/T10. Testing strategy (per-rule, idempotency, compile-
  identical, CRLF) -> distributed across T1-T9.
- **Placeholder scan:** the Task 8 `verify_compile_identical` is explicitly a placeholder
  replaced by the real implementation in Task 9 (called out in both). No other placeholders.
- **Type consistency:** `format_text`, `split_comment`, `align_is`, `fix_comment_space`,
  `fix_keyword_case`, `align_continuations`, `report_findings`, `run`,
  `verify_compile_identical` names and signatures are consistent across tasks. `_IS_DEF`,
  `_KEYWORDS`, `NAME_FIELD` defined in T3 and reused in T7. Pipeline insertion order in
  `format_text`: Rule 1 -> 4 -> 5 -> 6 -> 7 -> 2 -> 3 (trailing strip and final newline
  last), matching the spec.
