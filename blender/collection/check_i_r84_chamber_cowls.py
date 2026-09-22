"""R84 chamber/cowl contact sweep with real morph extremes. No automatic art pass."""
import bpy,json
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
R=Path(__file__).resolve().parents[2];OUT=R/'review/I_refinement/nautilus_reset_r82/chambers_r3'
d=json.loads((OUT/'build.json').read_text());bpy.ops.wm.open_mainfile(filepath=str(R/d['source']));scene=bpy.context.scene
covers=[bpy.data.objects[p['mesh']]for p in d['panels']]
cells=[o for o in bpy.data.objects if o.name.startswith('I84_Cell_')and o.type=='MESH']
def geo(o):
 ev=o.evaluated_get(bpy.context.evaluated_depsgraph_get());me=ev.to_mesh();me.calc_loop_triangles()
 vs=[ev.matrix_world@v.co for v in me.vertices];ts=[tuple(t.vertices)for t in me.loop_triangles];ev.to_mesh_clear()
 bounds=([min(v[k]for v in vs)for k in range(3)],[max(v[k]for v in vs)for k in range(3)])
 return BVHTree.FromPolygons(vs,ts,all_triangles=True),bounds
def intersects(a,b):
 if any(a[1][1][k]<b[1][0][k] or b[1][1][k]<a[1][0][k] for k in range(3)):return 0
 return len(a[0].overlap(b[0]))
contacts=[];rows=[]
for f,weight in [(1,0),(85,0),(100,0),(125,0),(145,0),(175,0),(205,-1),(205,0),(205,1),(260,0),(300,0),(350,0),(430,0)]:
 scene.frame_set(f)
 for c in d['new_cells']:
  obj=bpy.data.objects[c['diaphragm']];keys=obj.data.shape_keys.key_blocks
  keys['MusicPressure'].value=max(0,weight);keys['MusicRebound'].value=max(0,-weight)
 bpy.context.view_layer.update()
 shell={o.name:geo(o)for o in covers};hardware={o.name:geo(o)for o in cells}
 for i,a in enumerate(covers):
  for b in covers[i+1:]:
   n=intersects(shell[a.name],shell[b.name])
   if n:contacts.append({'frame':f,'weight':weight,'a':a.name,'b':b.name,'pairs':n})
  for b in cells:
   n=intersects(shell[a.name],hardware[b.name])
   if n:contacts.append({'frame':f,'weight':weight,'a':a.name,'b':b.name,'pairs':n})
 rows.append({'frame':f,'weight':weight});print('R84_CONTACT',f,weight,'contacts',len(contacts),flush=True)
(OUT/'cowl_contact_check.json').write_text(json.dumps({'source_sha256':d['source_sha256'],'poses':rows,'contacts':contacts,'subset_clear':not contacts,'scope':'Six ceramic covers against each other and new chamber meshes, 13 poses including membrane extremes. Not telescopic hardware, all internals, continuous motion or art acceptance.'},indent=2)+'\n')
print('R84_CONTACT_DONE',len(contacts),flush=True)
