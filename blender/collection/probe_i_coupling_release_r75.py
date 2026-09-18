"""Read-only panel02 release after the currently checked support/port poses."""
import bpy,json,hashlib,collections,math
from pathlib import Path
from mathutils import Vector,Quaternion
from mathutils.bvhtree import BVHTree
ROOT=Path(__file__).resolve().parents[2];OUT=ROOT/'review/I_refinement/nautilus_r1/coupling_release_r75';OUT.mkdir(parents=True,exist_ok=True)
s=json.loads((ROOT/'review/I_refinement/nautilus_r1/coupling_threads_r75/build.json').read_text());plan=json.loads((ROOT/'review/I_refinement/nautilus_r1/port_edge_r68/release_probe/probe.json').read_text());assert plan['source_sha256']==s['seam_fasteners']['parent_source_sha256'];assert hashlib.sha256((ROOT/s['source']).read_bytes()).hexdigest()==s['source_sha256'];bpy.ops.wm.open_mainfile(filepath=str(ROOT/s['source']));bpy.context.scene.frame_set(1)
for row in s['form_panels']:
 o=bpy.data.objects[row['node']];o.animation_data_clear();o.location=Vector(row['pivot_blender'])+Vector(row['lift_blender']);o.rotation_quaternion=Quaternion(Vector(row['axis_blender']),row['angle'])
 if 'mechanism'in row:
  m=row['mechanism']
  for k in ['carriage','rotor']:bpy.data.objects[m[k]].animation_data_clear()
  bpy.data.objects[m['carriage']].location=(0,0,m['stroke']);bpy.data.objects[m['rotor']].rotation_quaternion=Quaternion(Vector(m['axis_local_blender']),row['angle'])
bpy.context.view_layer.update();body=bpy.data.objects['IN1_BodyRoot'];mouth=bpy.data.objects['IAM_MODULE'];parts=list(dict.fromkeys(o for r in [body,mouth]for o in r.children_recursive if o.type=='MESH'))
orig=set(bpy.data.objects);bpy.ops.import_scene.gltf(filepath=str(ROOT/'app/assets/helios_model.glb'));base=next(o for o in bpy.data.objects if o not in orig and o.name.split('.')[0]=='BASE_FIXED');base_parts=[o for o in [base,*base.children_recursive]if o.type=='MESH']
offsets={o.name:Vector((0,0,.45))if o.name not in plan['fixed_adapter_names']else Vector()for o in parts}
for row in plan['groups']+plan['legs']+plan['ports']:
 for name in row['names']:offsets[name]+=Vector(row['offset'])
homes={o.name:o.matrix_world.copy()for o in parts}
def depth(o):
 n=0
 while o.parent:n+=1;o=o.parent
 return n
for o in sorted(parts,key=depth):
 pose=homes[o.name].copy();pose.translation+=offsets[o.name];o.matrix_world=pose
bpy.context.view_layer.update()
front=json.loads((ROOT/'review/I_refinement/nautilus_r1/service_r63/stage03_wide/plan.json').read_text());rear=json.loads((ROOT/'review/I_refinement/nautilus_r1/rear03_release_r70/two_stage_r5/probe.json').read_text());assert rear['source_sha256']==s['seam_fasteners']['parent_source_sha256']and all(not x['contacts']for x in rear['samples'])
previous_homes={o.name:o.matrix_world.copy()for o in parts};extra={}
for row in front['groups']:
 if row['id']not in ['cover_03','pin_cap_03','pin_03']:continue
 for name in row['meshes']:extra[name]=Vector(row['offset_blender'])
for row in rear['groups']:
 d=Vector(row['normal'])*(.810 if row['id'].startswith('rear_bolt')else .8)if row['id']!='rear_shell03'else Vector(rear['shell_waypoints'][2])
 for name in row['names']:assert name not in extra;extra[name]=d
for o in sorted([bpy.data.objects[n]for n in extra],key=depth):
 pose=previous_homes[o.name].copy();pose.translation+=extra[o.name];o.matrix_world=pose
