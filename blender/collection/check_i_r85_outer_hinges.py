"""Check actual R85 outer hinge parts and chambers against every moving cover."""
import bpy,json,sys
from pathlib import Path
from mathutils.bvhtree import BVHTree
R=Path(__file__).resolve().parents[2]
args=sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else []
report_arg=next((a.split('=',1)[1] for a in args if a.startswith('--report=')),None)
if report_arg:
 report_path=(R/report_arg).resolve();assert report_path.is_relative_to(R.resolve()) and report_path.name=='build.json'
 OUT=report_path.parent
else:
 variant=args[0] if args else 'outer_hinge_r1'
 assert variant in ['outer_hinge_r1','outer_hinge_r2']
 OUT=R/'review/I_refinement/nautilus_reset_r82'/variant
s=json.loads((OUT/'build.json').read_text());bpy.ops.wm.open_mainfile(filepath=str(R/s['source']));scene=bpy.context.scene
covers=[bpy.data.objects[p['mesh']]for p in s['panels']]
parts=[o for o in bpy.data.objects if o.type=='MESH'and o.name.startswith(('I85_','I84_Cell_','I88_','I90_'))]
finish_only='--finish-only' in args
include_finish='--include-finish' in args
if finish_only or include_finish:
 finish_parts=[bpy.data.objects[n] for n in ['R82_Acoustic_Chamber_Liner','R82_Fixed_Rear_Keel','I86_ReceiverCasting']]
 parts=finish_parts if finish_only else parts+finish_parts
def geo(o):
 ev=o.evaluated_get(bpy.context.evaluated_depsgraph_get());me=ev.to_mesh();me.calc_loop_triangles();vs=[ev.matrix_world@v.co for v in me.vertices];ts=[tuple(t.vertices)for t in me.loop_triangles];ev.to_mesh_clear()
 return BVHTree.FromPolygons(vs,ts,all_triangles=True),[min(v[k]for v in vs)for k in range(3)],[max(v[k]for v in vs)for k in range(3)]
def hit(a,b):
 if any(a[2][k]<b[1][k]or b[2][k]<a[1][k]for k in range(3)):return 0
 return len(a[0].overlap(b[0]))
contacts=[]
DENSE='--dense' in args
poses=[(f,0.)for f in ([1]+list(range(85,176,2))+list(range(234,325,2))+[350,430] if DENSE else [1,85,95,108,125,145,175,205,250,285,315,350,430])]
if DENSE:poses +=[(175,-1.),(175,1.)]
for f,weight in poses:
 scene.frame_set(f)
 for c in s['new_cells']:
  keys=bpy.data.objects[c['diaphragm']].data.shape_keys.key_blocks
  keys['MusicPressure'].value=max(0,weight);keys['MusicRebound'].value=max(0,-weight)
 bpy.context.view_layer.update();geometry={o.name:geo(o)for o in covers+parts}
 for i,a in enumerate(covers):
  for b in covers[i+1:]+parts:
   n=hit(geometry[a.name],geometry[b.name])
   if n:contacts.append({'frame':f,'weight':weight,'a':a.name,'b':b.name,'pairs':n})
 print('R85_CONTACT',f,len(contacts),flush=True)
name=('finish_' if finish_only else '')+('contact_check_dense.json' if DENSE else 'contact_check.json')
scope='Saved-source poses: cover/cover and cover/reconstructed liner, rear skin and independent receiver casting.' if finish_only else 'Saved-source poses: cover/cover, cover/new chambers and new outer-hinge parts. Dense mode also checks membrane extremes.'
if include_finish:scope+=' Also cover/reconstructed liner, rear skin and receiver casting.'
(OUT/name).write_text(json.dumps({'source_sha256':s['source_sha256'],'poses':poses,'contacts':contacts,'scope':scope+' Does not prove fixed-stock seating, all-pair/self contact or continuous motion.'},indent=2)+'\n')
print('R85_CONTACT_DONE',len(contacts),flush=True)
