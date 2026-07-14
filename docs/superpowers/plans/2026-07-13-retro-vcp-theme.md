# Retro VCP Theme Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Generate a vintage-panel VCP theme (parallel skin `acroloc_retro_vcp_skin`, set as default) from a single stdlib-only Python generator, per `docs/superpowers/specs/2026-07-13-retro-vcp-theme-design.md`.

**Architecture:** One generator module `tools/vcpgen.py` holds all geometry, styles, icons, traced nameplate glyphs, and a declarative `BUTTONS` table. Running it emits every artifact: `resources/vcp/Buttons/retro_*/` (XML + state SVGs), `resources/vcp/images/acroloc_nameplate.svg`, and `resources/vcp/skins/acroloc_retro_vcp_skin.vcp`. Behavior (skin events, PLC bits) is copied from the stock button XMLs at generation time; only graphics are new. `tools/test_vcpgen.py` validates structure into a temp dir.

**Tech Stack:** Python 3 stdlib only (`os`, `re`, `unittest`, `xml.etree`, `tempfile`). No pip, no pytest (dev box has neither). SVG 1.1, Centroid VCP skin XML.

## Global Constraints

- Python: stdlib only, runs as `python3 tools/vcpgen.py` from any cwd (paths derived from `__file__`).
- All emitted files 7-bit ASCII (repo convention for controller-consumed files). Use `-` not unicode minus in legends.
- Deterministic output: running the generator twice yields byte-identical files. No timestamps, no randomness (fixed gradient/filter ids are fine because each SVG is its own document).
- Do NOT modify: `Centroid-Acroloc-ALLIN1DC.src`, `mfunc*.mac`, any stock button folder, `servo_mill_vcp_skin.vcp`, `servo_mill_vcp_rapid_skin.vcp`.
- Stock XML is the single source of truth for `skin_event_num` / `plc_output` numbers — never hard-code them in the table.
- The CNC12 renderer ignores `text-anchor`: every `<text>` gets an explicit computed left-edge `x` and NO `text-anchor` attribute.
- Branch: `retro-vcp-theme`. Commit after every task. PR to `main` at the end.
- Tests run with: `python3 tools/test_vcpgen.py` (unittest, not pytest).

---

### Task 1: Generator core — geometry, styles, text metrics, button SVG renderer

**Files:**
- Create: `tools/vcpgen.py`
- Create: `tools/test_vcpgen.py`

**Interfaces:**
- Produces: `vcpgen.render_button_svg(lines, style, icon='', fs=15, text_y=None, text_x=None, span=1) -> str` (complete SVG document, trailing newline); `vcpgen.STYLES` dict with keys `amber, lit, red, green, grnlit`; `vcpgen.text_width(s, fs) -> float`; `vcpgen.text_el(s, cx, y, fs, fill) -> str`.
- Coordinate contract: single-cell artboard `viewBox 0 0 116 97`, rendered `width=100 height=84` (stock buttons are 100x100; shorter height creates the row-seam clearance for group labels). Cap rect at x14 y15 w(vbw-28) h66. Icon/text content is wrapped in `<g transform="translate(0,-10)">` so all content coordinates use the mockup's center-(58,58) system. Default text_y (content coords): 1 line `[63]`, 2 lines `[51,69]`.

- [ ] **Step 1: Write the failing test**

```python
# tools/test_vcpgen.py
import os
import sys
import unittest
import xml.etree.ElementTree as ET

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import vcpgen


class TestButtonSvg(unittest.TestCase):
    def test_amber_button_parses_and_is_ascii(self):
        svg = vcpgen.render_button_svg(['SPIN', '100%'], 'amber')
        svg.encode('ascii')                      # raises if non-ASCII
        root = ET.fromstring(svg)                # raises if malformed
        self.assertEqual(root.get('width'), '100')
        self.assertEqual(root.get('height'), '84')
        self.assertEqual(root.get('viewBox'), '0 0 116 97')

    def test_no_text_anchor_and_explicit_x(self):
        svg = vcpgen.render_button_svg(['FLOOD'], 'amber')
        self.assertNotIn('text-anchor', svg)
        self.assertIn('<text x="', svg)

    def test_lit_style_has_glow(self):
        svg = vcpgen.render_button_svg(['X1'], 'lit')
        self.assertIn('feGaussianBlur', svg)
        off = vcpgen.render_button_svg(['X1'], 'amber')
        self.assertNotIn('feGaussianBlur', off)

    def test_span_widens_artboard(self):
        svg = vcpgen.render_button_svg(['RESET'], 'red', span=3)
        root = ET.fromstring(svg)
        self.assertEqual(root.get('width'), '300')
        self.assertEqual(root.get('viewBox'), '0 0 348 97')

    def test_text_width_monotonic(self):
        self.assertLess(vcpgen.text_width('I', 15), vcpgen.text_width('W', 15))
        self.assertAlmostEqual(vcpgen.text_width('', 15), 0.0)


if __name__ == '__main__':
    unittest.main()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python3 tools/test_vcpgen.py`
Expected: FAIL / ERROR with `ModuleNotFoundError: No module named 'vcpgen'`

- [ ] **Step 3: Write the implementation**

