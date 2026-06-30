#!/usr/bin/env bash
#
# compile.sh — compile the Acroloc PLC source with Centroid mpucomp and check
# whether it still matches the binary currently running on the machine.
#
# Use this to test changes to Centroid-Acroloc-ALLIN1DC.src before loading them:
#   ./compile.sh                 # compile + verify against the running baseline
#   ./compile.sh -o mpu.plc      # also write the compiled output to mpu.plc
#
# Runs mpucomp.exe natively on Windows, or via Wine on Linux/macOS.
#
set -euo pipefail
cd "$(dirname "$0")"

SRC="Centroid-Acroloc-ALLIN1DC.src"
COMPILER="mpucomp.exe"

# Checksums of the PLC running on the machine (mpu.plc, C:\cncm source,
# file date 2024-04-18). A clean checkout compiles byte-for-byte to this.
EXPECTED="EEB77825 E1E90F82 4EF4D51D E514E66E"

OUT=""                          # optional: -o <file> to keep the compiled binary
while getopts ":o:h" opt; do
  case "$opt" in
    o) OUT="$OPTARG" ;;
    h) sed -n '2,12p' "$0"; exit 0 ;;
    *) echo "usage: $0 [-o output.plc]" >&2; exit 2 ;;
  esac
done

fail() { echo "ERROR: $*" >&2; exit 1; }

# --- verify the setup -------------------------------------------------------
[[ -f "$SRC" ]]      || fail "source '$SRC' not found"
[[ -f "$COMPILER" ]] || fail "compiler '$COMPILER' not found in repo root"

if [[ "${OS:-}" == "Windows_NT" ]]; then
  RUN=()                                            # native Windows
else
  command -v wine >/dev/null 2>&1 \
    || fail "wine not found — needed to run $COMPILER on this OS (e.g. 'sudo apt install wine')"
  RUN=(env WINEDEBUG=-all wine)
fi

# --- compile a CRLF-normalized copy ----------------------------------------
# mpucomp's checksum is line-ending sensitive and the machine source is CRLF,
# so normalize to CRLF in a temp copy. This keeps the result deterministic no
# matter how the working tree was checked out, and never edits your source.
TMP="$(mktemp -d)"; trap 'rm -rf "$TMP"' EXIT
CRLF_SRC="$TMP/$(basename "$SRC")"
PLC_OUT="$TMP/plc.out"
sed 's/\r$//' "$SRC" | sed 's/$/\r/' > "$CRLF_SRC"

echo "Compiling $SRC ..."
if ! "${RUN[@]}" "$COMPILER" "$CRLF_SRC" "$PLC_OUT" > "$TMP/log" 2>&1; then
  grep -iE "error|fail" "$TMP/log" || cat "$TMP/log"
  fail "compilation failed"
fi
grep -iE "Compilation successful|Program size" "$TMP/log" || true
grep -iE "error|Compilation failed" "$TMP/log" && fail "compilation reported errors"

# --- report + verify checksum ----------------------------------------------
ACTUAL="$(grep -i -a -m1 'Checksums' "$PLC_OUT" | sed 's/.*: *//; s/[[:space:]]*$//')"
echo
echo "Checksums (this build) : $ACTUAL"
echo "Checksums (running PLC): $EXPECTED"
echo
if [[ "$ACTUAL" == "$EXPECTED" ]]; then
  echo "MATCH — compiles byte-for-byte to the PLC running on the machine."
else
  echo "DIFFERS from the running PLC (expected if you changed logic on purpose)."
fi

if [[ -n "$OUT" ]]; then
  cp "$PLC_OUT" "$OUT"
  echo "Wrote compiled binary to $OUT"
fi
