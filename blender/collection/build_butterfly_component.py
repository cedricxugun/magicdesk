"""Independent G1 component. Reuses authored curved wing shells, new drive assembly.
Does not open or overwrite the animated full-G source. Fine wing inlays still WIP.
"""
import bpy,bmesh,sys,math,json,hashlib
from pathlib import Path
from mathutils import Vector,Quaternion,Matrix
from mathutils.geometry import tessellate_polygon
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(Path(__file__).parent))
from geometry import Builder,pose
b=Builder('GB2','Porcelain butterfly independent component')
b.material('Porcelain',(.77,.735,.66),0,.29,rough='ceramic_glaze_roughness.png',normal='ceramic_glaze_normal.png',coat=.40)
b.material('ArchiveGold',(.55,.34,.115),1,.28,rough='metal_roughness.png',normal='metal_normal.png')
b.material('Nickel',(.44,.48,.50),1,.24)
b.material('Satin',(.12,.145,.15),.95,.34)
b.material('Red',(.19,.004,.008),0,.17,coat=.60)
root=b.empty('GB2_Butterfly',b.upper);drives=[]
# Exact fixed-length four-bar closure. Reflect only X for the left wing.
A=Vector((-.032,.045,0));CRANK=.025;ROD=.060;HORN=.022

def sphere(name,r,key,parent,loc=(0,0,0),scale=None):
    # Micro fasteners do not need the same tessellation as the garnet head.
    n,rows=(24,12) if r<=.010 else (40,20) if r<=.030 else (64,32)
    scale=scale or (1,1,1);vertices=[];uv=[];faces=[]
    for j in range(rows+1):
        t=j*math.pi/rows
        for k in range(n+1):
            a=k*math.tau/n;vertices.append((r*math.sin(t)*math.cos(a)*scale[0],r*math.sin(t)*math.sin(a)*scale[1],r*math.cos(t)*scale[2]));uv.append((k/n,j/rows))
    for j in range(rows):
        for k in range(n):
            q=j*(n+1)+k;faces.append((q,q+1,q+n+2,q+n+1))
    return b.fast['fast_instance'](b.name(name),vertices,faces,key,parent,loc,smooth_faces=True,uv=uv)

def closure(theta,side):
    B=Vector((HORN*math.cos(theta),-HORN*math.sin(theta),0));D=B-A;d=D.length
    cosine=(d*d+CRANK*CRANK-ROD*ROD)/(2*d*CRANK)
    assert abs(cosine)<1.0,('outside linkage reach',theta,cosine)
    phi=math.atan2(D.y,D.x)+math.acos(cosine)
    C=A+Vector((CRANK*math.cos(phi),CRANK*math.sin(phi),0))
    return Vector((side*B.x,B.y,0)),Vector((side*C.x,C.y,0)),phi

def ball_cup(parent,offset):
    # A hollow upper hemisphere; local Y stays vertical in the rod frame.
    n=32;rows=8;vertices=[];faces=[]
    for r in [.0085,.0073]:
        for j in range(rows+1):
            t=j*math.pi/2/rows
            for k in range(n):
                a=k*math.tau/n;vertices.append((r*math.sin(t)*math.cos(a),r*math.cos(t),offset+r*math.sin(t)*math.sin(a)))
    size=(rows+1)*n
    for shell in range(2):
        for j in range(rows):
            for k in range(n):
                q=shell*size+j*n+k;faces.append((q,shell*size+j*n+(k+1)%n,shell*size+(j+1)*n+(k+1)%n,q+n))
    for k in range(n):faces.append((rows*n+k,rows*n+(k+1)%n,size+rows*n+(k+1)%n,size+rows*n+k))
    obj=b.fast['fast_instance'](b.name('HollowBallCup'),vertices,faces,'ArchiveGold',parent,(0,0,0),smooth_faces=True)
    bm=bmesh.new();bm.from_mesh(obj.data);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(obj.data);bm.free()

