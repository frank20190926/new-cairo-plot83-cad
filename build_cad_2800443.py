#!/usr/bin/env python3
"""Plot 83 deterministic schematic CAD package. Metres in model, mm in DXF.

Uses existing ezdxf and PyMuPDF only. Does NOT claim construction compliance.
Run: python3 build_cad_2800443.py [--config parameters.json] [--out exports]
Every drawing/export is generated from the same geometric primitives.
"""
from __future__ import annotations
import argparse, dataclasses, hashlib, html, json, math, pathlib, zipfile
from dataclasses import dataclass, field
import ezdxf
from ezdxf.enums import TextEntityAlignment
import fitz

ROOT = pathlib.Path(__file__).resolve().parent
PAPER = '#f6f3eb'; INK = '#253b3d'; MUTED = '#657473'; TEAL = '#087c83'; AMBER = '#a96519'
LIGHT = '#dfebe6'; WATER = '#d6e9ec'; GRAY = '#e5e5df'; RED = '#a84332'
LAYER_COLORS = {'SITE_BOUNDARY':7,'WALLS':7,'COLUMNS':8,'DIMENSIONS':8,'SWEPT_PATH':4,
 'POOL_BUFFER':30,'PASSIVE_WIND_SUN':4,'TEXT':7,'FURNITURE':8,'LANDSCAPE':3,'GLAZING':4,
 'CORE':7,'RAMP':30,'ISSUES':1,'AREA_BOUNDARY':3}

@dataclass(frozen=True)
class Parameters:
    plot_w: float = 17.0
    plot_d: float = 25.0
    west_setback: float = 3.0
    rear_setback: float = 4.0
    road_w: float = 15.0
    spine_w: float = 10.0
    ground_ratio: float = .50
    typical_ratio: float = .55
    roof_ratio: float = .25
    floor_depth: float = 17.0
    ground_east_gap: float = 1.0
    typical_east_gap: float = .25
    rear_wall_y: float = 19.9
    wall: float = .25
    partition: float = .20
    ramp_width: float = 3.5
    ramp_grade: float = .15
    basement_z: float = -3.2
    ground_z: float = .45
    storey: float = 3.3
    roof_depth: float = 10.0
    pool_w: float = 6.0
    pool_d: float = 3.0
    pool_shell: float = .20
    pool_buffer: float = 1.5
    pool_water_z: float = -1.80
    pool_depth: float = 1.20
    bay_w: float = 2.40
    bay_d: float = 4.60
    car_w: float = 1.80
    car_l: float = 4.30
    aisle: float = 6.0
    inner_r: float = 3.2
    outer_r: float = 5.8
    family_area: float = 32.0
    gym_area: float = 18.0
    storage_area: float = 10.0
    kitchenette_area: float = 8.0
    reception_area: float = 58.0
    kitchen_area: float = 18.0
    latitude: float = 30.03
    @property
    def land(self): return self.plot_w*self.plot_d
    @property
    def gf_w(self): return self.land*self.ground_ratio/self.floor_depth
    @property
    def tf_w(self): return self.land*self.typical_ratio/self.floor_depth
    @property
    def rf_w(self): return self.land*self.roof_ratio/self.roof_depth
    @property
    def gf_x(self): return self.plot_w-self.ground_east_gap-self.gf_w
    @property
    def tf_x(self): return self.plot_w-self.typical_east_gap-self.tf_w
    @property
    def front_y(self): return self.rear_wall_y-self.floor_depth
    @property
    def ramp_run(self): return -self.basement_z/self.ramp_grade
    @property
    def levels(self): return [self.basement_z]+[self.ground_z+i*self.storey for i in range(5)]
    @property
    def pool(self):
        return (self.plot_w-1.25-self.pool_w, self.rear_wall_y+self.pool_buffer+self.pool_shell,
                self.pool_w,self.pool_d)

@dataclass
class Primitive:
    kind: str
    data: tuple
    layer: str='WALLS'
    color: str=INK
    width: float=.025
    fill: str|None=None
    dash: bool=False

@dataclass
class Drawing:
    key: str
    title: str
    box: tuple
    items: list=field(default_factory=list)
    rooms: list=field(default_factory=list)
    def line(self,x1,y1,x2,y2,layer='WALLS',color=INK,width=.025,dash=False):
        self.items.append(Primitive('line',(x1,y1,x2,y2),layer,color,width,None,dash))
    def poly(self,pts,layer='WALLS',color=INK,width=.025,fill=None,dash=False,closed=True):
        self.items.append(Primitive('poly',(tuple(pts),closed),layer,color,width,fill,dash))
    def rect(self,x,y,w,h,layer='WALLS',color=INK,width=.035,fill=None,dash=False):
        self.poly([(x,y),(x+w,y),(x+w,y+h),(x,y+h)],layer,color,width,fill,dash)
    def circle(self,x,y,r,layer='FURNITURE',color=MUTED,width=.018,fill=None):
        self.items.append(Primitive('circle',(x,y,r),layer,color,width,fill))
    def arc(self,x,y,r,a,b,layer='SWEPT_PATH',color=TEAL,width=.04,dash=True):
        self.items.append(Primitive('arc',(x,y,r,a,b),layer,color,width,None,dash))
    def text(self,x,y,txt,size=.28,color=INK,align='left',bold=False,layer='TEXT',rotate=0):
        self.items.append(Primitive('text',(x,y,str(txt),size,align,bold,rotate),layer,color))
    def arrow(self,x1,y1,x2,y2,color=TEAL,layer='PASSIVE_WIND_SUN',width=.055):
        self.line(x1,y1,x2,y2,layer,color,width)
        a=math.atan2(y2-y1,x2-x1); l=.32
        self.poly([(x2,y2),(x2-l*math.cos(a-.4),y2-l*math.sin(a-.4)),
                   (x2-l*math.cos(a+.4),y2-l*math.sin(a+.4))],layer,color,.01,color)
    def hatch(self,x,y,w,h,color=AMBER,layer='POOL_BUFFER',step=.22):
        self.rect(x,y,w,h,layer,color,.018,fill='#f2e7d2')
        t=-h
        while t < w:
            xa=max(0,t); xb=min(w,t+h)
            if xb>xa: self.line(x+xa,y+h-(xa-t),x+xb,y+h-(xb-t),layer,color,.011)
            t+=step
    def dimh(self,x1,x2,y,label=None,ext_y=None):
        self.line(x1,y,x2,y,'DIMENSIONS',MUTED,.013)
        for x in (x1,x2):
            self.line(x-.10,y+.13,x+.10,y-.13,'DIMENSIONS',MUTED,.02)
            if ext_y is not None:self.line(x,ext_y,x,y-.17 if ext_y>y else y+.17,'DIMENSIONS',MUTED,.01)
        self.text((x1+x2)/2,y-.12,label or f'{x2-x1:.2f} m',.28,MUTED,'center')
    def dimv(self,y1,y2,x,label=None,ext_x=None):
        self.line(x,y1,x,y2,'DIMENSIONS',MUTED,.013)
        for y in (y1,y2):
            self.line(x-.13,y+.10,x+.13,y-.10,'DIMENSIONS',MUTED,.02)
            if ext_x is not None:self.line(ext_x,y,x+.17,y,'DIMENSIONS',MUTED,.01)
        self.text(x-.16,(y1+y2)/2,label or f'{y2-y1:.2f} m',.28,MUTED,'center',rotate=90)
    def room(self,id,name,x,y,w,h,target=None,color=None,label=True):
        self.rect(x,y,w,h,color=MUTED,width=.025,fill=color)
        self.rooms.append(dict(id=id,name=name,x=x,y=y,w=w,h=h,area=w*h,target=target))
        if label:
            lines=name.split('|')
            for j,s in enumerate(lines): self.text(x+w/2,y+h/2+(j-(len(lines)-1)/2)*.40,s,.28,align='center',bold=True)
            self.text(x+w/2,y+h/2+(len(lines)+1)/2*.40,f'{w*h:.2f} m2',.24,MUTED,'center')
    def door(self,x,y,w=.85,side='right'):
        # Schematic door symbol, white mask opens an existing partition.
        self.line(x,y,x+w,y,'WALLS',PAPER,.10)
        self.line(x,y,x,y+w,'WALLS',INK,.025)
        self.arc(x,y,w,0,90,'WALLS',MUTED,.014,False)
    def door_v(self,x,y,w=.85):
        self.line(x,y,x,y+w,'WALLS',PAPER,.12)
        self.line(x,y,x-w,y,'WALLS',INK,.025)
        self.arc(x,y,w,90,180,'WALLS',MUTED,.014,False)
    def window(self,x1,y1,x2,y2):
        self.line(x1,y1,x2,y2,'GLAZING',PAPER,.11)
        self.line(x1,y1,x2,y2,'GLAZING',TEAL,.04)
        if abs(y2-y1)<.01:self.line(x1,y1+.10,x2,y2+.10,'GLAZING',TEAL,.018)
        else:self.line(x1+.10,y1,x2+.10,y2,'GLAZING',TEAL,.018)
    def bed(self,x,y,w=1.60,h=2.0):
        self.rect(x,y,w,h,'FURNITURE',MUTED,.02)
        self.rect(x+.08,y+.08,w/2-.12,.38,'FURNITURE',MUTED,.012)
        self.rect(x+w/2+.04,y+.08,w/2-.12,.38,'FURNITURE',MUTED,.012)
        self.line(x,y+.57,x+w,y+.57,'FURNITURE',MUTED,.012)
    def sofa(self,x,y,w=2.2,h=.8):
        self.rect(x,y,w,h,'FURNITURE',MUTED,.02)
        self.line(x+.12,y+.18,x+w-.12,y+.18,'FURNITURE',MUTED,.012)
        self.line(x+w/2,y+.18,x+w/2,y+h,'FURNITURE',MUTED,.012)


