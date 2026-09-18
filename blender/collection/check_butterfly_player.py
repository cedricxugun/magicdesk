"""Independent butterfly against the actual sampled loaded-record machine pose."""
import bpy,json,hashlib,math,sys
from pathlib import Path
from mathutils import Matrix,Vector,Quaternion
from mathutils.bvhtree import BVHTree
ROOT=Path(__file__).resolve().parents[2]
model=ROOT/'app/assets/collection/models/G_optical_curator';data=json.loads(model.with_suffix('.json').read_text())
take=json.loads((ROOT/'review/G_optical_curator/curator_take.json').read_text())
for ext,key in [('glb','model_sha256'),('json','metadata_sha256')]:assert hashlib.sha256(model.with_suffix('.'+ext).read_bytes()).hexdigest()==take[key]
bpy.ops.wm.open_mainfile(filepath=str(ROOT/'blender/collection/G_optical_curator.blend'))
C=Matrix(((1,0,0,0),(0,0,1,0),(0,-1,0,0),(0,0,0,1)));CI=C.inverted()
def pose(p):return CI@Matrix.LocRotScale(Vector(p['p']),Quaternion((p['q'][3],*p['q'][:3])),Vector(p['s']))@C
for obj in bpy.data.objects:obj.animation_data_clear()
sample=next(s for s in take['samples'] if s['state']['stage']=='playing' and s['state']['loaded_index']==1)
for name,p in sample['poses'].items():
    if name in bpy.data.objects:bpy.data.objects[name].matrix_basis=pose(p)
old=bpy.data.objects[data['g_archive']['contents'][1]['root']]
for obj in list(old.children_recursive)+[old]:bpy.data.objects.remove(obj,do_unlink=True)
component=ROOT/'app/assets/collection/components/G_butterfly_r2.glb';entry=json.loads(component.with_suffix('.json').read_text())
bpy.ops.import_scene.gltf(filepath=str(component));content=bpy.data.objects[entry['root']]
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
record=bpy.data.objects[data['record_player']['records'][1]];bpy.context.view_layer.update();tree,_,_=mesh_tree(members(record))
heights=[]
for r in [0,.006,.010,.012,.016,.020,.024,.026,.028,.030,.032,.034,.036,.038,.040,.060,.080,.092,.100,.120]:
    samples=[]
    for k in range(16):
        a=k*math.tau/16;point=print_root.matrix_world@Vector((r*math.cos(a),r*math.sin(a),2))
        location,_,_,_=tree.ray_cast(point,Vector((0,0,-1)))
        if location is not None:samples.append((print_root.matrix_world.inverted()@location).z)
    heights.append({'radius':r,'max_height':max(samples) if samples else None})
out=ROOT/'review/G_optical_curator/butterfly_r2'
(out/'record_height_probe.json').write_text(json.dumps(heights,indent=2)+'\n');print('BUTTERFLY_RECORD_HEIGHTS',heights,flush=True)
if '--mount-probe' in sys.argv:raise SystemExit(0)
mount=float(entry['mount_offset_z']);content.location.z=mount
groups={name:members(bpy.data.objects[name],True) for name in parts};groups={n:v for n,v in groups.items() if v}
platter=bpy.data.objects[data['record_player']['platter']];platter_home=platter.matrix_basis.copy();record_home=record.matrix_basis.copy()
A=Vector(entry['drive']['a']);crank=entry['drive']['crank_length'];rod=entry['drive']['rod_length'];horn=entry['drive']['horn_radius']
def set_wings(theta):
    for r in entry['rig']:
        angle=theta if r['upper'] else min(1.20,theta+.06)
        B=Vector((horn*math.cos(angle),-horn*math.sin(angle),0));D=B-A;d=D.length;phi=math.atan2(D.y,D.x)+math.acos((d*d+crank*crank-rod*rod)/(2*d*crank));point=A+Vector((crank*math.cos(phi),crank*math.sin(phi),0))
        B.x*=r['side'];point.x*=r['side'];wing=bpy.data.objects[r['wing']];input=bpy.data.objects[r['crank']];link=bpy.data.objects[r['rod']]
        wing.rotation_mode='XYZ';wing.rotation_euler=(0,0,-r['side']*angle);input.rotation_mode='XYZ';input.rotation_euler=(0,0,r['side']*phi)
        link.location=Vector(r['center'])+Vector((0,0,r['link_height']))+point;axis=(B-point).normalized();up=Vector((0,0,1));link.rotation_mode='QUATERNION';link.rotation_quaternion=Matrix((up.cross(axis),up,axis)).transposed().to_quaternion()
hits=[];cache={};count=0
for theta in [.04,.30,.60,.90,1.18]:
    set_wings(theta)
    for i in range(24):
        angle=i*math.tau/24;platter.matrix_basis=platter_home@Matrix.Rotation(angle,4,'Z');record.matrix_basis=record_home@Matrix.Rotation(angle,4,'Z');bpy.context.view_layer.update()
        a,lo,hi=mesh_tree(members(content));count+=1
        for name,objects in groups.items():
            signature=tuple(tuple(x for row in o.matrix_world for x in row) for o in objects)
            if name not in cache or cache[name][0]!=signature:cache[name]=(signature,mesh_tree(objects))
            b,low,high=cache[name][1]
            if any(hi[k]<low[k] or high[k]<lo[k] for k in range(3)):continue
            overlap=a.overlap(b)
            if overlap:hits.append({'wing_angle':theta,'platter_angle':angle,'other':name,'triangle_pairs':len(overlap)})
report={'passed':not hits,'samples':count,'mount_offset_z':mount,'collisions':hits,'component_sha256':hashlib.sha256(component.read_bytes()).hexdigest(),'main_model_sha256':take['model_sha256'],'main_metadata_sha256':take['metadata_sha256'],'scope':'5 wing poses x 24 platter angles against actual loaded-record player geometry. Not runtime animation equivalence or all transfer stages.'}
(out/'player_clearance.json').write_text(json.dumps(report,indent=2)+'\n');print('BUTTERFLY_PLAYER_CLEARANCE',json.dumps(report),flush=True)
raise SystemExit(0 if report['passed'] else 2)
