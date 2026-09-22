"""Manufacture cover 02's compact oblique hinge after the route study.
Retains R86's formed liner, complete Moonlight core and unchanged closed covers.
"""
import bpy,json,math,hashlib,sys
from pathlib import Path
from mathutils import Vector,Quaternion
R=Path(__file__).resolve().parents[2];sys.path.insert(0,str(Path(__file__).parent))
from i_r82_coil_surface import CoilSurface
import i_machined_geometry as P
BASE=R/'review/I_refinement/nautilus_reset_r82'
old=json.loads((BASE/'finish_r86/r4/build.json').read_text())
study=json.loads((BASE/'finish_r86/r4/panel02_axis_dense.json').read_text())
assert study['source_sha256']==old['source_sha256']
choices=[row for row in study['candidates'] if not row['contacts']]
assert len(choices)==1,'Do not build an unverified or ambiguous axis'
choice=choices[0]
OUT=BASE/'oblique_hinge_r87';OUT.mkdir(exist_ok=True)
SRC=R/'blender/collection/I_r87_oblique_hinge_r1.blend';COMP=R/'app/assets/collection/components/I_r87_oblique_hinge_r1.glb'
assert not SRC.exists() and not COMP.exists()
bpy.ops.wm.open_mainfile(filepath=str(R/old['source']));scene=bpy.context.scene;scene.frame_set(1);bpy.context.view_layer.update()
root=bpy.data.objects['R82_COIL_ROOT'];P.configure(bpy.data.collections['R82_NEW_FORM'])
surface=CoilSurface(json.loads((BASE/'mechanism_r9/build.json').read_text())['shape_parameters'])
witness={p['mesh']:[o.matrix_world@v.co for v in o.data.vertices] for p in old['panels'] for o in [bpy.data.objects[p['mesh']]]}
p=old['panels'][1];j=old['joints'][1];node=bpy.data.objects[p['node']];carriage=bpy.data.objects[j['carriage']]
axis=Vector(choice['axis']).normalized();pivot=Vector(p['pivot']);delta=Vector(p['translation']);direction=delta.normalized();length=j['guide_length'];radius=j['rod_radius'];span=j['crosshead_span'];tm=(p['ta']+p['tb'])/2
old_axis=p['axis'];p['latch_axis']=old_axis;p['axis']=list(axis);j['axis']=list(axis)
prefixes=('I85_Guide_2_','I85_Wiper_2_','I85_Rod_2_','I85_SupportA_2_','I85_SupportB_2_','I85_CoverEar_2_','I85_RotorStop_2_')
for o in list(bpy.data.objects):
 if o.name.startswith(prefixes) or o.name in ['I85_Crosshead_02','I85_HingePin_02']:bpy.data.objects.remove(o,do_unlink=True)
def bar(name,a,b,r,parent):
 a,b=Vector(a),Vector(b);return P.cylinder(name,r,(b-a).length,parent,(a+b)/2,'A_Nickel',(b-a).normalized(),min(.0015,r*.15))
for side in [-1,1]:
 tip=pivot+axis*span*side
 P.sleeve(f'I85_Guide_2_{side}',radius*2.25,radius+.0015,length,root,tip-direction*length/2,'A_Nickel',direction)
 P.sleeve(f'I85_Wiper_2_{side}',radius*2.4,radius+.0008,.006,root,tip+direction*.001,'A_Rubber',direction)
 P.cylinder(f'I85_Rod_2_{side}',radius,length,carriage,axis*span*side-direction*(length/2-.004),'A_Nickel',direction,.0005)
 tp=tm+side*.10;up=math.tau-.24
 contact=surface.point(tp,up,.016)+surface.normal(tp,up)*.005;back=tip-direction*(length-.014)
 mid=contact.lerp(back,.5)+surface.normal(tp,up)*.010
 bar(f'I85_SupportA_2_{side}',contact,mid,radius*1.20,root);bar(f'I85_SupportB_2_{side}',mid,back,radius*1.20,root)
 anchor=surface.point(tp,.15,0.)+surface.normal(tp,.15)*.010
 bar(f'I85_CoverEar_2_{side}',axis*span*side,anchor-pivot,radius*.80,node)
 P.sleeve(f'I85_RotorStop_2_{side}',radius*1.7,radius*1.01,.006,node,axis*side*(span+.012),'A_Bronze',axis)
