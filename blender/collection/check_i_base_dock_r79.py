"""Independent current candidate contact/operating-pose checks, with all bodies retained."""
import bpy,json,hashlib,collections
from pathlib import Path
from mathutils import Vector,Quaternion
from mathutils.bvhtree import BVHTree
ROOT=Path(__file__).resolve().parents[2];OUT=ROOT/'review/I_refinement/nautilus_r1/base_dock_r79'
s=json.loads((OUT/'build.json').read_text());assert hashlib.sha256((ROOT/s['source']).read_bytes()).hexdigest()==s['source_sha256']
bpy.ops.wm.open_mainfile(filepath=str(ROOT/s['source']));bpy.context.scene.frame_set(1);bpy.context.view_layer.update()
body=bpy.data.objects['IN1_BodyRoot'];mouth=bpy.data.objects['IAM_MODULE'];base=bpy.data.objects['BASE_FIXED']
all_meshes=list(dict.fromkeys(o for r in [body,mouth,base] for o in [r,*r.children_recursive] if o.type=='MESH'))
new_names=set(s['base_dock']['new_meshes']);new=[o for o in all_meshes if o.name in new_names];fixed=[o for o in all_meshes if o.name not in new_names]
def geo(objects):
 v=[];f=[];names=[];dg=bpy.context.evaluated_depsgraph_get()
 for o in objects:
  e=o.evaluated_get(dg);m=e.to_mesh();m.calc_loop_triangles();start=len(v);v.extend(e.matrix_world@p.co for p in m.vertices);f.extend(tuple(start+i for i in t.vertices) for t in m.loop_triangles);names.extend([o.name]*len(m.loop_triangles));e.to_mesh_clear()
 return v,f,names
def bvh(objects):
 v,f,n=geo(objects);return BVHTree.FromPolygons(v,f,all_triangles=True),v,f,n
def counter(a,b):
 return dict(collections.Counter(a[3][i]+' / '+b[3][j] for i,j in a[0].overlap(b[0])))
self_checks=[]
for o in new+[bpy.data.objects[n] for n in s['base_dock']['modified'] if n!='BASE_FIXED_DisplayMesh']:
 t,v,f,n=bvh([o]);hits=[(a,b) for a,b in t.overlap(t) if a<b and not set(f[a])&set(f[b])]
 self_checks.append({'name':o.name,'self_contacts':len(hits),'examples':[[[list(v[i]) for i in f[k]] for k in pair] for pair in hits[:3]]})
new_geometry=[bvh([o]) for o in new];new_pairs={}
for i,a in enumerate(new_geometry):
 for b in new_geometry[i+1:]:new_pairs.update(counter(a,b))
initial={}
for r in s['form_panels']:
 node=bpy.data.objects[r['node']];node.animation_data_clear();initial[node.name]=node.matrix_basis.copy()
 if 'mechanism' in r:
  for key in ['carriage','rotor']:
   o=bpy.data.objects[r['mechanism'][key]];o.animation_data_clear();initial[o.name]=o.matrix_basis.copy()
samples=[]
for u in [0.,.125,.25,.375,.5,.625,.75,.875,1.]:
 for r in s['form_panels']:
  node=bpy.data.objects[r['node']];fraction=r.get('lift_fraction',0.);clear=min(1.,u/max(fraction,1e-6));turn=max(0.,min(1.,(u-fraction)/max(1.-fraction,1e-6)))
  node.matrix_basis=initial[node.name];node.location+=Vector(r.get('lift_blender',[0,0,0]))*clear;node.rotation_mode='QUATERNION';node.rotation_quaternion=Quaternion(Vector(r['axis_blender']),r['angle']*turn)@node.rotation_quaternion
  if 'mechanism' in r:
   m=r['mechanism'];carriage=bpy.data.objects[m['carriage']];rotor=bpy.data.objects[m['rotor']];carriage.matrix_basis=initial[carriage.name];rotor.matrix_basis=initial[rotor.name];carriage.location.z+=m['stroke']*clear;rotor.rotation_mode='QUATERNION';rotor.rotation_quaternion=Quaternion(Vector(m['axis_local_blender']),r['angle']*turn)@rotor.rotation_quaternion
 bpy.context.view_layer.update();a=bvh(new);b=bvh(fixed);contacts=counter(a,b)
 samples.append({'opening':u,'contacts':contacts});print('R79_CONTACTS',u,contacts,flush=True)
report={'source_sha256':s['source_sha256'],'self_checks':self_checks,'new_vs_new':new_pairs,'operating_samples':samples,
 'passed':not new_pairs and all(not r['self_contacts'] for r in self_checks) and all(not r['contacts'] for r in samples),
 'scope':'Current new hardware self/pair contacts and nine actual opening poses against all retained body/mouth/base meshes. Does not certify continuous motion, loads, hidden threads or full service.'}
(OUT/'contact_check.json').write_text(json.dumps(report,indent=2)+'\n');print('R79_CHECK_PASSED',report['passed'],flush=True)
