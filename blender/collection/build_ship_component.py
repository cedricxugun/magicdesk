"""G2 independent sculpted hull and connected sailing mechanism; never rebuilds full G."""
import bpy, sys, math, json, hashlib
from pathlib import Path
from mathutils import Vector
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(Path(__file__).parent))
from geometry import Builder, pose
b = Builder('GS2', 'Tidal ship independent refinement')
b.material('Porcelain', (.78,.74,.66), 0,.27, normal='ceramic_glaze_normal.png', coat=.38)
b.material('Brass', (.52,.32,.12), 1,.28, normal='metal_normal.png')
b.material('Nickel', (.45,.50,.53), 1,.27, normal='metal_normal.png')
b.material('Dark', (.08,.10,.11), .85,.34)
b.material('Enamel', (.16,.007,.012), 0,.25, coat=.5)
b.material('Sail', (.76,.72,.62), 0,.63)
root=b.empty('GS2_Ship', b.upper)

def mesh(name, vertices, faces, material, parent, uv=None):
    return b.fast['fast_instance'](b.name(name),vertices,faces,material,parent,(0,0,0),smooth_faces=True,uv=uv)

def ring(name, radius, inside, depth, material, parent, loc, axis=(0,0,1)):
    obj=b.sleeve(name,radius,inside,depth,material,parent,loc,48)
    obj.rotation_euler=Vector(axis).to_track_quat('Z','Y').to_euler()
    obj.modifiers[0].width=.0006
    return obj

def bolt(parent, loc, axis=(0,0,1), radius=.004):
    obj=b.cyl('CaptiveBolt',radius,.003,'Nickel',parent,loc,Vector(axis).to_track_quat('Z','Y'),12)
    p=Vector(loc)+Vector(axis)*.0016
    b.cube('BoltSlot',(radius*1.25,.0008,.0004),'Dark',parent,p,.0001,Vector(axis).to_track_quat('Z','Y'))
    return obj

# Label-scale fixed foot, real blind bore instead of a solid overlapping center pin.
foot=b.cyl('BlindMount',.092,.018,'Nickel',root,(0,0,.025),n=80)
cutter=b.cyl('BoreCutter',.034,.012,'Dark',root,(0,0,.021),n=64)
bpy.context.view_layer.update();bpy.context.view_layer.objects.active=foot
mod=foot.modifiers.new('Original spindle recess','BOOLEAN');mod.operation='DIFFERENCE';mod.object=cutter
bpy.ops.object.modifier_apply(modifier=mod.name);bpy.data.objects.remove(cutter,do_unlink=True)
ring('MountRim',.096,.087,.012,'Brass',root,(0,0,.029))
for a in [0,math.tau/3,2*math.tau/3]:bolt(root,(.074*math.cos(a),.074*math.sin(a),.036))

# Visible two-axis gimbal. Y trunnions carry pitch; X trunnions carry roll.
pitch=b.empty('GS2_PitchYoke',root,(0,0,.27))
roll=b.empty('GS2_HullCarrier',pitch)
for side in [-1,1]:
    b.tube('FixedPitchFork',[(.045,side*.045,.036),(.080,side*.050,.205),(0,side*.055,.23),(0,side*.055,.249)],.007,'Nickel',root)
    ring('PitchBearing',.014,.0068,.009,'Dark',root,(0,side*.055,.27),(0,1,0))
    b.cyl('PitchTrunnion',.006,.028,'Nickel',pitch,(0,side*.049,0),(math.pi/2,0,0),40)
    b.tube('PitchYoke',[(0,side*.042,0),(side*.055,side*.042,0),(side*.055,side*.015,0)],.005,'Brass',pitch)
    ring('RollBearing',.013,.0058,.010,'Dark',pitch,(side*.055,0,0),(1,0,0))
    b.cyl('RollTrunnion',.005,.026,'Nickel',roll,(side*.05,0,0),(0,math.pi/2,0),40)
    bolt(root,(0,side*.065,.27),(0,side,0))

for side in [-1,1]:
    b.tube('HullKeelCradle',[(side*.04,0,0),(side*.04,0,.022),(side*.085,0,.035)],.005,'Nickel',roll)

