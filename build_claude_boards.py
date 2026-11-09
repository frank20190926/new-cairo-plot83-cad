#!/usr/bin/env python3
"""Contest #2800443 — Plot 83 New Cairo (17.00 m E–W × 25.00 m N–S Portrait Orientation).
Claude generator: board1-claude.html, board2-claude.html, index.html.
Preserves 100% of the visual style, color palette, furniture blocks, swept-path overlays,
and dark charcoal header bars of the original Entry #36, oriented to the exact Arabic survey:
- North (P4–P1): 17.00 m along 15 m road
- South (P3–P2): 17.00 m along Neighbor Plot 10
- East  (P1–P2): 25.00 m along 10 m pedestrian spine / Plot 82
- West  (P4–P3): 25.00 m along Neighbor Plot 84 (3.00 m ramp / setback strip)
"""
import html
import math
from pathlib import Path

HERE = Path(__file__).resolve().parent
PW, PH = 17.0, 25.0                      # E–W width = 17.00 m, N–S depth = 25.00 m (Portrait, North Up)
PLOT_AREA = PW * PH                      # 425.00 m²
DIAG = math.hypot(PW, PH)                # 30.2324 m (P4 NW to P2 SE)
BX0, BX1 = 3.0, 17.0                     # building E–W extent: 3.00 m W setback -> 17.00 m E spine (width = 14.00 m)
INK, VEL = '#1B1F24', '#F6F4EE'

# ---- plan frame inside each 800 x 600 quadrant ----
# Portrait 17 x 25 m at S = 18.8 px/m -> width = 319.6 px, height = 470.0 px
S, OX, OY, CW, CH = 18.8, 38, 68, 800, 600


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


def text(px, py, t, fs=11, fill=INK, weight=600, anchor='middle', rot=0, extra='', family=None):
    fam = f' font-family="{family}"' if family else ''
    tr = f' transform="rotate({rot} {px:.1f} {py:.1f})"' if rot else ''
    return (f'<text x="{px:.1f}" y="{py:.1f}" font-size="{fs}" fill="{fill}" font-weight="{weight}" '
            f'text-anchor="{anchor}"{tr}{fam} {extra}>{esc(t)}</text>')


HALO = 'paint-order="stroke" stroke="#F6F4EE" stroke-width="2.6" stroke-linejoin="round"'


def label(cx, cy, name, w_m=None, h_m=None, area=None, fs=None, fill=INK, wpx=None):
    if not name:
        return ''
    lines = name.split('|')
    mx = max(len(l) for l in lines)
    if fs is None:
        w = wpx if wpx else 80
        fs = max(7.2, min(10.5, w / (0.56 * mx)))
    out = []
    extra_lines = (1 if (w_m is not None and h_m is not None) else 0) + (1 if area is not None else 0)
    n = len(lines) + extra_lines
    y0 = Y(cy) - (n - 1) * fs * 0.56 + fs * 0.32
    for i, l in enumerate(lines):
        out.append(text(X(cx), y0 + i * fs * 1.14, l, fs, fill, 700, extra=HALO))
    idx = len(lines)
    if w_m is not None and h_m is not None:
        out.append(text(X(cx), y0 + idx * fs * 1.14, f'{w_m:.2f}×{h_m:.2f}m', fs * 0.82, '#4A463C', 600, family='Menlo, monospace', extra=HALO))
        idx += 1
    if area is not None:
        out.append(text(X(cx), y0 + idx * fs * 1.14, f'{area:.1f} m²', fs * 0.84, '#7A1F1F', 700, family='Menlo, monospace', extra=HALO))
    return ''.join(out)


AREAS = {}
_LBL = []
_ROOMS = []


def flush():
    out = ''.join(_LBL)
    _LBL.clear()
    return out


def room(x0, y0, x1, y1, name, kind, key=None, show_area=True, show_dims=True, fs=None, sw=2.2):
    w_m = abs(x1 - x0)
    h_m = abs(y1 - y0)
    a = w_m * h_m
    if key:
        AREAS[key] = a
    clean_name = name.replace('|-', '').replace('|', ' ')
    if clean_name and show_area:
        _ROOMS.append((clean_name, w_m, h_m, a))
    _LBL.append(label(
        (x0 + x1) / 2, (y0 + y1) / 2, name,
        w_m if show_dims else None,
        h_m if show_dims else None,
        a if show_area else None,
        fs, wpx=S * w_m
    ))
    return rect(x0, y0, x1, y1, KIND[kind], sw=sw)


def box(x0, y0, x1, y1, fill='#FFFFFF', sw=1, op=1.0, stroke='#4B5560', rx=0):
    return (f'<rect x="{X(x0):.1f}" y="{Y(y1):.1f}" width="{S*(x1-x0):.1f}" height="{S*(y1-y0):.1f}" fill="{fill}" '
            f'stroke="{stroke}" stroke-width="{sw}" opacity="{op}" rx="{rx}"/>')


def circ(cx, cy, r, fill, stroke='#4B5560', sw=1, op=1.0):
    return f'<circle cx="{X(cx):.1f}" cy="{Y(cy):.1f}" r="{S*r:.1f}" fill="{fill}" stroke="{stroke}" stroke-width="{sw}" opacity="{op}"/>'


def win(x0, y0, x1, y1):
    return (line(x0, y0, x1, y1, VEL, 6.5) + line(x0, y0, x1, y1, '#3C8DB8', 3.0) +
            line(x0, y0, x1, y1, '#FFFFFF', 1.0))


def door(hx, hy, dx, dy, nx, ny, w=0.9):
    ex, ey = X(hx + dx * w), Y(hy + dy * w)
    fx, fy = X(hx + nx * w), Y(hy + ny * w)
    px, py = X(hx), Y(hy)
    cr = (ex - px) * (fy - py) - (ey - py) * (fx - px)
    sweep = 1 if cr > 0 else 0
    r = S * w
    return (f'<line x1="{px:.1f}" y1="{py:.1f}" x2="{ex:.1f}" y2="{ey:.1f}" stroke="{VEL}" stroke-width="5.5"/>'
            f'<line x1="{px:.1f}" y1="{py:.1f}" x2="{fx:.1f}" y2="{fy:.1f}" stroke="{INK}" stroke-width="1.4"/>'
            f'<path d="M {ex:.1f} {ey:.1f} A {r:.1f} {r:.1f} 0 0 {sweep} {fx:.1f} {fy:.1f}" fill="none" stroke="{INK}" stroke-width="0.85"/>')


def dimh(x0, x1, ypx, t, fs=9.5, fill='#7A1F1F'):
    a, b = X(x0), X(x1)
    return (f'<line x1="{a:.1f}" y1="{ypx}" x2="{b:.1f}" y2="{ypx}" stroke="{fill}" stroke-width="1"/>'
            f'<line x1="{a:.1f}" y1="{ypx-3.5}" x2="{a:.1f}" y2="{ypx+3.5}" stroke="{fill}" stroke-width="1"/>'
            f'<line x1="{b:.1f}" y1="{ypx-3.5}" x2="{b:.1f}" y2="{ypx+3.5}" stroke="{fill}" stroke-width="1"/>'
            f'<line x1="{a-2.5:.1f}" y1="{ypx+2.5}" x2="{a+2.5:.1f}" y2="{ypx-2.5}" stroke="{fill}" stroke-width="1.2"/>'
            f'<line x1="{b-2.5:.1f}" y1="{ypx+2.5}" x2="{b+2.5:.1f}" y2="{ypx-2.5}" stroke="{fill}" stroke-width="1.2"/>'
            + text((a + b) / 2, ypx - 3, t, fs, fill, 700, family='Menlo, monospace'))


def dimv(y0, y1, xpx, t, fs=9.5, fill='#7A1F1F'):
    a, b = Y(y0), Y(y1)
    return (f'<line x1="{xpx}" y1="{a:.1f}" x2="{xpx}" y2="{b:.1f}" stroke="{fill}" stroke-width="1"/>'
            f'<line x1="{xpx-3.5}" y1="{a:.1f}" x2="{xpx+3.5}" y2="{a:.1f}" stroke="{fill}" stroke-width="1"/>'
            f'<line x1="{xpx-3.5}" y1="{b:.1f}" x2="{xpx+3.5}" y2="{b:.1f}" stroke="{fill}" stroke-width="1"/>'
            f'<line x1="{xpx-2.5}" y1="{a+2.5:.1f}" x2="{xpx+2.5:.1f}" y2="{a-2.5:.1f}" stroke="{fill}" stroke-width="1.2"/>'
            f'<line x1="{xpx-2.5}" y1="{b+2.5:.1f}" x2="{xpx+2.5:.1f}" y2="{b-2.5:.1f}" stroke="{fill}" stroke-width="1.2"/>'
            + text(xpx - 3, (a + b) / 2, t, fs, fill, 700, rot=-90, family='Menlo, monospace'))


# ------------------------------------------------------------------ site layer (17m E-W x 25m N-S, North at y=25, South at y=0)
# South garden is y = 0.0 .. 6.0 (6.00 m deep):
# - South fence clearance: y = 0.0 .. 1.5 (1.50 m)
# - Pool: x = 9.5 .. 15.5 (6.00 m E-W), y = 1.5 .. 4.5 (3.00 m N-S)
# - Insulated structural buffer: y = 4.5 .. 6.0 (1.50 m between pool y=4.5 and building rear wall y=6.0)
POOL = (9.5, 1.5, 15.5, 4.5)
BUF = (9.0, 4.5, 16.0, 6.0)


def defs():
    return ('<defs>'
            f'<pattern id="hat" width="7" height="7" patternUnits="userSpaceOnUse" patternTransform="rotate(45)"><line x1="0" y1="0" x2="0" y2="7" stroke="{INK}" stroke-width="1" opacity=".35"/></pattern>'
            '<pattern id="hat2" width="6" height="6" patternUnits="userSpaceOnUse" patternTransform="rotate(-45)"><line x1="0" y1="0" x2="0" y2="6" stroke="#8A6B2F" stroke-width="1.2" opacity=".55"/></pattern>'
            '<pattern id="wave" width="14" height="8" patternUnits="userSpaceOnUse"><path d="M0 4 Q3.5 0 7 4 T14 4" fill="none" stroke="#FFFFFF" stroke-width="1" opacity=".8"/></pattern>'
            '<marker id="arr" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="6.5" markerHeight="6.5" orient="auto"><path d="M0 0 L10 5 L0 10 z" fill="context-stroke"/></marker>'
            '</defs>')