def make_hinge(wing,side,upper):
    center=wing.location.copy();fixed=b.empty('GB2_FixedClevis'+wing.name,root,center)
    # Through-pin, actual hub bore, spaced thrust washers and fixed cheeks.
    for z in [-.023,.023]:
        b.sleeve('FixedClevisCheek',.027,.0085,.008,'Nickel',fixed,(0,0,z),64)
        b.beam('ClevisAttachment',(0,.020,z),(-side*.039,.035,z),.009,'Satin',fixed)
    b.beam('FixedClevisBackbone',(-side*.035,.035,-.024),(-side*.035,.035,.024),.010,'Satin',fixed)
    b.cyl('ContinuousWingPin',.008,.066,'Nickel',fixed,n=48)
    for z in [-.032,.032]:b.cyl('PinRetainer',.012,.004,'ArchiveGold',fixed,(0,0,z),n=48)
    for z in [-.016,.016]:b.sleeve('ThrustWasher',.019,.0085,.005,'ArchiveGold',fixed,(0,0,z),64)
    b.sleeve('RotatingWingHub',.019,.0087,.024,'ArchiveGold',wing,n=64)
    b.beam('WingRootSpar',(side*.016,0,0),(side*.040,-.012,0),.006,'ArchiveGold',wing)
    b.beam('WingRootElbow',(side*.040,-.012,0),(side*.047,-.012,.050 if upper else -.050),.006,'ArchiveGold',wing)
    height=.054 if upper else -.052
    b.beam('HubHornOutrigger',(side*.013,0,0),(side*.035,0,0),.004,'ArchiveGold',wing)
    b.beam('HubHornRiser',(side*.035,0,0),(side*.035,0,height-.012),.004,'ArchiveGold',wing)
    b.beam('WingCrankHorn',(side*.035,0,height-.012),(side*HORN,0,height-.012),.004,'ArchiveGold',wing)
    sphere('HornRodEnd',.007,'Nickel',wing,(side*HORN,0,height))
    b.cyl('HornBallStud',.0035,.012,'Nickel',wing,(side*HORN,0,height-.006),n=32)
    a=center+Vector((side*A.x,A.y,height));crank=b.empty('GB2_DriveCrank'+wing.name,root,a)
    b.sleeve('DriveBearing',.014,.0065,.028,'Satin',root,a+Vector((0,0,-.034)),48)
    brace_root=a+Vector((0,0,-.034));back=center+Vector((-side*.035,.105,0))
    elbow=Vector((back.x,back.y,brace_root.z))
    b.beam('DriveBearingBrace',brace_root,elbow,.006,'Nickel',root)
    b.beam('DriveBearingRearRiser',elbow,back,.006,'Nickel',root)
    b.beam('DriveBearingFrameSeat',back,center+Vector((-side*.035,.035,0)),.006,'Nickel',root)
    for z in [-.046,-.022]:b.sleeve('BearingThrustLip',.015,.0065,.003,'ArchiveGold',root,a+Vector((0,0,z)),48)
    b.cyl('CrankAxle',.006,.050,'Nickel',root,a+Vector((0,0,-.024)),n=32)
    b.sleeve('InputCrankHub',.010,.0064,.008,'ArchiveGold',crank,(0,0,-.012),48)
    b.beam('InputCrankLever',(side*.011,0,-.012),(side*CRANK,0,-.012),.004,'ArchiveGold',crank)
    sphere('CrankRodEnd',.007,'Nickel',crank,(side*CRANK,0,0))
    b.cyl('CrankBallStud',.0035,.012,'Nickel',crank,(side*CRANK,0,-.006),n=32)
    rod=b.empty('GB2_ConnectingRod'+wing.name,root)
    b.cyl('ConstantLengthRod',.0032,ROD-.016,'Nickel',rod,(0,0,ROD/2),n=24)
    for z in [0,ROD]:ball_cup(rod,z)
    drives.append({'wing':wing,'crank':crank,'rod':rod,'side':side,'upper':upper,'center':center,'height':height})

def curve_outline(control,subdiv=8):
    control=[Vector(p) for p in control];out=[]
    for k in range(len(control)):
        p0,p1,p2,p3=[control[j%len(control)] for j in [k-1,k,k+1,k+2]]
        for j in range(subdiv):
            t=j/subdiv;out.append(.5*(2*p1+(-p0+p2)*t+(2*p0-5*p1+4*p2-p3)*t*t+(-p0+3*p1-3*p2+p3)*t*t*t))
    return out
