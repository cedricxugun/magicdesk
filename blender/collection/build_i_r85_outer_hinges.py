"""R85 actual outer-edge slides, trunnions and fitted support/cover shoes.
Preserves closed ceramic geometry and uses the checked outer-release path."""
import bpy,bmesh,json,math,hashlib,sys
from pathlib import Path
from mathutils import Vector,Matrix,Quaternion
R=Path(__file__).resolve().parents[2];sys.path.insert(0,str(Path(__file__).parent))
from i_r82_coil_surface import CoilSurface
import i_machined_geometry as P
BASE=R/'review/I_refinement/nautilus_reset_r82'
seed=json.loads((BASE/'chambers_r3/build.json').read_text())
reference=json.loads((BASE/'mechanism_r9/build.json').read_text())
surface=CoilSurface(reference['shape_parameters'])
EXTERNAL='--external-shoes' in sys.argv
suffix='r2' if EXTERNAL else 'r1'
OUT=BASE/('outer_hinge_'+suffix);OUT.mkdir(exist_ok=True)
SRC=R/('blender/collection/I_r85_outer_hinge_'+suffix+'.blend');COMP=R/('app/assets/collection/components/I_r85_outer_hinge_'+suffix+'.glb')
assert not SRC.exists() and not COMP.exists()
bpy.ops.wm.open_mainfile(filepath=str(R/seed['source']));scene=bpy.context.scene;scene.frame_set(1);bpy.context.view_layer.update()
root=bpy.data.objects['R82_COIL_ROOT'];col=bpy.data.collections['R82_NEW_FORM'];P.configure(col)
for target,source in [('Collection_A_Rubber','R82_Recessed_Graphite'),('Collection_A_Nickel','R82_Satin_Nickel'),('Collection_A_Bronze','R82_Warm_Acoustic_Alloy')]:
 if target not in bpy.data.materials:
  ma=bpy.data.materials[source].copy();ma.name=target
def remove(o):
 for c in list(o.children_recursive):bpy.data.objects.remove(c,do_unlink=True)
 bpy.data.objects.remove(o,do_unlink=True)
def mesh(name,vs,fs,parent,material):
 me=bpy.data.meshes.new(name+'Mesh');me.from_pydata(vs,[],fs);me.update();o=bpy.data.objects.new(name,me);col.objects.link(o);o.parent=parent;me.materials.append(bpy.data.materials[material])
 bm=bmesh.new();bm.from_mesh(me);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(me);bm.free()
 for p in me.polygons:p.use_smooth=True
 return o
def shoe(name,t,u,parent,origin,inset):
 vs=[];fs=[];NU=12;NV=12
 for layer in [0,.004]:
  for i in range(NU+1):
   tt=t-.065+.13*i/NU
   for j in range(NV+1):
    uu=u-.060+.12*j/NV
    n=surface.normal(tt,uu)
    vs.append(surface.point(tt,uu,inset)+n*(.001+layer)-origin)
 count=(NU+1)*(NV+1);stride=NV+1
 for lay in [0,1]:
  for i in range(NU):
   for j in range(NV):
    a=lay*count+i*stride+j;q=(a,a+1,a+stride+1,a+stride);fs.append(q if lay==0 else q[::-1])
 edge=list(range(stride))+[i*stride+NV for i in range(1,NU+1)]+[NU*stride+j for j in range(NV-1,-1,-1)]+[i*stride for i in range(NU-1,0,-1)]
 for i,a in enumerate(edge):
  b=edge[(i+1)%len(edge)];fs.append((a,b,b+count,a+count))
 return mesh(name,vs,fs,parent,'Collection_A_Nickel')
def bar(name,a,b,r,parent,material='A_Nickel'):
 a,b=Vector(a),Vector(b);return P.cylinder(name,r,(b-a).length,parent,(a+b)/2,material,(b-a).normalized(),bevel=min(.0015,r*.15))
# Closed-state geometry witnesses, before moving pivots.
witnesses={}
for p in seed['panels']:
 o=bpy.data.objects[p['mesh']]
 witnesses[p['id']]=[o.matrix_world@v.co for v in o.data.vertices]
