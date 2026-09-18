"""Read-only panel02 release after the currently checked support/port poses."""
import bpy,json,hashlib,collections,math
from pathlib import Path
from mathutils import Vector,Quaternion,Matrix
from mathutils.bvhtree import BVHTree
ROOT=Path(__file__).resolve().parents[2];OUT=ROOT/'review/I_refinement/nautilus_r1/clamp_release_r73';OUT.mkdir(parents=True,exist_ok=True)
s=json.loads((ROOT/'review/I_refinement/nautilus_r1/seam_release_r73/build.json').read_text());plan=json.loads((ROOT/'review/I_refinement/nautilus_r1/port_edge_r68/release_probe/probe.json').read_text());assert plan['source_sha256']==s['seam_fasteners']['parent_source_sha256'];assert hashlib.sha256((ROOT/s['source']).read_bytes()).hexdigest()==s['source_sha256'];bpy.ops.wm.open_mainfile(filepath=str(ROOT/s['source']));bpy.context.scene.frame_set(1)
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
mount=bpy.data.objects['IC1_MouthMount'];axis=mount.matrix_world.to_3x3().col[1].normalized();depth_axis=mount.matrix_world.to_3x3().col[2].normalized();lift=Vector((0,0,.45))
groups=[]
for sign in [-1,1]:
 groups.append({'id':'socket_'+str(sign),'names':['IC73_SeamSocket_'+str(sign)],'cap_side':-1 if sign<0 else 1,'center':list(mount.matrix_world@Vector((sign*.601,0,.590))+lift)})
groups.extend([{'id':'right_stud','names':['IC1_SeamCrossBolt_1']},{'id':'upper_coupling','names':[name for i in range(3)for name in ['IN3_CouplingBolt_%02d'%i,'IN3_CouplingBolt_%02d_Washer'%i]]},{'id':'upper_collar','names':['IC1_CollarUpper','IC1_SeamCrossBolt_-1','IC1_SeamWasher_-1_1','IC1_SeamWasher_1_1']}])
claimed={n for g in groups for n in g['names']};assert len(claimed)==sum(len(g['names'])for g in groups)
fixed=[o for o in parts+base_parts if o.name not in claimed];fv,ff,fn=geo(fixed);ft=BVHTree.FromPolygons(fv,ff,all_triangles=True)
for g in groups:g['geo']=geo([bpy.data.objects[n]for n in g['names']])
def moved(g,phase,u,axial_only=False):
 v,f,n=g['geo'];d=Vector();rotation=None;center=Vector()
 if g['id'].startswith('socket_'):
  distance=g['cap_side']*.014*(u if phase==0 else 1.);d=axis*distance;rotation=Quaternion(axis,0. if axial_only else math.tau*distance/.001);center=Vector(g['center'])
  if g['id']=='socket_1'and phase==3:d+=axis*.18*u
 elif g['id']=='right_stud':d=-axis*.069*(u if phase==1 else 1. if phase>1 else 0.)
 elif g['id']=='upper_coupling':d=depth_axis*.012*(u if phase==2 else 1. if phase>2 else 0.)
 elif g['id']=='upper_collar':d=axis*.18*u if phase==3 else Vector()
 return [center+rotation@(p-center)+d if rotation is not None else p+d for p in v],f,n
samples=[]
for phase in range(4):
 for u in [0.,.0125,.025,.05,.075,.1,.15,.2,.3,.4,.5,.65,.8,1.]:
  rows=[];trees=[]
  for g in groups:
   v,f,n=moved(g,phase,u);tree=BVHTree.FromPolygons(v,f,all_triangles=True);hits=tree.overlap(ft)
   if hits:rows.append({'pair':g['id']+' / fixed','count':len(hits),'owners':dict(collections.Counter(n[a]+' / '+fn[b]for a,b in hits))})
   trees.append((g,tree,n))
  for i,(g,tree,n)in enumerate(trees):
   for other,ot,on in trees[i+1:]:
    hits=tree.overlap(ot)
    if hits:rows.append({'pair':g['id']+' / '+other['id'],'count':len(hits),'owners':dict(collections.Counter(n[a]+' / '+on[b]for a,b in hits))})
  samples.append({'phase':phase,'fraction':u,'contacts':rows});print('CLAMP_RELEASE',phase,u,[(r['pair'],r['count'])for r in rows],flush=True)
# Independent interlocking witness: a quarter pitch without the required twist
# must strike the real thread, while the matched helical motion must be clear.
interlock=[]
for g in groups[:2]:
 pin=bpy.data.objects['IC1_SeamCrossBolt_'+g['id'].split('_')[-1]];pv,pf,pn=geo([pin]);pt=BVHTree.FromPolygons(pv,pf,all_triangles=True)
 counts=[]
 for axial in [False,True]:
  v,f,n=moved(g,0,.00025/.014,axial);counts.append(len(BVHTree.FromPolygons(v,f,all_triangles=True).overlap(pt)))
 interlock.append({'socket':g['names'][0],'helical_contacts':counts[0],'axial_only_contacts':counts[1]})
for g in groups:g.pop('geo')
result={'source_sha256':s['source_sha256'],'groups':groups,'axis_world':list(axis),'depth_axis_world':list(depth_axis),'thread_interlock':interlock,'samples':samples,'scope':'Measured mixed-side sockets with matching helix, short right-stud withdrawal, upper coupling withdrawal and upper half-ring release after earlier prepared service stages. All fixed and intergroup contacts retained; no continuous/path, torque, full service or art acceptance.'};(OUT/'probe.json').write_text(json.dumps(result,indent=2)+'\n');print('THREAD_INTERLOCK',interlock)