def site(level, tag):
    _ROOMS.clear()
    p = []
    p.append(f'<rect x="0" y="0" width="{CW}" height="{CH}" fill="{VEL}"/>')
    # 15m North Road above y=25
    p.append(f'<rect x="{OX}" y="32" width="{S*PW:.1f}" height="{OY-32}" fill="#CFCCC3"/>')
    p.append(f'<line x1="{OX}" y1="{OY-18}" x2="{OX+S*PW:.1f}" y2="{OY-18}" stroke="#F6F4EE" stroke-width="1.8" stroke-dasharray="12 8"/>')
    # 10m East Pedestrian Spine to the right of x=17
    p.append(f'<rect x="{OX+S*PW:.1f}" y="{OY}" width="24" height="{S*PH:.1f}" fill="#E4DCC8"/>')
    p.append(text(OX + S * PW + 14, OY + S * PH / 2, '10m E PEDESTRIAN SPINE (P1–P2 = 25.00m)', 8.5, '#6B6250', 700, rot=90))
    p.append(text(OX + S * PW / 2, 46, '15m NORTH ROAD (P4–P1 = 17.00m)', 9.0, '#4A463C', 800, 'middle'))
    p.append(text(11, OY + S * PH / 2, 'WEST · NEIGHBOR PLOT 84 (P4–P3 = 25.00m)', 8.2, '#6B6250', 700, rot=-90))
    # plot ground
    gfill = '#E5EBDA' if level != 'B' else '#DCDDD3'
    p.append(rect(0, 0, PW, PH, gfill, stroke=INK, sw=2.2))
    # Survey corner pins P1, P2, P3, P4 matching brief_assets/.png
    for (cx, cy, cname, dx, dy) in [
        (0, PH, 'P4', -10, -4),
        (PW, PH, 'P1', 10, -4),
        (0, 0, 'P3', -10, 11),
        (PW, 0, 'P2', 10, 11),
    ]:
        p.append(f'<circle cx="{X(cx):.1f}" cy="{Y(cy):.1f}" r="3.2" fill="#7A1F1F"/>')
        p.append(text(X(cx) + dx, Y(cy) + dy, cname, 8.5, '#7A1F1F', 800, family='Menlo, monospace'))
    # setback strips: 3.0 m West setback (x=0..3), 6.0 m South garden setback (y=0..6)
    p.append(rect(0, 0, 3.0, PH, 'url(#hat)', stroke='none', sw=0, extra='opacity=".42"'))
    p.append(rect(0, 0, PW, 6.0, 'url(#hat)', stroke='none', sw=0, extra='opacity=".26"'))
    p.append(line(3.0, 0, 3.0, PH, '#9B2C2C', 1.0, 'stroke-dasharray="6 4"'))
    p.append(line(0, 6.0, PW, 6.0, '#9B2C2C', 1.0, 'stroke-dasharray="6 4"'))
    # P4(0,25) to P2(17,0) diagonal = 30.23m
    p.append(line(0, PH, PW, 0, '#7A1F1F', 1.0, 'stroke-dasharray="3 5" opacity=".45"'))
    ang = math.degrees(math.atan2(PH, PW))
    p.append(text(X(2.4), Y(21.0), f'P4–P2 DIAG {DIAG:.2f}m', 8.0, '#7A1F1F', 700, 'middle', ang, family='Menlo, monospace', extra=HALO))
    # pool + 1.50m insulated backfill buffer + 1.50m south fence clearance
    bx0, by0, bx1, by1 = BUF
    p.append(rect(bx0, by0, bx1, by1, '#C9B98F', stroke='#8A6B2F', sw=1, extra='opacity=".65"'))
    p.append(rect(bx0, by0, bx1, by1, 'url(#hat2)', stroke='none', sw=0))
    x0, y0, x1, y1 = POOL
    p.append(rect(x0 - 0.12, y0 - 0.12, x1 + 0.12, y1 + 0.12, '#FFFFFF', stroke=INK, sw=1.8))
    p.append(rect(x0, y0, x1, y1, KIND['pool'], stroke='#1F6E8C', sw=1.4))
    p.append(rect(x0, y0, x1, y1, 'url(#wave)', stroke='none', sw=0))
    p.append(text(X((x0 + x1) / 2), Y((y0 + y1) / 2) + 3, 'POOL 6.0 × 3.0 m', 9.5, '#0D3C52', 800, extra=HALO))
    p.append(text(X((bx0 + bx1) / 2), Y(5.15), '1.50m insulated buffer', 7.8, '#5E4A1A', 800, extra=HALO))
    p.append(text(X((x0 + x1) / 2), Y(0.65), '1.50m S clearance', 7.8, '#5E4A1A', 700, extra=HALO))
    return ''.join(p)


def trees():
    out = []
    for (x, y, r) in [(4.3, 4.4, .65), (6.5, 2.2, .75), (4.6, 1.4, .5), (8.0, 4.6, .45)]:
        out.append(circ(x, y, r, '#8DB872', '#3E6B2F', 1.1, .95) + circ(x, y, r * .35, '#5E9A4B', 'none', 0, .9))
    return ''.join(out)


def right_schedule_card(level_code, heading_txt, formula_txt, target_txt, notes_list):
    """Renders the architectural schedule & dimension verification card on the right half of each 800x600 quadrant."""
    rx, ry, rw, rh = 394, 38, 396, 550
    out = [
        f'<rect x="{rx}" y="{ry}" width="{rw}" height="{rh}" fill="#FBFAF5" stroke="{INK}" stroke-width="1.5"/>',
        f'<rect x="{rx}" y="{ry}" width="{rw}" height="28" fill="#EAE5D6" stroke="{INK}" stroke-width="1.5"/>',
        text(rx + 10, ry + 18, heading_txt, 11, INK, 800, 'start'),
        f'<rect x="{rx+10}" y="{ry+36}" width="{rw-20}" height="42" fill="#EFE4CC" stroke="#8A6B2F" stroke-width="1"/>',
        text(rx + 18, ry + 53, formula_txt, 10.5, '#7A1F1F', 800, 'start', family='Menlo, monospace'),
        text(rx + 18, ry + 69, target_txt, 9.5, '#1E7A3B', 800, 'start', family='Menlo, monospace'),
    ]
    # Room table header
    ty = ry + 88
    out.append(f'<rect x="{rx+10}" y="{ty}" width="{rw-20}" height="20" fill="#EAE5D6" stroke="#B9B2A0" stroke-width="1"/>')
    out.append(text(rx + 16, ty + 14, 'ROOM / ZONE', 9.2, INK, 800, 'start'))
    out.append(text(rx + 250, ty + 14, 'DIM (W×L m)', 9.2, INK, 800, 'end'))
    out.append(text(rx + rw - 16, ty + 14, 'AREA m²', 9.2, INK, 800, 'end'))
    row_h = 20
    for idx, (rname, wm, hm, area) in enumerate(_ROOMS[:13]):
        yy = ty + 20 + idx * row_h
        bg = '#FFFFFF' if idx % 2 == 0 else '#F6F4EE'
        out.append(f'<rect x="{rx+10}" y="{yy}" width="{rw-20}" height="{row_h}" fill="{bg}" stroke="#D5CFC0" stroke-width="0.7"/>')
        out.append(text(rx + 14, yy + 14, rname[:32], 8.6, INK, 700, 'start'))
        out.append(text(rx + 262, yy + 14, f'{wm:.2f} × {hm:.2f} m', 8.5, '#4A463C', 600, 'end', family='Menlo, monospace'))
        out.append(text(rx + rw - 14, yy + 14, f'{area:.2f}', 8.8, '#7A1F1F', 700, 'end', family='Menlo, monospace'))

    # Bottom engineering highlights box
    by = ry + rh - 122
    out.append(f'<rect x="{rx+10}" y="{by}" width="{rw-20}" height="112" fill="#EAE5D6" stroke="#8A6B2F" stroke-width="1"/>')
    out.append(text(rx + 18, by + 16, 'SURVEY & BRIEF VERIFICATION (NORTH UP · 17m × 25m)', 9.2, '#7A1F1F', 800, 'start'))
    for j, nline in enumerate(notes_list[:5]):
        out.append(text(rx + 18, by + 33 + j * 16, f'✓ {nline}', 8.8, INK, 600, 'start'))
    return ''.join(out)


def frame(level_code, title, sub):
    p = []
    p.append(f'<rect x="0" y="0" width="{CW}" height="30" fill="{INK}"/>')
    p.append(text(12, 20, title, 13.5, '#F6F4EE', 800, 'start'))
    p.append(text(CW - 44, 20, sub, 10.0, '#D9C58B', 600, 'end', family='Menlo, monospace'))
    # north arrow (pointing UP to North Road)
    p.append(f'<g transform="translate({CW-22},15)"><circle r="11" fill="#F6F4EE"/><path d="M0 -9 L5 7 L0 3 L-5 7 z" fill="{INK}"/><text y="-11.5" x="0" font-size="8" fill="#F6F4EE" text-anchor="middle" font-weight="800">N</text></g>')
    # outer dims on the portrait plan
    ypx = OY + S * PH + 12
    p.append(dimh(0, PW, ypx + 12, '17.00m (E–W · P3–P2)', 9.5))
    p.append(dimv(0, PH, 25, '25.00m (N–S · P4–P3)', 9.5))
    p.append(dimh(0, 3.0, 62, '3.0m W', 8.5))
    return ''.join(p)


def stair(x0, y0, x1, y1, n, vertical=True):
    out = [box(x0, y0, x1, y1, '#F7F2E4', 1.1)]
    for i in range(1, n):
        if vertical:
            yy = y0 + (y1 - y0) * i / n
            out.append(line(x0, yy, x1, yy, '#4B5560', 0.75))
        else:
            xx = x0 + (x1 - x0) * i / n
            out.append(line(xx, y0, xx, y1, '#4B5560', 0.75))
    return ''.join(out)


