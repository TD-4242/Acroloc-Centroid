# F510 RS-485 Modbus Communication

How to talk to the F510 over serial — for run/frequency control and, most usefully here, to
**back up and restore the whole parameter set from a PC**. Source: §6.3, §7.3, Group 09
(§4.2 p.100), monitor `12-42`.

## Interface

- **Physical:** a built-in **RS-485** port on connector **CN6** (8-pin RJ45-style). The two
  data lines are **`S+`** and **`S-`** (pin 1 = S+, pin 2 = S-); tie cable shield to the
  control ground terminal. (§6.3 / §7.3 diagrams.) The same port is used whether you command
  the drive or just read from it.
- **Protocol:** **Modbus RTU**. (`09-01` = 0 selects MODBUS; the drive also offers BACNET,
  METASYS, Pump-parallel, and PROFIBUS on `09-01`.) The link supports (verbatim §7.3):
  1) monitoring (data/function read), 2) frequency setting, 3) operation command (FWD, REV,
  and other digital-input commands), 4) writing function data.
- **Function codes:** standard Modbus — **`03`** read holding registers, **`06`** write
  single register. Each frame ends in a **CRC16** (last two bytes).

## Selecting RS-485 as the command source

To *drive* the motor over RS-485 (as opposed to just reading), point the sources at
communication:

- **Run command:** `00-02` = **2** ("Communication Control (RS-485)").
- **Frequency command:** `00-05` = **3** ("Communication Control (RS-485)").

> Manual inconsistency to be aware of: the §7.3 body text says "set `00-02` to 3", but that
> section's own option list and the Group 00 table (§4.2) both define `00-02` **2** as
> Communication Control and 3 as PLC. Trust the option list: **2 = communication** for
> `00-02`; **3 = communication** for `00-05`. Verify on the drive's own parameter screen.
>
> You do **not** need these set to read parameters for a backup — reads work regardless of
> the command source.

## Group 09 — communication setup (§4.2 p.100)

| Code | Name | Range / options | Default |
| --- | --- | --- | --- |
| 09-00 | INV Communication Station Address | 1–31 | 1 |
| 09-01 | Communication Mode | 0 MODBUS · 1 BACNET · 2 METASYS · 3 Pump-parallel · 4 PROFIBUS | 0 |
| 09-02 | Baud Rate | 0:1200 · 1:2400 · 2:4800 · 3:9600 · 4:19200 · 5:38400 | 4 (19200) |
| 09-03 | Stop Bit | 0: 1 stop bit · 1: 2 stop bits | 0 |
| 09-04 | Parity | 0 None · 1 Even · 2 Odd | 0 |
| 09-05 | Data Bits | 0: 8-bit · 1: 7-bit | 0 |
| 09-06 | Communication Error Detection Time | 0.0–25.5 s | 0.0 |
| 09-07 | Fault Stop Selection | 0 decel(time1)·1 coast·2 decel(time2)·3 keep running·4 run freq by AI2 on comm fault | 3 |
| 09-08 | Comm Fault Tolerance Count | 1–20 | 1 |
| 09-09 | Waiting Time | 5–65 ms | 5 |
| 09-10 | Device Instance Number | 1–254 | 1 |

**Important (verbatim §4.2):** "Parameters in group 09 are **not** affected by a parameter
initialization (`13-08`)." So a factory-restore will not change your comm settings — but it
also will not restore them from a backup unless you write them explicitly.

**Default-setting discrepancy:** §6.3/§7.3 state the factory default as "Address 1, 9600
bps, 1 start / 1 stop bit, No Parity", while the `09-02` default is **4 = 19200**. Read the
actual `09-00`–`09-05` values off the drive before connecting; set your master to match.

## Key control registers (Modbus, hexadecimal)

| Register | Meaning | Notes |
| --- | --- | --- |
| `2501h` | **Command register** | Bit 0 = Run Forward · Bit 1 = Run Reverse · Bits 2–15 other digital-input commands (see manual) |
| `2502h` | **Frequency reference** | Value = Hz × 100, range 0.00–400.00 Hz (i.e. 0–40000) |

**Examples** (write single register, function `06`, node address `01`; last two bytes are
CRC16):

```
Run Forward :  01 06 25 01 00 01 12 C6
Run Reverse :  01 06 25 01 00 03 93 07
Stop        :  01 06 25 01 00 00 D3 06
Freq 10.00Hz:  01 06 25 02 03 E8 23 B8      ; 0x03E8 = 1000 = 10.00 Hz
Freq 30.00Hz:  01 06 25 02 0B B8 24 44      ; 0x0BB8 = 3000
Freq 60.00Hz:  01 06 25 02 17 70 2D 12      ; 0x1770 = 6000
```

## Reading / backing up the full configuration to a PC

There is **no keypad parameter-copy/clone** on the F510 (Groups 13 and 16 have none), so
RS-485 is the config-transfer path.

1. **Wire it:** a **USB-to-RS-485 adapter** from the PC to CN6 `S+`/`S-` (shield to control
   ground).
2. **Match settings:** read `09-00`–`09-05` off the drive and configure your Modbus master to
   the same address / baud / parity / stop / data bits.
3. **Back up (read):** use Modbus function **`03`** to read the holding registers for every
   parameter and log them to a file. Each parameter `GG-CC` occupies a holding register
   addressed in hex (the control/frequency registers above, `2501h`/`2502h`, show the
   scheme). For the **full per-parameter register map**, use TECO's Modbus register table /
   the option-card documentation (§11.6) or a **vendor PC tool**, which already knows the
   map — this manual spells out only the command/monitor registers, not every parameter's
   address.
4. **Restore / clone (write):** write the saved values back with function `06` (or `10h` for
   multiple registers). Remember Group 09's own values won't come back via `13-08`
   restore-factory — write them explicitly if needed.

> For a mill spindle driven by the controller's 0–10 V analog command, RS-485 is typically
> used for **backup/restore and diagnostics**, not for live speed control (that stays on the
> analog line). See `SKILL.md` "controller ↔ VFD seam".

## Diagnostics

- **`12-42` RS-485 Error Code** — a bitfield reporting CRC error, data-length, illegal
  function, parity, overrun, and framing errors. Read it when comms are flaky.
- `09-06` (error-detection time), `09-08` (fault tolerance count) and `09-07` (fault-stop
  action) govern how the drive reacts to a dropped link.
