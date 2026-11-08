#!/usr/bin/env python3
"""Contest #2800443 — Plot 83 New Cairo (17 x 25 m).
Claude generator: board1-claude.html, board2-claude.html, index.html.
Single source of geometry; every area printed on the sheets is computed here.
Plot frame: x = East-West (0 = west boundary, 25 = east spine), y = North-South (0 = south, 17 = north road).
"""
import html
import math
from pathlib import Path

HERE = Path(__file__).resolve().parent
PW, PH = 25.0, 17.0
PLOT_AREA = PW * PH                      # 425.00
DIAG = math.hypot(PW, PH)                # 30.23
BX0, BX1 = 3.0, 24.25                    # building x extent (3.0 W setback, 21.25 wide)
INK, VEL = '#1B1F24', '#F6F4EE'

# ---- plan frame (800 x 600 cell, 30 px/m) ----
S, OX, OY, CW, CH = 30, 30, 64, 800, 600


def X(x): return OX + S * x
def Y(y): return OY + S * (PH - y)


KIND = {
    'living': '#EFE4CC', 'wet': '#CFE3E8', 'service': '#E3DDCF', 'garage': '#E1E2DE',
    'bed': '#F1DFD6', 'core': '#D8D0BC', 'out': '#DCE7CF', 'work': '#E9E2D2',
    'roof': '#ECE9DF', 'pool': '#86C8DC', 'void': '#CFE0C0', 'pv': '#2E4A6B',
}


def esc(t): return html.escape(str(t), quote=True)


def rect(x0, y0, x1, y1, fill, stroke=INK, sw=1.5, extra=''):
    return (f'<rect x="{X(x0):.1f}" y="{Y(y1):.1f}" width="{S*(x1-x0):.1f}" height="{S*(y1-y0):.1f}" '
            f'fill="{fill}" stroke="{stroke}" stroke-width="{sw}" {extra}/>')


def line(x0, y0, x1, y1, stroke=INK, sw=1.5, extra=''):
    return f'<line x1="{X(x0):.1f}" y1="{Y(y0):.1f}" x2="{X(x1):.1f}" y2="{Y(y1):.1f}" stroke="{stroke}" stroke-width="{sw}" {extra}/>'


def text(px, py, t, fs=12, fill=INK, weight=600, anchor='middle', rot=0, extra='', family=None):
    fam = f' font-family="{family}"' if family else ''
    tr = f' transform="rotate({rot} {px:.1f} {py:.1f})"' if rot else ''
    return (f'<text x="{px:.1f}" y="{py:.1f}" font-size="{fs}" fill="{fill}" font-weight="{weight}" '
            f'text-anchor="{anchor}"{tr}{fam} {extra}>{esc(t)}</text>')
HALO = 'paint-order="stroke" stroke="#F6F4EE" stroke-width="2.6" stroke-linejoin="round"'


def label(cx, cy, name, area=None, fs=None, fill=INK, wpx=None):
    if not name:
        return ''
    lines = name.split('|')
    mx = max(len(l) for l in lines)
    if fs is None:
        w = wpx if wpx else 100
        fs = max(8, min(13, w / (0.58 * mx)))
    out = []
    n = len(lines) + (1 if area is not None else 0)
    y0 = Y(cy) - (n - 1) * fs * 0.6 + fs * 0.35
    for i, l in enumerate(lines):
        out.append(text(X(cx), y0 + i * fs * 1.2, l, fs, fill, 700, extra=HALO))
    if area is not None:
        out.append(text(X(cx), y0 + len(lines) * fs * 1.2, f'{area:.1f} m²', fs * 0.85, fill, 500, family='Menlo, monospace', extra=HALO))
    return ''.join(out)


AREAS = {}
_LBL = []


def flush():
    out = ''.join(_LBL)
    _LBL.clear()
    return out


def room(x0, y0, x1, y1, name, kind, key=None, show_area=True, fs=None, sw=2.6):
    a = (x1 - x0) * (y1 - y0)
    if key:
        AREAS[key] = a
    _LBL.append(label((x0 + x1) / 2, (y0 + y1) / 2, name, a if show_area else None, fs, wpx=S * (x1 - x0)))
    return rect(x0, y0, x1, y1, KIND[kind], sw=sw)


def box(x0, y0, x1, y1, fill='#FFFFFF', sw=1, op=1.0, stroke='#4B5560', rx=0):
    return (f'<rect x="{X(x0):.1f}" y="{Y(y1):.1f}" width="{S*(x1-x0):.1f}" height="{S*(y1-y0):.1f}" fill="{fill}" '
            f'stroke="{stroke}" stroke-width="{sw}" opacity="{op}" rx="{rx}"/>')


def circ(cx, cy, r, fill, stroke='#4B5560', sw=1, op=1.0):
    return f'<circle cx="{X(cx):.1f}" cy="{Y(cy):.1f}" r="{S*r:.1f}" fill="{fill}" stroke="{stroke}" stroke-width="{sw}" opacity="{op}"/>'


def win(x0, y0, x1, y1):
    """Window on an exterior wall: paper gap + glazing line."""
    return (line(x0, y0, x1, y1, VEL, 8) + line(x0, y0, x1, y1, '#3C8DB8', 3.4) +
            line(x0, y0, x1, y1, '#FFFFFF', 1.2))


def door(hx, hy, dx, dy, nx, ny, w=0.9):
    ex, ey = X(hx + dx * w), Y(hy + dy * w)
    fx, fy = X(hx + nx * w), Y(hy + ny * w)
    px, py = X(hx), Y(hy)
    cr = (ex - px) * (fy - py) - (ey - py) * (fx - px)
    sweep = 1 if cr > 0 else 0
    r = S * w
    return (f'<line x1="{px:.1f}" y1="{py:.1f}" x2="{ex:.1f}" y2="{ey:.1f}" stroke="{VEL}" stroke-width="7"/>'
            f'<line x1="{px:.1f}" y1="{py:.1f}" x2="{fx:.1f}" y2="{fy:.1f}" stroke="{INK}" stroke-width="1.6"/>'
            f'<path d="M {ex:.1f} {ey:.1f} A {r:.1f} {r:.1f} 0 0 {sweep} {fx:.1f} {fy:.1f}" fill="none" stroke="{INK}" stroke-width="0.9"/>')


def dimh(x0, x1, ypx, t, fs=11, fill='#7A1F1F'):
    a, b = X(x0), X(x1)
    return (f'<line x1="{a:.1f}" y1="{ypx}" x2="{b:.1f}" y2="{ypx}" stroke="{fill}" stroke-width="1"/>'
            f'<line x1="{a:.1f}" y1="{ypx-4}" x2="{a:.1f}" y2="{ypx+4}" stroke="{fill}" stroke-width="1"/>'
            f'<line x1="{b:.1f}" y1="{ypx-4}" x2="{b:.1f}" y2="{ypx+4}" stroke="{fill}" stroke-width="1"/>'
            f'<line x1="{a-3:.1f}" y1="{ypx+3}" x2="{a+3:.1f}" y2="{ypx-3}" stroke="{fill}" stroke-width="1.4"/>'
            f'<line x1="{b-3:.1f}" y1="{ypx+3}" x2="{b+3:.1f}" y2="{ypx-3}" stroke="{fill}" stroke-width="1.4"/>'
            + text((a + b) / 2, ypx - 3, t, fs, fill, 700, family='Menlo, monospace'))


def dimv(y0, y1, xpx, t, fs=11, fill='#7A1F1F'):
    a, b = Y(y0), Y(y1)
    return (f'<line x1="{xpx}" y1="{a:.1f}" x2="{xpx}" y2="{b:.1f}" stroke="{fill}" stroke-width="1"/>'
            f'<line x1="{xpx-4}" y1="{a:.1f}" x2="{xpx+4}" y2="{a:.1f}" stroke="{fill}" stroke-width="1"/>'
            f'<line x1="{xpx-4}" y1="{b:.1f}" x2="{xpx+4}" y2="{b:.1f}" stroke="{fill}" stroke-width="1"/>'
            f'<line x1="{xpx-3}" y1="{a+3:.1f}" x2="{xpx+3}" y2="{a-3:.1f}" stroke="{fill}" stroke-width="1.4"/>'
            f'<line x1="{xpx-3}" y1="{b+3:.1f}" x2="{xpx+3}" y2="{b-3:.1f}" stroke="{fill}" stroke-width="1.4"/>'
            + text(xpx - 3, (a + b) / 2, t, fs, fill, 700, rot=-90, family='Menlo, monospace'))


# ------------------------------------------------------------------ site layer
POOL = (12.0, 0.5, 18.0, 3.5)          # 6.0 (E-W) x 3.0 (N-S)
BUF = (10.5, 0.0, 19.5, 5.0)           # pool + 1.5 m buffer to building walls


def defs():
    return ('<defs>'
            f'<pattern id="hat" width="7" height="7" patternUnits="userSpaceOnUse" patternTransform="rotate(45)"><line x1="0" y1="0" x2="0" y2="7" stroke="{INK}" stroke-width="1" opacity=".35"/></pattern>'
            '<pattern id="hat2" width="6" height="6" patternUnits="userSpaceOnUse" patternTransform="rotate(-45)"><line x1="0" y1="0" x2="0" y2="6" stroke="#8A6B2F" stroke-width="1.2" opacity=".55"/></pattern>'
            '<pattern id="wave" width="14" height="8" patternUnits="userSpaceOnUse"><path d="M0 4 Q3.5 0 7 4 T14 4" fill="none" stroke="#FFFFFF" stroke-width="1" opacity=".8"/></pattern>'
            '<marker id="arr" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="7" markerHeight="7" orient="auto"><path d="M0 0 L10 5 L0 10 z" fill="context-stroke"/></marker>'
            '</defs>')


def site(level, tag):
    p = []
    p.append(f'<rect x="0" y="0" width="{CW}" height="{CH}" fill="{VEL}"/>')
    # road (north), spine (east)
    p.append(f'<rect x="{OX}" y="30" width="{S*PW}" height="{OY-30}" fill="#CFCCC3"/>')
    p.append(f'<line x1="{OX}" y1="{OY-17}" x2="{OX+S*PW}" y2="{OY-17}" stroke="#F6F4EE" stroke-width="2" stroke-dasharray="14 9"/>')
    p.append(f'<rect x="{OX+S*PW}" y="{OY}" width="{CW-OX-S*PW}" height="{S*PH}" fill="#E4DCC8"/>')
    p.append(text(OX + S * PW + 10, OY + S * PH / 2, '10m E SPINE', 10, '#6B6250', 700, rot=90))
    p.append(text(OX + 90, 49, '15m NORTH ROAD (main entrance + car ramp)', 10.5, '#4A463C', 700, 'start'))
    # plot ground
    gfill = '#E5EBDA' if level != 'B' else '#DCDDD3'
    p.append(rect(0, 0, PW, PH, gfill, stroke='none', sw=0))
    # setback strips
    p.append(rect(0, 0, 3.0, PH, 'url(#hat)', stroke='none', sw=0, extra='opacity=".45"'))
    p.append(rect(0, 0, PW, 4.0, 'url(#hat)', stroke='none', sw=0, extra='opacity=".28"'))
    p.append(line(3.0, 0, 3.0, PH, '#9B2C2C', 1.1, 'stroke-dasharray="7 4"'))
    p.append(line(0, 4.0, PW, 4.0, '#9B2C2C', 1.1, 'stroke-dasharray="7 4"'))
    # diagonal (30.23 m)
    p.append(line(0, 0, PW, PH, '#7A1F1F', 1, 'stroke-dasharray="2 5" opacity=".4"'))
    ang = -math.degrees(math.atan2(PH, PW))
    p.append(text(X(PW * 0.06 + 0.4), Y(PH * 0.06 + 0.5), f'DIAG {DIAG:.2f}m', 9.5, '#7A1F1F', 700, 'middle', ang, family='Menlo, monospace'))
    # pool + buffer
    bx0, by0, bx1, by1 = BUF
    p.append(rect(bx0, max(by0, 0), bx1, by1, '#C9B98F', stroke='#8A6B2F', sw=1, extra='opacity=".55"'))
    p.append(rect(bx0, max(by0, 0), bx1, by1, 'url(#hat2)', stroke='none', sw=0))
    x0, y0, x1, y1 = POOL
    p.append(rect(x0 - 0.12, y0 - 0.12, x1 + 0.12, y1 + 0.12, '#FFFFFF', stroke=INK, sw=2))
    p.append(rect(x0, y0, x1, y1, KIND['pool'], stroke='#1F6E8C', sw=1.5))
    p.append(rect(x0, y0, x1, y1, 'url(#wave)', stroke='none', sw=0))
    p.append(text(X((x0 + x1) / 2), Y((y0 + y1) / 2) + 4, 'POOL 3.0 × 6.0 m', 12, '#0D3C52', 800))
    p.append(f'<g>{dimh(x0, x1, int(Y(y1)-8), "6.00m", 9.5)}</g>')
    p.append(text(X(bx0 + 0.15), Y(4.62), '1.50m insulated backfill buffer', 8.5, '#5E4A1A', 700, 'start'))
    p.append(dimv(3.5, 5.0, int(X(19.0)), '1.50', 9))
    return ''.join(p)