def wing(side,upper):
    z=.56 if upper else .43;node=b.empty('GB2_Wing%s%d'%('Upper' if upper else 'Lower',side),root,(side*.055,0 if upper else .055,z))
    control=[(.045,.040),(.045,.21),(.17,.42),(.37,.49),(.47,.43),(.43,.21),(.28,.065),(.070,.012)] if upper else [(.050,-.035),(.10,.005),(.28,-.035),(.34,-.16),(.28,-.27),(.145,-.275),(.065,-.16)]
    control=[(x*.82,z*.90) for x,z in control]
    outline=curve_outline(control);center=sum(outline,Vector((0,0)))/len(outline);n=len(outline);rings=12;verts=[];uv=[];faces=[]
    def surface(p,t,back=False):return (side*p.x,(-.013 if not back else .004)-.012*(1-t*t),p.y)
    def cross(a,c):return a.x*c.y-a.y*c.x
    def surface_point(p,offset=0):
        direction=p-center;distance=100.0
        for a,c in zip(outline,outline[1:]+outline[:1]):
            edge=c-a;den=cross(direction,edge)
            if abs(den)<1e-9:continue
            t=cross(a-center,edge)/den;u=cross(a-center,direction)/den
            if t>0 and 0<=u<=1:distance=min(distance,t)
        value=surface(p,min(1,1/max(.001,distance)),False)
        return (value[0],value[1]-offset,value[2])
    for back in [False,True]:
        for j in range(rings+1):
            t=max(.0001,j/rings)
            for k,p in enumerate(outline):
                pos=center.lerp(p,t);verts.append(surface(pos,t,back));uv.append((k/n,t))
    count=(rings+1)*n
    for shell in range(2):
        for j in range(rings):
            for k in range(n):
                a=shell*count+j*n+k;f=(a,shell*count+j*n+(k+1)%n,shell*count+(j+1)*n+(k+1)%n,a+n);faces.append(tuple(reversed(f)) if shell else f)
    for k in range(n):faces.append((rings*n+k,rings*n+(k+1)%n,count+rings*n+(k+1)%n,count+rings*n+k))
    obj=b.fast['fast_instance'](b.name('DomedWingEnamel'),verts,faces,'Porcelain',node,(0,0,0),smooth_faces=True,uv=uv)
    bm=bmesh.new();bm.from_mesh(obj.data);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(obj.data);bm.free()
    b.tube('WingRolledGoldRim',[(side*p.x,-.019,p.y) for p in outline+[outline[0]]],.0095,'ArchiveGold',node)
    # Large curved branches with a finer repeating edge stitch.
    root_point=Vector((.042,.040) if upper else (.047,-.043))
    for tip in [control[k] for k in ([2,3,4,5,6] if upper else [1,2,3,4,5])]:
        end=Vector(tip);middle=(end+root_point)*.5+Vector((-.026,.016));path=[]
        for j in range(25):
            t=j/24;p=(1-t)**2*root_point+2*(1-t)*t*middle+t*t*end
            path.append(surface_point(p,.0025))
        b.tube('CurvedWingSpar',path,.0048,'ArchiveGold',node)
        # Rear reinforcement fits the same shell, with visible screwed seats.
        back_path=[(x,y+.021,z) for x,y,z in path]
        b.tube('RearWingRib',back_path,.0032,'Nickel',node)
        for j in [8,17]:
            x,y,z=back_path[j];b.cyl('RearRibFastener',.004,.003,'ArchiveGold',node,(x,y+.0015,z),(math.pi/2,0,0),24)
            b.cube('RearFastenerSlot',(.004,.001,.0009),'Satin',node,(x,y+.0034,z),.0002)
    for k in range(0,n,5):
        p=outline[k];sphere('WingRimRivet',.0038,'Nickel',node,(side*p.x,-.030,p.y))
    # A curved burgundy enamel ribbon follows the real outer tip instead of
    # a flat triangular sticker; both metal seat and inlay lie on this shell.
    start,end=(3*8,5*8) if upper else (3*8,5*8)
    edge=outline[start:end+1]
    outer=[p.lerp(center,.055) for p in edge]
    inner=[p.lerp(center,.10+.25*math.sin(math.pi*i/(len(edge)-1))) for i,p in enumerate(edge)]
    polygon=outer+list(reversed(inner));flat=[Vector((p.x,p.y,0)) for p in polygon]
    tris=tessellate_polygon([flat]);pv=[surface_point(p,.0015) for p in polygon]
    pf=[tuple(v if isinstance(v,int) else min(range(len(flat)),key=lambda i:(flat[i]-v).length_squared) for v in tri) for tri in tris]
    patch=b.fast['fast_instance'](b.name('CurvedBurgundyEnamel'),pv,pf,'Red',node,(0,0,0),smooth_faces=True)
    bm=bmesh.new();bm.from_mesh(patch.data);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(patch.data);bm.free()
    shell=patch.modifiers.new('Enamel inlay thickness','SOLIDIFY');shell.thickness=.0015
    border=[surface_point(p,.0025) for p in polygon]
    b.tube('CurvedInlaySeat',border+[border[0]],.0025,'ArchiveGold',node)
    b.tube('RearEdgeSeal',[(side*p.x,.005,p.y) for p in outline+[outline[0]]],.0028,'Satin',node)
    make_hinge(node,side,upper)
    return node

