#!/usr/bin/env python3
"""Generate the Acroloc retro VCP theme (skin + buttons + nameplate).

Stdlib-only and deterministic. Emits ASCII-only files:
  resources/vcp/images/acroloc_nameplate.svg
  resources/vcp/Buttons/retro_<name>/  (XML + state SVGs)
  resources/vcp/skins/acroloc_retro_vcp_skin.vcp

Usage: python3 tools/vcpgen.py            # writes into the repo tree
Design: docs/superpowers/specs/2026-07-13-retro-vcp-theme-design.md
"""
import math
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
# Arial Bold advance widths (fraction of font size, from the standard AFM
# metrics). The CNC12 renderer ignores text-anchor, so every <text> gets an
# explicit left-edge x. Font is plain Arial: the control PC lacks Arial
# Narrow and the silent fallback made all legends render right of center.
CHAR_W = {
    'A': 0.722, 'B': 0.722, 'C': 0.722, 'D': 0.722, 'E': 0.667, 'F': 0.611,
    'G': 0.778, 'H': 0.722, 'I': 0.278, 'J': 0.556, 'K': 0.722, 'L': 0.611,
    'M': 0.833, 'N': 0.722, 'O': 0.778, 'P': 0.667, 'Q': 0.778, 'R': 0.722,
    'S': 0.667, 'T': 0.611, 'U': 0.722, 'V': 0.667, 'W': 0.944, 'X': 0.667,
    'Y': 0.667, 'Z': 0.611,
    'b': 0.611, 'c': 0.556, 'd': 0.611, 'e': 0.556, 'h': 0.611, 'i': 0.278,
    'l': 0.278, 'n': 0.611, 'o': 0.611, 'r': 0.389, 't': 0.333, 'w': 0.778,
    'y': 0.556,
    '+': 0.584, '-': 0.333, '%': 0.889, ' ': 0.278, '/': 0.278, '.': 0.278,
}
CHAR_W_DIGIT = 0.556
CHAR_W_DEFAULT = 0.6
LETTER_SPACING = 0.4


def text_width(s, fs):
    if not s:
        return 0.0
    w = sum(CHAR_W_DIGIT if c.isdigit() else CHAR_W.get(c, CHAR_W_DEFAULT)
            for c in s) * fs
    return w + LETTER_SPACING * (len(s) - 1)


def text_el(s, cx, y, fs, fill):
    x = cx - text_width(s, fs) / 2.0
    return ('<text x="%.1f" y="%s" font-size="%s" font-weight="700" '
            'letter-spacing="0.4" fill="%s" '
            'font-family="Arial, sans-serif">%s</text>'
            % (x, y, fs, fill, s))


# The VCP's SVG converter (Svg2Xaml) only proves out a narrow feature set in
# the stock skins: paths/shapes/polygons/text, gradients with ABSOLUTE
# userSpaceOnUse coordinates, and NO <filter> primitives. Percentage
# gradient coordinates and feGaussianBlur/feMerge crash the panel silently,
# so everything below sticks to the proven subset.
def _grad(gid, kind, stops, geom):
    body = ''.join('<stop offset="%s" stop-color="%s"/>' % st for st in stops)
    if kind == 'radial':
        return ('<radialGradient id="%s" cx="%.1f" cy="%.1f" r="%.1f" '
                'gradientUnits="userSpaceOnUse">%s</radialGradient>'
                % (gid, geom['cx'], geom['cy'], geom['r'], body))
    return ('<linearGradient id="%s" x1="%.1f" y1="%.1f" x2="%.1f" y2="%.1f" '
            'gradientUnits="userSpaceOnUse">%s</linearGradient>'
            % (gid, geom['x1'], geom['y1'], geom['x2'], geom['y2'], body))


BEZEL_STOPS = (('0', '#9a958e'), ('0.55', '#615c56'), ('1', '#26231f'))


def _bezel_grad(gid, vbw, vbh):
    return _grad(gid, 'radial', BEZEL_STOPS,
                 dict(cx=0.3 * vbw, cy=0.2 * vbh, r=0.8 * vbw))