def site(d,p,diagonal=False,context=True):
    if context:
        d.rect(0,-1.25,p.plot_w,1.25,'SITE_BOUNDARY',MUTED,.012,GRAY)
        d.text(p.plot_w/2,-.67,f'NORTH / {p.road_w:.2f} m MAIN ROAD',.33,align='center',bold=True)
        d.text(p.plot_w+1.18,p.plot_d/2,f'EAST / {p.spine_w:.2f} m PEDESTRIAN SPINE',.30,MUTED,'center',rotate=90)
        d.text(-1.25,p.plot_d/2,'WEST / NEIGHBOR PLOT 84',.28,MUTED,'center',rotate=90)
        d.text(p.plot_w/2,p.plot_d+.73,'SOUTH / NEIGHBOR PLOT 10',.30,MUTED,'center')
    d.rect(0,0,p.plot_w,p.plot_d,'SITE_BOUNDARY',INK,.055)
    for x,y,name,dx,dy in [(0,0,'P4',-.48,-.1),(p.plot_w,0,'P1',.15,-.1),(0,p.plot_d,'P3',-.48,.3),(p.plot_w,p.plot_d,'P2',.15,.3)]:
        d.circle(x,y,.065,'SITE_BOUNDARY',INK,fill=INK);d.text(x+dx,y+dy,name,.25,bold=True)
    d.line(p.west_setback,0,p.west_setback,p.plot_d,'DIMENSIONS',MUTED,.018,True)
    d.line(0,p.plot_d-p.rear_setback,p.plot_w,p.plot_d-p.rear_setback,'DIMENSIONS',MUTED,.018,True)
    d.dimh(0,p.plot_w,-1.8,ext_y=0);d.dimv(0,p.plot_d,-2.0,ext_x=0)
    d.dimh(0,p.west_setback,26.3,f'{p.west_setback:.2f} setback')
    d.dimv(p.plot_d-p.rear_setback,p.plot_d,18.95,f'{p.rear_setback:.2f} rear')
    if diagonal:
        d.line(0,0,p.plot_w,p.plot_d,'DIMENSIONS',MUTED,.014,True)
        d.text(5.5,10.6,f'P4-P2 {math.hypot(p.plot_w,p.plot_d):.4f} m',.25,MUTED)
    d.arrow(19.0,2.3,19.0,.4,INK,'DIMENSIONS',.025); d.text(19,0,'N',.4,align='center',bold=True)
    for i in range(5):d.rect(i*1.0,27.2,1.0,.13,'DIMENSIONS',INK,.01,INK if i%2==0 else PAPER)
    d.text(0,27.75,'0',.22);d.text(5,27.75,'5 m',.22,align='right')


def pool_plan(d,p,buffer=True):
    x,y,w,h=p.pool;s=p.pool_shell
    d.rect(x-s,y-s,w+2*s,h+2*s,'WALLS',INK,.04,GRAY)
    d.rect(x,y,w,h,'WALLS',TEAL,.035,WATER)
    for i in range(1,6):d.line(x+.15,y+i*h/6,x+w-.15,y+i*h/6,'FURNITURE','#a6cbd0',.012)
    d.text(x+w/2,y+h/2,'OPEN-AIR POOL',.29,TEAL,'center',True)
    d.text(x+w/2,y+h/2+.42,f'{h:.2f} x {w:.2f} m clear water',.24,TEAL,'center')
    d.dimh(x,x+w,y+h+.56,f'{w:.2f} m',ext_y=y+h)
    if buffer:
        d.hatch(x-s,p.rear_wall_y,w+2*s,p.pool_buffer)
        d.dimh(x-s,x+w+s,p.rear_wall_y+.8,'BACKFILL + INSULATION')
        d.dimv(p.rear_wall_y,y-s,x+w+s+.45,f'{p.pool_buffer:.2f} m')
    for x0,y0 in [(4.5,22.1),(6.7,23.7),(2.1,23.2)]:
        d.circle(x0,y0,.65,'LANDSCAPE','#82937b',.02,LIGHT);d.circle(x0,y0,.16,'LANDSCAPE','#82937b',.01)
    d.text(5.6,24.75,'LANDSCAPED GARDEN',.24,MUTED,'center')


def ramp(d,p):
    d.rect(0,0,p.ramp_width,p.ramp_run,'RAMP',AMBER,.045,'#f1e6d7')
    for y in range(1,math.ceil(p.ramp_run)):d.line(.15,y,p.ramp_width-.15,y,'RAMP',AMBER,.012)
    d.arrow(p.ramp_width/2,2,p.ramp_width/2,p.ramp_run-1,AMBER,'RAMP')
    d.text(1.35,12.7,f'{p.ramp_grade:.0%} RAMP / RUN {p.ramp_run:.3f} m',.31,AMBER,'center',rotate=90)
    d.dimh(0,p.ramp_width,1.0,f'{p.ramp_width:.2f} m clear*')
    d.text(p.ramp_width/2,p.ramp_run+.65,f'{p.basement_z:+.2f}',.3,AMBER,'center',True)
    d.text(1.75,22.5,'NO LANDING',.22,RED,'center',True)
    d.rect(0,p.ramp_run,p.ramp_width,p.plot_d-p.ramp_run,'ISSUES',RED,.04,dash=True)


def core(d,p,x=None,y=None,compact=False):
    x=p.gf_x if x is None else x;y=p.front_y if y is None else y
    w=4.85;h=5.65
    d.rect(x,y,w,h,'CORE',INK,.065,GRAY)
    # 2 x 1.10 m clear flights, 0.20 spine. 20 risers / typical storey.
    sx=x+.25;sy=y+.25;fw=1.1;gap=.20;run=2.7;landing=1.2
    for xx in (sx,sx+fw+gap):
        d.rect(xx,sy,fw,run+2*landing,'CORE',INK,.025,PAPER)
        for j in range(10):d.line(xx,sy+landing+j*.30,xx+fw,sy+landing+j*.30,'CORE',MUTED,.016)
    d.arrow(sx+.55,sy+4.1,sx+.55,sy+1.4,INK,'CORE',.025)
    d.arrow(sx+fw+gap+.55,sy+1.4,sx+fw+gap+.55,sy+4.1,INK,'CORE',.025)
    ex=sx+2*fw+gap+.20;ey=sy
    d.rect(ex,ey,1.75,2.0,'CORE',INK,.05,PAPER)
    d.line(ex,ey,ex+1.75,ey+2,'CORE',MUTED,.013)
    d.line(ex+1.75,ey,ex,ey+2,'CORE',MUTED,.013)
    d.text(ex+.875,ey+1.15,'LIFT',.25,align='center',bold=True)
    d.text(ex+.875,ey+3.15,'LOBBY',.25,align='center',bold=True)
    d.text(ex+.875,ey+3.55,'B CORE',.23,MUTED,'center')
    d.door_v(x+w,y+3.35,.85)


def car(d,x,y,w,l,number):
    d.rect(x,y,w,l,'FURNITURE',MUTED,.018,'#ecece5')
    d.rect(x+.13,y+.75,w-.26,l-1.6,'FURNITURE',MUTED,.014)
    d.line(x+.13,y+1.05,x+w-.13,y+1.05,'FURNITURE',MUTED,.014)
    d.line(x+.13,y+l-.9,x+w-.13,y+l-.9,'FURNITURE',MUTED,.014)
    d.text(x+w/2,y+l/2+.16,str(number),.42,INK,'center',True)


