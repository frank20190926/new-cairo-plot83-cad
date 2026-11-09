#!/usr/bin/env python3
"""Plot 83 editorial boards and interactive review page.

Run AFTER build_cad_2800443.py. All drawings are embedded from that generator's
canonical exports; this file deliberately contains no second floor-plan model.
North is up: 17 m E-W frontage, 25 m N-S depth. No network assets are required.
"""
from __future__ import annotations
import html
import re
from pathlib import Path

HERE = Path(__file__).resolve().parent
EXPORTS = HERE / 'exports'
PLAN_DATA = [
    ('B', 'Basement', '−3.20 m', 'plan_basement_sweptpath', 'Six parking bays',
     '6.00 m maneuvering aisle · Ri 3.20 / Ro 5.80 m',
     'Family sitting toward the south courtyard; kitchenette, two bathrooms, gym, storage and utility rooms.'),
    ('G', 'Ground floor', '+0.45 m', 'plan_ground', '212.50 m² / 50.00%',
     '13.00 × 17.00 − 8.50 m² open court',
     'North entry forecourt: 2.00 m. South garden: 6.00 m. Building X = 3.50–16.50 m; Y = 6.00–23.00 m.'),
    ('T', 'Typical floors ×3', '+3.75 / +7.05 / +10.35 m', 'plan_typical', '233.75 m² / 55.00%',
     '13.75 × 17.6181818… − 8.50 m² open court',
     'Reception north; three bedrooms east toward the pedestrian spine; kitchen and bathrooms on the west wall.'),
    ('R', 'Roof floor', '+13.65 m', 'plan_roof', '106.25 m² / 25.00%',
     '12.50 × 8.50 m enclosed roof floor',
     'A compact roof enclosure with open terraces, planting and reserved passive/environmental systems.'),
]


def esc(value):
    return html.escape(str(value), quote=True)


def drawing(key, instance=''):
    """Inline a canonical SVG with document-unique glyph IDs."""
    path = EXPORTS / f'{key}.svg'
    if not path.is_file():
        raise SystemExit(f'Missing {path.name}; run python3 build_cad_2800443.py first.')
    source = path.read_text(encoding='utf-8')
    source = source[source.index('<svg'):]
    prefix = key.replace('_', '-') + '-' + instance + '-'
    ids = re.findall(r'\bid="([^"]+)"', source)
    for old in sorted(set(ids), key=len, reverse=True):
        new = prefix + old
        source = source.replace(f'id="{old}"', f'id="{new}"')
        source = source.replace(f'="#{old}"', f'="#{new}"')
        source = source.replace(f'url(#{old})', f'url(#{new})')
    source = re.sub(r'(<svg\b[^>]*?)\swidth="[^"]*"', r'\1', source, count=1)
    source = re.sub(r'(<svg\b[^>]*?)\sheight="[^"]*"', r'\1', source, count=1)
    return source.replace('<svg ', f'<svg role="img" aria-label="{esc(key.replace("_", " "))}" ', 1)


