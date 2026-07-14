#!/usr/bin/env python3
"""plcfmt -- canonical formatter for Centroid CNC12 PLC source (.src).

Rewrites Centroid-Acroloc-ALLIN1DC.src to one style. Rules touch only
whitespace, comments, and keyword casing, so a correct reformat compiles to the
same program; --fix verifies this via ./compile.sh before keeping it.

Gate design (reverse-engineered empirically -- see docs/superpowers/specs). The
.plc is NOT byte-stable (build timestamp) and embeds a full copy of the source
plus an indentation-mirroring listing, so the binary and most of its four header
checksums move under harmless formatting. The invariant semantic fingerprint is:

  * the compiled program words -- every line of exactly 8 hex digits;
  * checksum C2 (2nd) -- source line structure;
  * checksum C4 (4th) -- the I/O resource map.

Formatting keeps all three identical; a logic edit moves the words, an I/O
rebind moves C4, a line add/remove moves C2 (and the words). Checksums C1 (raw
source hash) and C3 (listing/text hash) move under formatting and are ignored.
"""
import argparse
import difflib
import os
import re
import subprocess
import sys
import tempfile

SRC = "Centroid-Acroloc-ALLIN1DC.src"

NAME_FIELD = 31                       # name field width; " IS " -> IS at column 33
_KEYWORDS = ("IF", "THEN", "SET", "RST")
_IS_DEF = re.compile(r"^([A-Za-z_]\w*)\s+IS\s+(.*)$", re.IGNORECASE)
_KW_RE = re.compile(r"\b(?:IF|THEN|SET|RST|IS)\b", re.IGNORECASE)
_OPEN_IF = re.compile(r"^\s*IF\b")
_AFTER_THEN = re.compile(r"\bTHEN\b[ ]*")
_AFTER_IF = re.compile(r"^(\s*)IF[ ]+")

# resource-token pattern -> required name suffix (report-only)
_SUFFIX = [
    (re.compile(r"^INP\d+$"), "_I"),
    (re.compile(r"^OUT\d+$"), "_O"),
    (re.compile(r"^MEM\d+$"), "_M"),
    (re.compile(r"^W\d+$"), "_W"),
    (re.compile(r"^T\d+$"), "_T"),
    (re.compile(r"^SV_"), "_SV"),
    (re.compile(r"^-?\d+$"), "_C"),
]


# --------------------------------------------------------------------------- #
# I/O and helpers
# --------------------------------------------------------------------------- #
def read_src(path):
    """Read a .src file as bytes; assert 7-bit ASCII and CRLF-only endings."""
    with open(path, "rb") as f:
        data = f.read()
    bad = [i for i, b in enumerate(data) if b > 0x7F]
    if bad:
        raise ValueError("non-ASCII byte(s) at offset(s): %s" % bad[:10])
    stray = data.replace(b"\r\n", b"")
    if b"\n" in stray or b"\r" in stray:
        raise ValueError(
            "bare LF or CR line ending found; %s must be CRLF-only "
            "(.gitattributes pins eol=crlf)" % path)
    return data.decode("ascii")


def split_comment(line):
    """Split a line at its first ';'. Returns (code, comment_incl_semicolon)."""
    i = line.find(";")
    if i == -1:
        return line, ""
    return line[:i], line[i:]


def _code(line):
    return split_comment(line)[0]


# --------------------------------------------------------------------------- #
# Autofix rules
# --------------------------------------------------------------------------- #
def align_is(line):
    """Rule 4: canonically align a `Name IS Resource` definition line."""
    m = _IS_DEF.match(line)
    if not m:
        return line
    name, rest = m.group(1), m.group(2)
    if name.upper() in _KEYWORDS:        # not a definition (e.g. 'IF ... IS ...')
        return line
    return "{0:<{1}} IS {2}".format(name, NAME_FIELD, rest)


def fix_comment_space(line):
    """Rule 5: ensure at least one space after ';', except banners and blanks.

    Existing wider spacing is preserved on purpose: many comments align
    continuation text well past the ';' and collapsing would destroy it.
    """
    code, comment = split_comment(line)
    if not comment:
        return line
    after = comment[1:]
    if after and after[0] not in " -=*#":    # skip banners (-,=,*,#) and lone ';'
        comment = "; " + after
    return code + comment


def fix_keyword_case(line):
    """Rule 6: uppercase reserved keywords in the code portion only."""
    code, comment = split_comment(line)
    code = _KW_RE.sub(lambda m: m.group(0).upper(), code)
    return code + comment


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


def format_text(text):
    """Apply the canonical formatting pipeline. Preserves CRLF."""
    lines = text.split("\r\n")
    lines = [l.expandtabs(8) for l in lines]        # Rule 1: no tab characters
    lines = [align_is(l) for l in lines]            # Rule 4: IS-column alignment
    lines = [fix_comment_space(l) for l in lines]   # Rule 5: comment spacing
    lines = [fix_keyword_case(l) for l in lines]    # Rule 6: keyword case
    lines = align_continuations(lines)              # Rule 7: continuation align
    lines = [l.rstrip() for l in lines]             # Rule 2: trailing whitespace
    while lines and lines[-1] == "":                # Rule 3: single final newline
        lines.pop()
    return "\r\n".join(lines) + "\r\n"


