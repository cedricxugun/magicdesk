"""Keep the visible R10 hub registration; machine nesting and fit its backing to the core."""
import bpy,bmesh,json,hashlib,sys,shutil,struct,math
from pathlib import Path
from mathutils import Vector,Matrix
from mathutils.bvhtree import BVHTree
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(Path(__file__).parent))
import i_fitted_surface as fitted
import i_machined_geometry as h
OUT=ROOT/'review/I_refinement/nautilus_r1/throat_chambers_r11';OUT.mkdir(parents=True,exist_ok=True)
TARGET=ROOT/'blender/collection/I_nautilus_hub_backing_r11.blend'
COMPONENT=ROOT/'app/assets/collection/components/I_nautilus_hub_backing_r11.glb'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
seed=json.loads((ROOT/'review/I_refinement/nautilus_r1/chamber_seats_r10/build.json').read_text())
assert sha(ROOT/seed['source'])==seed['source_sha256']=='24fb44f53582cc1599fa99d43663187824c37bc97581ec83cc81bb9015e604c3'
if TARGET.exists():
    old=json.loads((OUT/'build.json').read_text());assert sha(TARGET)==old['source_sha256'],'Unrecorded R11 edits'
    archive=OUT/'iterations'/old['source_sha256'][:12];archive.mkdir(parents=True,exist_ok=True)
    for p in OUT.glob('*.json'):shutil.copy2(p,archive/p.name)
    if (OUT/'views').exists():shutil.copytree(OUT/'views',archive/'views',dirs_exist_ok=True)
    (TARGET.parent/'checkpoints'/('I-hub-backing-'+old['source_sha256'][:12]+'.blend')).write_bytes(TARGET.read_bytes())
bpy.ops.wm.open_mainfile(filepath=str(ROOT/seed['source']));scene=bpy.context.scene;scene.frame_set(1);bpy.context.view_layer.update()
body=bpy.data.objects['IN1_BodyRoot'];core=bpy.data.objects['IN3_ContinuousThroat']
hub_names=['IN1_SpiralHubFront','IN1_HubCeramicFront','IN1_HubRingFront','IN1_HubRecessFront','IN1_HubInsetFront']
hubs=[bpy.data.objects[n] for n in hub_names];edited=[core]+hubs[:-1]
def fingerprint(o):
    d=hashlib.sha256()
    for v in o.data.vertices:d.update(struct.pack('<3f',*v.co))
    for f in o.data.polygons:d.update(struct.pack('<'+'I'*len(f.vertices),*f.vertices))
    return [d.hexdigest(),[list(r) for r in o.matrix_world],o.parent.name if o.parent else None,[m.name if m else None for m in o.data.materials]]
protected={o.name:fingerprint(o) for o in bpy.data.objects if o.type=='MESH' and o not in edited}
hub_transforms={o.name:[list(r) for r in o.matrix_world] for o in hubs}
for o in edited:
    assert not o.modifiers
    old=o.data;old.calc_loop_triangles();triangles=list(old.loop_triangles)
    m=bpy.data.meshes.new(o.name+'_R11Machining');m.from_pydata([tuple(v.co) for v in old.vertices],[],[tuple(t.vertices) for t in triangles]);m.update()
    for material in old.materials:m.materials.append(material)
    for p,t in zip(m.polygons,triangles):p.material_index=old.polygons[t.polygon_index].material_index;p.use_smooth=old.polygons[t.polygon_index].use_smooth
    for layer in old.uv_layers:
        uv=m.uv_layers.new(name=layer.name)
        for i,t in enumerate(triangles):
            for j,loop in enumerate(t.loops):uv.data[i*3+j].uv=layer.data[loop].uv
    m.normals_split_custom_set([old.corner_normals[i].vector.copy() for t in triangles for i in t.loops]);o.data=m