def trees():
    out = []
    for (x, y, r) in [(21.2, 1.9, .8), (23.4, 3.8, .6), (22.9, 0.8, .45), (8.9, 0.9, .5)]:
        out.append(circ(x, y, r, '#8DB872', '#3E6B2F', 1.2, .95) + circ(x, y, r * .35, '#5E9A4B', 'none', 0, .9))
    return ''.join(out)


def frame(level_code, title, sub, note=''):
    p = []
    p.append(f'<rect x="0" y="0" width="{CW}" height="30" fill="{INK}"/>')
    p.append(text(12, 21, title, 14.5, '#F6F4EE', 800, 'start'))
    p.append(text(CW - 44, 21, sub, 10.5, '#D9C58B', 600, 'end', family='Menlo, monospace'))
    # north arrow
    p.append(f'<g transform="translate({CW-22},15)"><circle r="11" fill="#F6F4EE"/><path d="M0 -9 L5 7 L0 3 L-5 7 z" fill="{INK}"/><text y="-11.5" x="0" font-size="8" fill="#F6F4EE" text-anchor="middle" font-weight="800">N</text></g>')
    # outer dims
    ypx = OY + S * PH + 10
    p.append(dimh(0, PW, ypx + 13, '25.00m (E–W)', 11))
    p.append(dimv(0, PH, 21, '17.00m (N–S)', 11))
    p.append(dimh(0, 3.0, 58, '3.0m W', 9.5))
    p.append(dimh(BX0, BX1, 58, '21.25m', 10.5))
    p.append(dimv(0, 4.0, int(X(24.62)), '4.0m S', 8.5))
    return ''.join(p)


def stair(x0, y0, x1, y1, n, vertical=True):
    out = [box(x0, y0, x1, y1, '#F7F2E4', 1.2)]
    for i in range(1, n):
        if vertical:
            yy = y0 + (y1 - y0) * i / n
            out.append(line(x0, yy, x1, yy, '#4B5560', 0.8))
        else:
            xx = x0 + (x1 - x0) * i / n
            out.append(line(xx, y0, xx, y1, '#4B5560', 0.8))
    return ''.join(out)


def core_plan(level):
    """Core NW zone x3..8, y12.5..17 (option B drawn: lift adjacent to stair)."""
    out = [rect(3, 12.5, 8, 17, KIND['core'], sw=2.6)]
    # dogleg stair (2.7 wide) with centre well
    out.append(stair(3.15, 12.65, 4.45, 16.0, 9))
    out.append(stair(4.55, 12.65, 5.7, 16.0, 9))
    out.append(box(3.15, 16.0, 5.7, 16.85, '#F7F2E4', 1.2))
    out.append(line(4.5, 12.65, 4.5, 16.0, INK, 1.2))
    out.append(f'<path d="M {X(3.8):.1f} {Y(12.9):.1f} L {X(3.8):.1f} {Y(15.4):.1f} " stroke="#B03A2E" stroke-width="1.4" marker-end="url(#arr)" fill="none" opacity=".8"/>')
    # lift shaft
    out.append(box(5.85, 15.0, 7.85, 16.9, '#EDEDED', 1.6, stroke=INK))
    out.append(line(5.85, 15.0, 7.85, 16.9, '#4B5560', 0.9))
    out.append(line(5.85, 16.9, 7.85, 15.0, '#4B5560', 0.9))
    out.append(text(X(6.85), Y(15.95) + 3, 'LIFT', 8.5, INK, 800))
    out.append(text(X(4.45), Y(16.45) + 3, 'STAIR', 9, INK, 800))
    out.append(text(X(6.95), Y(13.7), 'LOBBY', 9, INK, 800))
    return ''.join(out)


def car(x0, y0, w=2.0, h=4.6, vertical=True):
    cx0, cy0, cx1, cy1 = x0, y0, x0 + w, y0 + h
    out = [f'<rect x="{X(cx0):.1f}" y="{Y(cy1):.1f}" width="{S*w:.1f}" height="{S*h:.1f}" rx="9" fill="#7E8A97" stroke="#2F3944" stroke-width="1.4"/>']
    out.append(f'<rect x="{X(cx0+0.2):.1f}" y="{Y(cy1-0.9):.1f}" width="{S*(w-0.4):.1f}" height="{S*0.55:.1f}" rx="4" fill="#C7D6E2" stroke="#2F3944" stroke-width="0.8"/>')
    out.append(f'<rect x="{X(cx0+0.2):.1f}" y="{Y(cy0+1.0):.1f}" width="{S*(w-0.4):.1f}" height="{S*0.5:.1f}" rx="4" fill="#C7D6E2" stroke="#2F3944" stroke-width="0.8"/>')
    out.append(f'<rect x="{X(cx0+0.3):.1f}" y="{Y(cy1-1.7):.1f}" width="{S*(w-0.6):.1f}" height="{S*1.9:.1f}" rx="5" fill="#97A4B1" stroke="none"/>')
    return ''.join(out)


def bed(x0, y0, x1, y1, head='n'):
    out = [box(x0, y0, x1, y1, '#FFFFFF', 1.1, rx=2)]
    pw, pl = 0.75, 0.4
    if head == 'n':
        out += [box(x0 + .1, y1 - pl - .08, x0 + .1 + pw, y1 - .08, '#E8EEF5', .8), box(x1 - .1 - pw, y1 - pl - .08, x1 - .1, y1 - .08, '#E8EEF5', .8)]
    elif head == 'e':
        out += [box(x1 - pl - .08, y0 + .1, x1 - .08, y0 + .1 + pw, '#E8EEF5', .8), box(x1 - pl - .08, y1 - .1 - pw, x1 - .08, y1 - .1, '#E8EEF5', .8)]
    elif head == 's':
        out += [box(x0 + .1, y0 + .08, x0 + .1 + pw, y0 + .08 + pl, '#E8EEF5', .8), box(x1 - .1 - pw, y0 + .08, x1 - .1, y0 + .08 + pl, '#E8EEF5', .8)]
    out.append(box(x0 + .05, y0 + .05, x1 - .05, y0 + (y1 - y0) * .5 if head == 'n' else y1 - .05, 'none', .6, 0.5, stroke='#7A8794'))
    return ''.join(out)


def wc(x, y, rot_n=True):
    return box(x, y, x + 0.4, y + 0.65, '#FFFFFF', 1, rx=5) + box(x, y + 0.5, x + 0.4, y + 0.75, '#FFFFFF', 1)


def sofa(x0, y0, x1, y1):
    return box(x0, y0, x1, y1, '#C9A98B', 1.1, rx=3)


def table(x0, y0, x1, y1, chairs=True, horizontal=True):
    out = [box(x0, y0, x1, y1, '#E6D2B0', 1.2, rx=3)]
    if chairs:
        if horizontal:
            n = max(2, int((x1 - x0) / 0.6))
            for i in range(n):
                cx = x0 + (i + .5) * (x1 - x0) / n
                out += [box(cx - .2, y1 + .06, cx + .2, y1 + .46, '#B79C73', .8, rx=2), box(cx - .2, y0 - .46, cx + .2, y0 - .06, '#B79C73', .8, rx=2)]
        else:
            n = max(2, int((y1 - y0) / 0.6))
            for i in range(n):
                cy = y0 + (i + .5) * (y1 - y0) / n
                out += [box(x1 + .06, cy - .2, x1 + .46, cy + .2, '#B79C73', .8, rx=2), box(x0 - .46, cy - .2, x0 - .06, cy + .2, '#B79C73', .8, rx=2)]
    return ''.join(out)


def counter(x0, y0, x1, y1):
    return box(x0, y0, x1, y1, '#D9D4C7', 1.2) + box(x0 + .1, y0 + .1, x0 + .6, y0 + .55, '#9FB3C0', .8, rx=2)


# ------------------------------------------------------------------ levels
def swept_overlay():
    """Swept path: outer R=5.8 / inner R=3.2 (2.6 m car lane), left-turn from aisle into stalls 2,4,6."""
    out = ['<g class="swept">']
    # approach centre line (ramp -> wing -> aisle)
    pts = [(2.2, 16.6), (2.2, 3.4), (2.6, 2.9), (9.2, 2.9), (9.5, 4.2), (9.5, 9.0), (24.0, 9.0)]
    d = 'M ' + ' L '.join(f'{X(a):.1f} {Y(b):.1f}' for a, b in pts)
    out.append(f'<path d="{d}" fill="none" stroke="#C0392B" stroke-width="2.4" stroke-dasharray="9 5" marker-end="url(#arr)" opacity=".95"/>')
    cols = {1: '#C0392B', 3: '#D35400', 5: '#8E44AD'}
    for i in (1, 3, 5):
        xs = 8.5 + 2.6 * i + 1.3
        cx, cy = xs - 4.5, 13.5
        ro, ri = 5.8, 3.2
        p1 = (cx, cy - ro); p2 = (cx + ro, cy); p3 = (cx + ri, cy); p4 = (cx, cy - ri)
        d = (f'M {X(p1[0]):.1f} {Y(p1[1]):.1f} A {S*ro:.1f} {S*ro:.1f} 0 0 0 {X(p2[0]):.1f} {Y(p2[1]):.1f} '
             f'L {X(p3[0]):.1f} {Y(p3[1]):.1f} A {S*ri:.1f} {S*ri:.1f} 0 0 1 {X(p4[0]):.1f} {Y(p4[1]):.1f} Z')
        out.append(f'<path d="{d}" fill="{cols[i]}" fill-opacity=".20" stroke="{cols[i]}" stroke-width="1.6" stroke-dasharray="5 3"/>')
        out.append(text(X(cx + 4.6), Y(cy - 4.9) + 4, f'P{i+1}', 10, cols[i], 800))
    out.append(f'<rect x="{X(11.2):.1f}" y="{Y(8.0):.1f}" width="190" height="34" fill="#FFFFFF" fill-opacity=".92" stroke="#C0392B" stroke-width="1"/>')
    out.append(text(X(11.2) + 6, Y(8.0) + 14, 'SWEPT PATH  R_out = 5.8 m', 10, '#C0392B', 800, 'start', family='Menlo, monospace'))
    out.append(text(X(11.2) + 6, Y(8.0) + 27, 'R_in = 3.2 m · lane 2.6 m · 6.0m aisle', 9.5, '#C0392B', 700, 'start', family='Menlo, monospace'))
    out.append('</g>')
    return ''.join(out)


