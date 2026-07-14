# tools/plcfmt.py -- Centroid PLC source formatter

Rewrites `Centroid-Acroloc-ALLIN1DC.src` to one canonical style: no tabs, single
trailing newline, `Name IS Resource` aligned to column 33, `; ` comment spacing,
uppercase `IF/THEN/IS/SET/RST`, and aligned multi-line statement continuations.
Suffix-naming and non-ASCII issues are reported (never auto-changed). CRLF line
endings are preserved.

## Usage

    python3 tools/plcfmt.py            # check (dry run): print diff + findings, exit 1 if changes needed
    python3 tools/plcfmt.py --fix      # apply, then verify the compiled program is unchanged
    python3 tools/plcfmt.py --fix --no-verify   # apply without the compile gate

## Safety gate

`--fix` compiles the source before and after via `./compile.sh` and keeps the change
only if the compiled program is unchanged. The `.plc` is not byte-stable (it carries a
build timestamp and embeds a copy of the source), so the gate compares a **fingerprint**
that is invariant to formatting but sensitive to real program changes:

- the compiled MPU program words (every line of exactly 8 hex digits in the `.plc`),
- checksum C2 (source line structure) and checksum C4 (the I/O resource map).

A logic edit moves the words, an I/O rebind moves C4, a line add/remove moves C2. If the
fingerprint differs (or the formatted source fails to compile), the original bytes are
restored and the tool errors out. See `docs/superpowers/specs/2026-07-13-plc-formatter-design.md`
for how this was reverse-engineered.

## Tests

    python3 tools/test_plcfmt.py

Dependency-free (no pytest needed). The compile-gate integration tests self-skip when the
Centroid compiler / Wine is unavailable.
