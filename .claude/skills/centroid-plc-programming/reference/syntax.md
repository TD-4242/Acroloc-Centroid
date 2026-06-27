# Centroid PLC Language: Syntax Reference

**Sources used:**
- `scratchpad/plc-manual.txt` — extracted text of Centroid CNC PLC and CNC Functions Programming Manual rev7 (2022–23)
- `docs/official/_ALLIN1DC/_basic/cncm/allin1dc-basic-v6.src` — Centroid stock ALLIN1DC basic PLC, shipped with CNC12

Every code example below is a real line from one of those two sources, cited by line number.

---

## Execution Model

The PLC program is a **flat, sequential list of stages** (STG-numbered). On every **scan**, the executor sweeps the file from top to bottom and runs every `IF` statement it encounters — but **only within stages that are currently SET**. A stage whose bit is not SET is skipped entirely; logic inside it is not evaluated.

- **Regular stages** (`STG` type) execute at **50 scans per second**.
- **Fast stages** (`FSTG` type) and code placed outside any stage execute at **1000 scans per second**.
- On each scan, a snapshot of hardware inputs is taken at the start; reads of the same input return the same value throughout that scan.
- **Memory bits, Words, One-Shots, System Variable bits, Stage bits, and the output image update live** during the scan — a later line in the same scan sees the new value written by an earlier line.
- Only the **hardware input snapshot and Timer values are frozen** for the full scan: they hold the same value at the start of the pass as at the end. The output image is **not** frozen — it can be changed on any line, and a later line that reads an output sees the value an earlier line in the same scan wrote.

> Manual ref: `scratchpad/plc-manual.txt` lines 504–517

`STG1` is SET automatically by the executor at startup. Stages enable and disable each other with `SET` and `RST`:

```
; In InitialStage: run once, then hand control to MainStage and never return.
IF 1==1 THEN SET True,             ; allin1dc-basic-v6.src, line 1057
             SET MainStage,        ; allin1dc-basic-v6.src, line 1060
             RST InitialStage      ; allin1dc-basic-v6.src, line 1076
```

When a stage is RST, whatever its internal variables were SET or RST to **remain** in that state until modified by code elsewhere. No checks are made against RST-ing every stage simultaneously — if all stages are RST, the program loops uselessly.

---

## Statement Forms

### 1. Definition — `Name IS Resource`

Used **only** in the definition section at the top of the file, before the first `IF` statement. Binds a symbolic name to a hardware resource or system variable. At compile time the name is substituted; it has no runtime cost.

```
Ax1_MinusLimitOk              IS INP1          ; allin1dc-basic-v6.src, line 168
EStopOk                       IS INP11         ; allin1dc-basic-v6.src, line 178
PLCExecutorFault_M            IS MEM1          ; allin1dc-basic-v6.src, line 482
WatchDogStage                 IS STG1          ; allin1dc-basic-v6.src, line 1001
MainStage                     IS STG4          ; allin1dc-basic-v6.src, line 1004
```

Constants can include arithmetic, and may reference previously defined constants (wrap the whole expression in parentheses):

```
DEFINED_CONSTANT              IS (1+2+5*7)     ; plc-manual.txt, line 731
SECOND_CONST                  IS (DEFINED_CONSTANT*10)  ; plc-manual.txt, line 732
```

No definition is allowed after the first `IF` statement; the compiler will reject it.

### 2. Conditional statement — `IF <condition> THEN <action> [, <action>]*`

Every executable line begins with `IF`. Multiple actions after `THEN` are **comma-separated**. A single statement may span multiple physical lines; continuation lines are indented past the `IF` column.

```
IF SV_PLC_FAULT_STATUS != 0                          ; allin1dc-basic-v6.src, line 1035
  THEN PLC_Fault_W    = SV_PLC_FAULT_STATUS,         ; allin1dc-basic-v6.src, line 1037
       PLCFaultAddr_W = SV_PLC_FAULT_ADDRESS,
       SET PLCExecutorFault_M, RST MessageStage, SET SV_STOP
```

The unconditional idiom uses a relational tautology:

```
IF 1==1 THEN SET True,                               ; allin1dc-basic-v6.src, line 1057
             SET OnAtPowerUp_M,
             SET AxesEnableStage
```

There is **no ELSE keyword**. Complement a condition explicitly with a second line:

```
IF LubeS_W == 0 THEN SET LubeUsePumpTimersStage, RST LubeUsePLCTimersStage  ; allin1dc-basic-v6.src, line 1131
IF LubeS_W != 0 THEN SET LubeUsePLCTimersStage, RST LubeUsePumpTimersStage  ; allin1dc-basic-v6.src, line 1132
```

### 3. Word assignment — `<Word> = <expression>`

Assigns a value to a Word, Timer, or Floating-point Word. Appears as an action on the right side of `THEN`. Word types cannot appear bare as conditions; they must be used in a relational expression.

```
IF 1==1 THEN W1 = 10                        ; plc-manual.txt, line 1023
IF True THEN Lube_W = SV_MACHINE_PARAMETER_179,     ; allin1dc-basic-v6.src, line 1126
             LubeM_W = (Lube_W / 100) * 60000,
             LubeS_W = (Lube_W % 100) * 1000
```

### 4. Output Coil — `(<VarName>)`

Parentheses on the right side of `THEN` form a **coil**: the variable is SET if the condition is true, and RST if the condition is false. This is unlike `SET`/`RST`, which act unconditionally regardless of the IF result.

```
IF MEM1 THEN (OUT2)                         ; plc-manual.txt, line 1076 — SET if MEM1 true, RST if MEM1 false
```

Caution: do not mix coils and explicit `SET`/`RST` on the same variable across different lines — the last scan-order write wins and results are often surprising.

### 5. Jump — `JMP <stage>`

RSTs the current stage and SETs the named stage. Does not change the execution point within the current scan; execution continues below the `JMP` line and into the newly SET stage on the next scan.

```
IF 1==1 THEN JMP MainStage                  ; plc-manual.txt, line 1105 — typical end of InitialStage
```

---

## Operators

### Logical Operators

Apply to **bit-type variables only** (inputs, outputs, memory bits, stages, fast stages, one-shots, SV bits, timers). Cannot be applied directly to Word-type variables.

| Symbol | Meaning | Confirmed example |
|--------|---------|-------------------|
| `&&` | AND — both sides must be true | `IF MEM1 && INP2 THEN (OUT1)` (plc-manual.txt, line 1195) |
| `\|\|` | OR — either side must be true | `IF (SV_PROGRAM_RUNNING \|\| SV_MDI_MODE) THEN SET Lube` (allin1dc-basic-v6.src, line 1216) |
| `!` | NOT (unary) — inverts a single bit | `IF !SV_PC_SOFTWARE_READY && (SV_PLC_FAULT_STATUS == 0)` (allin1dc-basic-v6.src, line 1042) |
| `XOR` or `^` | Exclusive OR — exactly one side true | `IF RapidOverPD^ SelectRapidOverride THEN (SelectRapidOverride)` (plc-manual.txt, line 4772) |

A relational comparison result (a boolean bit) can be combined with logical operators:

```
IF (W1 > W2) || !MEM4 THEN (OUT5)          ; plc-manual.txt, line 1196
```

Parentheses may be used freely for grouping to override default precedence.

### Relational Operators

Apply to **Word-type variables, SV Words, and Timers** only. Bit-type variables cannot be compared with these operators. The result is a boolean (true/false) that can be used in a logical expression.

| Symbol | Meaning | Confirmed example |
|--------|---------|-------------------|
| `==` | Equal to | `IF SV_PC_SOFTWARE_READY && (SV_PLC_FAULT_STATUS == 0)` (allin1dc-basic-v6.src, line 1047) |
| `!=` | Not equal to | `IF SV_PLC_FAULT_STATUS != 0` (allin1dc-basic-v6.src, line 1035) |
| `>` | Greater than | `IF W1 > W2 THEN (OUT1)` (plc-manual.txt, line 1145) |
| `<` | Less than | `IF SV_PLC_SPINDLE_KNOB < 1  THEN SV_PLC_SPINDLE_KNOB = 1` (allin1dc-basic-v6.src, line 1859) |
| `>=` | Greater than or equal | `IF ( p171_W <= 0) \|\| ( p171_W >= 10) THEN LubeOut_W = 2` (plc-manual.txt, line 973) |
| `<=` | Less than or equal | `IF ( p171_W <= 0) \|\| ( p171_W >= 10) THEN LubeOut_W = 2` (plc-manual.txt, line 973) |

Note: Using `==` or `!=` with Floating-point Words may fail due to rounding error; prefer `>=`/`<=` for floating-point comparisons.

Using a Timer with relational operators checks the **current elapsed count in ms**, not whether it has expired:

