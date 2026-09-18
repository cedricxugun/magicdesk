"""Single connected annular liner; measured exterior and monotone bore topology."""
import bpy,bmesh,json,hashlib,math,array
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
ROOT=Path(__file__).resolve().parents[2];OUT=ROOT/'review/I_refinement/nautilus_r1/port_rebuild_r66';OUT.mkdir(parents=True,exist_ok=True)
s=json.loads((ROOT/'review/I_refinement/nautilus_r1/curved_returns_r61/build.json').read_text());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();assert sha(ROOT/s['source'])==s['source_sha256'];bpy.ops.wm.open_mainfile(filepath=str(ROOT/s['source']));bpy.context.scene.frame_set(1);bpy.context.view_layer.update()
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
old_tree,_,_=geometry(o);skins=[geometry(bpy.data.objects[n])[0]for n in ['IN1_PorcelainPanel_01','IN1_PorcelainPanel_02']]
def hit_z(tree,r,a):
    origin=F@Vector((r*math.cos(a),r*math.sin(a),.4));hit,normal,_,_=tree.ray_cast(origin,-axis,.5)
    if hit is None:return None
    return (inv@hit).z
edge_extrapolations=[]
def front(r,a):
    if r>.0406:
        inner=min(r-2e-5,.0408);origin=F@Vector((inner*math.cos(a),inner*math.sin(a),.4));hit,normal,_,_=old_tree.ray_cast(origin,-axis,.5)
        assert hit is not None
        local=inv@hit;n=F.to_3x3().transposed()@normal;assert abs(n.z)>.1
        z=local.z-(n.x*(r*math.cos(a)-local.x)+n.y*(r*math.sin(a)-local.y))/n.z
        edge_extrapolations.append({'radius':r,'angle':a,'radial_extrapolation':r-inner});return z
    z=hit_z(old_tree,r,a)
    if z is None:
        z=hit_z(old_tree,r-2e-7,a)
    assert z is not None,(r,a)
    return z
constraints=[]
def back(r,a):
    top=front(r,a);values=[z for tree in skins if (z:=hit_z(tree,r,a))is not None]
    z=max([top-.0038]+[x+.0004 for x in values])
    if top-z<.0008:constraints.append({'radius':r,'angle':a,'old_front':top,'skin_depths':values,'required_front_for_thickness':z+.0038})
    return z
N=192;angles=[i*math.tau/N for i in range(N)];port=s['metal_supports']['ports'][0];start,end=port['axial_limits'];radii=[.0345,.035,.0365,.038,.039,.0405]
outer=lambda a:.041*math.cos(math.pi/64)/math.cos(a%(math.tau/64)-math.pi/64)
rings=[]
def ring(radius,height):rings.append([Vector(((r:=radius(a)if callable(radius)else radius)*math.cos(a),r*math.sin(a),height(r,a)if callable(height)else height))for a in angles])
ring(.0295,start);ring(.0295,end-.008);ring(.0306,end-.008);ring(.0306,end);ring(.0336,end)
for r in radii:ring(r,front)
ring(outer,front);ring(outer,back)
for r in reversed(radii):ring(r,back)
ring(.0336,lambda r,a:back(.0345,a));ring(.0336,start)
(OUT/'surface_constraints.json').write_text(json.dumps({'violations':constraints},indent=2)+'\n');assert not constraints,'Old front surface cannot provide a sound wall over actual skins; inspect surface_constraints.json'
points=[p for row in rings for p in row];faces=[];front_faces=set()
for j in range(len(rings)):
    for i in range(N):
        a=j*N+i;b=j*N+(i+1)%N;c=((j+1)%len(rings))*N+(i+1)%N;d=((j+1)%len(rings))*N+i
        # The front/back height fields must share the same XY diagonal.
        # Independent quad triangulation can cross steep but separated layers.
        if 4<=j<=10:front_faces.update([len(faces),len(faces)+1])
        faces.extend([(a,b,d),(b,c,d)]if 12<=j<=18 else [(a,b,c),(a,c,d)])