newparts=[];removed=[]
for p,j in zip(seed['panels'],seed['joints']):
 k=p['id'];node=bpy.data.objects[p['node']]
 if k==1:
  p['translation']=reference['panels'][0]['translation'];p['angle']=reference['panels'][0]['angle']
  j['stroke']=Vector(p['translation']).length
  continue
 old_p=Vector(p['pivot']);tm=(p['ta']+p['tb'])/2
 pivot=surface.point(tm,.02,-.052 if EXTERNAL else -.023);axis=Vector(p['axis']).normalized()
 delta=Vector((0,-.06,0))+surface.frame(tm)[1]*.02;direction=delta.normalized();length=delta.length+.055
 # Retire the former central and telescopic mechanism, not the decorative shell.
 prefixes=[f'R82_R3_Guide_Sleeve_{k}_',f'R82_R3_Guide_Wiper_{k}_',f'R82_R3_Guide_Foot_{k}_',f'R82_R3_Slider_Rod_{k}_',f'R82_R3_Crosshead_{k:02d}',f'R82_R3_Rotating_Pin_{k:02d}',f'R82_R3_Pin_Stop_{k}_',f'R82_R5_Cover_Pad_{k}_',f'R82_R5_Short_Rotor_Ear_{k}_',f'I84_ExtensionTube_{k}_',f'I84_ExtensionSeal_{k}_']
 for ob in list(bpy.data.objects):
  if ob.name.startswith(tuple(prefixes)):
   removed.append(ob.name);bpy.data.objects.remove(ob,do_unlink=True)
 old_stage=bpy.data.objects.get(f'I84_TelescopeStage_{k:02d}')
 if old_stage:remove(old_stage)
 # Shift only object-local positions to keep every cosmetic mesh in its exact
 # closed world position under the new pivot. No vertex fitting by eye.
 for child in list(node.children):child.location+=old_p-pivot
 node.animation_data_clear();node.location=pivot;node.rotation_mode='QUATERNION';node.rotation_quaternion=Quaternion()
 carriage=bpy.data.objects[j['carriage']];carriage.animation_data_clear();carriage.location=pivot
 radius=j['rod_radius'];span=j['crosshead_span']
 for side in [-1,1]:
  tip=pivot+axis*span*side
  sleeve=P.sleeve(f'I85_Guide_{k}_{side}',radius*2.25,radius+.0015,length,root,tip-direction*length/2,'A_Nickel',direction)
  P.sleeve(f'I85_Wiper_{k}_{side}',radius*2.4,radius+.0008,.006,root,tip+direction*.001,'A_Rubber',direction)
  P.cylinder(f'I85_Rod_{k}_{side}',radius,length,carriage,axis*span*side-direction*(length/2-.004),'A_Nickel',direction,.0005)
  # Fitted rear shoe and formed short support into the back of the guide.
  tp=tm+side*.10;up=math.tau-.24
  fixed_shoe=shoe(f'I85_FixedShoe_{k}_{side}',tp,up,root,Vector(),.016)
  contact=surface.point(tp,up,.016)+surface.normal(tp,up)*.005
  back=tip-direction*(length-.014)
  mid=contact.lerp(back,.5)+surface.normal(tp,up)*.010
  bar(f'I85_SupportA_{k}_{side}',contact,mid,radius*1.20,root)
  bar(f'I85_SupportB_{k}_{side}',mid,back,radius*1.20,root)
  # Inner cover shoe and a short rotor arm carry the ceramic cover.
  covered=shoe(f'I85_CoverShoe_{k}_{side}',tp,.15,node,pivot,0. if EXTERNAL else .018)
  anchor=surface.point(tp,.15,0. if EXTERNAL else .018)+surface.normal(tp,.15)*(.010 if EXTERNAL else -.001)
  bar(f'I85_CoverEar_{k}_{side}',axis*span*side,anchor-pivot,radius*.80,node)
  P.sleeve(f'I85_RotorStop_{k}_{side}',radius*1.7,radius*1.01,.006,node,axis*side*(span+.012),'A_Bronze',axis)
  newparts.extend([sleeve.name,fixed_shoe.name,covered.name])
 P.sleeve(f'I85_Crosshead_{k:02d}',radius*2.55,radius*1.06,2*span+.018,carriage,(0,0,0),'A_Nickel',axis)
 P.cylinder(f'I85_HingePin_{k:02d}',radius,2*span+.024,node,(0,0,0),'A_Bronze',axis,.0005)
 p['pivot']=list(pivot);p['translation']=list(delta);p['angle']=math.pi/4
 j.update({'pivot':list(pivot),'slide_direction':list(direction),'stroke':delta.length,'guide_length':length,'minimum_rod_engagement':.055,'extension_nodes':[]})
