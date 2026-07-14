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
