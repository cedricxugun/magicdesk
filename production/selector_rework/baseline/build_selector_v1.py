import sys,math
from pathlib import Path
import bpy
from mathutils import Vector
sys.path.insert(0,str(Path(__file__).resolve().parent))
from geometry import Builder,window

B=Builder('S','机械档案匣')

def sector(name,r0,r1,a0,a1,z,thickness,key,parent):
    verts=[];faces=[];steps=32
    for zz in [z-thickness/2,z+thickness/2]:
        for radius in [r0,r1]:
            for i in range(steps+1):
                a=math.radians(a0+(a1-a0)*i/steps);verts.append((radius*math.cos(a),radius*math.sin(a),zz))
    n=steps+1
    for i in range(steps):
        faces.extend([(i,i+1,n+i+1,n+i),(2*n+i,3*n+i,3*n+i+1,2*n+i+1),(i,2*n+i,2*n+i+1,i+1),(n+i,n+i+1,3*n+i+1,3*n+i)])
    faces.extend([(0,n,3*n,2*n),(n-1,3*n-1,4*n-1,2*n-1)])
    return B.fast['fast_instance'](name,verts,faces,key,parent,(0,0,0),smooth_faces=False)

fixed=B.part('Pocket',(0,0,0),.9)
sector('S_PocketFloor',.70,1.35,-140,-105,.466,.006,'Black',fixed)
sector('S_InnerPocketCover',.70,1.01,-140,-105,.569,.012,'Steel',fixed)
cover=B.part('Hatch',(0,0,0),.9)
def hatch(o,t):
    down=window(t,0,.18);slide=window(t,.10,.30)
    o.location=(.574*.30*slide,.819*.30*slide,-.070*down)
c=B.control('HatchSlide',cover,hatch)
sector('S_HatchCover',1.012,1.344,-140,-105,.62,.008,'Chrome',c)
strip=B.part('PressureStrip',(0,0,0),.9)
def press_move(o,t):o.location.z=-.007*window(t,0,.08)
press=B.control('PressureTravel',strip,press_move)
sector('S_PressureStrip',1.29,1.348,-133,-114,.635,.010,'Chrome',press)
sector('S_SeamLight',1.287,1.293,-133,-114,.632,.003,'Glow',press)
rail=B.part('Carriage',(0,0,0),.9)
origin=Vector((-.688,-.983,.50));lifted=Vector((-.688,-.983,.71))
for i in range(3):
    p=B.part('Rail'+str(i),(0,0,0),.9)
    def rail_move(o,t,index=i):
        lift=window(t,.23,.42);extension=window(t,.44,.71)
        o.location=origin.lerp(lifted,lift)+Vector((-.35-index*.29,.08+index*.03,0))*extension
    r=B.control('Rail'+str(i),p,rail_move)
    B.cube('TelescopicRail',(.43,.09,.025),'Steel',r,(0,0,0),.008)
    for y in [-.042,.042]:B.beam('RailLip',(-.215,y,.015),(.215,y,.015),.008,'Chrome',r)
    for x in [-.15,.15]:B.screw(r,(x,0,.02),(0,0,1),.011)
    if i==2:
        spindle=B.empty('S_INDEX_SPINDLE',r,(.25,-.09,.045))
        B.cyl('IndexRoller',.065,.055,'Steel',spindle)
        B.torus('IndexRollerRing',.060,.006,'Chrome',spindle,(0,0,.030))
        for tooth in range(20):
            a=tooth*math.tau/20;B.cube('IndexKnurl',(.012,.008,.05),'Chrome',spindle,(.061*math.cos(a),.061*math.sin(a),0),.002,(0,0,a))
        B.cube('IndexPointer',(.011,.049,.003),'Red',spindle,(0,.018,.029),.001)
        B.extra['index_spindle']=spindle.name

