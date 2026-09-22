"""R82 r6 compact coordinated motion and separate old-music spatial fit study."""
import bpy,math,json,hashlib,sys
from pathlib import Path
from mathutils import Vector,Quaternion,Matrix
from mathutils.bvhtree import BVHTree
R=Path(__file__).resolve().parents[2];IN=R/'review/I_refinement/nautilus_reset_r82/mechanism_r5'
SADDLE_CLEARANCE='--saddle-clearance' in sys.argv
variant='mechanism_r7' if SADDLE_CLEARANCE else 'mechanism_r6'
OUT=R/'review/I_refinement/nautilus_reset_r82'/variant;OUT.mkdir(parents=True,exist_ok=True)
SRC=R/('blender/collection/I_nautilus_reset_r82_'+variant+'.blend');assert not SRC.exists()
d=json.loads((IN/'build.json').read_text());choice=json.loads((IN/'opening_search_compact.json').read_text())['first_feasible'];assert choice
if SADDLE_CLEARANCE:
 choice['translations'][1][1]=-.20
 choice['translations'][1][2]=.060
 choice['saddle_revision']='02 lower return cover rises .060 while leaving the saddle, instead of descending into its cheek.'
bpy.ops.wm.open_mainfile(filepath=str(R/d['source']));s=bpy.context.scene;s.frame_set(1)
col=bpy.data.collections['R82_NEW_FORM'];root=bpy.data.objects['R82_COIL_ROOT']
def cylinder(r,length,center,axis):
 bpy.ops.mesh.primitive_cylinder_add(vertices=64,radius=r,depth=length);o=bpy.context.object;o.location=center;o.rotation_mode='QUATERNION';o.rotation_quaternion=Vector(axis).to_track_quat('Z','Y');return o
def cut(o,tool):
 bpy.context.view_layer.objects.active=o;mod=o.modifiers.new('Current guide port','BOOLEAN');mod.operation='DIFFERENCE';mod.solver='EXACT';mod.object=tool
 bpy.ops.object.modifier_move_to_index(modifier=mod.name,index=0);bpy.ops.object.modifier_apply(modifier=mod.name);bpy.data.objects.remove(tool,do_unlink=True)
for p,j,D in zip(d['panels'],d['joints'],choice['translations']):
 k=p['id'];P=Vector(p['pivot']);A=Vector(p['axis']);D=Vector(D);S=D.normalized();L=D.length+.055
 p['translation']=list(D);p['angle']*=choice['inner_angle_multiplier'] if k==1 else choice['angle_multiplier']
 j['stroke']=D.length;j['slide_direction']=list(S);j['guide_length']=L;j['minimum_rod_engagement']=.055
 for side in [-1,1]:
  tip=P+A*j['crosshead_span']*side
  sleeve=bpy.data.objects[f'R82_R3_Guide_Sleeve_{k}_{side}'];bare=max(v.co.z for v in sleeve.data.vertices)-min(v.co.z for v in sleeve.data.vertices)
  sleeve.location=tip-S*L/2;sleeve.scale.z=L/bare;sleeve.rotation_quaternion=S.to_track_quat('Z','Y')
  for stem,offset in [('Guide_Wiper',.001),('Guide_Foot',-(L-.009))]:
   o=bpy.data.objects[f'R82_R3_{stem}_{k}_{side}'];o.location=tip+S*offset;o.rotation_quaternion=S.to_track_quat('Z','Y')
  rod=bpy.data.objects[f'R82_R3_Slider_Rod_{k}_{side}'];bare=max(v.co.z for v in rod.data.vertices)-min(v.co.z for v in rod.data.vertices)
  rod.scale.z=L/bare;rod.location=A*j['crosshead_span']*side-S*(L/2-.005);rod.rotation_quaternion=S.to_track_quat('Z','Y')
# Restore unperforated fixed skins. Old port holes must not accumulate.
with bpy.data.libraries.load(str(R/'blender/collection/I_nautilus_reset_r82_mechanism_r3b.blend'),link=False)as(src,dst):
 dst.objects=['R82_Fixed_Rear_Keel','R82_Acoustic_Chamber_Liner']
