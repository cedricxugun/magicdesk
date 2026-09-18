"""Restore original normal-operation silhouette. Isolated candidate, never a main-App promotion."""
import bpy,bmesh,sys,math,json,hashlib
from pathlib import Path
from mathutils import Vector,Matrix,Quaternion
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(Path(__file__).parent))
from geometry import Builder,C,smooth,pose
SOURCE=ROOT/'blender/collection/I_art_r8.blend';SHELL=ROOT/'blender/collection/I_assembly_r5.blend'
TARGET=ROOT/'blender/collection/I_restore_r9.blend';OUT=ROOT/'review/I_refinement/restore_r9';OUT.mkdir(parents=True,exist_ok=True)
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
assert sha(SOURCE)==json.loads((ROOT/'review/I_refinement/art_r8/build.json').read_text())['source_sha256']
assert sha(SHELL)==json.loads((ROOT/'review/I_refinement/assembly_r5/build.json').read_text())['source_sha256']
if TARGET.exists():
    previous=json.loads((OUT/'build.json').read_text());assert sha(TARGET)==previous['source_sha256'],'Unrecorded candidate edits'
    backup=TARGET.parent/'checkpoints'/('I-r9-'+sha(TARGET)[:12]+'.blend');backup.parent.mkdir(exist_ok=True);backup.write_bytes(TARGET.read_bytes())
bpy.ops.wm.open_mainfile(filepath=str(SOURCE));scene=bpy.context.scene;scene.frame_set(1)
root=bpy.data.objects['IH1_MODULE'];upper=bpy.data.objects['IH1_UPPER'];fixed=bpy.data.objects['IH1_FixedChamber']
for o in [root]+list(root.children_recursive):o.animation_data_clear()
# Unsplit cage skeleton remains stationary, preserving R8 manufactured details and lower seating.
for name in ['IS7_CageLeft','IS7_CageRight']:
    node=bpy.data.objects[name]
    for child in list(node.children):
        world=child.matrix_world.copy();child.parent=fixed;child.matrix_world=world
    bpy.data.objects.remove(node,do_unlink=True)
bpy.context.view_layer.update()
# Remove only old front split assemblies and their obsolete sliding guides/mounts.
removed=[]
for o in list(bpy.data.objects):
    if o.name.startswith('IS7_FrontShell'):
        for c in list(o.children_recursive):removed.append(c.name);bpy.data.objects.remove(c,do_unlink=True)
        removed.append(o.name);bpy.data.objects.remove(o,do_unlink=True)
old_guide_names={x['barrel'] for x in json.loads((ROOT/'review/I_refinement/r1/guide_manifest.json').read_text())}
for row in json.loads((ROOT/'review/I_refinement/assembly_r5/build.json').read_text())['guide_mounts']:
    old_guide_names.update(row[k] for k in ['fused','clamp','saddle','web'] if k in row)
for name in old_guide_names:
    o=bpy.data.objects.get(name)
    if o:removed.append(name);bpy.data.objects.remove(o,do_unlink=True)
b=Builder.__new__(Builder);b.id='IR9';b.serial=0;b.root=root;b.upper=upper;b.col=bpy.data.collections.new('I_ORIGINAL_RESTORE_R9');scene.collection.children.link(b.col);b.mats={}
for name,color,metal,rough in [('Nickel',(.40,.43,.42),.95,.28),('DarkNickel',(.065,.077,.073),.82,.32),('Bronze',(.43,.25,.09),.93,.29),('Rubber',(.014,.018,.016),0,.65),('Red',(.32,.012,.008),.18,.27)]:b.material(name,color,metal,rough)
ns={'bpy':bpy,'math':math,'Vector':Vector,'Matrix':Matrix,'Quaternion':Quaternion,'COL':b.col,'M':b.mats};exec(compile((ROOT/'blender/fast_geometry.py').read_text(),str(ROOT/'blender/fast_geometry.py'),'exec'),ns);b.fast=ns
# Load only a copy of the manufactured unsplit porcelain/edge/screw assemblies from R5.
with bpy.data.libraries.load(str(SHELL),link=False) as (src,dst):
    original_names=list(src.objects);dst.objects=original_names.copy()