for side in [-1,1]:wing(side,True);wing(side,False)
# Open paired thorax rails and a segmented abdomen, with actual perch contacts.
for side in [-1,1]:
    b.tube('ThoraxRail',[(side*.026,.035,.37),(side*.030,.035,.47),(side*.025,.035,.59)],.010,'Nickel',root)
    b.beam('ShoulderCrossMember',(side*.025,.035,.55),(side*.020,.035,.56),.010,'Satin',root)
    b.beam('HindwingCrossMember',(side*.026,.035,.43),(side*.020,.090,.43),.010,'Satin',root)
for i,z in enumerate([.305,.34,.375,.410,.455,.50,.55,.59]):
    r=.021 if i<3 else .030
    sphere('AbdomenSegment',r,'Satin' if i%2 else 'Nickel',root,(0,0,z),(.83,.85,1.14))
    b.torus('AbdomenUnion',r*.85,.003,'ArchiveGold',root,(0,0,z-.011))
    if i>=3:sphere('VentralPlate',r*.72,'Porcelain',root,(0,-r*.8,z),(.75,.19,.82))
for z in [.462,.518]:
    barrel=b.sleeve('ClockDriveBarrel',.026,.020,.039,'ArchiveGold',root,(0,.045,z),64);barrel.rotation_euler.x=math.pi/2
    b.cyl('DriveBarrelAxle',.006,.046,'Nickel',root,(0,.045,z),(math.pi/2,0,0),32)
    for j in range(6):
        a=j*math.tau/6;b.beam('VentedBarrelSpoke',(.006*math.cos(a),.064,z+.006*math.sin(a)),(.021*math.cos(a),.064,z+.021*math.sin(a)),.0025,'Nickel',root)
    for i in range(12):
        a=i*math.tau/12;b.cube('WindingTeeth',(.004,.014,.009),'Nickel',root,(.029*math.sin(a),.054,z+.029*math.cos(a)),.001,(0,a,0))
sphere('GarnetHead',.040,'Red',root,(0,0,.64),(.8,.75,1.08))
b.torus('HeadCollar',.029,.004,'ArchiveGold',root,(0,0,.607))
for side in [-1,1]:
    for y in [.012]:sphere('OpticalEye',.009,'Lens',root,(side*.029,y-.026,.647),(.6,.8,1))
    a=Vector((side*.014,0,.673));mid=Vector((side*.020,-.035,.834));end=Vector((side*.068,-.020,.79))
    b.tube('SpringAntenna',[(1-t)**2*a+2*(1-t)*t*mid+t*t*end for t in [i/32 for i in range(33)]],.003,'ArchiveGold',root)
    sphere('AntennaTip',.007,'Porcelain',root,end)
    # Raised branches stay within the original disc's label-scale mount area.
    b.tube('PerchBranch',[(0,0,.10),(side*.060,.080,.18),(side*.120,.052,.23)],.009,'ArchiveGold',root)
    for i,z in enumerate([.40,.43,.46]):
        tip=Vector((side*(.055+i*.027),.076-i*.010,.178+i*.020));knee=Vector((side*(.075+i*.020),.140,.29+i*.025));start=Vector((side*.022,.105,z))
        b.beam('LegCoxa',(side*.022,.022,z),start,.004,'Nickel',root);sphere('CoxaJoint',.006,'ArchiveGold',root,start)
        b.beam('LegFemur',start,knee,.0035,'Nickel',root);sphere('LegKnee',.005,'ArchiveGold',root,knee)
        b.beam('LegTibia',knee,tip,.0030,'Nickel',root)
        b.tube('PerchGrasp',[tip+Vector((0,-.009,0)),tip+Vector((0,-.009,-.009)),tip+Vector((0,.006,-.012))],.0027,'Satin',root)
