"""Read-only panel02 release after the currently checked support/port poses."""
import bpy,json,hashlib,collections,sys
from pathlib import Path
from mathutils import Vector,Quaternion
from mathutils.bvhtree import BVHTree
ROOT=Path(__file__).resolve().parents[2];OUT=ROOT/'review/I_refinement/nautilus_r1/rear03_release_r70';OUT.mkdir(parents=True,exist_ok=True)
partial='--partial-bolts'in sys.argv
if partial:OUT=OUT/('two_stage_r5'if '--two-step'in sys.argv else 'route_r4'if '--wide-search'in sys.argv else 'partial_bolts_r3');OUT.mkdir(parents=True,exist_ok=True)
s=json.loads((ROOT/'review/I_refinement/nautilus_r1/port_edge_r68/build.json').read_text());plan=json.loads((ROOT/'review/I_refinement/nautilus_r1/port_edge_r68/release_probe/probe.json').read_text());assert plan['source_sha256']==s['source_sha256'];assert hashlib.sha256((ROOT/s['source']).read_bytes()).hexdigest()==s['source_sha256'];bpy.ops.wm.open_mainfile(filepath=str(ROOT/s['source']));bpy.context.scene.frame_set(1)
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
front=json.loads((ROOT/'review/I_refinement/nautilus_r1/service_r63/stage03_wide/plan.json').read_text())
front_names=set();front_homes={o.name:o.matrix_world.copy()for o in parts};front_deltas={}
for row in front['groups']:
 if row['id']not in ['cover_03','pin_cap_03','pin_03']:continue
 for name in row['meshes']:front_names.add(name);front_deltas[name]=Vector(row['offset_blender'])
for o in sorted([bpy.data.objects[n]for n in front_names],key=depth):
 pose=front_homes[o.name].copy();pose.translation+=front_deltas[o.name];o.matrix_world=pose
bpy.context.view_layer.update()
front_pose_error=max(abs(o.matrix_world[i][j]-(front_homes[o.name][i][j]+(front_deltas[o.name][i]if j==3 and i<3 else 0.)))for o in [bpy.data.objects[n]for n in front_names]for i in range(4)for j in range(4))
assert front_pose_error<1e-6
def geo(objects):
 v=[];f=[];owners=[];dg=bpy.context.evaluated_depsgraph_get()
 for o in objects:
  e=o.evaluated_get(dg);m=e.to_mesh();m.calc_loop_triangles();n=len(v);v.extend(e.matrix_world@x.co for x in m.vertices);f.extend(tuple(n+i for i in t.vertices)for t in m.loop_triangles);owners.extend([o.name]*len(m.loop_triangles));e.to_mesh_clear()
 return v,f,owners
row=next(r for r in s['form_panels']if r['mesh']=='IN1_PorcelainPanel_03');normal=Vector(row['mechanism']['rear_shoe']['normal']).normalized();tangent=Vector(row['axis_blender']).normalized()
groups=[];retained=[]
for sign in [-1,1]:
 prefix='IN2_Cassette03BodyBolt'+str(sign)
 names=[prefix+'Bolt',prefix+'OuterWasher'];assert all(n in bpy.data.objects for n in names)
 retained.extend(prefix+suffix for suffix in ['BoreLiner','InnerWasher','ThreadedInsert'])
 groups.append({'id':'rear_bolt_'+str(sign),'names':names,'normal':list(normal),'park':list(tangent*sign*.13)})