for ref in dst.objects:
 name=ref.name.split('.')[0];bpy.data.objects[name].data=ref.data.copy();bpy.data.objects.remove(ref,do_unlink=True)
ports=[]
for name in ['R82_Fixed_Rear_Keel','R82_Acoustic_Chamber_Liner']:
 o=bpy.data.objects[name];bpy.context.view_layer.update()
 ev=o.evaluated_get(bpy.context.evaluated_depsgraph_get());me=ev.to_mesh();me.calc_loop_triangles()
 tree=BVHTree.FromPolygons([o.matrix_world@v.co for v in me.vertices],[tuple(t.vertices)for t in me.loop_triangles],all_triangles=True);ev.to_mesh_clear()
 for j in d['joints']:
  P=Vector(j['pivot']);A=Vector(j['axis']);S=Vector(j['slide_direction']);L=j['guide_length']
  for side in [-1,1]:
   tip=P+A*j['crosshead_span']*side;start=tip-S*(L+.05);length=L+j['stroke']+.10
   hit=tree.ray_cast(start,S,length)
   if hit[0] is None:continue
   rad=j['rod_radius']*2.25+.002;cut(o,cylinder(rad,length,start+S*length/2,S))
   ports.append({'body':name,'id':j['id'],'side':side,'radius':rad,'hit':list(hit[0])})
def smooth(x):x=max(0,min(1,x));return x*x*x*(x*(x*6-15)+10)
for f in range(1,301):
 s.frame_set(f)
 for p,j in zip(d['panels'],d['joints']):
  k=p['id'];t=(f-25-(k-1)*1.5)/82 if f<150 else 1-(f-174-(6-k)*1.5)/82;t=max(0,min(1,t));lift=smooth(t/.30);turn=smooth((t-.30)/.70)
  o=bpy.data.objects[p['node']];o.location=Vector(p['pivot'])+Vector(p['translation'])*lift;o.rotation_quaternion=Quaternion(Vector(p['axis']),p['angle']*turn)
  o.keyframe_insert('location',frame=f);o.keyframe_insert('rotation_quaternion',frame=f)
  car=bpy.data.objects[j['carriage']];car.location=o.location;car.keyframe_insert('location',frame=f)
s.frame_set(1)
bpy.ops.wm.save_as_mainfile(filepath=str(SRC),compress=True)
d.update({'source_parent':d['source'],'source':SRC.relative_to(R).as_posix(),'source_sha256':hashlib.sha256(SRC.read_bytes()).hexdigest(),'current_ports':ports,'status':'independent_refinement_candidate_pending_full_checks','compact_opening':choice})
(OUT/'build.json').write_text(json.dumps(d,indent=2)+'\n')
try:
 pref=bpy.context.preferences.addons['cycles'].preferences;pref.compute_device_type='CUDA';pref.get_devices()
 for dv in pref.devices:dv.use=dv.type=='CUDA'
 s.cycles.device='GPU'
