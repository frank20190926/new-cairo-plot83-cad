#!/usr/bin/env python3
"""Plot 83 deterministic schematic CAD package. Metres in model, mm in DXF.

Uses existing ezdxf and PyMuPDF only. Does NOT claim construction compliance.
Run: python3 build_cad_2800443.py [--config parameters.json] [--out exports]
Every drawing/export is generated from the same geometric primitives.
"""
from __future__ import annotations
import argparse, dataclasses, hashlib, html, json, math, pathlib, re, zipfile
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
    rear_setback: float = 6.0
    road_w: float = 15.0
    spine_w: float = 10.0
    ground_ratio: float = .50
    typical_ratio: float = .55
    roof_ratio: float = .25
    floor_depth: float = 17.0
    ground_east_gap: float = .5
    typical_east_gap: float = .25
    rear_wall_y: float = 19.0
    wall: float = .25
    partition: float = .20
    ramp_width: float = 3.0
    ramp_grade: float = .20
    basement_z: float = -3.2
    ground_z: float = .45
    storey: float = 3.3
    roof_depth: float = 8.5
    pool_w: float = 6.0
    pool_d: float = 3.0
    pool_shell: float = .20
    pool_buffer: float = 1.5
    pool_water_z: float = -2.0
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
    def gf_w(self): return (self.land*self.ground_ratio+self.court_area)/self.floor_depth
    @property
    def tf_w(self): return 13.75
    @property
    def tf_depth(self): return (self.land*self.typical_ratio+self.court_area)/self.tf_w
    @property
    def tf_front_y(self): return self.rear_wall_y-self.tf_depth
    @property
    def court_area(self): return 2.5*3.4
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
        return (self.plot_w-1.25-self.pool_w, self.rear_wall_y+self.pool_buffer,
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
            label_x=x+1.65 if id.startswith('T-BED') else x+w/2
            for j,s in enumerate(lines): self.text(label_x,y+h/2-.26+(j-(len(lines)-1)/2)*.32,s,.26,align='center',bold=True)
            self.text(label_x,y+h/2+.08+(len(lines)-1)*.16,f'{w:.2f} x {h:.2f} m',.22,MUTED,'center')
            self.text(label_x,y+h/2+.36+(len(lines)-1)*.16,f'{w*h:.2f} m2',.22,MUTED,'center')
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
        d.text(p.plot_w+1.18,p.plot_d/2,f'EAST / {p.spine_w:.2f} m PEDESTRIAN SPINE / PLOT 82',.30,MUTED,'center',rotate=90)
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
        d.text(5.5,10.6,f'P4-P2 {math.hypot(p.plot_w,p.plot_d):.2f} m',.25,MUTED)
    d.arrow(19.0,2.3,19.0,.4,INK,'DIMENSIONS',.025); d.text(19,0,'N',.4,align='center',bold=True)
    for i in range(5):d.rect(i*1.0,27.2,1.0,.13,'DIMENSIONS',INK,.01,INK if i%2==0 else PAPER)
    d.text(0,27.75,'0',.22);d.text(5,27.75,'5 m',.22,align='right')


def pool_plan(d,p,buffer=True):
    # Pool dimensions describe the OUTSIDE shell; the 200 mm shell lies inside.
    x,y,w,h=p.pool;s=p.pool_shell
    d.rect(x,y,w,h,'WALLS',INK,.04,GRAY)
    d.rect(x+s,y+s,w-2*s,h-2*s,'WALLS',TEAL,.035,WATER)
    d.text(x+w/2,y+1.15,'SUNKEN POOL',.31,TEAL,'center',True)
    d.text(x+w/2,y+1.62,'6.00 x 3.00 m OUTER SHELL',.23,TEAL,'center')
    d.text(x+w/2,y+2.02,'5.60 x 2.60 m clear water',.22,TEAL,'center')
    if buffer:
        d.hatch(x,p.rear_wall_y,w,p.pool_buffer)
        d.text(x+w/2,p.rear_wall_y+.85,'INSULATED BACKFILL',.25,AMBER,'center',True)
    d.dimv(p.rear_wall_y,y,16.25,'1.50 m')
    d.dimv(y,y+h,16.25,'3.00 m')
    d.dimv(y+h,p.plot_d,16.25,'1.50 m')
    d.text(6,24.15,'SOUTH GARDEN',.27,MUTED,'center')
    d.text(6,24.65,'6.00 m TOTAL DEPTH',.23,MUTED,'center')
    for xx,yy in [(4.7,21.8),(6.9,22.9)]:d.circle(xx,yy,.65,'LANDSCAPE','#82937b',.02,LIGHT)


def ramp(d,p):
    d.rect(0,0,p.ramp_width,p.ramp_run,'RAMP',AMBER,.045,'#f1e6d7')
    for y in range(1,math.ceil(p.ramp_run)):d.line(.15,y,p.ramp_width-.15,y,'RAMP',AMBER,.012)
    d.arrow(1.5,2,1.5,p.ramp_run-1,AMBER,'RAMP')
    d.text(1.20,8.5,f'{p.ramp_grade:.0%} RAMP / {p.ramp_run:.2f} m RUN',.29,AMBER,'center',rotate=90)
    d.dimh(0,p.ramp_width,1.0,f'{p.ramp_width:.2f} m strip')
    d.text(1.5,p.ramp_run+.65,f'{p.basement_z:+.2f}',.30,AMBER,'center',True)
    d.text(1.5,18.2,'B1 LANDING',.23,TEAL,'center',True)


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
    d.text(ex+.875,ey+.8,'LIFT',.24,align='center',bold=True)
    d.text(ex+.875,ey+1.2,'1.75 x 2.00 m',.19,align='center')
    d.text(ex+.875,ey+1.55,'3.50 m2',.19,align='center')
    d.text(ex+.875,ey+3.15,'LOBBY',.25,align='center',bold=True)
    d.text(ex+.875,ey+3.55,'1.75 x 3.15 m',.19,MUTED,'center')
    d.text(ex+.875,ey+3.9,'5.51 m2',.19,MUTED,'center')
    d.text(sx+1.2,sy+5.45,'STAIR 2.40 x 5.10 m / 12.24 m2',.18,MUTED,'center')
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
    d.rect(3,0,14,19,'WALLS',INK,.09)
    bx=9.55;aisle_y=4.85;right=16.75
    for j,by in enumerate((.25,10.85)):
        for i in range(3):
            xx=bx+i*p.bay_w
            d.rect(xx,by,p.bay_w,p.bay_d,'DIMENSIONS',MUTED,.018)
            car(d,xx+.3,by+.15,p.car_w,p.car_l,j*3+i+1)
    d.rect(bx,aisle_y,7.2,p.aisle,'AREA_BOUNDARY',MUTED,.012,fill='#edf2ed')
    d.text(13.15,7.5,'6-CAR GARAGE',.35,align='center',bold=True)
    d.text(13.15,8.0,'2.40 x 4.60 m compact bays',.24,MUTED,'center')
    d.dimv(aisle_y,aisle_y+p.aisle,17.2,'6.00 m CLEAR')
    for r,c in [(p.inner_r,TEAL),(p.outer_r,AMBER)]:d.arc(10.95,10.85,r,-90,0,color=c,width=.045)
    d.text(10,5.6,'Ri 3.20 / Ro 5.80 m',.28,TEAL,bold=True)
    d.text(13.15,10.25,'SWEPT-PATH MANEUVERING AISLE',.215,MUTED,'center')
    core(d,p)
    d.room('B-ELEC','ELECTRIC',3.25,10.9,4.35,1.1)
    d.room('B-WATER','WATER',3.25,12.2,4.35,1.1)
    d.room('B-WC1','WC 1',3.25,7.9,2.075,1.8)
    d.room('B-WC2','WC 2',5.525,7.9,2.075,1.8)
    d.room('B-STO','STORAGE',3.25,13.5,4.35,1.1)
    d.room('B-KIT','KITCHENETTE',3.25,14.8,4.35,1.6)
    d.room('B-GYM','SMALL GYM',3.25,16.6,4.35,2.15)
    d.room('B-FAM','FAMILY SITTING',9.55,15.7,7.2,3.05,color=LIGHT)
    d.sofa(10,15.95,2.4);d.sofa(13.4,15.95,2.4)
    d.window(9.8,19,16.4,19)
    d.arrow(13.1,18.4,13.1,20.3)
    for rm in d.rooms:
        if rm['id'].startswith('B-WC'):d.door(rm['x']+.5,rm['y']+rm['h'],.75)
        elif rm['id']=='B-FAM':d.door_v(rm['x'],rm['y']+.7,.85)
        else:d.door_v(rm['x']+rm['w'],rm['y']+.25,min(.75,rm['h']-.35))
    d.text(8.55,12.5,'SERVICE / PEDESTRIAN HALL',.24,MUTED,'center',rotate=90)
    for xx,yy in [(3,0),(16.75,0),(16.75,15.45),(3,18.7)]:d.rect(xx,yy,.25,.3,'COLUMNS',INK,.018,INK)
    pool_plan(d,p)
    d.text(8.5,26.45,'6-Car Garage + Family Sitting Overlooking Sunken Pool Court',.25,TEAL,'center',True)
    return d


def court(d,p):
    d.rect(7.5,10,2.5,3.4,'AREA_BOUNDARY',TEAL,.05,fill=PAPER)
    d.text(8.75,11.05,'OPEN SKY',.26,TEAL,'center',True)
    d.text(8.75,11.48,'WIND COURT',.24,TEAL,'center',True)
    d.text(8.75,12.05,'2.50 x 3.40 m',.23,TEAL,'center')
    d.text(8.75,12.48,'8.50 m2 VOID',.23,TEAL,'center')
    d.arrow(8.75,12.8,8.75,13.25)


def ground(p):
    d=Drawing('plan_ground',f'00 / GROUND {p.ground_z:+.2f} m',(-2.8,-2.7,23,31.3));site(d,p)
    ramp(d,p);pool_plan(d,p)
    x,y,w,h=p.gf_x,p.front_y,p.gf_w,p.floor_depth
    d.rect(x,y,w,h,'AREA_BOUNDARY',INK,.09);core(d,p);court(d,p)
    d.room('G-REC','NORTH RECEPTION',8.6,2.25,7.65,5.25,color=LIGHT)
    d.line(8.6,5.35,8.6,6.2,'WALLS',PAPER,.12)
    d.line(9,2.25,10,2.25,'WALLS',PAPER,.12)
    d.door(10.25,7.5,.9)
    d.sofa(9,2.65,2.5);d.sofa(13.2,2.65,2.5)
    d.room('G-KIT','KITCHEN',3.75,7.9,3.5,4.1)
    d.room('G-WC','BATH',3.75,12.2,2.25,2.6)
    d.room('G-STORE','PANTRY',3.75,15.05,2.25,3.7)
    d.room('G-DINE','DINING',11.5,7.75,4.75,7.05,color=LIGHT)
    d.rect(12.55,9,2.3,1.0,'FURNITURE',MUTED,.025)
    d.room('G-VER','GARDEN VERANDA',6.2,15.05,10.05,3.7,color=LIGHT)
    d.window(9,2,16,2);d.window(4,19,16.1,19)
    d.window(3.5,8.3,3.5,11.4);d.window(3.5,12.7,3.5,14.3)
    d.window(16.5,8.3,16.5,14.2)
    d.door(9,2,1.0)
    for xx,yy in [(7.25,9),(6,12.8),(11.5,8.4)]:d.door_v(xx,yy,.8)
    d.door(10.2,15.05,1.0);d.door(4.4,15.05,.75)
    d.arrow(9.5,.2,9.5,1.8,INK,'DIMENSIONS')
    d.text(12,.85,'2.00 m ENTRY FORECOURT',.27,align='center',bold=True)
    d.dimh(x,x+w,-.12,'13.00 m E-W / OUTER ENVELOPE')
    d.text(8.5,26.45,'13.00 x 17.00 - 8.50 = 212.50 m2 / 50.00%',.30,TEAL,'center',True)
    return d


def typical(p):
    d=Drawing('plan_typical','01-03 / TYPICAL +3.75 / +7.05 / +10.35 m',(-2.8,-2.7,23,31.3));site(d,p)
    x,y,w,h=p.tf_x,p.tf_front_y,p.tf_w,p.tf_depth
    d.rect(x,y,w,h,'AREA_BOUNDARY',INK,.09);core(d,p);court(d,p)
    d.room('T-REC','NORTH RECEPTION',8.6,y+.25,7.9,6.85-y-.25,color=LIGHT)
    d.line(8.6,5.35,8.6,6.2,'WALLS',PAPER,.12)
    d.sofa(9,y+.65,2.5);d.sofa(13.3,y+.65,2.5)
    d.room('T-KIT','KITCHEN',3.25,7.9,4.0,4.6)
    for i,(yy,hh) in enumerate([(12.7,1.8),(14.7,1.8),(16.7,2.05)]):
        d.room('T-WC'+str(i+1),'BATH '+str(i+1),3.25,yy,2.25,hh)
        d.window(3,yy+.35,3,yy+hh-.35)
        d.line(5.5,yy+.3,5.5,yy+1.05,'WALLS',PAPER,.12)
        d.line(5.59,yy+.95,5.59,yy+1.65,'WALLS',INK,.025)
    d.room('T-LAUN','LAUNDRY',5.7,16.55,1.55,2.2)
    for i,(yy,hh) in enumerate([(7.1,3.6),(10.9,3.6),(14.7,4.05)]):
        d.room('T-BED'+str(i+1),['BEDROOM 01','BEDROOM 02','MASTER BEDROOM'][i],11.5,yy,5,hh,color=LIGHT)
        d.bed(14.55,yy+.3);d.window(16.75,yy+.45,16.75,yy+hh-.45);d.door_v(11.5,yy+.65,.85)
    d.text(10.75,15.8,'1.50 m PRIVATE HALL',.23,MUTED,'center',rotate=90)
    d.window(9,y,16.2,y);d.window(3,8.4,3,12)
    d.door_v(7.25,8.6,.85);d.door(10.25,6.85,.9);d.door_v(7.25,17,.75)
    for j in range(32):
        yy=y+.2+j*(h-.4)/32;d.line(x-.16,yy,x-.16,yy+.23,'PASSIVE_WIND_SUN',AMBER,.065)
    d.text(1.35,10.5,'WEST SOLAR SCREEN',.27,AMBER,'center',rotate=90)
    d.arrow(12,-.05,12,y+1.4)
    d.dimh(x,x+w,y-.5,'13.75 m E-W')
    d.text(8.5,21.5,'3 FLOORS / ONE APARTMENT EACH',.36,align='center',bold=True)
    d.text(8.5,22.25,'13.75 x 17.6181818 - 8.50 = 233.75 m2',.29,TEAL,'center',True)
    d.text(8.5,22.9,'55.00% / depth rounds to 17.62 m',.28,MUTED,'center')
    d.text(8.5,23.6,'3 east bedrooms / west kitchen + baths / north living',.25,MUTED,'center')
    d.dimv(y,19,18.8,'17.62 m*')
    return d


def roof(p):
    d=Drawing('plan_roof',f'R / ROOF {p.levels[-1]:+.2f} m',(-2.8,-2.7,23,31.3));site(d,p)
    x,y,w,h=3.5,1.5,p.rf_w,p.roof_depth
    d.rect(p.tf_x,p.tf_front_y,p.tf_w,p.tf_depth,'DIMENSIONS',MUTED,.03,fill=LIGHT)
    d.rect(x,y,w,h,'AREA_BOUNDARY',INK,.075,fill=PAPER);core(d,p);court(d,p)
    d.room('R-GREY','GREYWATER PLANT',9.55,1.75,6.20,2.8)
    d.room('R-WASTE','SORTING ROOM',9.55,4.75,6.20,2.8)
    d.room('R-SERVICE','SERVICE / PLANT',3.75,7.9,12,1.85)
    d.door_v(9.55,3.2,.85);d.door_v(9.55,5.8,.85);d.door(8.55,7.9,.85);d.door(12.5,9.75,1.0)
    for i in range(3):
        for j in range(2):d.rect(3.65+i*2.5,14+j*1.65,2.3,1.4,'PASSIVE_WIND_SUN',TEAL,.025,'#bdd3d2')
    d.text(8.5,18.25,'PV PERGOLA / MODULE RESERVATIONS',.27,TEAL,'center',True)
    d.text(8.5,20.9,'LANDSCAPED ROOF TERRACE',.36,align='center',bold=True)
    d.text(8.5,21.7,'Court remains open to sky / clean inlet + separate exhaust',.25,MUTED,'center')
    d.text(8.5,22.5,'Open-air pergola & green terrace zone',.25,MUTED,'center')
    d.dimh(x,x+w,.9,'12.50 m E-W')
    d.text(8.5,26.45,'12.50 x 8.50 = 106.25 m2 / 25.00%',.30,TEAL,'center',True)
    return d


def section(p):
    d=Drawing('section_aa','A-A / NORTH-SOUTH ENVIRONMENTAL SECTION',(-2.7,-18.2,32,25.0))
    x1=p.front_y;x2=p.rear_wall_y;z=p.levels
    d.line(-.7,0,19,0,'SITE_BOUNDARY',INK,.055)
    d.line(23.5,0,26,0,'SITE_BOUNDARY',INK,.055)
    d.text(0,1.0,'N / ROAD',.32,align='center',bold=True)
    d.text(25,1.0,'S / PLOT 10',.32,align='center',bold=True)
    d.rect(0,-p.ground_z,19,p.ground_z-p.basement_z,'WALLS',INK,.07,fill=PAPER)
    for i in range(1,5):
        floor=z[i];ceil=z[i+1];left=x1 if i==1 else p.tf_front_y
        d.rect(left,-ceil,19-left,ceil-floor,'WALLS',INK,.065,fill=PAPER)
        d.rect(left,-floor,19-left,.22,'WALLS',INK,.02,fill=GRAY)
        d.line(left,-floor-.5,left,-ceil+.6,'GLAZING',TEAL,.05)
        d.line(19,-floor-.5,19,-ceil+.6,'GLAZING',TEAL,.05)
        mid=-(floor+ceil)/2
        d.arrow(left-1,mid,left+3,mid,TEAL)
        d.arrow(left+3,mid,18,mid-.3,TEAL)
        d.text(10,mid+.65,'NORTH AIR INLET > COURT / HIGH OUTLET',.28,MUTED,'center')
    rfz=z[-1]
    d.rect(1.5,-rfz-3,p.roof_depth,3,'WALLS',INK,.065,PAPER)
    d.text(5.75,-rfz-1.2,'ROOF SERVICES',.35,align='center',bold=True)
    d.line(13.5,-rfz-1,18,-rfz-1.8,'PASSIVE_WIND_SUN',TEAL,.12)
    d.text(15.7,-rfz-2.3,'PV PERGOLA',.30,TEAL,'center',True)
    d.rect(10,-rfz,3.4,rfz-p.ground_z,'PASSIVE_WIND_SUN',TEAL,.025)
    d.arrow(11.7,-rfz+3,11.7,-rfz-1.0,TEAL)
    d.text(11.7,-rfz-1.4,'OPEN SKY',.27,TEAL,'center')
    d.text(9,1.2,'FAMILY SITTING / SUNKEN COURTYARD',.33,bold=True)
    d.line(19,.7,19,2.6,'GLAZING',TEAL,.065)
    # Lowered retained structural fill leaves a sightline above the buffer.
    d.hatch(19,2.6,1.5,.8,AMBER)
    py=p.pool[1]
    d.rect(py,2.0,3,1.4,'WALLS',INK,.06,GRAY)
    d.rect(py+.2,2.0,2.6,1.2,'WALLS',TEAL,.025,WATER)
    d.line(23.5,0,23.5,3.4,'WALLS',INK,.055)
    d.line(19,2.6,20.5,2.6,'LANDSCAPE',MUTED,.04)
    d.line(16,1.6,22,2.0,'PASSIVE_WIND_SUN',TEAL,.025,True)
    d.text(9,2.05,'Glazing overlooks lowered buffer and open pool court',.28,TEAL)
    d.text(9,2.65,'1.50 m insulated structural buffer separates basement & pool shell',.25,MUTED)
    d.dimh(19,20.5,4.1,'1.50 m')
    d.dimh(20.5,23.5,4.1,'3.00 m')
    d.dimh(23.5,25,4.1,'1.50 m')
    d.dimh(19,25,5.25,'6.00 m SOUTH GARDEN')
    d.text(26,2.05,'Water -2.00',.27,TEAL)
    d.text(26,2.7,'Bed -3.20',.27,TEAL)
    d.text(26,3.3,'Separate shell',.25,MUTED)
    for i,lev in enumerate(z):
        tag=['B1','G','01','02','03','R'][i]
        d.line(-.15,-lev,x1-.2,-lev,'DIMENSIONS',MUTED,.014)
        d.text(-.2,-lev-.12,f'{tag} {lev:+.2f}',.29,INK,'right',True)
    d.dimv(-z[-1],-z[1],27.3,'4 x 3.30 m = 13.20 m')
    d.text(14,6.1,'SECTION A-A / North-South environmental section through wind court & sunken pool',.26,MUTED,'center')
    return d


def survey(p):
    d=Drawing('site_survey','S0 / SOURCE SURVEY ORIENTATION',(-2.8,-2.7,23,31.3))
    site(d,p,diagonal=True)
    d.text(8.5,7,'PLOT 83 / SECTOR B',.65,align='center',bold=True)
    d.text(8.5,8.05,'17.00 m E-W x 25.00 m N-S',.39,TEAL,'center',True)
    d.text(8.5,9.0,'425.00 m2 / NORTH UP',.38,align='center')
    for yy,txt in [(14,'P4 NW (0.00, 25.00)'),(15,'P1 NE (17.00, 25.00)'),(16,'P3 SW (0.00, 0.00)'),(17,'P2 SE (17.00, 0.00)')]:
        d.text(8.5,yy,txt,.35,align='center')
    d.text(8.5,19,'Coordinates in metres; origin at P3',.29,MUTED,'center')
    d.text(8.5,24,'SOUTH GARDEN / 6.00 m DEEP',.31,TEAL,'center',True)
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
    d.rect(-1.02,-2.3,2.04,3.0,'WALLS',INK,.04,LIGHT)
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
    d.text(-7.8,8.65,'Prevailing N/NW summer breeze + calculated solar paths (30.03 deg N).',.26,MUTED)
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
    d.text(bx,8.0,'SELECTED / aligned shear-wall layout',.27,TEAL)
    d.text(0,8.65,f'Net-to-gross efficiency: A {ea:.2%} / B {eb:.2%} (+{(eb-ea):.2%} floor plate gain)',.29,bold=True)
    d.text(0,9.25,'COMPACT SIDE-BY-SIDE CORE SAVES 9.80 m2 PER FLOOR PLATE.',.31,TEAL,bold=True)
    d.text(0,9.8,'Identical gross floor plate; aligned 2-flight U-stair + 8-person lift.',.26,MUTED)
    return d


def schedule_drawing(p,issues):
    d=Drawing('area_and_constraints','S / AREA SCHEDULE + DESIGN HOLD POINTS',(0,0,28,20))
    d.text(.5,1,'AREA / OUTER FOOTPRINT LESS OPEN COURT',.60,bold=True)
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
        page.insert_text((815,39),'17.00 m E-W x 25.00 m N-S / CAD SET',fontsize=11,fontname='hebo',color=rgb(TEAL))
        page.draw_line((34,75),(W-34,75),color=rgb(INK),width=1)
        draw_pdf(page,d,fitz.Rect(36,88,W-36,H-63))
        page.draw_line((34,H-48),(W-34,H-48),color=rgb(INK),width=.6)
        page.insert_text((34,H-29),'Contest 2800443 | B+G+3+R | dimensions in metres | CAD model in mm | North Up (17m E-W x 25m N-S)',fontsize=9,color=rgb(MUTED))
        page.insert_text((W-242,H-29),f'ARCHITECTURAL CAD SET   {i+1:02d}/{len(drawings):02d}',fontsize=9,fontname='hebo',color=rgb(TEAL))
    doc.set_metadata({'title':'Plot 83 New Cairo - B+G+3+R Architectural CAD Set','author':'Architectural Design Team','subject':'17m E-W x 25m N-S Portrait Survey Orientation'})
    doc.save(out,garbage=4,deflate=True);doc.close()


def export_dxf(drawings,out):
    doc=ezdxf.new('R2010');doc.units=4;doc.header['$INSUNITS']=4;doc.header['$MEASUREMENT']=1
    doc.linetypes.new('STUDY_DASH',dxfattribs={'description':'Schematic dashed line','pattern':[240,140,-100]})
    for name,c in LAYER_COLORS.items():doc.layers.new(name,dxfattribs={'color':c})
    m=doc.modelspace();offset=0;index=[]
    for d in drawings:
        origin=offset-d.box[0]
        plan=d.key.startswith('plan_') or d.key=='site_survey'
        y_origin=25.0 if plan else 0.0
        index.append({'drawing':d.key,'offset_x_mm':origin*1000,'offset_y_mm':0,'local_coordinates':'X east; Y north; P3=(0,0)' if plan else 'diagram coordinates','units':'mm'})
        def xy(x,y):return ((x+origin)*1000,(y_origin-y)*1000)
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
      dict(id='H01',title='RAMP CONNECTION / SWEPT PATH',short='3.00 m west strip; 20% x 16.00 m nominal run. Transitions and garage link unresolved.',detail='The west strip satisfies the requested plan width. Walls reduce usable clear width; local ramp slope limits, transitions, headroom and six-car entry/exit routes are not verified. Ri3.20/Ro5.80 arcs are geometric templates, not vehicle simulation.'),
      dict(id='H02',title='SUNKEN POOL / RETAINING',short='6 x 3 m outside shell; 1.50 m building buffer + 1.50 m south-fence clearance.',detail='The 200 mm shell lies inside the pool footprint, leaving 5.60 x 2.60 m clear water. The buffer is lowered and retained to allow the basement overlook. Retaining, foundations, waterproofing, drainage, flood protection and guarding need engineering design.'),
      dict(id='H03',title='AREA MEASUREMENT',short='Ground221.00-8.50=212.50; typical242.25-8.50=233.75; roof106.25 m2.',detail='Typical depth is exactly17.618181818m, rounded17.62m on dimensions. Open-sky court is2.50x3.40m. Coverage assumes the court is excluded; statutory counting and projections must be confirmed locally.'),
      dict(id='H04',title='CORE / STRUCTURE / SERVICES',short='Core B selected. Fire, egress, structure, lift and services remain schematic.',detail='The clear 6m parking aisle contains no columns in this scheme. Structural spans, stacked core, ventilation, external openings and roof installations are not certified. No14% efficiency or energy-performance claim is made.')]