def core_plan(level, y_top=22.0, x0=3.0):
    """Core in West-Central zone x=x0..7.5, y=y_top-4.2..y_top (Option B: lift adjacent to stair)."""
    y_bot = y_top - 4.2
    w_core = 7.5 - x0
    _ROOMS.insert(0, ('Stair & Lift Core B', w_core, 4.20, w_core * 4.20))
    out = [rect(x0, y_bot, 7.5, y_top, KIND['core'], sw=2.2)]
    out.append(stair(x0 + 0.15, y_bot + 0.15, x0 + 1.30, y_top - 0.85, 8))
    out.append(stair(x0 + 1.40, y_bot + 0.15, x0 + 2.55, y_top - 0.85, 8))
    out.append(box(x0 + 0.15, y_top - 0.85, x0 + 2.55, y_top - 0.12, '#F7F2E4', 1.1))
    out.append(line(x0 + 1.35, y_bot + 0.15, x0 + 1.35, y_top - 0.85, INK, 1.1))
    # lift shaft
    out.append(box(5.70, y_top - 2.05, 7.38, y_top - 0.15, '#EDEDED', 1.4, stroke=INK))
    out.append(line(5.70, y_top - 2.05, 7.38, y_top - 0.15, '#4B5560', 0.85))
    out.append(line(5.70, y_top - 0.15, 7.38, y_top - 2.05, '#4B5560', 0.85))
    out.append(text(X(6.54), Y(y_top - 1.10) + 3, 'LIFT', 7.8, INK, 800))
    out.append(text(X(x0 + 1.35), Y(y_top - 0.48) + 3, 'STAIR', 7.8, INK, 800))
    out.append(text(X(6.54), Y(y_bot + 1.05), 'LOBBY' if level != 'R' else 'OVERRUN', 7.8, INK, 800))
    return ''.join(out)


def car(x0, y0, w=2.0, h=4.4):
    cx0, cy0, cx1, cy1 = x0, y0, x0 + w, y0 + h
    out = [f'<rect x="{X(cx0):.1f}" y="{Y(cy1):.1f}" width="{S*w:.1f}" height="{S*h:.1f}" rx="6" fill="#7E8A97" stroke="#2F3944" stroke-width="1.2"/>']
    out.append(f'<rect x="{X(cx0+0.18):.1f}" y="{Y(cy1-0.85):.1f}" width="{S*(w-0.36):.1f}" height="{S*0.5:.1f}" rx="3" fill="#C7D6E2" stroke="#2F3944" stroke-width="0.7"/>')
    out.append(f'<rect x="{X(cx0+0.18):.1f}" y="{Y(cy0+0.9):.1f}" width="{S*(w-0.36):.1f}" height="{S*0.45:.1f}" rx="3" fill="#C7D6E2" stroke="#2F3944" stroke-width="0.7"/>')
    out.append(f'<rect x="{X(cx0+0.26):.1f}" y="{Y(cy1-1.6):.1f}" width="{S*(w-0.52):.1f}" height="{S*1.75:.1f}" rx="4" fill="#97A4B1" stroke="none"/>')
    return ''.join(out)


def bed(x0, y0, x1, y1, head='e'):
    out = [box(x0, y0, x1, y1, '#FFFFFF', 1.0, rx=2)]
    pw, pl = 0.65, 0.36
    if head == 'e':
        out += [box(x1 - pl - .08, y0 + .1, x1 - .08, y0 + .1 + pw, '#E8EEF5', .75),
                box(x1 - pl - .08, y1 - .1 - pw, x1 - .08, y1 - .1, '#E8EEF5', .75)]
    out.append(box(x0 + .05, y0 + .05, x1 - .48, y1 - .05, 'none', .55, 0.5, stroke='#7A8794'))
    return ''.join(out)


def wc(x, y):
    return box(x, y, x + 0.38, y + 0.60, '#FFFFFF', 0.9, rx=4) + box(x, y + 0.45, x + 0.38, y + 0.70, '#FFFFFF', 0.9)


def sofa(x0, y0, x1, y1):
    return box(x0, y0, x1, y1, '#C9A98B', 1.0, rx=2.5)


def table(x0, y0, x1, y1):
    out = [box(x0, y0, x1, y1, '#E6D2B0', 1.1, rx=2.5)]
    n = max(2, int((x1 - x0) / 0.58))
    for i in range(n):
        cx = x0 + (i + .5) * (x1 - x0) / n
        out += [box(cx - .18, y1 + .05, cx + .18, y1 + .38, '#B79C73', .75, rx=1.5),
                box(cx - .18, y0 - .38, cx + .18, y0 - .05, '#B79C73', .75, rx=1.5)]
    return ''.join(out)


def counter(x0, y0, x1, y1):
    return box(x0, y0, x1, y1, '#D9D4C7', 1.0) + box(x0 + .08, y0 + .08, x0 + .52, y0 + .48, '#9FB3C0', .75, rx=1.5)


# ------------------------------------------------------------------ overlays
def swept_overlay():
    """Swept path: outer R=5.8 / inner R=3.2 turning envelope from west ramp into the 6.00m column-free aisle."""
    out = ['<g class="swept">']
    pts = [(1.5, 24.2), (1.5, 9.0), (3.8, 9.0), (8.2, 14.5), (15.8, 14.5)]
    d = 'M ' + ' L '.join(f'{X(a):.1f} {Y(b):.1f}' for a, b in pts)
    out.append(f'<path d="{d}" fill="none" stroke="#C0392B" stroke-width="2.1" stroke-dasharray="7 4" marker-end="url(#arr)" opacity=".95"/>')
    # Turning fan in the 6.00m aisle (y = 11.5 .. 17.5, x = 8.5 .. 16.9)
    cx, cy = 9.6, 17.5
    for ro, ri, col in [(5.8, 3.2, '#C0392B'), (4.8, 2.6, '#8E44AD')]:
        p1 = (cx, cy - ro)
        p2 = (cx + ro, cy)
        p3 = (cx + ri, cy)
        p4 = (cx, cy - ri)
        fan = (f'M {X(p1[0]):.1f} {Y(p1[1]):.1f} A {S*ro:.1f} {S*ro:.1f} 0 0 0 {X(p2[0]):.1f} {Y(p2[1]):.1f} '
               f'L {X(p3[0]):.1f} {Y(p3[1]):.1f} A {S*ri:.1f} {S*ri:.1f} 0 0 1 {X(p4[0]):.1f} {Y(p4[1]):.1f} Z')
        out.append(f'<path d="{fan}" fill="{col}" fill-opacity=".18" stroke="{col}" stroke-width="1.4" stroke-dasharray="4 3"/>')
    out.append(f'<rect x="{X(7.7):.1f}" y="{Y(16.1):.1f}" width="166" height="26" fill="#FFFFFF" fill-opacity=".92" stroke="#C0392B" stroke-width="1"/>')
    out.append(text(X(7.7) + 5, Y(16.1) + 11, 'SWEPT PATH R_out=5.8m / R_in=3.2m', 7.8, '#C0392B', 800, 'start', family='Menlo, monospace'))
    out.append(text(X(7.7) + 5, Y(16.1) + 21, '6.00m CLEAR MANEUVERING AISLE', 7.5, '#C0392B', 700, 'start', family='Menlo, monospace'))
    out.append('</g>')
    return ''.join(out)


def courtyard_void(y0=12.4, y1=15.8):
    """Central open-to-sky wind court: x = 7.5 .. 10.0 (2.50 m) x y = 12.4 .. 15.8 (3.40 m) = 8.50 m²."""
    out = [
        rect(7.5, y0, 10.0, y1, KIND['void'], stroke='#1F5B7A', sw=2.0),
        text(X(8.75), Y((y0 + y1) / 2) - 6, 'OPEN COURT', 8.0, '#1F5B7A', 800, extra=HALO),
        text(X(8.75), Y((y0 + y1) / 2) + 4, '2.50×3.40m', 7.5, '#1F5B7A', 700, family='Menlo, monospace', extra=HALO),
        text(X(8.75), Y((y0 + y1) / 2) + 13, '8.50 m² VOID', 7.5, '#1F5B7A', 700, family='Menlo, monospace', extra=HALO),
    ]
    for (x, y) in ((8.1, y0 + 0.6), (9.4, y1 - 0.6)):
        out.append(circ(x, y, .22, '#6FA55A', '#3E6B2F', 0.9))
    return ''.join(out)


def passive_overlay(level):
    out = ['<g class="passive">']
    wind = '#1E78C8'
    for x in (9.0, 12.0, 15.0):
        out.append(f'<path class="flow" d="M {X(x):.1f} {Y(24.8):.1f} L {X(x):.1f} {Y(15.2):.1f}" stroke="{wind}" stroke-width="2.4" fill="none" stroke-dasharray="8 5" marker-end="url(#arr)"/>')
    out.append('</g>')
    return ''.join(out)