```python
#!/usr/bin/env python3
"""Generate the Acroloc retro VCP theme (skin + buttons + nameplate).

Stdlib-only and deterministic. Emits ASCII-only files:
  resources/vcp/images/acroloc_nameplate.svg
  resources/vcp/Buttons/retro_<name>/  (XML + state SVGs)
  resources/vcp/skins/acroloc_retro_vcp_skin.vcp

Usage: python3 tools/vcpgen.py            # writes into the repo tree
Design: docs/superpowers/specs/2026-07-13-retro-vcp-theme-design.md
"""
import os
import re

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# ------------------------------------------------------------- geometry ---
VB_W, VB_H = 116, 97           # single-cell artboard (viewBox units)
RENDER_W, RENDER_H = 100, 84   # rendered size; stock buttons are 100x100

# ------------------------------------------------------------ cap styles --
STYLES = {
    'amber':  dict(grad=('linear', (('0', '#e3ac5c'), ('0.55', '#c88a3e'), ('1', '#8a5a24'))),
                   stroke='#5a3a18', text='#3a2008', glow=False),
    'lit':    dict(grad=('radial', (('0', '#ff8a8a'), ('0.45', '#ee2222'), ('1', '#8c0000'))),
                   stroke='#ff6f6f', text='#4a0008', glow=True),
    'red':    dict(grad=('linear', (('0', '#d94040'), ('0.55', '#a81c1c'), ('1', '#5c0808'))),
                   stroke='#4a0000', text='#ffd9d9', glow=False),
    'green':  dict(grad=('linear', (('0', '#3aa060'), ('0.55', '#12703a'), ('1', '#053a1c'))),
                   stroke='#003a18', text='#d9ffe4', glow=False),
    'grnlit': dict(grad=('radial', (('0', '#8affb0'), ('0.45', '#1ecc55'), ('1', '#00591f'))),
                   stroke='#6fff9e', text='#00350f', glow=True),
}

# ------------------------------------------------------------ text metrics -
# Arial Narrow Bold width fractions (of font size). The CNC12 renderer
# ignores text-anchor, so every <text> gets an explicit left-edge x.
CHAR_W = {
    'I': 0.26, 'J': 0.40, 'L': 0.42, 'F': 0.44, 'T': 0.46, 'E': 0.46,
    'M': 0.68, 'W': 0.70, '%': 0.72, '+': 0.48, '-': 0.34, ' ': 0.24,
    '/': 0.26, '.': 0.22, '1': 0.40,
}
CHAR_W_DEFAULT = 0.50
LETTER_SPACING = 0.4


def text_width(s, fs):
    if not s:
        return 0.0
    w = sum(CHAR_W.get(c, CHAR_W_DEFAULT) for c in s) * fs
    return w + LETTER_SPACING * (len(s) - 1)


def text_el(s, cx, y, fs, fill):
    x = cx - text_width(s, fs) / 2.0
    return ('<text x="%.1f" y="%s" font-size="%s" font-weight="700" '
            'letter-spacing="0.4" fill="%s" '
            'font-family="Arial Narrow, Arial, sans-serif">%s</text>'
            % (x, y, fs, fill, s))


def _grad(gid, kind, stops):
    body = ''.join('<stop offset="%s" stop-color="%s"/>' % st for st in stops)
    if kind == 'radial':
        return ('<radialGradient id="%s" cx="50%%" cy="35%%" r="75%%">%s'
                '</radialGradient>' % (gid, body))
    return ('<linearGradient id="%s" x1="0" y1="0" x2="0" y2="1">%s'
            '</linearGradient>' % (gid, body))


BEZEL_GRAD = ('<radialGradient id="bz" cx="30%" cy="20%" r="80%">'
              '<stop offset="0" stop-color="#9a958e"/>'
              '<stop offset="0.55" stop-color="#615c56"/>'
              '<stop offset="1" stop-color="#26231f"/></radialGradient>')
GLOW_FILTERS = ('<filter id="sg" x="-60%" y="-60%" width="220%" height="220%">'
                '<feGaussianBlur stdDeviation="2.2" result="b"/>'
                '<feMerge><feMergeNode in="b"/>'
                '<feMergeNode in="SourceGraphic"/></feMerge></filter>'
                '<filter id="bg" x="-100%" y="-100%" width="300%" height="300%">'
                '<feGaussianBlur stdDeviation="8"/></filter>')


def render_button_svg(lines, style, icon='', fs=15, text_y=None, text_x=None,
                      span=1):
    """Render one button state as a complete SVG document string."""
    st = STYLES[style]
    vbw = VB_W * span
    w = RENDER_W * span
    capx, capw = 14, vbw - 28
    cx = text_x if text_x is not None else vbw / 2.0
    if text_y is None:
        text_y = [63] if len(lines) == 1 else [51, 69]
    texts = ''.join(text_el(t, cx, y, fs, st['text'])
                    for t, y in zip(lines, text_y))
    ic = icon.replace('FILL', st['text']).replace('CX', '%.0f' % (vbw / 2.0))
    kind, stops = st['grad']
    p = []
    p.append('<svg xmlns="http://www.w3.org/2000/svg" width="%d" height="%d" '
             'viewBox="0 0 %d %d">' % (w, RENDER_H, vbw, VB_H))
    p.append('<defs>' + BEZEL_GRAD + _grad('cap', kind, stops)
             + (GLOW_FILTERS if st['glow'] else '') + '</defs>')
    p.append('<rect x="2" y="2" width="%d" height="93" rx="5" fill="url(#bz)" '
             'stroke="#100f0d" stroke-width="1"/>' % (vbw - 4))
    p.append('<rect x="6" y="6" width="%d" height="85" rx="3" fill="none" '
             'stroke="#c9c5be" stroke-width="0.6" opacity="0.35"/>' % (vbw - 12))
    p.append('<rect x="9" y="9" width="%d" height="79" rx="3" fill="#141210" '
             'stroke="#000000" stroke-width="1"/>' % (vbw - 18))
    p.append('<rect x="9" y="9" width="%d" height="8" rx="2" fill="#000000" '
             'opacity="0.45"/>' % (vbw - 18))
    cap_extra = ''
    if st['glow']:
        p.append('<rect x="%d" y="13" width="%d" height="70" rx="6" '
                 'fill="url(#cap)" opacity="0.55" filter="url(#bg)"/>'
                 % (capx - 2, capw + 4))
        cap_extra = ' filter="url(#sg)"'
    p.append('<rect x="%d" y="15" width="%d" height="66" rx="4" '
             'fill="url(#cap)" stroke="%s" stroke-width="1.4"%s/>'
             % (capx, capw, st['stroke'], cap_extra))
    p.append('<rect x="%d" y="18" width="%d" height="14" rx="2" '
             'fill="#ffffff" opacity="0.18"/>' % (capx + 3, capw - 6))
    p.append('<g transform="translate(0,-10)">' + ic + texts + '</g>')
    p.append('</svg>')
    return ''.join(p) + '\n'
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python3 tools/test_vcpgen.py`
Expected: `OK` (5 tests)

- [ ] **Step 5: Commit**

```bash
git add tools/vcpgen.py tools/test_vcpgen.py
git commit -m "feat(vcpgen): retro button SVG renderer (geometry, styles, text metrics)"
```

---

### Task 2: Icon library

**Files:**
- Modify: `tools/vcpgen.py` (append after `render_button_svg`)
- Modify: `tools/test_vcpgen.py` (append test class)

**Interfaces:**
- Produces: `vcpgen.ICONS` dict, keys: `up, down, left, right, cw, ccw, wheel, pump, flood, hare, tortoise`. Values are SVG fragment strings in the content coordinate system (center 58,58; `FILL` placeholder for the state text color, `CX` for horizontal center). `render_button_svg` already substitutes both placeholders.

- [ ] **Step 1: Write the failing test** (append to `tools/test_vcpgen.py` before the `__main__` block)

```python
class TestIcons(unittest.TestCase):
    def test_all_icons_render(self):
        for key in ('up', 'down', 'left', 'right', 'cw', 'ccw', 'wheel',
                    'pump', 'flood', 'hare', 'tortoise'):
            svg = vcpgen.render_button_svg([], 'amber', icon=vcpgen.ICONS[key])
            svg.encode('ascii')
            ET.fromstring(svg)
            self.assertNotIn('FILL', svg)
            self.assertNotIn('CX', svg)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python3 tools/test_vcpgen.py`
