import sys
import math
from pathlib import Path
import bpy
from mathutils import Vector
sys.path.insert(0,str(Path(__file__).resolve().parent))
from geometry import Builder, smooth, window, ROOT, ASSETS

def rod(B,name,endpoints,r=.024,offset=(0,0,.35),key='Chrome',telescopic=False):
    p=B.part(name,offset,.25)
    def update(o,t):
        a,b=[Vector(v) for v in endpoints(t)];v=b-a
        o.location=(a+b)*.5;o.rotation_mode='QUATERNION';o.rotation_quaternion=v.to_track_quat('Z','Y');o.scale=(1,1,v.length)
    c=B.control(name,p,update);B.cyl('Rod',r,1,key,c)
    if B.id=='F':
        for side in [-1,1]:B.cyl('LinkageParallelRail',r*.28,.82,'Chrome',c,(side*r*1.35,-r*.3,0),n=20)
        B.cyl('LinkageWeb',r*.6,.66,'Black',c,(0,-r*.6,0),n=20)
    if telescopic:
        minimum=min((Vector(endpoints(t)[1])-Vector(endpoints(t)[0])).length for t in [k/100 for k in range(101)])
        sleeve_length=min(.14,minimum*.70)
        def barrel(o,t):
            a,b=[Vector(v) for v in endpoints(t)];direction=(b-a).normalized()
            o.location=a+direction*sleeve_length*.5;o.rotation_mode='QUATERNION';o.rotation_quaternion=direction.to_track_quat('Z','Y')
        shell=B.control(name+'_barrel',p,barrel)
        B.sleeve('TelescopicSleeve',r*1.45,r*1.06,sleeve_length,'Steel',shell)
        for z in [-sleeve_length*.42,sleeve_length*.42]:B.torus('SleeveLip',r*1.45,.006,'Chrome',shell,(0,0,z))
    for index in [0,1]:
        j=B.control(name+'_end'+str(index),p,lambda o,t,k=index:setattr(o,'location',endpoints(t)[k]))
        B.joint(j,(0,0,0),r*2.4)
    return p

def gauge(B,parent,loc,r=.15):
    front=(math.pi/2,0,0)
    B.cyl('GaugeHousing',r,.055,'Steel',parent,loc,front)
    B.cyl('GaugeFace',r*.87,.004,'Ivory',parent,Vector(loc)+Vector((0,-.032,0)),front)
    B.torus('GaugeBezel',r*.91,.012,'Chrome',parent,Vector(loc)+Vector((0,-.038,0)),front)
    for i in range(13):
        a=math.radians(35+110*i/12)
        q=Vector(loc)+Vector((r*.68*math.cos(a),-.04,r*.68*math.sin(a)))
        B.cube('GaugeTick',(.005,.004,.021),'Black',parent,q,.001,(0,a-math.pi/2,0))
    n=B.rotor('GaugeNeedle'+str(B.serial),parent,'y',.8,.24)
    n.location=Vector(loc)+Vector((0,-.043,0))
    B.beam('Needle',(0,0,0),(.06,0,.08),.004,'Red',n)
    B.sphere('NeedleHub',.012,'Chrome',n)