def passive_overlay(level):
    out = ['<g class="passive">']
    wind = '#1E78C8'
    for i, x in enumerate((9.5, 12.5, 15.5)):
        y_end = {'B': 9.5, 'G': 8.2, 'T': 6.6, 'R': 12.2}[level]
        out.append(f'<path class="flow" d="M {X(x):.1f} {Y(19.2):.1f} L {X(x):.1f} {Y(y_end):.1f}" stroke="{wind}" stroke-width="3" fill="none" stroke-dasharray="10 6" marker-end="url(#arr)"/>')
    out.append(text(X(12.5), Y(19.3) - 2, 'PREVAILING NORTH WIND', 10, wind, 800, family='Menlo, monospace'))
    if level != 'B':
        out.append(f'<path class="flow" d="M {X(15.5):.1f} {Y(9.7):.1f} C {X(18):.1f} {Y(9.7):.1f} {X(18):.1f} {Y(8):.1f} {X(15.5):.1f} {Y(8):.1f}" stroke="{wind}" stroke-width="2" fill="none" stroke-dasharray="6 4"/>')
        out.append(text(X(15.5), Y(9.75) + 3, 'STACK ↑', 9, wind, 800))
    for x, c, t in ((20.0, '#E8710A', 'SUMMER 83.4°'), (22.6, '#2B7BB9', 'WINTER 36.6°')):
        out.append(f'<path d="M {X(x):.1f} {Y(0.2):.1f} L {X(x):.1f} {Y(2.6):.1f}" stroke="{c}" stroke-width="3" fill="none" marker-end="url(#arr)"/>')
        out.append(text(X(x), Y(2.9), t, 9, c, 800, family='Menlo, monospace'))
    out.append('</g>')
    return ''.join(out)


def plan_basement(passive=False):
    AREAS.clear()
    p = [site('B', 'B')]
    # ramp
    p.append(rect(0, 1, 3, 17, '#D5D0C1', sw=3))
    p.append(rect(0, 1, 3, 17, 'url(#hat)', stroke='none', sw=0))
    for yy in (14, 11, 8, 5):
        p.append(f'<path d="M {X(2.2):.1f} {Y(yy+1.2):.1f} L {X(2.2):.1f} {Y(yy-0.2):.1f}" stroke="{INK}" stroke-width="1.6" marker-end="url(#arr)" fill="none"/>')
    p.append(text(X(0.9), Y(9.5), 'CAR RAMP 20% · 16.0 m · 3.0 m wide ↓ −3.20', 10.5, INK, 800, rot=-90, extra=HALO))
    # garage + wings
    p.append(room(3, 1, 10.5, 5, 'DRIVE WING|(ramp → garage)', 'garage', 'bsmt_wing', fs=11))
    p.append(room(8, 6, 24.25, 12, '', 'garage', 'bsmt_aisle', show_area=False))
    _LBL.append(text(X(16.1), Y(11.2), '6.0 m MANEUVERING AISLE · COLUMN-FREE', 11.5, INK, 800, extra=HALO))
    p.append(rect(8, 5, 10.5, 6, KIND['garage'], sw=2))
    p.append(room(10.5, 5, 19.5, 6, 'MEP / LIGHT TRENCH', 'service', None, show_area=False, fs=9))
    # stalls
    for i in range(6):
        x0 = 8.5 + 2.6 * i
        p.append(rect(x0, 12, x0 + 2.6, 17, KIND['garage'], sw=1.6))
        p.append(car(x0 + 0.3, 12.2))
        p.append(text(X(x0 + 1.3), Y(16.9) + 1, f'P{i+1}', 11, '#0B1522', 800))
    for i in range(7):
        x = 8.5 + 2.6 * i
        p.append(box(x - 0.2, 11.8, x + 0.2, 12.2, INK, 1, stroke=INK))
    # west amenity block
    p.append(room(3, 9.5, 8, 12.5, 'SMALL GYM', 'work', 'bsmt_gym'))
    p.append(box(3.3, 10.0, 5.2, 10.7, '#BFC7CF', 1)); p.append(box(5.6, 11.4, 7.5, 12.1, '#BFC7CF', 1)); circ_ = circ(6.5, 10.3, .35, '#BFC7CF')
    p.append(circ_)
    p.append(room(3, 7.5, 4.5, 9.5, 'BATH|1', 'wet', 'bsmt_bath1', fs=8.5))
    p.append(room(4.5, 7.5, 6, 9.5, 'BATH|2', 'wet', 'bsmt_bath2', fs=8.5))
    p.append(room(6, 7.5, 8, 9.5, 'KITCH-|ENETTE', 'service', 'bsmt_kit', fs=8.5))
    p.append(wc(3.2, 8.0)); p.append(wc(4.7, 8.0)); p.append(counter(6.1, 8.9, 7.9, 9.4))
    p.append(room(3, 5, 5.5, 7.5, 'STORE', 'service', 'bsmt_store'))
    p.append(room(5.5, 5, 6.75, 7.5, 'ELEC|UTIL', 'service', 'bsmt_elec', fs=8.5))
    p.append(room(6.75, 5, 8, 7.5, 'WATER|UTIL', 'service', 'bsmt_water', fs=8.5))
    # family room facing the pool
    p.append(room(19.5, 1, 24.25, 6, 'FAMILY SITTING|overlooks pool', 'living', 'bsmt_family', fs=11))
    p.append(sofa(20.0, 1.4, 23.6, 2.2)); p.append(sofa(23.4, 2.4, 24.1, 4.8)); p.append(box(20.9, 3.0, 22.3, 4.0, '#E6D2B0', 1, rx=3))
    # core
    p.append(core_plan('B'))
    # walls
    poly = [(3, 1), (10.5, 1), (10.5, 5), (19.5, 5), (19.5, 1), (24.25, 1), (24.25, 17), (3, 17)]
    pts = ' '.join(f'{X(a):.1f},{Y(b):.1f}' for a, b in poly)
    p.append(f'<polygon points="{pts}" fill="none" stroke="{INK}" stroke-width="7" stroke-linejoin="miter"/>')
    p.append(line(3, 1.5, 3, 4.5, VEL, 7))
    p.append(text(X(3) + 5, Y(3.0) + 3, 'GARAGE DOOR', 7.5, '#6B1F1F', 800, rot=-90))
    p.append(win(19.5, 1.5, 19.5, 5.4)); p.append(win(20.2, 1, 23.8, 1))
    p.append(door(21.0, 6, 1, 0, 0, -1, .9)); p.append(door(8, 10.2, 0, 1, -1, 0, .9)); p.append(door(8, 8.2, 0, 1, -1, 0, .8))
    p.append(door(8, 13.4, 0, 1, 1, 0, .9)); p.append(door(10.5, 17.0, 1, 0, 0, -1, .0001))
    p.append(flush())
    p.append(frame('B', 'A-01 · BASEMENT −3.20 m · 304.0 m² · 6 CARS · SWEPT PATH · POOL BUFFER',
                   f'SHEET A-01 · PLOT 83 · {PLOT_AREA:.0f} m²'))
    p.append(swept_overlay())
    if passive:
        p.append(passive_overlay('B'))
    return ''.join(p)


def plan_ground(passive=False):
    p = [site('G', 'G'), trees()]
    # ramp
    p.append(rect(0, 1, 3, 17, '#D5D0C1', sw=3))
    p.append(rect(0, 1, 3, 17, 'url(#hat)', stroke='none', sw=0))
    for yy in (14, 11, 8, 5):
        p.append(f'<path d="M {X(2.2):.1f} {Y(yy+1.2):.1f} L {X(2.2):.1f} {Y(yy-0.2):.1f}" stroke="{INK}" stroke-width="1.6" marker-end="url(#arr)" fill="none"/>')
    p.append(text(X(0.9), Y(9.5), 'OPEN CAR RAMP ↓ −3.20 (20%)', 10.5, INK, 800, rot=-90, extra=HALO))
    p.append(room(3, 12.5, 8, 17, '', 'core', None, False))
    p.append(room(8, 14.5, 12, 17, 'ENTRANCE|LOBBY', 'living', 'g_lobby'))
    p.append(room(12, 11.5, 17, 17, 'GUEST MAJLIS|(north · prevailing wind)', 'living', 'g_majlis', fs=10.5))
    p.append(room(8, 11.5, 12, 14.5, 'FAMILY|LOUNGE', 'living', 'g_lounge'))
    p.append(room(8, 8, 14, 11.5, 'DINING', 'living', 'g_dining'))
    p.append(room(14, 8, 17, 11.5, 'COURTYARD|VENT SHAFT', 'void', 'g_court', fs=9.5, sw=2))
    p.append(room(8, 7, 17, 8, 'SOUTH LOGGIA  (shaded by 1.0 m overhang)', 'out', 'g_loggia', show_area=False, fs=9))
    p.append(room(3, 9, 8, 12.5, 'KITCHEN / PREP', 'service', 'g_kitchen'))
    p.append(room(3, 7, 5.5, 9, 'ZERO-WASTE|HUB', 'service', 'g_hub', fs=9))
    p.append(room(5.5, 7, 8, 9, 'WC +|LAUNDRY', 'wet', 'g_wc', fs=9))
    p.append(room(17, 7, 24.25, 12, 'GUEST SUITE', 'bed', 'g_guest'))
    p.append(room(17, 12, 24.25, 17, 'STUDY / OFFICE', 'work', 'g_office'))
    # core
    p.append(core_plan('G'))
    # furniture
    p.append(sofa(12.4, 15.9, 16.4, 16.7)); p.append(sofa(12.4, 12.0, 13.0, 15.6)); p.append(box(14.2, 13.9, 15.8, 14.9, '#E6D2B0', 1, rx=3))
    p.append(sofa(8.3, 12.0, 11.7, 12.7)); p.append(box(9.2, 13.1, 10.8, 13.9, '#E6D2B0', 1, rx=3))
    p.append(table(9.0, 9.4, 12.6, 10.3))
    p.append(counter(3.1, 11.8, 7.9, 12.4)); p.append(counter(3.1, 9.2, 3.7, 11.8)); p.append(box(4.8, 10.2, 6.8, 11.0, '#D9D4C7', 1.2))
    p.append(bed(18.0, 8.0, 20.0, 10.0, 'e')); p.append(box(23.4, 8.0, 24.1, 10.8, '#D9D4C7', 1))
    p.append(box(18.0, 15.9, 21.2, 16.7, '#D9C9A8', 1.2)); p.append(box(23.4, 12.3, 24.1, 16.7, '#D9D4C7', 1))
    p.append(wc(5.8, 8.0)); p.append(box(6.8, 7.2, 7.7, 8.0, '#BFC7CF', 1))
    for (x, y) in ((15.0, 9.2), (15.9, 10.5), (14.5, 10.6)):
        p.append(circ(x, y, .25, '#6FA55A', '#3E6B2F', 1))
    # walls
    p.append(f'<rect x="{X(BX0):.1f}" y="{Y(17):.1f}" width="{S*(BX1-BX0):.1f}" height="{S*10:.1f}" fill="none" stroke="{INK}" stroke-width="7"/>')
    p.append(win(12.8, 17, 16.4, 17)); p.append(win(18.2, 17, 23.2, 17)); p.append(win(24.25, 8.2, 24.25, 11.2)); p.append(win(24.25, 13.0, 24.25, 16.2))
    p.append(win(3, 10.0, 3, 12.0)); p.append(win(3, 7.6, 3, 8.4)); p.append(win(9.0, 7, 13.0, 7)); p.append(win(18.0, 7, 23.0, 7))
    p.append(door(9.0, 17, 1, 0, 0, -1, 1.2) .replace('stroke-width="7"', 'stroke-width="8"'))
    p.append(door(8, 15.2, 0, 1, 1, 0, .9)); p.append(door(12, 14.0, 0, 1, -1, 0, .9)); p.append(door(17, 9.0, 0, 1, 1, 0, .9)); p.append(door(17, 14.5, 0, 1, 1, 0, .9))
    p.append(door(8, 10.3, 0, 1, 1, 0, .9)); p.append(door(4.0, 9.0, 1, 0, 0, 1, .8))
    p.append(flush())
    p.append(frame('G', 'A-01 · GROUND FLOOR  +0.45 m  ·  50% = 212.50 m²',
                   f'SHEET A-01 · PLOT 83 · {PLOT_AREA:.0f} m²'))
    p.append(dimh(BX0, BX1, int(Y(6.3)), '21.25m', 10.5)); p.append(dimv(7, 17, int(X(24.7)), '10.00m', 9))
    p.append(text(X(3.3), Y(3.0), 'GROUND  21.25 × 10.00', 10.5, '#7A1F1F', 800, 'start', family='Menlo, monospace')); p.append(text(X(3.3), Y(2.2), '= 212.50 m² (50.00 %)', 10.5, '#7A1F1F', 800, 'start', family='Menlo, monospace'))
    p.append(swept_overlay().replace('class="swept"', 'class="swept" style="display:none"') if False else '')
    if passive:
        p.append(passive_overlay('G'))
    return ''.join(p)


