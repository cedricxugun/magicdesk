"""Actual new cell boundaries vs liner/rear and other cells at morph extremes."""
import bpy,json,sys
from pathlib import Path
from mathutils.bvhtree import BVHTree
R=Path(__file__).resolve().parents[2];args=sys.argv[sys.argv.index('--')+1:]if '--'in sys.argv else [];variant=args[0]if args else 'built_r1'
OUT=R/'review/I_refinement/nautilus_reset_r82/chambers_r89'/variant;s=json.loads((OUT/'build.json').read_text());bpy.ops.wm.open_mainfile(filepath=str(R/s['source']));scene=bpy.context.scene;scene.frame_set(175)
def geometry(o):
 ev=o.evaluated_get(bpy.context.evaluated_depsgraph_get());me=ev.to_mesh();me.calc_loop_triangles();vs=[ev.matrix_world@v.co for v in me.vertices];tri=[tuple(t.vertices)for t in me.loop_triangles];ev.to_mesh_clear()
 return BVHTree.FromPolygons(vs,tri,all_triangles=True),[min(v[k]for v in vs)for k in range(3)],[max(v[k]for v in vs)for k in range(3)]
def hits(a,b):
 if any(a[2][k]<b[1][k]or b[2][k]<a[1][k]for k in range(3)):return 0
 return len(a[0].overlap(b[0]))
parts=[o for o in bpy.data.objects if o.type=='MESH'and o.name.startswith('I84_Cell_')]
stock=[bpy.data.objects[n]for n in ['R82_Acoustic_Chamber_Liner','R82_Fixed_Rear_Keel']]
contacts=[]
for weight in [0.,1.,-1.]:
 for c in s['new_cells']:
  keys=bpy.data.objects[c['diaphragm']].data.shape_keys.key_blocks;keys['MusicPressure'].value=max(0.,weight);keys['MusicRebound'].value=max(0.,-weight)
 bpy.context.view_layer.update();g={o.name:geometry(o)for o in parts+stock}
 for i,a in enumerate(parts):
  for b in stock+[p for p in parts[i+1:]if p.name[9:11]!=a.name[9:11]]:
   n=hits(g[a.name],g[b.name])
   if n:contacts.append({'weight':weight,'a':a.name,'b':b.name,'triangle_pairs':n})
 print('R89_CELL_CONTACTS',weight,len(contacts),flush=True)
(OUT/'cell_contacts.json').write_text(json.dumps({'source_sha256':s['source_sha256'],'contacts':contacts,'scope':'All actual new cell parts against fixed gold liner/rear sheet and other cell groups at zero, pressure and rebound extremes. Within-cell mates excluded; cover/core checks are separate. Not continuous-time or whole assembly certification.'},indent=2)+'\n')