loaded=dict(zip(original_names,dst.objects))
for obj in loaded.values():
    b.col.objects.link(obj);obj.animation_data_clear()
bpy.context.view_layer.update();panels=[];kept=[];shell_world_reference={}
for i in range(6):
    group=b.empty('IR9_Shell'+str(i),upper);panels.append(group);bpy.context.view_layer.update()
    for obj in list(loaded['IH1_FrontPanel'+str(i)].children_recursive):
        name=next(k for k,v in loaded.items() if v==obj)
        if not any(x in name for x in ['Porcelain','PanelLip','Screw','HoodAttachment']):continue
        world=obj.matrix_world.copy();obj.parent=group;obj.matrix_parent_inverse=Matrix.Identity(4);obj.matrix_basis=group.matrix_world.inverted()@world;obj.name='IR9_Restored_'+name;kept.append(obj);shell_world_reference[obj.name]=world
for obj in loaded.values():
    if obj not in kept:bpy.data.objects.remove(obj,do_unlink=True)
bpy.context.view_layer.update()
shell_transfer_error=max(abs(obj.matrix_world[r][c]-shell_world_reference[obj.name][r][c]) for obj in kept for r in range(4) for c in range(4));assert shell_transfer_error<1e-6,shell_transfer_error
P=[Vector(v) for v in [(-.38,-.53,2.25),(-.15,.62,2.10),(.45,.78,2.82),(.45,.74,3.38)]]
R=[(0,.90),(.14,.89),(.28,.93),(.43,.85),(.60,.65),(.76,.39),(.9,.18),(1,.055)]
def center(t):return P[0]*(1-t)**3+P[1]*3*(1-t)**2*t+P[2]*3*(1-t)*t*t+P[3]*t**3
def tangent(t):return ((P[1]-P[0])*(1-t)**2+(P[2]-P[1])*2*(1-t)*t+(P[3]-P[2])*t*t).normalized()
def radius(t):
    for (a,x),(c,y) in zip(R,R[1:]):
        if t<=c:return x+(y-x)*smooth((t-a)/(c-a))
    return R[-1][1]
frames=[];last=tangent(0);normal=(Vector((0,0,1))-last*last.z).normalized()
for j in range(601):
    axis=tangent(j/600);normal=last.rotation_difference(axis)@normal;normal=(normal-axis*normal.dot(axis)).normalized();frames.append((normal.copy(),axis.cross(normal).normalized()));last=axis
def axes(t):return frames[round(t*600)]
def point(t,a,r):
    n,v=axes(t);return center(t)+(n*math.cos(a)+v*math.sin(a))*r
# A continuous close-fitted acoustic skin replaces empty space between the annular ribs.
# Real oval perforations: each cell is a closed annular mesh with a hole, not a black decal.
core=[]
for band in range(14):
    t0=.05+.83*band/14+.008;t1=.05+.83*(band+1)/14-.008
    count=max(16,round(math.tau*radius((t0+t1)/2)*.63/.058));verts=[];faces=[]
    for k in range(count):
        a=(k+.5)*math.tau/count;da=math.pi/count;tm=(t0+t1)/2;dt=(t1-t0)/2
        # Polygonal cell boundary and elliptical bore share radial order.
        boundary=[(-1,-1),(0,-1),(1,-1),(1,0),(1,1),(0,1),(-1,1),(-1,0)]
        base=len(verts)
        for inner_depth in [0,.004]:
            for hole in [False,True]:
                for dx,dy in boundary:
                    if hole:
                        l=math.hypot(dx,dy);dx=dx/l*.51;dy=dy/l*.68
                    tt=tm+dy*dt;aa=a+dx*da;verts.append(point(tt,aa,radius(tt)*.635-inner_depth))
        for j in range(8):
            q=(j+1)%8
            for offset,rev in [(0,False),(16,True)]:
                f=(base+offset+j,base+offset+q,base+offset+8+q,base+offset+8+j);faces.append(f[::-1] if rev else f)
            faces.append((base+8+j,base+8+q,base+24+q,base+24+j));faces.append((base+j,base+16+j,base+16+q,base+q))
    o=b.fast['fast_instance'](b.name('ContinuousAcousticSkin'),verts,faces,'DarkNickel',upper,(0,0,0),smooth_faces=True)
    bm=bmesh.new();bm.from_mesh(o.data);bmesh.ops.remove_doubles(bm,verts=list(bm.verts),dist=1e-6);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(o.data);bm.free();core.append(o.name)
    # Rolled lips connect into annular frame material at both ends.
    for t in [t0,t1]:b.tube('CoreRolledSeam',[point(t,k*math.tau/96,radius(t)*.644) for k in range(97)],min(.012,radius(t)*.025),'Nickel',upper)