except:pass
s.cycles.samples=48;s.render.resolution_x=1000;s.render.resolution_y=1100;cam=s.camera
def view(name,frame,loc=(-4,-7,3.65),target=(0,0,1.57),scale=4.1):
 s.frame_set(frame);cam.location=loc;cam.rotation_euler=(Vector(target)-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.ortho_scale=scale
 s.render.filepath=str(OUT/(name+'.png'));bpy.ops.render.render(write_still=True)
view('closed',1);view('open',145)
print('R82_R6_BODY_READY',flush=True)
# Preserve the body source above. This next scene is only a trial fit of actual
# existing mouth/optics; it is not certified or wired to music playback.
spec=json.loads((R/'review/I_refinement/part_a_mouth/shutter_r2/collar_clamps/build.json').read_text())
assert hashlib.sha256((R/spec['source']).read_bytes()).hexdigest()==spec['source_sha256']
s.frame_set(1)
with bpy.data.libraries.load(str(R/spec['source']),link=False)as(src,dst):dst.collections=['MODULE_IAM']
s.collection.children.link(dst.collections[0]);mouth_root=bpy.data.objects['IAM_MODULE']
pars=d['shape_parameters'];theta=pars['END'];r=pars['RMAX'];grow=pars['GROW']
C=Vector(pars['SHIFT'])+Vector((r*math.cos(theta),-.44,r*math.sin(theta)))
front=Vector((r*(grow*math.cos(theta)-math.sin(theta)),-.44*3/1.25,r*(grow*math.sin(theta)+math.cos(theta)))).normalized()
back=-front;up=(Vector((0,0,1))-back*back.z).normalized();right=up.cross(back).normalized()
basis=Matrix((right,up,back)).transposed();M=basis.to_4x4();M.translation=C+front*.018
scale=.64;M=M@Matrix.Diagonal((scale,scale,scale,1.))
mouth_root.matrix_world=M
layout=json.loads((R/'app/assets/collection/art/I/desktop_optics_r60/score_layout.json').read_text())
with bpy.data.libraries.load(str(R/layout['source']),link=False)as(src,dst):dst.objects=[n for n in src.objects if n.startswith('I_')]
for o in dst.objects:s.collection.objects.link(o)
optics=next(o for o in dst.objects if o.name=='I_MusicOptics');optics.parent=bpy.data.objects['IAM_Mouth']
# Real engraving alpha, fully transparent between glyphs. Static fit proof only.
sheet=bpy.data.objects['I_MoonlightStaff']
ma=bpy.data.materials.new('R82_Real_Score_Fit_Only');ma.use_nodes=True;n=ma.node_tree.nodes;n.clear()
out=n.new('ShaderNodeOutputMaterial');mix=n.new('ShaderNodeMixShader');tr=n.new('ShaderNodeBsdfTransparent');em=n.new('ShaderNodeEmission');em.inputs[0].default_value=(1,.77,.35,1);em.inputs[1].default_value=2
tex=n.new('ShaderNodeTexImage');tex.image=bpy.data.images.load(str(R/'app/assets/collection/art/I/moonlight_candidate/score/m1.0/000.png'))
links=ma.node_tree.links;links.new(tex.outputs['Alpha'],mix.inputs[0]);links.new(tr.outputs[0],mix.inputs[1]);links.new(em.outputs[0],mix.inputs[2]);links.new(mix.outputs[0],out.inputs[0])
sheet.data.materials.clear();sheet.data.materials.append(ma)
for name in [layout['scanner']['line']]+[v['ray']for v in layout['scanner']['tips']]:
 o=bpy.data.objects.get(name)
 if o:o.hide_render=True # Static fit has no timing-driven scan effect.
bpy.context.view_layer.update()
mouth_meshes=[o for o in mouth_root.children_recursive if o.type=='MESH']
vs=[o.matrix_world@v.co for o in mouth_meshes for v in o.data.vertices]
bbox={axis:[min(v[k]for v in vs),max(v[k]for v in vs)]for k,axis in enumerate(['x','y','z'])}
fit={'body_source':d['source'],'old_mouth_source':spec['source'],'old_mouth_sha256':spec['source_sha256'],'scale':scale,'old_runtime_scale':.7,'mouth_center':list(C),'mouth_front':list(front),'mouth_bbox':bbox,'score_world_nominal_width':layout['width']*scale,'score_world_nominal_height':layout['height']*scale,'scope':'Actual old mouth and optical geometry statically trial-positioned. Static real score alpha only, no playback; all mouth-shell collisions, leaf travel and desktop readability remain to inspect. Original music manifests/audio/controller not changed.'}
(OUT/'music_spatial_fit.json').write_text(json.dumps(fit,indent=2)+'\n')
fitfile=R/('blender/collection/I_nautilus_reset_r82_music_fit_r2.blend' if SADDLE_CLEARANCE else 'blender/collection/I_nautilus_reset_r82_music_fit_r1.blend');assert not fitfile.exists()
s.frame_set(1);bpy.ops.wm.save_as_mainfile(filepath=str(fitfile),compress=True)
view('music_fit_closed',1);view('music_fit_open',145)
print('R82_MUSIC_FIT_STUDY_READY',flush=True)
