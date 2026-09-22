"""R86: restore the visible liner using the actual cartridge envelope,
retain functional central guides, and dress receiver metal below the liner."""
import bpy,bmesh,json,math,hashlib,sys
from pathlib import Path
from mathutils import Vector
R=Path(__file__).resolve().parents[2];sys.path.insert(0,str(Path(__file__).parent))
from i_r82_coil_surface import CoilSurface
import i_machined_geometry as P
args=sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else []
revision=next((a.split('=',1)[1] for a in args if a.startswith('--revision=')),'r1')
assert revision in ['r1','r2','r3','r4']
wide_finish=revision in ['r3','r4']
BASE=R/'review/I_refinement/nautilus_reset_r82';OUT=BASE/'finish_r86'
if revision!='r1':OUT=OUT/revision
OUT.mkdir(parents=True,exist_ok=True)
old=json.loads((BASE/'outer_hinge_r2/build.json').read_text())
pars=json.loads((BASE/'mechanism_r9/build.json').read_text())['shape_parameters'];surface=CoilSurface(pars)
SRC=R/f'blender/collection/I_r86_inner_finish_{revision}.blend';COMP=R/f'app/assets/collection/components/I_r86_inner_finish_{revision}.glb';assert not SRC.exists()and not COMP.exists()
bpy.ops.wm.open_mainfile(filepath=str(R/old['source']));scene=bpy.context.scene;scene.frame_set(1)
root=bpy.data.objects['R82_COIL_ROOT'];liner=bpy.data.objects['R82_Acoustic_Chamber_Liner'];rear=bpy.data.objects['R82_Fixed_Rear_Keel'];col=bpy.data.collections['R82_NEW_FORM']
P.configure(col)
baseline=[]
for ob in [liner,rear]:
 bm=bmesh.new();bm.from_mesh(ob.data);baseline.append({'name':ob.name,'nonmanifold':sum(not e.is_manifold for e in bm.edges),'minimum_face_area':min(f.calc_area()for f in bm.faces)});bm.free()
print('R86_BASELINE_TOPOLOGY',baseline,flush=True)
def create(name,vs,fs,parent=root):
 me=bpy.data.meshes.new(name+'Mesh');me.from_pydata(vs,[],fs);me.update();o=bpy.data.objects.new(name,me);col.objects.link(o);o.parent=parent
 bm=bmesh.new();bm.from_mesh(me);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(me);bm.free()
 return o
def boolean(obj,tool,operation='DIFFERENCE'):
 bpy.context.view_layer.update();bpy.context.view_layer.objects.active=obj
 m=obj.modifiers.new('Fitted receiver space','BOOLEAN');m.operation=operation;m.solver='EXACT';m.object=tool
 bpy.ops.object.modifier_move_to_index(modifier=m.name,index=0);bpy.ops.object.modifier_apply(modifier=m.name);bpy.data.objects.remove(tool,do_unlink=True)
def grid_shell(name,ta,tb,ua,ub,nt,nu,layer_point):
 vs=[];fs=[];stride=nu+1;count=(nt+1)*stride
 for side in [0,1]:
  for i in range(nt+1):
   t=ta+(tb-ta)*i/nt
   for j in range(nu+1):vs.append(layer_point(t,ua+(ub-ua)*j/nu,side))
 for side in [0,1]:
  for i in range(nt):
   for j in range(nu):
    k=side*count+i*stride+j;q=(k,k+stride,k+stride+1,k+1);fs.append(q if side==0 else q[::-1])
 edge=list(range(stride))+[i*stride+nu for i in range(1,nt+1)]+[nt*stride+j for j in range(nu-1,-1,-1)]+[i*stride for i in range(nt-1,0,-1)]
 for i,a in enumerate(edge):
  b=edge[(i+1)%len(edge)];fs.append((a,b,b+count,a+count))
 return create(name,vs,fs)
def smooth(a,b,x):
 v=max(0.,min(1.,(x-a)/(b-a)));return v*v*(3.-2.*v)
bpy.context.view_layer.update();mouth_inverse=bpy.data.objects['IAM_Mouth'].matrix_world.inverted()
def liner_point(t,u,side):
 inset,thick=surface.wall(t);p=surface.point(t,u,inset+thick*side)
 if revision=='r4' and t>surface.T-.7:
  ref=surface.point(t,u,inset);local=mouth_inverse@ref;angle=math.atan2(local.y,local.x)
  # A formed return flares over the cartridge seat instead of leaving a cut
  # slit. It stays inside the existing ceramic wall, to be contact-checked.
  weight=smooth(-.42,-.26,angle)*(1.-smooth(.28,.48,angle))*smooth(.09,.15,local.z)*(1.-smooth(.255,.30,local.z))
  p+=surface.normal(t,u)*(.012*weight)
 return p
