"""Validated internal frame grooves, derived from the preserved manufacturing R5 source."""
import bpy,bmesh,json,hashlib,shutil,math,sys
from pathlib import Path
from mathutils import Vector,Matrix,Quaternion
from mathutils.bvhtree import BVHTree
ROOT=Path(__file__).resolve().parents[2];SOURCE=ROOT/'blender/collection/I_assembly_r5.blend';TARGET=ROOT/'blender/collection/I_clearance_r6.blend'
sys.path.insert(0,str(Path(__file__).parent))
from geometry import Builder
OUT=ROOT/'review/I_refinement/clearance_r6';OUT.mkdir(parents=True,exist_ok=True)
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
previous=json.loads((ROOT/'review/I_refinement/assembly_r5/build.json').read_text());assert sha(SOURCE)==previous['source_sha256']
if TARGET.exists():
    saved=json.loads((OUT/'build.json').read_text());assert sha(TARGET)==saved['source_sha256'],'Unrecorded clearance-source edits'
    backup=TARGET.parent/'checkpoints'/('I-clearance-'+sha(TARGET)[:12]+'.blend');backup.write_bytes(TARGET.read_bytes())
bpy.ops.wm.open_mainfile(filepath=str(SOURCE));scene=bpy.context.scene;scene.frame_set(1)
root=bpy.data.objects['IH1_MODULE'];fixed=bpy.data.objects['IH1_FixedChamber']
P=[Vector(v) for v in [(-.38,-.53,2.25),(-.15,.62,2.10),(.45,.78,2.82),(.45,.74,3.38)]]
def center(t):return P[0]*(1-t)**3+P[1]*3*(1-t)**2*t+P[2]*3*(1-t)*t*t+P[3]*t**3
def tangent(t):return ((P[1]-P[0])*(1-t)**2+(P[2]-P[1])*2*(1-t)*t+(P[3]-P[2])*t*t).normalized()
R=[(0,.90),(.14,.89),(.28,.93),(.43,.85),(.60,.65),(.76,.39),(.9,.18),(1,.055)]
def radius(t):
    for (a,x),(c,y) in zip(R,R[1:]):
        if t<=c:
            u=max(0.,min(1.,(t-a)/(c-a)));return x+(y-x)*u*u*(3-2*u)
    return R[-1][1]
frames=[];previous_axis=tangent(0);normal=(Vector((0,0,1))-previous_axis*previous_axis.z).normalized()
for j in range(301):
    axis=tangent(j/300);normal=previous_axis.rotation_difference(axis)@normal;normal=(normal-axis*normal.dot(axis)).normalized();frames.append((normal.copy(),axis.cross(normal).normalized()));previous_axis=axis
centers=[fixed.matrix_world@center(j/300) for j in range(301)]
def geo(obj):
    ev=obj.evaluated_get(bpy.context.evaluated_depsgraph_get());mesh=ev.to_mesh();mesh.calc_loop_triangles();vs=[obj.matrix_world@v.co for v in mesh.vertices];fs=[tuple(t.vertices) for t in mesh.loop_triangles];ev.to_mesh_clear();return vs,fs
spines=sorted([o for o in fixed.children if 'ChamberSpine' in o.name],key=lambda o:o.name)
spine_start=.05+.83/14
def rail_radius(t):
    r=radius(t);u=max(0.,min(1.,(t-spine_start)/.15));u=u*u*(3-2*u)
    return r*.66+(max(r*.66,r-.080)-r*.66)*u
def rail_point(t,angle):
    n,v=frames[round(t*300)];return center(t)+(n*math.cos(angle)+v*math.sin(angle))*rail_radius(t)
for spine,angle in zip(spines,[math.pi/2-.032,math.pi/2+.032,-math.pi/2-.032,-math.pi/2+.032]):
    spine.data=spine.data.copy();spine.data.use_fill_caps=True;spine.data.bevel_depth=.018;points=spine.data.splines[0].points
    for j,p in enumerate(points):
        t=spine_start+(1-spine_start)*j/(len(points)-1);n,v=frames[round(t*300)]
        p.co=(*(spine.matrix_local.inverted()@rail_point(t,angle)),1);p.radius=min(1.,radius(t)/.25)