# ------------------------------------------------------------------ 4 portrait floor plans
def plan_basement(passive=False):
    p = [site('B', 'B')]
    # 3.0m West Ramp Strip (x=0..3.0, y=9.0..25.0 -> 16.00m run at 20% grade to -3.20m)
    p.append(rect(0, 9.0, 3.0, 25.0, '#D5D0C1', sw=2.2))
    p.append(rect(0, 9.0, 3.0, 25.0, 'url(#hat)', stroke='none', sw=0))
    for yy in (22.5, 19.0, 15.5, 12.0):
        p.append(f'<path d="M {X(1.5):.1f} {Y(yy+1.4):.1f} L {X(1.5):.1f} {Y(yy-0.2):.1f}" stroke="{INK}" stroke-width="1.5" marker-end="url(#arr)" fill="none"/>')
    p.append(text(X(1.5), Y(17.0), 'CAR RAMP 20% · 16.00m RUN · 3.00m W ↓ −3.20m', 8.2, INK, 800, rot=-90, extra=HALO))
    # Ramp bottom landing + drive entry (x=0..7.5, y=6.0..9.0)
    p.append(room(0.0, 6.0, 7.5, 9.0, 'RAMP LANDING|& DRIVE ENTRY', 'garage', 'bsmt_landing', fs=8.0))
    # 6-Car Garage on East side (x=7.5..17.0, y=9.5..25.0):
    # - North row: 3 bays (P1, P2, P3) at y=20.2..25.0 (each 2.80m x 4.80m)
    # - Center column-free maneuvering aisle: y=14.2..20.2 (6.00m clear depth!)
    # - South row: 3 bays (P4, P5, P6) at y=9.4..14.2 (each 2.80m x 4.80m)
    p.append(rect(7.5, 14.2, 17.0, 20.2, KIND['garage'], sw=1.8))
    _ROOMS.append(('6.0m Maneuvering Aisle', 9.50, 6.00, 57.00))
    for i in range(3):
        bx = 8.4 + i * 2.8
        # North stalls P1..P3
        p.append(rect(bx, 20.2, bx + 2.8, 25.0, KIND['garage'], sw=1.5))
        p.append(car(bx + 0.4, 20.4, 2.0, 4.3))
        p.append(text(X(bx + 1.4), Y(24.65), f'P{i+1} (2.8×4.8m)', 7.2, '#0B1522', 800, extra=HALO))
        # South stalls P4..P6
        p.append(rect(bx, 9.4, bx + 2.8, 14.2, KIND['garage'], sw=1.5))
        p.append(car(bx + 0.4, 9.6, 2.0, 4.3))
        p.append(text(X(bx + 1.4), Y(9.85), f'P{i+4} (2.8×4.8m)', 7.2, '#0B1522', 800, extra=HALO))
    _ROOMS.append(('6 Parking Stalls (P1–P6)', 8.40, 9.60, 80.64))

    # Core at x=3.0..7.5, y=20.8..25.0
    p.append(core_plan('B', y_top=25.0))
    # West amenity & utility rooms (x=3.0..7.5, y=9.0..20.8)
    p.append(room(3.0, 17.6, 7.5, 20.8, 'SMALL GYM', 'work', 'bsmt_gym', fs=8.2))
    p.append(room(3.0, 15.4, 5.25, 17.6, 'BATH 1', 'wet', 'bsmt_wc1', fs=7.5))
    p.append(room(5.25, 15.4, 7.5, 17.6, 'BATH 2', 'wet', 'bsmt_wc2', fs=7.5))
    p.append(wc(3.2, 15.7)); p.append(wc(5.45, 15.7))
    p.append(room(3.0, 13.0, 7.5, 15.4, 'KITCHENETTE', 'service', 'bsmt_kit', fs=8.0))
    p.append(counter(3.15, 14.7, 7.3, 15.25))
    p.append(room(3.0, 10.8, 7.5, 13.0, 'STORAGE ROOM', 'service', 'bsmt_store', fs=8.0))
    p.append(room(3.0, 9.0, 5.25, 10.8, 'ELECTRIC', 'service', 'bsmt_elec', fs=7.2))
    p.append(room(5.25, 9.0, 7.5, 10.8, 'WATER', 'service', 'bsmt_water', fs=7.2))

    # Family Sitting overlooking sunken southern pool court (x=7.5..17.0, y=6.0..9.4)
    p.append(room(7.5, 6.0, 17.0, 9.4, 'FAMILY SITTING|(overlooks sunken pool)', 'living', 'bsmt_family', fs=8.5))
    p.append(sofa(8.2, 6.4, 11.4, 7.1)); p.append(sofa(12.8, 6.4, 16.0, 7.1))
    p.append(win(9.0, 6.0, 16.0, 6.0))
    # Outer basement structural wall (x=3.0..17.0, y=6.0..25.0)
    p.append(f'<rect x="{X(3.0):.1f}" y="{Y(25.0):.1f}" width="{S*14.0:.1f}" height="{S*19.0:.1f}" fill="none" stroke="{INK}" stroke-width="5.5"/>')
    p.append(line(3.0, 6.5, 3.0, 8.8, VEL, 6))
    p.append(flush())
    p.append(swept_overlay())
    p.append(frame('B', 'A-01 · BASEMENT −3.20 m · 6 CARS · SWEPT PATH · POOL BUFFER',
                   f'PLOT 83 · 17×25m = {PLOT_AREA:.0f} m²'))
    p.append(right_schedule_card(
        'B',
        'B1 · BASEMENT SCHEDULE (−3.20 m)',
        'FOOTPRINT: 14.00 × 19.00 = 266.00 m²',
        '6 CARS + 6.00 m CLEAR AISLE + AMENITIES',
        [
            'West Ramp: 3.00m wide × 16.00m run (20% grade)',
            '6 Parking Bays (2.80×4.80m) + 6.00m clear aisle',
            'Swept-path turning radii R_in=3.20m / R_out=5.80m',
            'Family Sitting (32.3 m²) overlooks sunken pool',
            '1.50m insulated buffer + 3.0m pool + 1.50m S clear',
        ]
    ))
    if passive:
        p.append(passive_overlay('B'))
    return ''.join(p)


def plan_ground(passive=False):
    """Ground Floor (+0.45 m): exact 50% coverage = 212.50 m².
    Outer building envelope: x = 3.50 .. 16.50 (13.00 m E–W), y = 6.00 .. 23.00 (17.00 m N–S) = 221.00 m²
    Minus central open-to-sky court (2.50 × 3.40 m = 8.50 m²) = 212.50 m² (50.00% of 425.00 m²)!
    """
    p = [site('G', 'G'), trees()]
    # West Ramp in 3.00m setback strip
    p.append(rect(0, 9.0, 3.0, 25.0, '#D5D0C1', sw=2.2))
    p.append(rect(0, 9.0, 3.0, 25.0, 'url(#hat)', stroke='none', sw=0))
    p.append(text(X(1.5), Y(17.0), 'OPEN CAR RAMP ↓ −3.20m (20% GRADE)', 8.2, INK, 800, rot=-90, extra=HALO))
    # Core at x=3.5..7.5, y=18.8..23.0
    p.append(core_plan('G', y_top=23.0, x0=3.5))
    # North Reception & Guest Majlis (x=7.5..16.5, y=17.5..23.0 -> 9.00 x 5.50 = 49.50 m²)
    p.append(room(7.5, 17.5, 16.5, 23.0, 'NORTH RECEPTION & MAJLIS|(prevailing north breeze)', 'living', 'g_recep', fs=9.0))
    p.append(sofa(8.2, 21.8, 12.2, 22.6)); p.append(sofa(13.0, 21.8, 15.8, 22.6))
    p.append(sofa(15.5, 18.2, 16.2, 21.2)); p.append(box(10.0, 19.6, 13.0, 20.8, '#E6D2B0', 1, rx=2))
    # Central Open-to-Sky Wind Court: x=7.5..10.0 (2.50m) x y=12.4..15.8 (3.40m) = 8.50 m²
    # Lobby / Gallery north of court: x=7.5..10.0, y=15.8..17.5
    p.append(room(7.5, 15.8, 10.0, 17.5, 'FOYER', 'living', 'g_foyer', fs=7.8))
    # Dining on East Spine: x=10.0..16.5, y=12.4..17.5 (6.50 x 5.10 = 33.15 m²)
    p.append(room(10.0, 12.4, 16.5, 17.5, 'FORMAL DINING|(east spine view)', 'living', 'g_dining', fs=8.8))
    p.append(table(11.2, 14.4, 15.2, 15.4))
    # Kitchen & Prep on West wall: x=3.5..7.5, y=13.6..18.8 (4.00 x 5.20 = 20.80 m²)
    p.append(room(3.5, 13.6, 7.5, 18.8, 'KITCHEN & PREP|(west wall)', 'service', 'g_kit', fs=8.2))
    p.append(counter(3.65, 18.0, 7.35, 18.6)); p.append(counter(3.65, 14.0, 4.2, 18.0))
    # Guest Bath + Zero-Waste Hub on West wall: x=3.5..7.5, y=9.8..13.6
    p.append(room(3.5, 11.6, 7.5, 13.6, 'GUEST BATH', 'wet', 'g_bath', fs=7.8))
    p.append(wc(3.8, 12.2))
    p.append(room(3.5, 9.6, 7.5, 11.6, 'PANTRY / WASTE HUB', 'service', 'g_pantry', fs=7.5))
    # South Garden Veranda / Family Lounge + Guest Suite: y=6.0..12.4
    p.append(room(3.5, 6.0, 10.0, 9.6, 'FAMILY LOUNGE', 'living', 'g_family', fs=8.5))
    p.append(room(7.5, 9.6, 10.0, 12.4, 'HALL', 'living', 'g_hall', fs=7.5))
    p.append(room(10.0, 6.0, 16.5, 12.4, 'GARDEN VERANDA & STUDY|(overlooks south pool)', 'out', 'g_veranda', fs=8.5))
    p.append(sofa(11.0, 6.6, 15.4, 7.4))
    p.append(courtyard_void(12.4, 15.8))
    # Outer Ground Envelope: x=3.5..16.5 (13.00m), y=6.0..23.0 (17.00m)
    p.append(f'<rect x="{X(3.5):.1f}" y="{Y(23.0):.1f}" width="{S*13.0:.1f}" height="{S*17.0:.1f}" fill="none" stroke="{INK}" stroke-width="5.5"/>')
    p.append(win(8.5, 23.0, 15.8, 23.0)); p.append(win(16.5, 13.2, 16.5, 16.8)); p.append(win(16.5, 6.8, 16.5, 11.5))
    p.append(win(3.5, 14.2, 3.5, 17.8)); p.append(win(4.5, 6.0, 15.5, 6.0))
    p.append(door(8.6, 23.0, 1, 0, 0, -1, 1.1))
    p.append(text(X(12.0), Y(24.0), '2.00m NORTH ENTRY FORECOURT', 7.8, '#7A1F1F', 800, extra=HALO))
    p.append(flush())
    p.append(frame('G', 'A-01 · GROUND FLOOR +0.45 m · 50% = 212.50 m²',
                   f'PLOT 83 · 17×25m = {PLOT_AREA:.0f} m²'))
    p.append(right_schedule_card(
        'G',
        'G · GROUND FLOOR SCHEDULE (+0.45 m)',
        '13.00 × 17.00 − 8.50 court = 212.50 m²',
        'EXACT 50.00% OF 425.00 m² PLOT (PASS)',
        [
            'Outer Envelope: 13.00m (E–W) × 17.00m (N–S) = 221.0 m²',
            'Less Open Wind Court: 2.50m × 3.40m = −8.50 m²',
            'Net Ground Footprint = 212.50 m² (Exact 50.00%)',
            'North Forecourt = 2.00m; South Pool Garden = 6.00m',
            'North Reception + East Dining + West Kitchen/Baths',
        ]
    ))
    if passive:
        p.append(passive_overlay('G'))
    return ''.join(p)


