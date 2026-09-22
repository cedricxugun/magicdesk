"""Actual installed body/core contacts at working and pressure poses.
Coplanar carrier seats are listed separately, never a blanket body-pair exemption.
"""
import bpy,json,math,sys
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
R=Path(__file__).resolve().parents[2]
args=sys.argv[sys.argv.index('--')+1:] if '--'in sys.argv else []
report_arg=next((a.split('=',1)[1] for a in args if a.startswith('--report=')),None)
if report_arg:
 report_path=(R/report_arg).resolve();assert report_path.is_relative_to(R.resolve()) and report_path.name=='build.json'
 OUT=report_path.parent
else:
 variant=args[0] if args else 'installed_r3'
 assert variant in ['installed_r3','installed_r5']
 OUT=R/'review/I_refinement/nautilus_reset_r82/music_interface_r1'/variant
d=json.loads((OUT/'build.json').read_text());core=json.loads((R/d['core_report']).read_text())
bpy.ops.wm.open_mainfile(filepath=str(R/d['source']));scene=bpy.context.scene;scene.frame_set(1);bpy.context.view_layer.update()
root=bpy.data.objects['R82_COIL_ROOT'];module=bpy.data.objects['IAM_MODULE'];mouth=bpy.data.objects['IAM_Mouth']
exclude={'I_MoonlightStaff','I_CentralReadingLine','I_TipReadingRay_0','I_TipReadingRay_1','I_TipReadingRay_2'}
bodyparts=[o for o in root.children_recursive if o.type in ['MESH','CURVE']]
coreparts=[o for o in module.children_recursive if o.type in ['MESH','CURVE']and o.name not in exclude]
cache={}
def bbox(o):
 ev=o.evaluated_get(bpy.context.evaluated_depsgraph_get());vs=[ev.matrix_world@Vector(p)for p in ev.bound_box]
 return [min(v[k]for v in vs)for k in range(3)],[max(v[k]for v in vs)for k in range(3)]
def broad(a,b):return all(a[0][k]<=b[1][k] and b[0][k]<=a[1][k]for k in range(3))
def geometry(o):
 ev=o.evaluated_get(bpy.context.evaluated_depsgraph_get());keys=tuple(k.value for k in o.data.shape_keys.key_blocks)if o.type=='MESH' and o.data.shape_keys else ()
 signature=(o.name,tuple(v for row in ev.matrix_world for v in row),keys)
 if signature in cache:return cache[signature]
 me=ev.to_mesh();me.calc_loop_triangles();vs=[ev.matrix_world@v.co for v in me.vertices];tri=[tuple(t.vertices)for t in me.loop_triangles]
 ev.to_mesh_clear();value=(BVHTree.FromPolygons(vs,tri,all_triangles=True),vs,tri);cache[signature]=value;return value
moving=bpy.data.objects[core['diaphragm']['moving']];rest=moving.location.copy();moving.animation_data_clear()
for n in core['diaphragm']['morphs']:
 ob=bpy.data.objects[n]
 if ob.data.shape_keys.animation_data:ob.data.shape_keys.animation_data_clear()
head_rest={tip['head']:bpy.data.objects[tip['head']].matrix_basis.to_3x3().copy()for tip in core['physical_heads']}
for name in head_rest:bpy.data.objects[name].animation_data_clear()
layout=json.loads((R/'app'/core['music_optics_layout'].removeprefix('res://')).read_text())
results=[];unexpected=[];seats=[]
poses=[(1,0.),(40,0.),(78,0.),(100,0.),(145,0.),(175,0.),(205,-.006),(205,0.),(205,.006),(260,0.),(330,0.),(400,0.),(430,0.)]
for f,stroke in poses:
 scene.frame_set(f);moving.location=rest+Vector((0,0,stroke))
 for n in core['diaphragm']['morphs']:
  keys=bpy.data.objects[n].data.shape_keys.key_blocks;keys[core['diaphragm']['pressure_key']].value=max(0.,stroke/.006);keys[core['diaphragm']['rebound_key']].value=max(0.,-stroke/.006)
 bpy.context.view_layer.update();focus=mouth.matrix_world@Vector(layout['scanner']['focus'])
 for name,rest_basis in head_rest.items():
  head=bpy.data.objects[name];parent=head.parent.matrix_world.to_3x3();baseline=parent@rest_basis
  axis=(baseline@Vector((0,0,-1))).normalized();to=(focus-head.matrix_world.translation).normalized()
  head.rotation_quaternion=(parent.inverted()@axis.rotation_difference(to).to_matrix()@baseline).to_quaternion()
 bpy.context.view_layer.update();inv=mouth.matrix_world.inverted()
 bounds_b={o.name:bbox(o)for o in bodyparts};bounds_c={o.name:bbox(o)for o in coreparts}
 contacts=0
 for a in coreparts:
  for b in bodyparts:
   if not broad(bounds_c[a.name],bounds_b[b.name]):continue
   ta,va,fa=geometry(a);tb,vb,fb=geometry(b);hits=ta.overlap(tb)
   if not hits:continue
   contacts+=1;intentional=False;plane=None
   if a.name=='IAM_EyelidFixedCarrier' and (b.name in ['R82_Fixed_Rear_Keel','I86_ReceiverCasting'] or b.name.startswith('I83_HeadWasher_')):
    za=[(inv@va[i]).z for pair in hits for i in fa[pair[0]]]
    zb=[(inv@vb[i]).z for pair in hits for i in fb[pair[1]]]
    if b.name in ['R82_Fixed_Rear_Keel','I86_ReceiverCasting']:
     plane=.230;intentional=max(za)<=plane+2e-5 and min(zb)>=plane-2e-5
    else:
     plane=.214;intentional=min(za)>=plane-2e-5 and max(zb)<=plane+2e-5
   row={'frame':f,'stroke':stroke,'core':a.name,'body':b.name,'triangle_pairs':len(hits)}
   if intentional:row['mating_plane_mouth_z']=plane;seats.append(row)
   else:unexpected.append(row)
 results.append({'frame':f,'stroke':stroke,'contact_pairs':contacts});print('I83_CONTACT_POSE',f,stroke,'unexpected',len(unexpected),flush=True)
 # Bounds and evaluated curve/shape meshes are cached only for this pose family.
 if len(cache)>2500:cache.clear()
report={'source':d['source'],'source_sha256':d['source_sha256'],'scope':'13 saved-source body/throat working states and diaphragm pressure extremes, physical cartridge/projector parts vs complete upper body. Holographic surfaces excluded. Carrier seating only classified if both triangle half-spaces meet the exact .230/.214 plane. Not self-contact, all-pair mechanical certification, continuous motion or art acceptance.','body_parts':len(bodyparts),'core_parts':len(coreparts),'poses':results,'intentional_seating':seats,'unexpected':unexpected,'subset_clear':not unexpected}
(OUT/'installed_contact_check.json').write_text(json.dumps(report,indent=2)+'\n')
print('I83_INSTALLED_CONTACTS',len(unexpected),flush=True)