# The front support ring belongs to the removable perforated assembly.
front_ring=bpy.data.objects['IH1_AcousticChamberRib_0194'];world=front_ring.matrix_world.copy();front_ring.parent=bpy.data.objects['IS4_PerforatedCartridge'];front_ring.matrix_world=world
groups=json.loads(json.dumps(previous['groups']));next(g for g in groups if g['name']=='IS4_PerforatedCartridge')['members'].append(front_ring.name)
bpy.context.view_layer.update()
b=Builder.__new__(Builder);b.id='IS6';b.serial=0;b.root=root;b.upper=fixed
b.col=bpy.data.collections.new('I_FRAME_WEBS_R6');scene.collection.children.link(b.col)
b.mats={'FrameMetal':bpy.data.materials['Collection_HelixSupportNickel']}
ns={'bpy':bpy,'math':math,'Vector':Vector,'Matrix':Matrix,'Quaternion':Quaternion,'COL':b.col,'M':b.mats}
exec(compile((ROOT/'blender/fast_geometry.py').read_text(),str(ROOT/'blender/fast_geometry.py'),'exec'),ns);b.fast=ns
frame_webs=[]
for index in range(1,15):
    t=.05+.83*index/14;n,v=frames[round(t*300)];rib=bpy.data.objects['IH1_AcousticChamberRib_'+str(194+index).zfill(4)]
    for side in [1,-1]:
        angle=side*math.pi/2-.032;first=center(t)+(n*math.cos(angle)+v*math.sin(angle))*radius(t)*.66;last=rail_point(t,angle)
        if (last-first).length<.002:continue
        web=b.beam('RadialFrameWeb',first,last,.007*min(1.,radius(t)/.35),'FrameMetal',fixed)
        frame_webs.append({'name':web.name,'rib':rib.name,'spine':spines[0 if side>0 else 2].name})
    if index in [1,5,9,14]:
        for side in [1,-1]:
            web=b.beam('TwinRailTie',rail_point(t,side*math.pi/2-.032),rail_point(t,side*math.pi/2+.032),.006*min(1.,radius(t)/.35),'FrameMetal',fixed)
            frame_webs.append({'name':web.name,'rail_pair':[o.name for o in spines[0:2] if side>0] if side>0 else [o.name for o in spines[2:4]]})
for obj in b.col.objects:
    if obj.type!='MESH':continue
    if obj.data.users>1:obj.data=obj.data.copy()
    bm=bmesh.new();bm.from_mesh(obj.data);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(obj.data);bm.free()
tools=[]
for spine in spines:
    cutter=spine.copy();cutter.data=spine.data.copy();cutter.name='GrooveTool_'+spine.name;spine.users_collection[0].objects.link(cutter)
    cutter.data.bevel_depth+=.0015;cutter.data.use_fill_caps=True
    bpy.ops.object.select_all(action='DESELECT');cutter.select_set(True);bpy.context.view_layer.objects.active=cutter;bpy.ops.object.convert(target='MESH')
    cutter=bpy.context.view_layer.objects.active;bm=bmesh.new();bm.from_mesh(cutter.data);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(cutter.data);bm.free()
    tools.append((spine,cutter))