def plan_typical(passive=False):
    p = [site('T', 'T'), trees()]
    p.append(room(3, 12.5, 8, 17, '', 'core', None, False))
    p.append(room(8, 11.5, 17, 17, 'RECEPTION / LIVING|(north · prevailing wind)', 'living', 't_recep', fs=11))
    p.append(room(8, 8, 14, 11.5, 'DINING', 'living', 't_dining'))
    p.append(room(14, 8, 17, 11.5, 'COURTYARD|VENT SHAFT', 'void', 't_court', fs=9.5, sw=2))
    p.append(room(8, 6, 14, 8, 'PASSAGE / STUDY NOOK', 'work', 't_pass', fs=9))
    p.append(room(14, 6, 17, 8, 'BALCONY', 'out', 't_balc', fs=9))
    p.append(room(3, 9, 8, 12.5, 'KITCHEN|(west wall)', 'service', 't_kitchen', fs=10))
    p.append(room(3, 6, 5.5, 9, 'BATH 1', 'wet', 't_bath1', fs=9.5))
    p.append(room(5.5, 6, 8, 9, 'BATH 2', 'wet', 't_bath2', fs=9.5))
    p.append(room(17, 13.33, 24.25, 17, 'MASTER BEDROOM|(east)', 'bed', 't_bed1', fs=10))
    p.append(room(17, 9.67, 24.25, 13.33, 'BEDROOM 2|(east)', 'bed', 't_bed2', fs=10))
    p.append(room(17, 6, 24.25, 9.67, 'BEDROOM 3|(east)', 'bed', 't_bed3', fs=10))
    p.append(core_plan('T'))
    # furniture
    p.append(sofa(9.0, 15.9, 13.2, 16.7)); p.append(sofa(15.9, 12.0, 16.7, 15.7)); p.append(sofa(9.0, 12.0, 9.7, 15.0)); p.append(box(11.0, 13.6, 14.0, 14.7, '#E6D2B0', 1, rx=3)); p.append(box(13.4, 11.7, 15.6, 12.1, '#2F3944', 1))
    p.append(table(9.4, 9.4, 12.8, 10.3))
    p.append(counter(3.1, 12.0, 7.9, 12.4)); p.append(counter(3.1, 9.1, 3.55, 12.0)); p.append(box(4.7, 10.3, 6.7, 11.1, '#D9D4C7', 1.2))
    p.append(wc(3.3, 6.6)); p.append(box(4.3, 6.2, 5.3, 6.8, '#BFC7CF', 1)); p.append(box(3.15, 8.2, 3.95, 8.9, '#BFC7CF', 1))
    p.append(wc(5.9, 6.6)); p.append(box(6.8, 6.2, 7.8, 6.8, '#BFC7CF', 1)); p.append(box(5.65, 8.2, 6.45, 8.9, '#BFC7CF', 1))
    p.append(bed(20.0, 14.0, 22.0, 16.2, 'e')); p.append(box(17.2, 15.6, 17.8, 16.8, '#D9D4C7', 1))
    p.append(bed(20.0, 10.5, 22.0, 12.7, 'e')); p.append(box(17.2, 12.0, 17.8, 13.1, '#D9D4C7', 1))
    p.append(bed(20.0, 6.9, 22.0, 9.0, 'e')); p.append(box(17.2, 8.5, 17.8, 9.5, '#D9D4C7', 1))
    for (x, y) in ((15.0, 9.2), (15.9, 10.5), (14.5, 10.6)):
        p.append(circ(x, y, .25, '#6FA55A', '#3E6B2F', 1))
    # outer wall: typical floor 21.25 x 11 = 233.75
    p.append(f'<rect x="{X(BX0):.1f}" y="{Y(17):.1f}" width="{S*(BX1-BX0):.1f}" height="{S*11:.1f}" fill="none" stroke="{INK}" stroke-width="7"/>')
    p.append(win(9.0, 17, 16.4, 17)); p.append(win(18.0, 17, 23.5, 17)); p.append(win(24.25, 14.0, 24.25, 16.5)); p.append(win(24.25, 10.4, 24.25, 12.9)); p.append(win(24.25, 6.8, 24.25, 9.3))
    p.append(win(3, 10.0, 3, 12.0)); p.append(win(3, 7.0, 3, 7.8)); p.append(win(3, 6.6, 3, 6.9)); p.append(win(18.0, 6, 23.5, 6)); p.append(win(9.0, 6, 13.0, 6))
    p.append(door(8, 15.2, 0, 1, 1, 0, .9)); p.append(door(8, 10.3, 0, 1, 1, 0, .9)); p.append(door(8.4, 9.0, 0, 1, 1, 0, .001))
    p.append(door(17, 16.0, 0, -1, -1, 0, .9)); p.append(door(17, 12.6, 0, -1, -1, 0, .9)); p.append(door(17, 9.0, 0, -1, -1, 0, .9))
    p.append(door(4.0, 9.0, 1, 0, 0, -1, .8)); p.append(door(6.5, 9.0, 1, 0, 0, -1, .8))
    p.append(flush())
    p.append(frame('T', 'A-01 · TYPICAL ×3  +3.75 / +7.05 / +10.35 · 55% = 233.75 m²',
                   f'SHEET A-01 · PLOT 83 · {PLOT_AREA:.0f} m²'))
    p.append(dimh(BX0, BX1, int(Y(5.3)), '21.25m', 10.5)); p.append(dimv(6, 17, int(X(24.7)), '11.00m', 9))
    p.append(text(X(3.3), Y(3.0), 'TYPICAL  21.25 × 11.00', 10.5, '#7A1F1F', 800, 'start', family='Menlo, monospace')); p.append(text(X(3.3), Y(2.2), '= 233.75 m² (55.00 %)', 10.5, '#7A1F1F', 800, 'start', family='Menlo, monospace'))
    p.append(text(X(12.0), Y(4.55) + 0, '', 9))
    if passive:
        p.append(passive_overlay('T'))
    return ''.join(p)


def plan_roof(passive=False):
    p = [site('R', 'R'), trees()]
    # lower flat roof (typical roof slab) 233.75 outline
    p.append(rect(BX0, 6, BX1, 12, '#E6E3D8', sw=1.4, extra='stroke-dasharray="8 5"'))
    p.append(rect(BX0, 6, BX1, 12, 'url(#hat)', stroke='none', sw=0, extra='opacity=".5"'))
    p.append(text(X(10.0), Y(10.3), 'COOL / GREEN ROOF OF TYPICAL FLOOR', 10, '#4A463C', 800))
    p.append(text(X(10.0), Y(9.5), '127.50 m² catchment · AC-condensate + rain tank', 9.5, '#4A463C', 600))
    p.append(circ(5.2, 7.6, 0.9, '#9DC4D8', INK, 1.4)); p.append(text(X(5.2), Y(7.6) + 3, 'TANK', 8, INK, 800))
    p.append(rect(14, 8, 17, 11.5, KIND['void'], sw=1.8, extra='stroke-dasharray="5 3"'))
    p.append(text(X(15.5), Y(9.75) + 3, 'SHAFT ▲', 9.5, INK, 800))
    for i in range(6):
        p.append(box(18.0 + i * 1.0, 7.0, 18.8 + i * 1.0, 11.5, '#8FA9C4', .8))
    p.append(text(X(21.0), Y(6.55), 'SOLAR THERMAL ROW', 8.5, '#0B1522', 800))
    # roof level 25% = 106.25
    p.append(rect(BX0, 12, BX1, 17, KIND['roof'], sw=2.6))
    AREAS['roof'] = (BX1 - BX0) * 5
    p.append(core_plan('R').replace('LOBBY', 'OVERRUN'))
    p.append(rect(8, 12, 24.25, 17, '#EFEBE0', sw=2))
    for r in range(4):
        for c in range(7):
            x0 = 8.6 + c * 2.2
            y0 = 12.6 + r * 1.0
            p.append(f'<rect x="{X(x0):.1f}" y="{Y(y0+0.78):.1f}" width="{S*1.9:.1f}" height="{S*0.78:.1f}" fill="#2E4A6B" stroke="#A9C2DC" stroke-width="1"/>')
    p.append(text(X(12.5), Y(8.4), 'PV ARRAY above: 28 panels ≈ 41.5 m²', 10, '#0B1522', 800))
    p.append(text(X(12.5), Y(7.6), 'pergola-mounted · shades roof terrace', 9, '#0B1522', 600))
    p.append(f'<rect x="{X(BX0):.1f}" y="{Y(17):.1f}" width="{S*(BX1-BX0):.1f}" height="{S*5:.1f}" fill="none" stroke="{INK}" stroke-width="7"/>')
    p.append(door(8.0, 14.0, 0, 1, -1, 0, .9))
    p.append(flush())
    p.append(frame('R', 'A-01 · ROOF LEVEL  +13.65 m  ·  25% = 106.25 m²',
                   f'SHEET A-01 · PLOT 83 · {PLOT_AREA:.0f} m²'))
    p.append(dimh(BX0, BX1, int(Y(5.3)), '21.25m', 10.5)); p.append(dimv(12, 17, int(X(24.7)), '5.00m', 9))
    p.append(text(X(3.3), Y(3.0), 'ROOF LEVEL  21.25 × 5.00', 10.5, '#7A1F1F', 800, 'start', family='Menlo, monospace')); p.append(text(X(3.3), Y(2.2), '= 106.25 m² (25.00 %)', 10.5, '#7A1F1F', 800, 'start', family='Menlo, monospace'))
    if passive:
        p.append(passive_overlay('R'))
    return ''.join(p)


def svg_wrap(inner, cls='', w=CW, h=CH, idn=''):
    return f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" width="{w}" height="{h}" class="{cls}" {idn} font-family="Helvetica Neue, Arial, sans-serif">{defs()}{inner}</svg>'


