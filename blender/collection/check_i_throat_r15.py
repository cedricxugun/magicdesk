import bpy,bmesh,json,hashlib
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
ROOT=Path(__file__).resolve().parents[2];OUT=ROOT/'review/I_refinement/opening_r15';spec=json.loads((OUT/'build.json').read_text());source=ROOT/spec['source'];assert hashlib.sha256(source.read_bytes()).hexdigest()==spec['source_sha256'];bpy.ops.wm.open_mainfile(filepath=str(source));scene=bpy.context.scene;scene.frame_set(1);bpy.context.view_layer.update();deps=bpy.context.evaluated_depsgraph_get();mouth=bpy.data.objects['IH1_Mouth']
def local_points(o):return [mouth.matrix_world.inverted()@(o.matrix_world@v.co) for v in o.data.vertices]
stem=bpy.data.objects[spec['hub_shaft']];hub=next(o for o in bpy.data.objects if o.name.startswith('IC11_ResonatorHub'));membrane=next(o for o in bpy.data.objects if 'DiaphragmEnvelope' in o.name and o.name.startswith('IO15'))
a=local_points(stem);b=local_points(hub);d=local_points(membrane);gap=abs(min(v.z for v in a)-max(v.z for v in b))
rows=[]
for name in ['IC11_RolledThroatPorcelain_Upper',spec['fixed_upper_neck']]:
 obj=bpy.data.objects[name];bm=bmesh.new();bm.from_mesh(obj.data);rows.append({'name':name,'nonmanifold_edges':sum(not e.is_manifold for e in bm.edges),'signed_volume':bm.calc_volume(signed=True)});bm.free()
def tree(o):
 e=o.evaluated_get(deps);m=e.to_mesh();m.calc_loop_triangles();v=[o.matrix_world@x.co for x in m.vertices];f=[tuple(x.vertices) for x in m.loop_triangles];e.to_mesh_clear();return BVHTree.FromPolygons(v,f,all_triangles=True)
fixed=[(o.name,tree(o)) for o in [stem,hub]];hits=[]
for frame in range(1,362,4):
 scene.frame_set(frame);bpy.context.view_layer.update()
 for row in spec['leaves']:
  for obj in bpy.data.objects[row['name']].children:
   if obj.type!='MESH':continue
   t=tree(obj)
   for name,other in fixed:
    if t.overlap(other):hits.append({'frame':frame,'leaf':obj.name,'against':name})
# Dense check of the actual metal-ring disengagement, including subframes near first/last release.
hood=bpy.data.objects['IC11_RolledThroatPorcelain_Upper'];metal=next(o for o in bpy.data.objects if o.name.startswith('IC11_ThinMouthMachinedLip'));scene.frame_set(1);bpy.context.view_layer.update();metal_tree=tree(metal)
e=hood.evaluated_get(deps);m=e.to_mesh();m.calc_loop_triangles();hv=[v.co.copy() for v in m.vertices];hf=[tuple(t.vertices) for t in m.loop_triangles];e.to_mesh_clear();hood_hits=[]
frames=set(float(x) for x in range(1,362))
for lo,hi in [(16,50),(282,316)]:frames.update(lo+j/4 for j in range((hi-lo)*4+1))
for time in sorted(frames):
 frame=int(time);scene.frame_set(frame,subframe=time-frame);bpy.context.view_layer.update();t=BVHTree.FromPolygons([hood.matrix_world@p for p in hv],hf,all_triangles=True)
 if t.overlap(metal_tree):hood_hits.append(time)
result={'source_sha256':spec['source_sha256'],'hub_to_shaft_end_gap_local':gap,'shaft_reaches_membrane_volume':max(v.z for v in a)>=min(v.z for v in d),'split_parts':rows,'iris_shaft_contacts':hits,'hood_metal_sample_count':len(frames),'hood_metal_contacts':hood_hits,'passed':gap<1e-6 and not hits and not hood_hits and all(r['nonmanifold_edges']==0 and r['signed_volume']>0 for r in rows),'scope':'Hub/shaft end coincidence, diaphragm reach and sampled iris vs shaft/hub surfaces; split front-hood/fixed-neck topology. Not whole-machine clearance, fastener manufacture or art acceptance.'}
(OUT/'throat_check.json').write_text(json.dumps(result,indent=2)+'\n');print(result,flush=True)