new=grid_shell('R86_Liner',.01,surface.T,.06,math.pi-.06,600,96,liner_point)
for ma in liner.data.materials:new.data.materials.append(ma)
liner.data=new.data;bpy.data.objects.remove(new,do_unlink=True)
for f in liner.data.polygons:f.use_smooth=True
def rear_point(t,u,side):
 r=surface.frame(t)[0];remaining=min(pars['RAD'],pars['DEPTH'])*r-.016
 thickness=surface.smooth_min(.022,remaining-.002,.001)
 return surface.point(t,u,.016+max(.001,thickness)*side)
rear_bounds=(math.pi+.003,math.tau-.003) if wide_finish else (math.pi-.04,math.tau+.04)
new=grid_shell('R86_RearSkin',.01,surface.T,*rear_bounds,600,96,rear_point)
for ma in rear.data.materials:new.data.materials.append(ma)
rear.data=new.data;bpy.data.objects.remove(new,do_unlink=True)
for f in rear.data.polygons:f.use_smooth=True
# The old internal guide ports 02-06 are not recreated. 01 still operates.
for j in old['joints'][:1]:
 guide_pivot=Vector(j['pivot']);A=Vector(j['axis']);D=Vector(j['slide_direction']);L=j['guide_length']
 for side in [-1,1]:
  start=guide_pivot+A*j['crosshead_span']*side-D*(L+.05);length=L+j['stroke']+.10
  bpy.ops.mesh.primitive_cylinder_add(vertices=96,radius=j['rod_radius']*2.25+.002,depth=length)
  tool=bpy.context.object;tool.location=start+D*length/2;tool.rotation_mode='QUATERNION';tool.rotation_quaternion=D.to_track_quat('Z','Y')
  other=tool.copy();other.data=tool.data.copy();col.objects.link(other);boolean(liner,tool);boolean(rear,other)
# Retain the authored twelve true openings.
vs=[];fs=[]
for row in old['new_cells']:
 c=row['surface_chart'];N=96;NR=8;layers=[]
 def point(s,a,h):
  t=c['t']+c['half_t']*s*(math.cos(a)+.10*math.sin(a)**2);u=c['u']+c['half_u']*s*math.sin(a)
  return surface.point(t,u)+surface.normal(t,u)*h
 for h in [-.036,.026]:
  rings=[[len(vs)]];vs.append(point(0,0,h))
  for ri in range(1,NR+1):
   rings.append(list(range(len(vs),len(vs)+N)));vs.extend(point(.915*ri/NR,math.tau*k/N,h)for k in range(N))
  layers.append(rings)
 for side,rings in enumerate(layers):
  for k in range(N):
   tri=(rings[0][0],rings[1][k],rings[1][(k+1)%N]);fs.append(tri if side==0 else tri[::-1])
  for ri in range(1,NR):
   for k in range(N):
    q=(rings[ri][k],rings[ri+1][k],rings[ri+1][(k+1)%N],rings[ri][(k+1)%N]);fs.append(q if side==0 else q[::-1])
 for k in range(N):fs.append((layers[0][-1][k],layers[0][-1][(k+1)%N],layers[1][-1][(k+1)%N],layers[1][-1][k]))
boolean(liner,create('R86_CellTools',vs,fs))
# Carrier ears require the larger pocket only at their actual depth.
profile=[(-.16,.851),(-.09,.851),(.20,.856),(.235,.863),(.25,.854),(.43,.848),(.48,.62),(.62,.50)]
sector=None
if revision in ['r2','r3','r4']:
 evidence='gap_sector_wide.json' if wide_finish else 'gap_sector_envelope.json'
 envelope=json.loads((BASE/'finish_r86'/evidence).read_text(encoding='utf-8'))
 assert max(row['maximum_radius'] for row in envelope['samples'])<(.69 if wide_finish else .58)
 sector={'angle':[-.3,-.2,.5,.65] if wide_finish else [.1,.2,.5,.6],'depth':[.245,.27,.43,.45],'radius':.78,'measured_core_bound':max(row['maximum_radius'] for row in envelope['samples']),'evidence':'review/I_refinement/nautilus_reset_r82/finish_r86/'+evidence}
def profile_radius(z):
 for (za,ra),(zb,rb) in zip(profile,profile[1:]):
  if za<=z<=zb:return ra+(rb-ra)*(z-za)/(zb-za)
 raise ValueError(z)
depths=sorted(set([z for z,_ in profile]+([.245,.25,.255,.26,.265,.27,.3,.34,.38,.42,.435,.44,.445,.45] if sector else [])))
vs=[];fs=[];N=384 if sector else 192
for z in depths:
 r=profile_radius(z)
 for i in range(N):
  a=math.tau*i/N;radius=r
  if sector:
   angle=a if a<=math.pi else a-math.tau
   aa,ab,ac,ad=sector['angle']
   weight=smooth(aa,ab,angle)*(1.-smooth(ac,ad,angle))*smooth(.245,.27,z)*(1.-smooth(.43,.45,z))
   radius=r+(min(r,sector['radius'])-r)*weight
  vs.append((radius*math.cos(a),radius*math.sin(a),z))
for j in range(len(depths)-1):
 for i in range(N):fs.append((j*N+i,j*N+(i+1)%N,(j+1)*N+(i+1)%N,(j+1)*N+i))