def all_plans(passive=False):
    return {'B': svg_wrap(plan_basement(passive), 'plan'), 'G': svg_wrap(plan_ground(passive), 'plan'),
            'T': svg_wrap(plan_typical(passive), 'plan'), 'R': svg_wrap(plan_roof(passive), 'plan')}


# ------------------------------------------------------------------ section A-A
SX0, SSC = 70, 36           # x origin, px/m
Z0 = 700                    # z=0 at pixel row
SEC_W, SEC_H = 800, 840


def SX(y): return SX0 + SSC * (PH - y)
def SZ(z): return Z0 - SSC * z


def sec_rect(y_n, y_s, z0, z1, fill, stroke=INK, sw=1.4, extra=''):
    return f'<rect x="{SX(y_n):.1f}" y="{SZ(z1):.1f}" width="{SSC*(y_n-y_s):.1f}" height="{SSC*(z1-z0):.1f}" fill="{fill}" stroke="{stroke}" stroke-width="{sw}" {extra}/>'


def sec_text(y, z, t, fs=10, fill=INK, weight=700, anchor='middle', rot=0):
    return text(SX(y), SZ(z), t, fs, fill, weight, anchor, rot)


def section_svg():
    p = [defs(), f'<rect width="{SEC_W}" height="{SEC_H}" fill="{VEL}"/>']
    # ground / site
    p.append(f'<rect x="0" y="{SZ(0):.1f}" width="{SX(17)-0:.1f}" height="14" fill="#CFCCC3"/>')           # road
    p.append(text(36, SZ(0) + 11, 'N ROAD 15m', 9, '#4A463C', 800))
    p.append(f'<rect x="{SX(17):.1f}" y="{SZ(0):.1f}" width="{SSC*17:.1f}" height="{SSC*3.4:.1f}" fill="#D8D2BE"/>')       # soil
    p.append(f'<rect x="{SX(17):.1f}" y="{SZ(0):.1f}" width="{SSC*17:.1f}" height="{SSC*3.4:.1f}" fill="url(#hat)" opacity=".5"/>')
    p.append(f'<line x1="{SX(17)}" y1="{SZ(0)}" x2="{SX(0)}" y2="{SZ(0)}" stroke="#4B5C3B" stroke-width="2.4"/>')
    p.append(sec_text(1.2, 0.35, 'GARDEN ±0.00', 9.5, '#3E6B2F'))
    # basement shell
    p.append(sec_rect(17, 5, -3.2, 0.15, '#E1E2DE', sw=0))
    # stall + car profile (stall 3 at cut)
    p.append(sec_rect(17, 12, -3.2, -0.6, '#D9DAD5', sw=0))
    p.append(sec_rect(16.7, 12.3, -3.05, -2.3, '#7E8A97', stroke='#2F3944', sw=1.2, extra='rx="8"'))
    p.append(sec_rect(15.6, 13.4, -2.3, -1.7, '#C7D6E2', stroke='#2F3944', sw=1, extra='rx="6"'))
    p.append(sec_text(14.5, -1.3, 'STALL P3 (CAR)', 9, '#2F3944'))
    p.append(sec_text(9.0, -1.4, '6.0 m AISLE', 10, '#2F3944'))
    p.append(sec_text(9.0, -1.95, '(no columns in lane)', 9, '#2F3944', 600))
    # slabs (poche)
    def slab(yn, ys, z, t=0.3, fill=INK):
        return sec_rect(yn, ys, z - t, z, fill, sw=0)
    p.append(slab(17, 5, -3.2 + 0.3, 0.3))                         # basement slab on grade
    p.append(sec_rect(17, 5, -3.5, -3.2, INK, sw=0))
    p.append(slab(17, 7, 0.45))                                    # ground slab
    for z in (3.75, 7.05, 10.35):
        p.append(slab(17, 6, z))
    p.append(slab(17, 6, 13.65))                                   # roof of typical floors
    p.append(sec_rect(17, 12, 16.35, 16.65, INK, sw=0))            # roof-level slab
    # walls: north wall y 17 and south wall; courtyard void walls
    p.append(sec_rect(17.0, 16.78, -3.5, 16.65, INK, sw=0))
    p.append(sec_rect(5.22, 5.0, -3.5, 0.15, INK, sw=0))           # basement south wall
    p.append(sec_rect(7.22, 7.0, 0.15, 3.45, INK, sw=0))           # ground south wall (with openings below)
    for z0 in (3.75, 7.05, 10.35):
        p.append(sec_rect(6.22, 6.0, z0, z0 + 3.0, INK, sw=0))
    # window openings (cut out walls): north reception at each floor, south loggia
    for z in (0.45, 3.75, 7.05, 10.35):
        p.append(sec_rect(17.0, 16.78, z + 0.9, z + 2.4, VEL, sw=0))
        p.append(sec_rect(17.0, 16.78, z + 0.9, z + 2.4, '#CFE6F2', stroke='#3C8DB8', sw=1.2))
    p.append(sec_rect(7.22, 7.0, 0.45 + 0.1, 0.45 + 2.5, VEL, sw=0)); p.append(sec_rect(7.22, 7.0, 0.55, 2.95, '#CFE6F2', stroke='#3C8DB8', sw=1.2))
    for z in (3.75, 7.05, 10.35):
        p.append(sec_rect(6.22, 6.0, z + 0.1, z + 2.7, VEL, sw=0)); p.append(sec_rect(6.22, 6.0, z + 0.1, z + 2.7, '#CFE6F2', stroke='#3C8DB8', sw=1.2))
    # brise-soleil 0.9 m at each typical floor head + ground overhang (1.0 m = typical slab over y6..7)
    for z in (3.75 + 3.0, 7.05 + 3.0):
        p.append(sec_rect(6.0, 5.1, z - 0.0, z + 0.12, '#8A6B2F', sw=0))
    p.append(sec_rect(6.0, 5.1, 3.75 - 0.0 + 0.0 - 0.0, 3.75 + 0.0, 'none', sw=0))
    p.append(sec_rect(6.0, 5.1, 13.65 - 0.12, 13.65, '#8A6B2F', sw=0))
    p.append(sec_rect(6.0, 5.1, 3.75 - 0.12 + 0.0, 3.75, 'none', sw=0))
    # level markers
    lv = [(-3.2, 'BASEMENT −3.20'), (0.45, 'GROUND +0.45'), (3.75, 'TYPICAL 1  +3.75'), (7.05, 'TYPICAL 2  +7.05'), (10.35, 'TYPICAL 3  +10.35'), (13.65, 'ROOF +13.65'), (16.65, 'PARAPET +16.65')]
    for z, t in lv:
        p.append(f'<line x1="{SX(17)-38:.1f}" y1="{SZ(z):.1f}" x2="{SX(17)+10:.1f}" y2="{SZ(z):.1f}" stroke="#7A1F1F" stroke-width="1"/>')
        p.append(f'<path d="M {SX(17)-14:.1f} {SZ(z)-6:.1f} L {SX(17)-8:.1f} {SZ(z):.1f} L {SX(17)-14:.1f} {SZ(z)+6:.1f}" fill="none" stroke="#7A1F1F" stroke-width="1"/>')
    p.append(f'<g font-family="Menlo, monospace" font-size="8.5" font-weight="700" fill="#7A1F1F">'
             + ''.join(f'<text x="2" y="{SZ(z)-3:.1f}">{esc(t.split("  ")[-1] if "TYPICAL" in t else t.split(" ")[-1])}</text>' for z, t in lv) + '</g>')
    # room labels at cut
    for z, nm in ((0.45, 'MAJLIS'), (3.75, 'RECEPTION'), (7.05, 'RECEPTION'), (10.35, 'RECEPTION')):
        p.append(sec_text(14.25, z + 1.7, nm, 10.5, '#4A463C', 700))
    # courtyard shaft (void) y 8..11.5 from z .45 up to open sky
    p.append(sec_rect(11.5, 8.0, 0.45, 16.9, '#D5E8F2', stroke='none', sw=0, extra='opacity=".75"'))
    p.append(f'<line x1="{SX(11.5):.1f}" y1="{SZ(0.45):.1f}" x2="{SX(11.5):.1f}" y2="{SZ(16.9):.1f}" stroke="{INK}" stroke-width="2" stroke-dasharray="7 4"/>')
    p.append(f'<line x1="{SX(8.0):.1f}" y1="{SZ(0.45):.1f}" x2="{SX(8.0):.1f}" y2="{SZ(16.9):.1f}" stroke="{INK}" stroke-width="2" stroke-dasharray="7 4"/>')
    p.append(sec_text(9.75, 12.0, 'COURTYARD', 10, '#1F5B7A', 800, rot=-90))
    p.append(sec_text(9.75, 5.5, 'VENT SHAFT', 10, '#1F5B7A', 800, rot=-90))
    p.append(sec_text(7.0, 0.35, '', 9))
    # loggia/balcony labels
    p.append(sec_text(6.6, 1.65, 'LOGGIA', 8.5, '#4A463C', 800, rot=-90))
    p.append(sec_text(7.0, 5.0, 'BALCONY', 8.5, '#4A463C', 800, rot=-90))
    # roof-level pavilion + PV
    p.append(sec_rect(17, 12, 13.65, 16.35, '#ECE9DF', stroke='none', sw=0))
    p.append(sec_text(14.5, 14.2, 'ROOF TERRACE', 10, '#4A463C', 700)); p.append(sec_text(14.5, 13.9, '', 8))
    p.append(f'<polygon points="{SX(16.5):.1f},{SZ(15.6):.1f} {SX(12.5):.1f},{SZ(16.6):.1f} {SX(12.5):.1f},{SZ(16.45):.1f} {SX(16.5):.1f},{SZ(15.45):.1f}" fill="#2E4A6B" stroke="#A9C2DC"/>')
    p.append(sec_text(14.5, 17.25, 'PV @ 30°  (pergola)', 9.5, '#2E4A6B', 800))
    p.append(sec_rect(6.0, 5.0, 13.65, 13.95, '#B9C7A8', stroke='none', sw=0))
    p.append(sec_rect(12.0, 6.0, 13.65, 13.95, '#B9C7A8', stroke='none', sw=0))
    p.append(sec_text(9.0, 14.25, 'GREEN / COOL ROOF + RAIN TANK', 9, '#3E6B2F', 800))
    # pool + buffer + south wall of basement
    p.append(sec_rect(5.0, 3.5, -3.2, 0.0, '#C9B98F', stroke='#8A6B2F', sw=1.4, extra='opacity=".7"'))
    p.append(sec_rect(5.0, 3.5, -3.2, 0.0, 'url(#hat2)', stroke='none', sw=0))
    p.append(sec_text(4.25, -0.9, '1.5m', 9, '#5E4A1A', 800, rot=-90)); p.append(sec_text(4.25, -2.1, 'INSULATED', 8, '#5E4A1A', 800, rot=-90))
    p.append(sec_rect(3.5, 0.5, -1.6, 0.0, '#86C8DC', stroke='#1F6E8C', sw=2))
    p.append(sec_rect(3.62, 0.38, -1.75, -1.6, INK, sw=0))
    p.append(sec_rect(3.62, 3.5, -1.75, 0.05, INK, sw=0)); p.append(sec_rect(0.5, 0.38, -1.75, 0.05, INK, sw=0))
    p.append(sec_text(2.0, -0.7, 'POOL 3.0 m × 1.5 deep', 9.5, '#0D3C52', 800))
    p.append(sec_text(2.0, -1.2, '(independent structure)', 8.5, '#0D3C52', 700))
    p.append(f'<line x1="{SX(5.0)-1:.1f}" y1="{SZ(-3.5):.1f}" x2="{SX(3.5)+1:.1f}" y2="{SZ(-3.5):.1f}" stroke="{INK}" stroke-width="1"/>')
    # south garden planting
    p.append(f'<circle cx="{SX(1.2):.1f}" cy="{SZ(1.6):.1f}" r="22" fill="#8DB872" stroke="#3E6B2F"/><rect x="{SX(1.2)-2:.1f}" y="{SZ(0.9):.1f}" width="4" height="{SSC*0.9:.1f}" fill="#6B4E2A"/>')
    # --- solar rays (south on the right) ---
    sun = {'summer': ('#E8710A', 83.44), 'equinox': ('#C9A100', 60.0), 'winter': ('#2B7BB9', 36.56)}
    shade_notes = []

    def ray(season, y_wall, z_t, z_soffit, depth):
        col, alt = sun[season]
        ta = math.tan(math.radians(alt))
        d_hit = (z_soffit - z_t) / ta
        blocked = d_hit < depth
        L = 9.0
        y_start = y_wall - L * math.cos(math.radians(alt))
        z_start = z_t + L * math.sin(math.radians(alt))
        if blocked:
            ye, ze = y_wall - d_hit, z_soffit
        else:
            ye, ze = y_wall, z_t
        dash = '' if not blocked else ' stroke-dasharray="7 4"'
        out = (f'<line x1="{SX(y_start):.1f}" y1="{SZ(z_start):.1f}" x2="{SX(ye):.1f}" y2="{SZ(ze):.1f}" stroke="{col}" stroke-width="2.4"{dash}/>')
        out += f'<circle cx="{SX(ye):.1f}" cy="{SZ(ze):.1f}" r="3.6" fill="{col}"/>'
        if blocked:
            out += (f'<path d="M {SX(ye)-5:.1f} {SZ(ze)-5:.1f} L {SX(ye)+5:.1f} {SZ(ze)+5:.1f} M {SX(ye)+5:.1f} {SZ(ze)-5:.1f} L {SX(ye)-5:.1f} {SZ(ze)+5:.1f}" stroke="#B03A2E" stroke-width="2"/>')
        return out, blocked

    # target: Typical 1 south window (z=3.75+1.5) shaded by soffit of T2 brise-soleil (z=7.05-... head 6.75, depth 0.9 beyond wall y=6)
    for season in ('summer', 'equinox', 'winter'):
        o, b = ray(season, 6.0, 5.1, 6.75, 0.9)
        p.append(o)
        shade_notes.append((season, b))
    # ground floor window shaded by 1.0 m overhang (typical slab, soffit 3.45)
    for season in ('summer', 'winter'):
        o, b = ray(season, 7.0, 1.9, 3.45, 1.0)
        p.append(o)
    # sun angle labels
    ax, az = SX(-4.6), SZ(14.6)
    p.append(f'<g font-family="Menlo, monospace" font-size="10" font-weight="800">'
             f'<text x="{SX(0.5)+8:.1f}" y="{SZ(14.9):.1f}" fill="#E8710A">SUMMER NOON 83.4°</text>'
             f'<text x="{SX(0.5)+8:.1f}" y="{SZ(14.9)+13:.1f}" fill="#C9A100">EQUINOX 60.0°</text>'
             f'<text x="{SX(0.5)+8:.1f}" y="{SZ(14.9)+26:.1f}" fill="#2B7BB9">WINTER NOON 36.6°</text>'
             f'<text x="{SX(0.5)+8:.1f}" y="{SZ(14.9)+42:.1f}" fill="#4A463C">LAT 30° N · CAIRO</text></g>')
    # --- airflow (north wind, animated) ---
    wc_ = '#1E78C8'
    for z in (0.45, 3.75, 7.05, 10.35):
        zc = z + 1.65
        d = (f'M 16 {SZ(zc):.1f} L {SX(17)-2:.1f} {SZ(zc):.1f} L {SX(14.0):.1f} {SZ(zc):.1f} '
             f'C {SX(11.5):.1f} {SZ(zc):.1f} {SX(10.5):.1f} {SZ(zc+0.2):.1f} {SX(9.75):.1f} {SZ(zc+1.2):.1f}')
        p.append(f'<path class="flow" d="{d}" fill="none" stroke="{wc_}" stroke-width="3.2" stroke-dasharray="11 7" marker-end="url(#arr)"/>')
        d2 = f'M {SX(9.75):.1f} {SZ(zc+0.2):.1f} C {SX(8.6):.1f} {SZ(zc):.1f} {SX(7.6):.1f} {SZ(zc):.1f} {SX(5.4):.1f} {SZ(zc):.1f}'
        if z > 0.45:
            p.append(f'<path class="flow" d="{d2}" fill="none" stroke="{wc_}" stroke-width="2.4" stroke-dasharray="9 6" marker-end="url(#arr)" opacity=".85"/>')
    p.append(f'<path class="flow up" d="M {SX(9.75):.1f} {SZ(1.0):.1f} L {SX(9.75):.1f} {SZ(17.9):.1f}" fill="none" stroke="#C0392B" stroke-width="3.4" stroke-dasharray="10 7" marker-end="url(#arr)"/>')
    p.append(text(SX(9.75) + 14, SZ(18.15), 'STACK EXHAUST ↑', 10, '#C0392B', 800, family='Menlo, monospace'))
    p.append(text(18, SZ(0.45 + 1.65) - 10, 'N WIND', 9.5, wc_, 800))
    # pool cooling → basement light-well
    p.append(f'<path class="flow" d="M {SX(0.0):.1f} {SZ(0.7):.1f} C {SX(2.5):.1f} {SZ(0.9):.1f} {SX(3.4):.1f} {SZ(1.5):.1f} {SX(4.2):.1f} {SZ(0.1):.1f}" fill="none" stroke="#2E9CCA" stroke-width="2.2" stroke-dasharray="6 5" marker-end="url(#arr)"/>')
    p.append(text(SX(0.4), SZ(1.5), 'pool-cooled air', 8.5, '#1F6E8C', 800))
    # N / S markers
    p.append(text(SX(17) + 4, SZ(18.4), 'NORTH ▶ road side', 11, INK, 800, 'start'))
    p.append(text(SX(0) - 4, SZ(18.4), 'SOUTH ▶ garden / pool', 11, INK, 800, 'end'))
    # dims
    p.append(dimh_sec(17, 0, SZ(-3.9) + 6, '17.00m (N–S)'))
    p.append(dimh_sec(17, 6.0, SZ(-3.9) - 8, ''))
    return ''.join(p), shade_notes