def render_button_svg(lines, style, icon='', fs=15, text_y=None, text_x=None,
                      span=1, rows=1):
    """Render one button state as a complete SVG document string.

    rows > 1 stretches the same 1x1 styling over a vertical span: the row
    pitch is ~116.5 render units (from the stock 3x3 reset artboard), so
    each extra row adds 116.5 render / 135 viewBox units of cap height.
    Content stays centered as a block."""
    st = STYLES[style]
    vbw = VB_W * span
    vbh = VB_H + (rows - 1) * 135
    w = RENDER_W * span
    h = RENDER_H + (rows - 1) * 116
    capx, capw = 14, vbw - 28
    cap_h = 66                       # regular cap; rows>1 pads, not stretches
    y0 = (vbh - VB_H) / 2.0          # center the standard button vertically
    if text_y is None:
        text_y = [63] if len(lines) == 1 else [51, 69]
    if not isinstance(text_x, (list, tuple)):
        text_x = [text_x] * len(lines)
    texts = ''.join(
        text_el(t, x if x is not None else vbw / 2.0, y, fs, st['text'])
        for t, y, x in zip(lines, text_y, text_x))
    ic = icon.replace('FILL', st['text']).replace('CX', '%.0f' % (vbw / 2.0))
    kind, stops = st['grad']
    # cap occupies x[capx..capx+capw] y[y0+15..y0+81]; absolute gradient coords
    if kind == 'radial':
        cap_geom = dict(cx=vbw / 2.0, cy=y0 + 15 + 0.35 * cap_h,
                        r=0.75 * capw)
    else:
        cap_geom = dict(x1=vbw / 2.0, y1=y0 + 15, x2=vbw / 2.0,
                        y2=y0 + 15 + cap_h)
    p = []
    p.append('<svg xmlns="http://www.w3.org/2000/svg" width="%d" height="%d" '
             'viewBox="0 0 %d %d">' % (w, h, vbw, vbh))
    if rows > 1:
        p.append('<rect x="0" y="0" width="%d" height="%d" fill="#141210"/>'
                 % (vbw, vbh))
    p.append('<defs>' + _bezel_grad('bz', vbw, vbh)
             + _grad('cap', kind, stops, cap_geom) + '</defs>')
    p.append('<rect x="2" y="%.1f" width="%d" height="93" rx="5" '
             'fill="url(#bz)" stroke="#100f0d" stroke-width="1"/>'
             % (y0 + 2, vbw - 4))
    p.append('<rect x="6" y="%.1f" width="%d" height="85" rx="3" fill="none" '
             'stroke="#c9c5be" stroke-width="0.6" opacity="0.35"/>'
             % (y0 + 6, vbw - 12))
    p.append('<rect x="9" y="%.1f" width="%d" height="79" rx="3" '
             'fill="#141210" stroke="#000000" stroke-width="1"/>'
             % (y0 + 9, vbw - 18))
    p.append('<rect x="9" y="%.1f" width="%d" height="8" rx="2" '
             'fill="#000000" opacity="0.45"/>' % (y0 + 9, vbw - 18))
    if st['glow']:
        # fake bloom: layered translucent halo rects (no <filter> support)
        p.append('<rect x="%d" y="%.1f" width="%d" height="76" rx="8" '
                 'fill="%s" opacity="0.18"/>'
                 % (capx - 5, y0 + 10, capw + 10, st['stroke']))
        p.append('<rect x="%d" y="%.1f" width="%d" height="72" rx="6" '
                 'fill="%s" opacity="0.30"/>'
                 % (capx - 3, y0 + 12, capw + 6, st['stroke']))
    p.append('<rect x="%d" y="%.1f" width="%d" height="66" rx="4" '
             'fill="url(#cap)" stroke="%s" stroke-width="1.4"/>'
             % (capx, y0 + 15, capw, st['stroke']))
    p.append('<rect x="%d" y="%.1f" width="%d" height="14" rx="2" '
             'fill="#ffffff" opacity="0.18"/>' % (capx + 3, y0 + 18, capw - 6))
    p.append('<g transform="matrix(1 0 0 1 0 %.1f)">' % (y0 - 10)
             + ic + texts + '</g>')
    p.append('</svg>')
    return ''.join(p) + '\n'


# ------------------------------------------------------------- icons ------
# Content coordinate system: cap center (58,58); FILL -> state text color,
# CX -> horizontal center.
# NOTE: in the stock tortoise_hare.svg the FIRST path is the hare and the
# SECOND the tortoise (verified on-machine 2026-07-14; the animals are
# stylized enough that the original top/bottom reading was backwards).
HARE_PATH = 'M54.08,66.76s12.71,3,12.29,4.28S66,73,57.53,71,41,68.24,38.34,69.5c0,0-1.24-4.53-3.73-5.22s-4.83,0-5.52,1.38.28,4.83,2.35,5.93a57.86,57.86,0,0,0-4.84,5.8c-1.79,2.63-6.21,7-14.63,8.15s-7.46,7.73-.69,5.25,17.53-6.49,27.34-6.08,21.26,4.56,30.93.14c4.83,3.73,9.41,6.61,11.89,7s13.65,0,13.65,0,.82-2.12-3.73-2.6c-1.13-.12-9-1.25-9-1.25S74.52,83.88,74,82.36s.41-3.72.41-3.72,9.52,1.1,11.6,1a4.07,4.07,0,0,0,3.2-1.84l.1-.15c.67-1-2.92-8.11-6.48-9.37-3.35-1.19-4.8-2-6.76-1.38-1,.3-2.63,1.24-3.73,1.24S66.1,63.72,61.4,63.45,44.14,66.21,54.08,66.76Z'
TORT_PATH = 'M90.89,29.61a3.73,3.73,0,0,0,1.88-2.31,3.38,3.38,0,0,0,1-1.72c-.11-1.56-1.81-2.81-3.61-3.11a6.75,6.75,0,0,0-4.33-.42A33.18,33.18,0,0,0,79,24.27c-.49.06-2.62,1.55-2.76.92S69.66,15.58,60.34,10.3s-21.26,0-21.26,0c-8.89,3.47-15.15,16.84-16.17,18.33s-5.79-3.44-5.79-3.44c.62,5.81,8.7,8.06,8.7,8.06l-.43,6.94h7.28a20.09,20.09,0,0,1,.43-4C33.54,34.41,36,34.9,36,34.9l.43,5.29h6.41l2-6.28c2,1.16,11.15-.66,11.15-.66l-.44,6.94h6.41s3.93-6.94,4.51-6.77S66,40.19,66,40.19h6.11s1.75-5.12,2-6.75,7-1.45,7.64-1.71a7,7,0,0,1,3.72-1.09,16,16,0,0,0,5.38-1'