def build_f():
    B=Builder('F','拉格朗日天平');B.pedestal_mount()
    p=B.part('ContinuousSpine',(0,.15,.45),.8)
    angles=[math.radians(60+240*i/120) for i in range(121)]
    pts=[(-.1+math.cos(a),.055,1.8+math.sin(a)) for a in angles]
    B.ribbon('Spine',pts,.084,.07,'Steel',p)
    B.ribbon('SpineGasket',[(x,-.005,z) for x,y,z in pts],.107,.032,'Black',p)
    for side in [-1,1]:
        B.tube('SpineEdge',[(-.1+(1+side*.113)*math.cos(a),-.02,1.8+(1+side*.113)*math.sin(a)) for a in angles],.014,'Chrome',p)
    for j in range(6):
        aa=angles[j*20+1:j*20+20]
        shell=B.part('SpineCover'+str(j),(.42*math.cos(aa[9]),-.27,.30*math.sin(aa[9])+.50),.2+j*.055)
        B.ribbon('CeramicSpine',[(-.1+math.cos(a),-.032,1.8+math.sin(a)) for a in aa],.097,.025,'Ivory',shell)
        for a in [aa[2],aa[-3]]:B.screw(shell,(-.1+math.cos(a),-.068,1.8+math.sin(a)),(0,-1,0),.014)
        if j==2:gauge(B,shell,(-1.04,-.075,1.97),.10)
        a=aa[9]
        B.cube('SpineServiceCatch',(.047,.037,.105),'Red',shell,(-.1+1.02*math.cos(a),.005,1.8+1.02*math.sin(a)),.012,(0,-a,0))
    for j in range(1,24):
        a=math.radians(60+j*10)
        for side in [-1,1]:
            radial=1+side*.12
            B.cyl('RadialSleeve',.017,.038,'Steel',p,(-.1+radial*math.cos(a),.055,1.8+radial*math.sin(a)),(math.pi/2,0,0),20)
    B.tube('SpineSignalBus',[(-.1+1.075*math.cos(a),.107,1.8+1.075*math.sin(a)) for a in angles],.008,'Red',p)
    B.beam('MountYoke',(0,0,.77),(.4,.055,.934),.065,'Steel',p)
    H=Vector((.4,-.055,2.64));Q=H+Vector((0,0,-.32))
    B.beam('FixedPivotYoke',H,Q,.045,'Steel',p)
    def end(t,lower=False):
        a=math.radians(-80+60*smooth(t));h=Q if lower else H
        return h+Vector((.82*math.cos(a),0,.82*math.sin(a)))
    rod(B,'UpperFourBar',lambda t:(H,end(t)),offset=(.2,-.3,.40))
    rod(B,'LowerFourBar',lambda t:(Q,end(t,True)),offset=(.45,.15,.20))
    rod(B,'Coupler',lambda t:(end(t),end(t,True)),offset=(.60,-.05,.2))
    drop=B.part('PrismWeight',(.75,.1,.28),.12)
    c=B.control('PrismHanger',drop,lambda o,t:setattr(o,'location',end(t,True)))
    B.cyl('PrismNeck',.025,.22,'Chrome',c,(0,0,-.10))
    B.cube('FacetedWeight',(.28,.25,.40),'Ivory',c,(0,0,-.37),.055)
    for z in [-.17,-.58]:B.cube('WeightFerrule',(.30,.27,.045),'Chrome',c,(0,0,z),.035)
    for x in [-.115,.115]:B.beam('WeightRail',(x,-.095,-.17),(x,-.095,-.58),.009,'Chrome',c)
    def pearl_end(t):
        a=math.radians(-145+35*smooth(t));return H+Vector((.66*math.cos(a),-.09,.66*math.sin(a)))
    rod(B,'CounterArm',lambda t:(H+Vector((0,-.09,0)),pearl_end(t)),offset=(-.45,-.15,.25))
    pearl=B.part('PearlWeight',(-.55,-.2,.2),.16)
    c=B.control('PearlHanger',pearl,lambda o,t:setattr(o,'location',pearl_end(t)))
    B.cyl('PearlNeck',.022,.20,'Chrome',c,(0,0,-.10))
    r=B.rotor('PearlSwing',c,'y',.9,.08);r.location=(0,0,-.2)
    B.sphere('Pearl',1,'Chrome',r,(0,0,-.25),(.15,.13,.25))
    for k in range(4):
        a=k*math.tau/4
        pts=[]
        for i in range(31):
            u=i/30;rr=.17*math.sin(u*math.pi)**.7;pts.append((rr*math.cos(a),rr*math.sin(a),-.5*u))
        B.tube('PearlRib',pts,.009,'Copper',r)
    B.socket('weight_tip',r,(0,0,-.5))
    for pos in [H,Q]:B.joint(p,pos,.075)
    B.socket('field',B.upper,(0,-.12,.80));return B

