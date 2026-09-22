"""Author complete forward/return motion in Blender and export its exact keys."""
import bpy, json, math, hashlib, struct, sys
from pathlib import Path
from mathutils import Vector, Quaternion, Matrix
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(Path(__file__).parent))
from i_service_r76_prepare import prepare,depth
OUT=ROOT/'review/I_refinement/nautilus_r1/coupling_repair_r76'
ART=ROOT/'app/assets/collection/art/I/coupling_r76';ART.mkdir(parents=True,exist_ok=True)
s=json.loads((OUT/'build.json').read_text());route=json.loads((OUT/'release/probe.json').read_text())
assert all(not r['contacts'] for r in route['samples']) and route['source_sha256']==s['source_sha256']
assert json.loads((OUT/'thread_interlock.json').read_text())['passed']
art=ROOT/'production/I_refinement/nautilus_r1/coupling_repair_r76/release_storyboard.png';assert art.exists()
body,mouth,parts,preparation=prepare(s)
for o in bpy.data.objects:
    if o.animation_data:o.animation_data_clear()
    if o.type=='MESH' and o.data.shape_keys and o.data.shape_keys.animation_data:o.data.shape_keys.animation_data_clear()
mount=bpy.data.objects['IC1_MouthMount'];axis_delta=mount.matrix_world.to_3x3().col[2];axis=axis_delta.normalized()
root=bpy.data.objects.new('IS76_MotionRoot',None);bpy.context.scene.collection.objects.link(root)
groups=[{'id':'Mouth','members':route['assembly_members'],'center':Vector()}]
for row in s['coupling_threads']['threads']:
    center=mount.matrix_world@Vector(row['center_parent'])+Vector((0,0,.45))
    groups.extend([{'id':'Screw%02d'%row['index'],'members':[row['bolt']],'center':center,'pitch':row['pitch_parent']},
                   {'id':'Washer%02d'%row['index'],'members':[row['bolt']+'_Washer'],'center':center}])
members=[n for g in groups for n in g['members']];assert len(set(members))==len(members)
homes={n:bpy.data.objects[n].matrix_world.copy() for n in members}
markers={}
for g in groups:
    marker=bpy.data.objects.new('IS76_'+g['id'],None);bpy.context.scene.collection.objects.link(marker)
    marker.parent=root;marker.location=g['center'];marker.rotation_mode='QUATERNION';markers[g['id']]=marker
    bpy.context.view_layer.update()
    for n in sorted(g['members'],key=lambda n:depth(bpy.data.objects[n])):
        o=bpy.data.objects[n];o.parent=marker;o.matrix_parent_inverse=Matrix.Identity(4);o.matrix_world=homes[n]

def smooth(t):
    t=max(0.,min(1.,t));return t*t*t*(10+t*(-15+6*t))

def motion(g,t):
    loosen=smooth((t-.5)/2.4)
    # Keep a separate low-speed disengagement stroke before the main travel.
    withdrawal=.035*smooth((t-3.25)/.6)+.765*smooth((t-3.85)/1.9)
    if g['id']=='Mouth':return -axis*withdrawal,Quaternion()
    distance=.006*loosen
    twist=math.tau*distance/axis_delta.length/g['pitch'] if 'pitch' in g else 0.
    return g['center']+axis*distance,Quaternion(axis,twist)

scene=bpy.context.scene;fps=60;end=384;scene.render.fps=fps
scene.frame_start=0;scene.frame_end=804
for frame in range(805):
    t=min(frame/fps,end/fps) if frame<=420 else max(0.,(804-frame)/fps)
    for g in groups:
        marker=markers[g['id']];marker.location,marker.rotation_quaternion=motion(g,t)
        marker.keyframe_insert(data_path='location',frame=frame);marker.keyframe_insert(data_path='rotation_quaternion',frame=frame)
for marker in markers.values():
    for curve in marker.animation_data.action.layers[0].strips[0].channelbag(marker.animation_data.action_slot).fcurves:
        for key in curve.keyframe_points:key.interpolation='LINEAR'