cards=[]
for i in range(6):
    p=B.part('Plaque'+str(i),(0,0,0),.9)
    def card_move(o,t,index=i):
        lift=window(t,.24,.43);extend=window(t,.44,.71)
        unfold=window(t,.65+(5-index)*.025,.84+(5-index)*.025)
        home=Vector((-.491+.819*(index-2.5)*.026,-1.079-.574*(index-2.5)*.026,.482+index*.0205))
        carriage=home+Vector((0,0,.225))*lift+Vector((-1.05,.26,0))*extend
        target=Vector((-2.82+index*.305,-.78,.78+abs(index-2.5)*.008))
        o.location=carriage.lerp(target,unfold)
        o.rotation_euler=(math.pi/2*(1-unfold),0,math.radians(-125)*(1-unfold)+math.radians((index-2.5)*-3)*unfold)
    c=B.control('Plaque'+str(i),p,card_move);cards.append(c.name)
    B.cube('PlaqueBacking',(.246,.002,.39),'Black',c,(0,.001,.21),.001)
    for x in [-.13,.13]:B.cube('PlaqueFrame',(.011,.006,.415),'Chrome',c,(x,0,.21),.003)
    for z in [.004,.416]:B.cube('PlaqueFrame',(.27,.006,.011),'Chrome',c,(0,0,z),.003)
    B.cube('EtchedGlass',(.239,.002,.387),'Glass',c,(0,-.002,.21),.001)
    B.cyl('OffsetHinge',.011,.020,'Steel',c,(.141,0,.02),(0,math.pi/2,0),24)
    B.cube('PlaqueFoot',(.29,.025,.025),'Steel',c,(0,.016,-.013),.004)
    for x in [-.119,.119]:
        for z in [.019,.40]:B.cyl('Rivet',.006,.002,'Copper',c,(x,-.004,z),(math.pi/2,0,0),12)
B.extra['cards']=cards
B.extra['pressure_strip']=press.name
for i in range(6):
    support=B.part('PlaqueCarrier'+str(i),(0,0,0),.9)
    def support_move(o,t,index=i):
        home=Vector((-.76,-.86,.477+index*.021))
        lifted=home+Vector((0,0,.225))*window(t,.24,.43)
        carriage=lifted+Vector((-1.05,.16,0))*window(t,.44,.71)
        target=Vector((-2.82+index*.305,-.765,.749))
        o.location=carriage.lerp(target,window(t,.55,.82))
    c=B.control('PlaqueCarrier'+str(i),support,support_move)
    B.cube('CarrierRail',(.335,.043,.010),'Steel',c,(0,0,0),.003)
    B.beam('CarrierTrim',(-.168,-.024,.012),(.168,-.024,.012),.006,'Chrome',c)

widgets=B.empty('S_WIDGET_LIBRARY',B.root)
def widget(kind):
    o=B.empty('S_WIDGET_'+kind,widgets)
    B.cyl('WidgetSocket',.119,.025,'Steel',o,(0,0,0),(math.pi/2,0,0),48)
    B.torus('WidgetRim',.114,.009,'Chrome',o,(0,-.017,0),(math.pi/2,0,0))
    return o
button=widget('button')
B.cube('ButtonCap',(.166,.038,.166),'Ivory',button,(0,-.030,0),.024)
B.cube('ButtonStroke',(.011,.002,.050),'Red',button,(0,-.051,0),.002)
knob=widget('knob')
B.cyl('Knob',.092,.07,'Ivory',knob,(0,-.04,0),(math.pi/2,0,0),64)
for j in range(24):
    a=j*math.tau/24;B.beam('Knurl',(.093*math.cos(a),-.025,.093*math.sin(a)),(.093*math.cos(a),-.068,.093*math.sin(a)),.0035,'Steel',knob)
B.cube('DialIndex',(.009,.003,.064),'Red',knob,(0,-.077,.025),.002)
lever=widget('lever')
B.cube('LeverBed',(.09,.022,.19),'Black',lever,(0,-.02,0),.022)
B.beam('LeverStem',(0,-.03,-.025),(0,-.11,.07),.015,'Chrome',lever)
B.cube('LeverGrip',(.055,.039,.069),'Red',lever,(0,-.11,.085),.015)
rocker=widget('rocker')
for side in [-1,1]:
    B.cube('RockerWing',(.073,.04,.16),'Ivory',rocker,(side*.043,-.035,0),.02,(0,0,side*.08))
    B.cube('RockerMark',(.007,.003,.046),'Red',rocker,(side*.043,-.058,0),.001)
plate=B.empty('S_PANEL',B.root)
verts=[];faces=[];uv=[];steps=64
for z in [.16,.46]:
    for i in range(steps+1):
        a=math.radians(-136+92*i/steps);verts.append((1.367*math.cos(a),1.367*math.sin(a),z));uv.append((i/steps,(z-.16)/.30))
for i in range(steps):faces.append((i,i+1,steps+2+i,steps+1+i))
B.fast['fast_instance']('S_OperationCassette',verts,faces,'Ivory',plate,(0,0,0),smooth_faces=True,uv=uv)
backing=B.part('ControlPocketBacking',(0,0,0),.9)
B.fast['fast_instance']('S_ControlPocketBacking',[(x*.86,y*.86,z) for x,y,z in verts],faces,'Black',backing,(0,0,0),smooth_faces=True,uv=uv)
B.extra['widgets']={k:'S_WIDGET_'+k for k in ['button','knob','lever','rocker']}
B.export()
