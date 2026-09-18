"""New authored parts for the selected AI curator, not the rejected claw."""
import bpy,math
from mathutils import Vector,Matrix
from geometry import pose

def clevis(b,parent,name,span=.16,radius=.085,reach=.19):
    """A supported fork and through-axle, not a decorative floating disk."""
    root=b.empty(name,parent)
    for side in [-1,1]:
        pts=[]
        for i in range(33):
            t=i/32;pts.append((side*(span-.035*math.sin(t*math.pi)),.025*math.sin(t*math.pi),-reach*(1-t)))
        b.ribbon('LoadBearingCheek',pts,[.018+.025*math.sin(i/32*math.pi) for i in range(33)],.026,'PlayerGold',root)
        b.cyl('ClevisBearing',radius,.030,'PlayerNickel',root,(side*span,0,0),(0,math.pi/2,0),64)
        b.torus('BearingSeal',radius*.82,.004,'Black',root,(side*(span+.018),0,0),(0,math.pi/2,0))
        b.cyl('RetainingBolt',radius*.37,.012,'PlayerGold',root,(side*(span+.025),0,0),(0,math.pi/2,0),12)
    b.cyl('ContinuousAxle',radius*.39,span*2+.042,'PlayerNickel',root,rot=(0,math.pi/2,0),n=48)
    b.beam('ClevisCrossbridge',(-span,0,-reach),(span,0,-reach),.030,'PlayerGold',root)
    return root