# --------------------------------------------------------------------------- #
# Report-only rules
# --------------------------------------------------------------------------- #
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
        name = m.group(1)
        rest = split_comment(m.group(2))[0].strip()
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
    return findings


# --------------------------------------------------------------------------- #
# Compile-checksum safety gate
# --------------------------------------------------------------------------- #
_WORD_RE = re.compile(r"[0-9A-F]{8}")
_CHECKSUMS_RE = re.compile(
    r"Checksums\s*:\s*([0-9A-Fa-f]+)\s+([0-9A-Fa-f]+)\s+"
    r"([0-9A-Fa-f]+)\s+([0-9A-Fa-f]+)")


def plc_fingerprint(plc_path):
    """Semantic fingerprint of a compiled .plc: (program_words, C2, C4).

    program_words is the tuple of 8-hex-digit compiled MPU words; C2/C4 are the
    line-structure and I/O-map checksums. All three are invariant under
    whitespace/comment/case reformatting and move on a real program change.
    """
    with open(plc_path, "rb") as f:
        text = f.read().decode("latin1")
    words = tuple(l for l in text.split("\r\n") if _WORD_RE.fullmatch(l))
    m = _CHECKSUMS_RE.search(text)
    if not m:
        raise RuntimeError("no checksum header found in %s" % plc_path)
    return (words, m.group(2).upper(), m.group(4).upper())


def _compile(cwd, out_plc):
    r = subprocess.run(["./compile.sh", "-o", out_plc],
                       cwd=cwd, capture_output=True, text=True)
    if r.returncode != 0:
        tail = (r.stdout + r.stderr).strip().splitlines()[-8:]
        raise RuntimeError("compile.sh failed:\n  " + "\n  ".join(tail))


def verify_compile_identical(path, original, formatted):
    """Compile before/after; keep formatted only if the .plc fingerprint matches.

    On mismatch or compile failure, restore the original bytes and raise
    RuntimeError.
    """
    cwd = os.path.dirname(os.path.abspath(path)) or "."
    # compile.sh cd's to its own directory and compiles the hardcoded SRC name,
    # so verifying any other file would compile the wrong source and pass
    # vacuously. Refuse rather than pretend to verify.
    if os.path.basename(path) != SRC:
        raise RuntimeError(
            "cannot verify %r: compile.sh only compiles %s -- "
            "use --no-verify to format without the gate" % (path, SRC))
    if not os.path.exists(os.path.join(cwd, "compile.sh")):
        raise RuntimeError(
            "cannot verify: compile.sh not found next to %r -- "
            "use --no-verify to format without the gate" % path)
    with tempfile.TemporaryDirectory() as td:
        before = os.path.join(td, "before.plc")
        after = os.path.join(td, "after.plc")
        _compile(cwd, before)                       # original is on disk now
        fp_before = plc_fingerprint(before)
        with open(path, "wb") as f:                 # write candidate
            f.write(formatted.encode("ascii"))
        try:
            # revert on ANY failure once the candidate is on disk -- compile
            # error, fingerprint extraction, anything.
            _compile(cwd, after)
            fp_after = plc_fingerprint(after)
        except Exception:
            with open(path, "wb") as f:
                f.write(original.encode("ascii"))
            raise
        if fp_before != fp_after:
            with open(path, "wb") as f:
                f.write(original.encode("ascii"))
            reason = "program words" if fp_before[0] != fp_after[0] else \
                     "C2 (line structure)" if fp_before[1] != fp_after[1] else \
                     "C4 (I/O map)"
            raise RuntimeError(
                "compiled program changed (%s differs); reverted (formatter bug)"
                % reason)


# --------------------------------------------------------------------------- #
# CLI
# --------------------------------------------------------------------------- #
def run(path, fix, verify):
    original = read_src(path)
    formatted = format_text(original)
    findings = report_findings(formatted)
    changed = formatted != original

    if fix:
        if changed:
            if verify:
                verify_compile_identical(path, original, formatted)
            else:
                with open(path, "wb") as f:
                    f.write(formatted.encode("ascii"))
        for ln, rule, msg in findings:
            sys.stderr.write("%s:%d: [%s] %s\n" % (path, ln, rule, msg))
        return 0

    if changed:
        diff = difflib.unified_diff(
            original.splitlines(True), formatted.splitlines(True),
            fromfile=path, tofile=path + " (formatted)")
        sys.stdout.writelines(diff)
    for ln, rule, msg in findings:
        sys.stderr.write("%s:%d: [%s] %s\n" % (path, ln, rule, msg))
    # findings are advisory (they can never be autofixed); only a pending
    # reformat fails the check, so CI stays green on a formatted file.
    return 1 if changed else 0


def main(argv=None):
    p = argparse.ArgumentParser(description="Format Centroid PLC .src source.")
    p.add_argument("file", nargs="?", default=SRC)
    g = p.add_mutually_exclusive_group()
    g.add_argument("--fix", action="store_true", help="rewrite the file in place")
    g.add_argument("--check", action="store_true", help="dry-run (default)")
    p.add_argument("--no-verify", action="store_true",
                   help="skip the program-checksum gate on --fix")
    args = p.parse_args(argv)
    try:
        return run(args.file, fix=args.fix, verify=not args.no_verify)
    except (RuntimeError, ValueError, OSError) as e:
        sys.stderr.write("error: %s\n" % e)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
