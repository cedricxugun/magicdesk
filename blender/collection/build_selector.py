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
origin=Vector((-.657,-.939,.50));lifted=Vector((-.657,-.939,.735))
for i in range(3):
    p=B.part('Rail'+str(i),(0,0,0),.9)
    def rail_move(o,t,index=i):
        lift=window(t,.23,.42);extension=window(t,.44,.71)
        home=[origin,Vector((-.60,-.92,.55)),Vector((-.64,-.86,.585))][index]
        raised=Vector((home.x,home.y,.735))
        target=[lifted+Vector((-.574,-.819,0))*.30,Vector((-1.20,-1.318,.735)),Vector((-1.53,-1.318,.735))][index]
        o.location=home.lerp(raised,lift).lerp(target,extension)
        o.rotation_euler=(0,0,math.radians(-125) if index==0 else 0)
    r=B.control('Rail'+str(i),p,rail_move)
    length=.32 if i==0 else .52
    width=[.105,.085,.055][i];height=[.060,.046,.025][i]
    for z in [-height/2,height/2]:B.cube('ChannelFlange',(length,width,.009),'Chrome',r,(0,0,z),.003)
    B.cube('ChannelWeb',(length,.012,height),'Steel',r,(0,width/2,0),.003)
    B.tube('ArchiveSignalRail',[(-length/2,-width/2,.012),(length/2,-width/2,.012)],.004,'Glow',r,1)
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
        carriage=home+Vector((0,0,.225))*lift+Vector((-.42,-.30,0))*window(t,.44,.64)
        target=Vector((-2.82+index*.305,-1.34,.81))
        o.location=carriage.lerp(target,unfold)
        o.rotation_euler=(math.pi/2*(1-unfold),0,math.radians(-125)*(1-unfold)+math.radians((index-2.5)*-3)*unfold)
    c=B.control('Plaque'+str(i),p,card_move);cards.append(c.name)
    B.cube('PlaqueBacking',(.246,.002,.39),'Black',c,(0,.001,.21),.001)
    for x in [-.13,.13]:B.cube('PlaqueFrame',(.016,.014,.415),'Chrome',c,(x,0,.21),.004)
    for z in [.004,.416]:B.cube('PlaqueFrame',(.27,.014,.016),'Chrome',c,(0,0,z),.004)
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
        carriage=lifted+Vector((-.42,-.30,0))*window(t,.44,.64)
        target=Vector((-2.82+index*.305,-1.324,.779))
        o.location=carriage.lerp(target,window(t,.62,.84))
    c=B.control('PlaqueCarrier'+str(i),support,support_move)
    B.cube('CarrierRail',(.291,.043,.010),'Steel',c,(0,0,0),.003)
    B.beam('CarrierTrim',(-.145,-.024,.012),(.145,-.024,.012),.006,'Chrome',c)
    B.cyl('RailArticulation',.018,.055,'Chrome',c,(.1525,0,0),(math.pi/2,0,0),24)

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