# Hull surface is lofted from a sheer line and rounded bilge, with a true inner shell.
# All following coordinates are relative to the gimbal, X bow to stern, Z up.
def hull_point(u, a, inset=0):
    x=-.335+.67*u
    width=.145*max(0,math.sin(math.pi*u))**.67
    keel=.023+.194*abs(2*u-1)**5
    sheer=.164+.053*abs(2*u-1)**2
    return (x, max(.0004,width-inset)*math.sin(a), keel+(sheer-keel)*(1-math.cos(a))+.6*inset)

verts=[];faces=[];uv=[];nx=64;ny=32
for shell in range(2):
    for i in range(nx+1):
        for j in range(ny+1):
            verts.append(hull_point(i/nx, -math.pi/2+math.pi*j/ny,.004*shell));uv.append((i/nx,j/ny))
size=(nx+1)*(ny+1)
for shell in range(2):
    for i in range(nx):
        for j in range(ny):
            k=shell*size+i*(ny+1)+j;q=(k,k+1,k+ny+2,k+ny+1);faces.append(q if shell==0 else q[::-1])
for i in range(nx):
    for j in [0,ny]:
        k=i*(ny+1)+j;faces.append((k,k+ny+1,k+ny+1+size,k+size))
for i in [0,nx]:
    for j in range(ny):
        k=i*(ny+1)+j;faces.append((k,k+1,k+1+size,k+size))
hull=mesh('LoftedPorcelainHull',verts,faces,'Porcelain',roll,uv)
for side in [-1,1]:
    outline=[hull_point(i/64,side*math.pi/2) for i in range(65)]
    b.tube('ContinuousGunwale',outline,.004,'Brass',roll)
    stripe=[hull_point(i/64,side*1.10) for i in range(4,62)]
    b.tube('LowerHullNickelStrake',stripe,.0025,'Nickel',roll)
    for i in [12,22,32,42,52]:
        p=Vector(hull_point(i/64,side*1.30));p.y+=side*.002
        ring('PortholeBezel',.0125,.0089,.003,'Brass',roll,p,(0,side,0))
        b.cyl('PortholeDarkGlass',.0085,.002,'Lens',roll,p,(math.pi/2,0,0),32)
    for i in range(7,61,7):
        p=Vector(hull_point(i/64,side*1.51));bolt(roll,p,(0,side,.15),.0027)
    # Low bulwark and deck cleats follow the hull shape, not a straight floating rail.
    for i in [12,25,39,52]:
        p=Vector(hull_point(i/64,side*math.pi/2));p.y*=.82
        b.cyl('CleatPost',.003,.014,'Nickel',roll,p+Vector((0,0,.004)),n=24)
        b.beam('CleatCrossbar',p+Vector((-.009,0,.012)),p+Vector((.009,0,.012)),.0027,'Brass',roll)

# Open deck frame visible in source service view; fitted inset deck above actual ribs.
deck=b.empty('GS2_Deck',roll)
for u in [.15,.30,.45,.60,.75,.87]:
    pts=[hull_point(u,-math.pi/2+math.pi*j/24,.009) for j in range(25)]
    b.tube('InternalHullRib',pts,.0035,'Nickel',roll)
b.tube('KeelSpine',[hull_point(i/64,0,.006) for i in range(65)],.004,'Dark',roll)
vertices=[];faces=[]
for i in range(65):
    u=i/64;x,y,z=hull_point(u,math.pi/2,.009)
    for side in [-1,1]:vertices.append((x,side*y,z-.008))
for i in range(64):faces.append((i*2,i*2+1,i*2+3,i*2+2))
deckmesh=mesh('FittedDeck',vertices,faces,'Dark',deck)
solid=deckmesh.modifiers.new('Deck thickness','SOLIDIFY');solid.thickness=.003
# A removable curved access cover follows the actual deck, clear of winch feet.
def deck_height(x):return hull_point((x+.335)/.67,math.pi/2,.009)[2]-.008
outline=[];cx=.065;hx=.065;hy=.035;radius=.010
for q,(x,y) in enumerate([(cx+hx-radius,hy-radius),(cx-hx+radius,hy-radius),(cx-hx+radius,-hy+radius),(cx+hx-radius,-hy+radius)]):
    for k in range(12):
        angle=q*math.pi/2+k*math.pi/22
        outline.append((x+radius*math.cos(angle),y+radius*math.sin(angle)))
