"""Compare evaluated Blender body witnesses with raw glTF; no self-comparison."""
import json,struct,math,sys
from pathlib import Path
import numpy as np
R=Path(__file__).resolve().parents[1]
BASE=R/'review/I_refinement/nautilus_reset_r82/music_interface_r1'
def load_glb(path):
 raw=path.read_bytes();off=12;doc=None;blob=None
 while off<len(raw):
  n,t=struct.unpack_from('<II',raw,off);off+=8;chunk=raw[off:off+n];off+=n
  if t==0x4e4f534a:doc=json.loads(chunk)
  elif t==0x004e4942:blob=chunk
 return doc,blob
def positions(d,blob,accessor):
 a=d['accessors'][accessor];v=d['bufferViews'][a['bufferView']]
 assert a['componentType']==5126 and a['type']=='VEC3'
 offset=v.get('byteOffset',0)+a.get('byteOffset',0);stride=v.get('byteStride',12)
 return np.ndarray((a['count'],3),dtype='<f4',buffer=blob,offset=offset,strides=(stride,4))
variant=sys.argv[1] if len(sys.argv)>1 else 'installed_r4'
assert variant in ['installed_r4','installed_r5']
spec=json.loads((BASE/variant/'build.json').read_text());source=json.loads((BASE/variant/'evaluated_geometry.json').read_text())
doc,blob=load_glb(R/spec['component']);prior,_=load_glb(R/spec['parent_component'])
nodes={n['name']:n for n in doc['nodes']if 'name'in n};old_nodes={n['name']:n for n in prior['nodes']if 'name'in n}
rows=[];failures=[];old_omissions=[]
for row in source['objects']:
 node=nodes.get(row['name'])
 if node is None or 'mesh'not in node:failures.append({'name':row['name'],'error':'missing exported mesh'});continue
 primitives=doc['meshes'][node['mesh']]['primitives']
 count=sum(doc['accessors'][p['indices']]['count']//3 for p in primitives)
 arrays=np.concatenate([positions(doc,blob,p['attributes']['POSITION'])for p in primitives],axis=0)
 expected=np.array([[v[0],v[2],-v[1]]for v in row['local_samples_blender']],dtype=np.float32)
 error=max(float(np.sqrt(np.min(np.sum((arrays-point)**2,axis=1))))for point in expected)
 match=count==row['evaluated_triangles'] and error<.000003
 item={'name':row['name'],'source_triangles':row['evaluated_triangles'],'gltf_triangles':count,'samples':len(expected),'max_local_sample_error':error,'passed':match}
 rows.append(item)
 if not match:failures.append(item)
 old_node=old_nodes.get(row['name'])
 if old_node and 'mesh'in old_node:
  old_count=sum(prior['accessors'][p['indices']]['count']//3 for p in prior['meshes'][old_node['mesh']]['primitives'])
  if old_count!=row['evaluated_triangles']:old_omissions.append({'name':row['name'],'old_triangles':old_count,'evaluated_triangles':row['evaluated_triangles'],'modifiers':row['modifiers']})
out={'source_sha256':spec['source_sha256'],'component_sha256':spec['component_sha256'],'passed':not failures,'objects':rows,'failures':failures,'old_export_omissions':old_omissions,'scope':'Raw glTF versus independent evaluated Blender source: all body object triangle counts and sampled local coordinates, including modifier-added vertices. Not full directed triangles/normals, Godot imported pose, continuous collision or art acceptance.'}
(BASE/variant/'export_geometry_check.json').write_text(json.dumps(out,indent=2)+'\n')
print('objects',len(rows),'old omissions',len(old_omissions),'failures',len(failures),'max error',max(r['max_local_sample_error']for r in rows))
if failures:print(failures[:8]);raise SystemExit(1)
