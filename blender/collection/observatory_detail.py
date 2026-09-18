"""Curved architectural skins, open windows and real working clock details."""
import bpy,math
from mathutils import Vector
from geometry import pose

def refine(b,root,item):
    front=(math.pi/2,0,0)
    for obj in list(root.children_recursive):
        if any(tag in obj.name for tag in ['PiercedPorcelainArch','ArchGoldInnerEdge','CupolaRib']):bpy.data.objects.remove(obj,do_unlink=True)
    def ring_band(name,r,inside,z0,z1,key):
        return b.sleeve(name,r,inside,z1-z0,key,root,(0,0,(z0+z1)*.5),112)
    ring_band('StoneworkBaseRing',.304,.265,.052,.093,'PlayerPorcelain')
    ring_band('ArcadeSill',.274,.238,.14,.191,'PlayerPorcelain')
    ring_band('Entablature',.278,.237,.630,.683,'PlayerPorcelain')
    for z in [.095,.139,.193,.627,.685]:b.torus('GildedCornice',.278 if z>.60 else .282,.0035,'PlayerGold',root,(0,0,z))
    # A closed curved spandrel above each arch. Windows stay open all the way
    # through the cylindrical facade; this is not a pattern painted on a slab.
    for bay in range(6):
        mid=(bay+.5)*math.tau/6;span=math.tau/6*.88;verts=[];uv=[];faces=[];n=33
        for band in range(4):
            radius=.268 if band in [0,1] else .246
            for j in range(n):
                u=j/(n-1);a=mid+(u-.5)*span
                arch=.410+.215*math.sqrt(max(0,1-(2*u-1)**2))
                z=arch if band in [0,3] else .661
                verts.append((radius*math.cos(a),radius*math.sin(a),z));uv.append((u,band/3))
        for band in range(4):
            for j in range(n-1):faces.append((band*n+j,band*n+j+1,((band+1)%4)*n+j+1,((band+1)%4)*n+j))
        faces.extend([(0,n,2*n,3*n),(n-1,4*n-1,3*n-1,2*n-1)])
        b.fast['fast_instance'](b.name('PiercedCurvedSpandrel'),verts,faces,'PlayerPorcelain',root,(0,0,0),smooth_faces=True,uv=uv)
        rim=[]
        for j in range(n):
            u=j/(n-1);a=mid+(u-.5)*span;rim.append((.270*math.cos(a),.270*math.sin(a),.410+.215*math.sqrt(max(0,1-(2*u-1)**2))))
        b.tube('ArchWindowReveal',rim,.0045,'PlayerGold',root)
        # Mechanical rosette above the window, seated on the curved facade.
        pos=Vector((.274*math.cos(mid),.274*math.sin(mid),.645));normal=Vector((math.cos(mid),math.sin(mid),0))
        b.cyl('SpandrelRosette',.020,.009,'PlayerGold',root,pos,normal.to_track_quat('Z','Y'),40)
        b.sphere('RosetteRuby',.012,'PlayerRuby',root,pos+normal*.007)
        for a in [mid-span*.5,mid+span*.5]:
            x=.261*math.cos(a);y=.261*math.sin(a)
            b.cyl('WindowJamb',.015,.237,'PlayerPorcelain',root,(x,y,.2975),n=40)
            b.cyl('JambFoot',.023,.028,'PlayerGold',root,(x,y,.193),n=40)
            b.torus('JambCapital',.020,.004,'PlayerGold',root,(x,y,.421))
    # The observatory roof has curved ribs and slender porcelain webs, with
    # empty panes between them to reveal the armillary and escapement below.
    for i in range(12):
        a=i*math.tau/12
        pts=[]
        for j in range(33):
            t=j/32;r=.253*(1-t)**.62+.012*t;pts.append((r*math.cos(a),r*math.sin(a),.68+.278*t))
        b.tube('CupolaCurvedRib',pts,.008 if i%2==0 else .0045,'PlayerGold',root)
        if i%2==0:b.ribbon('CupolaPorcelainWeb',pts,[.005+.010*math.sin(math.pi*j/32) for j in range(33)],.008,'PlayerPorcelain',root)
    # Clock hands expose a meaningful time-bias control; gears retain the
    # existing working mechanism behind this open dial.
    dial=b.empty('GA_ClockDialMount',root,(0,-.236,.478))
    for r,inside,depth,key in [(.136,.112,.023,'PlayerGold'),(.117,.096,.009,'PlayerPorcelain')]:
        n=b.sleeve('OpenClockDial',r,inside,depth,key,dial,n=96);n.rotation_euler=front
    for i in range(60):
        a=i*math.tau/60;r=.108
        b.cube('ClockMinuteIndex',(.0025,.002,.008 if i%5 else .014),'PlayerGold',dial,(r*math.sin(a),-.016,r*math.cos(a)),.0005,(0,a,0))
    for name,length,width in [('hour',.071,.0032),('minute',.100,.0020)]:
        hand=b.empty('GA_Observatory_'+name,dial,(0,-.026 if name=='hour' else -.030,0))
        b.beam('EngravedClockHand',(0,0,-.018),(0,0,length),width,'PlayerNickel',hand)
        b.sphere('ClockHandFinial',width*1.8,'PlayerGold',hand,(0,0,length))
        item['rig'].append({'name':hand.name,'home':pose(hand.matrix_basis),'kind':name})
    b.cyl('DialCentralPin',.008,.018,'PlayerGold',dial,(0,-.040,0),front,32)
    for x in [-.135,.135]:
        b.beam('ClockBridgeBracket',(x,0,.48),(x,-.24,.478),.006,'PlayerGold',root)
    # Lower doorway with true negative space rather than an opaque plaque.
    frame=[(-.045,-.275,.085),(-.045,-.275,.17)]
    frame.extend((.045*math.cos(a),-.275,.17+.047*math.sin(a)) for a in [math.pi-j*math.pi/24 for j in range(25)])
    frame.append((.045,-.275,.085));b.tube('LowerDoorArch',frame,.009,'PlayerPorcelain',root)
    b.tube('DoorGildedReveal',[(x,y-.010,z) for x,y,z in frame],.003,'PlayerGold',root)
    for x in [-.025,0,.025]:b.beam('DoorClockworkGrille',(x,-.274,.093),(x,-.274,.176),.002,'PlayerGold',root)
    for i in range(8):
        a=i*math.tau/8
        b.screw(root,(.299*math.cos(a),.299*math.sin(a),.050),(0,0,1),.0045)