foot=b.cyl('FootMount',.092,.018,'Nickel',root,(0,0,.025),n=96)
# Blind underside socket clears the real record spindle while retaining
# a solid upper web under the perch column.
cutter=b.cyl('TemporarySpindlePocket',.034,.012,'Black',root,(0,0,.021),n=64)
bpy.context.view_layer.update();bpy.context.view_layer.objects.active=foot
cut=foot.modifiers.new('Blind record spindle socket','BOOLEAN');cut.operation='DIFFERENCE';cut.solver='EXACT';cut.object=cutter;bpy.ops.object.modifier_apply(modifier=cut.name);bpy.data.objects.remove(cutter,do_unlink=True)
b.sleeve('FootBrassRim',.096,.087,.016,'ArchiveGold',root,(0,0,.032),96)
b.cyl('PerchColumn',.020,.074,'Nickel',root,(0,0,.070),n=48)
for z in [.045,.071,.095]:b.torus('ColumnCollar',.021,.003,'ArchiveGold',root,(0,0,z))

# Author a bounded 18 second motion take: rest, open, preload, beats, settle, rest.
scene=bpy.context.scene;scene.render.fps=30;scene.frame_end=541
max_error=0.;min_reach=1.;keys=[]
for frame in range(1,542):
    t=(frame-1)/30
    smooth=lambda u:(max(0,min(1,u)))**2*(3-2*max(0,min(1,u)))
    aperture=smooth((t-1)/2.4)*(1-smooth((t-14)/2.6))
    energy=smooth((t-5)/.8)*(1-smooth((t-10.5)/1.4))
    for d in drives:
        phase=t*math.tau*1.30-(0 if d['upper'] else .28)
        theta=.20+(1-aperture)*.98+math.sin(phase)*(.010+energy*.16)*(1 if d['upper'] else .70)
        B,C,phi=closure(theta,d['side']);origin=d['center']+Vector((0,0,d['height']));a=Vector((d['side']*A.x,A.y,0))
        d['wing'].rotation_euler.z=-d['side']*theta;d['crank'].rotation_euler.z=d['side']*phi
        d['rod'].location=origin+C;d['rod'].rotation_mode='QUATERNION';axis=(B-C).normalized();up=Vector((0,0,1));d['rod'].rotation_quaternion=Matrix((up.cross(axis),up,axis)).transposed().to_quaternion()
        max_error=max(max_error,abs((B-C).length-ROD),abs((C-a).length-CRANK))
        for key in ['wing','crank']:d[key].keyframe_insert('rotation_euler',frame=frame)
        d['rod'].keyframe_insert('location',frame=frame);d['rod'].keyframe_insert('rotation_quaternion',frame=frame)
for action in bpy.data.actions:
    for layer in action.layers:
        for strip in layer.strips:
            for bag in strip.channelbags:
                for fc in bag.fcurves:
                    for key in fc.keyframe_points:key.interpolation='LINEAR'