ICONS = {
    'up':    '<polygon points="CX,36 44,54 72,54" fill="FILL"/>',
    'down':  '<polygon points="CX,80 44,62 72,62" fill="FILL"/>',
    'left':  '<polygon points="38,45 56,34 56,56" fill="FILL"/>',
    'right': '<polygon points="78,45 60,34 60,56" fill="FILL"/>',
    'cw':    ('<g transform="matrix(0.65 0 0 0.65 -1.7 20.3)">'
              '<path d="M 58 40 a 18 18 0 1 1 -15 8" fill="none" stroke="FILL" '
              'stroke-width="5"/>'
              '<polygon points="34,44 46,53 31,59" fill="FILL"/></g>'),
    'ccw':   ('<g transform="matrix(0.65 0 0 0.65 -1.7 20.3)">'
              '<path d="M 58 40 a 18 18 0 1 0 15 8" fill="none" stroke="FILL" '
              'stroke-width="5"/>'
              '<polygon points="82,44 70,53 85,59" fill="FILL"/></g>'),
    'wheel': ('<circle cx="CX" cy="58" r="17" fill="none" stroke="FILL" '
              'stroke-width="3.5"/>'
              '<circle cx="CX" cy="58" r="3" fill="FILL"/>'
              '<circle cx="CX" cy="45" r="4" fill="FILL"/>'),
    'pump':  ('<g transform="matrix(1 0 0 1 -2 11)">'
              '<rect x="42" y="52" width="22" height="18" rx="2" fill="none" '
              'stroke="FILL" stroke-width="1.5"/>'
              '<circle cx="53" cy="61" r="4" fill="FILL"/>'
              '<path d="M64 56 h8 v-8" fill="none" stroke="FILL" '
              'stroke-width="1.5"/>'
              '<path d="M74 54 c-4 6 -4 9 0 9 c4 0 4 -3 0 -9 z" fill="FILL"/>'
              '</g>'),
    # stock CNC12 flood_coolant line-art (black outline paths), recolored
    'flood': ('<g transform="matrix(0.4 0 0 0.4 52.4 45.2)">' + '<path d="M60.12,38.62H35.79V32.19H60.12ZM37.24,37.17H58.67V33.64H37.24Z" fill="FILL"/><path d="M51.56,42.59h-7.2V37.17h7.2Zm-5.75-1.45h4.3V38.62h-4.3Z" fill="FILL"/><path d="M77.17,67.19H65.32V60H59.58a13,13,0,0,1-23.25,0H19.18V48.13h3.68c.85,0,1.7,0,2.54,0,3.64,0,7.29,0,10.93,0a13,13,0,0,1,23.24,0h2.28a30.42,30.42,0,0,1,4.26.17c5.28.73,11,4,11.07,9.42,0,.8,0,1.61,0,2.41v1.11c0,1.2,0,2.41,0,3.61Zm-10.4-1.45h9v-.92c0-1.2,0-2.41,0-3.62V60.09c0-.8,0-1.59,0-2.38-.06-4.58-5.13-7.35-9.82-8h0a28.64,28.64,0,0,0-4-.16h-3.2l-.19-.42a11.59,11.59,0,0,0-21,0l-.2.42h-.46c-3.83,0-7.6,0-11.37,0H20.62v9H37.24l.2.42a11.6,11.6,0,0,0,21,0l.19-.42h8.1Z" fill="FILL"/><path d="M85,92H58l9.63-25.11h7.88ZM60.14,90.54H82.93L74.54,68.33H68.66Z" fill="FILL"/>' + '</g>'),
    'hare':  ('<g transform="matrix(0.75 0 0 0.75 20.5 0.3)">'
              '<path d="' + HARE_PATH + '" fill="FILL"/>'
              '<circle cx="79.41" cy="71.04" r="1.41" fill="#ffffff" '
              'opacity="0.85"/></g>'),
    'tortoise': ('<g transform="matrix(0.75 0 0 0.75 20.5 39)">'
              '<path d="' + TORT_PATH + '" fill="FILL"/>'
              '<ellipse cx="86.4" cy="23.98" rx="1.01" ry="0.61" fill="#ffffff" '
              'opacity="0.85"/></g>'),
}


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


def _xform_path(d, s, tx, ty):
    """Bake scale+translate into absolute M/L/H/V path data (no transform
    attribute -- Svg2Xaml stacks transformed glyphs at the origin)."""
    def repl(m):
        cmd, rest = m.group(1), m.group(2)
        if cmd == 'H':
            return 'H%.1f' % (float(rest) * s + tx)
        if cmd == 'V':
            return 'V%.1f' % (float(rest) * s + ty)
        x, y = rest.split(',')
        return '%s%.1f,%.1f' % (cmd, float(x) * s + tx, float(y) * s + ty)
    return re.sub(r'([MLHV])(-?[\d.]+(?:,-?[\d.]+)?)', repl, d)