vertices=[(cx,0,deck_height(cx)+.002)];faces=[];n=len(outline)
for row in range(1,9):
    for x,y in outline:
        u=row/8;x=cx+(x-cx)*u;y=y*u;vertices.append((x,y,deck_height(x)+.002))
for j in range(n):faces.append((0,1+j,1+(j+1)%n))
for row in range(7):
    for j in range(n):
        a=1+row*n+j;b0=1+row*n+(j+1)%n;faces.append((a,b0,b0+n,a+n))
hatch=mesh('FittedEnamelAccessCover',vertices,faces,'Enamel',deck)
solid=hatch.modifiers.new('Cover thickness','SOLIDIFY');solid.thickness=.002
b.tube('AccessCoverRolledRim',[(x,y,deck_height(x)+.0024) for x,y in outline+[outline[0]]],.0012,'Brass',deck)
for x in [.018,.112]:
    for y in [-.021,.021]:bolt(deck,(x,y,deck_height(x)+.003),radius=.0027)
winch_lifts={}
for x in [-.18,.16]:
    lift=hull_point((x+.335)/.67,math.pi/2,.009)[2]-.008-.1685+.0003
    winch_lifts[x]=lift
    for y in [-.040,.040]:
        b.cyl('DeckWinchFoot',.011,.009,'Nickel',deck,(x,y,.173+lift),n=40)
        b.cyl('DeckWinchDrum',.006,.018,'Brass',deck,(x,y,.184+lift),n=32)
        b.cyl('WinchCap',.010,.003,'Nickel',deck,(x,y,.194+lift),n=32)

# One stepped mast and two independent true vertical sail pivots at its heel.
mastx=-.060;mastbase=.173;masttop=.655
mast=b.empty('GS2_Mast',roll,(mastx,0,mastbase))
ring('MastStepSocket',.021,.0105,.024,'Nickel',mast,(0,0,.006))
b.cyl('ContinuousMast',.008,masttop-mastbase,'Brass',mast,(0,0,(masttop-mastbase)/2),n=56)
for z in [.010,.088,.32,.477]:ring('MastCollar',.011,.0085,.008,'Nickel',mast,(0,0,z))
b.sphere('MastFinial',.009,'Brass',mast,(0,0,.491))
for side in [-1,1]:
    b.tube('FixedShroud',[(mastx,0,masttop-.026),(mastx,side*.106,.176)],.0017,'Nickel',roll)
    ring('ShroudDeckEye',.004,.002,.003,'Brass',roll,(mastx,side*.106,.176),(1,0,0))

sails=[];cloths=[]
def sail_point(u,v,length,side):
    # u ascends mast; v runs mast to leech. Curved cloth retains real corner anchors.
    x=side*(.020+length*(1-u)*v)
    z=.032+(.414 if side==1 else .385)*u
    y=.038*math.sin(math.pi*u)*math.sin(math.pi*v)
    return Vector((x,y,z))