def basement(p):
    d=Drawing('plan_basement_sweptpath',f'B1 / BASEMENT {p.basement_z:+.2f} m',(-2.8,-2.7,23,31.3))
    site(d,p);ramp(d,p)
    x0=p.ramp_width;right=p.plot_w-p.wall;sy=p.wall
    d.rect(x0,0,p.plot_w-x0,p.rear_wall_y,'WALLS',INK,.09)
    bx=right-3*p.bay_w; aisle_y=sy+p.bay_d
    for j in range(2):
        by=sy if j==0 else aisle_y+p.aisle
        for i in range(3):
            xx=bx+i*p.bay_w
            d.rect(xx,by,p.bay_w,p.bay_d,'DIMENSIONS',MUTED,.018)
            car(d,xx+(p.bay_w-p.car_w)/2,by+(p.bay_d-p.car_l)/2,p.car_w,p.car_l,j*3+i+1)
    d.rect(bx,aisle_y,3*p.bay_w,p.aisle,'AREA_BOUNDARY',MUTED,.012,fill='#edf2ed')
    d.text(bx+3*p.bay_w/2,aisle_y+2.6,'6-CAR GARAGE',.39,align='center',bold=True)
    d.text(bx+3*p.bay_w/2,aisle_y+3.1,f'{p.bay_w:.2f} x {p.bay_d:.2f} m compact stalls',.25,MUTED,'center')
    d.dimv(aisle_y,aisle_y+p.aisle,right+.25,f'{p.aisle:.2f} m CLEAR')
    cx=right-p.outer_r;cy=aisle_y+p.aisle
    for r,c in [(p.inner_r,TEAL),(p.outer_r,AMBER)]:d.arc(cx,cy,r,-90,0,color=c,width=.045)
    d.text(bx+.2,aisle_y+.65,f'Ri {p.inner_r:.2f} / Ro {p.outer_r:.2f}',.30,TEAL,bold=True)
    d.text(bx+.2,aisle_y+5.45,'ANNULAR TEMPLATE / NOT FULL VEHICLE TRACK',.205,MUTED)
    # Kinematic reference fails the connection; do not disguise it as a pass.
    d.arc(p.ramp_width,p.ramp_run,p.outer_r,-90,0,'ISSUES',RED,.035,True)
    d.text(3.8,21.1,'RAMP LINK UNRESOLVED',.28,RED,bold=True)
    core(d,p)
    sx=x0+p.wall; sw=4.35; right_service=sx+sw
    family_y=p.rear_wall_y-p.wall-p.family_area/8.0
    d.room('B-FAM','FAMILY|SITTING',right-8,family_y,8,p.family_area/8,p.family_area,LIGHT)
    d.sofa(right-7.6,family_y+.3,2.5);d.sofa(right-3.2,family_y+.3,2.5)
    d.window(right-7.7,p.rear_wall_y,right-.25,p.rear_wall_y)
    d.arrow(right-4.0,p.rear_wall_y-.6,right-4.0,p.rear_wall_y+1.2,TEAL)
    y=p.rear_wall_y-p.wall-p.gym_area/sw
    d.room('B-GYM','PRIVATE GYM',sx,y,sw,p.gym_area/sw,p.gym_area)
    d.rect(sx+.2,y+.2,.65,1.55,'FURNITURE',MUTED,.02)
    d.circle(sx+sw-.6,y+.6,.35)
    y-=p.partition+p.kitchenette_area/sw
    d.room('B-KIT','KITCHENETTE',sx,y,sw,p.kitchenette_area/sw,p.kitchenette_area)
    d.rect(sx+.1,y+.1,.6,p.kitchenette_area/sw-.2,'FURNITURE',MUTED,.018)
    y-=p.partition+p.storage_area/sw
    d.room('B-STO','STORAGE',sx,y,sw,p.storage_area/sw,p.storage_area)
    y-=p.partition+2.0
    bw=(sw-p.partition)/2
    d.room('B-WC1','WC 1',sx,y,bw,2)
    d.room('B-WC2','WC 2',sx+bw+p.partition,y,bw,2)
    uy=p.wall;uh=p.front_y-p.wall-p.partition
    d.room('B-ELEC','ELECTRICAL',sx,uy,sw,(uh-p.partition)/2)
    d.room('B-PUMP','WATER PUMP',sx,uy+(uh+p.partition)/2,sw,(uh-p.partition)/2)
    for rm in d.rooms:
        if rm['id'].startswith('B-') and rm['id']!='B-FAM':
            # Side opening into continuous service circulation, shown at east edge.
            xx=rm['x']+rm['w'];yy=rm['y']+rm['h']*.45
            d.line(xx,yy,xx,yy+.75,'WALLS',PAPER,.10);d.line(xx,yy,xx-.75,yy,'WALLS',INK,.02)
    d.door_v(right-8,family_y+.7,.95)
    d.text(8.85,12.2,'SERVICE ACCESS',.23,MUTED,'center',rotate=90)
    # Perimeter piers only; no columns inside marked parking aisle.
    for xx,yy in [(x0,0),(p.plot_w-.25,0),(p.plot_w-.25,15.2),(x0,p.rear_wall_y-.3)]:
        d.rect(xx,yy,.25,.30,'COLUMNS',INK,.018,INK)
    pool_plan(d,p)
    d.text(6,26.45,'Pool shell 200 mm / independent foundation',.25,MUTED)
    return d


def ground(p):
    d=Drawing('plan_ground',f'00 / GROUND {p.ground_z:+.2f} m',(-2.8,-2.7,23,31.3));site(d,p)
    ramp(d,p);pool_plan(d,p)
    x,y,w,h=p.gf_x,p.front_y,p.gf_w,p.floor_depth
    d.rect(x,y,w,h,'AREA_BOUNDARY',INK,.09)
    core(d,p)
    left=x+p.wall; east=x+w-p.wall; y0=y+p.wall; core_right=x+4.85
    rx=core_right+.25;rh=5.15
    d.room('G-SALON','NORTH RECEPTION|& SALON',rx,y0,east-rx,rh,color=LIGHT)
    d.sofa(rx+.3,y0+.3,2.6);d.sofa(east-1.2,y0+1.5,.8,2.2)
    d.window(rx+.35,y,east-.35,y)
    kitchen_y=y+5.95
    d.room('G-KIT','KITCHEN',left,kitchen_y,4.35,4.0)
    d.rect(left+.1,kitchen_y+.15,.6,3.65,'FURNITURE',MUTED,.02)
    d.room('G-BATH','BATH',left,kitchen_y+4.2,2.4,2.4)
    d.room('G-SERVICE','SERVICE|LOBBY',left+2.6,kitchen_y+4.2,1.75,2.4)
    d.room('G-DINE','DINING',rx,y0+5.4,east-rx,4.1,color=LIGHT)
    d.rect(rx+1,y0+6.55,2.6,1.0,'FURNITURE',MUTED,.025)
    for xx in (rx+1.3,rx+2.3,rx+3.3):
        for yy in (y0+6.25,y0+7.85):d.circle(xx,yy,.18)
    vy=kitchen_y+6.85
    d.room('G-VER','GARDEN VERANDA|ENCLOSED IN 50%',left,vy,east-left,p.rear_wall_y-p.wall-vy,color=LIGHT)
    d.window(left+.5,p.rear_wall_y,east-.3,p.rear_wall_y)
    d.window(x+w,y+10,x+w,p.rear_wall_y-1)
    for wx in (x,x+w):d.window(wx,y+6.5,wx,y+9.3)
    d.door(rx,y,.95)
    d.door_v(left+4.35,kitchen_y+1.2,.9)
    d.door_v(left+2.4,kitchen_y+4.8,.8)
    d.door_v(left+4.35,kitchen_y+4.8,.8)
    d.door_v(rx,y0+1.6,.9)
    d.door_v(rx,y0+6.5,.9)
    d.door(left+5.2,vy,1.2)
    d.arrow(rx+.4,1.1,rx+.4,y-.15,INK,'DIMENSIONS')
    d.text(rx+1.2,1.1,'MAIN ENTRY',.28,align='center',bold=True)
    for yy in (kitchen_y+1.4,vy+1):
        d.line(core_right,yy,rx,yy,'WALLS',PAPER,.9)
    d.dimh(x,x+w,y-1.0,f'{w:.2f} m / {w*h:.2f} m2 GROSS')
    return d


def typical(p):
    d=Drawing('plan_typical','01-03 / TYPICAL '+ ' / '.join(f'{z:+.2f}' for z in p.levels[2:5])+' m',(-2.8,-2.7,23,31.3));site(d,p)
    x,y,w,h=p.tf_x,p.front_y,p.tf_w,p.floor_depth;east=x+w-p.wall
    d.rect(x,y,w,h,'AREA_BOUNDARY',INK,.09)
    d.rect(p.gf_x,y,p.gf_w,h,'DIMENSIONS',MUTED,.018,dash=True)
    core(d,p)
    rx=p.gf_x+4.85+.2;rw=east-rx;ry=y+p.wall;rh=p.reception_area/rw
    d.room('T-REC','GRAND RECEPTION|LIVING / DINING',rx,ry,rw,rh,p.reception_area,LIGHT)
    d.sofa(rx+.3,ry+.25,2.7);d.sofa(east-1.05,ry+.5,.8,2.5)
    d.rect(rx+.9,ry+rh-1.75,2.6,.95,'FURNITURE',MUTED,.018)
    d.window(rx+.3,y,east-.3,y)
    sx=x+p.wall;sy=y+5.9;kw=4.0;kh=p.kitchen_area/kw
    d.room('T-KIT','KITCHEN',sx,sy,kw,kh,p.kitchen_area)
    d.rect(sx+.1,sy+.1,.6,kh-.2,'FURNITURE',MUTED,.02)
    d.door_v(sx+kw,sy+1.2,.9)
    bath_y=sy+kh+p.partition
    bath_depth=(p.rear_wall_y-p.wall-bath_y-2*p.partition)/3
    for i in range(3):
        yy=bath_y+i*(bath_depth+p.partition)
        d.room('T-WC'+str(i+1),'BATH '+str(i+1),sx,yy,2.25,bath_depth)
        d.circle(sx+.45,yy+.45,.19)
        d.window(x,yy+.5,x,yy+1.3)
        d.door_v(sx+2.25,yy+.45,.75)
    d.room('T-LAUN','LAUNDRY',sx+2.45,p.rear_wall_y-p.wall-2.2,1.55,2.2)
    d.circle(sx+2.85,p.rear_wall_y-p.wall-1.5,.24)
    # Three true east-facing room polygons, with a 1.45 m circulation strip.
    bed_x=rx+1.45;bed_w=east-bed_x;bed_y=ry+rh+p.partition
    bh=(p.rear_wall_y-p.wall-bed_y-2*p.partition)/3
    for i,name in enumerate(['BEDROOM 02','BEDROOM 03','MASTER SUITE']):
        yy=bed_y+i*(bh+p.partition)
        d.room('T-BED'+str(i+1),name,bed_x,yy,bed_w,bh,color='#edf1e9')
        d.bed(east-1.9,yy+.25,1.6,min(2.0,bh-.35))
        d.window(x+w,yy+.4,x+w,yy+bh-.4)
        d.door_v(bed_x,yy+.50,.85)
    d.text(rx+.55,bed_y+(p.rear_wall_y-bed_y)/2,'PRIVATE HALL',.25,MUTED,'center',rotate=90)
    d.text(sx+3.3,bath_y+1.7,'SERVICE HALL',.23,MUTED,'center',rotate=90)
    d.door(rx,ry+rh,.9)
    # Perforated west screen is offset from external wall.
    for j in range(32):
        yy=y+.2+j*(h-.4)/32
        d.line(x-.16,yy,x-.16,yy+.23,'PASSIVE_WIND_SUN',AMBER,.065)
    d.text(1.55,10.5,'WEST SOLAR SCREEN',.27,AMBER,'center',rotate=90)
    d.window(x,sy+.5,x,sy+kh-.4)
    d.arrow(12,-.05,12,y+2.4)
    d.arrow(12,y+2.4,10.0,y+6.7)
    d.arrow(10,y+6.7,7.6,y+9)
    d.arrow(7.6,y+9,x-.5,y+9)
    d.dimh(x,x+w,y-.85,f'{w:.2f} m / {w*h:.2f} m2 GROSS')
    d.text(8.5,23.2,'3 FLOORS / ONE APARTMENT EACH',.38,align='center',bold=True)
    d.text(8.5,23.8,'East bedrooms / west services / north living',.28,MUTED,'center')
    d.text(8.5,24.45,'Master-suite bath via private service hall; doors schematic',.23,MUTED,'center')
    return d


