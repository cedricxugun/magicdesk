"""Scoped actual network fit: retain only the authored liner/backbone bond."""
import bpy,json,sys
from pathlib import Path
from mathutils.bvhtree import BVHTree
R=Path(__file__).resolve().parents[2];args=sys.argv[sys.argv.index('--')+1:]if '--'in sys.argv else [];variant=args[0]if args else 'built_r2';OUT=R/'review/I_refinement/nautilus_reset_r82/network_r90'/variant
s=json.loads((OUT/'build.json').read_text());bpy.ops.wm.open_mainfile(filepath=str(R/s['source']));scene=bpy.context.scene;scene.frame_set(175);bpy.context.view_layer.update()
def geo(o):
 ev=o.evaluated_get(bpy.context.evaluated_depsgraph_get());me=ev.to_mesh();me.calc_loop_triangles();v=[ev.matrix_world@x.co for x in me.vertices];f=[tuple(t.vertices)for t in me.loop_triangles];ev.to_mesh_clear();return BVHTree.FromPolygons(v,f,all_triangles=True),[min(x[k]for x in v)for k in range(3)],[max(x[k]for x in v)for k in range(3)]
def hit(a,b):
 if any(a[2][k]<b[1][k]or b[2][k]<a[1][k]for k in range(3)):return 0
 return len(a[0].overlap(b[0]))
root=bpy.data.objects['R82_COIL_ROOT'];new=[o for o in root.children_recursive if o.type=='MESH'and o.name.startswith('I90_')]
moving=set()
for p,j in zip(s['panels'],s['joints']):
 for node in [bpy.data.objects[p['node']],bpy.data.objects[j['carriage']]]:moving.add(node);moving.update(node.children_recursive)
old=[o for o in root.children_recursive if o.type in ['MESH','CURVE']and o not in new and o not in moving]
new_geo={o.name:geo(o)for o in new};contacts=[]
for weight in [0.,1.,-1.]:
 for c in s['new_cells']:
  keys=bpy.data.objects[c['diaphragm']].data.shape_keys.key_blocks;keys['MusicPressure'].value=max(0.,weight);keys['MusicRebound'].value=max(0.,-weight)
 bpy.context.view_layer.update();old_geo={o.name:geo(o)for o in old}
 for a in new:
  for b in old:
   if a.name==s['network']['backbone'] and b.name=='R82_Acoustic_Chamber_Liner':continue
   count=hit(new_geo[a.name],old_geo[b.name])
   if count:contacts.append({'weight':weight,'new':a.name,'old':b.name,'triangle_pairs':count})
 print('R90_FIT',weight,len(contacts),flush=True)
glass_contacts=[];glass_hardware_contacts=[];backbone=new_geo[s['network']['backbone']]
for row in s['network']['segments']:
 count=hit(new_geo[row['mesh']],backbone)
 if count:glass_contacts.append({'glass':row['mesh'],'backbone':s['network']['backbone'],'triangle_pairs':count})
 for part in new:
  if not part.name.startswith(('I90_JunctionCap_','I90_JunctionSeal_','I90_FeedPin_','I90_FeedCollar_')):continue
  count=hit(new_geo[row['mesh']],new_geo[part.name])
  if count:glass_hardware_contacts.append({'glass':row['mesh'],'hardware':part.name,'triangle_pairs':count})
(OUT/'network_contacts.json').write_text(json.dumps({'source_sha256':s['source_sha256'],'contacts':contacts,'glass_channel_contacts':glass_contacts,'glass_hardware_contacts':glass_hardware_contacts,'scope':'New network meshes against old fixed body/cell meshes at three membrane extremes; optical solids also against casing and mechanical caps/seals/pins/collars. Only the designed shallow integral liner/backbone bond omitted. Covers and music-core checked separately; remaining new-new junction seats are not certified here.'},indent=2)+'\n')
print('R90_NETWORK_CONTACTS',len(contacts),len(glass_contacts),flush=True)