def make_head(b,wrist):
    front=(math.pi/2,0,0)
    b.material('ShutterSteel',(.025,.028,.030),.88,.30,rough='metal_roughness.png',normal='metal_normal.png')
    b.material('PixelSignalAmber',(1,.48,.08),.0,.22,emission=2.8)
    b.material('OpticBlack',(.003,.004,.004),.05,.21,coat=.35)
    carriage=b.empty('GA_CarrierMount',wrist)
    b.sphere('WristBall',.070,'PlayerGold',carriage)
    b.cyl('NeckPillar',.05,.21,'PlayerNickel',carriage,(0,0,.115))
    for z in [.04,.185]:b.torus('NeckSeal',.055,.005,'PlayerGold',carriage,(0,0,z))
    b.sphere('HeadUniversalBall',.056,'PlayerGold',carriage,(0,0,.24))
    face=b.empty('GA_CharacterGimbal',carriage,(0,0,.40))
    body=b.empty('GA_ShellAssembly',face)
    # Curved open-front porcelain shell: a real cavity around the lens.
    controls=[(-.237,.235),(-.222,.251),(-.17,.279),(-.08,.296),(.04,.293),(.145,.25),(.23,.17),(.275,.050),(.279,.015)]
    profile=[]
    for k in range(len(controls)-1):
        p0=Vector(controls[max(0,k-1)]);p1=Vector(controls[k]);p2=Vector(controls[k+1]);p3=Vector(controls[min(len(controls)-1,k+2)])
        for j in range(8):
            t=j/8;profile.append(.5*((2*p1)+(-p0+p2)*t+(2*p0-5*p1+4*p2-p3)*t*t+(-p0+3*p1-3*p2+p3)*t*t*t))
    verts=[];faces=[];uv=[];n=96
    for k,(y,r) in enumerate(profile):
        for j in range(n):
            a=j*math.tau/n;verts.append((r*math.cos(a),y,r*.99*math.sin(a)));uv.append((j/n,k/(len(profile)-1)))
    for k in range(len(profile)-1):
        for j in range(n):faces.append((k*n+j,k*n+(j+1)%n,(k+1)*n+(j+1)%n,(k+1)*n+j))
    shell=b.fast['fast_instance'](b.name('CuratorFormedShell'),verts,faces,'PlayerPorcelain',body,(0,0,0),smooth_faces=True,uv=uv)
    solid=shell.modifiers.new('Porcelain skin thickness','SOLIDIFY');solid.thickness=.010
    for degrees in [65,185,305]:
        angle=math.radians(degrees)
        line=[((r+.001)*math.cos(angle),y,(r+.001)*.99*math.sin(angle)) for y,r in profile[3:-5]]
        b.tube('CeramicPanelJoint',line,.0018,'Black',body,1)
        for k in [9,29]:
            y,r=profile[k];normal=Vector((math.cos(angle),-.15,math.sin(angle))).normalized()
            b.screw(body,((r+.004)*math.cos(angle),y,(r+.004)*.99*math.sin(angle)),normal,.0065)
    optics=b.part('OpticalBarrel',(0,-.30,0),.18,face)
    barrel=b.sleeve('LensBarrel',.238,.215,.068,'PlayerGold',optics,(0,-.218,0),96);barrel.rotation_euler=front
    for y in [-.188,-.250]:b.torus('LensRim',.229,.007,'PlayerNickel',optics,(0,y,0),front)
    retainer=b.sleeve('IrisRetainingPlate',.243,.207,.010,'PlayerGold',optics,(0,-.256,0),112);retainer.rotation_euler=front
    b.torus('IrisFaceLip',.210,.005,'PlayerNickel',optics,(0,-.264,0),front)
    b.cyl('PixelGlass',.203,.016,'OpticBlack',optics,(0,-.137,0),front,96)
    # UV-authored optical screen consumes the generated expression atlas.
    vs=[];uv=[];faces=[];n=96;rows=16
    for row in range(rows+1):
        r=.194*max(.0001,row/rows)
        for j in range(n+1):
            a=j*math.tau/n;vs.append((r*math.cos(a),-.178+.024*(r/.194)**2,r*math.sin(a)));uv.append((.5+.5*r/.194*math.cos(a),.5-.5*r/.194*math.sin(a)))
    for row in range(rows):
        for j in range(n):
            k=row*(n+1)+j;faces.append((k,k+1,k+n+2,k+n+1))
    screen_root=b.empty('GA_ExpressionMount',optics)
    screen=b.fast['fast_instance']('GA_ExpressionScreen',vs,faces,'OpticBlack',screen_root,(0,0,0),smooth_faces=True,uv=uv)
    iris=b.empty('GA_IrisDrive',optics,(0,-.198,0));leaves=[]
    for i in range(8):
        a=i*math.tau/8;hinge=Vector((.192*math.cos(a),0,.192*math.sin(a)))
        leaf=b.empty('GA_Shutter_%02d'%i,iris,hinge);leaves.append({'name':leaf.name,'home':pose(leaf.matrix_basis),'angle':a})
        # Curved leading and trailing edges replace the triangular shutter.
        local=[Vector((0,0,0))]
        left=Vector((.218*math.cos(math.radians(-25)),0,.218*math.sin(math.radians(-25))))
        control=Vector((.105,0,-.09))
        for j in range(1,13):
            t=j/12;local.append(2*(1-t)*t*control+t*t*left)
        for j in range(1,13):
            aa=math.radians(-25+51*j/12);local.append(Vector((.218*math.cos(aa),0,.218*math.sin(aa))))
        right=local[-1];control=Vector((.092,0,.015))
        for j in range(1,12):
            t=j/12;local.append((1-t)*(1-t)*right+2*(1-t)*t*control)
        # Intersect the blade's swept envelope with the space inside the
        # spherical casing. Rigid leaves cannot poke through porcelain.
        polygon=[Vector((v.x,v.z)) for v in local];pivot=Vector((.192,0))
        for phase in [j*.94/10 for j in range(11)]:
            co=math.cos(phase);si=math.sin(phase);center=pivot-Vector((co*pivot.x+si*pivot.y,-si*pivot.x+co*pivot.y))
            for plane in range(48):
                a0=plane*math.tau/48;normal=Vector((math.cos(a0),math.sin(a0)));limit=.247+center.dot(normal)
                clipped=[]
                for start,end in zip(polygon,polygon[1:]+polygon[:1]):
                    ds=start.dot(normal)-limit;de=end.dot(normal)-limit
                    if ds<=0:clipped.append(start)
                    if (ds<=0)!=(de<=0):clipped.append(start.lerp(end,ds/(ds-de)))
                polygon=clipped
        local=[Vector((p.x,0,p.y)) for p in polygon]
        rotation=Matrix.Rotation(-a,3,'Y');verts=[rotation@v-hinge for v in local]
        depth=-i*.0016
        verts=[v+Vector((0,depth,0)) for v in verts]
        uv=[(.5+v.x/.44,.5+v.z/.44) for v in verts]
        mesh=b.fast['fast_instance'](b.name('ShutterBlade'),verts,[tuple(range(len(verts)))],'ShutterSteel',leaf,(0,0,0),uv=uv)
        solid=mesh.modifiers.new('Stamped blade thickness','SOLIDIFY');solid.thickness=.0011
        bevel=mesh.modifiers.new('Blade edge break','BEVEL');bevel.width=.0006;bevel.segments=2
        b.cyl('IrisHinge',.007,.020,'PlayerGold',iris,hinge+Vector((0,-.013,0)),front,20)
    eyes=[]
    for side in [-1,1]:
        b.cyl('GimbalCheek',.083,.045,'PlayerGold',body,(side*.278,.02,0),(0,math.pi/2,0),64)
        b.cyl('GimbalRuby',.053,.009,'PlayerRuby',body,(side*.303,.02,0),(0,math.pi/2,0),56)
    for angle in [35,85,140,210,310]:
        a=math.radians(angle);b.screw(body,(.225*math.cos(a),-.18,.225*math.sin(a)),(0,-1,0),.009)
    b.tube('CrownSeam',[(.18*math.cos(a),.16*math.cos(a),.26*math.sin(a)) for a in [i*math.pi/48 for i in range(49)]],.004,'PlayerGold',body)
    b.cyl('CarrierDropStem',.027,.30,'PlayerNickel',wrist,(0,0,-.17),n=48)
    for z in [-.035,-.27]:b.torus('CarrierDropSeal',.031,.006,'PlayerGold',wrist,(0,0,z))
    projector=b.empty('GA_IndependentProjector',wrist,(0,0,-.35))
    b.sphere('ProjectorUniversal',.065,'PlayerNickel',projector)
    b.cyl('EmitterSleeve',.075,.080,'PlayerGold',projector,(0,0,-.045))
    b.torus('EmitterRim',.074,.009,'PlayerNickel',projector,(0,0,-.085))
    b.cyl('OpticalEmitter',.051,.014,'PlayerRuby',projector,(0,0,-.093),n=64)
    emitter=b.empty('GA_EmitterPoint',projector,(0,0,-.100))
    yoke=clevis(b,wrist,'GA_WristYoke',.108,.058,.11)
    from curator_head_internals import build
    service=build(b,face,body,optics,iris,screen_root,profile)
    return {'face':face.name,'face_pivot':[0,-.16,0],'carrier':carriage.name,'projector':projector.name,'emitter':emitter.name,'iris':iris.name,'leaves':leaves,'eyes':eyes,'screen':screen.name,'wrist_yoke':yoke.name,'head_diameter':.60,'beam_gap':.18,'head_service':service,'source':'production/G_record_player/r2/ART_AND_BEHAVIOR.md'}