```
IF T1 > 4000 THEN SET OUT 6                 ; plc-manual.txt, line 763 — has 4 seconds elapsed?
```

### Arithmetic Operators

Apply to **Word types only** (integer Words, floating-point Words, timers). Evaluated when computing the right-hand side of an assignment.

| Symbol | Meaning | Confirmed example |
|--------|---------|-------------------|
| `*` | Multiply | `IF 1==1 THEN W1 = 15*2` (plc-manual.txt, line 1117) |
| `/` | Divide | `IF 1==1 THEN W2 = 128 / 2` (plc-manual.txt, line 1120) |
| `+` | Add | `IF StopRunningPD THEN LubeAccumTime_W = LubeAccumTime_W + LubeM_T, RST LubeM_T` (allin1dc-basic-v6.src, line 1246) |
| `-` | Subtract | `KbOverride_W = KbOverride_W - 1` (allin1dc-basic-v6.src, line 1601) |
| `%` | Modulus (remainder) | `IF 1==1 THEN W3 = 15 % 2` (plc-manual.txt, line 1122) |

Assigning a floating-point result to an integer Word **truncates** the decimal portion (not rounded). The manual states this in prose (plc-manual.txt, line 1114): the line `IF 1==1 THEN W1 = 2.5*1` will result in W1 being set to 2.

### Assignment Operator

| Symbol | Meaning | Confirmed example |
|--------|---------|-------------------|
| `=` | Assign value to a Word or Timer | `IF 1==1 THEN W1 = 10` (plc-manual.txt, line 1023) |

Assignment may only appear as an **action** (right side of `THEN`), never in a condition.

---

## Conditions vs. Actions

The IF/THEN statement divides into two roles:

### What may appear in the condition (between `IF` and `THEN`)

- Any **bit-type variable** directly: input (`INP`), output (`OUT`), memory bit (`MEM`), stage (`STG`), fast stage (`FSTG`), one-shot (`PD`), SV bit, timer (evaluates to true when timer has expired/reached its set point)
- Any **relational expression** on a Word, SV Word, or Timer: `W1 > 10`, `SV_MACHINE_PARAMETER_800 == 0`
- Combinations using logical operators: `&&`, `||`, `!`, `XOR`/`^`
- Parentheses for grouping: `(W1 > W2) || MEM4`

A bare Word **cannot** appear as a condition. `IF W1 THEN SET OUT1` is a compiler error; `IF W1 > 0 THEN SET OUT1` is valid.

### What may appear as actions (after `THEN`, comma-separated)

| Action form | Effect |
|-------------|--------|
| `SET <bit-var>` | Turns on a bit variable unconditionally |
| `RST <bit-var>` | Turns off a bit variable unconditionally |
| `<word-var> = <expression>` | Assigns a computed value to a Word or Timer |
| `(<bit-var>)` | Output coil: SET if condition true, RST if condition false |
| `JMP <stage>` | RSTs current stage, SETs target stage |
| `MSG <word-var>` | Sends a message number to the CNC operator display |
| `SET <timer>` then `<timer> = <ms-value>` | Starts a timer counting (value assigned first, then SET) |

---

## Comments

Comments begin with `;` and extend to the **end of the line**. There is no block comment syntax.

```
EStopOk                       IS INP11         ; allin1dc-basic-v6.src, line 178
```

### Stage header convention

Stage names are centered on a line by themselves, surrounded above and below by a full-width line of `=` characters. This is the delimiter that makes stage boundaries visually obvious in the source file (from `allin1dc-basic-v6.src`, lines 1025–1030):

```
;=============================================================================
                          WatchDogStage
;=============================================================================
```

### Section header convention

Sub-sections within a stage use a full-width line of `-` characters:

```
;----------------------------------------------------------------
; METHOD 1 (SS == 0) For lube pumps with internal timers.
;----------------------------------------------------------------
```

### Definition alignment convention

In the definition section, the `IS` keyword is column-aligned across all definitions in a group. Comments trail at a consistent column:

```
Ax1_MinusLimitOk              IS INP1          ; allin1dc-basic-v6.src, line 168
EStopOk                       IS INP11         ; allin1dc-basic-v6.src, line 178
PLCExecutorFault_M            IS MEM1          ; allin1dc-basic-v6.src, line 482
```

Custom additions to stock code are tagged with a trailing comment identifying their origin (e.g., `; Acroloc`).