BASE = '''
:root{--paper:#F6F4EE;--ink:#1B1F24;--muted:#58615E;--wine:#7A1F1F;--line:#C6C4BA;--wash:#EAE5D6;--teal:#087C83}
*{box-sizing:border-box}body{margin:0;background:var(--paper);color:var(--ink);font-family:"Helvetica Neue",Arial,sans-serif}
h1,h2,h3,p{margin:0}svg{display:block;width:100%;height:100%}a{color:inherit}
.mono{font-family:Menlo,Consolas,monospace;font-variant-numeric:tabular-nums}.eyebrow{font-size:12px;letter-spacing:2px;text-transform:uppercase;font-weight:700;color:var(--wine)}
.serif{font-family:Georgia,"Times New Roman",serif;font-weight:400}.muted{color:var(--muted)}
'''
BOARD = BASE + '''
html,body{width:1600px;height:1200px}.board{width:1600px;height:1200px;padding:38px 42px;display:flex;flex-direction:column}
header{height:126px;display:flex;justify-content:space-between;align-items:flex-start;border-bottom:2px solid var(--ink);flex-shrink:0}
header h1{font-size:52px;line-height:1.12;margin-top:10px;letter-spacing:-1.4px}header .stamp{text-align:right;padding-top:3px;font-size:14px;line-height:1.8}.stamp b{font-size:24px;color:var(--wine)}
footer{margin-top:auto;padding-top:12px;border-top:1px solid var(--ink);display:flex;justify-content:space-between;gap:35px;font-size:11px;line-height:1.5;flex-shrink:0}footer p{max-width:1130px}
.plan-grid{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:22px;margin-top:23px}
.plan{min-width:0}.plan+.plan{border-left:1px solid var(--line);padding-left:22px}.plan-head{height:92px;border-bottom:1px solid var(--line)}
.plan-head .num{font:34px Georgia,serif;color:var(--wine);float:left;margin-right:12px}.plan-head h2{font-size:21px;padding-top:3px;font-weight:500}.level{font-size:11px;margin-top:9px;white-space:nowrap}
.plan-drawing{height:548px;padding-top:10px}.plan-value{font-size:23px;color:var(--wine);font-weight:500;margin-top:12px}.plan-formula{font-size:11px;line-height:1.5;margin-top:9px}.plan-note{font-size:13px;line-height:1.55;margin-top:12px;max-width:320px}
.orientation-strip{display:flex;justify-content:space-between;gap:28px;background:var(--wash);padding:18px 22px;margin-top:22px;font-size:14px;line-height:1.6}.orientation-strip strong{display:block;font-size:12px;letter-spacing:1px;color:var(--wine);text-transform:uppercase}
.study-grid{display:grid;grid-template-columns:395px 610px 463px;gap:24px;margin-top:24px;height:916px}.study-col{min-width:0}.study-col+.study-col{border-left:1px solid var(--line);padding-left:24px}
.study-col h2{font-size:23px;font-weight:500;line-height:1.2}.study-col .intro{font-size:13px;line-height:1.6;margin-top:9px;color:var(--muted)}
.survey{height:567px;margin-top:12px}.section{height:385px;margin-top:8px}.core{height:316px;margin-top:12px}.solar-row{display:grid;grid-template-columns:280px 1fr;gap:18px;margin-top:22px;border-top:1px solid var(--line);padding-top:17px}.solar{height:285px}
.facts{margin-top:15px;font-size:13px;line-height:1.65}.facts div{border-top:1px solid var(--line);padding:9px 0}.facts b{color:var(--wine)}
.area-table{width:100%;border-collapse:collapse;margin-top:14px;font-size:13px}.area-table th,.area-table td{padding:11px 4px;border-bottom:1px solid var(--line);text-align:left}.area-table th{font-size:11px;color:var(--muted);text-transform:uppercase}.area-table td:last-child,.area-table th:last-child{text-align:right}.area-table td:nth-child(2){text-align:right;font-family:Menlo,monospace}
.formulas{margin-top:18px;font-size:12px;line-height:1.7}.formulas p{margin-top:10px}.buffer{background:var(--wash);padding:17px;margin-top:20px;font-size:13px;line-height:1.55}.buffer b{display:block;color:var(--wine);font-size:20px;margin-bottom:5px}.small{font-size:11px;line-height:1.6;color:var(--muted)}
'''


def page(title, body, css):
    return f'<!doctype html>\n<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>{esc(title)}</title><style>{css}</style></head><body>{body}</body></html>\n'


def heading(number, title, subtitle):
    return f'<header><div><p class="eyebrow">Plot 83 · Sector B · New Cairo</p><h1 class="serif">{title}</h1></div><div class="stamp"><b class="mono">{number}</b><br>{subtitle}<br><span class="mono">17.00 × 25.00 m / 425.00 m²</span></div></header>'


def footer(number):
    return f'<footer><p>ARCHITECTURAL CAD SET · Dimensions in metres. North is up on every site plan (17.00 m E–W North Road P4–P1 × 25.00 m N–S East Pedestrian Spine P1–P2). Area calculations deduct the 2.50 × 3.40 m (8.50 m²) open-to-sky central court.</p><span class="mono">PLOT 83 / {number}</span></footer>'