def roof(p):
    d=Drawing('plan_roof',f'R / ROOF {p.levels[-1]:+.2f} m',(-2.8,-2.7,23,31.3));site(d,p)
    x,y=p.gf_x,p.front_y;w=p.rf_w;h=p.roof_depth
    d.rect(p.tf_x,y,p.tf_w,p.floor_depth,'DIMENSIONS',MUTED,.03,fill='#edf1e9')
    d.rect(x,y,w,h,'AREA_BOUNDARY',INK,.075,fill=PAPER)
    core(d,p)
    rx=x+5.05;rw=w-5.30
    d.room('R-GREY','GREYWATER|RECYCLING',rx,y+.25,rw,3.2)
    d.room('R-WASTE','SORTING +|CHUTE ROOM',rx,y+3.65,rw,2.8)
    d.room('R-SERVICE','SERVICE / PLANT',x+.25,y+6.65,w-.5,3.10)
    for i in range(3):
        d.circle(rx+.5+i*.65,y+1.0,.24,'FURNITURE',TEAL,.02)
        d.rect(rx+.4+i*.7,y+4.1,.5,.65,'FURNITURE',INK,.02,LIGHT)
    for i in range(4):
        for j in range(2):d.rect(x+.3+i*2.5,y+h+.9+j*1.55,2.3,1.35,'PASSIVE_WIND_SUN',TEAL,.025,'#bdd3d2')
    d.text(8.5,y+h+4.5,'PV PERGOLA / 8 MODULE RESERVATIONS',.27,TEAL,'center',True)
    d.text(8.5,y+h+5,'Pergola counted area subject to authority',.24,MUTED,'center')
    for xx in (x+1,x+w-1):
        d.circle(xx,y+h+.35,.25,'PASSIVE_WIND_SUN',TEAL,.03)
        d.arrow(xx,y+h+.3,xx,y+h-1.1)
    d.text(8.5,23,'LANDSCAPED ROOF TERRACE',.37,align='center',bold=True)
    d.text(8.5,23.65,'Cowls: extract wet rooms; clean wind inlet separate',.25,MUTED,'center')
    d.dimh(x,x+w,y-.85,f'{w:.3f} x {h:.2f} = {w*h:.2f} m2')
    return d


def section(p):
    d=Drawing('section_aa','A-A / NORTH-SOUTH ENVIRONMENTAL SECTION',(-2.7,-17.8,32,24.5))
    # x is north-south distance; y is negative elevation.
    x1=p.front_y;x2=p.rear_wall_y;bw=x2-x1;z=p.levels
    d.line(-.7,0,p.plot_d+1,0,'SITE_BOUNDARY',INK,.055)
    d.text(0,1.0,'N / ROAD',.33,align='center',bold=True)
    d.text(p.plot_d,1.0,'S / PLOT 10',.33,align='center',bold=True)
    d.rect(x1,-p.ground_z,bw,p.ground_z-p.basement_z,'WALLS',INK,.07,fill='#ecebe4')
    for i in range(1,5):
        floor=z[i];ceil=z[i+1]
        d.rect(x1,-ceil,bw,ceil-floor,'WALLS',INK,.065,fill=PAPER)
        d.rect(x1,-floor,bw,.22,'WALLS',INK,.02,fill=GRAY)
        d.line(x1,-floor-.5,x1,-ceil+.6,'GLAZING',TEAL,.05)
        d.line(x2,-floor-.5,x2,-ceil+.6,'GLAZING',TEAL,.05)
        mid=-(floor+ceil)/2
        d.arrow(x1-1.3,mid,x1+4,mid,TEAL)
        d.arrow(x1+4,mid,x2-1.0,mid-.35,TEAL)
        d.text(x1+bw/2,mid+.65,'NORTH INLET  >  OCCUPIED ROOMS  >  HIGH OUTLET',.25,MUTED,'center')
    rfz=z[-1];rh=3.0
    d.rect(x1,-rfz-rh,p.roof_depth,rh,'WALLS',INK,.065,PAPER)
    d.text(x1+p.roof_depth/2,-rfz-1.2,'ROOF SERVICES',.35,align='center',bold=True)
    d.line(x1+11,-rfz-1.0,x2,-rfz-1.9,'PASSIVE_WIND_SUN',TEAL,.12)
    d.text(x1+13,-rfz-2.25,'PV PERGOLA',.30,TEAL,'center',True)
    stack_x=x1+1.1
    d.rect(stack_x,-rfz-3.65,.65,rfz-p.basement_z+3.65,'PASSIVE_WIND_SUN',TEAL,.025)
    d.arrow(stack_x+.325,-rfz+1,stack_x+.325,-rfz-3.55,TEAL)
    d.text(stack_x+1.2,-rfz-3.25,'STACK EXTRACT COWL',.27,TEAL)
    d.text(x1+4,1.6,'BASEMENT FAMILY / GLAZING',.34,bold=True)
    d.text(x1+4,2.2,'Lower courtyard overlook / depressed open-air pool',.28,MUTED)
    d.line(x2,1.25,x2,3.0,'GLAZING',TEAL,.065)
    # Independent pool shell & earth separation. Water level deliberately below ground.
    py=p.pool[1];outer_n=py-p.pool_shell
    d.hatch(x2,0,p.pool_buffer,-p.basement_z,AMBER)
    d.rect(outer_n,-p.pool_water_z,p.pool_d+2*p.pool_shell,p.pool_depth+p.pool_shell,'WALLS',INK,.06,GRAY)
    d.rect(py,-p.pool_water_z,p.pool_d,p.pool_depth,'WALLS',TEAL,.025,WATER)
    d.line(outer_n,0,outer_n,-p.pool_water_z,'WALLS',INK,.045)
    d.line(py+p.pool_d+p.pool_shell,0,py+p.pool_d+p.pool_shell,-p.pool_water_z,'WALLS',INK,.045)
    d.dimh(x2,outer_n,4.2,f'{p.pool_buffer:.2f} m BACKFILL')
    d.dimh(py,py+p.pool_d,5.3,f'{p.pool_d:.2f} m POOL WATER')
    d.text(26.2,2.1,'Water -1.80',.28,TEAL)
    d.text(26.2,2.65,'Base -3.00',.28,TEAL)
    d.text(26.2,3.2,'Separate shell',.28,TEAL)
    d.text(26.2,3.75,'Drain + insulation',.25,AMBER)
    # Sightline test: seated eye at -2m is blocked by backfill; record explicitly.
    d.line(x2-3,2.0,py+1.5,1.8,'ISSUES',RED,.025,True)
    d.text(x1+4,3.05,'Seated sightline blocked by 1.50 m earth buffer',.28,RED)
    for i,lev in enumerate(z):
        tag=['B1','G','01','02','03','R'][i]
        d.line(-.15,-lev,x1-.2,-lev,'DIMENSIONS',MUTED,.014)
        d.text(-.2,-lev-.12,f'{tag} {lev:+.2f}',.29,INK,'right',True)
    d.dimv(-z[-1],-z[1],27.3,'4 x 3.30 m = 13.20 m')
    d.text(14,6.0,'SECTION A-A: schematic structure; no certified spans, fire or MEP sizing',.27,MUTED,'center')
    return d


def passive(p):
    d=Drawing('passive_sun_wind_diagram','P / PASSIVE SOLAR + WIND STUDY',(-9,-9,18,19))
    # Compass sun path: calculated horizon azimuth at solstices, north-up.
    cx=0;cy=-.8;r=6.2
    for rad in (2.1,4.15,6.2):d.circle(cx,cy,rad,'PASSIVE_WIND_SUN','#b8c4bd',.018)
    for a,name in [(0,'N'),(90,'E'),(180,'S'),(270,'W')]:
        aa=math.radians(a);xx=cx+7*math.sin(aa);yy=cy-7*math.cos(aa)
        d.text(xx,yy+.15,name,.5,INK,'center',True)
        d.line(cx,cy,xx*.9,cy+(yy-cy)*.9,'DIMENSIONS',MUTED,.012)
    for dec,color,label in [(23.44,AMBER,'SUMMER'),(0,'#b28b50','EQUINOX'),(-23.44,'#806449','WINTER')]:
        sunrise=math.degrees(math.acos(math.sin(math.radians(dec))/math.cos(math.radians(p.latitude))))
        # Polar sky plot radius = (90-altitude)/90 * outer radius.
        points=[]
        for k in range(81):
            H0=math.acos(-math.tan(math.radians(p.latitude))*math.tan(math.radians(dec)))
            H=-H0+2*H0*k/80
            alt=math.asin(math.sin(math.radians(p.latitude))*math.sin(math.radians(dec))+math.cos(math.radians(p.latitude))*math.cos(math.radians(dec))*math.cos(H))
            az=math.atan2(math.sin(H),math.cos(H)*math.sin(math.radians(p.latitude))-math.tan(math.radians(dec))*math.cos(math.radians(p.latitude)))+math.pi
            rr=(math.pi/2-alt)/(math.pi/2)*r
            points.append((rr*math.sin(az),cy-rr*math.cos(az)))
        d.poly(points,'PASSIVE_WIND_SUN',color,.045,closed=False)
        d.text(points[61][0]+.25,points[61][1]-.18,label,.27,color,'left',True)
    d.rect(-1.1,-2.1,2.2,2.7,'WALLS',INK,.04,LIGHT)
    d.text(0,-.75,'83',.65,INK,'center',True)
    for a in (0,315,330):
        aa=math.radians(a)
        x1=5.7*math.sin(aa);y1=cy-5.7*math.cos(aa)
        x2=2.6*math.sin(aa);y2=cy-2.6*math.cos(aa)
        d.arrow(x1,y1,x2,y2,TEAL,width=.085)
    d.text(-7.8,-7.9,'N / NW BREEZE',.35,TEAL,bold=True)
    d.text(-7.8,7.15,f'New Cairo latitude assumption: {p.latitude:.2f} N / true north',.30,MUTED)
    for i,(label,dec) in enumerate([('Jun',23.44),('Mar/Sep',0),('Dec',-23.44)]):
        alt=90-abs(p.latitude-dec)
        d.text(-7.8+i*5.4,7.85,f'{label}: noon {alt:.2f} deg',.29,AMBER,bold=True)
    d.text(-7.8,8.65,'Directional wind study only; no measured frequency / wind-rose dataset.',.26,MUTED)
    d.text(-7.8,9.25,'West mashrabiya + east morning light + north cross-ventilation.',.27,INK)
    return d


