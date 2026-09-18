"""Read-only search of whole throat axial disengagement before shell peeling."""
import bpy,json,math,hashlib
from pathlib import Path
from mathutils import Vector,Matrix
from mathutils.bvhtree import BVHTree
ROOT=Path(__file__).resolve().parents[2];BASE=ROOT/'review/I_refinement/opening_r15';OUT=ROOT/'review/I_refinement/receiver_r16';OUT.mkdir(parents=True,exist_ok=True);spec=json.loads((BASE/'build.json').read_text());src=ROOT/spec['source'];assert hashlib.sha256(src.read_bytes()).hexdigest()==spec['source_sha256'];bpy.ops.wm.open_mainfile(filepath=str(src));scene=bpy.context.scene;scene.frame_set(1);bpy.context.view_layer.update();deps=bpy.context.evaluated_depsgraph_get();mouth=bpy.data.objects['IH1_Mouth'];body=bpy.data.objects['IC11_ConchBody'];rest=mouth.location.copy()
def snapshot(o):
 e=o.evaluated_get(deps);m=e.to_mesh();m.calc_loop_triangles();v=[x.co.copy() for x in m.vertices];f=[tuple(t.vertices) for t in m.loop_triangles];e.to_mesh_clear();return v,f
names=[s['mesh'] for s in spec['shells']];shells=[(bpy.data.objects[n],snapshot(bpy.data.objects[n])) for n in names]
targets=[(o,snapshot(o)) for o in mouth.children_recursive if o.type=='MESH' and any(k in o.name for k in ['Porcelain','FixedUpperNeck','AcousticThroatConnector','DarkRecessedThroat','GrilleSeatedFrame'])]
axis=(mouth.matrix_local.to_3x3()@Vector((0,0,-1))).normalized()
def sm(t):t=max(0,min(1,t));return t*t*(3-2*t)
results=[]
for stroke in [0.,.12,.20,.28,.36,.44]:
 contacts=[]
 for frame in range(1,362,12):
  scene.frame_set(frame);sec=(frame-1)/30;amount=sm((sec-.5)/3) if sec<6 else 1-sm((sec-7)/3);release=sm(amount/.20)
  mouth.location=rest+axis*stroke*release;bpy.context.view_layer.update()
  fixed_t=[(o.name,BVHTree.FromPolygons([o.matrix_world@p for p in d[0]],d[1],all_triangles=True)) for o,d in targets]
  for o,d in shells:
   t=BVHTree.FromPolygons([o.matrix_world@p for p in d[0]],d[1],all_triangles=True)
   for name,other in fixed_t:
    if t.overlap(other):contacts.append({'frame':frame,'shell':o.name,'against':name})
 results.append({'stroke':stroke,'contact_records':len(contacts),'contacts':contacts});print('MOUTH_UNSEAT',stroke,len(contacts),flush=True)
(OUT/'mouth_unseat_options.json').write_text(json.dumps({'source_sha256':spec['source_sha256'],'tested':'31 forward/reverse frame samples, porcelain shells vs named moving throat surfaces only. No whole structure/art acceptance. New throat mount and acoustic coupling required.','options':results},indent=2)+'\n')