col=bpy.data.collections.new('I_HUB_BACKING_R11');scene.collection.children.link(col);h.configure(col)
root=h.empty('IH11_HubMount',body)
hub_points=[hubs[0].matrix_world@v.co for v in hubs[0].data.vertices]
center=Vector((.12,max(p.y for p in hub_points),1.96))
matrix=Matrix(((1,0,0,center.x),(0,0,-1,center.y),(0,1,0,center.z),(0,0,0,1)))
root.matrix_world=matrix;bpy.context.view_layer.update();inverse=matrix.inverted()
def tree(o):
    bpy.context.view_layer.update();o.data.calc_loop_triangles()
    return BVHTree.FromPolygons([inverse@o.matrix_world@v.co for v in o.data.vertices],[tuple(t.vertices) for t in o.data.loop_triangles],all_triangles=True)
def crossings(bvh,x,y):
    start=Vector((x,y,1));hits=[]
    for _ in range(8):
        hit=bvh.ray_cast(start,Vector((0,0,-1)),3)
        if hit[0] is None:break
        hits.append(float(hit[0].z));start=hit[0]+Vector((0,0,-.00001))
    return hits
outline=[(.164*math.cos(i*math.tau/96),.164*math.sin(i*math.tau/96)) for i in range(96)]
patch=fitted.clipped_surface([core],outline,frame=matrix,from_positive=True,normal_limit=.15)
vs,fs=fitted.extruded_patch(*patch,top_offset=.0002,bottom_z=-.0002)
m=bpy.data.meshes.new('IH11_FittedHubBackingMesh');m.from_pydata(vs,[],fs);m.update()
adapter=bpy.data.objects.new('IH11_FittedHubBacking',m);col.objects.link(adapter);h.finish(adapter,adapter.name,root,(0,0,0),'A_Satin')
bm=bmesh.new();bm.from_mesh(adapter.data)
if bm.calc_volume(signed=True)<0:bmesh.ops.reverse_faces(bm,faces=list(bm.faces));bm.to_mesh(adapter.data)
assert not any(not e.is_manifold for e in bm.edges);bm.free()
core_tree=tree(core);anchors=[];fasteners=[];nests=[]
def bolt(name,x,y,seat_z,bottom):
    washer=h.sleeve(name+'_Washer',.0055,.00255,.0012,root,(x,y,seat_z+.0007),'A_Bronze')
    head_z=seat_z+.0034
    shank=h.cylinder(name,.0022,head_z-bottom,root,(x,y,(head_z+bottom)/2),'A_Nickel',bevel=.0001)
    head=h.screw(name+'_Head',root,(x,y,head_z),.0048)
    bpy.context.view_layer.update();bpy.context.view_layer.objects.active=shank
    mod=shank.modifiers.new('One-piece tie bolt','BOOLEAN');mod.operation='UNION';mod.solver='EXACT';mod.object=head;bpy.ops.object.modifier_apply(modifier=mod.name)
    h.parts.remove(head.name);bpy.data.objects.remove(head,do_unlink=True)
    return {'mesh':shank.name,'washer':washer.name,'xy':[x,y],'shaft_bottom_z':bottom,'seat_z':seat_z}
for i in range(4):
    angle=i*math.tau/4;x=.10*math.cos(angle);y=.10*math.sin(angle)
    hits=crossings(core_tree,x,y);assert len(hits)>=2
    outer,inner=hits[:2];wall=outer-inner;depth=min(.016,.60*wall)
    assert depth>.008 and outer<-.012,(i,hits)
    seat_z=-.008
    h.drill(adapter,.0062,.040,root,(x,y,seat_z+.020),solver='MANIFOLD')
    bottom=outer-.004;top=.010
    h.drill(adapter,.00245,top-bottom,root,(x,y,(top+bottom)/2),solver='MANIFOLD')
    h.drill(core,.00245,depth+.002,root,(x,y,outer+(.002-depth)/2))
    anchors.append({**bolt('IH11_CoreAnchor_%02d'%i,x,y,seat_z,outer-depth+.001),'target':core.name,'outer_z':outer,'inner_z':inner,'blind_depth':depth,'expected_floor_z':outer-depth})
