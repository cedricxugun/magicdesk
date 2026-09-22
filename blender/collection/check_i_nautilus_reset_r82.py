"""Independent saved-source witnesses for the R82 form study, not final QA."""
import bpy,bmesh,json,math,hashlib
from pathlib import Path
from mathutils.bvhtree import BVHTree
R=Path(__file__).resolve().parents[2]
OUT=R/'review/I_refinement/nautilus_reset_r82/form_r2'
d=json.loads((OUT/'build.json').read_text())
bpy.ops.wm.open_mainfile(filepath=str(R/d['source']))
scene=bpy.context.scene
def triangles(o):
 ev=o.evaluated_get(bpy.context.evaluated_depsgraph_get());me=ev.to_mesh();me.calc_loop_triangles()
 vs=[o.matrix_world@v.co for v in me.vertices]
 ts=[tuple(t.vertices)for t in me.loop_triangles]
 ev.to_mesh_clear();return vs,ts
def bvh(o):
 vs,ts=triangles(o);return BVHTree.FromPolygons(vs,ts,all_triangles=True,epsilon=0)
panels=[bpy.data.objects[p['mesh']]for p in d['panels']]
rows=[]
for p in d['panels']:
 obj=bpy.data.objects[p['node']];mesh=bpy.data.objects[p['mesh']]
 scene.frame_set(1);m0=obj.matrix_world.copy()
 scene.frame_set(145);m1=obj.matrix_world.copy()
 scene.frame_set(300);m2=obj.matrix_world.copy()
 bm=bmesh.new();bm.from_mesh(mesh.data)
 rows.append({'id':p['id'],'translation':(m1.translation-m0.translation).length,
 'rotation_degrees':math.degrees(m0.to_quaternion().rotation_difference(m1.to_quaternion()).angle),
 'return_matrix_error':max(abs(m2[i][j]-m0[i][j])for i in range(4)for j in range(4)),
 'non_manifold_edges':sum(not e.is_manifold for e in bm.edges),
 'degenerate_faces':sum(f.calc_area()<1e-12 for f in bm.faces),
 'faces':len(bm.faces)})
 bm.free()
# Only ceramic against each other and the saddle, not every manufacturing contact.
fixed=[o for o in bpy.data.objects if o.name.startswith(('R82_Sculpted_Saddle','R82_Trunnion','R82_Base_Locating','R82_Keel_Lower'))]
contacts=[]
for f in [1,36,55,75,95,115,145,200,240,275,300]:
 scene.frame_set(f);trees={o.name:bvh(o)for o in panels+fixed}
 for i,a in enumerate(panels):
  for b in panels[i+1:]+fixed:
   hits=trees[a.name].overlap(trees[b.name])
   if hits:contacts.append({'frame':f,'a':a.name,'b':b.name,'triangle_pairs':len(hits)})
scene.frame_set(1)
report={'source':d['source'],'sha256':hashlib.sha256((R/d['source']).read_bytes()).hexdigest(),
 'scope':'Six saved panel transforms + raw closed manifold topology; finite ceramic/saddle and ceramic/ceramic triangle surface intersections only. No continuous collision or assembly certification.',
 'panels':rows,'all_six_move':all(r['translation']>.01 and r['rotation_degrees']>1 for r in rows),
 'all_return':all(r['return_matrix_error']<1e-6 for r in rows),
 'contacts':contacts,'full_art_or_runtime_pass':False}
(OUT/'motion_check.json').write_text(json.dumps(report,indent=2))
print(json.dumps(report),flush=True)