for label,length,side in [('Main',.345,1),('Jib',.252,-1)]:
    sail=b.empty('GS2_'+label+'Boom',mast,(0,0,.018 if side==1 else .042));sails.append(sail)
    ring('GooseneckBearing',.013,.0088,.014,'Dark',sail,(0,0,.014))
    b.beam('BoomElbow',(side*.012,0,.014),(side*.020,0,.028),.0035,'Brass',sail)
    b.beam('Boom',(side*.020,0,.028),(side*(length+.020),0,.028),.0035,'Brass',sail)
    vertices=[];faces=[];uv=[];n=32;indices={}
    # True triangular tessellation: one apex, no collapsed strip of 33 UV vertices.
    for i in range(n+1):
        for j in range(n-i+1):
            indices[i,j]=len(vertices)
            vertices.append(sail_point(i/n,j/max(1,n-i),length,side));uv.append((j/n,i/n))
    for i in range(n):
        for j in range(n-i):
            faces.append((indices[i,j],indices[i,j+1],indices[i+1,j]))
            if j<n-i-1:faces.append((indices[i,j+1],indices[i+1,j+1],indices[i+1,j]))
    cloth=mesh(label+'TailoredCloth',vertices,faces,'Sail',sail,uv);cloths.append((label,cloth))
    solid=cloth.modifiers.new('Sail fabric edge','SOLIDIFY');solid.thickness=.0012
    for points in [ [sail_point(i/n,0,length,side) for i in range(n+1)],
                    [sail_point(i/n,1,length,side) for i in range(n+1)],
                    [sail_point(0,i/n,length,side) for i in range(n+1)]]:
        b.tube('SailSewnEdge',points,.0018,'Porcelain',sail)
    for u in [.20,.40,.60,.80]:
        b.tube('ClothPanelSeam',[sail_point(u,j/n,length,side) for j in range(n+1)],.00055,'Porcelain',sail,1)
    # The burgundy band is baked into the cloth material; no offset overlay to flicker.
    top=.446 if side==1 else .417
    for p in [Vector((side*.020,0,.032)),Vector((side*(length+.020),0,.032)),Vector((side*.020,0,top))]:
        ring('SailCringle',.0038,.002,.002,'Brass',sail,p,(0,1,0))
    ring('RotatingSailHeadHank',.012,.0086,.002,'Nickel',sail,(0,0,top))
    b.beam('HeadHankTie',(side*.012,0,top),(side*.020,0,top),.001,'Nickel',sail)
    b.beam('TackTie',(side*.020,0,.028),(side*.020,0,.032),.001,'Nickel',sail)
    # An independent sheet tracks the boom endpoint during source animation.
    rope=b.tube('WorkingSheet',[(0,0,j/33) for j in range(34)],.0014,'Nickel',sail)
    sail['length']=length;sail['side']=side;sail['sheet_name']=rope.name

# Three chrome wave ribbons driven by eccentric cams under the hull.
waves=[];cams=[]
b.cyl('ContinuousCamshaft',.004,.266,'Nickel',root,(0,0,.104),(math.pi/2,0,0),32)
for i,y in enumerate([-.10,0,.10]):
    phase=i*math.tau/3
    cam=b.empty('GS2_Cam'+str(i),root,(0,y,.104));cams.append(cam)
    disk=b.cyl('EccentricCam',.017,.008,'Brass',cam,(.006,0,0),(math.pi/2,0,0),56)
    disk.data=disk.data.copy()
    cutter=b.cyl('CamBoreCutter',.0045,.024,'Dark',cam,(0,0,0),(math.pi/2,0,0),40)
    bpy.context.view_layer.update();bpy.context.view_layer.objects.active=disk
    bore=disk.modifiers.new('Actual eccentric axle bore','BOOLEAN');bore.operation='DIFFERENCE';bore.object=cutter
    bpy.ops.object.modifier_apply(modifier=bore.name);bpy.data.objects.remove(cutter,do_unlink=True)
    for sign in [-1,1]:
        ring('CamBearing',.011,.0045,.005,'Dark',root,(0,y+sign*.023,.104),(0,1,0))
        b.beam('BearingPedestal',(0,y+sign*.023,.05),(0,y+sign*.023,.097),.005,'Nickel',root)
        b.beam('PedestalFoot',(0,y+sign*.023,.05),(0,0,.044),.005,'Nickel',root)
    wave=b.empty('GS2_Wave'+str(i),root,(0,y,.144));waves.append(wave)
    # Continuous shaped ribbon with actual width and a folded lower edge.
    verts=[];faces=[]
    for j in range(65):
        t=j/64;x=-.33+.66*t
        z=.054+.022*math.sin(3*math.pi*t+phase)+.027*abs(2*t-1)**3
        taper=.10+.90*math.sin(math.pi*t)**.40
        for edge in [-1,1]:verts.append((x,edge*.005*taper,z+edge*.012*taper))
    for j in range(64):faces.append((j*2,j*2+1,j*2+3,j*2+2))
    ribbon=mesh('ShapedTidalRibbon',verts,faces,'Nickel',wave)
    solid=ribbon.modifiers.new('Solid metal ribbon','SOLIDIFY');solid.thickness=.003
    bevel=ribbon.modifiers.new('Soft polished rims','BEVEL');bevel.width=.001;bevel.segments=3
    for sign in [-1,1]:b.tube('RibbonRolledEdge',[Vector(verts[j*2+(0 if sign<0 else 1)]) for j in range(65)],.0018,'Brass',wave)
    b.beam('WaveCarrier',(0,0,0),(0,0,.054+.022*math.sin(1.5*math.pi+phase)),.004,'Dark',wave)
    b.cyl('CamFollowerRoller',.006,.008,'Nickel',wave,(0,0,-.017),(math.pi/2,0,0),40)
    b.beam('FollowerStem',(0,0,-.014),(0,0,.005),.003,'Nickel',wave)
    for sign in [-1,1]:
        b.cyl('VerticalGuideRod',.0025,.058,'Nickel',root,(sign*.035,y,.133),n=24)
        ring('GuideSleeve',.005,.0029,.014,'Brass',wave,(sign*.035,0,0))
        b.beam('GuideFoot', (sign*.035,y,.104),(sign*.035,y,.059),.0035,'Nickel',root)
        b.beam('GuideFootBrace',(sign*.035,y,.059),(0,y,.05),.0035,'Nickel',root)
    b.beam('FollowerCrosshead',(-.028,0,0),(.028,0,0),.003,'Dark',wave)