rows=[];changed=[]
shells=[o for o in root.children_recursive if 'RearPorcelain' in o.name and 'Hood' not in o.name and o.type=='MESH']
for shell in shells:
    old=shell.data.copy();v,f=geo(shell);outer=[]
    for face in f:
        a,b,c=[v[k] for k in face];mid=(a+b+c)/3;radial=mid-min(centers,key=lambda p:(p-mid).length_squared)
        if (b-a).cross(c-a).normalized().dot(radial.normalized())>.30:outer.append(face)
    outer_tree=BVHTree.FromPolygons(v,outer,all_triangles=True);whole=BVHTree.FromPolygons(v,f,all_triangles=True)
    applied=[];rejected=[]
    for spine,cutter in tools:
        cv,cf=geo(cutter);ct=BVHTree.FromPolygons(cv,cf,all_triangles=True)
        if not whole.overlap(ct):continue
        outside_hits=len(outer_tree.overlap(ct))
        if outside_hits:
            rejected.append({'spine':spine.name,'reason':'cutter intersects selected exterior surface','triangles':outside_hits});continue
        if shell.data.users>1:shell.data=shell.data.copy()
        bpy.context.view_layer.update();bpy.context.view_layer.objects.active=shell
        mod=shell.modifiers.new('Internal spine seating groove','BOOLEAN');mod.operation='DIFFERENCE';mod.object=cutter;bpy.ops.object.modifier_apply(modifier=mod.name);applied.append(spine.name)
    bm=bmesh.new();bm.from_mesh(shell.data);nonmanifold=sum(not e.is_manifold for e in bm.edges);volume=bm.calc_volume(signed=True);bm.free()
    nv,nf=geo(shell);newtree=BVHTree.FromPolygons(nv,nf,all_triangles=True)
    exterior_error=max((newtree.find_nearest((v[a]+v[b]+v[c])/3)[3] for a,b,c in outer),default=0.)
    thickness=[]
    for a,b,c in outer:
        point=(v[a]+v[b]+v[c])/3;normal=(v[b]-v[a]).cross(v[c]-v[a]).normalized();start=point-normal*.000003
        old_hit,_,_,old_depth=whole.ray_cast(start,-normal);new_hit,_,_,new_depth=newtree.ray_cast(start,-normal)
        if old_hit is not None and old_depth>.00001:thickness.append({'before':old_depth,'after':new_depth if new_hit is not None else 0.,'required':min(.008,old_depth*.65)})
    thin=sum(r['after']+1e-6<r['required'] for r in thickness)
    accepted=nonmanifold==0 and volume>0 and exterior_error<.00001 and thin==0
    if not accepted:shell.data=old
    elif applied:changed.append(shell.name)
    rows.append({'shell':shell.name,'applied':applied if accepted else [],'rejected':rejected,'nonmanifold_edges':nonmanifold,'volume':volume,'exterior_centroid_max_error':exterior_error,'thickness_samples':len(thickness),'thin_samples':thin,'minimum_after_thickness':min((r['after'] for r in thickness),default=None),'accepted':accepted})
for _,tool in tools:bpy.data.objects.remove(tool,do_unlink=True)
for image in bpy.data.images:
    if image.source=='FILE' and image.filepath and not image.packed_file:image.filepath=bpy.path.relpath(bpy.path.abspath(image.filepath),start=str(TARGET.parent))
scene.frame_set(1);bpy.ops.wm.save_as_mainfile(filepath=str(TARGET))
bpy.ops.object.select_all(action='DESELECT')
for obj in [root]+list(root.children_recursive):obj.select_set(True)
bpy.context.view_layer.objects.active=root;component=ROOT/'app/assets/collection/components/I_clearance_r6.glb'
bpy.ops.export_scene.gltf(filepath=str(component),export_format='GLB',use_selection=True,export_apply=False,export_animations=False,export_morph=True,export_extras=True)
shutil.copy2(ROOT/'review/I_refinement/assembly_r5/take.json',OUT/'take.json')
result={'source':str(TARGET.relative_to(ROOT)),'source_sha256':sha(TARGET),'input_source_sha256':sha(SOURCE),'component':str(component.relative_to(ROOT)),'component_sha256':sha(component),'groups':groups,'core_spines':[o.name for o in spines],'spine_start':spine_start,'frame_webs':frame_webs,'reparented_front_ring':front_ring.name,'grooves':rows,'changed_shells':changed,'scope':'Tapered frame neck, radial connections between inner ribs and longitudinal rails; front ring travels with perforated cartridge. Grooves admitted only with preserved solid/exterior/thickness samples. Full geometry/transit/source-runtime checks pending.'}
(OUT/'build.json').write_text(json.dumps(result,indent=2)+'\n');print('I_CLEARANCE_R6',len(changed),'covers modified',sum(len(r['rejected']) for r in rows),'grooves rejected',flush=True)
