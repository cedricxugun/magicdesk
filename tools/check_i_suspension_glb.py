"""Compare actual GLB morph positions to evaluated Blender points, without Blender."""
from pathlib import Path
import json,struct,hashlib,sys
import numpy as np
from scipy.spatial import cKDTree
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/(sys.argv[1] if len(sys.argv)>1 else 'review/I_refinement/part_a_mouth/shutter_r2/diaphragm');spec=json.loads((OUT/'build.json').read_text());gold=json.loads((OUT/'source_suspension_points.json').read_text());assert spec['source_sha256']==gold['source_sha256'];path=ROOT/spec['component'];raw=path.read_bytes();assert hashlib.sha256(raw).hexdigest()==gold['component_sha256']
length,kind=struct.unpack_from('<II',raw,12);gltf=json.loads(raw[20:20+length]);offset=20+length;binlength,binkind=struct.unpack_from('<II',raw,offset);blob=raw[offset+8:offset+8+binlength]

def accessor(index):
 a=gltf['accessors'][index];dtype={5126:'<f4',5125:'<u4',5123:'<u2',5121:'u1'}[a['componentType']];dim={'SCALAR':1,'VEC2':2,'VEC3':3,'VEC4':4}[a['type']];width=np.dtype(dtype).itemsize
 def read(view_index,offset,count,columns,dtype):
  view=gltf['bufferViews'][view_index];item=np.dtype(dtype).itemsize;stride=view.get('byteStride',columns*item);start=view.get('byteOffset',0)+offset
  return np.ndarray((count,columns),dtype=dtype,buffer=blob,offset=start,strides=(stride,item)).copy()
 result=read(a['bufferView'],a.get('byteOffset',0),a['count'],dim,dtype).astype(float) if 'bufferView' in a else np.zeros((a['count'],dim))
 if 'sparse' in a:
  sparse=a['sparse'];indices=sparse['indices'];values=sparse['values'];index_dtype={5125:'<u4',5123:'<u2',5121:'u1'}[indices['componentType']]
  selected=read(indices['bufferView'],indices.get('byteOffset',0),sparse['count'],1,index_dtype).ravel()
  result[selected]=read(values['bufferView'],values.get('byteOffset',0),sparse['count'],dim,dtype)
 return result

def local(node):
 if 'matrix' in node:return np.asarray(node['matrix']).reshape(4,4,order='F')
 x,y,z,w=node.get('rotation',[0,0,0,1]);rot=np.array([[1-2*(y*y+z*z),2*(x*y-z*w),2*(x*z+y*w)],[2*(x*y+z*w),1-2*(x*x+z*z),2*(y*z-x*w)],[2*(x*z-y*w),2*(y*z+x*w),1-2*(x*x+y*y)]])
 m=np.eye(4);m[:3,:3]=rot@np.diag(node.get('scale',[1,1,1]));m[:3,3]=node.get('translation',[0,0,0]);return m
nodes=gltf['nodes'];parents={child:i for i,n in enumerate(nodes) for child in n.get('children',[])};indices={n['name']:i for i,n in enumerate(nodes) if 'name' in n}

def world(index,stroke):
 m=local(nodes[index])
 if nodes[index].get('name')==spec['diaphragm']['moving']:m[1,3]+=stroke
 return world(parents[index],stroke)@m if index in parents else m

source=np.load(OUT/'source_suspension_points.npz');results=[]
for pose,stroke in enumerate(gold['strokes']):
 for name in gold['objects']:
  ni=indices[name];mesh=gltf['meshes'][nodes[ni]['mesh']];names=mesh.get('extras',{}).get('targetNames',[]);allpoints=[]
  for primitive in mesh['primitives']:
   p=accessor(primitive['attributes']['POSITION'])
   for target,label in zip(primitive.get('targets',[]),names):
    weight=max(0,stroke/.006) if label=='Pressure' else max(0,-stroke/.006) if label=='Rebound' else 0
    if weight:p+=weight*accessor(target['POSITION'])
   matrix=world(ni,stroke);allpoints.append(p@matrix[:3,:3].T+matrix[:3,3])
  actual=np.concatenate(allpoints);expected=source['pose%d__%s'%(pose,name)]
  error=max(float(cKDTree(expected).query(actual)[0].max()),float(cKDTree(actual).query(expected)[0].max()))
  results.append({'stroke':stroke,'name':name,'max_symmetric_vertex_distance':error,'passed':error<1e-5})
report={'source_sha256':gold['source_sha256'],'component_sha256':gold['component_sha256'],'passed':all(r['passed'] for r in results),'samples':results,'scope':'Actual GLB accessors, morph deltas and node hierarchy independently compared in both directions with evaluated Blender world positions at eight amplitudes. Does not prove raster normals, native input or complete collision.'}
(OUT/'glb_geometry_check.json').write_text(json.dumps(report,indent=2)+'\n');print('GLB_SUSPENSION_GEOMETRY',report['passed'],max(r['max_symmetric_vertex_distance'] for r in results));raise SystemExit(0 if report['passed'] else 1)
