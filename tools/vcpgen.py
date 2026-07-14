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
    'flood': ('<g transform="translate(34,10) scale(0.48)">' + '<path d="M60.12,38.62H35.79V32.19H60.12ZM37.24,37.17H58.67V33.64H37.24Z" fill="FILL"/><path d="M51.56,42.59h-7.2V37.17h7.2Zm-5.75-1.45h4.3V38.62h-4.3Z" fill="FILL"/><path d="M77.17,67.19H65.32V60H59.58a13,13,0,0,1-23.25,0H19.18V48.13h3.68c.85,0,1.7,0,2.54,0,3.64,0,7.29,0,10.93,0a13,13,0,0,1,23.24,0h2.28a30.42,30.42,0,0,1,4.26.17c5.28.73,11,4,11.07,9.42,0,.8,0,1.61,0,2.41v1.11c0,1.2,0,2.41,0,3.61Zm-10.4-1.45h9v-.92c0-1.2,0-2.41,0-3.62V60.09c0-.8,0-1.59,0-2.38-.06-4.58-5.13-7.35-9.82-8h0a28.64,28.64,0,0,0-4-.16h-3.2l-.19-.42a11.59,11.59,0,0,0-21,0l-.2.42h-.46c-3.83,0-7.6,0-11.37,0H20.62v9H37.24l.2.42a11.6,11.6,0,0,0,21,0l.19-.42h8.1Z" fill="FILL"/><path d="M85,92H58l9.63-25.11h7.88ZM60.14,90.54H82.93L74.54,68.33H68.66Z" fill="FILL"/>' + '</g>'),
    'hare':  ('<g transform="translate(20.5,39) scale(0.75)">'
              '<path d="' + HARE_PATH + '" fill="FILL"/>'
              '<ellipse cx="86.4" cy="23.98" rx="1.01" ry="0.61" fill="#ffffff" '
              'opacity="0.85"/></g>'),
    'tortoise': ('<g transform="translate(20.5,0.3) scale(0.75)">'
              '<path d="' + TORT_PATH + '" fill="FILL"/>'
              '<circle cx="79.41" cy="71.04" r="1.41" fill="#ffffff" '
              'opacity="0.85"/></g>'),
}