Expected: ERROR `AttributeError: module 'vcpgen' has no attribute 'ICONS'`

- [ ] **Step 3: Implement** — append to `tools/vcpgen.py`. The hare/tortoise path data is the stock artwork; re-extract it verbatim so no transcription error creeps in:

Run first (prints the two `d=` strings to splice into `HARE_PATH` / `TORT_PATH`):

```bash
python3 - <<'EOF'
import re
svg = open('resources/vcp/Buttons/tortoise_hare/tortoise_hare.svg').read()
tort, hare = re.findall(r'<path d="([^"]+)"', svg)
print('TORT_PATH =', repr(tort))
print('HARE_PATH =', repr(hare))
EOF
```

Then append (with the printed path strings substituted for the `<PASTE ...>` markers — they are ~540 chars each):

```python
# ------------------------------------------------------------- icons ------
# Content coordinate system: cap center (58,58); FILL -> state text color,
# CX -> horizontal center. Multi-line strings keep each shape readable.
TORT_PATH = '<PASTE tort path printed above>'
HARE_PATH = '<PASTE hare path printed above>'

ICONS = {
    'up':    '<polygon points="CX,36 44,54 72,54" fill="FILL"/>',
    'down':  '<polygon points="CX,80 44,62 72,62" fill="FILL"/>',
    'left':  '<polygon points="38,45 56,34 56,56" fill="FILL"/>',
    'right': '<polygon points="78,45 60,34 60,56" fill="FILL"/>',
    'cw':    ('<g transform="translate(-1.7,20.3) scale(0.65)">'
              '<path d="M 58 40 a 18 18 0 1 1 -15 8" fill="none" stroke="FILL" '
              'stroke-width="5"/>'
              '<polygon points="34,44 46,53 31,59" fill="FILL"/></g>'),
    'ccw':   ('<g transform="translate(-1.7,20.3) scale(0.65)">'
              '<path d="M 58 40 a 18 18 0 1 0 15 8" fill="none" stroke="FILL" '
              'stroke-width="5"/>'
              '<polygon points="82,44 70,53 85,59" fill="FILL"/></g>'),
    'wheel': ('<circle cx="CX" cy="58" r="17" fill="none" stroke="FILL" '
              'stroke-width="3.5"/>'
              '<circle cx="CX" cy="58" r="3" fill="FILL"/>'
              '<circle cx="CX" cy="45" r="4" fill="FILL"/>'),
    'pump':  ('<g transform="translate(3,-12)">'
              '<rect x="42" y="52" width="22" height="18" rx="2" fill="none" '
              'stroke="FILL" stroke-width="3"/>'
              '<circle cx="53" cy="61" r="4.5" fill="FILL"/>'
              '<path d="M64 56 h8 v-8" fill="none" stroke="FILL" '
              'stroke-width="3"/>'
              '<path d="M76 38 c-4 6 -4 9 0 9 c4 0 4 -3 0 -9 z" fill="FILL"/>'
              '</g>'),
    # stock CNC12 flood_coolant line-art (black outline paths), recolored
    'flood': ('<g transform="translate(34,10) scale(0.48)">'
              '<path d="M60.12,38.62H35.79V32.19H60.12ZM37.24,37.17H58.67V33.64'
              'H37.24Z" fill="FILL"/>'
              '<path d="M51.56,42.59h-7.2V37.17h7.2Zm-5.75-1.45h4.3V38.62h-4.3Z" '
              'fill="FILL"/>'
              '<path d="M77.17,67.19H65.32V60H59.58a13,13,0,0,1-23.25,0H19.18'
              'V48.13h3.68c.85,0,1.7,0,2.54,0,3.64,0,7.29,0,10.93,0a13,13,0,0,1,'
              '23.24,0h2.28a30.42,30.42,0,0,1,4.26.17c5.28.73,11,4,11.07,9.42,0,'
              '.8,0,1.61,0,2.41v1.11c0,1.2,0,2.41,0,3.61Zm-10.4-1.45h9v-.92c0-1.2,'
              '0-2.41,0-3.62V60.09c0-.8,0-1.59,0-2.38-.06-4.58-5.13-7.35-9.82-8h0'
              'a28.64,28.64,0,0,0-4-.16h-3.2l-.19-.42a11.59,11.59,0,0,0-21,0l-.2,'
              '.42h-.46c-3.83,0-7.6,0-11.37,0H20.62v9H37.24l.2.42a11.6,11.6,0,0,0,'
              '21,0l.19-.42h8.1Z" fill="FILL"/>'
              '<path d="M85,92H58l9.63-25.11h7.88ZM60.14,90.54H82.93L74.54,68.33'
              'H68.66Z" fill="FILL"/></g>'),
    'hare':  ('<g transform="translate(20.5,39) scale(0.75)">'
              '<path d="' + HARE_PATH + '" fill="FILL"/>'
              '<ellipse cx="86.4" cy="23.98" rx="1.01" ry="0.61" fill="#ffffff" '
              'opacity="0.85"/></g>'),
    'tortoise': ('<g transform="translate(20.5,0.3) scale(0.75)">'
              '<path d="' + TORT_PATH + '" fill="FILL"/>'
              '<circle cx="79.41" cy="71.04" r="1.41" fill="#ffffff" '
              'opacity="0.85"/></g>'),
}
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python3 tools/test_vcpgen.py`
Expected: `OK` (6 tests)

- [ ] **Step 5: Commit**

```bash
git add tools/vcpgen.py tools/test_vcpgen.py
git commit -m "feat(vcpgen): icon library (arrows, cw/ccw, wheel, pump, stock flood + hare/tortoise)"
```

---

### Task 3: ACROLOC nameplate SVG

**Files:**
- Modify: `tools/vcpgen.py` (append)
- Modify: `tools/test_vcpgen.py` (append test class)

**Interfaces:**
- Produces: `vcpgen.render_nameplate_svg() -> str`. Artboard `viewBox 0 0 634 100`, `width=634 height=100` (spans row 1 across 6 columns; the VCP scales an `<image>` to its spanned cells). Glyphs from `vcpgen.NAME_GLYPHS` (keys `A C R O L`), each in a 90x90 box, drawn at 64px pitch cells.

- [ ] **Step 1: Write the failing test** (append)

```python
class TestNameplate(unittest.TestCase):
    def test_nameplate_parses(self):
        svg = vcpgen.render_nameplate_svg()
        svg.encode('ascii')
        root = ET.fromstring(svg)
        self.assertEqual(root.get('viewBox'), '0 0 634 100')
        # ACROLOC = 7 glyph paths + plate rects
        paths = svg.count('fill-rule="evenodd"')
        self.assertEqual(paths, 7)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python3 tools/test_vcpgen.py`
