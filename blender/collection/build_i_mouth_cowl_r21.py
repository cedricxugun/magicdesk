"""Continue the current cowl forward around the existing A mechanism.

The monotone axial map preserves the outlet axis and every non-cowl component.
This is an independent shape candidate, not a replacement of the checked R20.
"""
import bpy,json,hashlib,math,struct,sys,shutil
from pathlib import Path
from mathutils import Vector,Matrix
ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'review/I_refinement/nautilus_r1/mouth_finish_r21';OUT.mkdir(parents=True,exist_ok=True)
TARGET=ROOT/'blender/collection/I_nautilus_mouth_cowl_r21.blend'
COMPONENT=ROOT/'app/assets/collection/components/I_nautilus_mouth_cowl_r21.glb'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
s=json.loads((ROOT/'review/I_refinement/nautilus_r1/linear_drives_r20/build.json').read_text())
assert sha(ROOT/s['source'])==s['source_sha256']
if TARGET.exists():
    old=json.loads((OUT/'build.json').read_text());assert sha(TARGET)==old['source_sha256']
    archive=OUT/'iterations'/old['source_sha256'][:12];archive.mkdir(parents=True,exist_ok=True)
    for f in OUT.glob('*.json'):shutil.copy2(f,archive/f.name)
    if (OUT/'views').exists():shutil.copytree(OUT/'views',archive/'views',dirs_exist_ok=True)
    shutil.copy2(TARGET,TARGET.parent/'checkpoints'/('I-mouth-cowl-'+old['source_sha256'][:12]+'.blend'))
bpy.ops.wm.open_mainfile(filepath=str(ROOT/s['source']));bpy.context.scene.frame_set(1);bpy.context.view_layer.update()
root=bpy.data.objects['IN1_BodyRoot'];mouth=bpy.data.objects['IAM_MODULE'];inv=mouth.matrix_world.inverted()
skins=[o for o in root.children_recursive if o.type=='MESH' and (o.name.startswith(('IN1_PorcelainPanel_','IN1_FixedRearShell_')) or o.name=='IN1_FixedMouthCheek05')]
def fingerprint(o):
    h=hashlib.sha256()
    for v in o.data.vertices:h.update(struct.pack('<3f',*v.co))
    for p in o.data.polygons:h.update(struct.pack('<'+'I'*len(p.vertices),*p.vertices))
    return [h.hexdigest(),[list(r)for r in o.matrix_world],o.parent.name if o.parent else None]
shoulder=bpy.data.objects['IN1_MouthShoulder']
protected={o.name:fingerprint(o)for o in bpy.data.objects if o.type=='MESH' and o not in skins and o!=shoulder}
start=.18/.70;end=.30/.70;extension=.215/.70
def weight(value,lo,hi):
    if value<=lo:return 1.,0.
    if value>=hi:return 0.,0.
    t=(value-lo)/(hi-lo)
    return 1.-t*t*(3.-2.*t),-6.*t*(1.-t)/(hi-lo)
def deformation(p):
    rho=math.hypot(p.x,p.y);a,da=weight(p.z,start,end);r,dr=weight(rho,.98,1.30)
    result=p.copy();result.z-=extension*a*r
    x=-extension*a*dr*p.x/max(rho,1e-8);y=-extension*a*dr*p.y/max(rho,1e-8);z=1.-extension*da*r
    assert z>=1.-1e-9
    return result,Matrix(((1,0,0),(0,1,0),(x,y,z)))