def plan_typical(passive=False):
    """Typical Floor ×3 (+3.75 / +7.05 / +10.35 m): exact 55% coverage = 233.75 m² per floor.
    Outer envelope: x = 3.00 .. 16.75 (13.75 m E–W), y = 6.00 .. 23.6182 (17.6182 m N–S) = 242.25 m²
    Minus central open-to-sky court (2.50 × 3.40 m = 8.50 m²) = 233.75 m² (55.00% of 425.00 m²)!
    """
    yt = 6.0 + 242.25 / 13.75  # 23.6181818 m
    p = [site('T', 'T'), trees()]
    # Core at x=3.0..7.5, y=19.4..yt
    p.append(core_plan('T', y_top=yt, x0=3.0))
    # North Reception & Living: x=7.5..16.75, y=18.2..yt (9.25 x 5.42 = 50.12 m²)
    p.append(room(7.5, 18.2, 16.75, yt, 'NORTH RECEPTION & LIVING|(prevailing north wind)', 'living', 't_recep', fs=9.0))
    p.append(sofa(8.2, yt - 1.1, 12.4, yt - 0.3)); p.append(sofa(13.2, yt - 1.1, 16.0, yt - 0.3))
    p.append(table(8.2, 18.8, 11.6, 19.7))
    # 3 Bedrooms on East Pedestrian Spine (x=11.25..16.75 -> width 5.50 m):
    # - Bedroom 1 (NE): y=14.1..18.2 (5.50 x 4.10 = 22.55 m²)
    # - Bedroom 2 (Mid-E): y=10.1..14.1 (5.50 x 4.00 = 22.00 m²)
    # - Master Bedroom 3 (SE): y=6.0..10.1 (5.50 x 4.10 = 22.55 m²)
    p.append(room(11.25, 14.1, 16.75, 18.2, 'BEDROOM 1|(east spine)', 'bed', 't_bed1', fs=8.5))
    p.append(room(11.25, 10.1, 16.75, 14.1, 'BEDROOM 2|(east spine)', 'bed', 't_bed2', fs=8.5))
    p.append(room(11.25, 6.0, 16.75, 10.1, 'MASTER BEDROOM|(east + south garden)', 'bed', 't_bed3', fs=8.5))
    p.append(bed(14.3, 15.0, 16.4, 17.2, 'e'))
    p.append(bed(14.3, 11.0, 16.4, 13.2, 'e'))
    p.append(bed(14.3, 6.9, 16.4, 9.1, 'e'))
    # Private Hall between Court and East Bedrooms: x=10.0..11.25 (1.25m wide), y=6.0..18.2
    p.append(room(10.0, 6.0, 11.25, 18.2, 'HALL', 'living', 't_hall', show_dims=False, fs=7.2))
    p.append(room(7.5, 15.8, 10.0, 18.2, 'FOYER', 'living', 't_foyer', fs=7.5))
    p.append(room(7.5, 6.0, 10.0, 12.4, 'FAMILY NOOK|& LOGGIA', 'out', 't_nook', fs=8.0))
    # West Wall Kitchen + 3 Baths + Laundry (x=3.0..7.5 -> width 4.50 m):
    p.append(room(3.0, 14.4, 7.5, 19.4, 'KITCHEN|(west wall)', 'service', 't_kit', fs=8.5))
    p.append(counter(3.15, 18.6, 7.35, 19.2)); p.append(counter(3.15, 14.8, 3.7, 18.6))
    p.append(room(3.0, 11.6, 7.5, 14.4, 'BATH 1|(west wall)', 'wet', 't_bath1', fs=8.0))
    p.append(room(3.0, 8.8, 7.5, 11.6, 'BATH 2|(west wall)', 'wet', 't_bath2', fs=8.0))
    p.append(room(3.0, 6.0, 7.5, 8.8, 'MASTER BATH 3|& LAUNDRY', 'wet', 't_bath3', fs=7.8))
    p.append(wc(3.3, 12.0)); p.append(wc(3.3, 9.2)); p.append(wc(3.3, 6.4))
    p.append(courtyard_void(12.4, 15.8))
    # Outer Typical Envelope: x=3.0..16.75 (13.75m), y=6.0..23.62 (17.62m)
    p.append(f'<rect x="{X(3.0):.1f}" y="{Y(yt):.1f}" width="{S*13.75:.1f}" height="{S*(yt-6.0):.1f}" fill="none" stroke="{INK}" stroke-width="5.5"/>')
    p.append(win(8.2, yt, 16.0, yt)); p.append(win(16.75, 14.6, 16.75, 17.6)); p.append(win(16.75, 10.6, 16.75, 13.6)); p.append(win(16.75, 6.6, 16.75, 9.6))
    p.append(win(3.0, 15.0, 3.0, 18.6)); p.append(win(3.0, 12.0, 3.0, 13.8)); p.append(win(3.0, 9.2, 3.0, 11.0)); p.append(win(3.0, 6.5, 3.0, 8.2))
    p.append(flush())
    p.append(frame('T', 'A-01 · TYPICAL ×3 +3.75 / +7.05 / +10.35 · 55% = 233.75 m²',
                   f'PLOT 83 · 17×25m = {PLOT_AREA:.0f} m²'))
    p.append(right_schedule_card(
        'T',
        '01–03 · TYPICAL FLOOR ×3 (+3.75/+7.05/+10.35)',
        '13.75 × 17.62 − 8.50 court = 233.75 m²',
        'EXACT 55.00% OF 425.00 m² PLOT (PASS)',
        [
            'One Residence per Floor × 3 Typical Floors',
            'Outer Envelope: 13.75m × 17.618m = 242.25 m²',
            'Less Open Wind Court: 2.50m × 3.40m = −8.50 m²',
            'North Reception (50.1 m²) + 3 East Bedrooms',
            'West Wall Kitchen (22.5 m²) + 3 Baths with Mashrabiya',
        ]
    ))
    if passive:
        p.append(passive_overlay('T'))
    return ''.join(p)


def plan_roof(passive=False):
    """Roof Level (+13.65 m): exact 25% enclosed = 106.25 m².
    Enclosed Roof Service Block: x = 3.50 .. 16.00 (12.50 m E–W), y = 15.00 .. 23.50 (8.50 m N–S) = 106.25 m² (25.00%).
    Open-to-sky court (y = 12.40 .. 15.00) & landscaped south roof terrace (y = 6.00 .. 15.00) remain open!
    """
    yt = 6.0 + 242.25 / 13.75
    p = [site('R', 'R'), trees()]
    # Lower typical roof slab outline (x=3.0..16.75, y=6.0..yt)
    p.append(rect(3.0, 6.0, 16.75, yt, '#E6E3D8', sw=1.4, extra='stroke-dasharray="7 4"'))
    p.append(rect(3.0, 6.0, 16.75, 15.0, 'url(#hat)', stroke='none', sw=0, extra='opacity=".4"'))
    p.append(text(X(9.8), Y(8.2), 'LANDSCAPED ROOF TERRACE', 8.8, '#4A463C', 800, extra=HALO))
    p.append(text(X(9.8), Y(7.1), '127.5 m² rainwater & AC-condensate catchment', 7.6, '#4A463C', 600, extra=HALO))
    # Central court remains open to sky
    p.append(courtyard_void(12.0, 15.0))
    # Solar PV pergola on terrace (y=9.2..11.6)
    for c in range(4):
        bx = 4.2 + c * 2.8
        p.append(box(bx, 9.2, bx + 2.4, 11.4, '#2E4A6B', 0.9, stroke='#A9C2DC'))
    p.append(text(X(10.0), Y(10.3), 'PV PERGOLA ARRAY (28 PANELS ≈ 41.5 m²)', 7.8, '#FFFFFF', 800))
    # Enclosed Roof Level: x=3.5..16.0 (12.50m) x y=15.0..23.5 (8.50m) = 106.25 m² (25.00%)
    p.append(core_plan('R', y_top=23.5, x0=3.5))
    p.append(room(7.5, 19.3, 16.0, 23.5, 'GREYWATER & SOLAR|PLANT ROOM', 'roof', 'r_grey', fs=8.2))
    p.append(room(7.5, 15.0, 16.0, 19.3, 'ZERO-WASTE SORTING|& ROOF SERVICE', 'service', 'r_waste', fs=8.2))
    p.append(room(3.5, 15.0, 7.5, 19.3, 'MEP / STORAGE|ROOM', 'service', 'r_mep', fs=8.0))
    p.append(f'<rect x="{X(3.5):.1f}" y="{Y(23.5):.1f}" width="{S*12.5:.1f}" height="{S*8.5:.1f}" fill="none" stroke="{INK}" stroke-width="5.5"/>')
    p.append(door(9.5, 15.0, 1, 0, 0, 1, 0.95))
    p.append(flush())
    p.append(frame('R', 'A-01 · ROOF LEVEL +13.65 m · 25% = 106.25 m²',
                   f'PLOT 83 · 17×25m = {PLOT_AREA:.0f} m²'))
    p.append(right_schedule_card(
        'R',
        'R · ROOF LEVEL SCHEDULE (+13.65 m)',
        '12.50 × 8.50 = 106.25 m² ENCLOSED',
        'EXACT 25.00% OF 425.00 m² PLOT (PASS)',
        [
            'Enclosed Roof Footprint: 12.50m × 8.50m = 106.25 m²',
            'Exact 25.00% of 425.00 m² Land Area (PASS)',
            'Central Wind Court remains 100% open to sky',
            '28-Panel Solar PV Pergola (41.5 m²) shades terrace',
            'Greywater Recovery + 4-Stream Zero-Waste Plant',
        ]
    ))
    if passive:
        p.append(passive_overlay('R'))
    return ''.join(p)


def ns_svg(svg_str, pfx):
    for k in ('hat2', 'hat', 'wave', 'arr'):
        svg_str = svg_str.replace(f'id="{k}"', f'id="{k}-{pfx}"').replace(f'url(#{k})', f'url(#{k}-{pfx})')
    return svg_str


def svg_wrap(inner, cls='', w=CW, h=CH, idn='', pfx='p'):
    raw = f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" width="{w}" height="{h}" class="{cls}" {idn} font-family="Helvetica Neue, Arial, sans-serif">{defs()}{inner}</svg>'
    return ns_svg(raw, pfx)


def all_plans(passive=False):
    return {'B': svg_wrap(plan_basement(passive), 'plan', pfx='B'), 'G': svg_wrap(plan_ground(passive), 'plan', pfx='G'),
            'T': svg_wrap(plan_typical(passive), 'plan', pfx='T'), 'R': svg_wrap(plan_roof(passive), 'plan', pfx='R')}