Expected: ERROR `AttributeError: ... 'render_nameplate_svg'`

- [ ] **Step 3: Implement** (append to `tools/vcpgen.py`)

```python
# -------------------------------------------------- ACROLOC nameplate -----
# Glyphs traced from the original machine badge photo, then idealized
# (edges snapped square, uniform stroke, 4-unit chamfers). 90x90 boxes.
NAME_GLYPHS = {
    'A': 'M48,0 H85 L90,6 V90 H58 L45,66 L46,62 H64 L66,60 V25 H63 L38,66 '
         'L27,90 H2 L0,87 L2,82 Z',
    'C': 'M4,0 H86 L90,4 V24 L86,28 H32 V62 H86 L90,66 V86 L86,90 H4 L0,86 '
         'V4 Z',
    'R': 'M4,0 H82 L86,4 V60 L82,64 L77,66 L90,85 V88 L88,90 H62 L38,50 '
         'L36,45 L39,42 H58 V28 H28 V88 L26,90 H4 L0,86 V4 Z',
    'O': 'M4,0 H86 L90,4 V86 L86,90 H4 L0,86 V4 Z M26,26 H64 V64 H26 Z',
    'L': 'M4,0 H24 L28,4 V62 H86 L90,66 V86 L86,90 H4 L0,86 V4 Z',
}


def render_nameplate_svg():
    word, gap, cell = 'ACROLOC', 10, 64
    scale = cell / 90.0
    total = len(word) * cell + (len(word) - 1) * gap
    x = (634 - total) / 2.0
    glyphs = []
    for ch in word:
        glyphs.append('<path d="%s" transform="translate(%.1f,18) '
                      'scale(%.3f)" fill="#4a2028" fill-rule="evenodd" '
                      'stroke="#3a1820" stroke-width="2" '
                      'stroke-linejoin="round"/>'
                      % (NAME_GLYPHS[ch], x, scale))
        x += cell + gap
    streaks = []
    for y in range(8, 96, 7):
        op = 0.04 + 0.05 * ((y * 13) % 10) / 10.0
        streaks.append('<line x1="6" y1="%d" x2="628" y2="%d" '
                       'stroke="#ffffff" stroke-width="0.5" opacity="%.3f"/>'
                       % (y, y + 1, op))
    return (
        '<svg xmlns="http://www.w3.org/2000/svg" width="634" height="100" '
        'viewBox="0 0 634 100">'
        '<defs><linearGradient id="alum" x1="0" y1="0" x2="0" y2="1">'
        '<stop offset="0" stop-color="#d8d5d0"/>'
        '<stop offset="0.3" stop-color="#b8b4ae"/>'
        '<stop offset="0.6" stop-color="#cac6c0"/>'
        '<stop offset="1" stop-color="#8e8a84"/></linearGradient></defs>'
        '<rect x="2" y="2" width="630" height="96" rx="4" fill="url(#alum)" '
        'stroke="#100f0d" stroke-width="1.5"/>'
        '<rect x="6" y="6" width="622" height="88" rx="2" fill="none" '
        'stroke="#ffffff" stroke-width="0.8" opacity="0.4"/>'
        + ''.join(streaks) + ''.join(glyphs) + '</svg>\n')
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python3 tools/test_vcpgen.py`
Expected: `OK` (7 tests)

- [ ] **Step 5: Commit**

```bash
git add tools/vcpgen.py tools/test_vcpgen.py
git commit -m "feat(vcpgen): ACROLOC nameplate SVG from traced badge glyphs"
```

---

### Task 4: Round RESET button SVGs (normal + tripped)

**Files:**
- Modify: `tools/vcpgen.py` (append)
- Modify: `tools/test_vcpgen.py` (append test class)

**Interfaces:**
- Produces: `vcpgen.render_reset_svg(tripped) -> str`. Artboard `viewBox 0 0 348 268`, `width=300 height=252` (3x3 cells at 100x84). Round red mushroom; tripped = depressed dome + glowing RESET/TRIPPED banners (mirrors stock `reset.xml` image_on/image_off pair).

- [ ] **Step 1: Write the failing test** (append)

```python
class TestReset(unittest.TestCase):
    def test_reset_states(self):
        normal = vcpgen.render_reset_svg(False)
        tripped = vcpgen.render_reset_svg(True)
        for svg in (normal, tripped):
            svg.encode('ascii')
            ET.fromstring(svg)
        self.assertIn('RESET', normal)
        self.assertNotIn('TRIPPED', normal)
        self.assertIn('TRIPPED', tripped)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python3 tools/test_vcpgen.py`
Expected: ERROR `AttributeError: ... 'render_reset_svg'`

- [ ] **Step 3: Implement** (append to `tools/vcpgen.py`)

