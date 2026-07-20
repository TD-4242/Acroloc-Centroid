# Retro VCP Theme - Design

Date: 2026-07-13
Status: approved via interactive mockup (v34, `.superpowers/brainstorm/*/content/vcp-panel-mockup-v34.html`)
Inspiration: `~/vintage-panel-buttons.html` (vintage illuminated panel buttons) and the
original Acroloc machine badge (photo `~/20260713_211852.jpg`).

## Goal

A vintage-panel theme for the CNC12 Virtual Control Panel: dark panel, brushed-metal
bezels, amber caps for inactive functions, glowing red caps for active ones, the traced
ACROLOC nameplate across the top, and a simplified button layout for this machine.
Delivered as a **parallel skin** so the stock skin remains intact and selectable.
This retro skin becomes the **default** (selected in `options.xml`).

## Non-goals

- No changes to the PLC program, macros, or any `skin_event_num`/PLC-bit wiring.
- No changes to stock button folders or the stock/rapid skins.
- Buttons dropped from the layout (aux1-12, aux13/14 legacy, 4th axis) keep their
  folders and wiring; they are simply not placed in the retro skin.

## Deliverables

1. `resources/vcp/skins/acroloc_retro_vcp_skin.vcp` - the retro skin (grid, borders,
   group labels, nameplate image, feedrate `plc_word` readout, hover/click styling,
   dark background).
2. `resources/vcp/Buttons/retro_*/` - one folder per placed button: `retro_<name>.xml`
   (copied behavior from the stock counterpart) + state SVGs.
3. `resources/vcp/images/acroloc_nameplate.svg` - the traced ACROLOC badge on a brushed
   aluminum plate.
4. `tools/vcpgen.py` - stdlib-only generator that emits ALL of the above from a
   declarative table; `tools/test_vcpgen.py` for basic checks.
5. `options.xml` updated: `Skin` = `acroloc_retro_vcp_skin`.

## Layout (14 rows x 6 columns, as built 2026-07-15)