def build_g():
    B=Builder('G','折维书匣');B.pedestal_mount(.29)
    spine=B.part('Spine',(0,.32,.65),.8)
    B.cyl('SpineAxis',.085,1.95,'Steel',spine,(0,0,1.82))
    for z in [.87,1.05,1.5,2.,2.55,2.77]:
        B.cyl('SpineSleeve',.13,.075,'Chrome',spine,(0,0,z))
        B.torus('SpineCopper',.132,.01,'Copper',spine,(0,0,z))
    for z in [1.20,2.40]:B.cube('HingeComb',(.18,.32,.065),'Chrome',spine,(0,0,z),.013)
    for i in range(6):
        page=B.part('Page'+str(i),(.0,(i-2.5)*.22,.35),.15)
        def move(o,t,index=i):
            u=window(t,.35+index*.035,.80+index*.035)
            angle=math.radians(-150+index*30)*u
            extension=.55*window(t,.60,1.0)
            o.location=(extension*math.cos(angle),(index-2.5)*.045+extension*math.sin(angle),1.8+window(t,.6,1)*(index-2.5)*.035)
            o.rotation_euler=(0,0,angle)
        c=B.control('PageHinge'+str(i),page,move)
        B.panel('RigidPage',c,.76,1.50,.025,(.53,0,0))
        B.cyl('PagePin',.016,1.64,'Chrome',c,(.025,0,0))
        for z in [-.6,.6]:
            B.cube('PageHingeLug',(.18,.050,.09),'Steel',c,(.085,0,z),.012)
            B.cyl('LensSeat',.050,.025,'Chrome',c,(.57,-.025,z*.65),(math.pi/2,0,0),32)
            B.sphere('AmberLens',.034,'Glow',c,(.57,-.042,z*.65),(.95,.28,.95))
        B.socket('page_'+str(i),c,(.57,-.06,.15))
        B.beam('IndexNeedle',(.08,-.07,-.62),(.62,-.07,-.48),.005,'Chrome',c)
        for face in [-1,1]:
            # Real engraved metal routing plates and optical registration marks.
            B.cube('PageInset',(.52,.009,1.18),'Black',c,(.55,face*.020,0),.018)
            for track in range(4):
                x=.34+track*.12
                path=[(x,face*.027,-.48),(x,face*.027,-.13),(x+.045,face*.027,-.06),(x+.045,face*.027,.45)]
                B.tube('PageOpticalCircuit',path,.0035,'Copper',c,1)
            for row in range(9):
                z=-.48+row*.12
                B.beam('PageCoordinateTick',(.79,face*.028,z),(.83,face*.028,z),.0025,'Chrome',c)
        for x in [.165,.895]:B.beam('PageFrame',(x,.018,-.73),(x,.018,.73),.008,'Chrome',c)
        for sign in [-1,1]:
            def supports(t,index=i,sgn=sign):
                u=window(t,.35+index*.035,.80+index*.035);angle=math.radians(-150+index*30)*u
                extension=.55*window(t,.60,1.)
                height=1.8+sgn*.60
                a=Vector((0,(index-2.5)*.045,height))
                b=Vector(((extension+.12)*math.cos(angle),(index-2.5)*.045+(extension+.12)*math.sin(angle),height+window(t,.6,1)*(index-2.5)*.035))
                return a,b
            rod(B,'PageSupport%d_%d'%(i,sign),supports,.014,((i-2.5)*.18,.35,sign*.3+.4),telescopic=True)
    for side in [-1,1]:
        p=B.part('Cover'+str(side),(.0,side*.90,.35),.05)
        def cover(o,t,s=side):
            angle=math.radians((-175 if s<0 else 18)*window(t,0,.32))
            extension=.45*window(t,.15,.45)
            o.location=(extension*math.cos(angle),s*.205+extension*math.sin(angle),1.82)
            o.rotation_euler=(0,0,angle)
        c=B.control('CoverHinge'+str(side),p,cover)
        B.panel('ThickCover',c,.98,1.91,.07,(.50,0,0))
        B.cube('NickelCoverBack',(.89,.016,1.82),'Steel',c,(.50,.046,0),.025)
        for x in [.18,.36,.64,.82]:B.beam('CoverCircuit',(x,.060,-.75),(x,.060,.75),.004,'Copper',c)
        B.cyl('CoverAxle',.075,2.02,'Chrome',c,(.015,0,0))
        for z in [-.75,0,.75]:B.cyl('CoverSleeve',.105,.12,'Steel',c,(.015,0,z))
        if side==-1:
            B.cube('ArchiveLatch',(.19,.075,.29),'Red',c,(.70,-.09,-.10),.035)
            B.torus('LatchKeyhole',.05,.01,'Chrome',c,(.70,-.136,-.10),(math.pi/2,0,0))
        for sign in [-1,1]:
            def cover_support(t,s=side,sgn=sign):
                angle=math.radians((-175 if s<0 else 18)*window(t,0,.32));extension=.45*window(t,.15,.45)
                a=Vector((0,s*.205,1.82+sgn*.75))
                return a,a+Vector(((extension+.015)*math.cos(angle),extension*math.sin(angle),0))
            rod(B,'CoverSupport%d_%d'%(side,sign),cover_support,.017,(0,side*.9,.35),telescopic=True)
    B.socket('field',B.upper,(.18,-.15,1.90));return B

def build_i():
    B=Builder('I','回声海螺');B.pedestal_mount(.35)
    frame=B.part('SpiralSkeleton',(0,.25,.5),.8)
    def center(u):
        a=math.pi+math.tau*1.02*u;r=.72*(1-.79*u)
        return Vector((.06+r*math.cos(a),.13+.13*u,1.9+r*math.sin(a)))
    path=[center(i/180) for i in range(181)]
    B.tube('ContinuousSpiral',path,.052,'Chrome',frame)
    B.beam('LowerSupport',(0,0,.78),(-.15,.15,1.19),.055,'Steel',frame)
    B.beam('DiagonalSupport',(.25,.22,.68),(.54,.16,1.75),.038,'Chrome',frame)
    for j in range(6):
        u0=j/6+.008;u1=(j+1)/6-.008;um=(u0+u1)/2;pivot=center(um)
        radial=Vector((pivot.x-.06,0,pivot.z-1.9)).normalized()
        part=B.part('SpiralShell'+str(j),(radial.x*.52,-.30,.60+radial.z*.35),.10)
        def shift(o,t,index=j,at=pivot.copy(),middle=um):
            v=window(t,0,.85)
            o.location=at+Vector((at.x-.06,-.12,at.z-1.9))*.45*v
            o.rotation_euler=(0,0,0)
        c=B.control('ShellHinge'+str(j),part,shift)
        points=[center(u0+(u1-u0)*k/25)-pivot for k in range(26)]
        widths=[.42*(1-(u0+(u1-u0)*k/25))+.065 for k in range(26)]
        B.ribbon('SpiralPorcelain',points,widths,[w*.88 for w in widths],'Ivory',c)
        for u in [u0,u1]:
            cp=center(u)-pivot;tan=center(min(1,u+.001))-center(max(0,u-.001));r=.42*(1-u)+.065
            B.torus('ShellMetalLip',r,.012,'Chrome',c,cp,tan.to_track_quat('Z','Y'))
            B.joint(c,cp,.045)
        B.coil(c,(0,0,0),.06,.12,6)
        fixed_anchor=pivot+Vector((0,.14,0))
        B.beam('ShellGuideBracket',pivot,fixed_anchor,.025,'Steel',frame)
        def shell_guide(t,at=pivot.copy(),a=fixed_anchor.copy()):
            shift=Vector((at.x-.06,-.12,at.z-1.9))*.45*window(t,0,.85)
            return a,at+shift+Vector((0,.065,0))
        rod(B,'ShellGuide'+str(j),shell_guide,.017,(radial.x*.35,.24,.55+radial.z*.25),telescopic=True)
    B.apply_pose(0)
    cutter=B.cyl('ApertureCutter',.395,1.3,'Black',B.upper,(-.57,-.20,1.88),(math.pi/2,0,0),96)
    for name in list(B.qa_shells):
        obj=bpy.data.objects.get(name)
        if obj is None:continue
        modifier=obj.modifiers.new('True acoustic aperture','BOOLEAN');modifier.operation='DIFFERENCE';modifier.solver='EXACT';modifier.object=cutter
        bpy.context.view_layer.objects.active=obj
        bpy.ops.object.modifier_apply(modifier=modifier.name)
    bpy.data.objects.remove(cutter,do_unlink=True)
    mouth=B.part('Resonator',(-.6,-.5,.1),.18)
    m=B.control('Throat',mouth,lambda o,t:setattr(o,'location',(-.57,-.21-.10*window(t,.3,.8),1.88)))
    q=(math.pi/2,0,0)
    B.cyl('ResonatorDrum',.44,.14,'Black',m,(0,0,0),q,64)
    for r in [.29,.34,.41,.46]:B.torus('DiaphragmRing',r,.012,'Chrome',m,(0,-.08,0),q)
    for k in range(24):
        a=k*math.tau/24
        B.beam('ResonatorSpoke',(.10*math.cos(a),-.087,.10*math.sin(a)),(.40*math.cos(a),-.087,.40*math.sin(a)),.005,'Steel',m)
    B.cyl('ResonatorHub',.11,.08,'Steel',m,(0,-.1,0),q)
    B.coil(m,(0,-.15,0),.075,.09,7,(0,1,0))
    for k in range(3):
        a=k*math.tau/3;pos=(.10*math.cos(a),-.19,.10*math.sin(a));B.cyl('TuningFork',.013,.15,'Red',m,pos,q,24)
    B.socket('field',m,(0,-.20,0))
    gauge(B,m,(0,-.03,-.53),.1)
    return B