```python
# ------------------------------------------------------- round RESET ------
def render_reset_svg(tripped):
    cx, cy = 174, 138            # button center in the 348x268 artboard
    dome_r = 82 if tripped else 94
    dome_y = cy + 12 if tripped else cy - 8
    dome = ('<radialGradient id="dome" cx="38%" cy="30%" r="75%">'
            '<stop offset="0" stop-color="%s"/>'
            '<stop offset="0.35" stop-color="%s"/>'
            '<stop offset="0.8" stop-color="%s"/>'
            '<stop offset="1" stop-color="%s"/></radialGradient>'
            % (('#ffb0b0', '#ff3838', '#c40f0f', '#7a0505') if tripped
               else ('#f26b6b', '#d42a2a', '#8c0f0f', '#5c0505')))
    p = []
    p.append('<svg xmlns="http://www.w3.org/2000/svg" width="300" '
             'height="252" viewBox="0 0 348 268">')
    p.append('<defs>' + BEZEL_GRAD.replace('id="bz"', 'id="rbz"') + dome +
             '<radialGradient id="skirt" cx="50%" cy="35%" r="70%">'
             '<stop offset="0" stop-color="#a81c1c"/>'
             '<stop offset="0.7" stop-color="#6e0c0c"/>'
             '<stop offset="1" stop-color="#3d0404"/></radialGradient>'
             '<radialGradient id="well" cx="50%" cy="40%" r="70%">'
             '<stop offset="0" stop-color="#1c1916"/>'
             '<stop offset="1" stop-color="#0a0908"/></radialGradient>'
             '<filter id="halo" x="-50%" y="-50%" width="200%" height="200%">'
             '<feGaussianBlur stdDeviation="14"/></filter>'
             '<filter id="txtglow" x="-40%" y="-40%" width="180%" '
             'height="180%"><feGaussianBlur stdDeviation="1.6" result="b"/>'
             '<feMerge><feMergeNode in="b"/>'
             '<feMergeNode in="SourceGraphic"/></feMerge></filter></defs>')
    p.append('<rect x="4" y="4" width="340" height="260" rx="8" '
             'fill="url(#rbz)" stroke="#100f0d" stroke-width="1.5"/>')
    p.append('<rect x="10" y="10" width="328" height="248" rx="5" fill="none" '
             'stroke="#c9c5be" stroke-width="0.8" opacity="0.35"/>')
    p.append('<rect x="15" y="15" width="318" height="238" rx="5" '
             'fill="url(#well)" stroke="#000000" stroke-width="1.5"/>')
    p.append('<rect x="15" y="15" width="318" height="16" rx="4" '
             'fill="#000000" opacity="0.45"/>')
    if tripped:
        p.append('<circle cx="%d" cy="%d" r="112" fill="#ff2020" '
                 'opacity="0.22" filter="url(#halo)"/>' % (cx, cy + 8))
    p.append('<circle cx="%d" cy="%d" r="106" fill="url(#skirt)" '
             'stroke="#2a0505" stroke-width="2"/>' % (cx, cy + 8))
    p.append('<circle cx="%d" cy="%d" r="%d" fill="url(#dome)" '
             'stroke="#4a0808" stroke-width="1.5"/>' % (cx, dome_y, dome_r))
    if tripped:
        p.append('<ellipse cx="%d" cy="%d" rx="%d" ry="16" fill="#000000" '
                 'opacity="0.35"/>' % (cx, dome_y - dome_r + 14, dome_r - 6))
        p.append('<ellipse cx="%d" cy="%d" rx="28" ry="14" fill="#ffffff" '
                 'opacity="0.14"/>' % (cx - 18, dome_y - 30))
        p.append(text_el('RESET', cx, 42, 26, '#ff5555')
                 .replace('<text ', '<text filter="url(#txtglow)" '))
        p.append(text_el('TRIPPED', cx, 246, 26, '#ff5555')
                 .replace('<text ', '<text filter="url(#txtglow)" '))
    else:
        p.append('<ellipse cx="%d" cy="%d" rx="40" ry="24" fill="#ffffff" '
                 'opacity="0.22"/>' % (cx - 24, dome_y - 30))
        p.append(text_el('RESET', cx, dome_y + 10, 32, '#ffd9d9'))
    p.append('</svg>')
    return ''.join(p) + '\n'
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python3 tools/test_vcpgen.py`
Expected: `OK` (8 tests)

- [ ] **Step 5: Commit**

```bash
git add tools/vcpgen.py tools/test_vcpgen.py
git commit -m "feat(vcpgen): round RESET mushroom SVGs (normal + depressed/tripped)"
```

---

### Task 5: BUTTONS table + button folder emission (behavior copied from stock)

**Files:**
- Modify: `tools/vcpgen.py` (append)
- Modify: `tools/test_vcpgen.py` (append test class)

**Interfaces:**
- Consumes: `render_button_svg`, `render_reset_svg`, `ICONS`.
- Produces: `vcpgen.BUTTONS` (list of dicts; every entry has `name,row,col`, optional `lines, lines_on, style, style_on, icon, icon_on, fs, text_y, text_x, row_span, col_span, special`); `vcpgen.emit_buttons(out_dir)` writing `resources/vcp/Buttons/retro_<name>/` under `out_dir`; helper `vcpgen.stock_xml(name) -> str`.
- XML rules: copy stock XML verbatim, then (a) `color_on/color_off` LED pairs become `image_on/image_off` pointing at `retro_<name>_on.svg` / `retro_<name>.svg`; (b) reset's stock `image_on/off` filenames are prefixed `retro_`; (c) `push_free`'s `on_click_swap` points at `retro_push_free_on.svg` (stock behavior kept — narrow, deliberate exception to "no on_click_swap" since the stock button IS a swap). A `_on.svg` is emitted whenever the stock XML contains `color_on`, `image_on`, or `on_click_swap`.

- [ ] **Step 1: Write the failing test** (append)

```python
import tempfile


class TestEmitButtons(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.out = tempfile.mkdtemp(prefix='vcpgen_')
        vcpgen.emit_buttons(cls.out)
        cls.bdir = os.path.join(cls.out, 'resources', 'vcp', 'Buttons')

    def _read(self, *parts):
        with open(os.path.join(self.bdir, *parts)) as f:
            return f.read()

    def test_every_table_entry_has_folder_xml_svg(self):
        for b in vcpgen.BUTTONS:
            rn = 'retro_' + b['name']
            xml = self._read(rn, rn + '.xml')
            ET.fromstring(xml)
            self.assertTrue(os.path.exists(
                os.path.join(self.bdir, rn, rn + '.svg')))

    def test_stateful_led_becomes_image_swap(self):
        xml = self._read('retro_spindle_cw', 'retro_spindle_cw.xml')
        self.assertIn('<number>1063</number>', xml)       # PLC bit preserved
        self.assertIn('<image_on>retro_spindle_cw_on.svg</image_on>', xml)
        self.assertIn('<image_off>retro_spindle_cw.svg</image_off>', xml)
        self.assertNotIn('color_on', xml)
        self.assertTrue(os.path.exists(os.path.join(
            self.bdir, 'retro_spindle_cw', 'retro_spindle_cw_on.svg')))

    def test_momentary_has_single_svg(self):
        xml = self._read('retro_x_positive', 'retro_x_positive.xml')
        self.assertIn('<skin_event_num>39</skin_event_num>', xml)
        self.assertFalse(os.path.exists(os.path.join(
            self.bdir, 'retro_x_positive', 'retro_x_positive_on.svg')))

    def test_reset_uses_retro_filenames(self):
        xml = self._read('retro_reset', 'retro_reset.xml')
        self.assertIn('<image_on>retro_reset_tripped.svg</image_on>', xml)
        self.assertIn('<image_off>retro_reset.svg</image_off>', xml)
        for f in ('retro_reset.svg', 'retro_reset_tripped.svg'):
            self.assertTrue(os.path.exists(
                os.path.join(self.bdir, 'retro_reset', f)))

    def test_legend_swap_pairs(self):
        on = self._read('retro_incr_cont', 'retro_incr_cont_on.svg')
        off = self._read('retro_incr_cont', 'retro_incr_cont.svg')
        self.assertIn('CONT', on)
        self.assertIn('INCR', off)

    def test_all_emitted_files_ascii(self):
        for root, _dirs, files in os.walk(self.bdir):
            for f in files:
                with open(os.path.join(root, f), 'rb') as fh:
                    data = fh.read()
                self.assertTrue(max(data) < 128,
                                'non-ASCII byte in %s' % f)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python3 tools/test_vcpgen.py`