def dimh_sec(y_a, y_b, ypx, t):
    a, b = SX(y_a), SX(y_b)
    c = '#7A1F1F'
    return (f'<line x1="{a:.1f}" y1="{ypx:.1f}" x2="{b:.1f}" y2="{ypx:.1f}" stroke="{c}"/>'
            f'<line x1="{a:.1f}" y1="{ypx-4:.1f}" x2="{a:.1f}" y2="{ypx+4:.1f}" stroke="{c}"/><line x1="{b:.1f}" y1="{ypx-4:.1f}" x2="{b:.1f}" y2="{ypx+4:.1f}" stroke="{c}"/>'
            + (text((a + b) / 2, ypx + 14, t, 10.5, c, 800, family='Menlo, monospace') if t else ''))


# ------------------------------------------------------------------ core options (Option A wrap vs B adjacent)
CS = 44   # px per m for core diagrams


def _cr(ox, oy):
    def R(x, y, w, h, fill='#F7F2E4', sw=1.4, extra=''):
        return f'<rect x="{ox+x*CS:.1f}" y="{oy+y*CS:.1f}" width="{w*CS:.1f}" height="{h*CS:.1f}" fill="{fill}" stroke="{INK}" stroke-width="{sw}" {extra}/>'

    def L(x0, y0, x1, y1):
        return f'<line x1="{ox+x0*CS:.1f}" y1="{oy+y0*CS:.1f}" x2="{ox+x1*CS:.1f}" y2="{oy+y1*CS:.1f}" stroke="#4B5560" stroke-width="0.9"/>'

    def T(x, y, t, fs=10):
        return f'<text x="{ox+x*CS:.1f}" y="{oy+y*CS+3:.1f}" font-size="{fs}" font-weight="800" text-anchor="middle" fill="{INK}">{esc(t)}</text>'
    return R, L, T


def core_options():
    W_, H_ = 380, 250
    wrap = lambda body: (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W_} {H_}" width="{W_}" height="{H_}" '
                         f'font-family="Helvetica Neue, Arial, sans-serif">{body}</svg>')
    # Option A: 4.4 x 4.4, west/east flights + north flight around 2.0 x 2.0 lift
    R, L, T = _cr(80, 14)
    a = [R(0, 0, 4.4, 4.4, '#D8D0BC', 3.4), R(0, 0, 1.2, 4.4), R(3.2, 0, 1.2, 4.4), R(1.2, 0, 2.0, 1.2)]
    for i in range(1, 7):
        yy = 1.2 + 3.2 * i / 7
        a += [L(0, yy, 1.2, yy), L(3.2, yy, 4.4, yy)]
    for i in range(1, 5):
        xx = 1.2 + 2.0 * i / 5
        a.append(L(xx, 0, xx, 1.2))
    a += [R(0, 0, 1.2, 1.2, '#E4D9BD'), R(3.2, 0, 1.2, 1.2, '#E4D9BD'),
          R(1.2, 1.2, 2.0, 2.0, '#EDEDED', 2.6), L(1.2, 1.2, 3.2, 3.2), L(1.2, 3.2, 3.2, 1.2), T(2.2, 2.2, 'LIFT', 11),
          R(1.2, 3.2, 2.0, 1.2, '#EFE4CC', 1.0, 'stroke-dasharray="4 3"'), T(2.2, 3.85, 'LIFT LOBBY', 9),
          T(0.6, 2.7, '↑ 1', 9), T(3.8, 2.7, '↓ 3', 9), T(2.2, 0.7, '2 →', 9)]
    a.append(f'<text x="{80+2.2*CS:.1f}" y="{H_-8}" font-size="11" text-anchor="middle" font-weight="800" fill="#7A1F1F" font-family="Menlo, monospace">4.40 × 4.40 = {4.4*4.4:.2f} m²</text>')
    # Option B: stair 2.7 x 3.9 (dogleg) + lift 2.0 x 2.0 + lobby
    R, L, T = _cr(70, 14)
    b = [R(0, 0, 4.7, 3.9, '#D8D0BC', 3.4), R(0, 0, 2.7, 1.2, '#E4D9BD'), R(0, 1.2, 1.3, 2.7), R(1.4, 1.2, 1.3, 2.7)]
    for i in range(1, 9):
        yy = 1.2 + 2.7 * i / 9
        b += [L(0, yy, 1.3, yy), L(1.4, yy, 2.7, yy)]
    b += [T(1.35, 0.65, 'LANDING', 8.5), T(0.65, 2.6, '↑ UP', 9), T(2.05, 2.6, '↓ DN', 9),
          R(2.7, 0, 2.0, 2.0, '#EDEDED', 2.6), L(2.7, 0, 4.7, 2.0), L(2.7, 2.0, 4.7, 0), T(3.7, 1.0, 'LIFT', 11),
          R(2.7, 2.0, 2.0, 1.9, '#EFE4CC', 1.0, 'stroke-dasharray="4 3"'), T(3.7, 3.0, 'LIFT LOBBY', 9)]
    b.append(f'<text x="{70+2.35*CS:.1f}" y="{H_-8}" font-size="11" text-anchor="middle" font-weight="800" fill="#7A1F1F" font-family="Menlo, monospace">4.70 × 3.90 = {4.7*3.9:.2f} m²</text>')
    sc = {'A': {'struct': 9, 'space': 7, 'pass': 6, 'cost': 7}, 'B': {'struct': 7, 'space': 9, 'pass': 8, 'cost': 9}}
    w = {'struct': .40, 'space': .30, 'pass': .15, 'cost': .15}
    tot = {k: sum(sc[k][c] * w[c] for c in w) for k in sc}
    return wrap(''.join(a)), wrap(''.join(b)), sc, w, tot


