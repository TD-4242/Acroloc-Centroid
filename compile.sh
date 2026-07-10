#!/usr/bin/env bash
#
# compile.sh — syntax/lint check the Acroloc PLC source with Centroid mpucomp.
#
# Use this to catch compile errors and warnings in Centroid-Acroloc-ALLIN1DC.src
# before loading changes on the machine:
#   ./compile.sh            # compile; report errors + a warning summary
#   ./compile.sh -v         # also print every compiler warning
#   ./compile.sh -o out.plc # keep the compiled binary at out.plc
#
# Runs mpucomp.exe natively on Windows, or via Wine on Linux/macOS. This only
# exercises the compiler's syntax checking/linting — it does NOT check that the
# output matches the binary currently on the machine (after real changes it
# shouldn't).
#
set -euo pipefail
cd "$(dirname "$0")"

SRC="Centroid-Acroloc-ALLIN1DC.src"
COMPILER="mpucomp.exe"

OUT=""                          # -o <file>: keep the compiled binary
VERBOSE=0                       # -v: print all warnings, not just a count
while getopts ":o:vh" opt; do
  case "$opt" in
    o) OUT="$OPTARG" ;;
    v) VERBOSE=1 ;;
    h) sed -n '2,15p' "$0"; exit 0 ;;
    *) echo "usage: $0 [-v] [-o output.plc]" >&2; exit 2 ;;
  esac
done

fail() { echo "ERROR: $*" >&2; exit 1; }

# --- verify the setup -------------------------------------------------------
[[ -f "$SRC" ]]      || fail "source '$SRC' not found"
[[ -f "$COMPILER" ]] || fail "compiler '$COMPILER' not found in repo root"

# Invoke as ./mpucomp.exe — Git Bash/MSYS does not search the CWD for binaries.
if [[ "${OS:-}" == "Windows_NT" ]]; then
  RUN=("./$COMPILER")                               # native Windows
else
  command -v wine >/dev/null 2>&1 \
    || fail "wine not found — needed to run $COMPILER on this OS (e.g. 'sudo apt install wine')"
  RUN=(env WINEDEBUG=-all wine "./$COMPILER")
fi

# --- compile ----------------------------------------------------------------
# Portable temp file (GNU mktemp needs no template; BSD/macOS does, hence -t).
PLC_OUT="$(mktemp 2>/dev/null || mktemp -t plc)"
LOG="$(mktemp 2>/dev/null || mktemp -t plclog)"
trap 'rm -f "$PLC_OUT" "$LOG"' EXIT

echo "Compiling $SRC ..."
set +e
"${RUN[@]}" -w "$SRC" "$PLC_OUT" > "$LOG" 2>&1
rc=$?
set -e

# --- report errors / warnings ----------------------------------------------
if grep -qiE "Compilation failed|^Error|Error Line" "$LOG" || [[ $rc -ne 0 ]]; then
  echo
  grep -iE "Error|Compilation failed" "$LOG" || cat "$LOG"
  fail "compilation failed"
fi

warn_count=$(grep -ciE "^Warning:" "$LOG" || true)
grep -iE "Compilation successful|Program size" "$LOG" || true
echo "Warnings: ${warn_count}"
if [[ "$VERBOSE" -eq 1 && "$warn_count" -gt 0 ]]; then
  echo "----"
  grep -iE "^Warning:" "$LOG"
  echo "----"
fi

if [[ -n "$OUT" ]]; then
  cp "$PLC_OUT" "$OUT"
  echo "Wrote compiled binary to $OUT"
fi