# Four-bar geometry: two equal parallel links per side; both ends physically pinned.
def apply(o):
    bpy.context.view_layer.objects.active=o
    for m in list(o.modifiers):bpy.ops.object.modifier_apply(modifier=m.name)
def sleeve(name,r,inside,depth,parent,position,axis,material='Nickel'):
    o=b.sleeve(name,r,inside,depth,material,parent,position,48);o.rotation_euler=axis.to_track_quat('Z','Y').to_euler();o.modifiers[0].width=min(.001,depth*.1);return o
routes=[]
for i,group in enumerate(panels):
    t=(i+.5)/6;rr=radius(t);n,v=axes(t);ax=tangent(t);drive=n*.10*rr+ax*.27*rr;hinge_axis=v;angle=[1.12,.94,.72,.72,.72,.72][i]
    # Quaternion sign is chosen to increase outward displacement.
    if (Quaternion(hinge_axis,angle)@drive-drive).dot(n)<0:angle=-angle
    motion={'name':group.name,'axis':list(v),'drive':list(drive),'angle':angle,'links':[],'anchors':[]}
    for side in [-1,1]:
        for j,depth in enumerate([-.030,.030]):
            tip=center(t)+n*math.cos(1.06)*rr*.958+v*side*math.sin(1.06)*rr*.958+ax*depth*min(1,rr/.3)
            anchor=tip-drive
            link=b.empty('IR9_Link_%d_%d_%d'%(i,side,j),upper,anchor)
            shaft_r=.008*min(1,rr/.25);eye_r=shaft_r*2.4;thick=shaft_r*1.3
            # Machined web ends before the bored eyes, so the pin does not pierce solid web.
            unit=drive.normalized();b.beam('LinkWeb',unit*eye_r*.8,drive-unit*eye_r*.8,shaft_r*.7,'Nickel',link)
            for p in [Vector(),drive]:sleeve('LinkEye',eye_r,shaft_r*1.08,thick,link,p,v)
            # Fixed bearing cheeks and continuous cross-pin, with explicit running gaps.
            for s in [-1,1]:
                sleeve('FixedPivotCheek',eye_r*1.12,shaft_r*1.05,thick*.55,upper,anchor+v*s*thick*.90,v,'DarkNickel')
            b.cyl('FixedHingePin',shaft_r,thick*2.8,'Bronze',upper,anchor,v.to_track_quat('Z','Y'),48)
            b.cyl('MovingHingePin',shaft_r,thick*2.8,'Bronze',group,tip,v.to_track_quat('Z','Y'),48)
            for s in [-1,1]:sleeve('ShellPivotCheek',eye_r*1.12,shaft_r*1.05,thick*.55,group,tip+v*s*thick*.90,v,'DarkNickel')
            # Seat bearing bosses to the retained spine and shell (provisional structural routing).
            spine=point(t,side*math.pi/2,rr-.05)
            b.beam('SpinePivotSeat',spine,anchor,shaft_r*1.8,'DarkNickel',upper)
            skin=point(t,side*1.06,rr-.018)+ax*depth*min(1,rr/.3)
            b.beam('ShellPivotSeat',tip,skin,shaft_r*1.8,'Nickel',group)
            motion['links'].append(link.name);motion['anchors'].append({'fixed':list(anchor),'moving':list(tip)})
    routes.append(motion)