def leaf(B,parent,position,angle):
    p=B.part('Leaf'+str(B.serial),(.10*math.cos(angle),.22,.18),.2,parent)
    c=B.control('LeafPivot'+str(B.serial),p,lambda o,t:set_leaf(o,t,position,angle))
    def side(sign):return [(i/24*.43,sign*.105*math.sin(math.pi*i/24),.045*math.sin(math.pi*i/24)) for i in range(25)]
    B.tube('LeafPerimeter',side(1)+side(-1)[::-1],.012,'Ivory',c,2)
    B.beam('LeafMidrib',(0,0,0),(.43,0,0),.009,'Chrome',c)
    for j in range(1,6):
        u=j/7;point=(u*.43,0,.02)
        for sign in [-1,1]:B.beam('LeafVein',point,(min(.98,u+.16)*.43,sign*.105*math.sin(math.pi*(u+.10)),.033),.005,'Chrome',c)
    B.joint(c,(0,0,0),.033,(1,0,0))

def set_leaf(o,t,position,angle):
    o.location=position;o.rotation_euler=(0,math.radians(48)*(1-window(t,.2,.85)),angle)

def flower(B,parent,position,index):
    p=B.part('FlowerCore'+str(index),(0,0,.32),.45,parent)
    p.location=position
    B.cyl('BudCollar',.12,.11,'Chrome',p,(0,0,0))
    B.sphere('BudBearing',.105,'Chrome',p,(0,0,.055))
    B.cyl('GlassPistil',.025,.42,'Red',p,(0,0,.28))
    B.sphere('PistilTip',.035,'Glow',p,(0,0,.51))
    B.socket('flower_'+str(index),p,(0,0,.51))
    for j in range(5):
        pp=B.part('Petal%d_%d'%(index,j),(.24*math.cos(j*math.tau/5),.24*math.sin(j*math.tau/5),.17),.08+j*.04,parent=p)
        def open_petal(o,t,k=j,n=index):
            a=k*math.tau/5;o.location=(.05*math.cos(a),.05*math.sin(a),.055);o.rotation_euler=(0,math.radians(65)*window(t,.25+n*.09,.75+n*.09),a)
        c=B.control('BudPetal%d_%d'%(index,j),pp,open_petal)
        pts=[(.02+.12*math.sin(math.pi*k/24),0,.46*k/24) for k in range(25)]
        tangential=[.008+.065*math.sin(math.pi*k/24)**.7 for k in range(25)]
        thickness=[.004+.012*math.sin(math.pi*k/24) for k in range(25)]
        B.ribbon('GlazedBudPetal',pts,thickness,tangential,'Ivory',c)
        B.joint(c,(.035,0,.045),.018)