# Centroid logo (www.centroidcnc.com), styles inlined; viewBox 0 0 560 100
CENTROID_LOGO = (
    '<g> <path fill="#243D7F" stroke="#FFFFFF" stroke-width="2" d="M557.3,85.5c0,6.'
    '2-5.8,11.3-12.8,11.3H129.5c-7.1,0-12.8-5-12.8-11.3V14.6c0-6.2,5.8-11.3,12.8-11'
    '.3h414.9 c7.1,0,12.8,5,12.8,11.3V85.5z"/> <g> <g> <path fill="#FFFFFF" d="M152'
    '.3,50.2c0-3.8,0.4-7.5,1.2-11.2c0.8-3.7,2.2-7.1,4-10.2c1.9-3.1,4.4-5.6,7.6-7.5c'
    '3.2-1.9,7-2.8,11.5-2.8 c0.9,0,1.6,0,2.1,0.1c2.6,0.2,5.1,0.8,7.5,2.1s4.6,2.8,6.'
    '5,4.8c1.9,2,3.4,4.4,4.5,7.1c1.1,2.7,1.7,5.6,1.7,8.7h-10.7 c-0.4-3.4-1.6-6.3-3.'
    '5-8.6c-1.9-2.3-4.6-3.5-8.1-3.5c-2.9,0.1-5.4,1.1-7.5,3.1c-2.1,2-3.6,4.6-4.6,7.9'
    'c-1,3.3-1.5,6.7-1.5,10.4 c0.1,3.7,0.6,7.1,1.7,10.3c1.1,3.2,2.6,5.8,4.6,7.8c2,2'
    ',4.4,3,7.1,3c2.1,0,4.1-0.5,5.8-1.5c1.7-1,3.1-2.3,4.1-4 c1.1-1.7,1.7-3.6,2.1-5.'
    '7h11.2c-0.2,2.5-0.7,5-1.7,7.5c-1,2.5-2.4,4.9-4.3,7.1c-1.9,2.2-4.3,4-7.3,5.3c-3'
    ',1.3-6.4,2-10.3,2 c-4.4,0-8.1-1-11.2-2.9c-3.1-2-5.5-4.5-7.3-7.7c-1.8-3.2-3.1-6'
    '.7-3.9-10.3C152.7,57.5,152.3,53.9,152.3,50.2z"/> <path fill="#FFFFFF" d="M207.'
    '1,80.8V19.2h38.7v11.1h-27V43h24.9v11.4h-24.9v15.1h28.4v11.4H207.1z"/> <path fi'
    'll="#FFFFFF" d="M253.4,80.8V19.2h11.2L286,60.9V19.2h11v61.6h-11l-21.4-42.4v42.'
    '4H253.4z"/> <path fill="#FFFFFF" d="M317.9,80.8V30.3H302V19.2h42.2v11.1h-15.3v'
    '50.5H317.9z"/> <path fill="#FFFFFF" d="M350.4,80.8V19.2h29.9c2,0,3.9,0.4,5.6,1'
    '.3c1.7,0.9,3.2,2,4.4,3.5c1.2,1.5,2.2,3.2,2.8,5.1s1,4,1,6.1 c0,3-0.7,5.9-2.1,8.'
    '6c-1.4,2.8-3.5,5.1-6.3,7c0.8,0.2,1.6,0.7,2.4,1.4c0.8,0.7,1.6,1.6,2.2,2.8c0.6,1'
    '.1,0.9,2.4,0.9,3.8l0.6,13.8 c0,1.3,0.2,2.4,0.7,3.4c0.5,0.9,0.9,1.4,1.4,1.4v3.3'
    'h-11.7c-1.3-3.6-2-7.8-2.2-12.8c0.1-1.2,0.2-2.9,0.2-5.1c0-1.8-0.2-3.1-0.5-4 c-0'
    '.3-0.9-1-1.5-2.1-2c-1.1-0.4-2.8-0.6-5.1-0.6h-11v24.5H350.4z M361.6,44.9h14.2c2'
    '.2,0,4-0.8,5.3-2.4c1.3-1.6,1.9-3.4,1.9-5.5 c0-2-0.6-3.7-1.9-5.1c-1.3-1.4-3.1-2'
    '.2-5.4-2.2h-14.1V44.9z"/> <path fill="#FFFFFF" d="M399.6,49.6c0.3-4.8,1.2-9.7,'
    '2.9-14.4c1.6-4.8,4.4-8.8,8.3-12.2c3.9-3.4,9-5.1,15.3-5.1 c4.3,0,8.4,1.2,12.2,3'
    '.6c3.8,2.4,6.9,6,9.4,11c2.4,5,3.8,11.1,4,18.5c0,4.4-0.5,8.4-1.4,12.2c-1,3.8-2.'
    '5,7.1-4.5,10.1 c-2.1,3-4.7,5.3-8,7c-3.3,1.7-7.1,2.5-11.6,2.5c-3.4,0-6.7-0.6-9.'
    '8-1.9c-3.2-1.3-6-3.2-8.5-5.9c-2.5-2.7-4.5-6.2-5.9-10.4 C400.3,60.2,399.6,55.3,'
    '399.6,49.6z M424.6,29.7c-2.7,0.1-5.2,1.2-7.2,3.2c-2.1,2.1-3.7,4.7-4.8,8c-1.1,3'
    '.3-1.7,6.8-1.8,10.4 c0.1,3.5,0.7,6.9,1.8,9.9c1.1,3.1,2.8,5.5,5.1,7.4c2.3,1.9,5'
    '.1,2.8,8.4,2.8c2.4,0,4.6-0.5,6.4-1.6c1.8-1.1,3.3-2.5,4.5-4.3 c1.2-1.8,2.1-3.9,'
    '2.6-6.3c0.6-2.4,0.9-4.8,0.9-7.4c0-2.9-0.3-5.6-1-8.2c-0.7-2.6-1.7-5-3-7.1c-1.3-'
    '2.1-3-3.8-5.1-5 C429.4,30.3,427.1,29.7,424.6,29.7z"/> <path fill="#FFFFFF" d="'
    'M457.9,80.8V19.2H469v61.6H457.9z"/> <path fill="#FFFFFF" d="M479.5,80.8V19.2h2'
    '2.3c3.5,0,6.7,0.8,9.4,2.5c2.8,1.7,5,4,6.9,6.9c1.8,2.9,3.2,6.2,4.1,9.9 c0.9,3.7'
    ',1.4,7.5,1.4,11.5c0,3.9-0.5,7.7-1.4,11.4c-0.9,3.7-2.3,7-4.1,9.9c-1.8,2.9-4.1,5'
    '.2-6.9,6.9c-2.8,1.7-5.9,2.5-9.4,2.5 H479.5z M490.5,69.4h9.8c2.5,0,4.6-0.9,6.3-'
    '2.8c1.8-1.9,3.1-4.3,4-7.3c0.9-3,1.3-6.2,1.3-9.6c0-3.5-0.4-6.8-1.3-9.9 c-0.9-3-'
    '2.2-5.5-4-7.4c-1.8-1.9-3.9-2.8-6.3-2.8h-9.8V69.4z"/> </g> </g> <g> <path fill='
    '"#FFFFFF" d="M529.9,19.5h-2.2V18h6.2v1.5h-2.2v6.3h-1.8V19.5z"/> <path fill="#F'
    'FFFFF" d="M541.8,22.8c0-0.9-0.1-2.1-0.1-3.2h0c-0.3,1-0.6,2.1-0.9,3l-1,3h-1.4l-'
    '0.9-3c-0.3-0.9-0.5-2-0.7-3.1h0 c0,1.1-0.1,2.3-0.1,3.2l-0.2,3h-1.7l0.5-7.8h2.5l'
    '0.8,2.6c0.3,0.9,0.5,1.9,0.7,2.8h0c0.2-0.9,0.5-1.9,0.8-2.8l0.9-2.6h2.4l0.4,7.8 '
    'h-1.8L541.8,22.8z"/> </g> <rect x="9.3" y="8.3" fill="#FFFFFF" stroke="#231F20'
    '" width="83.8" height="83.4"/> <path fill="#243D7F" d="M76.6,41.5L76.6,41.5l-0'
    '.1-16.5l-2.3,2.3c-5.9-5.6-14-9-23-9c-18.2,0-33,14.2-33,31.8 c0,17.5,14.8,31.8,'
    '33,31.8c9.4,0,17.9-3.8,23.9-9.9l-12.1-11c-3,3-7.1,4.8-11.8,4.8c-9,0-16.3-7-16.'
    '3-15.7 c0-8.7,7.3-15.7,16.3-15.7c4.4,0,8.4,1.7,11.3,4.4l-3.1,3L76.6,41.5z"/> <'
    'path fill="#243D7F" stroke="#FFFFFF" stroke-width="2" d="M89.1,3.3c5.9,0,10.6,'
    '4.6,10.6,10.3v72.9c0,5.7-4.7,10.3-10.6,10.3H13.3c-5.9,0-10.6-4.6-10.6-10.3V13.'
    '5 c0-5.7,4.7-10.3,10.6-10.3H89.1z M51.2,11.5c-22,0-39.7,17.2-39.7,38.5c0,21.2,'
    '17.8,38.5,39.7,38.5S90.9,71.2,90.9,50 C90.9,28.8,73.1,11.5,51.2,11.5z"/> </g>')