from ship_sail_materials import finish_sails
finish_sails(cloths)

# Authored source choreography: trim, wave build-up, gentle tidal pitch, ease to rest.
scene=bpy.context.scene;scene.render.fps=30;scene.frame_end=451
def smooth(u):
    u=max(0,min(1,u));return u*u*(3-2*u)
for frame in range(1,452):
    t=(frame-1)/30;energy=smooth((t-4)/1.3)*(1-smooth((t-10)/2.3))
    trim=math.radians(20)*smooth((t-1)/2)*(1-smooth((t-11.5)/2))
    pitch.rotation_euler.y=math.radians(5)*energy*math.sin(t*1.7)
    roll.rotation_euler.x=math.radians(2.0)*energy*math.sin(t*1.7+.65)
    pitch.keyframe_insert('rotation_euler',frame=frame);roll.keyframe_insert('rotation_euler',frame=frame)
    for i,(wave,cam) in enumerate(zip(waves,cams)):
        a=t*(.55+energy*.7)+i*math.tau/3
        cam.rotation_euler.y=-a
        # Roller center vertical and analytically tangent to the eccentric disc.
        dz=math.sqrt((.017+.006)**2-(.006*math.cos(a))**2)+.006*math.sin(a)
        wave.location.z=.104+dz+.017
        cam.keyframe_insert('rotation_euler',frame=frame);wave.keyframe_insert('location',frame=frame)
    for i,sail in enumerate(sails):
        sail.rotation_euler.z=trim*(1 if i==0 else .70)
        sail.keyframe_insert('rotation_euler',frame=frame)
    bpy.context.view_layer.update()
    for sail in sails:
        rope=bpy.data.objects[sail['sheet_name']]
        local_tip=Vector((sail['side']*(sail['length']+.020),0,.028))
        tip=roll.matrix_world.inverted()@sail.matrix_world@local_tip
        center=Vector((.16 if sail['side']>0 else -.18,-.04,0))
        d=tip-center;radius=.008
        tangent=math.atan2(d.y,d.x)+math.acos(radius/math.hypot(d.x,d.y))
        points=[local_tip]
        for j in range(33):
            u=j/32;angle=tangent+(math.tau*2-tangent)*u
            p=center+Vector((radius*math.cos(angle),radius*math.sin(angle),.180+.009*u+winch_lifts[.16 if sail['side']>0 else -.18]))
            points.append(sail.matrix_world.inverted()@roll.matrix_world@p)
        for j,p in enumerate(points):
            point=rope.data.splines[0].points[j];point.co=(*p,1);point.keyframe_insert('co',frame=frame)
