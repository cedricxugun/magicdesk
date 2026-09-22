"""R84 concert opening study with real two-stage telescopic slide geometry.
Closed ceramic shape retained; stronger opening is pending collision/art review."""
import bpy,json,math,hashlib,sys
from pathlib import Path
from mathutils import Vector,Quaternion
R=Path(__file__).resolve().parents[2];sys.path.insert(0,str(Path(__file__).parent))
import i_machined_geometry as P
IN=R/'review/I_refinement/nautilus_reset_r82/music_interface_r1/installed_r5'
OUT=R/'review/I_refinement/nautilus_reset_r82/chambers_r2';OUT.mkdir(parents=True,exist_ok=True)
SRC=R/'blender/collection/I_r84_concert_mechanism_r1.blend';assert not SRC.exists()
d=json.loads((IN/'build.json').read_text());bpy.ops.wm.open_mainfile(filepath=str(R/d['source']))
scene=bpy.context.scene;scene.frame_set(1);root=bpy.data.objects['R82_COIL_ROOT'];P.configure(bpy.data.collections['R82_NEW_FORM'])
if 'Collection_A_Rubber'not in bpy.data.materials:
 rubber=bpy.data.materials['R82_Recessed_Graphite'].copy();rubber.name='Collection_A_Rubber'
 bsdf=rubber.node_tree.nodes.get('Principled BSDF');bsdf.inputs['Metallic'].default_value=0.;bsdf.inputs['Roughness'].default_value=.55
def vec(v):return Vector(v)
def replace_sleeve(name,outer,inner,length,loc,axis,parent):
 old=bpy.data.objects[name];mat=old.data.materials[0]
 new=P.sleeve(name+'_NEW',outer,inner,length,parent,loc,'A_Nickel',axis)
 new.data.materials[0]=mat
 bpy.data.objects.remove(old,do_unlink=True);new.name=name;return new
extensions=[]
for p,j in zip(d['panels'],d['joints']):
 k=p['id'];old_stroke=vec(p['translation']).length;D=vec(p['translation'])*1.75
 if k==1:D=Vector((0,-.32,0))
 p['translation']=list(D);p['angle']=-math.radians(8 if k==1 else 32)
 A=vec(p['axis']);S=D.normalized();origin=vec(p['pivot']);radius=j['rod_radius']
 outer_length=j['guide_length'];stage_length=D.length/2+.055
 assert stage_length<=outer_length+.012,(k,stage_length,outer_length)
 stage=P.empty(f'I84_TelescopeStage_{k:02d}',root,origin)
 j['extension_nodes']=[{'node':stage.name,'fraction':.5}]
 j['stroke']=D.length;j['guide_length']=outer_length;j['stage_length']=stage_length;j['minimum_rod_engagement']=.055
 for side in [-1,1]:
  tip=origin+A*j['crosshead_span']*side
  replace_sleeve(f'R82_R3_Guide_Sleeve_{k}_{side}',radius*2.25,radius*1.58,outer_length,tip-S*outer_length/2,S,root)
  replace_sleeve(f'R82_R3_Guide_Wiper_{k}_{side}',radius*2.38,radius*1.53,.006,tip+S*.001,S,root)
  P.sleeve(f'I84_ExtensionTube_{k}_{side}',radius*1.48,radius*1.13,stage_length,stage,A*j['crosshead_span']*side-S*stage_length/2,'A_Nickel',S)
  P.sleeve(f'I84_ExtensionSeal_{k}_{side}',radius*1.56,radius*1.06,.005,stage,A*j['crosshead_span']*side+S*.001,'A_Rubber',S)
  rod=bpy.data.objects[f'R82_R3_Slider_Rod_{k}_{side}']
  bare=max(v.co.z for v in rod.data.vertices)-min(v.co.z for v in rod.data.vertices)
  rod.scale.z=stage_length/bare;rod.location=A*j['crosshead_span']*side-S*(stage_length/2-.005);rod.rotation_quaternion=S.to_track_quat('Z','Y')
 extensions.append((stage,p))
def ease(x):x=max(0,min(1,x));return x*x*x*(x*(x*6-15)+10)
for f in range(1,431):
 orig=f-60
 for p,j in zip(d['panels'],d['joints']):
  k=p['id'];t=(orig-25-(k-1)*1.5)/82 if orig<150 else 1-(orig-174-(6-k)*1.5)/82
  t=max(0,min(1,t));lift=ease(t/.3);turn=ease((t-.3)/.7)
  node=bpy.data.objects[p['node']];node.location=vec(p['pivot'])+vec(p['translation'])*lift;node.rotation_quaternion=Quaternion(vec(p['axis']),p['angle']*turn)
  node.keyframe_insert('location',frame=f);node.keyframe_insert('rotation_quaternion',frame=f)
  car=bpy.data.objects[j['carriage']];car.location=node.location;car.keyframe_insert('location',frame=f)
  stage=bpy.data.objects[j['extension_nodes'][0]['node']];stage.location=vec(p['pivot'])+vec(p['translation'])*lift*.5;stage.keyframe_insert('location',frame=f)
scene.frame_set(1);bpy.ops.wm.save_as_mainfile(filepath=str(SRC),compress=True)
d.update({'source':SRC.relative_to(R).as_posix(),'source_sha256':hashlib.sha256(SRC.read_bytes()).hexdigest(),'scope':'Stronger concert pose, closed ceramic unchanged, two-stage telescopic slides. New full-range fixture/ceramic clearance and visual assessment pending.'})
(OUT/'mechanism.json').write_text(json.dumps(d,indent=2)+'\n')
print('R84_CONCERT_SOURCE',d['source_sha256'],flush=True)