def validate_geometry(drawings,p):
    assert p.plot_w==17 and p.plot_d==25
    assert math.isclose(p.gf_x,3.5) and math.isclose(p.tf_x,3.0)
    assert p.ramp_width==p.west_setback==3
    assert p.front_y==2 and p.rear_wall_y==19
    x,y,w,h=p.pool
    assert math.isclose(y-p.rear_wall_y,1.5) and math.isclose(p.plot_d-y-h,1.5)
    assert x>=0 and x+w<=p.plot_w and y+h<=p.plot_d
    tests=[]
    for key,actual,expected in [('land',p.land,425),('ground',p.gf_w*p.floor_depth-p.court_area,212.5),('typical',p.tf_w*p.tf_depth-p.court_area,233.75),('roof',p.rf_w*p.roof_depth,106.25)]:
        assert math.isclose(actual,expected,abs_tol=1e-8)
        tests.append({'check':key+'_area','actual_m2':actual,'expected_m2':expected,'pass':True})
    rooms=[]
    for d in drawings:
        for rm in d.rooms:
            assert rm['w']>0 and rm['h']>0
            assert rm['x']>=3 and rm['x']+rm['w']<=17
            assert rm['y']>=0 and rm['y']+rm['h']<=19.001
            if d.key in ('plan_ground','plan_typical'):
                iw=min(rm['x']+rm['w'],10)-max(rm['x'],7.5)
                ih=min(rm['y']+rm['h'],13.4)-max(rm['y'],10)
                assert iw<=1e-7 or ih<=1e-7,(rm['id'],'overlaps court')
            rooms.append({'drawing':d.key,**rm})
        for i,a in enumerate(d.rooms):
            for b in d.rooms[i+1:]:
                iw=min(a['x']+a['w'],b['x']+b['w'])-max(a['x'],b['x'])
                ih=min(a['y']+a['h'],b['y']+b['h'])-max(a['y'],b['y'])
                assert iw<=1e-7 or ih<=1e-7,(d.key,a['id'],b['id'],'room overlap')
    # Check the actual emitted bay / column / aisle polygons, not just parameters.
    bd=next(d for d in drawings if d.key=='plan_basement_sweptpath')
    def bounds(z):
        pts,closed=z.data
        return min(x for x,y in pts),min(y for x,y in pts),max(x for x,y in pts),max(y for x,y in pts)
    bay_rects=[]
    for z in bd.items:
        if z.kind!='poly':continue
        x0,y0,x1,y1=bounds(z)
        if z.layer=='DIMENSIONS' and math.isclose(x1-x0,p.bay_w) and math.isclose(y1-y0,p.bay_d):bay_rects.append((x0,y0,x1,y1))
        if z.layer=='COLUMNS':
            assert min(x1,16.75)-max(x0,9.55)<=1e-8 or min(y1,10.85)-max(y0,4.85)<=1e-8,'column in aisle'
    assert len(bay_rects)==6
    assert any(z.kind=='poly' and z.layer=='AREA_BOUNDARY' and all(math.isclose(a,b) for a,b in zip(bounds(z),(9.55,4.85,16.75,10.85))) for z in bd.items)
    for d in drawings:
        if not (d.key.startswith('plan_') or d.key=='site_survey'):continue
        assert any(z.kind=='poly' and z.layer=='SITE_BOUNDARY' and all(math.isclose(a,b) for a,b in zip(bounds(z),(0,0,17,25))) for z in d.items)
    tests.extend([{'check':'room_reservations_no_overlap_or_court_intrusion','pass':True},
      {'check':'portrait_north_up_17EW_25NS','pass':True},
      {'check':'pool_outer_shell_and_both_1_50m_buffers','pass':True},
      {'check':'six_bays_and_column_free_6m_aisle','pass':True},
      {'check':'diagonal_P4_P2','actual_m':math.hypot(p.plot_w,p.plot_d),'display_m':30.23,'pass':True}])
    return tests,rooms