for parent,child in zip(hubs[:-1],hubs[1:]):
    points=[inverse@child.matrix_world@v.co for v in child.data.vertices]
    radius=max(math.hypot(p.x,p.y) for p in points);rear=min(p.z for p in points)
    floor=rear-.0002;top=.20
    h.drill(parent,radius+.0003,top-floor,root,(0,0,(top+floor)/2))
    nests.append({'parent':parent.name,'child':child.name,'child_radius':radius,'cavity_radius':radius+.0003,'child_rear_z':rear,'cavity_floor_z':floor})
adapter_tree=tree(adapter)
for i in range(4):
    angle=(i+.5)*math.tau/4;x=.154*math.cos(angle);y=.154*math.sin(angle)
    hits=crossings(adapter_tree,x,y);assert len(hits)==2,(i,hits)
    outer,inner=hits;depth=min(.012,.55*(outer-inner));assert depth>.006
    seat_z=.064
    h.drill(hubs[0],.0062,.05,root,(x,y,seat_z+.025))
    h.drill(hubs[0],.00245,.090,root,(x,y,.04))
    h.drill(adapter,.00245,depth+.002,root,(x,y,outer+(.002-depth)/2),solver='MANIFOLD')
    fasteners.append({**bolt('IH11_HubRetainer_%02d'%i,x,y,seat_z,outer-depth+.001),'target':adapter.name,'outer_z':outer,'inner_z':inner,'blind_depth':depth,'expected_floor_z':outer-depth})
cleanup=[]
for o in edited+[bpy.data.objects[n] for n in h.parts]:
    bm=bmesh.new();bm.from_mesh(o.data);bmesh.ops.remove_doubles(bm,verts=list(bm.verts),dist=1e-6);bmesh.ops.dissolve_degenerate(bm,edges=list(bm.edges),dist=3e-6)
    flaps=[f for f in bm.faces if f.calc_area()<1e-10 and any(len(e.link_faces)>2 for e in f.edges)]
    if flaps:bmesh.ops.delete(bm,geom=flaps,context='FACES_ONLY')
    bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces))
    if bm.calc_volume(signed=True)<0:bmesh.ops.reverse_faces(bm,faces=list(bm.faces))
    cleanup.append({'name':o.name,'nonmanifold':sum(not e.is_manifold for e in bm.edges),'volume':bm.calc_volume(signed=True)})
    bm.to_mesh(o.data);bm.free()
bpy.context.view_layer.update()
changed=[n for n,value in protected.items() if fingerprint(bpy.data.objects[n])!=value];assert not changed,changed
assert hub_transforms=={o.name:[list(r) for r in o.matrix_world] for o in hubs}
bpy.ops.wm.save_as_mainfile(filepath=str(TARGET),compress=True);bpy.ops.object.select_all(action='DESELECT')
for o in [body,*body.children_recursive]:o.select_set(True)
bpy.context.view_layer.objects.active=body
bpy.ops.export_scene.gltf(filepath=str(COMPONENT),export_format='GLB',use_selection=True,export_animations=False,export_morph=False,export_extras=True)
result={**seed,'source':str(TARGET.relative_to(ROOT)),'source_sha256':sha(TARGET),'component':str(COMPONENT.relative_to(ROOT)),'component_sha256':sha(COMPONENT),'parent_source_sha256':seed['source_sha256'],'status':'hub_backing_candidate_checks_pending','hub_backing':{'frame':root.name,'matrix_blender':[list(r) for r in matrix],'adapter':adapter.name,'new_meshes':list(h.parts),'modified_meshes':[o.name for o in edited],'core_anchors':anchors,'hub_fasteners':fasteners,'nests':nests,'cleanup':cleanup},'review_scope':'R10 silhouette, mouth, visible hub placement, chamber seats and common base preserved. Source-fitted backing, blind anchored screws and nested recesses built; contacts, throat-side end sockets, border capture, base load path, cover mechanisms, full music and native/art acceptance pending.'}
(OUT/'build.json').write_text(json.dumps(result,indent=2)+'\n')
(OUT/'protected_geometry.json').write_text(json.dumps({'source_sha256':result['source_sha256'],'passed':not changed,'count':len(protected),'changed':changed,'hub_transforms_unchanged':True},indent=2)+'\n')
print('HUB_BACKING_BUILT',json.dumps(result['hub_backing']),flush=True)
