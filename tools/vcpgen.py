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
    # cap occupies x[capx..capx+capw] y[15..81]; gradient coords are absolute
    if kind == 'radial':
        cap_geom = dict(cx=vbw / 2.0, cy=15 + 0.35 * 66, r=0.75 * capw)
    else:
        cap_geom = dict(x1=vbw / 2.0, y1=15, x2=vbw / 2.0, y2=81)
    p = []
    p.append('<svg xmlns="http://www.w3.org/2000/svg" width="%d" height="%d" '
             'viewBox="0 0 %d %d">' % (w, RENDER_H, vbw, VB_H))
    p.append('<defs>' + _bezel_grad('bz', vbw, VB_H)
             + _grad('cap', kind, stops, cap_geom) + '</defs>')
    p.append('<rect x="2" y="2" width="%d" height="93" rx="5" fill="url(#bz)" '
             'stroke="#100f0d" stroke-width="1"/>' % (vbw - 4))
    p.append('<rect x="6" y="6" width="%d" height="85" rx="3" fill="none" '
             'stroke="#c9c5be" stroke-width="0.6" opacity="0.35"/>' % (vbw - 12))
    p.append('<rect x="9" y="9" width="%d" height="79" rx="3" fill="#141210" '
             'stroke="#000000" stroke-width="1"/>' % (vbw - 18))
    p.append('<rect x="9" y="9" width="%d" height="8" rx="2" fill="#000000" '
             'opacity="0.45"/>' % (vbw - 18))
    if st['glow']:
        # fake bloom: layered translucent halo rects (no <filter> support)
        p.append('<rect x="%d" y="10" width="%d" height="76" rx="8" '
                 'fill="%s" opacity="0.18"/>'
                 % (capx - 5, capw + 10, st['stroke']))
        p.append('<rect x="%d" y="12" width="%d" height="72" rx="6" '
                 'fill="%s" opacity="0.30"/>'
                 % (capx - 3, capw + 6, st['stroke']))
    p.append('<rect x="%d" y="15" width="%d" height="66" rx="4" '
             'fill="url(#cap)" stroke="%s" stroke-width="1.4"/>'
             % (capx, capw, st['stroke']))
    p.append('<rect x="%d" y="18" width="%d" height="14" rx="2" '
             'fill="#ffffff" opacity="0.18"/>' % (capx + 3, capw - 6))
    p.append('<g transform="matrix(1 0 0 1 0 -10)">' + ic + texts + '</g>')
    p.append('</svg>')
    return ''.join(p) + '\n'