def boards(p):
    """Self-contained HTML: embeds the generated, text-outlined SVGs; no network fonts."""
    def art(name,cls=''):
        content=(BOARD_ASSET_DIR/f'{name}.svg').read_text()
        content=content[content.index('<svg'):]
        prefix=name+'-'
        content=re.sub(r'id="([^"]+)"',lambda m:'id="'+prefix+m.group(1)+'"',content)
        content=re.sub(r'((?:xlink:)?href)="#([^"]+)"',lambda m:m.group(1)+'="#'+prefix+m.group(2)+'"',content)
        content=re.sub(r'url\(#([^)]+)\)',lambda m:'url(#'+prefix+m.group(1)+')',content)
        content=content.replace('<svg ',f'<svg preserveAspectRatio="xMidYMin meet" class="{cls}" role="img" aria-label="{name.replace("_"," ")}" ',1)
        return content
    def frame(num,title,subtitle,asset,cls=''):
        facts={'plan_basement_sweptpath':'6 COMPACT BAYS / 6.00 m CLEAR AISLE<br>Ri 3.20 / Ro 5.80 m turning envelopes<br>3.00 m west ramp strip (20% / 16.00 m run)','plan_ground':'13.00 x 17.00 - 8.50 = 212.50 m²<br>2.50 x 3.40 m open-sky court<br>1.50 + 3.00 + 1.50 = 6.00 m garden','plan_typical':'13.75 x 17.6181818 - 8.50 = 233.75 m²<br>55.00% / each of three floors<br>North reception / three east bedrooms','plan_roof':'12.50 x 8.50 = 106.25 m²<br>25.00% enclosed / level +13.65 m<br>Open court maintained; PV terrace beyond'}
        fact=f'<p class="plan-fact">{facts[asset]}</p>' if asset in facts else ''
        return f'<section class="drawing {cls}"><div class="caption"><b>{num}</b><h2>{title}</h2></div><p class="sub">{subtitle}</p><div class="art">{art(asset)}</div>{fact}</section>'
    base='''*{box-sizing:border-box}html,body{margin:0;padding:0;width:1600px;height:1200px;background:#f6f3eb;color:#253b3d}body{font-family:"Helvetica Neue",Arial,sans-serif} .board{width:1600px;height:1200px;padding:40px 44px 30px;display:flex;flex-direction:column;gap:20px}header{height:132px;flex:none;display:grid;grid-template-columns:104px 1fr 338px;gap:24px;border-bottom:3px solid #253b3d;padding-bottom:18px}.number{font-size:100px;line-height:.92;font-weight:300;letter-spacing:-7px}.kicker{font:12px Menlo,monospace;letter-spacing:1.8px;margin:0 0 9px}h1{font-size:43px;line-height:1.06;letter-spacing:-1.7px;margin:0 0 10px;font-weight:600}header p{margin:0;font-size:15px;line-height:1.4}.meta{padding-left:20px;border-left:1px solid #b5bfba}.meta strong{display:block;font:700 13px Menlo,monospace;line-height:1.5;color:#087c83}.meta p{font-size:13px;margin-top:9px;line-height:1.5}.caption{display:flex;gap:11px;align-items:baseline;border-top:1px solid #253b3d;padding-top:10px}.caption b{font:12px Menlo,monospace;color:#087c83}h2{font-size:21px;line-height:1.2;letter-spacing:-.5px;margin:0;font-weight:600}.sub{font-size:12px;line-height:1.4;margin:5px 0 7px;color:#657473}.drawing{display:flex;flex-direction:column;min-height:0;min-width:0}.art{min-height:0;flex:1;display:flex;align-items:center;justify-content:center}.art svg{width:100%;height:100%;display:block}.notes{font-size:13px;line-height:1.5;margin-top:8px}.notes strong{color:#087c83}.legend{display:flex;gap:20px;font-size:12px;align-items:center}.legend i{display:inline-block;width:24px;height:3px;vertical-align:middle;margin-right:7px;background:#253b3d}.legend .teal{background:#087c83}.legend .amber{background:#a96519}.legend .red{background:#a84332}footer{height:44px;flex:none;border-top:1px solid #253b3d;padding-top:12px;font:11px Menlo,monospace;display:flex;justify-content:space-between;align-items:flex-start;gap:20px} .hold{color:#087c83} .small{font-size:11px;color:#657473}.facts{display:grid;grid-template-columns:repeat(4,1fr);border-top:1px solid #b7c2bb;margin-top:10px;padding-top:12px;gap:10px}.facts b{display:block;font:600 25px Menlo,monospace;letter-spacing:-1px}.facts span{font-size:12px;color:#657473}.strip{border-top:1px solid #253b3d;padding-top:10px;display:flex;justify-content:space-between;gap:20px;font-size:12px;line-height:1.5}.strip strong{color:#087c83}.board-one .main{flex:1;min-height:0;display:grid;grid-template-columns:repeat(4,1fr);gap:18px}.board-one .right{display:contents}.plan-fact{font:12px/1.8 Menlo,monospace;border-top:1px solid #b7c2bb;padding-top:14px;margin:0;height:125px;flex:none;color:#087c83}.board-one .strip{height:76px;flex:none}.board-two .main{flex:1;min-height:0;display:grid;grid-template-columns:936px 552px;grid-template-rows:493px 395px;gap:20px 24px}.board-two .bottom{display:flex;flex-direction:column;min-height:0}.area{width:100%;border-collapse:collapse;margin-top:10px;font-size:13px;line-height:1.4}.area th{font-size:11px;letter-spacing:.7px;color:#657473;text-align:left;font-weight:500;padding:7px 6px;border-bottom:1px solid #253b3d}.area td{padding:7px 6px;border-bottom:1px solid #c7cec7}.area th:nth-child(n+2),.area td:nth-child(n+2){text-align:right;font-family:Menlo,monospace}.area tr:last-child td{font-weight:600;border-bottom:1px solid #253b3d}.waste{display:grid;grid-template-columns:1fr 1fr;gap:10px 20px;font-size:12px;line-height:1.4;margin-top:15px}.waste b{display:block;font-size:13px;margin-bottom:3px}.board-two .sub{font-size:12px}.board-two .notes{font-size:12px}@media print{@page{size:1600px 1200px;margin:0}html,body{print-color-adjust:exact;-webkit-print-color-adjust:exact}}'''
    def head(n,title,sub):return f'''<header><div class="number">{n}</div><div><p class="kicker">PLOT 83 / SECTOR B / NEW CAIRO CITY</p><h1>{title}</h1><p>{sub}</p></div><div class="meta"><strong>ARCHITECTURAL CAD MASTER SET<br>NORTH UP · SURVEY ORIENTATION</strong><p>CONTEST #2800443 · B+G+3+R<br>17.00 × 25.00 m · 425.00 m²<br>P4–P2 diagonal: {math.hypot(p.plot_w,p.plot_d):.2f} m</p></div></header>'''
    foot='<footer><span>ARCHITECTURAL DESIGN TEAM / DETERMINISTIC 2D CAD SET / PLOT 83 NEW CAIRO</span><span class="hold">17.00 m (E–W North Road P4–P1) × 25.00 m (N–S East Spine P1–P2) · Millimetre-true DXF + Vector PDF</span><span>3200 × 2400</span></footer>'
    b1=head('01','Residential floor plans','North-facing living · East-facing bedrooms · Independent southern pool')
    b1+='<div class="main">'
    b1+=frame('B1','Basement & parking','6 compact stalls · 6.00 m aisle · Ri 3.20 / Ro 5.80 m swept path','plan_basement_sweptpath')
    b1+=frame('G','Ground floor','212.50 m² / 50% · Open court deducted · Northern main entry','plan_ground')
    b1+=frame('01–03','Typical apartment','233.75 m² / 55% · Open court deducted · One residence on each of 3 floors','plan_typical')
    b1+=frame('R','Roof level','106.25 m² enclosed / 25% · PV + resource recovery','plan_roof')+'</div>'
    b1+=f'''<div class="strip"><div><strong>01 / RAMP GEOMETRY</strong><br>3.20 ÷ 0.20 = {p.ramp_run:.2f} m run along 3.00 m west strip.<br>Direct entry from 15.00 m North Road beside Neighbor Plot 84.</div><div><strong>02 / POOL SEPARATION</strong><br>6.00 × 3.00 m outer shell; 5.60 × 2.60 m clear water.<br>1.50 m insulated buffer + 3.00 m pool + 1.50 m south fence clearance = 6.00 m.</div><div><strong>03 / DIMENSIONED ROOM SCHEDULE</strong><br>Every room labeled with explicit Width × Length (m) and area (m²).<br>2.50 × 3.40 m (8.50 m²) central wind court deducted from enclosed area.</div></div>'''+foot
    b2=head('02','Passive design & core study','Section A–A · Calculated solar geometry · Core alternatives · Resource strategy')
    b2+='<div class="main">'+frame('A–A','Climate, section & pool interface','Levels in metres · Four 3.30 m storeys above ground floor · Sunken courtyard daylighting','section_aa')+frame('P','Sun path / prevailing breeze','North-up sky plot · Sun paths calculated at 30.03° N','passive_sun_wind_diagram')
    b2+=frame('C','Stair + elevator alternatives','Same drawing scale · Option B selected for compact 27.40 m² core footprint','core_options_comparison')
    b2+='''<section class="bottom"><div class="caption"><b>S</b><h2>Area & resource schedule</h2></div><table class="area"><thead><tr><th>LEVEL</th><th>EACH m²</th><th>COUNT</th><th>SITE %</th></tr></thead><tbody>'''
    for n,a,c,r in [('Ground',p.land*p.ground_ratio,1,p.ground_ratio),('Typical',p.land*p.typical_ratio,3,p.typical_ratio),('Roof enclosed',p.land*p.roof_ratio,1,p.roof_ratio)]:
        b2+=f'<tr><td>{n}</td><td>{a:.2f}</td><td>{c}</td><td>{r:.0%}</td></tr>'
    total=p.land*(p.ground_ratio+3*p.typical_ratio+p.roof_ratio)
    b2+=f'<tr><td>Above-ground total</td><td>{total:.2f}</td><td>5</td><td>{p.ground_ratio+3*p.typical_ratio+p.roof_ratio:.0%}</td></tr></tbody></table>'
    b2+='''<div class="waste"><div><b>01 / Separate at source</b>Three-stream sorting room; isolated chute. Organics collected separately.</div><div><b>02 / Recover water</b>Greywater treatment to irrigation. Blackwater and pool water kept separate.</div><div><b>03 / Build for reuse</b>Modular partitions, bolted assemblies, local durable finishes; cut-list planning.</div><div><b>04 / Reduce demand</b>West solar screens, north/east openings, insulated envelope, PV pergola.</div></div><p class="notes"><strong>Passive cross-ventilation & zero-waste strategy:</strong> North breeze intake across reception to central wind court stack exhaust; roof PV pergola & greywater recycling.</p></section></div>'''+foot
    for i,body in [(1,b1),(2,b2)]:
        doc=f'<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=1600,initial-scale=1"><title>Plot 83 / Engineering Board {i}</title><style>{base}</style></head><body><main class="board board-{ "one" if i==1 else "two" }">{body}</main></body></html>'
        (ROOT/f'board{i}-codex.html').write_text(doc,encoding='utf-8')


