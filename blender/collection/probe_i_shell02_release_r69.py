"""Read-only panel02 release after the currently checked support/port poses."""
import bpy,json,hashlib,collections
from pathlib import Path
from mathutils import Vector,Quaternion
from mathutils.bvhtree import BVHTree
ROOT=Path(__file__).resolve().parents[2];OUT=ROOT/'review/I_refinement/nautilus_r1/shell02_release_r69';OUT.mkdir(parents=True,exist_ok=True)
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
bpy.context.view_layer.update();carrier=bpy.data.objects['IN1_PanelPivot_02'];selected=[o for o in [carrier,*carrier.children_recursive]if o.type=='MESH'];assert bpy.data.objects['IN1_PorcelainPanel_02']in selected
fixed=[o for o in parts+base_parts if o not in selected]
def geo(objects):
 v=[];f=[];owners=[];dg=bpy.context.evaluated_depsgraph_get()
 for o in objects:
  e=o.evaluated_get(dg);m=e.to_mesh();m.calc_loop_triangles();n=len(v);v.extend(e.matrix_world@x.co for x in m.vertices);f.extend(tuple(n+i for i in t.vertices)for t in m.loop_triangles);owners.extend([o.name]*len(m.loop_triangles));e.to_mesh_clear()
 return v,f,owners
v,f,n=geo(selected);fv,ff,fn=geo(fixed);ft=BVHTree.FromPolygons(fv,ff,all_triangles=True);bounds=[[min(p[k]for p in v)for k in range(3)],[max(p[k]for p in v)for k in range(3)]]
paths=[]
for label,direction in [('down',(0,0,-1)),('left_down',(-.7,0,-.7)),('back_down',(0,.6,-.8)),('front_down',(0,-.6,-.8)),('right_down',(.7,0,-.7))]:
 direction=Vector(direction).normalized()*.6;rows=[]
 for fraction in [0.,.005,.01,.02,.05,.1,.2,.4,.6,.8,1.]:
  tree=BVHTree.FromPolygons([p+direction*fraction for p in v],f,all_triangles=True);hits=tree.overlap(ft);rows.append({'fraction':fraction,'contacts':len(hits),'owners':dict(collections.Counter(n[a]+' / '+fn[b]for a,b in hits))})
 print('SHELL02_PATH',label,[(r['fraction'],r['contacts'])for r in rows],flush=True);paths.append({'name':label,'offset':list(direction),'samples':rows})
r={'source_sha256':s['source_sha256'],'selected':[o.name for o in selected],'bounds_blender':bounds,'paths':paths,'scope':'Actual panel02 carrier and its mesh children against all retained actual body, A, parked support/port groups and real base, in the terminal R65 partial release pose. Straight translations only; no new animation, physical fastener release, full sequence or art acceptance.'};(OUT/'probe.json').write_text(json.dumps(r,indent=2)+'\n')