scene.frame_set(0);bpy.context.view_layer.update()
start_errors=sorted([(max(abs(bpy.data.objects[n].matrix_world[i][j]-homes[n][i][j]) for i in range(4) for j in range(4)),n) for n in members],reverse=True)
print('R76_START_ERRORS',start_errors[:5],flush=True)
assert start_errors[0][0]<1e-6
positions={g['id']:[] for g in groups};rotations={g['id']:[] for g in groups};witnesses=[]
local=[Vector((0,0,0)),Vector((.01,0,0)),Vector((0,.01,0)),Vector((0,0,.01))]
C=Matrix(((1,0,0,0),(0,0,1,0),(0,-1,0,0),(0,0,0,1)))
def gv(v):return [float(v.x),float(v.z),-float(v.y)]
# Include every affected mesh in independent source-point witnesses, rather
# than assuming matching formulas imply matching imported hierarchy.
for frame in range(end+1):
    scene.frame_set(frame);bpy.context.view_layer.update();dg=bpy.context.evaluated_depsgraph_get()
    for g in groups:
        marker=markers[g['id']].evaluated_get(dg);positions[g['id']].append(gv(marker.location))
        q=(C@marker.matrix_local@C.inverted()).to_quaternion();rotations[g['id']].append([q.x,q.y,q.z,q.w])
    if frame in [0,30,60,90,120,150,174,195,213,231,255,285,315,345,384]:
        witnesses.append({'time':frame/fps,'points':{n:[gv(bpy.data.objects[n].evaluated_get(dg).matrix_world@p) for p in local] for n in members}})
scene.frame_set(804);bpy.context.view_layer.update()
return_error=max(abs(bpy.data.objects[n].matrix_world[i][j]-homes[n][i][j]) for n in members for i in range(4) for j in range(4))
assert return_error<1e-6
scene.frame_set(0)
source=ROOT/'blender/collection/I_coupling_motion_r76.blend';assert not source.exists()
bpy.ops.wm.save_as_mainfile(filepath=str(source),compress=True)
binary=bytearray();views=[];accessors=[]
def accessor(rows,width):
    offset=len(binary)
    for row in rows:binary.extend(struct.pack('<'+'f'*width,*row))
    view=len(views);views.append({'buffer':0,'byteOffset':offset,'byteLength':len(binary)-offset})
    index=len(accessors);accessors.append({'bufferView':view,'componentType':5126,'count':len(rows),'type':{1:'SCALAR',3:'VEC3',4:'VEC4'}[width],
        'min':[min(r[i] for r in rows) for i in range(width)],'max':[max(r[i] for r in rows) for i in range(width)]})
    return index
times=accessor([[f/fps] for f in range(end+1)],1)
nodes=[{'name':'IS76_MotionRoot','children':list(range(1,len(groups)+1))}];samplers=[];channels=[]
for i,g in enumerate(groups,1):
    nodes.append({'name':'IS76_'+g['id'],'translation':positions[g['id']][0],'rotation':rotations[g['id']][0]})
    for path,data,width in [('translation',positions,3),('rotation',rotations,4)]:
        output=accessor(data[g['id']],width);samplers.append({'input':times,'output':output,'interpolation':'LINEAR'})
        channels.append({'sampler':len(samplers)-1,'target':{'node':i,'path':path}})
data={'asset':{'version':'2.0','generator':'Blender evaluated R76 coupling motion'},'scene':0,'scenes':[{'nodes':[0]}],
    'nodes':nodes,'animations':[{'name':'CouplingService','samplers':samplers,'channels':channels}],
    'buffers':[{'byteLength':len(binary)}],'bufferViews':views,'accessors':accessors}
j=json.dumps(data,separators=(',',':')).encode();j+=b' '*((-len(j))%4);binary+=b'\0'*((-len(binary))%4)
glb=struct.pack('<III',0x46546c67,2,12+8+len(j)+8+len(binary))+struct.pack('<II',len(j),0x4e4f534a)+j+struct.pack('<II',len(binary),0x004e4942)+binary
asset=ART/'coupling_motion.glb';asset.write_bytes(glb);sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
manifest={'body_source_sha256':s['source_sha256'],'body_component_sha256':s['component_sha256'],
    'motion_source':str(source.relative_to(ROOT)).replace('\\','/'),'motion_source_sha256':sha(source),
    'motion_asset':'res://assets/collection/art/I/coupling_r76/coupling_motion.glb','motion_asset_sha256':sha(asset),
    'clip':'CouplingService','duration':end/fps,'fps':fps,
    'groups':[{'id':g['id'],'marker':'IS76_'+g['id'],'roots':g['members']} for g in groups],
    'local_points':[gv(v) for v in local],'source_witnesses':witnesses,'preparation':preparation,
    'source_return_scalar_error':return_error,'art_sha256':sha(art),
    'scope':'Actual 13-group Blender keyed screws/washers/intact mouth, forward 6.4 seconds and authored 13.4 second full round trip. Source ready-state only; combined prior service and native app integration remain pending.'}
(ART/'coupling_motion.json').write_text(json.dumps(manifest,indent=2)+'\n')
(OUT/'motion_manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
print('R76_ANIMATION_SAVED',manifest['motion_source_sha256'],len(members),return_error,flush=True)
