# Operator-Message Constant Encoding

## Encoding formula

Every operator message is identified by a single integer value stored in a Word variable
and sent to CNC12 via the `MSG` command:

```
value = type + 256 × msgNumber
```

where:
- **type** — `1` for Synchronous (halts the job; requires operator acknowledgement) or
  `2` for Asynchronous (informational; does not halt the job).
- **msgNumber** — the entry number that appears in the first column of `plcmsg.txt` (see
  below).

Source (scratchpad/plc-manual.txt, lines 795–815, CNC12 PLC Programming Manual rev7):

> "The method of formatting this value is to start with a 1 or 2 for Synchronous or
> Asynchronous respectively and then add the message number times 256."

Example table from the manual:

| Message Number | Type | Word Value | Notes |
|---|---|---|---|
| 1 | Synchronous | 257 | `1 + 1×256` |
| 2 | Asynchronous | 514 | `2 + 2×256` |
| 25 | Synchronous | 6401 | `1 + 25×256` |
| 50 | Asynchronous | 12802 | `2 + 50×256` |

### Note on CLAUDE.md variable names

`CLAUDE.md` expresses the same formula as `value = msgNumber + 256 × msgFile`, where
`msgNumber` is what the manual calls `type` (1 or 2) and `msgFile` is the plcmsg.txt
entry number. The formulas are mathematically equivalent; the naming difference is a
historical convention in this repo's documentation.

---

## Worked example

From `Centroid-Acroloc-ALLIN1DC.src`, line 200:

```
ATC_Spindle_Not_Parked_C        IS 44034;(2+256*172) Spindle not parked.  Z Axis not tool change position.
```

The comment `(2+256*172)` decodes as: **type = 2** (Asynchronous), **msgNumber = 172**
(entry 172 in `plcmsg.txt`). Compute the value:

```
2 + 256 × 172 = 2 + 44032 = 44034
```

which exactly matches the coded value `44034`. When type=2 the message displays as an
asynchronous (non-halting) notice; for a synchronous (job-halting) message the type digit
would be `1` instead.

Neighbouring constants from the same definition block (lines 200–202):

```
ATC_Spindle_Not_Parked_C  IS 44034;(2+256*172) Spindle not parked.  Z Axis not tool change position.
ATC_Lock_Not_Released_C   IS 44290;(2+256*173) Tool Carousel not locked.
ATC_Lock_Released_C       IS 45546;(2+256*174) Tool Carousel locked.
```

Verify: `2+256*172=44034` ✓, `2+256*173=44290` ✓, `2+256*174=44546` — but the third
constant is coded as `45546`, not `44546`. See the gotcha below.

### ⚠️ Gotcha: verify the coded value matches the arithmetic in the comment

Line 202, `ATC_Lock_Released_C IS 45546;(2+256*174)`, is a real-world example of a
discrepancy. The comment says `(2+256*174)`, which evaluates to `44546`, but the coded
value is `45546` — `1000` too high (a transposed-digit typo). The comment is the
authoritative record of intent; the literal `45546` will not decode to a valid
plcmsg.txt entry, so this message will not display. Always sanity-check the literal
against the comment's arithmetic. Future maintainers should correct line 202 to
`44546` or confirm the intended message number.

---

## `plcmsg.txt` format

`plcmsg.txt` (e.g. `docs/official/_ALLIN1DC/_basic/cncm/plcmsg.txt`) is a plain-text
file installed in CNC12's `cncm/` directory. Each non-blank line has three
space-separated fields (no trailing comments are allowed — all text after the second
space is the message):

```
MessageNumber  MessageLogNumber  Message text
```

- **MessageNumber** — the `msgNumber` in the encoding formula above; must match the
  `_C` constant comment.
- **MessageLogNumber** — a `9xxx` or `5xxx` or `2xxx` log code written to `msglog.txt`
  (parameter 140 must be set to log level 4).
- **Message text** — displayed verbatim on the CNC12 screen; extends to end of line.

Example from `docs/official/_ALLIN1DC/_basic/cncm/plcmsg.txt` (lines 1–3, 21, 24):

```
1   9001 !!! PLC EXECUTION FAULT !!!
5   9005 Axis 1 Communication In Fault
...
21  2021 Axis Faults Cleared
...
24  2024 PLC Faults Cleared
```

Custom messages (like the Acroloc ATC messages at entries 172–174) must be **appended**
to the project's `plcmsg.txt`. Do not renumber existing entries. The stock entries are
reserved by Centroid (in `docs/official/_ALLIN1DC/_basic/cncm/plcmsg.txt` the highest is
entry 168); before adding custom entries, verify the highest-numbered stock entry in your
own `plcmsg.txt` and number new entries above it.

---

## Using a `_C` constant in stage logic

The standard pattern has two Word variables (one for fault/sync messages, one for
async/info messages) that are assigned a `_C` constant and then sent to CNC12 via
`MSG`. From `Centroid-Acroloc-ALLIN1DC.src`:

Definitions (lines 1068, 1070):
```
FaultMsg_W  IS W51
InfoMsg_W   IS W53
```

Stage logic that posts a message (lines 2859–2864):
```
IF ATCManualUnlock_I THEN
  FaultMsg_W = ATC_Lock_Not_Released_C,
  SET ShowFaultStage
IF !ATCManualUnlock_I THEN
  FaultMsg_W = ATC_Lock_Released_C,
  SET ShowFaultStage
```

And the `ShowFaultStage` that actually sends it (lines 2973–2974):
```
IF True_M THEN MSG FaultMsg_W
IF !EStopOk_M THEN FaultMsg_W = 0, ...
```

Key rules:
1. Assign the `_C` constant to a Word variable **before** calling `MSG`.
2. To clear a message, assign the "cleared" sentinel constant (`MSG_CLEARED_MSG_C` for
   fault/sync, `ASYNC_MSG_CLEAR_C` for async) before the next `MSG` call.
3. You cannot re-send the same message number without sending a different message number
   first (the CNC12 de-duplicates). Always clear then re-set if re-triggering.
4. Synchronous (type=1) messages set `SV_STOP` and block job execution until
   acknowledged. Asynchronous (type=2) messages display and clear automatically.