def build_j():
    B=Builder('J','汞芽温室');B.pedestal_mount(.34)
    low=B.part('TrunkBarrel',(0,.2,.2),.8)
    B.sleeve('TrunkBarrel',.18,.155,.53,'Ivory',low,(0,0,1.04))
    B.cyl('InnerTrunkRod',.085,.76,'Chrome',low,(0,0,1.22))
    for z in [.80,1.28]:B.torus('TrunkSeal',.18,.019,'Chrome',low,(0,0,z))
    trunk=B.part('UpperTrunk',(0,.3,.52),.6)
    B.extraction_route(trunk,[(0,(0,0,0)),(.55,(0,0,.70)),(1,(0,.3,.80))])
    B.extraction_route(low,[(0,(0,0,0)),(.55,(0,0,0)),(1,(0,.2,.20))])
    c=B.control('TrunkExtension',trunk,lambda o,t:setattr(o,'location',(0,0,.28*window(t,0,.5))))
    pts=[(.06*math.sin(i/40*math.pi),.02*math.sin(i/40*math.pi*2),1.11+i/40*.98) for i in range(41)]
    B.ribbon('TrunkPorcelain',pts,[.13-.07*i/40 for i in range(41)],.085,'Ivory',c)
    B.tube('RootCapillary',[(x+.13,y-.04,z) for x,y,z in pts],.012,'Red',c)
    for index,(side,height) in enumerate([(-1,1.53),(1,1.67),(0,2.0)]):
        branch=B.part('Branch'+str(index),(.4*side,.1,.28),.38,parent=c)
        def bend(o,t,s=side,h=height):
            o.location=(.025,0,h);o.rotation_euler=(0,math.radians(40)*(1-window(t,.1,.65)) if s else 0,math.pi if s<0 else 0)
        arm=B.control('BranchElbow'+str(index),branch,bend)
        path=[(u*.58 if side else u*.08,.015*math.sin(u*math.pi),u*.44) for u in [k/30 for k in range(31)]]
        B.tube('BranchSpine',path,.034,'Chrome',arm)
        B.tube('BranchCapillary',[(x,y-.052,z) for x,y,z in path],.008,'Red',arm)
        for k in [0,15,30]:B.joint(arm,path[k],.06)
        flower(B,arm,path[-1],index)
        leaf(B,arm,path[16],-.6);leaf(B,arm,path[22],1.0)
    B.socket('field',c,(0,0,1.65));return B

def hood_half(B,parent,side):
    verts=[];faces=[];uv=[];nu=32;nv=20
    for j in range(nv+1):
        v=(j+.02)/(nv+.02)*math.pi/2
        for i in range(nu+1):
            u=-math.pi/2+math.pi*i/nu
            verts.append((side*(1.10*math.sin(v)*math.cos(u)+.023)-side*1.10,.54*math.sin(v)*math.sin(u),.76*math.cos(v)))
            uv.append((i/nu,j/nv))
    for j in range(nv):
        for i in range(nu):
            q=j*(nu+1)+i;face=(q,q+1,q+nu+2,q+nu+1)
            faces.append(face if side>0 else face[::-1])
    o=B.fast['fast_instance'](B.name('PorcelainHood'),verts,faces,'Ivory',parent,(0,0,0),smooth_faces=True,uv=uv)
    s=o.modifiers.new('Real shell thickness','SOLIDIFY');s.thickness=.028;s.offset=0
    b=o.modifiers.new('Hood edge radius','BEVEL');b.width=.005;b.segments=2
    B.qa_shells.append(o.name)
    for i in range(9):
        u=-math.pi/2+math.pi*i/8
        B.screw(parent,(side*(1.10*math.cos(u)+.023)-side*1.10,.54*math.sin(u),.012),(0,0,1),.013)

def build_k():
    B=Builder('K','星图刻写机');B.pedestal_mount(.36)
    bed=B.part('MachineBed',(0,.12,.35),.7)
    B.cube('Bed',(1.98,1.02,.10),'Steel',bed,(0,0,1.05),.10)
    for side in [-1,1]:
        B.beam('BedSupport',(side*.66,.24,.68),(side*.8,.24,1.02),.045,'Chrome',bed)
        reel=B.part('Reel'+str(side),(side*.48,.12,.5),.25)
        c=B.rotor('Reel'+str(side),reel,'z',side*.55);c.location=(side*.68,.02 if side<0 else .12,1.15)
        B.cyl('TapeSpool',.275,.15,'Black',c,(0,0,0),n=64)
        for z in [-.085,.085]:
            B.cyl('ReelFlange',.32,.025,'Chrome',c,(0,0,z),n=64)
            for j in range(3):
                a=j*math.tau/3;B.sphere('ReelInset',.082,'Black',c,(.165*math.cos(a),.165*math.sin(a),z+(.014 if z>0 else -.014)),(1,.65,.035))
        B.cyl('ReelHub',.065,.24,'Chrome',c)
        h=B.part('Hood'+str(side),(side*1.10,0,.15),.0)
        def move(o,t,s=side):
            u=window(t,0,.72);o.location=(s*(1.10+.14*window(t,0,.25)),0,1.12);o.rotation_euler=(0,s*math.radians(68)*u,0)
        c=B.control('Hood'+str(side),h,move);hood_half(B,c,side)
        B.joint(c,(0,0,0),.073,(0,1,0))
        B.cube('HoodLatch',(.1,.07,.14),'Red',c,(-side*.15,-.46,.045),.017)
    B.cube('TapePlaten',(1.40,.28,.025),'Black',bed,(0,-.23,1.19),.012)
    B.tube('TapeGuide',[(-.67,-.02,1.235),(-.4,-.23,1.235),(.4,-.23,1.235),(.67,.12,1.235)],.008,'Chrome',bed)
    B.beam('NeedleCrossbeam',(-.62,.2,1.69),(.62,.2,1.69),.036,'Steel',bed)
    for i in range(3):
        p=B.part('Stylus'+str(i),((i-1)*.10,-.12,.68),.85)
        x=(i-1)*.36
        c=B.control('StylusLift'+str(i),p,lambda o,t,xx=x:setattr(o,'location',(xx,.13,1.61+.08*(1-window(t,.3,.85)))))
        B.cyl('NeedleMotor',.068,.24,'Steel',c)
        B.cyl('NeedleSleeve',.076,.06,'Ivory',c,(0,0,.04))
        B.coil(c,(0,0,-.03),.074,.11,8)
        B.beam('StylusArm',(0,0,-.10),(0,-.28,-.23),.015,'Chrome',c)
        B.cyl('NeedleTip',.008,.09,'Copper',c,(0,-.28,-.275),n=16)
        B.socket('needle_'+str(i),c,(0,-.28,-.32))
    gauge(B,bed,(0,-.525,1.04),.09)
    B.socket('field',bed,(0,-.15,1.23));return B