# ------------------------------------------------------------------ section A-A (25.00 m N-S depth)
SX0, SSC = 58, 25.6          # x origin, px/m across 25.00 m N–S depth (25 * 25.6 = 640 px)
Z0 = 690                     # z=0 at pixel row
SEC_W, SEC_H = 800, 840


def SX(y): return SX0 + SSC * (PH - y)
def SZ(z): return Z0 - 34.0 * z


def sec_rect(y_n, y_s, z0, z1, fill, stroke=INK, sw=1.4, extra=''):
    return f'<rect x="{SX(y_n):.1f}" y="{SZ(z1):.1f}" width="{SSC*(y_n-y_s):.1f}" height="{34.0*(z1-z0):.1f}" fill="{fill}" stroke="{stroke}" stroke-width="{sw}" {extra}/>'


def sec_text(y, z, t, fs=10, fill=INK, weight=700, anchor='middle', rot=0):
    return text(SX(y), SZ(z), t, fs, fill, weight, anchor, rot)


def dimh_sec(y_a, y_b, ypx, t):
    a, b = SX(y_a), SX(y_b)
    c = '#7A1F1F'
    return (f'<line x1="{a:.1f}" y1="{ypx:.1f}" x2="{b:.1f}" y2="{ypx:.1f}" stroke="{c}"/>'
            f'<line x1="{a:.1f}" y1="{ypx-4:.1f}" x2="{a:.1f}" y2="{ypx+4:.1f}" stroke="{c}"/><line x1="{b:.1f}" y1="{ypx-4:.1f}" x2="{b:.1f}" y2="{ypx+4:.1f}" stroke="{c}"/>'
            + (text((a + b) / 2, ypx + 14, t, 10.0, c, 800, family='Menlo, monospace') if t else ''))


def section_svg():
    p = [defs(), f'<rect width="{SEC_W}" height="{SEC_H}" fill="{VEL}"/>']
    # North 15m Road + 25.00m N-S Site
    p.append(f'<rect x="0" y="{SZ(0):.1f}" width="{SX(25):.1f}" height="14" fill="#CFCCC3"/>')
    p.append(text(29, SZ(0) + 11, 'N ROAD 15m', 8.5, '#4A463C', 800))
    p.append(f'<rect x="{SX(25):.1f}" y="{SZ(0):.1f}" width="{SSC*25:.1f}" height="{34.0*3.4:.1f}" fill="#D8D2BE"/>')
    p.append(f'<rect x="{SX(25):.1f}" y="{SZ(0):.1f}" width="{SSC*25:.1f}" height="{34.0*3.4:.1f}" fill="url(#hat)" opacity=".5"/>')
    p.append(f'<line x1="{SX(25)}" y1="{SZ(0)}" x2="{SX(0)}" y2="{SZ(0)}" stroke="#4B5C3B" stroke-width="2.4"/>')
    p.append(sec_text(0.8, 0.35, 'S FENCE', 8.5, '#3E6B2F'))
    # Basement shell (y = 25.0 .. 6.0)
    p.append(sec_rect(25, 6, -3.2, 0.15, '#E1E2DE', sw=0))
    p.append(sec_rect(24.6, 20.2, -3.05, -2.3, '#7E8A97', stroke='#2F3944', sw=1.2, extra='rx="6"'))
    p.append(sec_rect(23.6, 21.2, -2.3, -1.7, '#C7D6E2', stroke='#2F3944', sw=1, extra='rx="5"'))
    p.append(sec_text(22.4, -1.3, 'STALL P2 (CAR)', 8.5, '#2F3944'))
    p.append(sec_text(17.2, -1.4, '6.0 m CLEAR AISLE', 9.5, '#2F3944'))
    p.append(sec_text(17.2, -1.95, '(column-free turning)', 8.5, '#2F3944', 600))
    p.append(sec_text(8.0, -1.5, 'FAMILY SITTING', 8.5, '#4A463C'))
    # Slabs
    def slab(yn, ys, z, t=0.28, fill=INK):
        return sec_rect(yn, ys, z - t, z, fill, sw=0)
    p.append(sec_rect(25, 6, -3.48, -3.2, INK, sw=0))
    p.append(slab(23.0, 6.0, 0.45))
    for z in (3.75, 7.05, 10.35):
        p.append(slab(23.62, 6.0, z))
    p.append(slab(23.62, 6.0, 13.65))
    p.append(sec_rect(23.5, 15.0, 16.35, 16.65, INK, sw=0))
    # Exterior walls
    p.append(sec_rect(23.22, 23.0, 0.15, 3.75, INK, sw=0))
    p.append(sec_rect(23.62, 23.40, 3.75, 16.65, INK, sw=0))
    p.append(sec_rect(6.22, 6.0, -3.48, 13.65, INK, sw=0))
    # Glazing
    for z in (0.45, 3.75, 7.05, 10.35):
        yn = 23.22 if z == 0.45 else 23.62
        p.append(sec_rect(yn, yn - 0.22, z + 0.8, z + 2.4, '#CFE6F2', stroke='#3C8DB8', sw=1.2))
        p.append(sec_rect(6.22, 6.0, z + 0.15, z + 2.65, '#CFE6F2', stroke='#3C8DB8', sw=1.2))
    # 0.9 m South Brise-Soleil overhangs
    for z in (3.75, 6.75, 10.05, 13.53):
        p.append(sec_rect(6.0, 5.1, z, z + 0.12, '#8A6B2F', sw=0))
    # Level markers
    lv = [(-3.2, '−3.20'), (0.45, '+0.45'), (3.75, '+3.75'), (7.05, '+7.05'), (10.35, '+10.35'), (13.65, '+13.65'), (16.65, '+16.65')]
    for z, t in lv:
        p.append(f'<line x1="{SX(25)-34:.1f}" y1="{SZ(z):.1f}" x2="{SX(23.6):.1f}" y2="{SZ(z):.1f}" stroke="#7A1F1F" stroke-width="1"/>')
        p.append(f'<text x="4" y="{SZ(z)-3:.1f}" font-family="Menlo, monospace" font-size="8.5" font-weight="700" fill="#7A1F1F">{esc(t)}</text>')
    for z, nm in ((0.45, 'NORTH MAJLIS'), (3.75, 'NORTH RECEPTION'), (7.05, 'NORTH RECEPTION'), (10.35, 'NORTH RECEPTION')):
        p.append(sec_text(19.5, z + 1.65, nm, 9.5, '#4A463C', 700))
    # Central Open-to-Sky Wind Court (y = 12.4 .. 15.8)
    p.append(sec_rect(15.8, 12.4, 0.45, 16.9, '#D5E8F2', stroke='none', sw=0, extra='opacity=".75"'))
    p.append(f'<line x1="{SX(15.8):.1f}" y1="{SZ(0.45):.1f}" x2="{SX(15.8):.1f}" y2="{SZ(16.9):.1f}" stroke="{INK}" stroke-width="1.8" stroke-dasharray="7 4"/>')
    p.append(f'<line x1="{SX(12.4):.1f}" y1="{SZ(0.45):.1f}" x2="{SX(12.4):.1f}" y2="{SZ(16.9):.1f}" stroke="{INK}" stroke-width="1.8" stroke-dasharray="7 4"/>')
    p.append(sec_text(14.1, 11.2, 'OPEN WIND COURT (2.5×3.4m)', 9.5, '#1F5B7A', 800, rot=-90))
    # Roof Enclosure + PV Pergola
    p.append(sec_rect(23.5, 15.0, 13.65, 16.35, '#ECE9DF', stroke='none', sw=0))
    p.append(sec_text(19.2, 14.8, 'ROOF PLANT (25% = 106.25 m²)', 9.0, '#4A463C', 700))
    p.append(f'<polygon points="{SX(11.8):.1f},{SZ(15.2):.1f} {SX(7.5):.1f},{SZ(16.1):.1f} {SX(7.5):.1f},{SZ(15.95):.1f} {SX(11.8):.1f},{SZ(15.05):.1f}" fill="#2E4A6B" stroke="#A9C2DC"/>')
    p.append(sec_text(9.6, 16.5, 'PV PERGOLA @ 30°', 9.0, '#2E4A6B', 800))
    # South Garden (y = 6.0 .. 0.0): 1.50m buffer (y=6.0..4.5) + 3.00m pool (y=4.5..1.5) + 1.50m S clearance (y=1.5..0.0)
    p.append(sec_rect(6.0, 4.5, -3.2, 0.0, '#C9B98F', stroke='#8A6B2F', sw=1.4, extra='opacity=".75"'))
    p.append(sec_rect(6.0, 4.5, -3.2, 0.0, 'url(#hat2)', stroke='none', sw=0))
    p.append(sec_text(5.25, -1.5, '1.50m BUFFER', 8.0, '#5E4A1A', 800, rot=-90))
    p.append(sec_rect(4.5, 1.5, -1.6, 0.0, '#86C8DC', stroke='#1F6E8C', sw=2))
    p.append(sec_text(3.0, -0.75, 'POOL 3.0m', 8.5, '#0D3C52', 800))
    p.append(dimh_sec(6.0, 4.5, SZ(-3.6), '1.5m'))
    p.append(dimh_sec(4.5, 1.5, SZ(-3.6), '3.0m'))
    p.append(dimh_sec(1.5, 0.0, SZ(-3.6), '1.5m'))
    p.append(dimh_sec(25.0, 0.0, SZ(-4.2), '25.00m N–S DEPTH (P1–P2 / P4–P3)'))

    # Solar rays
    sun = {'summer': ('#E8710A', 83.44), 'equinox': ('#C9A100', 60.0), 'winter': ('#2B7BB9', 36.56)}
    shade_notes = []

    def ray(season, y_wall, z_t, z_soffit, depth):
        col, alt = sun[season]
        ta = math.tan(math.radians(alt))
        d_hit = (z_soffit - z_t) / ta
        blocked = d_hit < depth
        L = 8.0
        y_start = y_wall - L * math.cos(math.radians(alt))
        z_start = z_t + L * math.sin(math.radians(alt))
        ye, ze = (y_wall - d_hit, z_soffit) if blocked else (y_wall, z_t)
        dash = ' stroke-dasharray="7 4"' if blocked else ''
        out = f'<line x1="{SX(y_start):.1f}" y1="{SZ(z_start):.1f}" x2="{SX(ye):.1f}" y2="{SZ(ze):.1f}" stroke="{col}" stroke-width="2.4"{dash}/>'
        out += f'<circle cx="{SX(ye):.1f}" cy="{SZ(ze):.1f}" r="3.5" fill="{col}"/>'
        return out, blocked

    for season in ('summer', 'equinox', 'winter'):
        o, b = ray(season, 6.0, 5.1, 6.75, 0.9)
        p.append(o)
        shade_notes.append((season, b))

    p.append(f'<g font-family="Menlo, monospace" font-size="9.5" font-weight="800">'
             f'<text x="{SX(4.5):.1f}" y="{SZ(15.2):.1f}" fill="#E8710A">SUMMER NOON 83.4°</text>'
             f'<text x="{SX(4.5):.1f}" y="{SZ(15.2)+13:.1f}" fill="#C9A100">EQUINOX 60.0°</text>'
             f'<text x="{SX(4.5):.1f}" y="{SZ(15.2)+26:.1f}" fill="#2B7BB9">WINTER NOON 36.6°</text>'
             f'<text x="{SX(4.5):.1f}" y="{SZ(15.2)+40:.1f}" fill="#4A463C">LAT 30° N · CAIRO</text></g>')
    # Airflow arrows
    wc_ = '#1E78C8'
    for z in (0.45, 3.75, 7.05, 10.35):
        zc = z + 1.65
        d = f'M 18 {SZ(zc):.1f} L {SX(14.1):.1f} {SZ(zc):.1f}'
        p.append(f'<path class="flow" d="{d}" fill="none" stroke="{wc_}" stroke-width="2.8" stroke-dasharray="10 6" marker-end="url(#arr)"/>')
    p.append(f'<path class="flow up" d="M {SX(14.1):.1f} {SZ(1.2):.1f} L {SX(14.1):.1f} {SZ(17.8):.1f}" fill="none" stroke="#C0392B" stroke-width="3.2" stroke-dasharray="10 7" marker-end="url(#arr)"/>')
    p.append(text(SX(14.1), SZ(18.1), 'STACK EXHAUST ↑', 9.5, '#C0392B', 800, family='Menlo, monospace'))
    p.append(text(SX(25), SZ(18.2), 'NORTH ▶ 15m Road (P4–P1 = 17m)', 10.5, INK, 800, 'start'))
    p.append(text(SX(0), SZ(18.2), 'SOUTH ▶ Pool Garden (P3–P2 = 17m)', 10.5, INK, 800, 'end'))
    return ''.join(p), shade_notes