# ------------------------------------------------------------------ schedules
def area_tables():
    basement = 21.25 * 12 + 7.5 * 4 + (24.25 - 19.5) * 4     # main + west drive wing + family wing below y=5
    ramp = 3.0 * 16
    ground = 21.25 * 10
    typical = 21.25 * 11
    roof = 21.25 * 5
    return dict(basement=basement, ramp=ramp, ground=ground, typical=typical, roof=roof,
                above=ground + 3 * typical + roof, total=basement + ground + 3 * typical + roof)


def schedule_html():
    a = area_tables()
    rows = [
        ('Basement', '−3.20', f'{a["basement"]:.2f}', f'{a["basement"]/PLOT_AREA*100:.1f}%', 'not capped', 'garage 6 cars + amenities'),
        ('Ground', '+0.45', f'{a["ground"]:.2f}', f'{a["ground"]/PLOT_AREA*100:.2f}%', '50% = 212.50', 'PASS'),
        ('Typical ×3 (each)', '+3.75 / +7.05 / +10.35', f'{a["typical"]:.2f}', f'{a["typical"]/PLOT_AREA*100:.2f}%', '55% = 233.75', 'PASS'),
        ('Typical ×3 (total)', '', f'{3*a["typical"]:.2f}', '', '', ''),
        ('Roof level', '+13.65', f'{a["roof"]:.2f}', f'{a["roof"]/PLOT_AREA*100:.2f}%', '25% = 106.25', 'PASS'),
        ('Above-ground GFA', '', f'{a["above"]:.2f}', '', '', '1 apartment per floor'),
        ('Total GFA incl. basement', '', f'{a["total"]:.2f}', '', '', ''),
    ]
    t1 = ''.join(f'<tr><td>{esc(r[0])}</td><td>{esc(r[1])}</td><td class="n">{r[2]}</td><td class="n">{r[3]}</td><td>{esc(r[4])}</td><td class="{"ok" if r[5]=="PASS" else ""}">{esc(r[5])}</td></tr>' for r in rows)
    chk = [
        ('Plot 17 × 25 m', f'{PLOT_AREA:.2f} m² · diagonal {DIAG:.2f} m', 'PASS'),
        ('West setback 3.0 m', 'building x ≥ 3.00 on all levels above ground; ramp sits in the strip', 'PASS'),
        ('South setback 4.0 m', 'ground y ≥ 7.00, typical y ≥ 6.00; pool 3.0 × 6.0 m inside strip', 'PASS'),
        ('Pool buffer 1.5 m', 'pool to basement wall: 1.50 N / W / E; pool structure independent', 'PASS'),
        ('Basement south wings', 'drive wing + family wing reach y = 1.0, under the 4.0 m strip (underground only)', 'CODE CHECK'),
        ('Ramp 20% max', 'drop 3.20 m over 16.0 m in west strip (N road → −3.20)', 'PASS (limit)'),
        ('6 cars + swept path', 'stalls 2.6 × 5.0 m, aisle 6.0 m, R 3.2 / 5.8 m, 0 columns in lanes', 'PASS'),
        ('Reception north / bedrooms east / kitchen+baths west', 'all 3 bedrooms on east façade; kitchen and 2 baths on west façade', 'PASS'),
        ('Daylight + cross-ventilation', 'every habitable room has an external wall; N → courtyard → S loggia path', 'PASS'),
    ]
    t2 = ''.join(f'<tr><td>{esc(r[0])}</td><td>{esc(r[1])}</td><td class="{"ok" if r[2].startswith("PASS") else "warn"}">{esc(r[2])}</td></tr>' for r in chk)
    roof_pv = 28 * 1.9 * 0.78
    catch = a['typical']
    zw = [
        ('Cut-and-fill', f'gross excavation ≈ {a["basement"]*3.5:.0f} m³ (est.); buffer backfill + garden regrading reuse on site; rest to licensed recycling'),
        ('Rain + condensate', f'catchment {catch:.2f} m²; Cairo ≈ 25 mm/yr gives only ≈ {catch*0.025*0.85:.1f} m³/yr, so AC condensate + greywater are the main sources'),
        ('Greywater', 'baths + laundry → garden / pool top-up tank in basement'),
        ('Waste hub', 'ground hub 5.0 m²: 4-stream sorting, compost for garden; kitchen sorting drawers on each floor'),
        ('Solar PV', f'28 panels = {roof_pv:.1f} m² on roof pergola; also shades terrace'),
        ('Materials', 'local limestone + hollow-block infill, recycled-aggregate concrete, lime plaster; 21.25 m modular grid, no cut-offs'),
    ]
    t3 = ''.join(f'<tr><td>{esc(r[0])}</td><td>{esc(r[1])}</td></tr>' for r in zw)
    return t1, t2, t3, a


# ------------------------------------------------------------------ boards
CSS_COMMON = '''
*{box-sizing:border-box;margin:0;padding:0}
html,body{width:1600px;height:1200px;overflow:hidden;background:#F6F4EE;font-family:"Helvetica Neue",Arial,sans-serif;color:#1B1F24}
.flow{animation:dash 1.4s linear infinite}
@keyframes dash{to{stroke-dashoffset:-34}}
'''


def board1():
    pl = all_plans()
    # remove swept overlay from non-basement plans (only basement has it) – plan_* already scoped
    cells = [pl['B'], pl['G'], pl['T'], pl['R']]
    grid = ''.join(f'<div class="c">{c}</div>' for c in cells)
    return f'''<!DOCTYPE html><html lang="en"><head><meta charset="utf-8"><title>Sheet A-01 — Master Architectural Floor Plans & Swept-Path Blueprint · Plot 83 New Cairo</title>
<style>{CSS_COMMON}
.g{{position:absolute;left:0;top:0;width:1600px;height:1200px;display:grid;grid-template-columns:800px 800px;grid-template-rows:600px 600px;border:0}}
.c{{width:800px;height:600px;overflow:hidden;position:relative;outline:1px solid #1B1F24;outline-offset:-1px}}
.c svg{{display:block;width:800px;height:600px}}
</style></head><body><div class="g">{grid}</div></body></html>'''


def board2():
    sec, shade = section_svg()
    svga, svgb, sc, w, tot = core_options()
    t1, t2, t3, a = schedule_html()
    section = f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {SEC_W} {SEC_H}" width="{SEC_W}" height="{SEC_H}" font-family="Helvetica Neue, Arial, sans-serif">{sec}</svg>'
    names = {'struct': 'Structural (40%)', 'space': 'Spatial (30%)', 'pass': 'Daylight / passive (15%)', 'cost': 'Cost / buildability (15%)'}
    srows = ''.join(f'<tr><td>{names[c]}</td><td class="n">{sc["A"][c]}</td><td class="n">{sc["B"][c]}</td></tr>' for c in names)
    winter_note = 'winter sun reaches the typical-floor glazing' if not dict(shade)['winter'] else 'winter sun blocked'
    summer_note = 'summer noon sun is stopped by the 0.9 m brise-soleil' if dict(shade)['summer'] else 'summer sun reaches glazing'
    return f'''<!DOCTYPE html><html lang="en"><head><meta charset="utf-8"><title>Sheet A-02 — Passive Design Analysis, Core Alternative Study & Zero-Waste Matrix · Plot 83 New Cairo</title>
<style>{CSS_COMMON}
.hd{{position:absolute;left:0;top:0;width:1600px;height:66px;background:#1B1F24;color:#F6F4EE;display:flex;align-items:center;padding:0 22px;gap:24px}}
.hd h1{{font-size:21px;font-weight:800;letter-spacing:.2px}}
.hd span{{font:600 12px Menlo,monospace;color:#D9C58B;margin-left:auto}}
.sec{{position:absolute;left:10px;top:72px;width:800px;height:840px}}
.leg{{position:absolute;left:10px;top:918px;width:800px;height:274px;border:1.5px solid #1B1F24;padding:10px 14px;font-size:12.5px;line-height:1.5;background:#FBFAF5}}
.leg h3{{font-size:13px;margin-bottom:4px;text-transform:uppercase;letter-spacing:.5px}}
.leg table{{width:100%;border-collapse:collapse;font-size:12px;margin:4px 0}}
.leg td,.leg th{{border:1px solid #B9B2A0;padding:2px 6px;text-align:left}}
.leg th{{background:#EAE5D6}}
.k{{display:inline-block;width:22px;height:0;border-top:3px solid;vertical-align:middle;margin-right:6px}}
.core{{position:absolute;left:820px;top:72px;width:770px;height:384px}}
.core .o{{position:absolute;top:0;width:380px;height:384px;border:1.5px solid #1B1F24;background:#FBFAF5}}
.core .o h2{{font-size:14px;padding:6px 10px;background:#EAE5D6;border-bottom:1.5px solid #1B1F24}}
.core .o p{{font-size:11.5px;line-height:1.38;padding:4px 10px}}
.sch{{position:absolute;left:820px;top:464px;width:770px;height:730px;border:1.5px solid #1B1F24;background:#FBFAF5;padding:8px 12px;overflow:hidden}}
.sch h2{{font-size:14px;margin:2px 0 4px;text-transform:uppercase;letter-spacing:.4px}}
table.t{{width:100%;border-collapse:collapse;font-size:11px;margin-bottom:6px}}
table.t td,table.t th{{border:1px solid #B9B2A0;padding:1.5px 6px;text-align:left;vertical-align:top}}
table.t th{{background:#EAE5D6;font-size:11px}}
.n{{text-align:right!important;font-family:Menlo,monospace}}
.ok{{color:#1E7A3B;font-weight:800}} .warn{{color:#B03A2E;font-weight:800}}
</style></head><body>
<div class="hd"><h1>SHEET A-02 · PASSIVE DESIGN ANALYSIS · CORE ALTERNATIVE STUDY · ZERO-WASTE MATRIX</h1><span>PLOT 83 · NEW CAIRO · {PW:.0f} × {PH:.0f} m = {PLOT_AREA:.2f} m² · LAT 30° N</span></div>
<div class="sec">{section}</div>
<div class="leg"><h3>Section A-A (N road → reception → courtyard shaft → loggia → pool buffer → pool) · sun &amp; wind</h3>
<div><span class="k" style="border-color:#1E78C8"></span>Prevailing north wind: enters every reception, crosses the courtyard, leaves through south balcony / loggia.
<span class="k" style="border-color:#C0392B;margin-left:12px"></span>Courtyard stack exhausts hot air at roof.</div>
<table><tr><th>Solar angle (noon, 30° N)</th><th>Altitude</th><th>Result on south glazing (0.9 m brise-soleil / 1.0 m slab overhang)</th></tr>
<tr><td style="color:#E8710A;font-weight:800">Summer solstice</td><td class="n">83.44°</td><td>shadow 0.9 × tan 83.44° = 8.0 m ≫ glazing height: fully shaded</td></tr>
<tr><td style="color:#C9A100;font-weight:800">Equinox</td><td class="n">60.00°</td><td>0.9 × tan 60° = 1.56 m: upper glazing shaded</td></tr>
<tr><td style="color:#2B7BB9;font-weight:800">Winter solstice</td><td class="n">36.56°</td><td>0.9 × tan 36.56° = 0.67 m: low sun enters, passive heat gain</td></tr></table>
<div>Dashed ray ✕ = stopped by overhang · solid ray = reaches glass. Check: {esc(summer_note)}; {esc(winter_note)}.</div></div>
<div class="core">
<div class="o" style="left:0"><h2>CORE OPTION A — stair wraps the lift</h2>{svga}
<p>Closed RC box (4 continuous walls) around a 2.0 × 2.0 shaft; three flights, one lobby. Strong torsion core, but 19.36 m² and the stair cannot take a façade window.</p></div>
<div class="o" style="left:390px"><h2>CORE OPTION B — lift beside the stair  ✔ drawn on plans</h2>{svgb}
<p>Dogleg stair 2.7 × 3.9 m plus lift 2.0 × 2.0 m: 18.33 m² (−1.03 m²/level, −5.2 m² over 5 levels). Stair sits on the north-west façade → daylight and smoke vent. Needs two shear-wall groups.</p></div></div>
<div class="sch">
<h2>Core scoring (preliminary, for structural engineer to confirm) — A {tot["A"]:.2f} · B {tot["B"]:.2f}  → Option B</h2>
<table class="t" style="width:48%;float:left;margin-right:2%"><tr><th>Criterion (weight)</th><th>A</th><th>B</th></tr>{srows}<tr><th>Weighted total</th><th class="n">{tot["A"]:.2f}</th><th class="n">{tot["B"]:.2f}</th></tr></table>
<table class="t" style="width:50%"><tr><th>Level</th><th>Elev.</th><th>GFA m²</th><th>% plot</th><th>Brief</th><th></th></tr>{t1}</table>
<h2 style="clear:both">Compliance schedule</h2><table class="t"><tr><th>Requirement</th><th>Provision</th><th>Status</th></tr>{t2}</table>
<h2>Zero-waste measures</h2><table class="t"><tr><th>Measure</th><th>Design response</th></tr>{t3}</table></div>
</body></html>'''