P.sleeve('I85_Crosshead_02',radius*2.55,radius*1.06,2*span+.018,carriage,(0,0,0),'A_Nickel',axis)
P.cylinder('I85_HingePin_02',radius,2*span+.024,node,(0,0,0),'A_Bronze',axis,.0005)
rebuilt=list(P.parts)
def smooth(x):
 x=max(0.,min(1.,x));return x*x*x*(x*(x*6.-15.)+10.)
node.animation_data_clear()
for f in range(1,431):
 phase=max(0.,min(1.,(f-85)/90)) if f<234 else 1.-max(0.,min(1.,(f-234)/90))
 node.location=pivot+delta*smooth(phase/.25);node.rotation_quaternion=Quaternion(axis,p['angle']*smooth((phase-.25)/.75))
 node.keyframe_insert('location',frame=f);node.keyframe_insert('rotation_quaternion',frame=f)
scene.frame_set(1);bpy.context.view_layer.update()
error=max((bpy.data.objects[name].matrix_world@v.co-target).length for name,pts in witness.items() for v,target in zip(bpy.data.objects[name].data.vertices,pts))
assert error<1e-6,error
bpy.ops.wm.save_as_mainfile(filepath=str(SRC),compress=True)
for ob in root.children_recursive:
 if ob.type=='MESH' and ob.modifiers and not ob.data.shape_keys:
  ev=ob.evaluated_get(bpy.context.evaluated_depsgraph_get());me=bpy.data.meshes.new_from_object(ev,preserve_all_data_layers=True,depsgraph=bpy.context.evaluated_depsgraph_get());ob.modifiers.clear();ob.data=me
curves=[o for o in root.children_recursive if o.type=='CURVE']
if curves:
 bpy.ops.object.select_all(action='DESELECT')
 for o in curves:o.select_set(True)
 bpy.context.view_layer.objects.active=curves[0];bpy.ops.object.convert(target='MESH')
bpy.ops.object.select_all(action='DESELECT')
for o in [root,*root.children_recursive]:o.select_set(True)
bpy.context.view_layer.objects.active=root
bpy.ops.export_scene.gltf(filepath=str(COMP),export_format='GLB',use_selection=True,export_animations=False,export_morph=True,export_morph_normal=True,export_apply=False,export_tangents=True,export_extras=True)
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
ART=R/'app/assets/collection/art/I/r87_oblique_hinge';ART.mkdir(exist_ok=True)
layout=json.loads((R/'app'/old['chamber_response_layout'].removeprefix('res://')).read_text());layout['source_sha256']=sha(SRC);layout['component_sha256']=sha(COMP)
(ART/'chamber_layout.json').write_text(json.dumps(layout,indent=2)+'\n')
report={**old,'source':SRC.relative_to(R).as_posix(),'source_sha256':sha(SRC),'component':COMP.relative_to(R).as_posix(),'component_sha256':sha(COMP),'parent_source':old['source'],'closed_ceramic_world_error':error,'rebuilt_oblique_parts':rebuilt,'oblique_axis_study':study,'chamber_response_layout':'res://'+(ART/'chamber_layout.json').relative_to(R/'app').as_posix(),'scope':'Real oblique pin/crosshead, guide, rod, fitted-shoe supports and cover ears for 02, with original short release stroke and 45-degree angle. Complete manufactured assembly contact/runtime/art review pending.'}
(OUT/'build.json').write_text(json.dumps(report,indent=2)+'\n')
bpy.ops.wm.open_mainfile(filepath=str(SRC));scene=bpy.context.scene;scene.frame_set(205)
try:
 pref=bpy.context.preferences.addons['cycles'].preferences;pref.compute_device_type='CUDA';pref.get_devices()
 for dv in pref.devices:dv.use=dv.type=='CUDA'
 scene.cycles.device='GPU'
except:pass
scene.cycles.samples=48;scene.render.resolution_x=1000;scene.render.resolution_y=1100
scene.render.filepath=str(OUT/'open.png');bpy.ops.render.render(write_still=True)
print('R87_BUILT',report['source_sha256'],'closed error',error,flush=True)
