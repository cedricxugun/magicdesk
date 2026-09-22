"""Bounded geometry study; not a manufactured linkage or production motion."""
import bpy,json,math,sys
from pathlib import Path
from mathutils import Vector,Quaternion
from mathutils.bvhtree import BVHTree
R=Path(__file__).resolve().parents[2];sys.path.insert(0,str(Path(__file__).parent))
from i_r82_coil_surface import CoilSurface
args=sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else []
report_arg=next((a.split('=',1)[1] for a in args if a.startswith('--report=')),None)
OUT=(R/report_arg).parent if report_arg else R/'review/I_refinement/nautilus_reset_r82/finish_r86/r2'
s=json.loads((OUT/'build.json').read_text());bpy.ops.wm.open_mainfile(filepath=str(R/s['source']));scene=bpy.context.scene
surface=CoilSurface(json.loads((R/'review/I_refinement/nautilus_reset_r82/mechanism_r9/build.json').read_text())['shape_parameters'])
p=s['panels'][1];node=bpy.data.objects[p['node']];cover=bpy.data.objects[p['mesh']];radial=surface.frame((p['ta']+p['tb'])/2)[1]
node.animation_data_clear()
excluded={'I_MoonlightStaff','I_CentralReadingLine','I_TipReadingRay_0','I_TipReadingRay_1','I_TipReadingRay_2'}
targets=[o for o in bpy.data.objects['IAM_MODULE'].children_recursive if o.type in ['MESH','CURVE'] and o.name not in excluded]
targets +=[bpy.data.objects[n] for n in ['R82_Acoustic_Chamber_Liner','R82_Fixed_Rear_Keel','I86_ReceiverCasting']]
targets +=[o for o in bpy.data.objects if o.type=='MESH' and o.name.startswith('I84_Cell_')]
targets +=[bpy.data.objects[row['mesh']] for row in s['panels'] if row['id']!=2]
def geo(o):
 ev=o.evaluated_get(bpy.context.evaluated_depsgraph_get());me=ev.to_mesh();me.calc_loop_triangles();v=[ev.matrix_world@x.co for x in me.vertices];t=[tuple(x.vertices) for x in me.loop_triangles];ev.to_mesh_clear()
 return BVHTree.FromPolygons(v,t,all_triangles=True),[min(x[k] for x in v) for k in range(3)],[max(x[k] for x in v) for k in range(3)]
def overlaps(a,b):
 if any(a[2][k]<b[1][k] or b[2][k]<a[1][k] for k in range(3)):return 0
 return len(a[0].overlap(b[0]))
def smooth(x):
 x=max(0.,min(1.,x));return x*x*x*(x*(x*6.-15.)+10.)
inward='--inward' in sys.argv
candidates=[{'translation':list(Vector((0,y,0))+radial*r),'contacts':[]} for y in ([-.06,-.14] if inward else [-.10,-.16,-.22,-.28]) for r in ([-.04,-.08,-.12] if inward else [.02,.06])]
forward='--forward' in sys.argv
if forward:candidates=[{'translation':list(Vector((0,y,0))+radial*r),'contacts':[]} for y in [-.26,-.38,-.50] for r in [-.03,.02]]
dense='--dense' in sys.argv
if dense:
 previous=json.loads((R/'review/I_refinement/nautilus_reset_r82/finish_r86/r2/panel02_route_forward.json').read_text())
 candidates=[{'translation':row['translation'],'contacts':[]} for row in previous['candidates'] if not row['contacts']]
axes='--axes' in sys.argv
if axes:
 candidates=[{'translation':p['translation'],'axis':list(Quaternion(Vector((0,1,0)),math.radians(a))@Quaternion(radial,math.radians(b))@Vector(p['axis'])),'axis_adjust_degrees':[a,b],'contacts':[]} for a in [-25.,0.,25.] for b in [-20.,0.,20.]]
axes_dense='--axes-dense' in sys.argv
if axes_dense:
 dense=True
 previous=json.loads((R/'review/I_refinement/nautilus_reset_r82/finish_r86/r3/panel02_axis_study.json').read_text())
 candidates=[{**row,'contacts':[]} for row in previous['candidates'] if not row['contacts']]
# Start at fully disengaged pose: closed seam defects are a separate repair.
phases=[i/40 for i in range(41)] if dense else [.25,.375,.5,.625,.75,.875,1.]
for phase in phases:
 scene.frame_set(round(85+90*phase));bpy.context.view_layer.update();fixed={o.name:geo(o) for o in targets}
 for row in candidates:
  node.location=Vector(p['pivot'])+Vector(row['translation'])*smooth(phase/.25);node.rotation_quaternion=Quaternion(Vector(row.get('axis',p['axis'])),p['angle']*smooth((phase-.25)/.75));bpy.context.view_layer.update();moving=geo(cover)
  for name,g in fixed.items():
   n=overlaps(moving,g)
   if n:row['contacts'].append({'phase':phase,'other':name,'triangle_pairs':n})
 print('ROUTE_PROGRESS',phase,[len(x['contacts']) for x in candidates],flush=True)
scope='41 sampled closed-to-open poses' if dense else 'Seven sampled fully-disengaged through full-45-degree poses'
(OUT/('panel02_axis_dense.json' if axes_dense else 'panel02_axis_study.json' if axes else 'panel02_route_dense.json' if dense else 'panel02_route_forward.json' if forward else 'panel02_route_inward.json' if inward else 'panel02_route_study.json')).write_text(json.dumps({'source_sha256':s['source_sha256'],'candidates':candidates,'scope':scope+' against actual core, skins, receiver, cells and other covers. Own linkage not rebuilt; no production motion claim.'},indent=2)+'\n')