fs +=[tuple(range(N-1,-1,-1)),tuple((len(depths)-1)*N+i for i in range(N))]
tool=create('R86_ReceiverEnvelope',vs,fs,parent=bpy.data.objects['IAM_Mouth'])
other=tool.copy();other.data=tool.data.copy();col.objects.link(other);boolean(liner,tool);boolean(rear,other)
# Keep the thick receiver casting as a valid separate manufactured part instead
# of fusing it into the thin rear skin (the previous fused skin was nonmanifold).
receiver_root=bpy.data.objects['I83_ReceiverRoot']
receiver=P.sleeve('I86_ReceiverCasting',.902,.862,.036,receiver_root,(0,0,.248),'A_Nickel')
for row in old['receiver_fasteners']:
 station=bpy.data.objects[row['station']];r=row['stud_radius'];k=row['id']
 pad=P.box('R86_PadTool_'+str(k),(.066,.021,.018),station,(r+.012,0,.239),'A_Nickel',.002)
 boolean(receiver,pad,'UNION')
 tool=P.cylinder('R86_PocketTool',.0029,.016,station,(r,0,.236),'A_Dark',bevel=0)
 boolean(receiver,tool)
# Remove the metal tongue that protruded through the restored gold wall.
# Only the terminal FRONT domain is trimmed; the rear skin and mounting zone remain.
def trim_point(t,u,side):
 inset,thick=surface.wall(t);p=surface.point(t,u,inset+thick+.001)
 return p+surface.normal(t,u)*(.18 if side else 0.)
trim_bounds=(-.08,math.pi+.08) if wide_finish else (.055,math.pi-.055)
trim=grid_shell('R86_ReceiverDressing',surface.T-(.80 if wide_finish else .60),surface.T+.005,*trim_bounds,96,96,trim_point)
boolean(receiver,trim)
validation=[]
for ob in [liner,rear,receiver]:
 changed=ob.data.validate(verbose=True,clean_customdata=False)
 bm=bmesh.new();bm.from_mesh(ob.data)
 bmesh.ops.dissolve_degenerate(bm,dist=1e-7,edges=list(bm.edges));bm.to_mesh(ob.data)
 row={'name':ob.name,'automatic_repairs':changed,'nonmanifold':sum(not e.is_manifold for e in bm.edges),'degenerate_faces':sum(f.calc_area()<1e-12 for f in bm.faces),'volume':bm.calc_volume(signed=True),'cleanup_edge_length_limit':1e-7}
 bm.free();validation.append(row)
assert all(not v['automatic_repairs'] and v['nonmanifold']==0 and v['volume']>0 for v in validation),validation
scene.frame_set(1);bpy.ops.wm.save_as_mainfile(filepath=str(SRC),compress=True)
# Export static evaluated surfaces, preserving all twelve membrane morphs.
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
ART=R/'app/assets/collection/art/I/r86_inner_finish';ART.mkdir(exist_ok=True)
if revision!='r1':ART=ART/revision;ART.mkdir(exist_ok=True)
layout=json.loads((R/'app'/old['chamber_response_layout'].removeprefix('res://')).read_text());layout['source_sha256']=sha(SRC);layout['component_sha256']=sha(COMP)
(ART/'chamber_layout.json').write_text(json.dumps(layout,indent=2)+'\n')
d={**old,'source':SRC.relative_to(R).as_posix(),'source_sha256':sha(SRC),'component':COMP.relative_to(R).as_posix(),'component_sha256':sha(COMP),'parent_source':old['source'],'chamber_response_layout':'res://'+(ART/'chamber_layout.json').relative_to(R/'app').as_posix(),'liner_receiver_profile':profile,'surface_validation':validation,'scope':'Restored terminal gold wall with tighter measured-profile receiver clearance; retired front guide ports 02-06 removed, central guide ports retained; protruding receiver stock dressed. New full core/fixture clearance and art verification pending.'}
d['receiver_sector_clearance']=sector
d['rear_angular_domain']=rear_bounds
d['formed_liner_return']={'maximum_normal_shift':.012,'angle':[-.42,-.26,.28,.48],'depth':[.09,.15,.255,.30]} if revision=='r4' else None
(OUT/'build.json').write_text(json.dumps(d,indent=2)+'\n')
bpy.ops.wm.open_mainfile(filepath=str(SRC));scene=bpy.context.scene;scene.frame_set(205);cam=scene.camera
try:
 pref=bpy.context.preferences.addons['cycles'].preferences;pref.compute_device_type='CUDA';pref.get_devices()
 for dv in pref.devices:dv.use=dv.type=='CUDA'
 scene.cycles.device='GPU'
except:pass
scene.cycles.samples=48;scene.render.resolution_x=1000;scene.render.resolution_y=1100
scene.render.filepath=str(OUT/'open_repaired.png');bpy.ops.render.render(write_still=True)
print('R86_INNER_FINISH_BUILT',d['source_sha256'],validation,flush=True)
