# Feedrate preset knob: four buttons rendered as one analog dial

Date: 2026-08-07
Status: approved

## Goal

Replace the four flat feedrate preset buttons (25 / 50 / 75 / 100%) on the retro VCP with a
single analog-looking rotary dial, in the style of the machine's original panel hardware. The
dial is built from four ordinary VCP buttons tiled 2x2; the selected preset draws a needle.

Visual reference: `~/switch.png`, the original FEEDRATE OVERRIDE knob (see "Dial face range"
for why the reproduction is deliberately not exact).

## Constraint that shapes the whole design

A VCP button has exactly **two** image states, `image_on` / `image_off`, selected by a single
PLC output bit (`.claude/skills/centroid-vcp/reference/visual-states.md`). There is no
rotation primitive, no gauge widget, and no way to drive an image from a PLC *word* — a
`<plc_word>` renders numeric text only. A continuously-swept needle is therefore impossible.
Every needle position must be baked into a static SVG chosen by a binary bit.

Four buttons x two states is the entire budget.

## Design

### Revision 2026-08-07: the face is a skin `<image>`, not button art

The first implementation split the dial face across the four button images. **It does not work,
and cannot.** The VCP always draws separate buttons with a gap between them and the skin
exposes no spacing control, so a face split across four button images is rendered as four
tiles with visible gaps — confirmed on the machine. The stock `coolant_auto_man` and
`incr_cont` knobs look continuous only because each is a *single* button with
`row_span=2 col_span=2`; one button means one skin event, which cannot carry four presets.

The fix is to separate the face from the needles:

- The **face** — panel, tick ring, labels, knob cap — is a skin `<image>` spanning rows 13-14,
  cols 4-5. An `<image>` covers a cell range without button chrome and without inter-button
  gaps, so it renders as one continuous graphic. This repo already uses the mechanism for
  `feedrate_bezel.svg`.
- The **needles** stay in the four buttons, which keep their skin events and LED bits, but
  their SVGs are now *fully transparent apart from the needle* so the face shows through,
  including through the gaps. The off state is an empty SVG.

One consequence needs calibration: the face `<image>` spans the whole cell range **including**
the gaps, while each needle is drawn in its own button's coordinate system, whose shared corner
therefore sits half a gap outside the face's true centre. `FKNOB_GAP_COMP` shifts each needle's
pivot back onto that centre. It ships at `0.0`; at realistic VCP spacing (2-4 px) the resulting
tip error is under 2 degrees against 15-degree tick spacing, but if the arrows visibly miss the
printed face, that is the single number to raise.

### Revision 2: face-space windows, measured calibration, vintage skirt

Machine screenshots showed the pointer displaced outward along each quadrant's diagonal.
Measuring them settled why. On this VCP a button is **79 x 63 px on a 111 px column pitch and
a 107 px row pitch** — a 41 px vertical gap, about 40% of the pitch. Consequences:

- **A button window does not reach the dial centre.** Its nearest corner is ~26 px away, about
  one cap radius. No amount of pivot compensation fixes that; `FKNOB_GAP_COMP` is deleted.
- **Pointers must lie along their window's diagonal.** The previous 255-degree angle for 25%
  fell entirely outside the SW window and would have rendered invisible. The presets therefore
  sit on the four diagonals, 90 degrees apart: `theta = 3.6 * value + 135`. That puts a
  90-degree dead zone at the bottom, like a real knob stop, and the scale is drawn from 25 to
  100 only.
- **Everything is expressed in face coordinates.** Each needle SVG declares a `viewBox` equal
  to the exact window of face space its button covers, so face and pointer share one
  coordinate system and align by construction. Each window's aspect equals its button's
  aspect, so nothing letterboxes. The window also clips the pointer's inner end, so it appears
  to emerge from the cap rather than from a pivot the button cannot reach.

An earlier revision had a second letterbox bug worth recording: a VCP button viewport is not
the 116x97 ordinary buttons assume, so a mismatched artboard is scaled to fit one axis and
centred on the other. Ordinary buttons never notice because their content is centred anyway,
but corner-anchored geometry shifts. Matching the viewBox aspect to the viewport is the fix.

Appearance follows the original hardware: a **silver/aluminium skirt** out to the tick marks,
a **black pointer on top of it**, and a black bakelite cap at the centre.

The five calibration numbers (`FK_BTN_PX`, `FK_COL_PITCH`, `FK_ROW_PITCH`, `FK_PX_PER_UNIT`,
`FK_PAD_PX`) are the only things to re-measure if the VCP is resized or the grid changes.

### Geometry

The dial's centre is the centre of the 2x2 cell range. Each button owns one 90-degree sector,
and the needle for a given preset is drawn from that centre outward into its own sector, so it
lies **entirely within its own button's cell** — still required, because a button can only
draw inside itself.

Angles below are measured clockwise from straight up (North).

| Cell | Grid position | Sector | Preset | Needle angle |
| --- | --- | --- | --- | --- |
| NW | row 13, col 4 | 270-360 | **50%** | 330 |
| NE | row 13, col 5 | 0-90 | **75%** | 45 |
| SW | row 14, col 4 | 180-270 | **25%** | 255 |
| SE | row 14, col 5 | 90-180 | **100%** | 120 |

The scale runs 0 at the bottom (180) sweeping **300 degrees clockwise** to 100 (at 120), a
3.0 degrees-per-percent scale, leaving a 60-degree dead gap between the 100 end and the 0 start.
Every preset lands inside a distinct sector with at least **15 degrees** of clearance from the
nearest cell boundary (the tightest is 25% at 255, which is 15 degrees off the 270 boundary).