Expected: ERROR `AttributeError: ... 'emit_buttons'`

- [ ] **Step 3: Implement** (append to `tools/vcpgen.py`)

```python
# ------------------------------------------------------- buttons table ----
# text_y values are in content coordinates (mockup center-58 system).
BUTTONS = [
    dict(name='spindle_plus', row=3, col=2, lines=['+'], fs=20, icon='up',
         text_y=[79]),
    dict(name='spindle_100', row=3, col=3, lines=['SPIN', '100%']),
    dict(name='spindle_minus', row=3, col=4, lines=['-'], fs=20, icon='down',
         text_y=[52]),
    dict(name='spindle_auto_man', row=3, col=5, lines=['SPIN', 'AUTO'],
         lines_on=['SPIN', 'MAN']),
    dict(name='spindle_cw', row=4, col=2, lines=['CW'], fs=14, icon='cw',
         text_x=78),
    dict(name='spindle_ccw', row=4, col=3, lines=['CCW'], fs=13, icon='ccw',
         text_x=80),
    dict(name='spindle_start', row=4, col=4, lines=['SPIN', 'START']),
    dict(name='spindle_cancel', row=4, col=5, lines=['SPIN', 'STOP']),
    dict(name='coolant_auto_man', row=5, col=2, lines=['CLNT', 'AUTO'],
         lines_on=['CLNT', 'MAN']),
    dict(name='flood_coolant', row=5, col=3, lines=['FLOOD', 'M8'], fs=13,
         icon='flood', text_y=[66, 82]),
    dict(name='coolant_pump', row=5, col=4, lines=['PUMP'], fs=13,
         icon='pump', text_y=[76]),
    dict(name='incr_cont', row=6, col=2, lines=['INCR'], lines_on=['CONT']),
    dict(name='x1', row=6, col=3, lines=['X1']),
    dict(name='x10', row=6, col=4, lines=['X10']),
    dict(name='x100', row=6, col=5, lines=['X100']),
    dict(name='mpg', row=6, col=6, lines=[], icon='wheel'),
    dict(name='y_positive', row=7, col=4, lines=['+Y'], icon='up',
         text_y=[79]),
    dict(name='z_positive', row=7, col=6, lines=['+Z'], icon='up',
         text_y=[79]),
    dict(name='x_negative', row=8, col=3, lines=['-X'], icon='left',
         text_y=[79]),
    dict(name='tortoise_hare', row=8, col=4, lines=[], icon='hare',
         icon_on='tortoise'),
    dict(name='x_positive', row=8, col=5, lines=['+X'], icon='right',
         text_y=[79]),
    dict(name='y_negative', row=9, col=4, lines=['-Y'], icon='down',
         text_y=[52]),
    dict(name='z_negative', row=9, col=6, lines=['-Z'], icon='down',
         text_y=[52]),
    dict(name='cycle_start', row=10, col=2, lines=['CYCLE', 'START'],
         style='green', style_on='grnlit'),
    dict(name='cycle_cancel', row=10, col=3, lines=['CYCLE', 'CANCEL'],
         fs=13, style='red', style_on='lit'),
    dict(name='single_block', row=10, col=4, lines=['SINGLE', 'BLOCK'],
         fs=13),
    dict(name='tool_check', row=10, col=5, lines=['TOOL', 'CHECK']),
    dict(name='feed_hold', row=10, col=6, lines=['FEED', 'HOLD']),
    dict(name='feedrate_negative', row=12, col=4, lines=['-'], fs=20,
         icon='down', text_y=[52]),
    dict(name='feedrate_100', row=12, col=5, lines=['FEED', '100%']),
    dict(name='feedrate_positive', row=12, col=6, lines=['+'], fs=20,
         icon='up', text_y=[79]),
    dict(name='feedrate_25', row=13, col=4, lines=['25%']),
    dict(name='feedrate_50', row=13, col=5, lines=['50%']),
    dict(name='feedrate_75', row=13, col=6, lines=['75%']),
    dict(name='reset', row=12, col=1, row_span=3, col_span=3,
         special='reset'),
    dict(name='vcp_options', row=14, col=4, lines=['VCP', 'OPTIONS'], fs=13),
    dict(name='push_free', row=14, col=5, lines=['PUSH', 'FREE']),
]


def stock_xml(name):
    p = os.path.join(REPO, 'resources', 'vcp', 'Buttons', name,
                     name + '.xml')
    with open(p) as f:
        return f.read()


def _retro_xml(name, xml):
    rn = 'retro_' + name
    xml = re.sub(r'<color_on>[^<]*</color_on>',
                 '<image_on>%s_on.svg</image_on>' % rn, xml)
    xml = re.sub(r'<color_off>[^<]*</color_off>',
                 '<image_off>%s.svg</image_off>' % rn, xml)
    xml = xml.replace('reset_tripped.svg', 'retro_reset_tripped.svg')
    xml = xml.replace('>reset.svg<', '>retro_reset.svg<')
    xml = xml.replace('push_pin.svg', 'retro_push_free_on.svg')
    if not xml.endswith('\n'):
        xml += '\n'
    return xml


def _write(path, content):
    with open(path, 'w', newline='\n') as f:
        f.write(content)


def emit_buttons(out_dir):
    for b in BUTTONS:
        name = b['name']
        rn = 'retro_' + name
        d = os.path.join(out_dir, 'resources', 'vcp', 'Buttons', rn)
        os.makedirs(d, exist_ok=True)
        xml = stock_xml(name)
        _write(os.path.join(d, rn + '.xml'), _retro_xml(name, xml))
        if b.get('special') == 'reset':
            _write(os.path.join(d, 'retro_reset.svg'),
                   render_reset_svg(False))
            _write(os.path.join(d, 'retro_reset_tripped.svg'),
                   render_reset_svg(True))
            continue
        kw = dict(fs=b.get('fs', 15), text_y=b.get('text_y'),
                  text_x=b.get('text_x'))
        _write(os.path.join(d, rn + '.svg'),
               render_button_svg(b.get('lines', []), b.get('style', 'amber'),
                                 ICONS.get(b.get('icon', ''), ''), **kw))
        if ('color_on' in xml or 'image_on' in xml or 'on_click_swap' in xml):
            _write(os.path.join(d, rn + '_on.svg'),
                   render_button_svg(
                       b.get('lines_on', b.get('lines', [])),
                       b.get('style_on', 'lit'),
                       ICONS.get(b.get('icon_on', b.get('icon', '')), ''),
                       **kw))
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python3 tools/test_vcpgen.py`
Expected: `OK` (14 tests)

- [ ] **Step 5: Commit**

```bash
git add tools/vcpgen.py tools/test_vcpgen.py
git commit -m "feat(vcpgen): BUTTONS table + retro button folder emission (behavior copied from stock)"
```