def render_nameplate_svg():
    # layout: ACROLOC centered on top; "with <Centroid logo>" below,
    # right-aligned to ACROLOC's right edge
    word, gap, cell = 'ACROLOC', 9, 56
    scale = cell / 90.0
    total = len(word) * cell + (len(word) - 1) * gap      # 446
    x0 = (634 - total) / 2.0
    x = x0
    glyphs = []
    for ch in word:
        # bright red-maroon lettering straight on the panel (no plate)
        glyphs.append('<path d="%s" fill="#c22540" fill-rule="evenodd" '
                      'stroke="#8a1428" stroke-width="2" '
                      'stroke-linejoin="round"/>'
                      % _xform_path(NAME_GLYPHS[ch], scale, x, 8))
        x += cell + gap
    acroloc_right = x0 + total
    logo_scale = 0.24                           # 560x100 -> 134.4x24
    logo_x = acroloc_right - 560 * logo_scale   # right edges align
    logo_y = 70.0                               # small gap under ACROLOC
    with_cx = logo_x - 8 - text_width('controlled by', 14) / 2.0
    return (
        '<svg xmlns="http://www.w3.org/2000/svg" width="634" height="100" '
        'viewBox="0 0 634 100">'
        + ''.join(glyphs)
        + text_el('controlled by', with_cx, 87, 14, '#b0a898')
        + '<g transform="matrix(%g 0 0 %g %g %g)">%s</g>'
          % (logo_scale, logo_scale, logo_x, logo_y, CENTROID_LOGO)
        + '</svg>\n')


# ------------------------------------------------------- round RESET ------
def render_reset_svg(tripped):
    # Stock reset.svg artboard is 378x349.9 for this same 3x3 span and the
    # VCP renders an image at its declared size - matching it exactly is
    # what makes the graphic fill the spanned area (a smaller artboard
    # leaves a gap; seen as a band above the tripped reset on-machine).
    W, H = 378, 350
    cx, cy = W / 2.0, 190
    dome_r = 92 if tripped else 105
    dome_y = cy - 8 if tripped else cy - 11
    stops = (('#ffb0b0', '#ff3838', '#c40f0f', '#7a0505') if tripped
             else ('#f26b6b', '#d42a2a', '#8c0f0f', '#5c0505'))
    dome = _grad('dome', 'radial',
                 (('0', stops[0]), ('0.35', stops[1]), ('0.8', stops[2]),
                  ('1', stops[3])),
                 dict(cx=cx - 0.24 * dome_r, cy=dome_y - 0.4 * dome_r,
                      r=1.5 * dome_r))
    p = []
    p.append('<svg xmlns="http://www.w3.org/2000/svg" width="%d" '
             'height="%d" viewBox="0 0 %d %d">' % (W, H, W, H))
    p.append('<rect x="0" y="0" width="%d" height="%d" fill="#141210"/>'
             % (W, H))
    p.append('<defs>' + _bezel_grad('rbz', W, H) + dome +
             _grad('skirt', 'radial',
                   (('0', '#a81c1c'), ('0.7', '#6e0c0c'), ('1', '#3d0404')),
                   dict(cx=cx, cy=cy - 26, r=168)) +
             _grad('well', 'radial',
                   (('0', '#1c1916'), ('1', '#0a0908')),
                   dict(cx=cx, cy=cy - 30, r=280)) + '</defs>')
    p.append('<rect x="4" y="4" width="%d" height="%d" rx="10" '
             'fill="url(#rbz)" stroke="#100f0d" stroke-width="2"/>'
             % (W - 8, H - 8))
    p.append('<rect x="12" y="12" width="%d" height="%d" rx="6" fill="none" '
             'stroke="#c9c5be" stroke-width="1" opacity="0.35"/>'
             % (W - 24, H - 24))
    p.append('<rect x="19" y="19" width="%d" height="%d" rx="6" '
             'fill="url(#well)" stroke="#000000" stroke-width="2"/>'
             % (W - 38, H - 38))
    if tripped:
        # fake halo: layered translucent circles (no <filter> support)
        p.append('<circle cx="%.0f" cy="%.0f" r="140" fill="#ff2020" '
                 'opacity="0.10"/>' % (cx, cy))
        p.append('<circle cx="%.0f" cy="%.0f" r="128" fill="#ff2020" '
                 'opacity="0.16"/>' % (cx, cy))
    p.append('<circle cx="%.0f" cy="%.0f" r="120" fill="url(#skirt)" '
             'stroke="#2a0505" stroke-width="3"/>' % (cx, cy))
    p.append('<circle cx="%.0f" cy="%.0f" r="%d" fill="url(#dome)" '
             'stroke="#4a0808" stroke-width="2"/>' % (cx, dome_y, dome_r))
    if tripped:
        # depression reads from the smaller, lower, darker dome + banners
        p.append('<ellipse cx="%.0f" cy="%.0f" rx="32" ry="16" '
                 'fill="#ffffff" opacity="0.14"/>'
                 % (cx - 21, dome_y - 36))
        p.append(text_el('RESET', cx, 52, 32, '#ff5555'))
        p.append(text_el('TRIPPED', cx, 324, 32, '#ff5555'))
    else:
        p.append('<ellipse cx="%.0f" cy="%.0f" rx="46" ry="28" '
                 'fill="#ffffff" opacity="0.22"/>'
                 % (cx - 28, dome_y - 36))
        p.append(text_el('RESET', cx, dome_y + 12, 38, '#ffd9d9'))
    p.append('</svg>')
    return ''.join(p) + '\n'