def area_table():
    return '''<table class="area-table"><thead><tr><th>Enclosed level</th><th>Area m²</th><th>Plot ratio</th></tr></thead><tbody><tr><td>Ground</td><td>212.50</td><td>50.00%</td></tr><tr><td>Typical · each ×3</td><td>233.75</td><td>55.00%</td></tr><tr><td>Roof</td><td>106.25</td><td>25.00%</td></tr><tr><td>Above-ground total</td><td>1,020.00</td><td>—</td></tr></tbody></table>'''


def board1():
    plans = []
    for code, title, level, asset, value, formula, note in PLAN_DATA:
        plans.append(f'<article class="plan"><div class="plan-head"><span class="num">{code}</span><h2>{title}</h2><p class="level mono">{level}</p></div><div class="plan-drawing" data-source="{asset}.svg">{drawing(asset,"board1")}</div><p class="plan-value">{value}</p><p class="plan-formula mono">{formula}</p><p class="plan-note">{note}</p></article>')
    strip = '''<div class="orientation-strip"><div><strong>North frontage · P4 → P1</strong>17.00 m along the 15 m road</div><div><strong>East depth · P1 → P2</strong>25.00 m along the 10 m pedestrian spine</div><div><strong>West access · P4 → P3</strong>3.00 m ramp strip beside Plot 84</div><div><strong>South garden · P3 → P2</strong>1.50 + 3.00 pool + 1.50 = 6.00 m</div></div>'''
    body = '<main class="board">' + heading('A–01', 'Four floors. One correct orientation.', 'Architectural plan set / north up') + '<div class="plan-grid">' + ''.join(plans) + '</div>' + strip + footer('A–01') + '</main>'
    return page('Plot 83 / Four portrait floor plans', body, BOARD)


def board2():
    left = f'''<section class="study-col"><p class="eyebrow">01 / Survey basis</p><h2 style="margin-top:8px">17 m frontage.<br>25 m depth.</h2><p class="intro">Boundary names and the P4–P2 diagonal follow the attached Arabic survey.</p><div class="survey">{drawing('site_survey','board2')}</div><div class="facts"><div><b>P4 (NW)</b> (0, 25) &nbsp; <b>P1 (NE)</b> (17, 25)</div><div><b>P3 (SW)</b> (0, 0) &nbsp; <b>P2 (SE)</b> (17, 0)</div><div><b>Diagonal</b> √(17² + 25²) = 30.23 m</div></div><p class="small" style="margin-top:10px">Cartesian coordinates: +X east, +Y north.<br>Road north · Plot 10 south · Plot 84 west · Spine / Plot 82 east.</p></section>'''
    center = f'''<section class="study-col"><p class="eyebrow">02 / Building & environment</p><h2 style="margin-top:8px">Section through the south garden</h2><div class="section">{drawing('section_aa','board2')}</div><div class="buffer"><b>1.50 m + 3.00 m + 1.50 m</b>Building wall → insulated backfill → pool → south fence. The 6.00 × 3.00 m pool dimension is its outer structural footprint; shell thickness lies within it.</div><div class="solar-row"><div class="solar">{drawing('passive_sun_wind_diagram','board2')}</div><div><h2 style="font-size:20px">Passive intent</h2><p class="intro">North reception receives prevailing breezes. East-facing bedrooms overlook the pedestrian spine.</p><p class="intro">The 2.50 × 3.40 m open court brings light and an exhaust path into the plan.</p><p class="small" style="margin-top:12px">Calculated for New Cairo (30.03° N): west solar mashrabiya, east morning light, and north-to-court cross-ventilation.</p></div></div></section>'''
    right = f'''<section class="study-col"><p class="eyebrow">03 / Core & area control</p><h2 style="margin-top:8px">A consistent vertical core</h2><div class="core">{drawing('core_options_comparison','board2')}</div><p class="small">Side-by-side comparison at identical scale: Option B saves 9.80 m² per floor plate with aligned shear walls.</p>{area_table()}<div class="formulas"><p><b>Ground</b><br><span class="mono">13.00 × 17.00 − 2.50 × 3.40<br>= 212.50 m²</span></p><p><b>Typical · each floor</b><br><span class="mono">13.75 × (242.25 / 13.75) − 8.50<br>= 233.75 m²</span></p><p class="small">Exact depth: 17.6181818… m; 17.62 m is the rounded drawing dimension.</p><p><b>Roof</b><br><span class="mono">12.50 × 8.50 = 106.25 m²</span></p></div></section>'''
    body = '<main class="board">' + heading('A–02', 'The survey sets the architecture.', 'Site, section & exact area reconciliation') + '<div class="study-grid">' + left + center + right + '</div>' + footer('A–02') + '</main>'
    return page('Plot 83 / Survey, section and area reconciliation', body, BOARD)


