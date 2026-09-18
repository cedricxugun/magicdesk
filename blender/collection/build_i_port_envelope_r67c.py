"""Single connected annular liner; measured exterior and monotone bore topology."""
import bpy,bmesh,json,hashlib,math,array
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
ROOT=Path(__file__).resolve().parents[2];OUT=ROOT/'review/I_refinement/nautilus_r1/port_envelope_r67/smooth_r3';OUT.mkdir(parents=True,exist_ok=True)
s=json.loads((ROOT/'review/I_refinement/nautilus_r1/port_rebuild_r66/build.json').read_text());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();assert sha(ROOT/s['source'])==s['source_sha256'];bpy.ops.wm.open_mainfile(filepath=str(ROOT/s['source']));bpy.context.scene.frame_set(1);bpy.context.view_layer.update()
o=bpy.data.objects['IS18_Leg01_PortLiner'];frame=bpy.data.objects['IS18_Leg01_PortFrame'];F=frame.matrix_world.copy();inv=F.inverted();axis=F.to_3x3().col[2].normalized()
def fingerprint(obj):
    m=obj.data;m.calc_loop_triangles();h=hashlib.sha256()
    for c,p,w,k in [(m.vertices,'co',3,'f'),(m.loop_triangles,'vertices',3,'I'),(m.corner_normals,'vector',3,'f')]:
        a=array.array(k,[0])*(len(c)*w);c.foreach_get(p,a);h.update(a.tobytes())
    for uv in m.uv_layers:
        a=array.array('f',[0])*(len(uv.data)*2);uv.data.foreach_get('uv',a);h.update(a.tobytes())
    if m.shape_keys:
        for key in m.shape_keys.key_blocks:
            a=array.array('f',[0])*(len(key.data)*3);key.data.foreach_get('co',a);h.update(key.name.encode());h.update(a.tobytes())
    return h.hexdigest(),[list(r)for r in obj.matrix_world],[x.name if x else None for x in m.materials],[f.material_index for f in m.polygons]
protected={x.name:fingerprint(x)for x in bpy.data.objects if x.type=='MESH'and x!=o}
def geometry(obj):
    m=obj.data;m.calc_loop_triangles();v=[obj.matrix_world@x.co for x in m.vertices];t=[tuple(f.vertices)for f in m.loop_triangles];return BVHTree.FromPolygons(v,t,all_triangles=True),v,t
solution=json.loads((OUT/'height_solution.json').read_text());M=o.matrix_world.copy()
points=[Vector(p)for p in solution['vertices']];old=o.data;old.calc_loop_triangles()
faces=[tuple(t.vertices)for t in old.loop_triangles if set(i//192 for i in t.vertices)!={4,5}]
for i in range(192):
    p=points[4*192+i].copy();p.z=points[5*192+i].z;points.append(p)
for first,second in [(4,21),(21,5)]:
    for i in range(192):
        a=first*192+i;b=first*192+(i+1)%192;c=second*192+(i+1)%192;d=second*192+i
        faces.extend([(a,b,c),(a,c,d)])
mesh=bpy.data.meshes.new('R67c_ConnectedFlange');mesh.from_pydata([M.inverted()@F@p for p in points],[],faces);mesh.update()
for material in old.materials:mesh.materials.append(material)
o.data=mesh
for face in mesh.polygons:face.use_smooth=True
bm=bmesh.new();bm.from_mesh(o.data);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));assert all(e.is_manifold for e in bm.edges)and all(v.is_manifold for v in bm.verts);volume=bm.calc_volume(signed=True);bm.to_mesh(o.data);bm.free();o.data.update()
tree,v,t=geometry(o);contacts=[(a,b)for a,b in tree.overlap(tree)if a<b and not set(t[a])&set(t[b])]
obstacles=[bpy.data.objects[n]for n in ['IN1_PorcelainPanel_01','IN1_PorcelainPanel_02','IS18_Leg01_PortSeal']if n in bpy.data.objects]
checks=[]
for obstacle in obstacles:
    other,_,_=geometry(obstacle)
    for step in ([0] if obstacle.name=='IS18_Leg01_PortSeal' else range(45)):
        offset=axis*(step*.005);moved=BVHTree.FromPolygons([p+offset for p in v],t,all_triangles=True);hits=moved.overlap(other)
        if hits:checks.append({'obstacle':obstacle.name,'distance':step*.005,'contacts':len(hits)})
probe={k:value for k,value in solution.items()if k!='vertices'};probe.update(parent_source_sha256=s['source_sha256'],volume=volume,self_contacts=len(contacts),self_pairs=contacts[:20],clearance_contacts=checks)
(OUT/'build_check.json').write_text(json.dumps(probe,indent=2)+'\n');print('R67_CHECK',json.dumps(probe),flush=True)
assert volume>0 and not contacts and not checks
assert all(fingerprint(bpy.data.objects[n])==p for n,p in protected.items())
source=ROOT/'blender/collection/I_nautilus_port_envelope_r67c.blend';component=ROOT/'app/assets/collection/components/I_nautilus_port_envelope_r67c.glb';assert not source.exists();bpy.ops.wm.save_as_mainfile(filepath=str(source),compress=True)
body=bpy.data.objects['IN1_BodyRoot'];bpy.ops.object.select_all(action='DESELECT')
for x in [body,*body.children_recursive]:x.select_set(True)
bpy.context.view_layer.objects.active=body;bpy.ops.export_scene.gltf(filepath=str(component),export_format='GLB',use_selection=True,export_animations=False,export_morph=True,export_morph_normal=True,export_extras=True)
ART=ROOT/'app/assets/collection/art/I/port_envelope_r67c';ART.mkdir(parents=True,exist_ok=True);layout=json.loads((ROOT/s['chamber_response_layout'].replace('res://','app/')).read_text());layout.update(source_sha256=sha(source),component_sha256=sha(component));(ART/'chamber_layout.json').write_text(json.dumps(layout,indent=2)+'\n')
d={**s,'source':str(source.relative_to(ROOT)),'source_sha256':sha(source),'component':str(component.relative_to(ROOT)),'component_sha256':sha(component),'chamber_response_layout':'res://assets/collection/art/I/port_envelope_r67c/chamber_layout.json','port_envelope':probe,'status':'envelope_port_liner_candidate'};(OUT/'build.json').write_text(json.dumps(d,indent=2)+'\n')