| Rows | Content |
|------|---------|
| 1 | ACROLOC nameplate `<image>`, cols 1-6 |
| 2 | Spindle readout `[ XXX% XXXXRPM ]` (`plc_word` 76 = `SpinOverride_W`, 77 = `SpinRPM_W`; same bezel/span as the feedrate display), cols 4-6 |
| 3-4 | SPIN MODE knob (2x2, cols 1-2). Row 3: `+` (3,4) / SPIN 100% (3,5) / `-` (3,6). Row 4: CW (4,3) / CCW (4,4) / SPIN START (4,5) / SPIN STOP (4,6) |
| 5-6 | CLNT MODE knob (2x2, cols 1-2); FLOOD M8 (5,3) over PUMP (6,3), regular 1x1 buttons. PUMP lights on the real pump output OUT4 (on for any reason) and its PLC latch (`PumpManual_M`) toggles in either coolant mode. Cols 4-6: X/Y/Z machine-coordinate readout (three 7-seg windows, `plc_word` 11/12/13 Float = `MachX/Y/Z_FW`, latched at machine zero by `cncm.hom`'s HomeSync pulse) |
| 7-8 | JOG MODE knob (2x2, cols 1-2) |
| 7-10 | Jog block: +Y (7,4), +Z (7,6), -X (8,3), hare/tortoise (8,4), +X (8,5), MPG (9,1), -Y (9,4), -Z (9,6), X1 (10,1), X10 (10,2), X100 (10,3) |
| 9 | SINGLE BLOCK (9,2) |
| 10 | TOOL CHECK (10,4) / FEED HOLD (10,5) |
| 11 | CYCLE START (11,1) / CYCLE CANCEL (11,2); RAPID 25% toggle (11,5) — rapids-only cut via `SV_PLC_RAPID_FEEDRATE_OVERRIDE` (`Rapid25_M` latch, stock `rapid_over` skin event 82 / LED OUT1133) |
| 12-14 | Round RESET, cols 1-3 (3x3 `<button ... column_span/row_span>`) |
| 12 | Feedrate readout (`plc_word` 4, DSEG7 7-seg red + separate `%` text over a bezel image), cols 4-6 |
| 13 | FEED `-` / FEED 100% / FEED `+` (cols 4-6) |
| 14 | 25% / 50% / 75% (cols 4-6) |

Group boxes: only FEEDRATE keeps a labeled `<border>`; the SPINDLE/COOLANT/AXIS JOG boxes were
dropped during on-machine testing (their labels straddled the row seams).
Background: dark (near-black, like the mockup's radial panel; skin background is a hex
color or image - use a dark hex, optionally a pre-rendered dark PNG later).

## Button design

- **Geometry**: rectangular artboard ~116x97 (the VCP renders a button at its SVG
  artboard size, so buttons come out shorter than square, leaving clearance between
  rows for the group labels). Brushed-metal bezel, dark recessed well, colored cap
  nearly filling the well (small even margin).
- **States**: amber cap = inactive; radial glowing red cap = active. Replaces the stock
  LED overlay: each stateful button uses `<plc_output>` (or `<plc_input>`/`<plc_memory>`
  where the stock button does) with `image_on`/`image_off` full-graphic swaps. The
  `<plc_output><number>` is copied verbatim from the stock button XML.
- **Legends**: mixed text/icons. Text engraved-style (dark brown on amber, dark red on
  lit red). Icons: jog arrows (arrow + axis label, arrow pointing outward from cluster
  center), small CW/CCW rotation arrows left of their lettering, MPG handwheel, stock
  flood line-art + "FLOOD"/"M8", custom pump icon + "PUMP", stock hare/tortoise artwork.
- **Momentary press feedback**: skin-level `on_click` outline (as stock); no per-button
  `on_click_swap` in v1.

### Special buttons

| Button | Off state | On state |
|--------|-----------|----------|
| CLNT MODE knob (2x2 bakelite rotary) | pointer left, "MAN" highlighted | pointer right, "AUTO" highlighted |
| SPIN MODE knob (2x2 bakelite rotary) | pointer left, "MAN" highlighted | pointer right, "AUTO" highlighted |
| JOG MODE knob (2x2 bakelite rotary) | pointer left, "CONT" highlighted | pointer right, "INCR" highlighted (bit ON = incremental, verified on-machine) |
| hare/tortoise | lit red cap + hare | amber cap + tortoise (PLC output 1094; bit is ON in tortoise/slow mode — verified on-machine 2026-07-14. Cap color is deliberately decoupled from bit state here so the hare stays red) |
| CYCLE START | solid green cap | glowing green cap |
| CYCLE CANCEL | solid red cap | glowing red cap |
| RESET | round red mushroom on square bezel, "RESET" on dome | depressed dome (lower, flatter, lip shadow, faint glow) + glowing "RESET" above / "TRIPPED" below (PLC output 1107, like stock) |

## ACROLOC nameplate

Letterforms machine-traced from the badge photo (paint mask -> Moore contour ->
Douglas-Peucker), then idealized: horizontals/verticals snapped, uniform stroke,
4-unit chamfers; the A's diagonals, R's open counter + kicked leg, and square O/C
counters preserved. Five unique glyphs (A C R O L), each normalized to the same square,
uniform pitch, maroon (#4a2028) on a brushed-aluminum plate. Full plate is one SVG
placed as the row-1 `<image>`.

Glyph path data (90x90 boxes):

- A: `M48,0 H85 L90,6 V90 H58 L45,66 L46,62 H64 L66,60 V25 H63 L38,66 L27,90 H2 L0,87 L2,82 Z`
- C: `M4,0 H86 L90,4 V24 L86,28 H32 V62 H86 L90,66 V86 L86,90 H4 L0,86 V4 Z`
- R: `M4,0 H82 L86,4 V60 L82,64 L77,66 L90,85 V88 L88,90 H62 L38,50 L36,45 L39,42 H58 V28 H28 V88 L26,90 H4 L0,86 V4 Z`
- O: `M4,0 H86 L90,4 V86 L86,90 H4 L0,86 V4 Z M26,26 H64 V64 H26 Z` (evenodd)
- L: `M4,0 H24 L28,4 V62 H86 L90,66 V86 L86,90 H4 L0,86 V4 Z`

## Generator (`tools/vcpgen.py`)

- Python 3 stdlib only (no pip on the dev box). Deterministic output.
- Declarative `BUTTONS` table: name, grid position/span, legend lines (off/on), icon
  key, cap style pair, stock XML source (for behavior copy), font size overrides.
- Emits: every `retro_*/retro_*.xml` + state SVGs, the nameplate SVG, and the skin
  `.vcp`. Running it twice produces identical bytes (safe to re-run after tweaks).
- Text rendering: the CNC12 renderer ignores `text-anchor`, so the generator computes
  explicit `x` per text line from a character-width table for Arial (Narrow) bold and
  centers manually. Known risk: metrics may need a tuning pass after the first
  on-machine look. (A follow-up could convert text to paths if needed.)
- All emitted files ASCII-only (repo convention for controller-consumed files).

## Testing / rollout

No local VCP renderer exists; validation is on the control PC:

1. `python3 tools/vcpgen.py` locally; `python3 tools/test_vcpgen.py` for structure
   checks (XML well-formed, referenced SVGs exist, skin references only existing
   buttons, ASCII-only).
2. Copy `resources/vcp/` to the control PC CNC12 directory (backup first), restart
   CNC12.
3. On-machine checklist: skin loads (no VCP error), every button renders at correct
   size/position, state swaps track the machine (spindle, coolant, incr/cont polarity,
   hare/tortoise, reset tripped), legends centered, group labels visible, feedrate
   readout live.
4. Rollback: set `options.xml` back to `servo_mill_vcp_skin`.

Integration: work on branch `retro-vcp-theme`, PR to `main` with the retro skin set as
default.