def write_notes(p,tests,rooms,issues,dxf_check,out):
    report={'status':'PORTRAIT_ORIENTATION_CORRECTED_SCHEMATIC', 'construction_compliance':False,
      'source':'brief_assets/.png, employer survey; current correction requirements',
      'coordinate_system':{'origin':'P3 SW','x':'east','y':'north','points_m':{'P4':[0,25],'P1':[17,25],'P3':[0,0],'P2':[17,0]}},
      'parameters':dataclasses.asdict(p),'geometry_checks':tests,'rooms':rooms,'dxf':dxf_check,'unresolved':issues,
      'area_calculations':{'ground':{'outer_m2':221,'court_m2':8.5,'enclosed_m2':212.5},'typical':{'width_m':13.75,'depth_m':p.tf_depth,'outer_m2':242.25,'court_m2':8.5,'enclosed_m2':233.75},'roof':{'width_m':12.5,'depth_m':8.5,'enclosed_m2':106.25}},
      'pool':{'dimension_basis':'outside structural shell','outer_m':[6,3],'clear_water_m':[5.6,2.6],'north_buffer_m':1.5,'south_fence_clearance_m':1.5,'garden_depth_m':6},
      'swept_path':{'method':'Annular geometric envelope, not kinematic vehicle simulation','r_inner_m':p.inner_r,'r_outer_m':p.outer_r,'six_vehicle_routes_verified':False,'ramp_connection':'UNRESOLVED'},
      'solar':{'latitude_assumed':p.latitude},'room_measurement':'schematic clear rectangular reservations; areas computed from dimensions'}
    (out/'engineering_validation.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    notes=["# Plot 83 / Portrait orientation correction", "", "Rebuild: `python3 build_cad_2800443.py` followed by `python3 build_claude_boards.py` and delivery rendering.", "",
      "The employer survey governs: north road P4–P1 =17m, east spine P1–P2 =25m, west Plot84 P4–P3 =25m, south Plot10 P3–P2 =17m. North is up. P4–P2 =30.2324329157m, displayed30.23m.", "",
      "All plan exports share the same geometric primitives. Screen drawing coordinates run south from the north edge; DXF local coordinates are X east and Y north, P3=(0,0). Drawing x offsets are recorded in engineering_validation.json; subtract each offset to recover the surveyed coordinates. DXF units are millimetres.", "",
      "Ground: world X=3.50..16.50, Y=6.00..23.00; 13.00×17.00=221.00 minus2.50×3.40=8.50 open court gives212.50m² (50%).",
      f"Typical: world X=3.00..16.75, Y=6.00..{25-p.tf_front_y:.9f}; 13.75×{p.tf_depth:.9f}=242.25 minus8.50 gives233.75m² (55%). The depth rounds to17.62m; treating17.62 as exact would add0.025m².",
      "Roof:12.50×8.50=106.25m² (25%), level+13.65m. The court stays open outside the roof enclosure.", "",
      "Pool:6.00×3.00m is the outside structural-shell footprint. A200mm shell lies INSIDE that footprint, leaving5.60×2.60m clear water. The south garden is exactly1.50m insulated structural buffer +3.00m pool shell +1.50m fence clearance=6.00m. A6×3m CLEAR-WATER pool plus shell cannot satisfy those exact dimensions inside a6m garden. The lowered, retained buffer permits a conceptual basement overlook; foundation and water details are pending.", "",
      "Basement has six2.40×4.60m compact bays, a6.00m aisle with no drawn columns, family sitting facing the sunken pool court, kitchenette,2WCs, gym, storage, electrical and water rooms. Ri3.2/Ro5.8 are geometric turning envelopes only. The3m west ramp strip has a nominal20%/16m run to−3.20m; its landing, grade transitions, wall deductions and connection to the parking aisle remain unresolved. Do not present six-car access as verified.", "",
      "Room dimensions and areas are schematic rectangular reservations. Door access, wall offsets, fire and structure need design development. Coverage is a geometric calculation, not local-authority approval. The package is not for construction.", "", "## Remaining design work", ""]
    for item in issues:notes.extend([f"### {item['id']} / {item['title']}",item['short'],item['detail'],""])
    notes.extend(["## Outputs", "DXF,9-page vector PDF,10 individual SVG/PNG drawings,parameters,validation and manifest; board HTML and final JPG copies rebuilt by the delivery renderer. No submission or deployment performed."])
    (ROOT/'ENGINEERING_NOTES.md').write_text('\n'.join(notes)+'\n',encoding='utf-8')
    rows=[('Survey17EW×25NS,N-up,P4-P2 diagonal','site_survey and all four plans','Verified geometry'),('Ground221−8.5=212.5m2','plan_ground','Verified geometry'),('Typical242.25−8.5=233.75m2','plan_typical; exact depth17.618181818m','Verified geometry'),('Roof12.5×8.5=106.25m2 at+13.65','plan_roof','Verified geometry'),('2.5×3.4 open-sky court','Ground/typical; remains open at roof','Verified plan geometry'),('Pool6×3 outside shell and both1.5m clearances','Plans + section; clear water5.6×2.6','Verified geometry; dimensional basis disclosed'),('6 stalls /6m aisle /Ri3.2 Ro5.8','Basement plan','Drawn; vehicle routes and ramp link UNRESOLVED'),('3m west ramp from north road','Basement and ground','Strip verified; slope/transitions/local permissions unresolved'),('Family sitting, kitchenette,2WC,gym,store,electric,water','Basement room schedule','Drawn; detailed egress pending'),('North reception,east3bedrooms,west kitchen/baths','Typical plan','Verified positioning'),('Every labeled room width,length and area','All room records and labels','Verified generated labels'),('Local code,structure,fire,services','Engineering hold points','Not certified')]
    (out/'requirement_matrix.md').write_text('# Requirement matrix / orientation correction\n\n| Requirement | Evidence | Status |\n|---|---|---|\n'+'\n'.join('| '+' | '.join(row)+' |' for row in rows)+'\n')