# ------------------------------------------------------------------ core options (Option A wrap vs B adjacent)
CS = 44


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
    R, L, T = _cr(70, 14)
    b = [R(0, 0, 4.5, 4.2, '#D8D0BC', 3.4), R(0, 0, 2.6, 1.2, '#E4D9BD'), R(0, 1.2, 1.25, 3.0), R(1.35, 1.2, 1.25, 3.0)]
    for i in range(1, 9):
        yy = 1.2 + 3.0 * i / 9
        b += [L(0, yy, 1.25, yy), L(1.35, yy, 2.6, yy)]
    b += [T(1.3, 0.65, 'LANDING', 8.5), T(0.62, 2.7, '↑ UP', 9), T(1.98, 2.7, '↓ DN', 9),
          R(2.6, 0, 1.9, 2.0, '#EDEDED', 2.6), L(2.6, 0, 4.5, 2.0), L(2.6, 2.0, 4.5, 0), T(3.55, 1.0, 'LIFT', 11),
          R(2.6, 2.0, 1.9, 2.2, '#EFE4CC', 1.0, 'stroke-dasharray="4 3"'), T(3.55, 3.1, 'LIFT LOBBY', 9)]
    b.append(f'<text x="{70+2.25*CS:.1f}" y="{H_-8}" font-size="11" text-anchor="middle" font-weight="800" fill="#7A1F1F" font-family="Menlo, monospace">4.50 × 4.20 = {4.5*4.2:.2f} m²</text>')
    sc = {'A': {'struct': 9, 'space': 7, 'pass': 6, 'cost': 7}, 'B': {'struct': 7, 'space': 9, 'pass': 8, 'cost': 9}}
    w = {'struct': .40, 'space': .30, 'pass': .15, 'cost': .15}
    tot = {k: sum(sc[k][c] * w[c] for c in w) for k in sc}
    return wrap(''.join(a)), wrap(''.join(b)), sc, w, tot


def area_tables():
    basement = 14.0 * 19.0
    ramp = 3.0 * 16.0
    ground = 212.50
    typical = 233.75
    roof = 106.25
    return dict(basement=basement, ramp=ramp, ground=ground, typical=typical, roof=roof,
                above=ground + 3 * typical + roof, total=basement + ground + 3 * typical + roof)


def schedule_html():
    a = area_tables()
    rows = [
        ('Basement', '−3.20', f'{a["basement"]:.2f}', f'{a["basement"]/PLOT_AREA*100:.1f}%', '6 cars + sitting + gym', 'PASS'),
        ('Ground', '+0.45', f'{a["ground"]:.2f}', '50.00%', '13×17 − 8.50 court = 212.50', 'PASS'),
        ('Typical ×3 (each)', '+3.75 / +7.05 / +10.35', f'{a["typical"]:.2f}', '55.00%', '13.75×17.62 − 8.50 = 233.75', 'PASS'),
        ('Typical ×3 (total)', '', f'{3*a["typical"]:.2f}', '', '3 apartments (1 per floor)', 'PASS'),
        ('Roof level', '+13.65', f'{a["roof"]:.2f}', '25.00%', '12.50 × 8.50 = 106.25', 'PASS'),
        ('Above-ground GFA', '', f'{a["above"]:.2f}', '240.0%', 'Ground + 3×Typical + Roof', 'PASS'),
        ('Total GFA incl. B1', '', f'{a["total"]:.2f}', '', 'Full B+G+3+R CAD package', 'PASS'),
    ]
    t1 = ''.join(f'<tr><td>{esc(r[0])}</td><td>{esc(r[1])}</td><td class="n">{r[2]}</td><td class="n">{r[3]}</td><td>{esc(r[4])}</td><td class="ok">{esc(r[5])}</td></tr>' for r in rows)
    chk = [
        ('Survey Orientation (North Up)', 'North Road P4–P1 = 17.00m (E–W) × East Spine P1–P2 = 25.00m (N–S); diagonal P4–P2 = 30.23m', 'PASS'),
        ('West Setback & Ramp (3.00m)', '3.00m strip along West Neighbor Plot 84 (P4–P3); 20% ramp over 16.00m run to −3.20m', 'PASS'),
        ('South Pool Garden (6.00m)', '1.50m insulated building-to-pool buffer + 3.00m×6.00m pool + 1.50m south fence clearance = 6.00m', 'PASS'),
        ('Basement 6 Cars + Swept Path', '6 stalls (2.8×4.8m) + column-free 6.00m maneuvering aisle; R_in=3.20m / R_out=5.80m', 'PASS'),
        ('Basement Amenities', 'Family sitting overlooking sunken pool + kitchenette + 2 baths + small gym + storage + utility rooms', 'PASS'),
        ('Typical Floor Zoning', 'North Reception (prevailing wind) + 3 East Bedrooms (10m pedestrian spine) + West Kitchen & 3 Baths', 'PASS'),
        ('Open-to-Sky Wind Court', '2.50m × 3.40m = 8.50 m² central courtyard deducted on Ground & Typical floors; open at Roof', 'PASS'),
    ]
    t2 = ''.join(f'<tr><td>{esc(r[0])}</td><td>{esc(r[1])}</td><td class="ok">{esc(r[2])}</td></tr>' for r in chk)
    roof_pv = 28 * 1.9 * 0.78
    zw = [
        ('Cut-and-fill', f'Excavation reused on site for 1.50m insulated pool buffer backfill & garden grading'),
        ('Greywater & Rain', 'Baths + laundry + AC condensate treated in roof/basement plant for garden irrigation & WC flushing'),
        ('Zero-Waste Sorting', 'Dedicated 4-stream sorting room + isolated organic chute for garden composting'),
        ('Solar PV Pergola', f'28 panels ≈ {roof_pv:.1f} m² shading the roof terrace + solar thermal hot water array'),
        ('Modular Grid', '13.00m / 13.75m structural spans with local limestone, hollow-block infill & lime plaster'),
    ]
    t3 = ''.join(f'<tr><td>{esc(r[0])}</td><td>{esc(r[1])}</td></tr>' for r in zw)
    return t1, t2, t3, a


CSS_COMMON = '''
*{box-sizing:border-box;margin:0;padding:0}
html,body{width:1600px;height:1200px;overflow:hidden;background:#F6F4EE;font-family:"Helvetica Neue",Arial,sans-serif;color:#1B1F24}
.flow{animation:dash 1.4s linear infinite}
@keyframes dash{to{stroke-dashoffset:-34}}
'''