# Visible porcelain cowl, placed outside the actuator sweep without scaling
# the authoritative circular base. It drapes over the upper fascia like the
# approved reference, rather than disappearing into a thin metallic plate.
cowl=B.part('ArchiveCowl',(0,0,0),.9)
press=B.control('CowlPress',cowl,lambda o,t:setattr(o,'location',(0,0,-.006*window(t,0,.06))))
click_surfaces=['S_PressureStrip','S_HatchCover'];latches=[]
for side,a0,a1 in [(-1,-142,-123.2),(1,-122.8,-104)]:
    hinge_angle=math.radians(a0 if side<0 else a1)
    pivot=Vector((1.45*math.cos(hinge_angle),1.45*math.sin(hinge_angle),.50))
    def open_cowl(o,t,s=side,angle=hinge_angle,at=pivot.copy()):
        from mathutils import Quaternion
        o.location=at;o.rotation_mode='QUATERNION';o.rotation_quaternion=Quaternion(Vector((0,0,1)),s*math.radians(92)*window(t,.10,.30))
    leaf=B.control('CowlLeaf'+str(side),press,open_cowl)
    vertices=[];faces=[];uv=[];steps=36;n=steps+1
    bands=20
    for band in range(bands):
        for j in range(n):
            degrees=a0+(a1-a0)*j/steps;a=math.radians(degrees)
            arch=math.sin(math.pi*(degrees+142)/38)**.72
            if band==0:radius,height=1.405,.615
            elif band==bands-1:radius,height=1.405,.625+.165*arch
            else:
                v=(band-1)/(bands-3)
                radius=1.455-.015*v+.085*math.sin(math.pi*v)
                height=.490+(.020+.280*arch)*v
            vertices.append(Vector((radius*math.cos(a),radius*math.sin(a),height))-pivot);uv.append((j/steps,band/(bands-1)))
    for band in range(bands):
        for j in range(steps):faces.append((band*n+j,band*n+j+1,((band+1)%bands)*n+j+1,((band+1)%bands)*n+j))
    faces.extend([tuple(i*n for i in range(bands)),tuple(i*n+n-1 for i in range(bands-1,-1,-1))])
    name='S_IvoryCowl_'+str(side)
    shell=B.fast['fast_instance'](name,vertices,faces,'Ivory',leaf,(0,0,0),smooth_faces=True,uv=uv)
    bevel=shell.modifiers.new('Porcelain edge radius','BEVEL');bevel.width=.005;bevel.segments=3;click_surfaces.append(name)
    for top in [False,True]:
        points=[]
        for j in range(n):
            degrees=a0+(a1-a0)*j/steps;a=math.radians(degrees)
            z=.51+.28*math.sin(math.pi*(degrees+142)/38)**.72 if top else .495
            radius=1.446 if top else 1.459
            points.append(Vector((radius*math.cos(a),radius*math.sin(a),z))-pivot)
        B.tube('CowlNickelBinding',points,.008,'Chrome',leaf)
    center_angle=math.radians(a1 if side<0 else a0)
    B.tube('CowlRedSeam',[Vector(((1.460-.015*v+.085*math.sin(math.pi*v))*math.cos(center_angle),(1.460-.015*v+.085*math.sin(math.pi*v))*math.sin(center_angle),.49+.30*v))-pivot for v in [j/30 for j in range(2,29)]],.004,'Glow',leaf)
    for degree in [a0+2,a1-2]:
        a=math.radians(degree)
        arch=math.sin(math.pi*(degree+142)/38)**.72;v=.35;radius=1.460-.015*v+.085*math.sin(math.pi*v);height=.49+(.02+.28*arch)*v
        B.screw(leaf,Vector((radius*math.cos(a),radius*math.sin(a),height))-pivot,(math.cos(a),math.sin(a),0),.012)
    B.joint(press,pivot,.041,(math.cos(hinge_angle),math.sin(hinge_angle),0))
    latch=B.control('Latch'+str(side),press,lambda o,t,s=side,at=pivot.copy(): (setattr(o,'location',at+Vector((0,0,.13))),setattr(o,'rotation_euler',(0,math.radians(58)*s*window(t,.03,.13),0))))
    B.cube('LatchPawl',(.055,.047,.09),'Steel',latch,(0,0,.02),.012);B.cyl('LatchPin',.025,.068,'Chrome',latch,(0,0,0),(math.pi/2,0,0),24);latches.append(latch.name)

scan_controls=[];scanner_aims=[];scanner_emitters=[]
for i,degrees in enumerate([-32,-164,90]):
    a=math.radians(degrees);at=Vector((1.44*math.cos(a),1.44*math.sin(a),.595))
    mount=B.part('ScannerMount'+str(i),(0,0,0),.9)
    B.cyl('ScannerFoot',.064,.055,'Steel',mount,at)
    inner=Vector((1.34*math.cos(a),1.34*math.sin(a),.585))
    B.beam('ScannerBracket',inner,at,.025,'Chrome',mount)
    B.sleeve('ScannerSleeve',.044,.030,.115,'Chrome',mount,at+Vector((0,0,.045)))
    lift=B.control('ScannerLift'+str(i),mount,lambda o,t,p=at.copy():setattr(o,'location',p+Vector((0,0,.06+.24*window(t,0,1)))))
    scan_controls.append(lift.name)
    for stage in range(3):
        piston=B.control('ScannerStage%d_%d'%(i,stage),mount,lambda o,t,p=at.copy(),k=stage:setattr(o,'location',p+Vector((0,0,.035+.08*(k+1)*window(t,0,1)))))
        scan_controls.append(piston.name)
        if stage<2:B.sleeve('ScannerTelescope',[.028,.021][stage],[.023,.017][stage],.12,'Chrome',piston)
        else:B.cyl('ScannerTelescope',.015,.12,'Chrome',piston)
    aim=B.empty('S_SCANNER_AIM_'+str(i),lift,(0,0,.01));aim.rotation_euler=(0,0,a+math.pi/2);scanner_aims.append(aim.name)
    B.cube('ScannerOptics',(.10,.13,.07),'Steel',aim,(0,0,0),.025)
    B.cyl('ScannerLens',.039,.06,'Chrome',aim,(0,-.073,0),(math.pi/2,0,0),40)
    B.cyl('ScannerAperture',.027,.005,'Red',aim,(0,-.106,0),(math.pi/2,0,0),32)
    emitter=B.socket('scanner_'+str(i),aim,(0,-.111,0));scanner_emitters.append(emitter.name)
B.extra.update({'click_surfaces':click_surfaces,'scan_controls':scan_controls,'scanner_aims':scanner_aims,'scanner_emitters':scanner_emitters,'selector_duration':2.0,'latches':latches,'visible_cowl':True})
B.export()