def cores(p):
    d=Drawing('core_options_comparison','C / CORE ALTERNATIVES AT THE SAME SCALE',(-.5,-1.7,15,12))
    ax=0;ay=0;aw=6.0;ah=6.2
    d.text(0,-.65,'A / WRAPPED LIFT',.44,bold=True)
    d.rect(ax,ay,aw,ah,'CORE',INK,.07,GRAY)
    d.rect(2.1,2.1,1.8,2.0,'CORE',INK,.06,PAPER)
    d.text(3,3.3,'LIFT',.30,align='center',bold=True)
    for j in range(11):
        t=.3+j*.30
        d.line(.25,t,1.45,t,'CORE',MUTED,.018)
        d.line(4.55,t+2.2,5.75,t+2.2,'CORE',MUTED,.018)
        d.line(t+1.2,.25,t+1.2,1.45,'CORE',MUTED,.018)
    d.arrow(.85,4.7,.85,1.7,INK,'CORE',.025)
    d.arrow(1.7,.85,4.2,.85,INK,'CORE',.025)
    d.arrow(5.15,1.6,5.15,4.8,INK,'CORE',.025)
    bx=8;by=0;bw=4.85;bh=5.65
    d.text(bx,-.65,'B / ADJACENT U-STAIR',.44,TEAL,bold=True)
    core(d,p,bx,by)
    d.dimh(0,aw,6.7,f'{aw:.2f} m');d.dimh(bx,bx+bw,6.7,f'{bw:.2f} m')
    a=aw*ah;b=bw*bh;gross=p.land*p.typical_ratio
    ea=(gross-a)/gross;eb=(gross-b)/gross
    d.text(0,7.4,f'A core reservation: {a:.2f} m2',.32,bold=True)
    d.text(bx,7.4,f'B core reservation: {b:.2f} m2',.32,TEAL,bold=True)
    d.text(0,8.0,'Multi-direction landings / more wall returns',.27,MUTED)
    d.text(bx,8.0,'SELECTED / aligned shear-wall concept',.27,TEAL)
    d.text(0,8.65,f'Core-excluded gross proxy: A {ea:.2%} / B {eb:.2%} / relative gain {(eb/ea-1):.2%}',.29,bold=True)
    d.text(0,9.25,'14% NET-TO-GROSS GAIN IS A REQUESTED TARGET, NOT VERIFIED.',.31,AMBER,bold=True)
    d.text(0,9.8,'Identical gross denominator; partition, riser and wall deductions not included.',.26,MUTED)
    return d


def schedule_drawing(p,issues):
    d=Drawing('area_and_constraints','S / AREA SCHEDULE + DESIGN HOLD POINTS',(0,0,28,20))
    d.text(.5,1,'AREA / GROSS ENCLOSED FOOTPRINT',.60,bold=True)
    rows=[('LAND',1,p.land,1),('GROUND',1,p.land*p.ground_ratio,p.ground_ratio),('TYPICAL',3,p.land*p.typical_ratio,p.typical_ratio),('ROOF',1,p.land*p.roof_ratio,p.roof_ratio)]
    for j,(name,n,a,r) in enumerate(rows):
        yy=2.5+j*1.05
        d.text(.5,yy,name,.40,bold=True);d.text(7,yy,f'{n} x {a:.2f} m2',.40);d.text(15,yy,f'{r:.0%} of land',.40)
        d.line(.5,yy+.3,26,yy+.3,'DIMENSIONS',MUTED,.018)
    total=p.land*(p.ground_ratio+3*p.typical_ratio+p.roof_ratio)
    d.text(.5,7.1,f'TOTAL ABOVE GROUND: {total:.2f} m2 / basement excluded',.47,bold=True)
    d.text(.5,8.2,'HOLD POINTS / DO NOT ISSUE FOR CONSTRUCTION',.47,AMBER,bold=True)
    for i,issue in enumerate(issues):
        yy=9.25+i*1.22
        d.text(.5,yy,issue['id']+' / '+issue['title'],.36,RED,bold=True)
        d.text(.5,yy+.48,issue['short'],.29,MUTED)
    return d


def rgb(s):return tuple(int(s[i:i+2],16)/255 for i in (1,3,5))
def arc_points(dat,n=65):
    x,y,r,a,b=dat
    return [(x+r*math.cos(math.radians(a+(b-a)*i/(n-1))),y+r*math.sin(math.radians(a+(b-a)*i/(n-1)))) for i in range(n)]


def svg(d,path):
    """Render one vector PDF page then outline its glyphs into SVG paths."""
    doc=fitz.open();page=doc.new_page(width=d.box[2]*40,height=d.box[3]*40)
    draw_pdf(page,d,fitz.Rect(0,0,page.rect.width,page.rect.height),background=False)
    result=page.get_svg_image(text_as_path=True)
    # Keep machine-readable metadata without reintroducing visible text elements.
    desc=html.escape(d.title+' | schematic study, not construction approval')
    result=result.replace('>',f'><title>{desc}</title>',1)
    path.write_text(result,encoding='utf-8');doc.close()


def draw_pdf(page,d,target,background=True):
    x0,y0,w,h=d.box;s=min(target.width/w,target.height/h)
    ox=target.x0+(target.width-w*s)/2-x0*s;oy=target.y0+(target.height-h*s)/2-y0*s
    def pt(x,y):return fitz.Point(ox+x*s,oy+y*s)
    if background:page.draw_rect(target,color=None,fill=rgb(PAPER),overlay=False)
    for z in d.items:
        c=rgb(z.color);fill=rgb(z.fill) if z.fill else None
        width=max(.12,z.width*s);dash=f'[{.14*s:.3f} {.10*s:.3f}] 0' if z.dash else None
        if z.kind=='text':
            x,y,txt,sz,align,bold,rotation=z.data;font='hebo' if bold else 'helv';fs=sz*s
            tw=fitz.get_text_length(txt,fontname=font,fontsize=fs)
            pp=pt(x,y)
            if rotation==0:
                if align=='center':pp.x-=tw/2
                elif align=='right':pp.x-=tw
            else:
                if align=='center':pp.y+=tw/2
                elif align=='right':pp.y+=tw
            page.insert_text(pp,txt,fontname=font,fontsize=fs,color=c,rotate=rotation)
            continue
        sh=page.new_shape()
        if z.kind=='line':
            x1,y1,x2,y2=z.data;sh.draw_line(pt(x1,y1),pt(x2,y2))
        elif z.kind=='circle':
            x,y,r=z.data;sh.draw_circle(pt(x,y),r*s)
        elif z.kind=='arc':
            sh.draw_polyline([pt(x,y) for x,y in arc_points(z.data)])
        else:
            points,closed=z.data;sh.draw_polyline([pt(x,y) for x,y in points]+([pt(*points[0])] if closed else []))
        sh.finish(color=c,fill=fill,width=width,dashes=dash,closePath=False);sh.commit()


def export_pdf(drawings,p,out):
    doc=fitz.open();W=1190.551;H=841.89 # A3 landscape points
    for i,d in enumerate(drawings):
        page=doc.new_page(width=W,height=H);page.draw_rect(page.rect,fill=rgb(PAPER),color=None)
        page.insert_text((34,39),'PLOT 83 / NEW CAIRO',fontsize=21,fontname='hebo',color=rgb(INK))
        page.insert_text((34,61),d.title,fontsize=12,fontname='hebo',color=rgb(INK))
        page.insert_text((815,39),'SCHEMATIC / CONSTRAINT STUDY',fontsize=11,fontname='hebo',color=rgb(AMBER))
        page.draw_line((34,75),(W-34,75),color=rgb(INK),width=1)
        draw_pdf(page,d,fitz.Rect(36,88,W-36,H-63))
        page.draw_line((34,H-48),(W-34,H-48),color=rgb(INK),width=.6)
        page.insert_text((34,H-29),'Contest 2800443 | B+G+3+R | dimensions in metres | CAD model in mm | use stated dimensions',fontsize=9,color=rgb(MUTED))
        page.insert_text((W-242,H-29),f'NOT FOR CONSTRUCTION   {i+1:02d}/{len(drawings):02d}',fontsize=9,fontname='hebo',color=rgb(AMBER))
    doc.set_metadata({'title':'Plot 83 New Cairo - B+G+3+R Engineering Constraint Study','author':'Architectural Design Team','subject':'Parametric concept; unresolved ramp, sightline and performance claims explicitly recorded'})
    doc.save(out,garbage=4,deflate=True);doc.close()