# Normal operation is independent of maintenance. A baked opening, hold, and reverse closing.
scene.render.fps=30;scene.frame_start=1;scene.frame_end=301
for frame in range(1,302):
    sec=(frame-1)/30
    progress=smooth((sec-.5)/2.) if sec<5 else 1.-smooth((sec-5.5)/2.)
    for i,row in enumerate(routes):
        amount=smooth((progress-i*.09)/.55);q=Quaternion(Vector(row['axis']),row['angle']*amount);offset=q@Vector(row['drive'])-Vector(row['drive'])
        group=panels[i];group.location=offset;group.keyframe_insert(data_path='location',frame=frame)
        for name in row['links']:
            link=bpy.data.objects[name];link.rotation_mode='QUATERNION';link.rotation_quaternion=q;link.keyframe_insert(data_path='rotation_quaternion',frame=frame)
    # Keep aperture opening linked to first half-second, exposing the real perforated cartridge.
    iris=smooth(sec/.5) if sec<5.5 else 1.-smooth((sec-7.5)/.5)
    for i in range(6):
        leaf=bpy.data.objects['IH1_IrisLeaf'+str(i)];leaf.rotation_euler.z=float(leaf['home_angle'])-1.05*iris;leaf.keyframe_insert(data_path='rotation_euler',frame=frame)
    cam=bpy.data.objects['IH1_IrisCamDrive'];cam.rotation_euler.z=-.30*iris;cam.keyframe_insert(data_path='rotation_euler',frame=frame)
for o in b.col.objects:
    if o.type=='MESH':apply(o)
for img in bpy.data.images:
    if img.source=='FILE' and img.filepath and not img.packed_file:img.filepath=bpy.path.relpath(bpy.path.abspath(img.filepath),start=str(TARGET.parent))
# Structural motion check independent of keyframe values: both ends of every rigid link meet pins.
errors=[];samples=[]
for frame in range(1,302,2):
    scene.frame_set(frame);bpy.context.view_layer.update();maxgap=0.
    for row in routes:
        group=bpy.data.objects[row['name']]
        for name,anchor in zip(row['links'],row['anchors']):
            link=bpy.data.objects[name]
            maxgap=max(maxgap,(link.matrix_world@Vector(row['drive'])-group.matrix_world@Vector(anchor['moving'])).length)
    samples.append({'frame':frame,'pin_gap':maxgap})
    if maxgap>1e-5:errors.append(samples[-1])
assert not errors,errors[:2]
source_poses={}
for frame in [1,16,35,55,76,120,175,210,245,301]:
    scene.frame_set(frame);bpy.context.view_layer.update();source_poses[str(frame)]={o.name:pose(o.matrix_world) for o in panels}
scene.frame_set(1);bpy.ops.wm.save_as_mainfile(filepath=str(TARGET))
bpy.ops.object.select_all(action='DESELECT')
for o in [root]+list(root.children_recursive):o.select_set(True)
bpy.context.view_layer.objects.active=root;component=ROOT/'app/assets/collection/components/I_restore_r9.glb'
bpy.ops.export_scene.gltf(filepath=str(component),export_format='GLB',use_selection=True,export_apply=False,export_animations=False,export_morph=True,export_extras=True)
rig={'version':1,'component':'res://assets/collection/components/I_restore_r9.glb','panels':[]}
for row in routes:
    x=dict(row);x['axis']=list((C.to_3x3()@Vector(row['axis'])));x['drive']=list((C.to_3x3()@Vector(row['drive'])));rig['panels'].append(x)
(ROOT/'app/assets/collection/i_restore_rig_r9.json').write_text(json.dumps(rig,indent=2)+'\n')
(OUT/'source_poses.json').write_text(json.dumps(source_poses,indent=2)+'\n')
(OUT/'build.json').write_text(json.dumps({'source':str(TARGET.relative_to(ROOT)),'source_sha256':sha(TARGET),'component':str(component.relative_to(ROOT)),'component_sha256':sha(component),'inputs':{str(SOURCE.relative_to(ROOT)):sha(SOURCE),str(SHELL.relative_to(ROOT)):sha(SHELL)},'restored_panels':len(panels),'retained_shell_parts':len(kept),'shell_transfer_matrix_error':shell_transfer_error,'continuous_core_sections':len(core),'removed_obsolete':removed,'sampled_link_pin_gap_max':max(x['pin_gap'] for x in samples),'scope':'Independent original-operation restoration candidate, not art acceptance. No split-cage animation. New support routes, shell/core/neighbor clearance, complete membrane/fork choreography, audio and native input unverified.'},indent=2)+'\n')
print('I_RESTORE_R9',len(panels),'shells',len(core),'core sections',flush=True)