---

### Task 6: Skin emission + generate() entry point

**Files:**
- Modify: `tools/vcpgen.py` (append)
- Modify: `tools/test_vcpgen.py` (append test class)

**Interfaces:**
- Consumes: `BUTTONS`, `emit_buttons`, `render_nameplate_svg`.
- Produces: `vcpgen.render_skin() -> str` (the `.vcp` XML string) and `vcpgen.generate(out_dir)` which emits everything (buttons, nameplate image, skin) under `out_dir`; `main()` calls `generate(REPO)`.
- Skin contents: dark background `#141210`; stock hover/click outlines; group-box `<border>`s with `<text>` labels (SPINDLE rows 3-4 cols 2-5, COOLANT row 5 cols 2-4, AXIS JOG rows 6-10 cols 2-6, FEEDRATE rows 12-13 cols 4-6); feedrate readout border (row 11 cols 4-6) with the stock `plc_word` number 4 restyled red-on-dark; nameplate `<image>` row 1 cols 1-6; `<button>` lines from `BUTTONS` (reset with `row_span`/`column_span` 3).

- [ ] **Step 1: Write the failing test** (append)

```python
class TestSkin(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.out = tempfile.mkdtemp(prefix='vcpgen_full_')
        vcpgen.generate(cls.out)

    def test_skin_parses_and_references_existing_buttons(self):
        skin_path = os.path.join(self.out, 'resources', 'vcp', 'skins',
                                 'acroloc_retro_vcp_skin.vcp')
        with open(skin_path) as f:
            skin = f.read()
        skin.encode('ascii')
        root = ET.fromstring(skin)
        names = [el.text for el in root.iter('button')]
        self.assertEqual(len(names), len(vcpgen.BUTTONS))
        for n in names:
            self.assertTrue(os.path.exists(os.path.join(
                self.out, 'resources', 'vcp', 'Buttons', n, n + '.xml')),
                'skin references missing button ' + n)

    def test_grid_positions_in_range(self):
        for b in vcpgen.BUTTONS:
            self.assertTrue(1 <= b['row'] <= 14 and 1 <= b['col'] <= 6)
            self.assertTrue(b['row'] + b.get('row_span', 1) - 1 <= 14)
            self.assertTrue(b['col'] + b.get('col_span', 1) - 1 <= 6)

    def test_no_duplicate_cells(self):
        seen = set()
        for b in vcpgen.BUTTONS:
            for r in range(b['row'], b['row'] + b.get('row_span', 1)):
                for c in range(b['col'], b['col'] + b.get('col_span', 1)):
                    self.assertNotIn((r, c), seen,
                                     'cell collision at %s' % ((r, c),))
                    seen.add((r, c))

    def test_nameplate_emitted(self):
        self.assertTrue(os.path.exists(os.path.join(
            self.out, 'resources', 'vcp', 'images',
            'acroloc_nameplate.svg')))

    def test_deterministic(self):
        out2 = tempfile.mkdtemp(prefix='vcpgen_det_')
        vcpgen.generate(out2)
        for root_dir, _dirs, files in os.walk(self.out):
            rel = os.path.relpath(root_dir, self.out)
            for f in files:
                a = os.path.join(root_dir, f)
                b = os.path.join(out2, rel, f)
                with open(a, 'rb') as fa, open(b, 'rb') as fb:
                    self.assertEqual(fa.read(), fb.read(),
                                     'nondeterministic: %s' % f)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python3 tools/test_vcpgen.py`
Expected: ERROR `AttributeError: ... 'generate'`

- [ ] **Step 3: Implement** (append to `tools/vcpgen.py`)

```python
# --------------------------------------------------------------- skin -----
def _border(col, colspan, row, rowspan, label=None, fill='Transparent',
            outline='#6a645c', thickness=1, extra=''):
    lab = ''
    if label:
        lab = ('\n\t\t<text>\n'
               '\t\t\t<content>%s</content>\n'
               '\t\t\t<fontsize>11</fontsize>\n'
               '\t\t\t<color>#b0a898</color>\n'
               '\t\t\t<font>Arial Narrow</font>\n'
               '\t\t\t<fontstyle>bold</fontstyle>\n'
               '\t\t\t<horizontalalignment>center</horizontalalignment>\n'
               '\t\t\t<verticalalignment>top</verticalalignment>\n'
               '\t\t\t<margintop>-8</margintop>\n'
               '\t\t</text>' % label)
    return ('\t<border>\n'
            '\t\t<column_span>%d</column_span>\n'
            '\t\t<column_start>%d</column_start>\n'
            '\t\t<fill>%s</fill>\n'
            '\t\t<row_span>%d</row_span>\n'
            '\t\t<row_start>%d</row_start>\n'
            '\t\t<outline_color>%s</outline_color>\n'
            '\t\t<outline_thickness>%d</outline_thickness>%s%s\n'
            '\t</border>\n'
            % (colspan, col, fill, rowspan, row, outline, thickness,
               lab, extra))


FEEDRATE_WORD = ('\n\t\t<plc_word>\n'
                 '\t\t\t<number>4</number>\n'
                 '\t\t\t<color>#ff3333</color>\n'
                 '\t\t\t<fontsize>26</fontsize>\n'
                 '\t\t\t<font>Consolas</font>\n'
                 '\t\t\t<fontstyle>bold</fontstyle>\n'
                 '\t\t\t<verticalalignment>center</verticalalignment>\n'
                 '\t\t\t<horizontalalignment>center</horizontalalignment>\n'
                 '\t\t\t<percentage>true</percentage>\n'
                 '\t\t</plc_word>')


def render_skin():
    p = ['<vcp_skin>\n']
    p.append('\t<background>#141210</background>\n')
    p.append(_border(2, 4, 3, 2, label='SPINDLE'))
    p.append(_border(2, 3, 5, 1, label='COOLANT'))
    p.append(_border(2, 5, 6, 5, label='AXIS JOG'))
    p.append(_border(4, 3, 12, 2, label='FEEDRATE'))
    p.append(_border(4, 3, 11, 1, fill='#1a0000', outline='#3a3630',
                     thickness=2, extra=FEEDRATE_WORD))
    p.append('\t<image>\n'
             '\t\t<column_span>6</column_span>\n'
             '\t\t<column_start>1</column_start>\n'
             '\t\t<row_span>1</row_span>\n'
             '\t\t<row_start>1</row_start>\n'
             '\t\t<path>resources\\vcp\\images\\acroloc_nameplate.svg</path>\n'
             '\t</image>\n')
    p.append('\t<on_click>\n\t\t<opacity>100</opacity>\n'
             '\t\t<outline_color>#000000</outline_color>\n\t</on_click>\n')
    p.append('\t<on_hover>\n\t\t<opacity>100</opacity>\n'
             '\t\t<outline_color>#ffffff</outline_color>\n\t</on_hover>\n')
    for b in sorted(BUTTONS, key=lambda x: (x['row'], x['col'])):
        span = ''
        if b.get('col_span', 1) > 1 or b.get('row_span', 1) > 1:
            span = (' column_span="%d" row_span="%d"'
                    % (b.get('col_span', 1), b.get('row_span', 1)))
        p.append('\t<button row="%d" column="%d"%s>retro_%s</button>\n'
                 % (b['row'], b['col'], span, b['name']))
    p.append('</vcp_skin>\n')
    return ''.join(p)


def generate(out_dir):
    emit_buttons(out_dir)
    img_dir = os.path.join(out_dir, 'resources', 'vcp', 'images')
    os.makedirs(img_dir, exist_ok=True)
    _write(os.path.join(img_dir, 'acroloc_nameplate.svg'),
           render_nameplate_svg())
    skin_dir = os.path.join(out_dir, 'resources', 'vcp', 'skins')
    os.makedirs(skin_dir, exist_ok=True)
    _write(os.path.join(skin_dir, 'acroloc_retro_vcp_skin.vcp'),
           render_skin())


def main():
    generate(REPO)
    print('retro VCP theme generated under %s' % REPO)


if __name__ == '__main__':
    main()
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python3 tools/test_vcpgen.py`
Expected: `OK` (19 tests)