def lens_head(B,parent,index,r=.22):
    B.sphere('OpticalPorcelain',r,'Ivory',parent,(0,0,0),(1.13,1,.9))
    B.cyl('LensBarrel',r*.76,.12,'Steel',parent,(0,-r*.80,0),(math.pi/2,0,0),64)
    B.torus('LensRim',r*.76,.015,'Chrome',parent,(0,-r*1.06,0),(math.pi/2,0,0))
    B.cyl('InnerOptics',r*.68,.008,'Black',parent,(0,-r*1.10,0),(math.pi/2,0,0),64)
    for k in range(7):
        a=k*math.tau/7
        pts=[]
        for j in range(12):
            aa=a+j/11*.75;rr=r*(.25+.39*j/11);pts.append((rr*math.cos(aa),-r*1.12,rr*math.sin(aa)))
        B.tube('IrisLeafEdge',pts,.009,'Copper',parent)
    B.sphere('CoatedLens',r*.43,'Lens',parent,(0,-r*1.145,0),(1,.16,1))
    B.sphere('IrisReflector',r*.15,'Glow',parent,(0,-r*1.22,0),(.7,.12,.7))
    for side in [-1,1]:
        B.cube('HeadLatch',(.07,.045,.08),'Red',parent,(side*r*.91,0,.025),.01)
        B.screw(parent,(side*r*.94,-.02,.06),(0,-1,0),.012)
    B.socket('lens_'+str(index),parent,(0,-r*1.23,0))

def build_l():
    B=Builder('L','三相窥镜');B.pedestal_mount(.4)
    look_pivots=[]
    shell=B.part('Carapace',(0,.12,.36),.55)
    B.sphere('IvoryCarapace',1,'Ivory',shell,(0,0,1.02),(.80,.48,.27))
    B.torus('CarapaceSeat',.65,.020,'Chrome',shell,(0,0,.825))
    for side in [-1,1]:
        for j in range(7):
            x=-.39+j*.13;y=side*.36
            B.cube('CarapaceVent',(.065,.015,.026),'Black',shell,(x,y,1.02),.006)
        B.tube('CarapaceTrim',[(.70*math.cos(a),.405*math.sin(a),1.015) for a in [k*math.pi/48 for k in range(49)]] if side==1 else [(.70*math.cos(a),-.405*math.sin(a),1.015) for a in [k*math.pi/48 for k in range(49)]],.011,'Chrome',shell)
    for i,(x,y,z,length,r) in enumerate([(-.49,-.13,1.15,.40,.20),(.02,.12,1.24,.66,.235),(.49,-.06,1.15,.48,.215)]):
        p=B.part('Neck'+str(i),(x*.6,.12,.35+i*.07),.30)
        axis=B.empty('L_NECK_AXIS_'+str(i),p,(x,y,z));axis.rotation_euler=(0,x*.30,0)
        B.cyl('NeckFoot',.105,.085,'Chrome',axis)
        B.joint(axis,(0,0,.075),.09)
        B.cyl('OuterNeck',.066,.32,'Steel',axis,(0,0,.21))
        for zz in [.07,.13,.35]:B.torus('NeckBand',.070,.012,'Chrome',axis,(0,0,zz))
        def extend(o,t,h=length,n=i):o.location=(0,0,h+(.18+.025*n)*window(t,n*.06,.7+n*.06))
        c=B.control('Telescope'+str(i),p,extend);c.parent=axis
        B.cyl('NeckPiston',.044,length,'Chrome',c,(0,0,-length*.5))
        B.joint(c,(0,0,.02),.085)
        head=B.part('Head'+str(i),(.18*x,-.22,.30),.16+i*.06,parent=c)
        yaw=B.rotor('HeadYaw'+str(i),head,'z',.55,.33,i*1.4)
        pitch=B.rotor('HeadPitch'+str(i),yaw,'x',.72,.10,i*.8);pitch.location=(0,0,.05);look_pivots.append(pitch.name)
        B.beam('HeadYoke',(-.14,0,0),(.14,0,0),.024,'Steel',pitch)
        B.joint(pitch,(0,0,0),.06)
        eye=B.empty('L_EYE_MOUNT_'+str(i),pitch,(0,0,.20))
        lens_head(B,eye,i,r)
    target=B.part('OpticalTarget',(0,-.28,.25),.25)
    B.sphere('CalibrationTarget',.035,'Chrome',target,(0,-.30,1.82))
    for x in [-.27,.27]:B.beam('TargetFilament',(x,-.22,1.17),(0,-.30,1.82),.003,'Chrome',target)
    B.extra['look_pivots']=look_pivots
    B.socket('field',B.upper,(0,-.30,1.82));return B