# ------------------------------------------------- spindle mode knob ------
def render_knob_svg(on, title, labels):
    """2x2 paddle selector (e.g. spindle MAN/AUTO, jog INCR/CONT).
    Clickable: the button keeps its stock skin event; the paddle position
    tracks the PLC bit - labels = (off_label, on_label), left/right.
    Artboard is 2/3 of the stock 3x3 reset so it fills a 2x2 span."""
    W, H = 252, 233
    kcx, kcy, base_r = 126.0, 148.0, 58.0
    ang = math.radians(40.0 if on else -40.0)
    c, s = math.cos(ang), math.sin(ang)
    tx = kcx - c * kcx + s * kcy
    ty = kcy - s * kcx - c * kcy
    ticks = []
    for a, label in ((-40.0, labels[0]), (40.0, labels[1])):
        r = math.radians(a)
        x1 = kcx + math.sin(r) * (base_r + 6)
        y1 = kcy - math.cos(r) * (base_r + 6)
        x2 = kcx + math.sin(r) * (base_r + 16)
        y2 = kcy - math.cos(r) * (base_r + 16)
        lx = kcx + math.sin(r) * (base_r + 30)
        ly = kcy - math.cos(r) * (base_r + 26)
        active = (a > 0) == on
        col = '#e3ac5c' if active else '#6a645c'
        ticks.append('<line x1="%.1f" y1="%.1f" x2="%.1f" y2="%.1f" '
                     'stroke="%s" stroke-width="3"/>' % (x1, y1, x2, y2, col))
        ticks.append(text_el(label, lx, ly, 14, col))
    return (
        '<svg xmlns="http://www.w3.org/2000/svg" width="%d" height="%d" '
        'viewBox="0 0 %d %d">' % (W, H, W, H)
        + '<rect x="0" y="0" width="%d" height="%d" fill="#141210"/>' % (W, H)
        + '<defs>' + _bezel_grad('bz', W, H)
        + _grad('base', 'radial',
                (('0', '#3a3733'), ('0.55', '#211f1c'), ('1', '#0f0e0d')),
                dict(cx=kcx - 16, cy=kcy - 20, r=base_r * 1.6)) + '</defs>'
        + '<rect x="13" y="16" width="%d" height="%d" rx="8" '
          'fill="url(#bz)" stroke="#100f0d" stroke-width="1.5"/>'
          % (W - 26, H - 32)
        + '<rect x="19" y="22" width="%d" height="%d" rx="5" fill="none" '
          'stroke="#c9c5be" stroke-width="0.8" opacity="0.35"/>'
          % (W - 38, H - 44)
        + '<rect x="24" y="27" width="%d" height="%d" rx="5" fill="#141210" '
          'stroke="#000000" stroke-width="1.5"/>' % (W - 48, H - 54)
        + text_el(title, kcx, 52, 16, '#b0a898')
        + ''.join(ticks)
        + '<circle cx="%.1f" cy="%.1f" r="%.1f" fill="#000000" '
          'opacity="0.4"/>' % (kcx, kcy + 2, base_r + 4)
        + '<circle cx="%.1f" cy="%.1f" r="%.1f" fill="url(#base)" '
          'stroke="#000000" stroke-width="2"/>' % (kcx, kcy, base_r)
        + '<circle cx="%.1f" cy="%.1f" r="%.1f" fill="none" '
          'stroke="#5a554e" stroke-width="1" opacity="0.5"/>'
          % (kcx, kcy, base_r - 4)
        + '<g transform="matrix(%.4f %.4f %.4f %.4f %.2f %.2f)">'
          % (c, s, -s, c, tx, ty)
        # bakelite pointer ridge: pointed at the indicating end, rounded tail
        + '<path d="M%.1f,%.1f C %.1f,%.1f %.1f,%.1f %.1f,%.1f '
          'C %.1f,%.1f %.1f,%.1f %.1f,%.1f '
          'C %.1f,%.1f %.1f,%.1f %.1f,%.1f '
          'C %.1f,%.1f %.1f,%.1f %.1f,%.1f Z" '
          'fill="#2a2724" stroke="#0c0b0a" stroke-width="1.5"/>'
          % (kcx, kcy - base_r - 12,
             kcx + 10, kcy - base_r + 10, kcx + 16, kcy - 20, kcx + 16, kcy,
             kcx + 16, kcy + 26, kcx + 10, kcy + 42, kcx, kcy + 50,
             kcx - 10, kcy + 42, kcx - 16, kcy + 26, kcx - 16, kcy,
             kcx - 16, kcy - 20, kcx - 10, kcy - base_r + 10,
             kcx, kcy - base_r - 12)
        + '<path d="M%.1f,%.1f C %.1f,%.1f %.1f,%.1f %.1f,%.1f" fill="none" '
          'stroke="#55504a" stroke-width="1.5" opacity="0.7"/>'
          % (kcx - 2, kcy - base_r - 6,
             kcx - 9, kcy - base_r + 14, kcx - 11, kcy - 16, kcx - 11, kcy + 20)
        + '</g></svg>\n')