# ------------------------------------------------------------------ index
def index_html():
    pl = all_plans(passive=True)
    svga, svgb, sc, w, tot = core_options()
    t1, t2, t3, a = schedule_html()
    names = {'B': 'Basement −3.20', 'G': 'Ground +0.45', 'T': 'Typical +3.75', 'R': 'Roof +13.65'}
    tabs = ''.join(f'<button class="tab{" on" if k=="B" else ""}" data-k="{k}">{names[k]}</button>' for k in 'BGTR')
    plans = ''.join(f'<div class="pv{" on" if k=="B" else ""}" id="pv{k}">{pl[k]}</div>' for k in 'BGTR')
    sec, _ = section_svg()
    section = f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {SEC_W} {SEC_H}" style="width:100%;max-width:760px" font-family="Helvetica Neue, Arial, sans-serif">{sec}</svg>'
    boards = ''.join(f'<a class="bd" href="{f}" target="_blank"><div class="fr"><iframe src="{f}" scrolling="no" loading="lazy"></iframe></div><span>{t}</span></a>' for f, t in (
        ('board1-claude.html', 'A-01 Claude · Master plans & swept path'), ('board2-claude.html', 'A-02 Claude · Passive + core study + matrix'),
        ('board1-codex.html', 'A-01 Codex'), ('board2-codex.html', 'A-02 Codex')))
    dls = ''.join(f'<a class="dl" href="exports/{f}" download>⬇ {f}<small>{d}</small></a>' for f, d in (
        ('Plot83_NewCairo_CAD_Package.zip', 'DXF + PDF + sources'), ('Plot83_NewCairo_B_G_3_R_Master.dxf', 'AutoCAD DXF · B / G / 3×T / R'), ('Plot83_NewCairo_Engineering_Set.pdf', 'Engineering drawing set')))
    return f'''<!DOCTYPE html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Plot 83 New Cairo — CAD &amp; Passive Design Explorer</title>
<style>
*{{box-sizing:border-box;margin:0;padding:0}}
body{{font-family:"Helvetica Neue",Arial,sans-serif;background:#F6F4EE;color:#1B1F24}}
header{{background:#1B1F24;color:#F6F4EE;padding:14px 28px;display:flex;align-items:baseline;gap:18px;flex-wrap:wrap}}
header h1{{font-size:20px}} header span{{font:600 12px Menlo,monospace;color:#D9C58B}}
nav{{display:flex;gap:6px;padding:10px 28px;border-bottom:1.5px solid #1B1F24;background:#EAE5D6;flex-wrap:wrap}}
nav button,.tab{{font:700 13px inherit;padding:7px 14px;border:1.5px solid #1B1F24;background:#FBFAF5;cursor:pointer}}
nav button.on,.tab.on{{background:#1B1F24;color:#F6F4EE}}
main{{padding:16px 28px 40px;max-width:1500px;margin:auto}}
.sec{{display:none}} .sec.on{{display:block}}
.bar{{display:flex;gap:18px;align-items:center;margin:8px 0 12px;flex-wrap:wrap;font-size:13px}}
.bar label{{display:flex;gap:6px;align-items:center;font-weight:700;cursor:pointer}}
.pv{{display:none;border:1.5px solid #1B1F24;background:#fff}} .pv.on{{display:block}}
.pv svg{{width:100%;height:auto;display:block}}
.noswept .swept,.nopass .passive{{display:none}}
.flow{{animation:dash 1.4s linear infinite}} @keyframes dash{{to{{stroke-dashoffset:-34}}}}
.grid2{{display:grid;grid-template-columns:repeat(auto-fit,minmax(360px,1fr));gap:16px}}
.card{{border:1.5px solid #1B1F24;background:#FBFAF5;padding:10px}} .card h3{{font-size:14px;margin-bottom:6px}} .card svg{{width:100%;height:auto}}
table.t{{width:100%;border-collapse:collapse;font-size:12.5px;margin:8px 0}} table.t td,table.t th{{border:1px solid #B9B2A0;padding:3px 7px;text-align:left}} table.t th{{background:#EAE5D6}}
.n{{text-align:right!important;font-family:Menlo,monospace}} .ok{{color:#1E7A3B;font-weight:800}} .warn{{color:#B03A2E;font-weight:800}}
.boards{{display:grid;grid-template-columns:repeat(auto-fit,minmax(420px,1fr));gap:18px}}
.bd{{text-decoration:none;color:inherit;display:block;border:1.5px solid #1B1F24;background:#FBFAF5}}
.fr{{width:100%;aspect-ratio:4/3;overflow:hidden;position:relative}} .fr iframe{{width:1600px;height:1200px;border:0;transform-origin:0 0;transform:scale(var(--s,.3));pointer-events:none}}
.bd span{{display:block;padding:8px 10px;font-weight:700;font-size:13px;border-top:1.5px solid #1B1F24}}
.dls{{display:flex;gap:14px;flex-wrap:wrap}} .dl{{display:block;padding:14px 18px;border:1.5px solid #1B1F24;background:#1B1F24;color:#F6F4EE;text-decoration:none;font-weight:800}} .dl small{{display:block;font-weight:500;color:#D9C58B;margin-top:3px}}
</style></head><body>
<header><h1>Plot No. 83 · New Cairo — CAD &amp; Passive Design Explorer</h1><span>{PW:.2f} × {PH:.2f} m = {PLOT_AREA:.2f} m² · diagonal {DIAG:.2f} m · Basement + Ground + 3 Typical + Roof</span></header>
<nav><button class="tab on" data-s="plans">CAD plans</button><button class="tab" data-s="passive">Section &amp; passive</button><button class="tab" data-s="core">Core A vs B</button><button class="tab" data-s="sched">Area &amp; compliance</button><button class="tab" data-s="boards">Presentation boards</button><button class="tab" data-s="dl">Downloads</button></nav>
<main>
<div class="sec on" id="s-plans"><div class="bar">{tabs}<label><input type="checkbox" id="tSwept" checked> Swept-path arcs (R 3.2 / 5.8 m)</label><label><input type="checkbox" id="tPass"> Sun / wind overlay</label></div><div id="pvs" class="noswept0 nopass">{plans}</div></div>
<div class="sec" id="s-passive"><div class="card"><h3>Section A-A — N road → reception → courtyard → pool · animated airflow &amp; solar angles (30° N)</h3>{section}</div></div>
<div class="sec" id="s-core"><div class="grid2"><div class="card"><h3>Option A — stair wraps the lift (19.36 m²)</h3>{svga}</div><div class="card"><h3>Option B — lift beside stair (18.33 m²) — selected</h3>{svgb}</div></div>
<table class="t"><tr><th>Criterion (weight)</th><th>A</th><th>B</th></tr><tr><td>Structural (40%)</td><td class="n">{sc["A"]["struct"]}</td><td class="n">{sc["B"]["struct"]}</td></tr><tr><td>Spatial (30%)</td><td class="n">{sc["A"]["space"]}</td><td class="n">{sc["B"]["space"]}</td></tr><tr><td>Daylight / passive (15%)</td><td class="n">{sc["A"]["pass"]}</td><td class="n">{sc["B"]["pass"]}</td></tr><tr><td>Cost / buildability (15%)</td><td class="n">{sc["A"]["cost"]}</td><td class="n">{sc["B"]["cost"]}</td></tr><tr><th>Weighted</th><th class="n">{tot["A"]:.2f}</th><th class="n">{tot["B"]:.2f}</th></tr></table><p style="font-size:12px">Preliminary schematic judgement; structural engineer to confirm.</p></div>
<div class="sec" id="s-sched"><table class="t"><tr><th>Level</th><th>Elev.</th><th>GFA m²</th><th>% plot</th><th>Brief</th><th></th></tr>{t1}</table><table class="t"><tr><th>Requirement</th><th>Provision</th><th>Status</th></tr>{t2}</table><table class="t"><tr><th>Zero-waste measure</th><th>Design response</th></tr>{t3}</table></div>
<div class="sec" id="s-boards"><div class="boards">{boards}</div></div>
<div class="sec" id="s-dl"><div class="dls">{dls}</div></div>
</main>
<script>
const $=s=>document.querySelector(s),$$=s=>[...document.querySelectorAll(s)];
$$('nav .tab').forEach(b=>b.onclick=()=>{{$$('nav .tab').forEach(x=>x.classList.remove('on'));b.classList.add('on');$$('.sec').forEach(x=>x.classList.remove('on'));$('#s-'+b.dataset.s).classList.add('on');fit()}});
$$('.bar .tab').forEach(b=>b.onclick=()=>{{$$('.bar .tab').forEach(x=>x.classList.remove('on'));b.classList.add('on');$$('.pv').forEach(x=>x.classList.remove('on'));$('#pv'+b.dataset.k).classList.add('on')}});
function sw(){{const p=$('#pvs');p.classList.toggle('noswept',!$('#tSwept').checked);p.classList.toggle('nopass',!$('#tPass').checked)}}
$('#tSwept').onchange=sw;$('#tPass').onchange=sw;sw();
function fit(){{$$('.fr').forEach(f=>f.firstChild.style.setProperty('--s',f.clientWidth/1600))}}
addEventListener('resize',fit);fit();
</script></body></html>'''


def main():
    (HERE / 'board1-claude.html').write_text(board1(), encoding='utf-8')
    (HERE / 'board2-claude.html').write_text(board2(), encoding='utf-8')
    (HERE / 'index.html').write_text(index_html(), encoding='utf-8')
    a = area_tables()
    print('areas', {k: round(v, 2) for k, v in a.items()}, 'diag', round(DIAG, 2))


if __name__ == '__main__':
    main()