WEB = BASE + '''
html{scroll-behavior:smooth}body{line-height:1.5}button,input{font:inherit}button,a,input{outline-offset:5px}button{cursor:pointer}
.site-header{max-width:1440px;margin:auto;padding:28px 32px 20px;display:flex;align-items:center;justify-content:space-between;border-bottom:1px solid var(--line)}.brand{font-weight:700;text-decoration:none;letter-spacing:1px}.site-header nav{display:flex;gap:28px;font-size:13px}.site-header nav a{text-decoration:none}
main{max-width:1440px;margin:auto;padding:0 32px}.hero{padding:55px 0 36px;display:flex;justify-content:space-between;align-items:flex-end;gap:48px}.hero h1{font-size:clamp(38px,5vw,68px);line-height:1.07;letter-spacing:-2px;margin:14px 0 22px}.hero p{max-width:690px;color:var(--muted);font-size:17px}.hero .land{border-left:1px solid var(--line);padding-left:30px;min-width:220px}.land b{font-size:40px;font-weight:400;color:var(--wine)}
.review-section{padding:38px 0;border-top:1px solid var(--ink);scroll-margin-top:20px}.section-title{display:flex;justify-content:space-between;align-items:flex-end;gap:20px;margin-bottom:25px}.section-title h2{font:34px Georgia,serif;margin-top:8px}.section-title p{font-size:13px;color:var(--muted);max-width:400px}
.tabs{display:flex;flex-wrap:wrap;border-bottom:1px solid var(--line);gap:4px}.tab{border:0;background:transparent;padding:13px 22px;color:var(--muted);border-bottom:3px solid transparent}.tab[aria-selected=true]{border-bottom-color:var(--wine);color:var(--wine);font-weight:700}.tab:focus-visible{outline:2px solid var(--wine)}
.plan-view[hidden]{display:none}.plan-view{display:grid;grid-template-columns:minmax(0,1fr) 290px;gap:36px;padding-top:26px}.plan-canvas{height:920px;min-height:550px;border:1px solid var(--line);background:#F9F7F1;overflow:auto}.plan-canvas .vector{height:100%;min-width:100%}.plan-aside h3{font:29px Georgia,serif}.plan-aside .elevation{font-size:12px;margin:12px 0 22px;color:var(--wine)}.plan-aside .area{font-size:25px;margin:20px 0 10px}.plan-aside p{font-size:14px;line-height:1.7}.plan-aside .formula{font-size:12px;padding:16px 0;border-top:1px solid var(--line);border-bottom:1px solid var(--line);margin-bottom:20px}.links{display:flex;gap:12px;flex-wrap:wrap;margin-top:22px}.links a{font-size:12px;text-underline-offset:4px}.zoom{display:flex;align-items:center;gap:12px;font-size:13px;padding-top:12px}.zoom input{width:180px}
.survey-grid{display:grid;grid-template-columns:minmax(280px,1fr) minmax(300px,1.1fr);gap:55px}.site-vector{height:650px}.survey-copy{padding-top:25px}.survey-copy h3{font:32px Georgia,serif;margin-bottom:20px}.survey-copy p{font-size:15px;margin:16px 0}.bounds{border-collapse:collapse;width:100%;font-size:14px;margin:20px 0}.bounds td{padding:12px 0;border-bottom:1px solid var(--line)}.bounds td:first-child{font-weight:700;width:30%}.buffer-note{background:var(--wash);padding:22px;margin-top:28px}.buffer-note b{font-size:23px;color:var(--wine)}
.section-vector{height:700px;max-width:1060px;margin:auto}.schedule-grid{display:grid;grid-template-columns:1fr 1fr;gap:55px}.area-table{width:100%;border-collapse:collapse;font-size:15px}.area-table td,.area-table th{padding:16px 9px;border-bottom:1px solid var(--line);text-align:left}.area-table td:nth-child(2),.area-table td:last-child{text-align:right;font-variant-numeric:tabular-nums}.area-table th{font-size:12px;color:var(--muted);font-weight:500}.calcs p{margin-bottom:18px;font-size:14px}.calcs b{display:block;margin-bottom:6px;color:var(--wine)}.calcs .mono{font-size:13px}.footnote{font-size:12px;color:var(--muted);margin-top:24px;max-width:900px}.diagram-pair{display:grid;grid-template-columns:1fr 1fr;gap:40px}.diagram-pair .vector{height:520px}
.gallery{display:grid;grid-template-columns:1fr 1fr;gap:30px}.gallery a{text-decoration:none}.gallery img{width:100%;height:auto;border:1px solid var(--line);display:block}.gallery span{font-size:13px;display:block;padding-top:10px}.downloads{display:grid;grid-template-columns:repeat(3,1fr);gap:20px}.download{padding:25px;border-top:3px solid var(--wine);background:var(--wash);text-decoration:none}.download strong{display:block;font:25px Georgia,serif}.download span{display:block;font-size:13px;margin-top:10px}.download:hover{background:#E0DAC9}.site-footer{max-width:1376px;margin:35px auto 0;padding:25px 0;border-top:1px solid var(--ink);font-size:12px;color:var(--muted)}
@media(max-width:850px){.hero{display:block}.hero .land{margin-top:25px;padding:0;border:0}.site-header nav{gap:15px}.plan-view{grid-template-columns:1fr}.plan-aside{order:-1}.plan-canvas{height:800px}.survey-grid,.schedule-grid,.diagram-pair{grid-template-columns:1fr}.downloads{grid-template-columns:1fr}.section-vector{height:550px}.diagram-pair .vector{height:460px}.site-footer{margin-left:32px;margin-right:32px}.section-title{display:block}.section-title p{margin-top:12px}}
@media(max-width:520px){main{padding:0 18px}.site-header{padding:20px 18px;align-items:flex-start}.site-header nav{gap:12px;font-size:11px}.hero{padding-top:32px}.hero h1{letter-spacing:-1px}.hero p{font-size:15px}.land b{font-size:30px}.tab{padding:12px 11px;font-size:12px}.gallery{grid-template-columns:1fr}.plan-canvas{height:640px}.site-vector{height:550px}.section-vector{height:380px}.bounds{font-size:12px}.site-footer{margin:30px 18px 0}}
@media(prefers-reduced-motion:reduce){html{scroll-behavior:auto}}
'''


