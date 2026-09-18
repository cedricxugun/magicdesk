"""Split deep ceramic receiver along actual helical shell sectors; keep mouth anchored."""
import bpy,bmesh,json,math,sys,hashlib,ast
from pathlib import Path
from mathutils import Matrix,Vector,Quaternion
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(Path(__file__).parent))
from geometry import reparent_preserving_world
BASE=ROOT/'review/I_refinement/opening_r15';prior=json.loads((BASE/'build.json').read_text());SOURCE=ROOT/prior['source'];TARGET=ROOT/'blender/collection/I_receiver_r16.blend';OUT=ROOT/'review/I_refinement/receiver_r16';OUT.mkdir(parents=True,exist_ok=True)
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();assert sha(SOURCE)==prior['source_sha256']
if TARGET.exists():
 old=json.loads((OUT/'build.json').read_text());assert sha(TARGET)==old['source_sha256'],'Unrecorded R16 edits';(TARGET.parent/'checkpoints'/('I-receiver-'+sha(TARGET)[:12]+'.blend')).write_bytes(TARGET.read_bytes())
bpy.ops.wm.open_mainfile(filepath=str(SOURCE));scene=bpy.context.scene;scene.frame_set(1);bpy.context.view_layer.update();root=bpy.data.objects['IC11_MODULE'];body=bpy.data.objects['IC11_ConchBody'];mouth=bpy.data.objects['IH1_Mouth'];col=bpy.data.collections.new('I_HELICAL_RECEIVER_R16');scene.collection.children.link(col)
recipe=ast.parse((ROOT/'blender/collection/build_i_conch_r13.py').read_text());ns={'Vector':Vector,'math':math};exec(compile(ast.Module(body=[n for n in recipe.body if isinstance(n,ast.FunctionDef) and n.name in ['center','radius']],type_ignores=[]),'<shape>','exec'),ns);center=ns['center']
def normalize(o):
 bm=bmesh.new();bm.from_mesh(o.data);bmesh.ops.remove_doubles(bm,verts=list(bm.verts),dist=1e-7);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(o.data);bm.free()
def clip(o,z,front):
 bm=bmesh.new();bm.from_mesh(o.data);r=bmesh.ops.bisect_plane(bm,geom=list(bm.verts)+list(bm.edges)+list(bm.faces),plane_co=Vector((0,0,z)),plane_no=Vector((0,0,1)),dist=1e-7,clear_outer=front,clear_inner=not front);edges=[e for e in r['geom_cut'] if isinstance(e,bmesh.types.BMEdge) and e.is_boundary]
 if edges:bmesh.ops.holes_fill(bm,edges=edges,sides=0)
 bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(o.data);bm.free()
def volume(o):
 bm=bmesh.new();bm.from_mesh(o.data);v=bm.calc_volume(signed=True);boundary=sum(not e.is_manifold for e in bm.edges);bm.free();return v,boundary
lower=bpy.data.objects['IC11_RolledThroatPorcelain_Lower'];lower.data=lower.data.copy();lower_neck=bpy.data.objects.new('IR16_LowerNeckSource',lower.data.copy());col.objects.link(lower_neck);lower_neck.parent=mouth;lower_neck.matrix_basis=Matrix.Identity(4)
clip(lower,.0145,True);clip(lower_neck,.0155,False)
upper_neck=bpy.data.objects[prior['fixed_upper_neck']];old_volume=sum(volume(o)[0] for o in [lower_neck,upper_neck]);neckpieces=[]
def partition(index):
 n=192;nu=10;v=[];f=[];stride=n+1
 for radial in [.0015,2.4]:
  for u in range(nu+1):
   for k in range(n+1):
    theta=k*math.tau/n;a=math.pi/2-theta;lo=(index-1+k/n)/5.;hi=(index+k/n)/5.
    if index==0:lo=-.30
    if index==5:hi=1.30
    q=lo+(hi-lo)*u/nu;c=center(max(0,min(1,q)));c.z=1.16+2.26*q;v.append(c+Vector((radial*math.cos(a),radial*.8*math.sin(a),0)))
 size=(nu+1)*stride
 for layer in [0,1]:
  for j in range(nu):
   for k in range(n):
    a=layer*size+j*stride+k;f.append((a,a+1,a+stride+1,a+stride))
 boundary=list(range(stride))+[j*stride+n for j in range(1,nu+1)]+[nu*stride+k for k in range(n-1,-1,-1)]+[j*stride for j in range(nu-1,0,-1)]
 for a,c in zip(boundary,boundary[1:]+boundary[:1]):f.append((a,c,c+size,a+size))
 data=bpy.data.meshes.new('IR16_Partition');data.from_pydata(v,[],f);o=bpy.data.objects.new('IR16_Partition'+str(index),data);col.objects.link(o);o.parent=body;normalize(o);return o