bpy.context.view_layer.update()
pose_error=max(abs(o.matrix_world[i][j]-(previous_homes[o.name][i][j]+(extra[o.name][i]if j==3 and i<3 else 0.)))for o in [bpy.data.objects[n]for n in extra]for i in range(4)for j in range(4));assert pose_error<1e-6
def geo(objects):
 v=[];f=[];owners=[];dg=bpy.context.evaluated_depsgraph_get()
 for o in objects:
  e=o.evaluated_get(dg);m=e.to_mesh();m.calc_loop_triangles();n=len(v);v.extend(e.matrix_world@x.co for x in m.vertices);f.extend(tuple(n+i for i in t.vertices)for t in m.loop_triangles);owners.extend([o.name]*len(m.loop_triangles));e.to_mesh_clear()
 return v,f,owners
mount=bpy.data.objects['IC1_MouthMount'];axis=mount.matrix_world.to_3x3().col[2].normalized();released={n for g in plan['groups']for n in g['names']}
assembly=[o for o in parts if (o.name.startswith('IAM_')or o.name.startswith(('IC1_','IC73_')))and o.name not in released]
assert bpy.data.objects['IC1_CollarUpper']in assembly and bpy.data.objects['IC1_CollarLower']in assembly and bpy.data.objects['IAM_RearMountFlange_0074']in assembly
bolts=[bpy.data.objects[n]for i in range(6)for n in ['IN3_CouplingBolt_%02d'%i,'IN3_CouplingBolt_%02d_Washer'%i]]
claimed=set(assembly+bolts);fixed=[o for o in parts+base_parts if o not in claimed];fv,ff,fn=geo(fixed);ft=BVHTree.FromPolygons(fv,ff,all_triangles=True);av,af,an=geo(assembly);bv,bf,bn=geo(bolts)
bolt_groups=[]
for i,row in enumerate(s['coupling_threads']['threads']):
 shaft=bpy.data.objects[row['bolt']];washer=bpy.data.objects[row['bolt']+'_Washer'];sv,sf,sn=geo([shaft]);wv,wf,wn=geo([washer]);center=mount.matrix_world@Vector(row['center_parent'])+Vector((0,0,.45));bolt_groups.append({'row':row,'shaft':(sv,sf,sn),'washer':(wv,wf,wn),'center':center})
axis_scale=mount.matrix_world.to_3x3().col[2].length
rows=[]
for phase in ['loosen','extract']:
 for fraction in [i/40 for i in range(41)]:
  distance=.006*(fraction if phase=='loosen'else 1.);d=axis*distance;ad=-axis*.8*fraction if phase=='extract'else Vector();at=BVHTree.FromPolygons([p+ad for p in av],af,all_triangles=True)
  vertices=[];faces=[];names=[]
  for g in bolt_groups:
   rotation=Quaternion(axis,math.tau*(distance/axis_scale)/g['row']['pitch_parent'])
   for kind in ['shaft','washer']:
    v,f,n=g[kind];start=len(vertices);vertices.extend(g['center']+rotation@(p-g['center'])+d if kind=='shaft'else p+d for p in v);faces.extend(tuple(start+i for i in tri)for tri in f);names.extend(n)
  bt=BVHTree.FromPolygons(vertices,faces,all_triangles=True);bn=names;contacts=[]
  for label,t,owners,other,on in [('mouth_collar / fixed',at,an,ft,fn),('bolts / fixed',bt,bn,ft,fn),('mouth_collar / bolts',at,an,bt,bn)]:
   hits=t.overlap(other)
   if hits:contacts.append({'pair':label,'count':len(hits),'owners':dict(collections.Counter(owners[a]+' / '+on[b]for a,b in hits))})
  rows.append({'phase':phase,'fraction':fraction,'contacts':contacts});print('MOUTH_CASSETTE',phase,fraction,[(c['pair'],c['count'])for c in contacts],flush=True)
result={'source_sha256':s['source_sha256'],'assembly_members':[o.name for o in assembly],'bolt_members':[o.name for o in bolts],'coupling_withdrawal':.006,'mouth_offset':list(-axis*.8),'samples':rows,'scope':'Authored short-thread geometry and helical release route check: intact A with both collar halves/seam hardware/bushes, six coupling bolts/washer sets moved .006 before withdrawal. Actual six screws rotate by the local modeled pitch with world/mount scale conversion; independent thread-disengagement witness still required. Finite source poses, not continuous collision, load/torque, animation or art acceptance.'};(OUT/'probe.json').write_text(json.dumps(result,indent=2)+'\n')
