"""Independent ship against the actual sampled loaded-record machine pose."""
import bpy,json,hashlib,math,sys
from pathlib import Path
from mathutils import Matrix,Vector,Quaternion
from mathutils.bvhtree import BVHTree
ROOT=Path(__file__).resolve().parents[2]
revision='r3' if '--r3' in sys.argv else 'r2'
model=ROOT/'app/assets/collection/models/G_optical_curator';data=json.loads(model.with_suffix('.json').read_text())
main_hash=hashlib.sha256(model.with_suffix('.glb').read_bytes()).hexdigest()
choices=[('ship_r3','ship'),('butterfly_r2','butterfly')]
for folder,label in choices:
    record=ROOT/('review/G_optical_curator/'+folder+'/full_take/curator_take.json')
    if not record.exists():continue
    take=json.loads(record.read_text())
    if take['model_sha256']==main_hash:
        candidate=model.parent/('G_optical_curator_'+label+'_candidate.json')
        assert hashlib.sha256(candidate.read_bytes()).hexdigest()==take['metadata_sha256']
        break
else:raise AssertionError('No recorded take matches current main model')
original=json.loads(candidate.read_text());normalized=dict(data)
for key in ['source_blend','development_status']:normalized[key]=original[key]
assert normalized==original, 'Recorded poses require runtime-equivalent current metadata'
bpy.ops.wm.open_mainfile(filepath=str(ROOT/'blender/collection/G_optical_curator.blend'))
C=Matrix(((1,0,0,0),(0,0,1,0),(0,-1,0,0),(0,0,0,1)));CI=C.inverted()
def pose(p):return CI@Matrix.LocRotScale(Vector(p['p']),Quaternion((p['q'][3],*p['q'][:3])),Vector(p['s']))@C
for obj in bpy.data.objects:obj.animation_data_clear()
sample=next(s for s in take['samples'] if s['state']['stage']=='playing' and s['state']['loaded_index']==2)
for name,p in sample['poses'].items():
    if name in bpy.data.objects:bpy.data.objects[name].matrix_basis=pose(p)
old=bpy.data.objects[data['g_archive']['contents'][2]['root']]
for obj in list(old.children_recursive)+[old]:bpy.data.objects.remove(obj,do_unlink=True)
component=ROOT/('app/assets/collection/components/G_ship_'+revision+'.glb')
entry=json.loads(component.with_suffix('.json').read_text())
component_source=ROOT/('blender/collection/G_ship_'+revision+'.blend')
with bpy.data.libraries.load(str(component_source),link=False) as (src,dst):
    dst.objects=[n for n in src.objects if n.startswith(('GS2_','GS3_')) and 'ReferenceOriginalDisc' not in n]
for obj in dst.objects:
    if obj: bpy.context.scene.collection.objects.link(obj)
content=bpy.data.objects[entry['root']]
print_root=bpy.data.objects[data['record_player']['print_root']];content.parent=print_root
content.matrix_basis=Matrix.Identity(4)
parts={p['name'] for p in data['parts']};excluded={c['root'] for c in data['g_archive']['contents']}|{content.name}
def members(root,prune=False):
    result=[]
    def walk(node):
        if prune and node!=root and (node.name in parts or node.name in excluded):return
        if node.type in ['MESH','CURVE','FONT']:result.append(node)
        for child in node.children:walk(child)
    walk(root);return result
def mesh_tree(objects):
    deps=bpy.context.evaluated_depsgraph_get();vertices=[];faces=[]
    for obj in objects:
        ev=obj.evaluated_get(deps);mesh=ev.to_mesh();mesh.calc_loop_triangles();start=len(vertices)
        vertices.extend(ev.matrix_world@v.co for v in mesh.vertices);faces.extend(tuple(start+i for i in t.vertices) for t in mesh.loop_triangles);ev.to_mesh_clear()
    return BVHTree.FromPolygons(vertices,faces,all_triangles=True),[min(v[k] for v in vertices) for k in range(3)],[max(v[k] for v in vertices) for k in range(3)]
record=bpy.data.objects[data['record_player']['records'][2]];bpy.context.view_layer.update();tree,_,_=mesh_tree(members(record))
heights=[]
for r in [0,.006,.010,.012,.016,.020,.024,.026,.028,.030,.032,.034,.036,.038,.040,.060,.080,.092,.100,.120]:
    samples=[]
    for k in range(16):
        a=k*math.tau/16;point=print_root.matrix_world@Vector((r*math.cos(a),r*math.sin(a),2))
        location,_,_,_=tree.ray_cast(point,Vector((0,0,-1)))
        if location is not None:samples.append((print_root.matrix_world.inverted()@location).z)
    heights.append({'radius':r,'max_height':max(samples) if samples else None})
out=ROOT/('review/G_optical_curator/ship_'+revision)
(out/'record_height_probe.json').write_text(json.dumps(heights,indent=2)+'\n');print('SHIP_RECORD_HEIGHTS',heights,flush=True)
if '--mount-probe' in sys.argv:raise SystemExit(0)
mount=float(entry['mount_offset_z']);content.location.z=mount
groups={name:members(bpy.data.objects[name],True) for name in parts};groups={n:v for n,v in groups.items() if v}
platter=bpy.data.objects[data['record_player']['platter']];platter_home=platter.matrix_basis.copy();record_home=record.matrix_basis.copy()
hits=[];cache={};count=0
for frame in [1,91,181,241,331,451]:
    bpy.context.scene.frame_set(frame)
    for i in range(24):
        angle=i*math.tau/24;platter.matrix_basis=platter_home@Matrix.Rotation(angle,4,'Z');record.matrix_basis=record_home@Matrix.Rotation(angle,4,'Z');bpy.context.view_layer.update()
        a,lo,hi=mesh_tree(members(content));count+=1
        for name,objects in groups.items():
            signature=tuple(tuple(x for row in o.matrix_world for x in row) for o in objects)
            if name not in cache or cache[name][0]!=signature:cache[name]=(signature,mesh_tree(objects))
            b,low,high=cache[name][1]
            if any(hi[k]<low[k] or high[k]<lo[k] for k in range(3)):continue
            overlap=a.overlap(b)
            if overlap:hits.append({'source_frame':frame,'platter_angle':angle,'other':name,'triangle_pairs':len(overlap)})
report={'passed':not hits,'samples':count,'mount_offset_z':mount,'collisions':hits,'component_sha256':hashlib.sha256(component.read_bytes()).hexdigest(),'main_model_sha256':take['model_sha256'],'main_metadata_sha256':hashlib.sha256(model.with_suffix('.json').read_bytes()).hexdigest(),'recorded_metadata_sha256':take['metadata_sha256'],'source_sha256':hashlib.sha256(component_source.read_bytes()).hexdigest(),'scope':'6 authored source poses x 24 platter angles against actual loaded-record player geometry. Not runtime animation equivalence or all transfer stages.'}
(out/'player_clearance.json').write_text(json.dumps(report,indent=2)+'\n');print('SHIP_PLAYER_CLEARANCE',json.dumps(report),flush=True)
raise SystemExit(0 if report['passed'] else 2)