def export_dxf(drawings,out):
    doc=ezdxf.new('R2010');doc.units=4;doc.header['$INSUNITS']=4;doc.header['$MEASUREMENT']=1
    doc.linetypes.new('STUDY_DASH',dxfattribs={'description':'Schematic dashed line','pattern':[240,140,-100]})
    for name,c in LAYER_COLORS.items():doc.layers.new(name,dxfattribs={'color':c})
    m=doc.modelspace();offset=0;index=[]
    for d in drawings:
        origin=offset-d.box[0]; index.append({'drawing':d.key,'offset_x_mm':origin*1000,'units':'mm'})
        def xy(x,y):return ((x+origin)*1000,-y*1000)
        m.add_text(d.title,dxfattribs={'height':420,'layer':'TEXT'}).set_placement(xy(d.box[0],d.box[1]-1))
        for z in d.items:
            att={'layer':z.layer,'true_color':int(z.color.lstrip('#'),16),'lineweight':max(13,min(100,round(z.width*1000)))}
            if z.dash:att['linetype']='STUDY_DASH'
            if z.kind=='line':
                x1,y1,x2,y2=z.data;m.add_line(xy(x1,y1),xy(x2,y2),dxfattribs=att)
            elif z.kind=='poly':
                pts,closed=z.data;m.add_lwpolyline([xy(x,y) for x,y in pts],close=closed,dxfattribs=att)
                if z.fill and closed:
                    h=m.add_hatch(color=7,dxfattribs={'layer':z.layer,'true_color':int(z.fill[1:],16)})
                    h.paths.add_polyline_path([xy(x,y) for x,y in pts],is_closed=True)
            elif z.kind=='circle':
                x,y,r=z.data;m.add_circle(xy(x,y),r*1000,dxfattribs=att)
            elif z.kind=='arc':
                x,y,r,a,b=z.data;m.add_arc(xy(x,y),r*1000,-b,-a,dxfattribs=att)
            else:
                x,y,txt,sz,align,bold,rot=z.data
                ta={**att,'height':sz*1000,'rotation':rot}
                ent=m.add_text(txt,dxfattribs=ta)
                alg={'center':TextEntityAlignment.CENTER,'left':TextEntityAlignment.LEFT,'right':TextEntityAlignment.RIGHT}[align]
                ent.set_placement(xy(x,y),align=alg)
        offset+=d.box[2]+7
    # Draw fills behind lines and text, preserving semantic layers.
    entities=list(m);ordered=[e for e in entities if e.dxftype()=='HATCH']+[e for e in entities if e.dxftype()!='HATCH']
    m.set_redraw_order([(e.dxf.handle,format(i+1,'X')) for i,e in enumerate(ordered)])
    doc.saveas(out)
    check=ezdxf.readfile(out);audit=check.audit()
    if audit.errors or audit.fixes:raise RuntimeError(f'DXF audit errors={len(audit.errors)}, fixes={len(audit.fixes)}')
    return {'version':check.dxfversion,'entities':len(check.modelspace()),'layers':list(LAYER_COLORS),'audit_errors':0,'audit_fixes':0,'drawing_index':index}


def engineering_issues(p):
    return [
      dict(id='H01',title='RAMP WIDTH / SETBACK',short=f'{p.ramp_width:.2f} m clear ramp exceeds {p.west_setback:.2f} m west setback; wall thickness additional.',
        detail='A setback is not necessarily a ramp-width limit. The extra 0.50 m is reserved inside the plot, but permissibility and clearances below the typical-floor overhang are not established.'),
      dict(id='H02',title='RAMP CONNECTION / SWEPT PATH',short=f'{p.ramp_run:.3f} m at 15% leaves {p.plot_d-p.ramp_run:.3f} m; landing and 5.80 m outer turn do not fit.',
        detail='The drawn straight ramp reaches basement datum behind the basement wall. Transition ramps, vehicle underside clearance, protected pedestrian path, road entry and connection to the parking aisle remain unresolved. Annular arcs do not validate six individual maneuvers.'),
      dict(id='H03',title='POOL OVERLOOK / EARTH BUFFER',short='A grade-height earth buffer obstructs basement full-height glazing and a seated pool view.',
        detail='Pool shell is separate and the 1.50 m plan separation is exact. A lowered retained courtyard or revised pool level is required; either changes the requested arrangement. The section explicitly shows the conflict rather than hiding it.'),
      dict(id='H04',title='CORE PERFORMANCE CLAIM',short='Option B selected; the requested 14% net-to-gross advantage is not demonstrated.',
        detail='Same-scale conceptual reservations: A 6.00 x 6.20 m, B 4.85 x 5.65 m. Core-excluded gross is only a proxy, not measured apartment net area. Stair, lift, fire strategy and structure need local design review.'),
      dict(id='H05',title='CODE / STRUCTURE / SERVICES',short='No structural, Egyptian-code, fire, accessibility, mechanical or local-authority certification.',
        detail='Areas are gross horizontal rectangles. Roof pergola counting, cantilever permissions, perimeter spans, shaft continuity, room access and basement egress are schematic. Zero-waste and energy savings are strategies without measured performance claims.'),
      dict(id='H06',title='CONTEST ELIGIBILITY',short='Employer brief states: AI-generated results are not accepted. No submission performed.',
        detail='This package is AI-assisted engineering concept work. Do not represent it as human-only authored or conceal its origin. The source title is ambiguous on orientation; attached plot image and user dimensions govern this study.')]


def validate_geometry(drawings,p):
    assert p.plot_w>0 and p.plot_d>0 and 0<p.ramp_grade<=.30
    assert 0<p.ground_ratio<=p.typical_ratio<1 and 0<p.roof_ratio<1
    assert p.pool_buffer>0 and p.outer_r>p.inner_r>0
    assert p.gf_x>=p.west_setback and p.tf_x>=p.west_setback-1e-8
    assert p.front_y>=0 and p.rear_wall_y<=p.plot_d-p.rear_setback
    assert p.car_w<p.bay_w and p.car_l<p.bay_d
    x,y,w,h=p.pool;s=p.pool_shell
    assert x-s>=0 and x+w+s<=p.plot_w and y+h+s<=p.plot_d
    assert abs((y-s)-p.rear_wall_y-p.pool_buffer)<1e-9
    tests=[]
    for key,actual,expected in [('land',p.land,p.plot_w*p.plot_d),('ground',p.gf_w*p.floor_depth,p.land*p.ground_ratio),('typical',p.tf_w*p.floor_depth,p.land*p.typical_ratio),('roof',p.rf_w*p.roof_depth,p.land*p.roof_ratio)]:
        assert math.isclose(actual,expected,abs_tol=1e-8)
        tests.append({'check':key+'_area','actual_m2':actual,'expected_m2':expected,'pass':True})
    rooms=[]
    for d in drawings:
        for rm in d.rooms:
            assert rm['w']>0 and rm['h']>0
            if rm['target'] is not None:assert math.isclose(rm['area'],rm['target'],abs_tol=1e-8)
            rooms.append({'drawing':d.key,**rm})
        # Interior room reservations must not overlap each other.
        for i,a in enumerate(d.rooms):
            for b in d.rooms[i+1:]:
                iw=min(a['x']+a['w'],b['x']+b['w'])-max(a['x'],b['x'])
                ih=min(a['y']+a['h'],b['y']+b['h'])-max(a['y'],b['y'])
                assert iw<=1e-7 or ih<=1e-7,(d.key,a['id'],b['id'],'room overlap')
    tests.extend([{'check':'room_target_areas','pass':True},{'check':'room_reservations_do_not_overlap','pass':True},
      {'check':'pool_shell_inside_site','pass':True},{'check':'pool_buffer_faces_1_50m','pass':True},
      {'check':'diagonal','actual_m':math.hypot(p.plot_w,p.plot_d),'display_m':round(math.hypot(p.plot_w,p.plot_d),2),'pass':True}])
    return tests,rooms