frame=bpy.data.objects['IN2_Cassette03_Frame'];bolt_names={n for r in groups for n in r['names']}
cassette=[o for o in frame.children_recursive if o.type=='MESH'and o.name not in front_names|bolt_names|set(retained)]
shell=[bpy.data.objects['IN1_FixedRearShell_03']]+[bpy.data.objects[n]for n in retained]
groups.extend([{'id':'cassette03','names':[o.name for o in cassette],'normal':list(normal)},{'id':'rear_shell03','names':[o.name for o in shell],'normal':list(normal)}])
claimed={n for g in groups for n in g['names']};assert sum(len(g['names'])for g in groups)==len(claimed)
fixed=[o for o in parts+base_parts if o.name not in claimed];fv,ff,fn=geo(fixed);ft=BVHTree.FromPolygons(fv,ff,all_triangles=True)
for g in groups:g['geo']=geo([bpy.data.objects[n]for n in g['names']])
def displacement(g,phase,u):
 if g['id'].startswith('rear_bolt'):
  if partial:return normal*(.010*u if phase==0 else .010)+normal*.8*(u if phase==2 else 1. if phase>2 else 0.)
  axial=normal*.07*min(1.,u)if phase==0 else normal*.07
  park=Vector(g['park'])*(u if phase==1 else 1. if phase>1 else 0.)
  return axial+park
 if g['id']=='cassette03':return normal*.8*(u if phase==2 else 1. if phase>2 else 0.)
 if g['id']=='rear_shell03':
  if phase!=3:return Vector()
  if '--two-step'in sys.argv:
   first=(normal+tangent*.7).normalized()*.12
   return first*(u/.25)if u<=.25 else first+Vector((0,.8,0))*((u-.25)/.75)
  return shell_direction*.65*u
 return Vector()
samples=[]
for phase in range(4):
 routes={'normal':normal}if phase<3 or not partial else {'normal':normal,'lower':(normal+tangent*.35).normalized(),'upper':(normal-tangent*.35).normalized(),'back':(normal+Vector((0,.6,0))).normalized(),'radial':Vector((normal.x,0,normal.z)).normalized()}
 if partial and phase==3 and '--wide-search'in sys.argv:routes={'lower07':(normal+tangent*.7).normalized(),'lower10':(normal+tangent).normalized(),'lower15':(normal+tangent*1.5).normalized(),'back_only':Vector((0,1,0)),'down_only':Vector((0,0,-1))}
 if '--two-step'in sys.argv:routes={'two_step':normal}
 for route,shell_direction in routes.items():
  for u in ([i/100 for i in range(101)]if '--two-step'in sys.argv else [0.,.02,.05,.1,.2,.35,.5,.7,.85,1.]):
   bodies=[];contacts=[]
   for g in groups:
    v,f,n=g['geo'];d=displacement(g,phase,u);tree=BVHTree.FromPolygons([p+d for p in v],f,all_triangles=True);hits=tree.overlap(ft)
    if hits:contacts.append({'pair':g['id']+' / fixed','count':len(hits),'owners':dict(collections.Counter(n[a]+' / '+fn[b]for a,b in hits))})
    bodies.append((g,tree,n))
   for i,(g,tree,n)in enumerate(bodies):
    for h,other,owners in bodies[i+1:]:
     hits=tree.overlap(other)
     if hits:contacts.append({'pair':g['id']+' / '+h['id'],'count':len(hits),'owners':dict(collections.Counter(n[a]+' / '+owners[b]for a,b in hits))})
   samples.append({'phase':phase,'route':route,'shell_direction':list(shell_direction),'fraction':u,'contacts':contacts});print('REAR03_PHASE',phase,u,[(c['pair'],c['count'])for c in contacts],flush=True)
for g in groups:g.pop('geo')
r={'source_sha256':s['source_sha256'],'partial_bolt_release':partial,'two_step_shell':('--two-step'in sys.argv),'shell_waypoints':[[0,0,0],list((normal+tangent*.7).normalized()*.12),list((normal+tangent*.7).normalized()*.12+Vector((0,.8,0)))],'groups':groups,'front_reference_sha256':front['source_sha256'],'front_pose_max_scalar_error':front_pose_error,'front_members':sorted(front_names),'prepared_support_plan_sha256':plan['source_sha256'],'samples':samples,'scope':('Partial bolt loosening .010, bolts follow cassette without lateral parking; then rear shell with retained liners/inserts.'if partial else 'Full bolt/washer withdrawal and lateral parking, cassette then rear shell.')+' Includes actual parked front/support/port meshes and original base. Finite translation samples, not source-animation compatibility, thread simulation, full service or art acceptance.'};(OUT/'probe.json').write_text(json.dumps(r,indent=2)+'\n')