> **This geometry is a starting point, tuned on paper.** The sweep, start angle and gap are
> single constants in the generator. Expect to adjust them once the dial is seen on the actual
> panel; that is a one-line change plus a regenerate, not a redesign.

Face detail: minor ticks every 5%, major labelled ticks at 25 / 50 / 75 / 100, a knob cap
drawn across all four cells, and the existing retro palette. The cap and face render
identically in both states — **only the needle differs between `image_off` and `image_on`** —
so switching presets changes nothing on screen except which needle appears.

### Layout

```
        col 4        col 5        col 6
row 13  +---------------------+  +--------+
        |   50 \      / 75    |  |   -    |
        |       \    /        |  +--------+
row 14  |   25 --(o)-- 100    |  |   +    |
        +---------------------+  +--------+
         knob spans 2x2          stacked
```

`feedrate_negative` and `feedrate_positive` move to column 6, stacked. This consumes exactly
the **same six cells** the flat buttons use today (rows 13-14, cols 4-6), inside the existing
`FEEDRATE` group box. Row 14 is the last row of the grid, so no other arrangement fits.

### No PLC change

Each quadrant keeps the skin event and LED bit its flat predecessor already used:

| Preset | Skin event | PLC output |
| --- | --- | --- |
| 25% | 113 | OUT1140 |
| 50% | 112 | OUT1139 |
| 75% | 111 | OUT1138 |
| 100% | 53 | OUT1137 |

`Centroid-Acroloc-ALLIN1DC.src` is **not touched**. The existing rungs at src:1978-1981 drive
these four bits off `FinalFeedOverride_W == 100 / 75 / 50 / 25`, which are mutually exclusive
by construction, so at most one needle is ever drawn.

Because the LED is replaced by a whole-image swap, each button's `<plc_output>` block carries
`<image_on>` / `<image_off>` instead of `<color_on>` / `<color_off>` — the same shape the
`reset` button already uses.

### Off-preset behaviour: no needle

The rungs test **exact equality**, so at any value the `-` / `+` buttons produce that is not
exactly 25/50/75/100 — including anything above 100, which P39 permits — **no bit is lit and
no needle is drawn.** The bare dial face shows.

This is intentional and was chosen over range-based ("snap to nearest") bits. A needle that
pointed at 75 while the true override was 63 would be a machine control lying about its state.
The seven-segment `FEEDRATE` readout, which displays `FinalFeedOverride_W` directly, remains
the source of truth and is unchanged.

Consequence worth expecting: during a G74/G84 tapping cycle CNC12 forces the applied override
to 100, so the needle jumps to the 100 position for the cycle and returns afterward. That is
the same behaviour the flat LEDs already show (see
[../../plc-spec/main-stage.md](../../plc-spec/main-stage.md), "Feedrate override LEDs and the
tapping lockout").

### Dial face range: 0-100, not 0-200

`switch.png` is a 0-200 face with 50/100/150 labelled. **That cannot be reproduced by this
scheme, and the two are mutually exclusive.** On a 0-200 face the presets 25/50/75/100 all fall
within roughly the first half of the sweep, clustering into one or two sectors — two buttons
would own two presets each and two would own none, destroying the one-needle-per-cell property
the design depends on.

The face therefore reads 0-100. It will read as an analog knob in the spirit of the original,
not as a replica of it. This trade was raised explicitly during design and the four-button
knob was chosen over photo fidelity.

## Implementation

All work is in `tools/vcpgen.py` and its generated output. **Never hand-edit anything under
`resources/vcp/`** — it is emitted.

- Add `render_feedrate_dial_face_svg()` (the continuous 2x2 face, emitted to
  `resources/vcp/images/feedrate_dial.svg` and placed by a skin `<image>`) and
  `render_feedrate_needle_svg(quadrant, on)` (transparent, needle only). Superseded first
  attempt, kept for the record: a single `render_feedrate_knob_svg(quadrant, on)` returning
  the SVG for one cell, face included. It sits
  alongside the existing `render_knob_svg()` (tools/vcpgen.py:394), which already performs the
  same rotate-a-knob-by-a-PLC-bit trick for the two-position SPIN/CLNT/JOG mode selectors and
  is the pattern to follow for artboard sizing and palette.
- Replace the four `feedrate_25/50/75/100` entries in `BUTTONS` with the 2x2 knob quadrants,
  and move `feedrate_negative` / `feedrate_positive` to column 6.
- Emit eight SVGs (four quadrants x on/off) plus the four button XMLs carrying
  `image_on`/`image_off`.
- Extend `tools/test_vcpgen.py`.

The generator only ever creates and overwrites; **it never deletes stale output.** The
previously emitted `retro_feedrate_25/50/75/100` button directories will be orphaned and must
be removed explicitly with `git rm -r`.

## Verification

- `python3 tools/test_vcpgen.py` — existing 21 tests plus new coverage.
- `./compile.sh` — expected **unchanged** at main's baseline (5040 tokens, 190 warnings), since
  no `.src` edit is made. Any change here means something was touched that should not have been.
- No orphaned `retro_feedrate_*` directories remain; no skin reference points at a deleted
  button (a skin referencing a missing button directory is the usual cause of the VCP failing
  to load).
- Machine check: load the VCP, confirm it opens, confirm each of the four quadrants selects its
  preset and draws its needle, and confirm the needle disappears after a `-` / `+` nudge.

## Out of scope

- Any change to `Centroid-Acroloc-ALLIN1DC.src`.
- Range-based / "snap to nearest" needle behaviour.
- Reproducing the 0-200 face from `switch.png`.
- The `-` / `+` button artwork beyond relocating them to column 6.
- The seven-segment `FEEDRATE` numeric readout, which is unchanged.