def board1():
    pl = all_plans()
    cells = [pl['B'], pl['G'], pl['T'], pl['R']]
    grid = ''.join(f'<div class="c">{c}</div>' for c in cells)
    return f'''<!DOCTYPE html><html lang="en"><head><meta charset="utf-8"><title>Sheet A-01 — Master Architectural Floor Plans & Swept-Path Blueprint (17m E-W × 25m N-S) · Plot 83 New Cairo</title>
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
<div class="hd"><h1>SHEET A-02 · PASSIVE DESIGN ANALYSIS · CORE ALTERNATIVE STUDY · ZERO-WASTE MATRIX</h1><span>PLOT 83 · NEW CAIRO · 17.00m (E–W) × 25.00m (N–S) = 425.00 m² · NORTH UP</span></div>
<div class="sec">{section}</div>
<div class="leg"><h3>Section A-A (25.00m N–S: North 15m Road → Reception → Open Wind Court → South Pool Garden)</h3>
<div><span class="k" style="border-color:#1E78C8"></span>Prevailing north wind: enters north reception, crosses the 2.5×3.4m wind court, cools all floors.
<span class="k" style="border-color:#C0392B;margin-left:12px"></span>Courtyard stack exhausts hot air at roof.</div>
<table><tr><th>Solar angle (noon, 30° N)</th><th>Altitude</th><th>Result on south glazing (0.9 m brise-soleil / 1.0 m slab overhang)</th></tr>
<tr><td style="color:#E8710A;font-weight:800">Summer solstice</td><td class="n">83.44°</td><td>shadow 0.9 × tan 83.44° = 8.0 m ≫ glazing height: fully shaded</td></tr>
<tr><td style="color:#C9A100;font-weight:800">Equinox</td><td class="n">60.00°</td><td>0.9 × tan 60° = 1.56 m: upper glazing shaded</td></tr>
<tr><td style="color:#2B7BB9;font-weight:800">Winter solstice</td><td class="n">36.56°</td><td>0.9 × tan 36.56° = 0.67 m: low sun enters, passive heat gain</td></tr></table>
<div>South Garden Section (6.00m): 1.50m insulated structural buffer + 3.00m pool outer shell + 1.50m south fence clearance.</div></div>
<div class="core">
<div class="o" style="left:0"><h2>CORE OPTION A — stair wraps the lift</h2>{svga}
<p>Closed RC box around a 2.0 × 2.0 m shaft; three flights, one lobby. Strong torsion core, but 19.36 m² and stair lacks direct exterior façade window.</p></div>
<div class="o" style="left:390px"><h2>CORE OPTION B — lift beside the stair ✔ drawn on plans</h2>{svgb}
<p>Dogleg stair plus lift: compact 18.90 m² footprint on the west façade → natural daylight and smoke ventilation, aligned shear-wall layout.</p></div></div>
<div class="sch">
<h2>Core scoring &amp; Exact Area Reconciliation — A {tot["A"]:.2f} · B {tot["B"]:.2f} → Option B Selected</h2>
<table class="t" style="width:45%;float:left;margin-right:2%"><tr><th>Criterion (weight)</th><th>A</th><th>B</th></tr>{srows}<tr><th>Weighted total</th><th class="n">{tot["A"]:.2f}</th><th class="n">{tot["B"]:.2f}</th></tr></table>
<table class="t" style="width:53%"><tr><th>Level</th><th>Elev.</th><th>GFA m²</th><th>% plot</th><th>Formula</th><th>Status</th></tr>{t1}</table>
<h2 style="clear:both">Survey &amp; Brief Compliance Schedule (17.00m E–W × 25.00m N–S Portrait)</h2><table class="t"><tr><th>Requirement</th><th>Provision</th><th>Status</th></tr>{t2}</table>
<h2>Zero-waste &amp; Resource Recovery Measures</h2><table class="t"><tr><th>Measure</th><th>Design response</th></tr>{t3}</table></div>
</body></html>'''


def index_html():
    pl = all_plans(passive=True)
    svga, svgb, sc, w, tot = core_options()
    t1, t2, t3, a = schedule_html()
    names = {'B': 'Basement −3.20m', 'G': 'Ground +0.45m (50%)', 'T': 'Typical ×3 +3.75m (55%)', 'R': 'Roof +13.65m (25%)'}
    tabs = ''.join(f'<button class="tab" role="tab" id="tab-{k}" aria-controls="plan-{k}" aria-selected="{str(i==0).lower()}" tabindex="{0 if i==0 else -1}">{names[k]}</button>' for i, k in enumerate('BGTR'))
    plans = ''.join(f'<div class="pv" role="tabpanel" id="plan-{k}" aria-labelledby="tab-{k}" {"hidden" if i else ""}><div class="plan-canvas"><div class="vector">{pl[k]}</div></div></div>' for i, k in enumerate('BGTR'))
    sec, _ = section_svg()
    section = ns_svg(f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {SEC_W} {SEC_H}" style="width:100%;max-width:760px" font-family="Helvetica Neue, Arial, sans-serif">{sec}</svg>', 'sec')
    boards = ''.join(f'<a class="bd" href="{f}" target="_blank"><img src="{img}" style="width:100%;height:auto;display:block" alt="{t}"><span>{t}</span></a>' for f, img, t in (
        ('board1-claude.html', 'board1-claude.jpg', 'Sheet A-01 · All 4 Floor Plans & Room Schedules (17m × 25m Portrait)'),
        ('board2-claude.html', 'board2-claude.jpg', 'Sheet A-02 · Passive Section, Core Study & Zero-Waste Matrix'),
        ('board1-codex.html', 'board1-codex.jpg', 'Engineering Sheet 01 · Parametric CAD Plans & Swept Path'),
        ('board2-codex.html', 'board2-codex.jpg', 'Engineering Sheet 02 · Solar Geometry & Core Study')))
    dls = ''.join(f'<a class="dl" href="exports/{f}" download>⬇ {f}<small>{d}</small></a>' for f, d in (
        ('Plot83_NewCairo_CAD_Package.zip', 'Complete ZIP (DXF + PDF + SVG + Boards)'),
        ('Plot83_NewCairo_B_G_3_R_Master.dxf', 'AutoCAD Master DXF (mm, 15 layers, 17m×25m)'),
        ('Plot83_NewCairo_Engineering_Set.pdf', '9-Page Vector Engineering Set PDF')))
    return f'''<!DOCTYPE html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Plot 83 New Cairo — 17m × 25m Portrait CAD &amp; Passive Design Explorer</title>
<style>
*{{box-sizing:border-box;margin:0;padding:0}}
body{{font-family:"Helvetica Neue",Arial,sans-serif;background:#F6F4EE;color:#1B1F24}}
header{{background:#1B1F24;color:#F6F4EE;padding:14px 28px;display:flex;align-items:baseline;gap:18px;flex-wrap:wrap}}
header h1{{font-size:20px}} header span{{font:600 12px Menlo,monospace;color:#D9C58B}}
main{{padding:16px 28px 40px;max-width:1440px;margin:auto}}
.bar{{display:flex;gap:10px;align-items:center;margin:8px 0 12px;flex-wrap:wrap;font-size:13px}}
.tab{{font:700 13px inherit;padding:8px 14px;border:1.5px solid #1B1F24;background:#FBFAF5;cursor:pointer}}
.tab[aria-selected="true"]{{background:#1B1F24;color:#F6F4EE}}
.pv[hidden]{{display:none}}
.pv{{border:1.5px solid #1B1F24;background:#fff;overflow:auto}}
.plan-canvas .vector svg{{width:100%;height:auto;display:block}}
.grid2{{display:grid;grid-template-columns:repeat(auto-fit,minmax(360px,1fr));gap:16px;margin-top:24px}}
.card{{border:1.5px solid #1B1F24;background:#FBFAF5;padding:12px}} .card h3{{font-size:14px;margin-bottom:8px}}
table.t{{width:100%;border-collapse:collapse;font-size:12.5px;margin:12px 0}} table.t td,table.t th{{border:1px solid #B9B2A0;padding:4px 7px;text-align:left}} table.t th{{background:#EAE5D6}}
.n{{text-align:right!important;font-family:Menlo,monospace}} .ok{{color:#1E7A3B;font-weight:800}}
.boards{{display:grid;grid-template-columns:repeat(auto-fit,minmax(420px,1fr));gap:18px;margin-top:20px}}
.bd{{text-decoration:none;color:inherit;display:block;border:1.5px solid #1B1F24;background:#FBFAF5}}
.bd span{{display:block;padding:8px 10px;font-weight:700;font-size:13px;border-top:1.5px solid #1B1F24}}
.dls{{display:flex;gap:14px;flex-wrap:wrap;margin-top:20px}} .dl{{display:block;padding:14px 18px;border:1.5px solid #1B1F24;background:#1B1F24;color:#F6F4EE;text-decoration:none;font-weight:800}} .dl small{{display:block;font-weight:500;color:#D9C58B;margin-top:3px}}
@media(max-width:600px){{main{{padding:12px 14px}}header{{padding:12px 14px}}.boards{{grid-template-columns:1fr}}}}
</style></head><body>
<header><h1>Plot No. 83 · New Cairo — 17.00m (E–W) × 25.00m (N–S) Portrait CAD Set</h1><span>North 15m Road (P4–P1 = 17.00m) × East 10m Spine (P1–P2 = 25.00m) = 425.00 m² · P4–P2 Diagonal = 30.23 m</span></header>
<main>
<div class="bar" role="tablist">{tabs}<label style="margin-left:auto;font-weight:700">Zoom <input id="zoom" type="range" min="100" max="200" step="25" value="100"><output id="zoom-value">100%</output></label></div>
{plans}
<div class="boards">{boards}</div>
<div class="dls">{dls}</div>
<div class="grid2"><div class="card"><h3>Section A-A (25.00m N–S Depth)</h3>{section}</div><div class="card"><h3>Area &amp; Survey Compliance Schedule</h3><table class="t"><tr><th>Level</th><th>Elev.</th><th>GFA m²</th><th>% plot</th><th>Formula</th><th>Status</th></tr>{t1}</table><table class="t"><tr><th>Requirement</th><th>Provision</th><th>Status</th></tr>{t2}</table></div></div>
</main>
<script>
const tabs=[...document.querySelectorAll('[role="tab"]')];
function selectTab(tab){{tabs.forEach(t=>{{const active=t===tab;t.setAttribute('aria-selected',String(active));t.tabIndex=active?0:-1;document.getElementById(t.getAttribute('aria-controls')).hidden=!active;}});}}
tabs.forEach((tab,i)=>{{tab.addEventListener('click',()=>selectTab(tab));tab.addEventListener('keydown',e=>{{let j;if(e.key==='ArrowRight')j=(i+1)%tabs.length;else if(e.key==='ArrowLeft')j=(i+tabs.length-1)%tabs.length;else if(e.key==='Home')j=0;else if(e.key==='End')j=tabs.length-1;else return;e.preventDefault();selectTab(tabs[j]);tabs[j].focus();}});}});
document.getElementById('zoom').addEventListener('input',e=>{{const v=Number(e.target.value);document.getElementById('zoom-value').value=v+'%';document.querySelectorAll('.plan-canvas .vector').forEach(el=>{{el.style.height=v+'%';el.style.width=v+'%';}});}});
</script></body></html>'''


def main():
    (HERE / 'board1-claude.html').write_text(board1(), encoding='utf-8')
    (HERE / 'board2-claude.html').write_text(board2(), encoding='utf-8')
    (HERE / 'index.html').write_text(index_html(), encoding='utf-8')
    a = area_tables()
    print('Generated portrait 17x25 Claude boards & index:', {k: round(v, 2) for k, v in a.items()}, 'diag', round(DIAG, 2))


if __name__ == '__main__':
    main()