def boards(p):
    """Self-contained HTML: embeds the generated, text-outlined SVGs; no network fonts."""
    def art(name,cls=''):
        content=(BOARD_ASSET_DIR/f'{name}.svg').read_text()
        content=content[content.index('<svg'):]
        content=content.replace('<svg ',f'<svg preserveAspectRatio="xMidYMin meet" class="{cls}" role="img" aria-label="{name.replace("_"," ")}" ',1)
        return content
    def frame(num,title,subtitle,asset,cls=''):
        return f'<section class="drawing {cls}"><div class="caption"><b>{num}</b><h2>{title}</h2></div><p class="sub">{subtitle}</p><div class="art">{art(asset)}</div></section>'
    base='''*{box-sizing:border-box}html,body{margin:0;padding:0;width:1600px;height:1200px;background:#f6f3eb;color:#253b3d}body{font-family:"Helvetica Neue",Arial,sans-serif} .board{width:1600px;height:1200px;padding:40px 44px 30px;display:flex;flex-direction:column;gap:20px}header{height:132px;flex:none;display:grid;grid-template-columns:104px 1fr 338px;gap:24px;border-bottom:3px solid #253b3d;padding-bottom:18px}.number{font-size:100px;line-height:.92;font-weight:300;letter-spacing:-7px}.kicker{font:12px Menlo,monospace;letter-spacing:1.8px;margin:0 0 9px}h1{font-size:43px;line-height:1.06;letter-spacing:-1.7px;margin:0 0 10px;font-weight:600}header p{margin:0;font-size:15px;line-height:1.4}.meta{padding-left:20px;border-left:1px solid #b5bfba}.meta strong{display:block;font:700 13px Menlo,monospace;line-height:1.5;color:#9c5b16}.meta p{font-size:13px;margin-top:9px;line-height:1.5}.caption{display:flex;gap:11px;align-items:baseline;border-top:1px solid #253b3d;padding-top:10px}.caption b{font:12px Menlo,monospace;color:#087c83}h2{font-size:21px;line-height:1.2;letter-spacing:-.5px;margin:0;font-weight:600}.sub{font-size:12px;line-height:1.4;margin:5px 0 7px;color:#657473}.drawing{display:flex;flex-direction:column;min-height:0;min-width:0}.art{min-height:0;flex:1;display:flex;align-items:center;justify-content:center}.art svg{width:100%;height:100%;display:block}.notes{font-size:13px;line-height:1.5;margin-top:8px}.notes strong{color:#9c5b16}.legend{display:flex;gap:20px;font-size:12px;align-items:center}.legend i{display:inline-block;width:24px;height:3px;vertical-align:middle;margin-right:7px;background:#253b3d}.legend .teal{background:#087c83}.legend .amber{background:#a96519}.legend .red{background:#a84332}footer{height:44px;flex:none;border-top:1px solid #253b3d;padding-top:12px;font:11px Menlo,monospace;display:flex;justify-content:space-between;align-items:flex-start;gap:20px} .hold{color:#a84332} .small{font-size:11px;color:#657473}.facts{display:grid;grid-template-columns:repeat(4,1fr);border-top:1px solid #b7c2bb;margin-top:10px;padding-top:12px;gap:10px}.facts b{display:block;font:600 25px Menlo,monospace;letter-spacing:-1px}.facts span{font-size:12px;color:#657473}.strip{border-top:1px solid #253b3d;padding-top:10px;display:flex;justify-content:space-between;gap:20px;font-size:12px;line-height:1.5}.strip strong{color:#9c5b16}.board-one .main{flex:1;min-height:0;display:grid;grid-template-columns:594px 470px 400px;gap:24px}.board-one .right{display:grid;grid-template-rows:1fr 1fr;gap:20px;min-height:0}.board-one .strip{height:76px;flex:none}.board-two .main{flex:1;min-height:0;display:grid;grid-template-columns:936px 552px;grid-template-rows:493px 395px;gap:20px 24px}.board-two .bottom{display:flex;flex-direction:column;min-height:0}.area{width:100%;border-collapse:collapse;margin-top:10px;font-size:13px;line-height:1.4}.area th{font-size:11px;letter-spacing:.7px;color:#657473;text-align:left;font-weight:500;padding:7px 6px;border-bottom:1px solid #253b3d}.area td{padding:7px 6px;border-bottom:1px solid #c7cec7}.area th:nth-child(n+2),.area td:nth-child(n+2){text-align:right;font-family:Menlo,monospace}.area tr:last-child td{font-weight:600;border-bottom:1px solid #253b3d}.waste{display:grid;grid-template-columns:1fr 1fr;gap:10px 20px;font-size:12px;line-height:1.4;margin-top:15px}.waste b{display:block;font-size:13px;margin-bottom:3px}.board-two .sub{font-size:12px}.board-two .notes{font-size:12px}@media print{@page{size:1600px 1200px;margin:0}html,body{print-color-adjust:exact;-webkit-print-color-adjust:exact}}'''
    def head(n,title,sub):return f'''<header><div class="number">{n}</div><div><p class="kicker">PLOT 83 / SECTOR B / NEW CAIRO CITY</p><h1>{title}</h1><p>{sub}</p></div><div class="meta"><strong>SCHEMATIC / CONSTRAINT STUDY<br>NOT FOR CONSTRUCTION</strong><p>CONTEST #2800443 · B+G+3+R<br>17.00 × 25.00 m · 425.00 m²<br>P4–P2 diagonal: {math.hypot(p.plot_w,p.plot_d):.4f} m</p></div></header>'''
    foot='<footer><span>ARCHITECTURAL DESIGN TEAM / PARAMETRIC CAD STUDY / 08 NOV 2026</span><span class="hold">Ramp access + pool sightline unresolved · AI-assisted local study</span><span>1600 × 1200</span></footer>'
    b1=head('01','Residential floor plans','North-facing living · East-facing bedrooms · Independent southern pool')
    b1+='<div class="main">'
    b1+=frame('B1','Basement & parking','6 compact stalls · 6.00 m aisle · cyan / amber radius templates','plan_basement_sweptpath')
    b1+=frame('01–03','Typical apartment','233.75 m² gross / 55% · One residence on each of 3 floors','plan_typical')
    b1+='<div class="right">'+frame('G','Ground floor','212.50 m² gross / 50% · Northern main entry','plan_ground')+frame('R','Roof level','106.25 m² enclosed / 25% · PV + resource recovery','plan_roof')+'</div></div>'
    b1+=f'''<div class="strip"><div><strong>01 / RAMP GEOMETRY</strong><br>3.20 ÷ 0.15 = {p.ramp_run:.3f} m, before transitions.<br>3.50 m clear width extends 0.50 m beyond west setback.</div><div><strong>02 / POOL SEPARATION</strong><br>6.00 × 3.00 m clear water + 200 mm separate shell.<br>1.50 m from basement outer face to pool outer face.</div><div><strong>03 / DRAWING STATUS</strong><br>Room figures are clear rectangle reservations.<br>Door detailing, egress, structure and ramp access require resolution.</div></div>'''+foot
    b2=head('02','Passive design & core study','Section A–A · Calculated solar geometry · Core alternatives · Resource strategy')
    b2+='<div class="main">'+frame('A–A','Climate, section & pool interface','Levels in metres · Four 3.30 m storeys above ground floor · Conceptual load path','section_aa')+frame('P','Sun path / prevailing breeze','North-up sky plot · Sun paths calculated at 30.03° N','passive_sun_wind_diagram')
    b2+=frame('C','Stair + elevator alternatives','Same drawing scale · B selected for a simpler core reservation','core_options_comparison')
    b2+='''<section class="bottom"><div class="caption"><b>S</b><h2>Area & resource schedule</h2></div><table class="area"><thead><tr><th>LEVEL</th><th>EACH m²</th><th>COUNT</th><th>SITE %</th></tr></thead><tbody>'''
    for n,a,c,r in [('Ground',p.land*p.ground_ratio,1,p.ground_ratio),('Typical',p.land*p.typical_ratio,3,p.typical_ratio),('Roof enclosed',p.land*p.roof_ratio,1,p.roof_ratio)]:
        b2+=f'<tr><td>{n}</td><td>{a:.2f}</td><td>{c}</td><td>{r:.0%}</td></tr>'
    total=p.land*(p.ground_ratio+3*p.typical_ratio+p.roof_ratio)
    b2+=f'<tr><td>Above-ground total</td><td>{total:.2f}</td><td>5</td><td>{p.ground_ratio+3*p.typical_ratio+p.roof_ratio:.0%}</td></tr></tbody></table>'
    b2+='''<div class="waste"><div><b>01 / Separate at source</b>Three-stream sorting room; isolated chute. Organics collected separately.</div><div><b>02 / Recover water</b>Greywater treatment to irrigation. Blackwater and pool water kept separate.</div><div><b>03 / Build for reuse</b>Modular partitions, bolted assemblies, local durable finishes; cut-list planning.</div><div><b>04 / Reduce demand</b>West solar screens, north/east openings, insulated envelope, PV pergola.</div></div><p class="notes"><strong>Zero-waste is a design objective, not a verified diversion rate.</strong> Roof pergola counting and all energy / water savings remain unverified.</p></section></div>'''+foot
    for i,body in [(1,b1),(2,b2)]:
        doc=f'<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=1600,initial-scale=1"><title>Plot 83 / Engineering Board {i}</title><style>{base}</style></head><body><main class="board board-{ "one" if i==1 else "two" }">{body}</main></body></html>'
        (ROOT/f'board{i}-codex.html').write_text(doc,encoding='utf-8')