M=o.matrix_world.copy();materials=list(o.data.materials);mesh=bpy.data.meshes.new('IS18_PortLiner01_ContinuousMesh');mesh.from_pydata([M.inverted()@F@p for p in points],[],faces);mesh.update()
for mat in materials:mesh.materials.append(mat)
bm=bmesh.new();bm.from_mesh(mesh);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));assert all(e.is_manifold for e in bm.edges)and all(v.is_manifold for v in bm.verts);volume=bm.calc_volume(signed=True)
if volume<0:bmesh.ops.reverse_faces(bm,faces=list(bm.faces));volume=-volume
bm.to_mesh(mesh);bm.free();mesh.update();o.data=mesh
for face in mesh.polygons:face.use_smooth=True
tree,v,t=geometry(o);contacts=[(a,b)for a,b in tree.overlap(tree)if a<b and not set(t[a])&set(t[b])]
front_tree=BVHTree.FromPolygons(v,[tuple(tr.vertices)for tr in mesh.loop_triangles if tr.polygon_index in front_faces],all_triangles=True)
visible=[];surface_distances=[]
for r in [.0345,.0365,.039,.0405]:
    for i in range(96):
        a=i*math.tau/96;before=hit_z(old_tree,r,a);after=hit_z(tree,r,a);assert after is not None;visible.append(abs(after-before))
        old_point=old_tree.ray_cast(F@Vector((r*math.cos(a),r*math.sin(a),.4)),-axis,.5)[0]
        surface_distances.append(front_tree.find_nearest(old_point)[3])
probe={'source_sha256':s['source_sha256'],'target':o.name,'vertices':len(v),'triangles':len(t),'volume':volume,'self_contacts':len(contacts),'self_pairs':contacts[:20],'outer_face_samples':len(visible),'maximum_outer_axial_change':max(visible),'scope':'Direct annular topology, original axis/bore/counterbore and sampled exterior. Inner shoulder/return rebuilt; not yet full clearance or visual acceptance.'}
probe['outer_edge_extrapolation_max']=max(x['radial_extrapolation']for x in edge_extrapolations)
probe['maximum_corresponding_front_surface_distance']=max(surface_distances)
(OUT/'build_check.json').write_text(json.dumps(probe,indent=2)+'\n');print('R66_LINER',probe,flush=True)
assert not contacts and volume>0 and max(surface_distances)<5e-7
assert all(fingerprint(bpy.data.objects[n])==p for n,p in protected.items())
source=ROOT/'blender/collection/I_nautilus_port_rebuild_r66.blend';component=ROOT/'app/assets/collection/components/I_nautilus_port_rebuild_r66.glb';assert not source.exists();bpy.ops.wm.save_as_mainfile(filepath=str(source),compress=True)
body=bpy.data.objects['IN1_BodyRoot'];bpy.ops.object.select_all(action='DESELECT')
for x in [body,*body.children_recursive]:x.select_set(True)
bpy.context.view_layer.objects.active=body;bpy.ops.export_scene.gltf(filepath=str(component),export_format='GLB',use_selection=True,export_animations=False,export_morph=True,export_morph_normal=True,export_extras=True)
ART=ROOT/'app/assets/collection/art/I/port_rebuild_r66';ART.mkdir(parents=True,exist_ok=True);layout=json.loads((ROOT/s['chamber_response_layout'].replace('res://','app/')).read_text());layout.update(source_sha256=sha(source),component_sha256=sha(component));(ART/'chamber_layout.json').write_text(json.dumps(layout,indent=2)+'\n')
d={**s,'source':str(source.relative_to(ROOT)),'source_sha256':sha(source),'component':str(component.relative_to(ROOT)),'component_sha256':sha(component),'chamber_response_layout':'res://assets/collection/art/I/port_rebuild_r66/chamber_layout.json','port_rebuild':probe,'status':'direct_port_liner_candidate'};(OUT/'build.json').write_text(json.dumps(d,indent=2)+'\n')
