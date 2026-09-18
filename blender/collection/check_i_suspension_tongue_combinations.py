"""Independent combinations of tongue opening and suspension amplitude."""
import bpy,json,hashlib
from pathlib import Path
import sys
from mathutils import Vector
from mathutils.bvhtree import BVHTree
ROOT=Path(__file__).resolve().parents[2];args=sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else [];OUT=ROOT/(args[0] if args else 'review/I_refinement/part_a_mouth/shutter_r2/diaphragm');spec=json.loads((OUT/'build.json').read_text());source=ROOT/spec['source'];assert hashlib.sha256(source.read_bytes()).hexdigest()==spec['source_sha256']
bpy.ops.wm.open_mainfile(filepath=str(source));scene=bpy.context.scene;scene.frame_set(1);moving=bpy.data.objects[spec['diaphragm']['moving']];moving.animation_data.action=None
for g in spec['tongues']:bpy.data.objects[g['drive']].animation_data_clear()
deps=bpy.context.evaluated_depsgraph_get()
def tree(o):
 e=o.evaluated_get(deps);m=e.to_mesh();m.calc_loop_triangles();t=BVHTree.FromPolygons([e.matrix_world@v.co for v in m.vertices],[tuple(t.vertices) for t in m.loop_triangles],all_triangles=True);e.to_mesh_clear();return t
names={o.name for o in moving.children_recursive if o.type=='MESH'}|set(spec['diaphragm']['morphs']);poses=[]
for stroke in [-.006,-.003,0.,.003,.006]:
 moving['stroke']=stroke;moving.update_tag();bpy.context.view_layer.update();assert abs(moving.location.z-stroke)<1e-6
 poses.append((stroke,[(name,tree(bpy.data.objects[name])) for name in names]))
contacts=[];rows=[]
for k in range(17):
 opening=k/16
 for g in spec['tongues']:
  lo,hi=g['window'];t=max(0,min(1,(opening-lo)/(hi-lo)));o=bpy.data.objects[g['drive']];o['feed']=float(t*t*(3-2*t));o.update_tag()
 bpy.context.view_layer.update();foils=[]
 for g in spec['tongues']:
  o=bpy.data.objects[g['mesh_names'][0]];actual=sum(i*key.value/256 for i,key in enumerate(o.data.shape_keys.key_blocks) if i>0);assert abs(actual-bpy.data.objects[g['drive']]['feed'])<1e-5
  foils.extend((name,tree(bpy.data.objects[name])) for name in g['mesh_names'])
 for stroke,suspension in poses:
  for name,ft in foils:
   for other,st in suspension:
    pairs=ft.overlap(st)
    if pairs:contacts.append({'opening':opening,'stroke':stroke,'foil':name,'suspension':other,'triangles':len(pairs)})
  rows.append({'opening':opening,'stroke':stroke})
 print('SUSPENSION_TONGUE_COMBINATION',opening,len(contacts),flush=True)
(OUT/'combination_check.json').write_text(json.dumps({'source_sha256':spec['source_sha256'],'passed':not contacts,'samples':rows,'contacts':contacts,'scope':'17 independently evaluated tongue openings x 5 suspension amplitudes, all six foils versus all moving/deforming suspension meshes. Driver refresh assertions included. Surface tests only; no continuous sweep, volume containment or entire disassembly coverage.'},indent=2)+'\n');print('I_SUSPENSION_COMBINATIONS',not contacts,flush=True)