assert max_error<1e-6,max_error
scene.frame_set(120);bpy.context.view_layer.update()
# Component-only runtime geometry, no shared HELIOS base or replacement record.
folder=ROOT/'app/assets/collection/components';folder.mkdir(exist_ok=True)
bpy.ops.object.select_all(action='DESELECT')
for obj in [root]+list(root.children_recursive):obj.select_set(True)
bpy.context.view_layer.objects.active=root
bpy.ops.export_scene.gltf(filepath=str(folder/'G_butterfly_r2.glb'),export_format='GLB',use_selection=True,export_apply=True,export_animations=False)
entry={'root':root.name,'source_blend':'blender/collection/G_butterfly_r2.blend','status':'Independent structural work in progress; not integrated','coordinate_system':'Blender Z-up, front negative Y; runtime adapter not yet implemented','mount_offset_z':.00125,'drive':{'a':list(A),'crank_length':CRANK,'rod_length':ROD,'horn_radius':HORN},'rig':[{'wing':d['wing'].name,'crank':d['crank'].name,'rod':d['rod'].name,'side':d['side'],'upper':d['upper'],'center':list(d['center']),'link_height':d['height']} for d in drives]}
(folder/'G_butterfly_r2.json').write_text(json.dumps(entry,indent=2)+'\n')
# Neutral source preview. Reference disc is excluded from the exported component.
b.cyl('ReferenceOriginalDisc',.420,.02352,'Black',b.root,(0,0,-.005),n=128)
scene.render.engine='CYCLES';scene.cycles.samples=24;scene.cycles.use_denoising=True;scene.render.resolution_x=1200;scene.render.resolution_y=1200;scene.render.resolution_percentage=100;scene.render.film_transparent=True
world=bpy.data.worlds.new('ButterflyStudio');world.use_nodes=True;scene.world=world
tex=world.node_tree.nodes.new('ShaderNodeTexEnvironment');tex.image=bpy.data.images.load(str(ROOT/'app/assets/studio_small_09_4k.exr'),check_existing=True);bg=next(n for n in world.node_tree.nodes if n.type=='BACKGROUND');bg.inputs['Strength'].default_value=.25;world.node_tree.links.new(tex.outputs['Color'],bg.inputs['Color'])
for i,(loc,power) in enumerate([((-2,-3,3),150),((2,1,3),180)]):
    light=bpy.data.lights.new('Studio'+str(i),'AREA');light.energy=power;light.shape='DISK';light.size=2;obj=bpy.data.objects.new(light.name,light);scene.collection.objects.link(obj);obj.location=loc;obj.rotation_euler=(Vector((0,0,.48))-obj.location).to_track_quat('-Z','Y').to_euler()
data=bpy.data.cameras.new('ButterflyCamera');camera=bpy.data.objects.new(data.name,data);scene.collection.objects.link(camera);scene.camera=camera;data.type='ORTHO';data.ortho_scale=1.25
camera.location=(.35,-3.5,1.25);camera.rotation_euler=(Vector((0,0,.48))-camera.location).to_track_quat('-Z','Y').to_euler()
path=ROOT/'blender/collection/G_butterfly_r2.blend'
if path.exists():
    backup=ROOT/'blender/collection/checkpoints'/('G_butterfly_r2-'+hashlib.sha256(path.read_bytes()).hexdigest()[:12]+'.blend');backup.write_bytes(path.read_bytes())
scene['status']='Independent structure and fitted wing-surface pass; full mesh sweeps and integration pending. Not in App.';bpy.ops.wm.save_as_mainfile(filepath=str(path));bpy.ops.file.make_paths_relative();bpy.ops.wm.save_as_mainfile(filepath=str(path))
review=ROOT/'review/G_optical_curator/butterfly_r2';review.mkdir(exist_ok=True)
(review/'drive_closure.json').write_text(json.dumps({'frames':541,'linkages':4,'max_length_error':max_error,'scope':'Four-bar analytic closure only; not triangle collision clearance or app acceptance'},indent=2)+'\n')
if '--no-render' not in sys.argv:
    for label,frame in [('component_open',120),('component_folded',1),('component_beat',204)]:
        scene.frame_set(frame);scene.render.filepath=str(review/(label+'.png'));bpy.ops.render.render(write_still=True)
    scene.frame_set(120);camera.location=(-.35,3.5,1.25);camera.rotation_euler=(Vector((0,0,.48))-camera.location).to_track_quat('-Z','Y').to_euler();scene.render.filepath=str(review/'component_rear.png');bpy.ops.render.render(write_still=True)
from optimize_runtime_meshes import optimize
optimize(folder/'G_butterfly_r2.glb')
print('BUTTERFLY_COMPONENT_SAVED',max_error,flush=True)