for i,row in enumerate(prior['shells']):
 tool=partition(i);bpy.context.view_layer.update()
 for src in [lower_neck,upper_neck]:
  o=src.copy();o.data=src.data.copy();o.name='IR16_Neck_'+str(i)+('_Lower' if src==lower_neck else '_Upper');col.objects.link(o);bpy.context.view_layer.update();bpy.context.view_layer.objects.active=o
  mod=o.modifiers.new('Own helical shell receiver portion','BOOLEAN');mod.operation='INTERSECT';mod.solver='EXACT';mod.object=tool;bpy.ops.object.modifier_apply(modifier=mod.name);normalize(o)
  if len(o.data.polygons)==0:bpy.data.objects.remove(o,do_unlink=True);continue
  reparent_preserving_world(o,bpy.data.objects[row['node']]);v,n=volume(o);neckpieces.append({'name':o.name,'shell':row['node'],'volume':v,'nonmanifold_edges':n})
 bpy.data.objects.remove(tool,do_unlink=True)
new_volume=sum(r['volume'] for r in neckpieces);assert abs(new_volume-old_volume)/old_volume<.005,(new_volume,old_volume)
for o in [lower_neck,upper_neck]:bpy.data.objects.remove(o,do_unlink=True)
# A small front-collar disengagement is tested as a bounded guide motion; no full-mouth translation.
release=bpy.data.objects.new('IR16_LowerLipRelease',None);col.objects.link(release);release.parent=mouth;bpy.context.view_layer.update();reparent_preserving_world(lower,release)
from geometry import smooth,pose,C
for frame in range(1,362):
 sec=(frame-1)/30;amount=smooth((sec-.5)/3) if sec<6 else 1-smooth((sec-7)/3);phase=smooth(amount/.22)
 release.location=(0,-.035*phase,-.08*phase);release.keyframe_insert('location',frame=frame)
new_release={'name':release.name,'kind':'release','home_matrix':[list(r) for r in Matrix.Identity(4)],'offset':[0,-.035,-.08],'order':-1,'phase_end':.22}
# Existing R15 motion is retained, including the provisional support envelopes.
scene.frame_set(1);bpy.context.view_layer.update();bpy.ops.wm.save_as_mainfile(filepath=str(TARGET));bpy.ops.object.select_all(action='DESELECT')
for o in [root]+list(root.children_recursive):o.select_set(True)
bpy.context.view_layer.objects.active=root;component=ROOT/'app/assets/collection/components/I_receiver_r16.glb';bpy.ops.export_scene.gltf(filepath=str(component),export_format='GLB',use_selection=True,export_apply=False,export_animations=False,export_extras=True)
data=json.loads((ROOT/'app/assets/collection/i_opening_rig_r15.json').read_text());runtime={k:v for k,v in new_release.items() if k!='home_matrix'};runtime['home']=pose(Matrix.Identity(4));runtime['offset']=list(C.to_3x3()@Vector(new_release['offset']));data['rig'].insert(0,runtime);(ROOT/'app/assets/collection/i_receiver_rig_r16.json').write_text(json.dumps(data,indent=2)+'\n')
poses={}
for frame in [1,31,61,91,121,181,241,301,361]:
 scene.frame_set(frame);bpy.context.view_layer.update();poses[str(frame)]={r['name']:pose(bpy.data.objects[r['name']].matrix_world) for r in data['rig']}
(OUT/'source_poses.json').write_text(json.dumps(poses,indent=2)+'\n')
result=dict(prior);result.update(source=str(TARGET.relative_to(ROOT)),source_sha256=sha(TARGET),component=str(component.relative_to(ROOT)),component_sha256=sha(component),input_source_sha256=sha(SOURCE),neck_pieces=neckpieces,neck_volume_before=old_volume,neck_volume_after=new_volume,lower_release=new_release,fixed_upper_neck=None,scope='R15 shape preserved with deep ceramic neck portions following their helical shells. Small lower front lip release is a layout candidate; mechanical guides and full clearance/art acceptance pending.')
result['rig']=prior['rig']+[{'name':release.name,'kind':'lower_lip','home_matrix':new_release['home_matrix']}];result['release_rig']=prior['release_rig']+[new_release]
(OUT/'build.json').write_text(json.dumps(result,indent=2)+'\n');print('I_RECEIVER_R16_BUILT',len(neckpieces),'volume retained',new_volume/old_volume,flush=True)