def index_html():
    tabs = ''.join(f'<button class="tab" role="tab" id="tab-{code}" aria-controls="plan-{code}" aria-selected="{str(i==0).lower()}" tabindex="{0 if i==0 else -1}" data-plan="{code}">{title}</button>' for i,(code,title,*_) in enumerate(PLAN_DATA))
    panels = []
    for i,(code,title,level,asset,value,formula,note) in enumerate(PLAN_DATA):
        panels.append(f'<section class="plan-view" id="plan-{code}" role="tabpanel" aria-labelledby="tab-{code}" {"hidden" if i else ""}><div class="plan-canvas"><div class="vector">{drawing(asset,"web")}</div></div><aside class="plan-aside"><h3>{title}</h3><p class="elevation mono">{level}</p><p class="area">{value}</p><p class="formula mono">{formula}</p><p>{note}</p><p style="margin-top:18px" class="muted">North is up. The 17.00 m frontage is horizontal; the 25.00 m depth is vertical.</p><div class="links"><a href="exports/{asset}.svg" download>Download vector SVG</a><a href="exports/{asset}.png" download>Download PNG</a></div></aside></section>')
    gallery = ''.join(f'<a href="board{n}-{author}.html" target="_blank" rel="noopener"><img src="board{n}-{author}.jpg" width="3200" height="2400" loading="lazy" alt="{label}"><span>{label} · open full sheet</span></a>' for n,author,label in [(1,'claude','A–01 · Four floor plans'),(2,'claude','A–02 · Survey, section & exact areas'),(1,'codex','Engineering sheet 01 · Parametric floor plans'),(2,'codex','Engineering sheet 02 · Solar & core studies')])
    body = f'''<div class="site-header"><a class="brand" href="#">PLOT 83</a><nav aria-label="Main"><a href="#plans">Plans</a><a href="#survey">Survey</a><a href="#areas">Areas</a><a href="#downloads">Downloads</a></nav></div>
<main><section class="hero"><div><p class="eyebrow">Sector B · New Cairo · Architectural study</p><h1 class="serif">17 m north frontage.<br>25 m depth.</h1><p>A north-facing house arranged around a light court, with east-facing bedrooms, a western access ramp and a six-metre-deep south pool garden.</p></div><div class="land"><b class="serif">425.00 m²</b><p>Plot 83<br>Basement + ground + 3 typical floors + roof</p></div></section>
<section class="review-section" id="plans"><div class="section-title"><div><p class="eyebrow">01 / Floor plans</p><h2>Every level, in the survey frame</h2></div><p>All drawings use one common geometry source. Room dimensions and areas are labeled in the plans.</p></div><div class="tabs" role="tablist" aria-label="Floor level">{tabs}</div><label class="zoom">Drawing zoom <input id="zoom" type="range" min="100" max="200" step="25" value="100" aria-label="Drawing zoom percentage"><output id="zoom-value">100%</output></label>{''.join(panels)}</section>
<section class="review-section" id="survey"><div class="section-title"><div><p class="eyebrow">02 / Survey reference</p><h2>Boundaries, coordinates and garden</h2></div><p>Mapped from the employer’s attached Arabic survey; north is the top edge.</p></div><div class="survey-grid"><div class="site-vector">{drawing('site_survey','web')}</div><div class="survey-copy"><h3>17.00 × 25.00 m</h3><table class="bounds"><tr><td>North · P4–P1</td><td>17.00 m · 15 m-wide road</td></tr><tr><td>East · P1–P2</td><td>25.00 m · 10 m pedestrian spine / Plot 82</td></tr><tr><td>West · P4–P3</td><td>25.00 m · Neighbor Plot 84 / 3.00 m ramp strip</td></tr><tr><td>South · P3–P2</td><td>17.00 m · Neighbor Plot 10</td></tr></table><p class="mono">P4 (0,25) &nbsp; P1 (17,25)<br>P3 (0,0) &nbsp; P2 (17,0)<br>P4–P2 = √(17² + 25²) ≈ 30.23 m</p><div class="buffer-note"><b>1.50 + 3.00 + 1.50 = 6.00 m</b><p>South wall → 1.50 m insulated backfill → 3.00 m pool depth in plan → 1.50 m south-fence clearance.</p><p>The pool occupies a 6.00 × 3.00 m outer structural footprint. The shell is contained within that envelope; these are not clear-water dimensions.</p></div></div></div></section>
<section class="review-section" id="section"><div class="section-title"><div><p class="eyebrow">03 / Section</p><h2>From the north road to the south pool</h2></div><p>Roof level +13.65 m; basement −3.20 m. Waterproofing, retaining structures and ramp transitions need detailed design.</p></div><div class="section-vector">{drawing('section_aa','web')}</div></section>
<section class="review-section" id="areas"><div class="section-title"><div><p class="eyebrow">04 / Area schedule</p><h2>Exact areas, explicit deductions</h2></div></div><div class="schedule-grid">{area_table()}<div class="calcs"><p><b>Ground floor</b><span class="mono">13.00 × 17.00 = 221.00 m²<br>221.00 − (2.50 × 3.40) = 212.50 m²</span></p><p><b>Typical floors · each</b><span class="mono">13.75 × (242.25 / 13.75) = 242.25 m²<br>242.25 − 8.50 = 233.75 m²</span><br>Depth is exactly 17.6181818… m; 17.62 m is a rounded label.</p><p><b>Roof floor</b><span class="mono">12.50 × 8.50 = 106.25 m²</span></p></div></div><p class="footnote">The 8.50 m² court is open to the sky. Enclosed areas and plot ratios are geometric calculations; local authority counting rules and statutory compliance are not certified by this schematic package.</p></section>
<section class="review-section" id="studies"><div class="section-title"><div><p class="eyebrow">05 / Design studies</p><h2>Sun, wind and the vertical core</h2></div><p>Passive strategies and core alternatives are conceptual. No unverified performance gain is claimed.</p></div><div class="diagram-pair"><div class="vector">{drawing('passive_sun_wind_diagram','web')}</div><div class="vector">{drawing('core_options_comparison','web')}</div></div></section>
<section class="review-section" id="boards"><div class="section-title"><div><p class="eyebrow">06 / Presentation set</p><h2>Four review sheets</h2></div><p>Open a sheet for the full vector presentation; downloadable CAD and PDF follow below.</p></div><div class="gallery">{gallery}</div></section>
<section class="review-section" id="downloads"><div class="section-title"><div><p class="eyebrow">07 / Files</p><h2>Inspect the drawing package</h2></div></div><div class="downloads"><a class="download" href="exports/Plot83_NewCairo_CAD_Package.zip" download><strong>Complete package</strong><span>ZIP · CAD, vector drawings, images and validation</span></a><a class="download" href="exports/Plot83_NewCairo_B_G_3_R_Master.dxf" download><strong>AutoCAD master</strong><span>DXF · basement, ground, typical, roof and studies</span></a><a class="download" href="exports/Plot83_NewCairo_Engineering_Set.pdf" download><strong>Engineering sheets</strong><span>PDF · complete vector drawing set</span></a></div><p class="footnote">Six parking bays, a 6.00 m maneuvering aisle and Ri 3.20 / Ro 5.80 m turning envelopes are drawn. These arcs do not establish complete vehicle accessibility or a certified swept-path simulation. See the package’s engineering validation for remaining constraints.</p></section></main>
<footer class="site-footer">PLOT 83 · SECTOR B · NEW CAIRO &nbsp; / &nbsp; Schematic architectural study. Dimensions in metres. North up.</footer>
<script>
const tabs=[...document.querySelectorAll('[role="tab"]')];
function selectTab(tab){{tabs.forEach(t=>{{const active=t===tab;t.setAttribute('aria-selected',String(active));t.tabIndex=active?0:-1;document.getElementById(t.getAttribute('aria-controls')).hidden=!active;}});}}
tabs.forEach((tab,i)=>{{tab.addEventListener('click',()=>selectTab(tab));tab.addEventListener('keydown',e=>{{let j;if(e.key==='ArrowRight')j=(i+1)%tabs.length;else if(e.key==='ArrowLeft')j=(i+tabs.length-1)%tabs.length;else if(e.key==='Home')j=0;else if(e.key==='End')j=tabs.length-1;else return;e.preventDefault();selectTab(tabs[j]);tabs[j].focus();}});}});
document.getElementById('zoom').addEventListener('input',e=>{{const v=Number(e.target.value);document.getElementById('zoom-value').value=v+'%';document.querySelectorAll('.plan-canvas .vector').forEach(el=>{{el.style.height=v+'%';el.style.width=v+'%';}});}});
</script>'''
    return page('Plot 83 / 17 m north frontage × 25 m depth', body, WEB)


def main():
    for filename, content in [('board1-claude.html',board1()),('board2-claude.html',board2()),('index.html',index_html())]:
        (HERE / filename).write_text(content,encoding='utf-8')
        print(f'Generated {filename} from canonical CAD SVGs')


if __name__ == '__main__':
    main()