bpy.context.view_layer.update()
error=0.
for p in seed['panels']:
 ob=bpy.data.objects[p['mesh']]
 error=max(error,max((ob.matrix_world@v.co-target).length for v,target in zip(ob.data.vertices,witnesses[p['id']])))
assert error<1e-6,error
def smooth(x):x=max(0,min(1,x));return x*x*x*(x*(x*6-15)+10)
for f in range(1,431):
 # Same spatial route for opening and return; no stagger between adjacent plates.
 phase=max(0,min(1,(f-85)/90)) if f<234 else 1-max(0,min(1,(f-234)/90))
 clear=smooth(phase/.25);turn=smooth((phase-.25)/.75)
 for p,j in zip(seed['panels'],seed['joints']):
  node=bpy.data.objects[p['node']];node.location=Vector(p['pivot'])+Vector(p['translation'])*clear
  node.rotation_quaternion=Quaternion(Vector(p['axis']),p['angle']*turn)
  node.keyframe_insert('location',frame=f);node.keyframe_insert('rotation_quaternion',frame=f)
  car=bpy.data.objects[j['carriage']];car.location=node.location;car.keyframe_insert('location',frame=f)
  for item in j.get('extension_nodes',[]):
   stage=bpy.data.objects[item['node']];stage.location=Vector(p['pivot'])+Vector(p['translation'])*clear*item['fraction'];stage.keyframe_insert('location',frame=f)
scene.frame_set(1);bpy.ops.wm.save_as_mainfile(filepath=str(SRC),compress=True)
# Bake only non-morph static modifiers into export copies.
for o in root.children_recursive:
 if o.type=='MESH' and o.modifiers and not o.data.shape_keys:
  ev=o.evaluated_get(bpy.context.evaluated_depsgraph_get());me=bpy.data.meshes.new_from_object(ev,preserve_all_data_layers=True,depsgraph=bpy.context.evaluated_depsgraph_get());o.modifiers.clear();o.data=me
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
ART=R/'app/assets/collection/art/I/r85_outer_hinge'
if EXTERNAL:ART=ART/'r2'
ART.mkdir(parents=True,exist_ok=True)
chambers=json.loads((R/'app'/seed['chamber_response_layout'].removeprefix('res://')).read_text());chambers['source_sha256']=sha(SRC);chambers['component_sha256']=sha(COMP)
(ART/'chamber_layout.json').write_text(json.dumps(chambers,indent=2)+'\n')
report={**seed,'source':SRC.relative_to(R).as_posix(),'source_sha256':sha(SRC),'component':COMP.relative_to(R).as_posix(),'component_sha256':sha(COMP),'parent_source':seed['source'],'motion_profile':'outer_edge_r85','motion_open_frames':[85,175],'motion_close_frames':[234,324],'closed_ceramic_world_error':error,'new_mechanism_parts':newparts,'removed_central_parts':removed,'chamber_response_layout':'res://'+(ART/'chamber_layout.json').relative_to(R/'app').as_posix(),'scope':'Real outer-edge guides, pins, fixed and moving shoes. Closed ceramic vertices preserved. Former internal guide ports still require closure/manifold treatment. Full assembly contacts and art acceptance pending.'}
(OUT/'build.json').write_text(json.dumps(report,indent=2)+'\n')
bpy.ops.wm.open_mainfile(filepath=str(SRC));scene=bpy.context.scene
try:
 pref=bpy.context.preferences.addons['cycles'].preferences;pref.compute_device_type='CUDA';pref.get_devices()
 for d in pref.devices:d.use=d.type=='CUDA'
 scene.cycles.device='GPU'
except:pass
scene.cycles.samples=40;scene.render.resolution_x=1000;scene.render.resolution_y=1100
for name,f in [('closed',1),('open',205)]:
 scene.frame_set(f);scene.render.filepath=str(OUT/(name+'.png'));bpy.ops.render.render(write_still=True)
print('R85_OUTER_HINGE_BUILT',error,flush=True)