changes=[]
for o in skins:
    m=o.data;basis=inv@o.matrix_world;inverse=basis.inverted();b=basis.to_3x3();ib=b.inverted()
    normals=[v.vector.copy() for v in m.corner_normals];transforms={};distances=[];relax_weights={}
    for v in m.vertices:
        p=basis@v.co;q,j=deformation(p)
        if (p-q).length<1e-10:continue
        old=v.co.copy();v.co=inverse@q;distances.append((o.matrix_world.to_3x3()@(v.co-old)).length)
        transforms[v.index]=(ib@j@b).inverted().transposed()
        t=max(0.,min(1.,(p.z-start)/(end-start)))
        # The outlet edge and untouched body section are pinned. Relax only
        # the stretched transition skin, preserving the existing assembly seats.
        relax_weights[v.index]=math.sin(math.pi*t)**2*weight(math.hypot(p.x,p.y),.98,1.30)[0]
    if not distances:continue
    m.update()
    # Transport the actual source split normals through the same deformation.
    # Replacing them with generic smooth normals loses the original hard edges.
    mapped=[(transforms[l.vertex_index]@n).normalized() if l.vertex_index in transforms else n for l,n in zip(m.loops,normals)]
    m.normals_split_custom_set(mapped)
    group=o.vertex_groups.new(name='R21_TransitionOnly')
    for index,w in relax_weights.items():
        if w>1e-5:group.add([index],w,'REPLACE')
    modifier=o.modifiers.new('Constrained formed-skin relaxation','SMOOTH');modifier.factor=.25;modifier.iterations=12;modifier.vertex_group=group.name
    bpy.context.view_layer.objects.active=o;bpy.ops.object.modifier_apply(modifier=modifier.name);m=o.data;m.update()
    relaxed=[]
    for loop,original in zip(m.loops,mapped):
        w=relax_weights.get(loop.vertex_index,0.)
        normal=m.vertices[loop.vertex_index].normal
        relaxed.append(original.lerp(normal,w).normalized())
    m.normals_split_custom_set(relaxed)
    changes.append({'mesh':o.name,'changed_vertices':len(distances),'maximum_axial_map_world_displacement':max(distances),'source_vertex_count':len(m.vertices),'render_triangle_count':len(m.loop_triangles),'surface_relaxation':'12 passes at 0.25, pinned outlet and body boundary; no mounting-seat displacement'})
assert changes
# R3's standalone cosmetic shoulder is superseded by the extended cowl itself.
# It has no child hardware or runtime binding. A remains retained by the real
# C1 rear collar and its two metal supports, all included in the protection set.
# The attempted extra nickel sleeve is archived, not stacked into this source.
assert not shoulder.children
removed={'mesh':shoulder.name,'source_fingerprint':fingerprint(shoulder),'reason':'Obsolete standalone shape-study fairing replaced by the continuous cowl; original structural A/C1 collar and supports retained'}
bpy.data.objects.remove(shoulder,do_unlink=True)
assert all(fingerprint(bpy.data.objects[n])==v for n,v in protected.items())
bpy.ops.wm.save_as_mainfile(filepath=str(TARGET),compress=True)
bpy.ops.object.select_all(action='DESELECT')
for o in [root,*root.children_recursive]:o.select_set(True)
bpy.context.view_layer.objects.active=root
bpy.ops.export_scene.gltf(filepath=str(COMPONENT),export_format='GLB',use_selection=True,export_animations=False,export_morph=False,export_extras=True)
r={**s,'source':str(TARGET.relative_to(ROOT)),'source_sha256':sha(TARGET),'component':str(COMPONENT.relative_to(ROOT)),'component_sha256':sha(COMPONENT),'parent_source_sha256':s['source_sha256'],'cowl_finish':{'modified_meshes':[r['mesh']for r in changes],'removed_obsolete_meshes':[removed],'changes':changes,'axial_extension_world':extension*.70,'old_front_depth_mouth':start,'new_front_depth_mouth':start-extension,'fixed_end_depth_mouth':end,'radial_full_weight':.98,'radial_zero_weight':1.30,'minimum_axial_map_jacobian':1.,'normal_policy':'Source corner normals transported by inverse-transpose, then blended with relaxed surface normals within the same pinned transition region','art':'production/I_refinement/nautilus_r1/mouth_finish_r21/mouth_junction_close_open_r1.png'},'status':'independent_cowl_continuation_candidate_clearance_and_visual_review_pending','review_scope':'Only near-mouth existing cowl surfaces extend forward; the obsolete detached fairing is replaced by this continuous surface. Original mouth, axis, body core, structural collar, supports, hinges, drives and pedestal remain unchanged. New surfaces and opening envelope need actual visual/contact checks. No native App or art acceptance.'}
(OUT/'build.json').write_text(json.dumps(r,indent=2)+'\n')
(OUT/'protected_geometry.json').write_text(json.dumps({'source_sha256':r['source_sha256'],'passed':True,'protected_mesh_count':len(protected),'changes':changes},indent=2)+'\n')
print('COWL_CANDIDATE',r['source_sha256'],json.dumps(changes),flush=True)