def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--config',type=pathlib.Path);ap.add_argument('--out',type=pathlib.Path,default=ROOT/'exports');ap.add_argument('--write-default-config',type=pathlib.Path)
    args=ap.parse_args();p=Parameters()
    if args.write_default_config:
        args.write_default_config.write_text(json.dumps(dataclasses.asdict(p),indent=2)+'\n');return
    if args.config:p=Parameters(**json.loads(args.config.read_text()))
    out=args.out.resolve();out.mkdir(parents=True,exist_ok=True)
    # HTML assets are embedded from the selected output directory.
    ds=[basement(p),ground(p),typical(p),roof(p),section(p),passive(p),cores(p),survey(p)]
    tests,rooms=validate_geometry(ds,p);issues=engineering_issues(p);ds.append(schedule_drawing(p,issues))
    svg_files=[]
    for d in ds:
        f=out/(d.key+'.svg');svg(d,f);svg_files.append(f)
        png=f.with_suffix('.png');raster=fitz.open(stream=f.read_bytes(),filetype='svg');raster[0].get_pixmap(matrix=fitz.Matrix(2,2),alpha=False).save(png);raster.close();svg_files.append(png)
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
    raster=fitz.open(stream=(out/'plan_roof_section.svg').read_bytes(),filetype='svg');raster[0].get_pixmap(matrix=fitz.Matrix(2,2),alpha=False).save(out/'plan_roof_section.png');raster.close();svg_files.append(out/'plan_roof_section.png')
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
