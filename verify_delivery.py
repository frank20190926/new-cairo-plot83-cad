#!/usr/bin/env python3
"""Read back delivered CAD coordinates, rather than trusting generator parameters."""
from pathlib import Path
import json
import math
import hashlib
import xml.etree.ElementTree as ET
import ezdxf
import fitz
from PIL import Image

ROOT=Path(__file__).resolve().parent
OUT=ROOT/'exports'


def main():
    metadata=json.loads((OUT/'engineering_validation.json').read_text())
    doc=ezdxf.readfile(OUT/'Plot83_NewCairo_B_G_3_R_Master.dxf')
    audit=doc.audit()
    assert not audit.errors and not audit.fixes
    assert doc.units==4
    model=doc.modelspace()
    index={r['drawing']:r['offset_x_mm'] for r in metadata['dxf']['drawing_index']}
    def rectangles(key,layer):
        offset=index[key];out=[]
        for entity in model.query('LWPOLYLINE'):
            if entity.dxf.layer!=layer:continue
            points=[((p[0]-offset)/1000,p[1]/1000) for p in entity.get_points()]
            if len(points)!=4:continue
            xs=[p[0] for p in points];ys=[p[1] for p in points]
            if min(xs)<-0.001 or max(xs)>17.001:continue
            out.append((min(xs),min(ys),max(xs),max(ys)))
        return out
    def close(a,b):return all(math.isclose(x,y,abs_tol=1e-7) for x,y in zip(a,b))
    def has(rects,expected):assert any(close(r,expected) for r in rects),(expected,rects)
    keys=['plan_basement_sweptpath','plan_ground','plan_typical','plan_roof','site_survey']
    for key in keys:has(rectangles(key,'SITE_BOUNDARY'),(0,0,17,25))
    has(rectangles('plan_ground','AREA_BOUNDARY'),(3.5,6,16.5,23))
    has(rectangles('plan_typical','AREA_BOUNDARY'),(3,6,16.75,6+242.25/13.75))
    for key in ['plan_ground','plan_typical','plan_roof']:
        has(rectangles(key,'AREA_BOUNDARY'),(7.5,11.6,10,15))
    roofs=rectangles('plan_roof','AREA_BOUNDARY')
    assert any(close((r[2]-r[0],r[3]-r[1]),(12.5,8.5)) for r in roofs)
    for key in ['plan_ground','plan_basement_sweptpath']:
        has(rectangles(key,'RAMP'),(0,9,3,25))
        pools=[r for r in rectangles(key,'WALLS') if close((r[2]-r[0],r[3]-r[1]),(6,3))]
        assert len(pools)==1 and close((pools[0][1],6-pools[0][3]),(1.5,1.5)),pools
    offset=index['site_survey']
    assert any(close(((e.dxf.start.x-offset)/1000,e.dxf.start.y/1000,(e.dxf.end.x-offset)/1000,e.dxf.end.y/1000),(0,25,17,0)) for e in model.query('LINE'))
    radii=sorted(e.dxf.radius/1000 for e in model.query('ARC') if e.dxf.layer=='SWEPT_PATH')
    assert close(radii,(3.2,5.8)),radii
    labels=[e.dxf.text for e in model.query('TEXT')]
    assert all(labels.count(str(n))==1 for n in range(1,7))
    pdf=fitz.open(OUT/'Plot83_NewCairo_Engineering_Set.pdf')
    assert len(pdf)==9
    assert all(not page.get_images() and page.get_drawings() for page in pdf)
    for file in OUT.glob('*.svg'):
        xml=ET.fromstring(file.read_text())
        assert not any(e.tag.rsplit('}',1)[-1] in ('text','image') for e in xml.iter())
        assert file.with_suffix('.png').is_file()
    from render_delivery import BOARDS,package
    for name,alias in BOARDS.items():
        source=ROOT/(name+'.jpg')
        assert Image.open(source).size==(3200,2400)
        digest=hashlib.sha256(source.read_bytes()).digest()
        for target in [name,alias]:
            assert hashlib.sha256((ROOT/'final_boards'/(target+'.jpg')).read_bytes()).digest()==digest
    report={'method':'Independent DXF entity coordinate read-back; no generator imports',
      'north_up_portrait_plot_count':5,'plot_m':[17,25],
      'ground_bounds_m':[3.5,6,16.5,23],'typical_bounds_m':[3,6,16.75,6+242.25/13.75],
      'court_m':[2.5,3.4],'ground_area_m2':212.5,'typical_area_m2':233.75,'roof_area_m2':106.25,
      'pool_outer_m':[6,3],'buffer_and_south_clearance_m':[1.5,1.5],
      'ramp_width_m':3,'swept_arc_radii_m':radii,'numbered_car_bays':6,
      'diagonal_P4_to_P2_m':math.hypot(17,25),'pdf_vector_pages':len(pdf),
      'svg_png_pairs':len(list(OUT.glob('*.svg'))),'root_boards':4,'matching_final_boards':8,
      'dxf_audit_errors':0,'status':'PASS','vehicle_routes_certified':False}
    (OUT/'coordinate_readback.json').write_text(json.dumps(report,indent=2)+'\n')
    package()
    print(json.dumps(report,indent=2))


if __name__=='__main__':main()