def make_observatory(b,catalog,print_root):
    """First record: a real pierced observatory built around its mechanism."""
    old=bpy.data.objects[catalog[0]['root']]
    for obj in list(old.children_recursive)+[old]:bpy.data.objects.remove(obj,do_unlink=True)
    root=b.empty('GA_Observatory',print_root);rig=[];anchors=[]
    def dynamic(name,parent,loc,kind,**kw):
        n=b.empty(name,parent,loc);rig.append({'name':n.name,'home':pose(n.matrix_basis),'kind':kind,**kw});return n
    def curve(name,points,r,key='PlayerGold',parent=root):
        return b.tube(name,points,r,key,parent,2)
    def arch(radius,z0,height,start,end,key,r):
        return [(radius*math.cos(a),radius*math.sin(a),z0+height*math.sin(math.pi*j/32)) for j,a in enumerate([start+(end-start)*j/32 for j in range(33)])]
    b.cyl('ObservatoryFoundation',.315,.038,'PlayerGold',root,(0,0,.025),n=128)
    b.torus('FoundationBlackInlay',.303,.005,'Black',root,(0,0,.046))
    for i in range(6):
        a=i*math.tau/6;x=.258*math.cos(a);y=.258*math.sin(a)
        anchors.append([x,.11,-y])
        b.cyl('ColumnShoe',.034,.06,'PlayerGold',root,(x,y,.072),n=40)
        b.cyl('PorcelainFlutedColumn',.024,.43,'PlayerPorcelain',root,(x,y,.31),n=48)
        for z in [.108,.20,.46,.532]:b.torus('ColumnCollar',.028,.004,'PlayerGold',root,(x,y,z))
        b.sphere('ColumnRuby',.025,'PlayerRuby',root,(x,y,.56))
        a2=a+math.tau/6
        points=arch(.258,.54,.15,a,a2,'',0)
        curve('PiercedPorcelainArch',points,.023,'PlayerPorcelain')
        curve('ArchGoldInnerEdge',[(x*.968,y*.968,z-.019) for x,y,z in points],.005)
        # Open spandrels preserve the architecture's depth through the object.
        curve('CupolaRib',[(.25*(1-t)*math.cos(a),.25*(1-t)*math.sin(a),.67+.28*t) for t in [j/32 for j in range(33)]],.010)
        b.cyl('SideFinial',.012,.17,'PlayerGold',root,(x,y,.76),n=24)
        b.sphere('FinialRuby',.019,'PlayerRuby',root,(x,y,.853))
    for r,z in [(.264,.125),(.272,.535),(.265,.665),(.089,.947)]:b.torus('ArchitecturalRing',r,.008,'PlayerGold',root,(0,0,z))
    for i,(x,z,r,ratio) in enumerate([(-.06,.32,.080,1.),(.06,.36,.067,-1.2),(0,.45,.049,1.65)]):
        n=dynamic('GA_Clockwork'+str(i),root,(x,.005,z),'gear',ratio=ratio)
        b.torus('GearRing',r,.009,'PlayerGold',n,rot=(math.pi/2,0,0))
        for k in range(24):
            a=k*math.tau/24;b.cube('GearTooth',(.014,.023,.014),'PlayerGold',n,(r*math.cos(a),0,r*math.sin(a)),.001,(0,-a,0))
        for k in range(5):
            a=k*math.tau/5;b.beam('GearSpoke',(0,0,0),(r*.91*math.cos(a),0,r*.91*math.sin(a)),.004,'PlayerNickel',n)
        b.cyl('GearAxle',.012,.045,'PlayerNickel',n,rot=(math.pi/2,0,0),n=32)
    clock=dynamic('GA_Pendulum',root,(0,.012,.50),'pendulum',swing_gain=.18)
    b.beam('PendulumStem',(0,0,0),(0,0,-.32),.005,'PlayerGold',clock)
    b.sphere('PendulumBob',.045,'PlayerGold',clock,(0,0,-.32),(1,.4,1))
    for i in range(40):
        a=-math.pi*.5+i*math.pi*1.55/39;z=.08+i*.50/39
        b.cube('SpiralStair',(.08,.042,.009),'PlayerPorcelain',root,(.29*math.cos(a),.29*math.sin(a),z),.003,(0,0,a))
    for r in [.255,.331]:curve('StairHandrail',[(r*math.cos(a),r*math.sin(a),.15+i*.50/80) for i,a in enumerate([-math.pi*.5+j*math.pi*1.55/80 for j in range(81)])],.004)
    b.cyl('CupolaPedestal',.09,.035,'PlayerGold',root,(0,0,.957),n=64)
    cage=dynamic('GA_CupolaOrbit',root,(0,0,1.045),'orbit',ratio=.3)
    for rot in [(0,0,0),(math.pi/2,0,0),(0,math.pi/2,0)]:b.torus('ArmillaryRing',.089,.0045,'PlayerGold',cage,rot=rot)
    b.sphere('CupolaRuby',.044,'PlayerRuby',root,(0,0,1.045))
    b.cyl('Spire',.004,.13,'PlayerGold',root,(0,0,1.15),n=24)
    catalog[0].update({'root':root.name,'title':'穹顶观测塔','parameter':'时间偏置','action':'发条共鸣','rig':rig,'build_anchors':anchors})
    from observatory_detail import refine
    refine(b,root,catalog[0])
