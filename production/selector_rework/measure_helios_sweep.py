import bpy,json,numpy as np
from pathlib import Path
from mathutils import Matrix,Vector,Quaternion
root=Path(__file__).resolve().parents[2]
bpy.ops.wm.read_factory_settings(use_empty=True);bpy.ops.import_scene.gltf(filepath=str(root/'app/assets/helios_model.glb'))
data=json.loads((root/'app/assets/mechanism.json').read_text());C=Matrix(((1,0,0,0),(0,0,1,0),(0,-1,0,0),(0,0,0,1)))
meshes=[o for o in bpy.data.objects['TURNTABLE'].children_recursive if o.type=='MESH']
vertices=[]
for obj in meshes:
    v=np.array([(*p.co,1) for p in obj.data.vertices]);vertices.append((obj,v))
result=[]
for step in range(0,101,10):
    for control in data['controls']:
        p=control['samples'][step];m=Matrix.LocRotScale(Vector(p['p']),Quaternion((p['q'][3],*p['q'][:3])),Vector(p['s']))
        bpy.data.objects[control['name']].matrix_basis=C.inverted()@m@C
    bpy.context.view_layer.update();limits={str(k/10):0. for k in range(6,10)}
    for obj,v in vertices:
        world=v@np.array(obj.matrix_world).T;r=np.sqrt(world[:,0]**2+world[:,1]**2)
        for k in range(6,10):
            sel=(world[:,2]>=k/10)&(world[:,2]<(k+1)/10)
            if np.any(sel):limits[str(k/10)]=max(limits[str(k/10)],float(r[sel].max()))
    result.append({'open':step/100,'radial_sweep':limits})
(root/'production/selector_rework/helios_sweep.json').write_text(json.dumps(result,indent=2));print(json.dumps(result),flush=True)