def write_notes(p,tests,rooms,issues,dxf_check,out):
    report={'status':'SCHEMATIC_WITH_UNRESOLVED_ENGINEERING_CONSTRAINTS','construction_compliance':False,
      'source':'brief_assets/contest_meta.json and brief_assets/.png; user task supplied room targets and levels',
      'parameters':dataclasses.asdict(p),'geometry_checks':tests,'rooms':rooms,'dxf':dxf_check,'unresolved':issues,
      'swept_path':{'method':'Annular geometric envelope, not kinematic vehicle simulation','r_inner_m':p.inner_r,'r_outer_m':p.outer_r,'six_vehicle_routes_verified':False,'ramp_connection':'FAIL'},
      'solar':{'latitude_assumed':p.latitude,'noon_altitudes_deg':{n:90-abs(p.latitude-v) for n,v in [('June',23.44),('Equinox',0),('December',-23.44)]}},
      'net_to_gross':{'A_core_m2':6*6.2,'B_core_m2':4.85*5.65,'claimed_14_percent_verified':False}}
    (out/'engineering_validation.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    text='''# Plot 83 / 参数化工程包说明\n\n状态：**约束研究方案，不能宣称 100% 工程合规、不能施工或作为通过审批的设计。**\n\n## 重建\n\n```sh\npython3 build_cad_2800443.py\npython3 build_cad_2800443.py --write-default-config parameters.json\npython3 build_cad_2800443.py --config parameters.json\n```\n\n只用现有 Python 环境的 `ezdxf` 和 `PyMuPDF`，未安装依赖、未修改用户配置。参数以米输入，DXF 以毫米、R2010 输出，图层包括指定的八层。PDF 为 A3 横向矢量页；SVG 字体转路径，无位图、无网络字体。两张 HTML 自包含，固定 1600×1200。\n\n`Parameters` 集中定义地块、面积比例、楼层深度、退距、标高、坡道、车位、泳池、房间面积及日照纬度。导出共用几何原语，目标房间面积、泳池间距、边界包含关系自动检查。参数可变不等于任意取值都有建筑可行解：不成立的几何输入会触发断言，工程约束始终单独报告。\n\n## 来源与边界\n\n原始 JSON 的标题把方位写得含混；附图明确 P4-P1=17m、P1-P2=25m，按用户本轮的明确方向建模。附图确认 Plot 83、Sector B、西侧 84、南侧 10，未包含地勘、消防、结构和设备设计数据。纬度 30.03°N 为新开罗区域近似假定，并非测量坐标。N/NW 风向来自设计 brief，未伪造实测风玫瑰频率。\n\n原始雇主 brief 写明 **AI-generated results are not accepted**。本包为 AI 辅助本地研究，未提交平台，不应隐瞒来源后参赛。\n\n## 已核实尺寸\n\n'''
    text+=f'- 地块 {p.plot_w:.2f} × {p.plot_d:.2f} = {p.land:.2f} m²；对角线 {math.hypot(p.plot_w,p.plot_d):.6f} m，显示 30.23m 为四舍五入。\n'
    text+=f'- 首层 {p.gf_w:.2f} × {p.floor_depth:.2f} = {p.land*p.ground_ratio:.2f} m²；标准层 {p.tf_w:.2f} × {p.floor_depth:.2f} = {p.land*p.typical_ratio:.2f} m²；屋顶 {p.rf_w:.3f} × {p.roof_depth:.2f} = {p.land*p.roof_ratio:.2f} m²。\n'
    text+='- 面积为封闭外轮廓总面积；楼板悬挑、屋顶棚架计容方式未取得当地主管部门认可。地下室面积不套用地上50%比例。\n'
    text+='- 泳池净水面 3×6m，外壳厚0.20m；1.50m从地下室外墙外表面量至泳池外壳外表面。南侧外壳仍在地块内。\n'
    text+='- 六个车位按2.40×4.60m紧凑车型预留，示例车辆1.80×4.30m；不是一般大型轿车/SUV通用车库认证。6m标注为车位之间的净通道。\n\n## 未消解的工程问题\n\n'
    for it in issues:text+=f"### {it['id']} / {it['title']}\n\n{it['short']}\n\n{it['detail']}\n\n"
    text+='''## 扫掠与核心筒计算\n\n青色 Ri=3.2m、琥珀色 Ro=5.8m 是给定的内外包络半径模板；红色为坡道出口所需外转弯与场地的冲突。未将圆弧当作轴距、转向角、前后悬和逆车策略完整定义的车辆运动学验证。六个车位均已画出，但六条可达、可退出的真实路线未成立。\n\nA 核心筒预留 6×6.2=37.20m²，B 预留4.85×5.65=27.4025m²，同一233.75m²标准层作分母。只可计算扣核心筒后的总面积比例，不能当实际套内净面积。楼梯图为20级/层、每级165mm及300mm踏步的标准层概念；地下室至首层3.65m需要单独校核踏步和净空。B 的规则剪力墙布局是概念，不是承载力或抗震验算结论。\n\n## 输出与验证\n\n- `engineering_validation.json`：参数、目标面积、实际矩形房间面积、DXF审计、未通过项。\n- `requirement_matrix.md`：用户全部主要要求与实现/未验证状态。\n- `manifest.json`：各图纸SHA-256与文件大小。\n- ZIP包含本次DXF、完整PDF和所有SVG，另附报告，防止脱离说明后误用。\n- `99_临时/qa/`：展板截图、PDF缩略图、浏览器布局检查。\n\n不提交、不推送、不部署，不改全局规则与配置。\n'''
    (ROOT/'ENGINEERING_NOTES.md').write_text(text,encoding='utf-8')
    lines=['# Requirement matrix / Plot 83','', '| Requirement | Evidence | Status |','|---|---|---|']
    rows=[('17 x 25 m / 425 m2 / P4-P2 30.23 m','All site plans; calculated diagonal','Verified geometry'),
      ('N 15 m road / E 10 m spine / W 84 / S 10','Source attachment and plan context','Verified source mapping'),
      ('3 m west / 4 m rear setbacks','Dashed site control lines','Drawn; ramp permission unresolved'),
      ('6 cars / 6 m clear aisle / Ri3.2 Ro5.8','Basement six compact bays; DXF true ARC entities','Bay count and aisle verified; complete swept paths NOT verified'),
      ('3.5 m west ramp at 15% to -3.2 m','21.333 m straight ramp; H01/H02','Unresolved entry/landing/connection'),
      ('Family32 / kitchen8 / gym18 / store10 / 2WC / electrical + pump','Basement room polygons in JSON','Area targets verified; access and egress schematic'),
      ('3 x 6 m independent pool + 1.5 m buffer','Separate shell; hatched face-to-face dimension','Verified plan geometry; foundation/retaining design absent'),
      ('Full-height family glazing directly overlooks pool','Section A-A shows soil obstruction','Not satisfied by current grade-height buffer'),
      ('Ground212.50 /50% / north entry and salon / west kitchen bath / veranda','Ground plan','Footprint verified; architectural concept'),
      ('Typical233.75 /55% / three elevations / one dwelling each','Typical plan and section','Footprint and levels verified'),
      ('North58 / kitchen18 / east3 bedrooms / west3 baths laundry','Typical room polygons','Targets and count drawn; door/privacy detailing schematic'),
      ('A wrapped lift vs B adjacent U-stair / 14% net efficiency','Same-scale core diagram with same denominator','Comparison drawn; B selected; 14% NOT substantiated'),
      ('Roof106.25 /25% / PV greywater sorting wind cowls garden','Roof plan','Area verified; systems reserved, capacities not sized'),
      ('Sun path / wind movement / passive strategy','Calculated sky paths; north-west arrows; section','Solar calculation verified; wind direction assumption, no measured rose'),
      ('Zero-waste / sustainable materials','Board 2 strategies','Targets only; no waste or energy performance claimed'),
      ('DXF all four floor plans + section named layers','R2010 master and audit','Generated and read-back audited'),
      ('Multi-page vector PDF / individual SVG / ZIP','Exports and manifest','Generated'),
      ('Two exact1600x1200 HTML boards without clipping','Self-contained HTML; separate browser QA','Generated; see board_layout_check.json')]
    for a,b,c in rows:lines.append(f'| {a} | {b} | {c} |')
    (out/'requirement_matrix.md').write_text('\n'.join(lines)+'\n')


def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--config',type=pathlib.Path);ap.add_argument('--out',type=pathlib.Path,default=ROOT/'exports');ap.add_argument('--write-default-config',type=pathlib.Path)
    args=ap.parse_args();p=Parameters()
    if args.write_default_config:
        args.write_default_config.write_text(json.dumps(dataclasses.asdict(p),indent=2)+'\n');return
    if args.config:p=Parameters(**json.loads(args.config.read_text()))
    out=args.out.resolve();out.mkdir(parents=True,exist_ok=True)
    # HTML assets are embedded from the selected output directory.
    ds=[basement(p),ground(p),typical(p),roof(p),section(p),passive(p),cores(p)]
    tests,rooms=validate_geometry(ds,p);issues=engineering_issues(p);ds.append(schedule_drawing(p,issues))
    svg_files=[]
    for d in ds:
        f=out/(d.key+'.svg');svg(d,f);svg_files.append(f)
    # Requested combined roof and section vector sheet, from the exact same primitives.
    combo=Drawing('plan_roof_section','ROOF PLAN + SECTION A-A',(-3,-3,63,32))
    for original,dx,dy in [(ds[3],0,0),(ds[4],29,17)]:
        for z in original.items:
            if z.kind=='line':x1,y1,x2,y2=z.data;dat=(x1+dx,y1+dy,x2+dx,y2+dy)
            elif z.kind=='poly':points,closed=z.data;dat=(tuple((x+dx,y+dy) for x,y in points),closed)
            else:
                a=list(z.data);a[0]+=dx;a[1]+=dy;dat=tuple(a)
            combo.items.append(dataclasses.replace(z,data=dat))
    svg(combo,out/'plan_roof_section.svg');svg_files.append(out/'plan_roof_section.svg')
    dxf=out/'Plot83_NewCairo_B_G_3_R_Master.dxf';pdf=out/'Plot83_NewCairo_Engineering_Set.pdf'
    dxf_check=export_dxf(ds,dxf);export_pdf(ds,p,pdf)
    # boards() receives actual output location, allowing reproducible --out use.
    boards_from(out,p)
    write_notes(p,tests,rooms,issues,dxf_check,out)
    (out/'parameters.json').write_text(json.dumps(dataclasses.asdict(p),indent=2)+'\n')
    files=[dxf,pdf,*svg_files,out/'engineering_validation.json',out/'requirement_matrix.md',out/'parameters.json']
    manifest={f.name:{'bytes':f.stat().st_size,'sha256':hashlib.sha256(f.read_bytes()).hexdigest()} for f in files}
    (out/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n');files.append(out/'manifest.json')
    package=out/'Plot83_NewCairo_CAD_Package.zip'
    with zipfile.ZipFile(package,'w',zipfile.ZIP_DEFLATED) as z:
        for f in files:z.write(f,f.name)
        z.write(ROOT/'ENGINEERING_NOTES.md','ENGINEERING_NOTES.md')
        z.write(ROOT/'build_cad_2800443.py','build_cad_2800443.py')
    with zipfile.ZipFile(package) as z:assert z.testzip() is None
    expected=[*files,package,ROOT/'board1-codex.html',ROOT/'board2-codex.html']
    assert all(f.exists() and f.stat().st_size>0 for f in expected)
    print(json.dumps({'status':'GENERATED_WITH_DISCLOSED_ENGINEERING_HOLD_POINTS','files':len(expected),'pdf_pages':len(ds),'dxf_audit_errors':dxf_check['audit_errors'],'geometry_checks':len(tests),'unresolved':len(issues),'zip':str(package)},indent=2))


def boards_from(out,p):
    # Avoid stale exports when an alternative output directory is requested.
    global BOARD_ASSET_DIR
    BOARD_ASSET_DIR=out
    boards(p)

if __name__=='__main__':main()
