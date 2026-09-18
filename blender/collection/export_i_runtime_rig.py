"""Read the saved source and export its actual runtime control anchors."""
import bpy,json,hashlib
from pathlib import Path
from mathutils import Vector
ROOT=Path(__file__).resolve().parents[2];build=json.loads((ROOT/'review/I_refinement/r2/build.json').read_text())
source=ROOT/build['source'];bpy.ops.wm.open_mainfile(filepath=str(source));bpy.context.scene.frame_set(1)
def v(p):return [p[0],p[2],-p[1]]
panels=[]
for i in range(6):
    o=bpy.data.objects['IH1_FrontPanel'+str(i)];panels.append({'name':o.name,'direction':v(o['open_direction']),'stroke':o['stroke']})
root=bpy.data.objects['IH1_MODULE'];curves=[]
for o in bpy.data.objects['IH1_UPPER'].children_recursive:
    if o.type=='CURVE' and any(k in o.name for k in ['BrassReturnConductor','ChamberSpine']):
        transform=root.matrix_world.inverted()@o.matrix_world
        curves.append({'name':o.name,'points':[v(transform@Vector(p.co[:3])) for p in o.data.splines[0].points]})
result={'version':1,'source_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'component':'res://assets/collection/components/I_pneumatic_r2.glb','component_sha256':build['component_sha256'],'panels':panels,'leaves':['IH1_IrisLeaf'+str(i) for i in range(6)],'cam':'IH1_IrisCamDrive','mouth':'IH1_Mouth','front':build['front_group'],'diaphragm':'IH1_Diaphragm','relief':build['relief_poppet'],'wall':build['bellows_wall'],'surround':build['surround'],'springs':build['springs'],'curves':curves,'stroke':.132,'visual_amplification':40.,'visual_limit':.014,'scope':'Godot Y-up anchors and existing glTF node names; no main registry change.'}
snapshots=[]
labels=[x['name'] for x in panels]+result['leaves']+[result['cam'],result['front'],result['diaphragm'],result['relief']]
C=__import__('mathutils').Matrix(((1,0,0,0),(0,0,1,0),(0,-1,0,0),(0,0,0,1)))
for frame in [1,39,88,96,109,185,226,361]:
    bpy.context.scene.frame_set(frame);bpy.context.view_layer.update();poses={}
    for label in labels:
        matrix=C@root.matrix_world.inverted()@bpy.data.objects[label].matrix_world@C.inverted();poses[label]=[list(row) for row in matrix]
    snapshots.append({'frame':frame,'poses':poses})
(ROOT/'review/I_refinement/r2/runtime_source_poses.json').write_text(json.dumps({'source_sha256':result['source_sha256'],'snapshots':snapshots},indent=2)+'\n')
path=ROOT/'app/assets/collection/i_runtime_rig.json';path.write_text(json.dumps(result,indent=2)+'\n');print('I_RUNTIME_RIG',path,len(curves))