for action in bpy.data.actions:
    for layer in action.layers:
        for strip in layer.strips:
            for bag in strip.channelbags:
                for fc in bag.fcurves:
                    for key in fc.keyframe_points:key.interpolation='LINEAR'
scene.frame_set(1);bpy.context.view_layer.update()
out=ROOT/'app/assets/collection/components';out.mkdir(exist_ok=True)
bpy.ops.object.select_all(action='DESELECT')
for obj in [root]+list(root.children_recursive):obj.select_set(True)
bpy.context.view_layer.objects.active=root
bpy.ops.export_scene.gltf(filepath=str(out/'G_ship_r2.glb'),export_format='GLB',use_selection=True,export_apply=True,export_animations=False)
(out/'G_ship_r2.json').write_text(json.dumps({'root':root.name,'source_blend':'blender/collection/G_ship_r2.blend',
    'status':'Independent source work in progress; not in app, no clearance acceptance',
    'coordinates':'Blender Z-up','mount_offset_z':.00125,
    'rig':{'pitch':pitch.name,'roll':roll.name,'sails':[o.name for o in sails],
           'waves':[o.name for o in waves],'cams':[o.name for o in cams]},
    'source_frames':451,'reference':'production/G_optical_curator/ship_r2/structure_and_motion.png'},indent=2)+'\n')
b.cyl('ReferenceOriginalDisc',.42,.02352,'Black',b.root,(0,0,-.005),n=128)
scene.render.engine='CYCLES';scene.cycles.samples=32;scene.cycles.use_denoising=True
scene.render.resolution_x=1200;scene.render.resolution_y=1200;scene.render.resolution_percentage=100;scene.render.film_transparent=True
world=bpy.data.worlds.new('ShipStudio');world.use_nodes=True;scene.world=world
tex=world.node_tree.nodes.new('ShaderNodeTexEnvironment');tex.image=bpy.data.images.load(str(ROOT/'app/assets/studio_small_09_4k.exr'),check_existing=True)
bg=next(n for n in world.node_tree.nodes if n.type=='BACKGROUND');bg.inputs['Strength'].default_value=.25;world.node_tree.links.new(tex.outputs['Color'],bg.inputs['Color'])
for i,(loc,power) in enumerate([((-2,-3,3),150),((2,1,3),180)]):
    light=bpy.data.lights.new('ShipStudio'+str(i),'AREA');light.energy=power;light.shape='DISK';light.size=2
    obj=bpy.data.objects.new(light.name,light);scene.collection.objects.link(obj);obj.location=loc;obj.rotation_euler=(Vector((0,0,.46))-obj.location).to_track_quat('-Z','Y').to_euler()
data=bpy.data.cameras.new('ShipCamera');camera=bpy.data.objects.new(data.name,data);scene.collection.objects.link(camera);scene.camera=camera
data.type='ORTHO';data.ortho_scale=1.22;camera.location=(1.5,-3.5,1.4);camera.rotation_euler=(Vector((0,0,.46))-camera.location).to_track_quat('-Z','Y').to_euler()
source=ROOT/'blender/collection/G_ship_r2.blend'
if source.exists():
    backup=ROOT/'blender/collection/checkpoints'/('G_ship_r2-'+hashlib.sha256(source.read_bytes()).hexdigest()[:12]+'.blend');backup.write_bytes(source.read_bytes())
scene['status']='Independent G2 refinement WIP, no whole-player collision test or app integration'
bpy.ops.wm.save_as_mainfile(filepath=str(source));bpy.ops.file.make_paths_relative();bpy.ops.wm.save_as_mainfile(filepath=str(source))
review=ROOT/'review/G_optical_curator/ship_r2';review.mkdir(exist_ok=True)
if '--no-render' not in sys.argv:
    for label,frame in [('component_calm',1),('component_tide',210)]:
        scene.frame_set(frame);scene.render.filepath=str(review/(label+'.png'));bpy.ops.render.render(write_still=True)
print('SHIP_COMPONENT_SAVED',source,flush=True)