# ------------------------------------------------------------- icons ------
# Content coordinate system: cap center (58,58); FILL -> state text color,
# CX -> horizontal center.
TORT_PATH = 'M54.08,66.76s12.71,3,12.29,4.28S66,73,57.53,71,41,68.24,38.34,69.5c0,0-1.24-4.53-3.73-5.22s-4.83,0-5.52,1.38.28,4.83,2.35,5.93a57.86,57.86,0,0,0-4.84,5.8c-1.79,2.63-6.21,7-14.63,8.15s-7.46,7.73-.69,5.25,17.53-6.49,27.34-6.08,21.26,4.56,30.93.14c4.83,3.73,9.41,6.61,11.89,7s13.65,0,13.65,0,.82-2.12-3.73-2.6c-1.13-.12-9-1.25-9-1.25S74.52,83.88,74,82.36s.41-3.72.41-3.72,9.52,1.1,11.6,1a4.07,4.07,0,0,0,3.2-1.84l.1-.15c.67-1-2.92-8.11-6.48-9.37-3.35-1.19-4.8-2-6.76-1.38-1,.3-2.63,1.24-3.73,1.24S66.1,63.72,61.4,63.45,44.14,66.21,54.08,66.76Z'
HARE_PATH = 'M90.89,29.61a3.73,3.73,0,0,0,1.88-2.31,3.38,3.38,0,0,0,1-1.72c-.11-1.56-1.81-2.81-3.61-3.11a6.75,6.75,0,0,0-4.33-.42A33.18,33.18,0,0,0,79,24.27c-.49.06-2.62,1.55-2.76.92S69.66,15.58,60.34,10.3s-21.26,0-21.26,0c-8.89,3.47-15.15,16.84-16.17,18.33s-5.79-3.44-5.79-3.44c.62,5.81,8.7,8.06,8.7,8.06l-.43,6.94h7.28a20.09,20.09,0,0,1,.43-4C33.54,34.41,36,34.9,36,34.9l.43,5.29h6.41l2-6.28c2,1.16,11.15-.66,11.15-.66l-.44,6.94h6.41s3.93-6.94,4.51-6.77S66,40.19,66,40.19h6.11s1.75-5.12,2-6.75,7-1.45,7.64-1.71a7,7,0,0,1,3.72-1.09,16,16,0,0,0,5.38-1'

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
    'pump':  ('<g transform="matrix(1 0 0 1 3 -12)">'
              '<rect x="42" y="52" width="22" height="18" rx="2" fill="none" '
              'stroke="FILL" stroke-width="3"/>'
              '<circle cx="53" cy="61" r="4.5" fill="FILL"/>'
              '<path d="M64 56 h8 v-8" fill="none" stroke="FILL" '
              'stroke-width="3"/>'
              '<path d="M76 38 c-4 6 -4 9 0 9 c4 0 4 -3 0 -9 z" fill="FILL"/>'
              '</g>'),
    # stock CNC12 flood_coolant line-art (black outline paths), recolored
    'flood': ('<g transform="matrix(0.48 0 0 0.48 34 10)">' + '<path d="M60.12,38.62H35.79V32.19H60.12ZM37.24,37.17H58.67V33.64H37.24Z" fill="FILL"/><path d="M51.56,42.59h-7.2V37.17h7.2Zm-5.75-1.45h4.3V38.62h-4.3Z" fill="FILL"/><path d="M77.17,67.19H65.32V60H59.58a13,13,0,0,1-23.25,0H19.18V48.13h3.68c.85,0,1.7,0,2.54,0,3.64,0,7.29,0,10.93,0a13,13,0,0,1,23.24,0h2.28a30.42,30.42,0,0,1,4.26.17c5.28.73,11,4,11.07,9.42,0,.8,0,1.61,0,2.41v1.11c0,1.2,0,2.41,0,3.61Zm-10.4-1.45h9v-.92c0-1.2,0-2.41,0-3.62V60.09c0-.8,0-1.59,0-2.38-.06-4.58-5.13-7.35-9.82-8h0a28.64,28.64,0,0,0-4-.16h-3.2l-.19-.42a11.59,11.59,0,0,0-21,0l-.2.42h-.46c-3.83,0-7.6,0-11.37,0H20.62v9H37.24l.2.42a11.6,11.6,0,0,0,21,0l.19-.42h8.1Z" fill="FILL"/><path d="M85,92H58l9.63-25.11h7.88ZM60.14,90.54H82.93L74.54,68.33H68.66Z" fill="FILL"/>' + '</g>'),
    'hare':  ('<g transform="matrix(0.75 0 0 0.75 20.5 39)">'
              '<path d="' + HARE_PATH + '" fill="FILL"/>'
              '<ellipse cx="86.4" cy="23.98" rx="1.01" ry="0.61" fill="#ffffff" '
              'opacity="0.85"/></g>'),
    'tortoise': ('<g transform="matrix(0.75 0 0 0.75 20.5 0.3)">'
              '<path d="' + TORT_PATH + '" fill="FILL"/>'
              '<circle cx="79.41" cy="71.04" r="1.41" fill="#ffffff" '
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


def render_nameplate_svg():
    word, gap, cell = 'ACROLOC', 10, 64
    scale = cell / 90.0
    total = len(word) * cell + (len(word) - 1) * gap
    x = (634 - total) / 2.0
    glyphs = []
    for ch in word:
        glyphs.append('<path d="%s" fill="#4a2028" fill-rule="evenodd" '
                      'stroke="#3a1820" stroke-width="2" '
                      'stroke-linejoin="round"/>'
                      % _xform_path(NAME_GLYPHS[ch], scale, x, 18))
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
        '<defs><linearGradient id="alum" x1="317" y1="0" x2="317" y2="100" '
        'gradientUnits="userSpaceOnUse">'
        '<stop offset="0" stop-color="#d8d5d0"/>'
        '<stop offset="0.3" stop-color="#b8b4ae"/>'
        '<stop offset="0.6" stop-color="#cac6c0"/>'
        '<stop offset="1" stop-color="#8e8a84"/></linearGradient></defs>'
        '<rect x="2" y="2" width="630" height="96" rx="4" fill="url(#alum)" '
        'stroke="#100f0d" stroke-width="1.5"/>'
        '<rect x="6" y="6" width="622" height="88" rx="2" fill="none" '
        'stroke="#ffffff" stroke-width="0.8" opacity="0.4"/>'
        + ''.join(streaks) + ''.join(glyphs) + '</svg>\n')