- [ ] **Step 5: Commit**

```bash
git add tools/vcpgen.py tools/test_vcpgen.py
git commit -m "feat(vcpgen): retro skin emission + generate() entry point"
```

---

### Task 7: Generate into the repo, switch default skin, docs

**Files:**
- Create (generated): `resources/vcp/Buttons/retro_*/`, `resources/vcp/images/acroloc_nameplate.svg`, `resources/vcp/skins/acroloc_retro_vcp_skin.vcp`
- Modify: `resources/vcp/options.xml` (Skin value)
- Modify: `tools/README.md` (add vcpgen section)

- [ ] **Step 1: Run the generator into the repo**

Run: `python3 tools/vcpgen.py`
Expected: `retro VCP theme generated under /home/bwarner/github/Acroloc-Centroid`

- [ ] **Step 2: Sanity-check the output tree**

Run: `ls resources/vcp/Buttons | grep -c '^retro_'`
Expected: `37`

Run: `git status --short | head -5`
Expected: new `retro_*` folders, the nameplate SVG, and the skin file; NO modifications to stock folders or stock skins.

- [ ] **Step 3: Switch the default skin in options.xml**

First inspect the current value:

Run: `grep -B1 -A2 '<Name>Skin</Name>' resources/vcp/options.xml`

Then edit the value element on the line after `<Name>Skin</Name>` from `servo_mill_vcp_skin` to `acroloc_retro_vcp_skin` (exact tag name as found — the stock file wraps the value in its own element; change only the text). Verify:

Run: `grep -A2 '<Name>Skin</Name>' resources/vcp/options.xml | grep acroloc_retro_vcp_skin`
Expected: one matching line.

- [ ] **Step 4: Add vcpgen section to tools/README.md**

Append:

```markdown
## vcpgen.py - retro VCP theme generator

Regenerates the `acroloc_retro_vcp_skin` VCP theme (all `retro_*` button
folders, the ACROLOC nameplate SVG, and the skin file) from the declarative
table in the script. Stdlib-only and deterministic - edit `tools/vcpgen.py`
(styles, `BUTTONS` table, icons), rerun, and commit the diff.

    python3 tools/vcpgen.py        # regenerate into the repo tree
    python3 tools/test_vcpgen.py   # structural checks

Behavior (skin events / PLC bits) is copied from the stock button XMLs at
generation time; never edit `retro_*` files by hand. Design spec:
docs/superpowers/specs/2026-07-13-retro-vcp-theme-design.md. Rollback: set
`Skin` back to `servo_mill_vcp_skin` in `resources/vcp/options.xml`.
```

- [ ] **Step 5: Run the full test suite one more time**

Run: `python3 tools/test_vcpgen.py`
Expected: `OK`

- [ ] **Step 6: Commit**

```bash
git add resources/vcp tools/README.md
git commit -m "feat(vcp): generate retro theme into repo; make acroloc_retro_vcp_skin the default"
```

---

### Task 8: Push branch and open PR

- [ ] **Step 1: Push**

```bash
git push -u origin retro-vcp-theme
```

- [ ] **Step 2: Open the PR**

```bash
gh pr create --base main --title "Retro VCP theme (acroloc_retro skin, set as default)" --body "$(cat <<'EOF'
Vintage-panel VCP theme for the Acroloc: dark panel, brushed bezels, amber
(inactive) / glowing red (active) caps via image_on/image_off swaps, traced
ACROLOC nameplate, simplified layout (aux/mist/4th-axis buttons unplaced).
Generated end-to-end by stdlib-only tools/vcpgen.py; stock skin and buttons
untouched and selectable via options.xml rollback.

Spec: docs/superpowers/specs/2026-07-13-retro-vcp-theme-design.md
Plan: docs/superpowers/plans/2026-07-13-retro-vcp-theme.md

## Testing
- python3 tools/test_vcpgen.py (structure, ASCII, determinism, PLC-bit
  preservation) - all green
- NOT yet validated on the control PC. On-machine checklist before merge:
  skin loads, button sizes/positions, state swaps track machine (spindle,
  coolant, incr/cont polarity, hare/tortoise, reset tripped), text
  centering (renderer ignores text-anchor - may need CHAR_W tuning),
  group labels visible, feedrate readout live.

Rollback: options.xml Skin -> servo_mill_vcp_skin.

🤖 Generated with [Claude Code](https://claude.com/claude-code)
EOF
)"
```

- [ ] **Step 3: Report the PR URL to the user**

---

## Self-review notes

- Spec coverage: skin (T6), retro buttons + state swaps (T5), nameplate (T3), reset (T4), generator+tests (T1-T6), options.xml default + docs (T7), branch/PR (T8). On-machine checklist lives in the PR body and spec.
- Deviation from spec recorded in T5 interfaces: `push_free` keeps its stock `on_click_swap` (pointed at a retro SVG) because the swap IS the stock behavior being copied.
- Type consistency: `BUTTONS` keys used in T5/T6 match (`row/col/row_span/col_span/lines/lines_on/style/style_on/icon/icon_on/fs/text_y/text_x/special`); `generate(out_dir)` consumed by tests in T5 (`emit_buttons`) and T6 (`generate`).
- Expected test counts: T1=5, T2=6, T3=7, T4=8, T5=14, T6=19.