def build_m():
    B=Builder('M','星噬仪')
    for i,a in enumerate([0,math.pi,math.pi/2]):
        rail=B.part('Guide'+str(i),(.25*math.cos(a),.25*math.sin(a),.08),.75)
        rr=B.empty('M_GUIDE_AXIS_'+str(i),rail);rr.rotation_euler=(0,0,a)
        for y in [-.14,.14]:B.cube('LinearRail',(.54,.035,.055),'Chrome',rr,(.98,y,.635),.006)
        pole=B.part('Pole'+str(i),(.40*math.cos(a),.40*math.sin(a),.32),.22+i*.06)
        def shift(o,t,angle=a):o.location=(0,0,0);o.rotation_euler=(0,0,angle);o.location=Vector((math.cos(angle),math.sin(angle),0))*(-.075*smooth(t))
        c=B.control('PoleSlide'+str(i),pole,shift)
        B.cube('Carriage',(.45,.37,.105),'Steel',c,(.98,0,.735),.028)
        B.cube('CoilFrame',(.28,.36,.40),'Steel',c,(1.03,0,1.00),.032)
        B.cube('IvoryPoleCap',(.35,.41,.055),'Ivory',c,(1.03,0,1.225),.02)
        for y in [-.205,.205]:
            B.cube('PoleCheek',(.34,.035,.36),'Ivory',c,(1.03,y,1.025),.018)
            for z in [.90,1.16]:B.screw(c,(1.02,y*1.09,z),(0,1 if y>0 else -1,0),.015)
        B.coil(c,(1.03,0,1.03),.115,.30,16)
        for y in [-.10,.10]:
            B.cube('SplitPoleTip',(.23,.068,.13),'Chrome',c,(.79,y,1.10),.016)
            B.cyl('FeedNozzle',.026,.18,'Chrome',c,(.62,y,1.10),(0,math.pi/2,0),24)
            B.sphere('InjectorGlow',.018,'Glow',c,(.52,y,1.10))
            B.tube('FeedTube',[(1.10,y,1.18),(1.27,y,1.18),(1.27,y,.86),(1.12,y,.80)],.012,'Copper',c)
        B.socket('injector_'+str(i),c,(.52,0,1.10))
    plate=B.part('CalibrationPlate',(0,.38,.40),.5)
    for x in [-.30,.30]:B.beam('PlatePost',(x,.95,.64),(x,.95,1.88),.022,'Steel',plate)
    for j in range(14):B.cube('CalibrationSlat',(.60,.035,.016),'Chrome',plate,(0,.95,.83+j*.073),.004)
    planets=[]
    for i,(r,orbit,angle) in enumerate([(.087,.35,0),(.14,.54,2.1),(.18,.74,4.2)]):
        key='Planet'+str(i);B.material(key,(.7,.7,.7),0,.62,albedo='collection/art/planet_atlas.png')
        anchor=B.empty('M_PLANET_'+str(i),B.upper,(orbit*math.cos(angle),orbit*math.sin(angle),1.90))
        mesh=B.sphere('World',r,key,anchor)
        for uv in mesh.data.uv_layers.active.data:uv.uv.y=(uv.uv.y+2-i)/3
        mesh.shape_key_add(name='Basis');stretch=mesh.shape_key_add(name='TidalStretch')
        for point in stretch.data:point.co.x*=2.7;point.co.y*=.55;point.co.z*=.55
        if i==2:
            for radius in [.238,.258,.278]:B.torus('PlanetaryRing',radius,.008,'Copper',anchor)
        planets.append({'node':anchor.name,'mesh':mesh.name,'radius':r,'orbit':orbit,'phase':angle})
    B.extra['planets']=planets
    core=B.sphere('EventHorizon',.115,'Black',B.upper,(0,0,1.90));B.extra['black_core']=core.name
    B.socket('field',B.upper,(0,0,1.90));return B

def interpolated_path(control,n=40):
    points=[Vector(p) for p in control];result=[]
    for j in range(n+1):
        t=j/n*(len(points)-1);i=min(len(points)-2,int(t));f=t-i
        p0=points[max(0,i-1)];p1=points[i];p2=points[i+1];p3=points[min(len(points)-1,i+2)]
        result.append(.5*((2*p1)+(-p0+p2)*f+(2*p0-5*p1+4*p2-p3)*f*f+(-p0+3*p1-3*p2+p3)*f*f*f))
    return result

