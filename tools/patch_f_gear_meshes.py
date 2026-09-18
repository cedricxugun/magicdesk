"""Append two replacement meshes to a GLB; preserve every other node/mesh/image byte."""
import json,struct,hashlib,copy,sys
import numpy as np
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'review/F_complete/revision_20260911/gears'
source=ROOT/'app/assets/collection/models/F_complete.glb'
raw=source.read_bytes();length=struct.unpack_from('<I',raw,12)[0];doc=json.loads(raw[20:20+length]);binary_offset=20+length
assert raw[binary_offset+4:binary_offset+8]==b'BIN\x00'
binary=bytearray(raw[binary_offset+8:]);old_binary=bytes(binary);before=copy.deepcopy(doc)
payload=json.loads((OUT/'mesh_payload.json').read_text());names={m['name']:i for i,m in enumerate(doc['materials'])}
def accessor(values,kind,components,integer=False):
    while len(binary)%4:binary.append(0)
    data=struct.pack('<'+('I' if integer else 'f')*len(values),*values)
    view=len(doc['bufferViews']);doc['bufferViews'].append({'buffer':0,'byteOffset':len(binary),'byteLength':len(data),'target':34963 if integer else 34962});binary.extend(data)
    a={'bufferView':view,'componentType':5125 if integer else 5126,'count':len(values)//components,'type':kind}
    if kind=='VEC3':
        a['min']=[min(values[i::components]) for i in range(components)];a['max']=[max(values[i::components]) for i in range(components)]
    index=len(doc['accessors']);doc['accessors'].append(a);return index
replaced=[]
for name,groups in payload.items():
    nodes=[n for n in doc['nodes'] if n.get('name')==name];assert len(nodes)==1,name
    mesh_index=nodes[0]['mesh'];assert sum(n.get('mesh')==mesh_index for n in doc['nodes'])==1
    node=nodes[0];x,y,z,w=node.get('rotation',[0,0,0,1]);q=np.array([x,y,z,w]);q=q/np.linalg.norm(q);x,y,z,w=q
    rotation=np.array([[1-2*(y*y+z*z),2*(x*y-z*w),2*(x*z+y*w)],[2*(x*y+z*w),1-2*(x*x+z*z),2*(y*z-x*w)],[2*(x*z-y*w),2*(y*z+x*w),1-2*(x*x+y*y)]])
    transform=np.eye(4);transform[:3,:3]=rotation@np.diag(node.get('scale',[1,1,1]));transform[:3,3]=node.get('translation',[0,0,0]);inverse=np.linalg.inv(transform)
    primitives=[]
    for material,group in groups.items():
        assert material in names,material
        # Payload is in gear-root space; the retained render-surface node has
        # its own 90-degree rotation and offset. Convert into that node's space.
        positions=np.einsum('ij,kj->ik',np.asarray(group['positions']).reshape(-1,3),inverse[:3,:3],optimize=False)+inverse[:3,3]
        normals=np.einsum('ij,jk->ik',np.asarray(group['normals']).reshape(-1,3),transform[:3,:3],optimize=False);normals/=np.linalg.norm(normals,axis=1)[:,None]
        tangents=np.asarray(group['tangents']).reshape(-1,4);tangents[:,:3]=np.einsum('ij,kj->ik',tangents[:,:3],inverse[:3,:3],optimize=False);tangents[:,:3]/=np.linalg.norm(tangents[:,:3],axis=1)[:,None]
        assert np.isfinite(positions).all() and np.isfinite(normals).all() and np.isfinite(tangents).all()
        group['positions']=positions.reshape(-1).tolist();group['normals']=normals.reshape(-1).tolist();group['tangents']=tangents.reshape(-1).tolist()
        attrs={key:accessor(group[field],kind,size) for key,field,kind,size in [('POSITION','positions','VEC3',3),('NORMAL','normals','VEC3',3),('TEXCOORD_0','uv','VEC2',2),('TANGENT','tangents','VEC4',4)]}
        primitives.append({'attributes':attrs,'indices':accessor(group['indices'],'SCALAR',1,True),'material':names[material],'mode':4})
    doc['meshes'][mesh_index]['primitives']=primitives;replaced.append(mesh_index)
doc['buffers'][0]['byteLength']=len(binary)
for key in before:
    if key not in ['meshes','accessors','bufferViews','buffers']:assert doc[key]==before[key],key
for i,mesh in enumerate(before['meshes']):
    if i not in replaced:assert doc['meshes'][i]==mesh
assert bytes(binary[:len(old_binary)])==old_binary
j=json.dumps(doc,separators=(',',':')).encode();j+=b' '*((-len(j))%4);binary+=b'\x00'*((-len(binary))%4)
output=b'glTF'+struct.pack('<II',2,12+8+len(j)+8+len(binary))+struct.pack('<I',len(j))+b'JSON'+j+struct.pack('<I',len(binary))+b'BIN\x00'+binary
target=source.with_name('F_gears_candidate.glb');target.write_bytes(output)
sys.path.insert(0,str(ROOT/'blender/collection'))
from f_gear_geometry import DISASSEMBLY_ROUTE
meta=json.loads(source.with_suffix('.json').read_text());
next(p for p in meta['parts'] if p['name']=='F2_P_Differential')['route']=DISASSEMBLY_ROUTE
meta['source_blend']='blender/collection/F_gear_refinement.blend';target.with_suffix('.json').write_text(json.dumps(meta,separators=(',',':'))+'\n')
report={'input_sha256':hashlib.sha256(raw).hexdigest(),'candidate_sha256':hashlib.sha256(output).hexdigest(),'replaced_meshes':replaced,'original_binary_prefix_preserved':True,'node_graph_materials_and_other_meshes_unchanged':True,'candidate':str(target.relative_to(ROOT)),'scope':'Two evaluated source gear meshes only; no current GLB replacement, no material or animation-node changes.'}
(OUT/'glb_patch.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
