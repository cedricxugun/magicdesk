"""Ray/object attribution for the visible mouth-left dark artifact.
The source is not saved or modified."""
import bpy,json,hashlib,sys
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
R=Path(__file__).resolve().parents[2]
args=sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else []
path=next((a.split('=',1)[1] for a in args if a.startswith('--report=')),None)
report=R/path if path else R/'review/I_refinement/nautilus_reset_r82/outer_hinge_r2/build.json'
OUT=report.parent if path else R/'review/I_refinement/nautilus_reset_r82/finish_r86';OUT.mkdir(exist_ok=True)
spec=json.loads(report.read_text(encoding='utf-8'))
bpy.ops.wm.open_mainfile(filepath=str(R/spec['source']));s=bpy.context.scene;s.frame_set(205);s.render.resolution_x=1000;s.render.resolution_y=1100
bpy.context.view_layer.update();cam=s.camera;frame=cam.data.view_frame(scene=s)
xmin=min(p.x for p in frame);xmax=max(p.x for p in frame);ymin=min(p.y for p in frame);ymax=max(p.y for p in frame)
direction=cam.matrix_world.to_quaternion()@Vector((0,0,-1))
objects=[]
for o in s.objects:
 if o.type not in ['MESH','CURVE']or o.hide_render or 'Ground'in o.name:continue
 ev=o.evaluated_get(bpy.context.evaluated_depsgraph_get());me=ev.to_mesh();me.calc_loop_triangles()
 verts=[ev.matrix_world@v.co for v in me.vertices];tri=[tuple(t.vertices)for t in me.loop_triangles]
 objects.append((o,BVHTree.FromPolygons(verts,tri,all_triangles=True),verts,tri));ev.to_mesh_clear()
results=[];target=None
for x,y in [(327,578),(330,588),(337,572),(345,577),(360,548),(313,598),(311,614),(319,627)]:
 origin=cam.matrix_world@Vector((xmin+(x+.5)/1000*(xmax-xmin),ymax-(y+.5)/1100*(ymax-ymin),0))
 hits=[]
 for o,tree,verts,tri in objects:
  point,normal,index,distance=tree.ray_cast(origin,direction,30)
  if point is not None:hits.append({'name':o.name,'distance':distance,'point':list(point),'triangle':index,'triangle_points':[list(verts[j])for j in tri[index]],'materials':[m.name if m else None for m in o.data.materials]})
 hits.sort(key=lambda h:h['distance']);results.append({'pixel':[x,y],'hits':hits[:8]})
 physical=[h for h in hits if h['name']not in ['I_MoonlightStaff','I_CentralReadingLine','I_TipReadingRay_0','I_TipReadingRay_1','I_TipReadingRay_2']]
 print('PIXEL',x,y,[(h['name'],round(h['distance'],5))for h in hits[:4]],flush=True)
 if target is None and physical:target=Vector(physical[0]['point'])
(OUT/'dark_face_attribution.json').write_text(json.dumps({'source_sha256':spec['source_sha256'],'samples':results},indent=2)+'\n')
if target:
 cam.location=target-direction*5;cam.data.ortho_scale=.72;s.render.resolution_x=1000;s.render.resolution_y=1000
 try:
  p=bpy.context.preferences.addons['cycles'].preferences;p.compute_device_type='CUDA';p.get_devices()
  for d in p.devices:d.use=d.type=='CUDA'
  s.cycles.device='GPU'
 except:pass
 s.cycles.samples=48;s.render.filepath=str(OUT/'mouth_left_macro.png');bpy.ops.render.render(write_still=True)