def probe(B,parent):
    B.cyl('ProbeBody',.052,.27,'Chrome',parent)
    B.cyl('IdentityBand',.056,.048,'Ivory',parent,(0,0,-.025))
    verts=[(0,0,.245)]+[(.053*math.cos(i*math.tau/32),.053*math.sin(i*math.tau/32),.135) for i in range(32)]
    faces=[(0,i+1,(i+1)%32+1) for i in range(32)]+[tuple(range(32,0,-1))]
    B.fast['fast_instance'](B.name('RedProbeNose'),verts,faces,'Red',parent,(0,0,0),smooth_faces=True)
    for j in range(3):B.cube('TailFin',(.11,.012,.10),'Black',parent,(0,0,-.16),.006,(0,0,j*math.tau/3))

def build_n():
    B=Builder('N','裂隙回廊');membranes=[]
    for index,(x,y,z,height,width) in enumerate([(-.64,.08,.74,1.38,.34),(.72,.12,.74,.83,.36)]):
        root=B.part('RiftBase'+str(index),((index*2-1)*.30,.12,.12),.8)
        anchor=B.empty('N_RIFT_'+str(index),root,(x,y,z))
        B.cube('RiftFoot',(.34,.30,.075),'Steel',anchor,(0,0,0),.045)
        paths=[];jaw_nodes=[]
        for side in [-1,1]:
            p=B.part('Jaw%d_%d'%(index,side),(side*.28,-.10,.22),.3,parent=anchor)
            def turn(o,t,s=side,idx=index):o.rotation_euler=(0,s*math.radians(22 if idx==0 else 32)*window(t,idx*.10,.82+idx*.10),0)
            c=B.control('Jaw%d_%d'%(index,side),p,turn);jaw_nodes.append(c)
            path=interpolated_path([(0,0,.035),(side*width*.8,0,height*.22),(side*width,0,height*.51),(side*width*.65,0,height*.80),(side*.075,0,height)])
            paths.append(path)
            B.tube('ContinuousNickelJaw',path,.032,'Steel',c)
            B.tube('NickelTendon',[(q.x,q.y+.04,q.z) for q in path],.014,'Chrome',c)
            for j in range(4):
                span=path[j*10+1:j*10+10]
                cover=B.part('Bone%d_%d_%d'%(index,side,j),(side*.12,-.14,.06+j*.035),.05+j*.045,parent=c)
                widths=[.014+.063*math.sin(math.pi*k/(len(span)-1)) for k in range(len(span))]
                B.ribbon('IvoryVertebra',[(q.x,q.y-.052,q.z) for q in span],widths,.028,'Ivory',cover)
                for q in [span[1],span[-2]]:B.screw(cover,(q.x,q.y-.085,q.z),(0,-1,0),.011)
                B.joint(c,path[j*10],.052)
            B.joint(c,(0,0,0),.074)
            B.cube('RedRiftCatch',(.065,.065,.10),'Red',c,(side*.06,-.055,.13),.012)
        verts=[];faces=[];uv=[];cols=14;rows=40
        for row in range(rows+1):
            for col in range(cols+1):
                u=col/cols;p=paths[0][row].lerp(paths[1][row],u);p.y+=.018*math.sin(u*math.pi*6)*math.sin(row/rows*math.pi)
                verts.append(p);uv.append((u,row/rows))
        for row in range(rows):
            for col in range(cols):
                a=row*(cols+1)+col;faces.append((a,a+cols+1,a+cols+2,a+1))
        mesh=B.fast['fast_instance']('N_Membrane_'+str(index),verts,faces,'Black',anchor,(0,0,0),smooth_faces=True,uv=uv)
        mesh.shape_key_add(name='Basis');opened=mesh.shape_key_add(name='Unfold')
        angle=math.radians(22 if index==0 else 32)
        from mathutils import Matrix
        for row in range(rows+1):
            a=Matrix.Rotation(-angle,3,'Y')@paths[0][row];b=Matrix.Rotation(angle,3,'Y')@paths[1][row]
            for col in range(cols+1):opened.data[row*(cols+1)+col].co=a.lerp(b,col/cols)
        membranes.append(mesh.name)
        B.socket('port_'+str(index),anchor,(0,-.025,height*.51))
        rail=B.part('ProbeRail'+str(index),((index*2-1)*.20,-.3,.2),.16)
        level=z+height*.51-.065
        B.cube('SupportedRail',(.13,.62,.035),'Steel',rail,(x,-.25,level),.013)
        for xx in [-.055,.055]:B.beam('RailEdge',(x+xx,-.57,level+.028),(x+xx,.06,level+.028),.009,'Chrome',rail)
        B.beam('RailSupport',(x,-.18,.62),(x,-.18,level),.02,'Steel',rail)
    B.extra['membranes']=membranes
    p=B.part('Probe',(-.2,-.32,.22),.08)
    carrier=B.empty('N_PROBE',p,(-.57,-.40,.74+1.38*.51));carrier.rotation_euler=(-math.pi/2,0,0)
    probe(B,carrier);B.extra['probe']=carrier.name
    B.socket('field',B.upper,(0,0,1.35));return B

BUILDERS={'F':build_f,'G':build_g,'I':build_i,'J':build_j,'K':build_k,'L':build_l,'M':build_m,'N':build_n}

if __name__=='__main__':
    args=sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else ['F']
    for ident in args:
        B=BUILDERS[ident]();B.export()