# ------------------------------------------------------- buttons table ----
# text_y values are in content coordinates (mockup center-58 system).
BUTTONS = [
    dict(name='spindle_plus', row=3, col=4, lines=['+'], fs=20, icon='up',
         text_y=[79]),
    dict(name='spindle_100', row=3, col=5, lines=['SPIN', '100%']),
    dict(name='spindle_minus', row=3, col=6, lines=['-'], fs=20, icon='down',
         text_y=[52]),
    dict(name='spindle_auto_man', row=3, col=1, row_span=2, col_span=2,
         special='knob', knob_title='SPIN MODE',
         knob_labels=('MAN', 'AUTO')),
    dict(name='spindle_cw', row=4, col=3, lines=['CW'], fs=14, icon='cw',
         text_x=78),
    dict(name='spindle_ccw', row=4, col=4, lines=['CCW'], fs=13, icon='ccw',
         text_x=80),
    dict(name='spindle_start', row=4, col=5, lines=['SPIN', 'START']),
    dict(name='spindle_cancel', row=4, col=6, lines=['SPIN', 'STOP']),
    dict(name='coolant_auto_man', row=5, col=1, row_span=2, col_span=2,
         special='knob', knob_title='CLNT MODE',
         knob_labels=('MAN', 'AUTO')),
    dict(name='flood_coolant', row=5, col=3, row_span=2, rows=2,
         lines=['FLOOD', 'M8'], fs=13, icon='flood',
         text_y=[48, 74], text_x=[None, 42]),
    dict(name='coolant_pump', row=5, col=4, row_span=2, rows=2,
         lines=['PUMP'], fs=13, icon='pump', text_y=[48]),
    dict(name='incr_cont', row=7, col=1, row_span=2, col_span=2,
         special='knob', knob_title='JOG MODE',
         knob_labels=('CONT', 'INCR')),
    dict(name='x1', row=10, col=1, lines=['X1']),
    dict(name='x10', row=10, col=2, lines=['X10']),
    dict(name='x100', row=10, col=3, lines=['X100']),
    dict(name='mpg', row=9, col=1, lines=[], icon='wheel'),
    dict(name='y_positive', row=7, col=4, lines=['+Y'], icon='up',
         text_y=[79]),
    dict(name='z_positive', row=7, col=6, lines=['+Z'], icon='up',
         text_y=[79]),
    dict(name='x_negative', row=8, col=3, lines=['-X'], icon='left',
         text_y=[79]),
    dict(name='tortoise_hare', row=8, col=4, lines=[], icon='hare',
         icon_on='tortoise', style='lit', style_on='amber'),
    dict(name='x_positive', row=8, col=5, lines=['+X'], icon='right',
         text_y=[79]),
    dict(name='y_negative', row=9, col=4, lines=['-Y'], icon='down',
         text_y=[52]),
    dict(name='z_negative', row=9, col=6, lines=['-Z'], icon='down',
         text_y=[52]),
    dict(name='cycle_start', row=11, col=1, lines=['CYCLE', 'START'],
         style='green', style_on='grnlit'),
    dict(name='cycle_cancel', row=11, col=2, lines=['CYCLE', 'CANCEL'],
         fs=13, style='red', style_on='lit'),
    dict(name='single_block', row=9, col=2, lines=['SINGLE', 'BLOCK'],
         fs=13),
    dict(name='tool_check', row=10, col=4, lines=['TOOL', 'CHECK']),
    dict(name='feed_hold', row=10, col=5, lines=['FEED', 'HOLD']),
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
    # CRLF: CNC12 runs on a Windows host
    with open(path, 'w', newline='\r\n') as f:
        f.write(content)


def emit_buttons(out_dir):
    for b in BUTTONS:
        name = b['name']
        rn = 'retro_' + name
        d = os.path.join(out_dir, 'resources', 'vcp', 'Buttons', rn)
        os.makedirs(d, exist_ok=True)
        if b.get('special') == 'knob':
            _write(os.path.join(d, rn + '.xml'),
                   _retro_xml(name, stock_xml(name)))
            title = b['knob_title']
            labels = b['knob_labels']
            _write(os.path.join(d, rn + '.svg'),
                   render_knob_svg(False, title, labels))
            _write(os.path.join(d, rn + '_on.svg'),
                   render_knob_svg(True, title, labels))
            continue
        xml = stock_xml(name)
        _write(os.path.join(d, rn + '.xml'), _retro_xml(name, xml))
        if b.get('special') == 'reset':
            _write(os.path.join(d, 'retro_reset.svg'),
                   render_reset_svg(False))
            _write(os.path.join(d, 'retro_reset_tripped.svg'),
                   render_reset_svg(True))
            continue
        kw = dict(fs=b.get('fs', 15), text_y=b.get('text_y'),
                  text_x=b.get('text_x'), rows=b.get('rows', 1))
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


# Live override digits in a seven-segment face (DSEG7 Classic must be
# installed on the control PC; Windows falls back to the default font if
# not). The % sign is a separate normal-font label - 7-seg fonts have no
# percent glyph.
def _seg_word(number, fs=24, marginright=None, font='DSEG7 Classic'):
    # marginright None = centered; else right-aligned marginright units in
    # from the border's right edge (same scheme the feedrate % label uses)
    halign = ('\t\t\t<horizontalalignment>center</horizontalalignment>\n'
              if marginright is None else
              '\t\t\t<horizontalalignment>right</horizontalalignment>\n'
              '\t\t\t<marginright>%d</marginright>\n' % marginright)
    return ('\n\t\t<plc_word>\n'
            '\t\t\t<number>%d</number>\n'
            '\t\t\t<color>#ff3333</color>\n'
            '\t\t\t<fontsize>%d</fontsize>\n'
            '\t\t\t<font>%s</font>\n'
            '\t\t\t<fontstyle>bold</fontstyle>\n'
            '\t\t\t<verticalalignment>center</verticalalignment>\n'
            '%s'
            '\t\t</plc_word>' % (number, fs, font, halign))


def _seg_label(content, fs, marginright):
    return ('\n\t\t<text>\n'
            '\t\t\t<content>%s</content>\n'
            '\t\t\t<fontsize>%d</fontsize>\n'
            '\t\t\t<color>#ff3333</color>\n'
            '\t\t\t<font>Arial</font>\n'
            '\t\t\t<fontstyle>bold</fontstyle>\n'
            '\t\t\t<horizontalalignment>right</horizontalalignment>\n'
            '\t\t\t<verticalalignment>center</verticalalignment>\n'
            '\t\t\t<marginright>%d</marginright>\n'
            '\t\t</text>' % (content, fs, marginright))


FEEDRATE_WORD = _seg_word(4)               # FinalFeedOverride_W, centered
FEEDRATE_PCT = _seg_label('%', 16, 68)
# spindle readout: [ XXX% XXXXRPM ] in one window, same 3-cell bezel as the
# feedrate display; every element is right-aligned so the group keeps its
# internal spacing (margins are right-edge offsets, per the feedrate %).
# One element per <border>: the VCP renders a single plc_word/text per
# border (stacking them in one border dropped the RPM half on-machine).
SPIN_ELEMENTS = (
    _seg_word(76, 18, 166),                # SpinOverride_W  -> "XXX"
    _seg_label('%', 13, 152),              # "%" hugging the override digits
    _seg_word(77, 13, 98, font='Arial'),   # SpinRPM_W: plain Arial like "%"
    _seg_label('RPM', 12, 68))


def render_readout_bezel_svg(w):
    # LED window smaller than the cell span: transparent artboard with a
    # centered dark bezel; one cell renders ~106 units wide, 84 tall
    x = (w - 146) / 2.0
    return (
        '<svg xmlns="http://www.w3.org/2000/svg" width="%d" height="84" '
        'viewBox="0 0 %d 84">'
        '<rect x="%.0f" y="28" width="146" height="28" rx="5" fill="#1a0000" '
        'stroke="#3a3630" stroke-width="2"/>'
        '<rect x="%.0f" y="31" width="138" height="5" rx="2" fill="#000000" '
        'opacity="0.5"/>'
        '</svg>\n' % (w, w, x, x + 4))


def render_skin():
    p = ['<vcp_skin>\n']
    p.append('\t<background>#141210</background>\n')
    p.append(_border(4, 3, 12, 2, label='FEEDRATE'))
    # readout: drawn bezel image (smaller than the cell span) under two
    # transparent borders carrying the 7-seg digits and the % label
    p.append('\t<image>\n'
             '\t\t<column_span>3</column_span>\n'
             '\t\t<column_start>4</column_start>\n'
             '\t\t<row_span>1</row_span>\n'
             '\t\t<row_start>11</row_start>\n'
             '\t\t<path>resources\\vcp\\images\\feedrate_bezel.svg</path>\n'
             '\t</image>\n')
    p.append(_border(4, 3, 11, 1, outline='Transparent',
                     extra=FEEDRATE_WORD))
    p.append(_border(4, 3, 11, 1, outline='Transparent',
                     extra=FEEDRATE_PCT))
    # spindle override % + commanded RPM readout, right-aligned on row 2
    # (same bezel image and span as the feedrate display)
    p.append('\t<image>\n'
             '\t\t<column_span>3</column_span>\n'
             '\t\t<column_start>4</column_start>\n'
             '\t\t<row_span>1</row_span>\n'
             '\t\t<row_start>2</row_start>\n'
             '\t\t<path>resources\\vcp\\images\\feedrate_bezel.svg</path>\n'
             '\t</image>\n')
    for el in SPIN_ELEMENTS:
        p.append(_border(4, 3, 2, 1, outline='Transparent', extra=el))
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
    _write(os.path.join(img_dir, 'feedrate_bezel.svg'),
           render_readout_bezel_svg(318))
    skin_dir = os.path.join(out_dir, 'resources', 'vcp', 'skins')
    os.makedirs(skin_dir, exist_ok=True)
    _write(os.path.join(skin_dir, 'acroloc_retro_vcp_skin.vcp'),
           render_skin())


def main():
    generate(REPO)
    print('retro VCP theme generated under %s' % REPO)


if __name__ == '__main__':
    main()