# ------------------------------------------------------- round RESET ------
def render_reset_svg(tripped):
    cx, cy = 174, 138            # button center in the 348x268 artboard
    dome_r = 82 if tripped else 94
    dome_y = cy + 12 if tripped else cy - 8
    stops = (('#ffb0b0', '#ff3838', '#c40f0f', '#7a0505') if tripped
             else ('#f26b6b', '#d42a2a', '#8c0f0f', '#5c0505'))
    dome = _grad('dome', 'radial',
                 (('0', stops[0]), ('0.35', stops[1]), ('0.8', stops[2]),
                  ('1', stops[3])),
                 dict(cx=cx - 0.24 * dome_r, cy=dome_y - 0.4 * dome_r,
                      r=1.5 * dome_r))
    p = []
    p.append('<svg xmlns="http://www.w3.org/2000/svg" width="300" '
             'height="252" viewBox="0 0 348 268">')
    p.append('<defs>' + _bezel_grad('rbz', 348, 268) + dome +
             _grad('skirt', 'radial',
                   (('0', '#a81c1c'), ('0.7', '#6e0c0c'), ('1', '#3d0404')),
                   dict(cx=cx, cy=cy - 24, r=148)) +
             _grad('well', 'radial',
                   (('0', '#1c1916'), ('1', '#0a0908')),
                   dict(cx=cx, cy=cy - 27, r=244)) + '</defs>')
    p.append('<rect x="4" y="4" width="340" height="260" rx="8" '
             'fill="url(#rbz)" stroke="#100f0d" stroke-width="1.5"/>')
    p.append('<rect x="10" y="10" width="328" height="248" rx="5" fill="none" '
             'stroke="#c9c5be" stroke-width="0.8" opacity="0.35"/>')
    p.append('<rect x="15" y="15" width="318" height="238" rx="5" '
             'fill="url(#well)" stroke="#000000" stroke-width="1.5"/>')
    p.append('<rect x="15" y="15" width="318" height="16" rx="4" '
             'fill="#000000" opacity="0.45"/>')
    if tripped:
        # fake halo: layered translucent circles (no <filter> support)
        p.append('<circle cx="%d" cy="%d" r="122" fill="#ff2020" '
                 'opacity="0.10"/>' % (cx, cy + 8))
        p.append('<circle cx="%d" cy="%d" r="112" fill="#ff2020" '
                 'opacity="0.16"/>' % (cx, cy + 8))
    p.append('<circle cx="%d" cy="%d" r="106" fill="url(#skirt)" '
             'stroke="#2a0505" stroke-width="2"/>' % (cx, cy + 8))
    p.append('<circle cx="%d" cy="%d" r="%d" fill="url(#dome)" '
             'stroke="#4a0808" stroke-width="1.5"/>' % (cx, dome_y, dome_r))
    if tripped:
        p.append('<ellipse cx="%d" cy="%d" rx="%d" ry="16" fill="#000000" '
                 'opacity="0.35"/>' % (cx, dome_y - dome_r + 14, dome_r - 6))
        p.append('<ellipse cx="%d" cy="%d" rx="28" ry="14" fill="#ffffff" '
                 'opacity="0.14"/>' % (cx - 18, dome_y - 30))
        p.append(text_el('RESET', cx, 42, 26, '#ff5555'))
        p.append(text_el('TRIPPED', cx, 246, 26, '#ff5555'))
    else:
        p.append('<ellipse cx="%d" cy="%d" rx="40" ry="24" fill="#ffffff" '
                 'opacity="0.22"/>' % (cx - 24, dome_y - 30))
        p.append(text_el('RESET', cx, dome_y + 10, 32, '#ffd9d9'))
    p.append('</svg>')
    return ''.join(p) + '\n'


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
    # CRLF: CNC12 runs on a Windows host
    with open(path, 'w', newline='\r\n') as f:
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
