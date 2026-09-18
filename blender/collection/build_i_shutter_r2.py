"""Restore the reference's asymmetric eyelid silhouette. REST component, no fake OPEN animation."""
import bpy,bmesh,json,math,hashlib,sys
from pathlib import Path
from mathutils import Vector,Quaternion
from mathutils.bvhtree import BVHTree
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(Path(__file__).parent))
from geometry import Builder
OUT=ROOT/'review/I_refinement/part_a_mouth/shutter_r2';OUT.mkdir(parents=True,exist_ok=True)
report=json.loads((ROOT/'review/I_refinement/part_a_mouth/build.json').read_text());src=ROOT/report['source']
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
assert sha(src)==report['source_sha256']
bpy.ops.wm.open_mainfile(filepath=str(src))
target=ROOT/'blender/collection/I_part_a_shutter_r2.blend'
if target.exists():
 prev=json.loads((OUT/'build.json').read_text());assert sha(target)==prev['source_sha256'],'Unrecorded shutter edits'
 (target.parent/'checkpoints'/('I-shutter-r2-'+sha(target)[:12]+'.blend')).write_bytes(target.read_bytes())
mouth=bpy.data.objects['IAM_Mouth'];col=bpy.data.collections['MODULE_IAM']
remove=set()
for o in bpy.data.objects:
 if any(s in o.name for s in ['IAM_IrisLeaf','IAM_IrisCam','IrisPivotPin','CamSupportRoller']):remove.add(o);remove.update(o.children_recursive)
for o in remove:bpy.data.objects.remove(o,do_unlink=True)
mat=bpy.data.materials['Collection_A_LeafNickel'];nickel=bpy.data.materials['Collection_A_Nickel'];dark=bpy.data.materials['Collection_A_Dark']
# The liner is blackened metal, not a bright mirror washing out the shutter silhouette.
liner=bpy.data.materials.new('IAM_BlackenedMouthLiner');liner.use_nodes=True
bsdf=next(n for n in liner.node_tree.nodes if n.type=='BSDF_PRINCIPLED');bsdf.inputs['Base Color'].default_value=(.028,.026,.023,1);bsdf.inputs['Metallic'].default_value=.62;bsdf.inputs['Roughness'].default_value=.55
for o in list(bpy.data.objects):
 if o.type=='MESH' and 'IrisOuterCase' in o.name:bpy.data.objects.remove(o,do_unlink=True)
# Preserve round holes while filling more of the original throat's diameter.
bpy.data.objects['IAM_AcousticGuard'].scale=(1.16,1.16,1)
def finish(o):
 bm=bmesh.new();bm.from_mesh(o.data);bmesh.ops.remove_doubles(bm,verts=list(bm.verts),dist=1e-8);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(o.data);bm.free();return o
def mesh_obj(name,vs,fs,material,smooth=True,uv=None):
 m=bpy.data.meshes.new(name+'Mesh');m.from_pydata(vs,[],fs);m.update();m.materials.append(material);o=bpy.data.objects.new(name,m);col.objects.link(o);o.parent=mouth
 for f in m.polygons:f.use_smooth=smooth
 if uv:
  layer=m.uv_layers.new(name='FormedFoilUV')
  for f in m.polygons:
   for li in f.loop_indices:layer.data[li].uv=uv[m.loops[li].vertex_index]
 return finish(o)
# Read the actual ivory inner wall; the old straight sleeve crossed it and caused depth fighting.
bpy.context.view_layer.update();ivory=next(o for o in bpy.data.objects if 'PorcelainUpper' in o.name);m=ivory.data;m.calc_loop_triangles()
tree=BVHTree.FromPolygons([ivory.matrix_world@v.co for v in m.vertices],[tuple(t.vertices) for t in m.loop_triangles],all_triangles=True)
cross=[];radial_gap=.002;wall=.006
for j in range(81):
 z=-.096+.270*j/80;direction=Vector((math.cos(.7),math.sin(.7),0));point,normal,index,distance=tree.ray_cast(Vector((0,0,z)),direction,2)
 assert point is not None,('No actual inner wall',z)
 cross.append((distance-radial_gap,z))
cross.extend([(cross[-1][0],.204),(.820,.226)])
profile=cross+[(r-wall,z) for r,z in reversed(cross)];vs=[];fs=[];n=256
for r,z in profile:
 for k in range(n):a=k*math.tau/n;vs.append((r*math.cos(a),r*math.sin(a),z))
for j in range(len(profile)):
 for k in range(n):fs.append((j*n+k,j*n+(k+1)%n,((j+1)%len(profile))*n+(k+1)%n,((j+1)%len(profile))*n+k))
mesh_obj('IAM_IrisOuterCase_Fitted',vs,fs,liner)
bands=[((.46,.59),(-.47,-.57),-.12,-.43),((.05,.745),(-.56,-.49),-.025,-.30),((-.29,.685),(-.67,-.28),-.025,-.245)];leaves=[];poles=[]
for i,(aa,dd,left,right) in enumerate(bands):
 A=Vector(aa);D=Vector(dd);axis=(D-A).normalized();side=Vector((-axis.y,axis.x));poles.extend([(A,.014+i*.036),(D,.014+i*.036)])
 for skin in range(2):
  vs=[];fs=[];uv=[];nu=80;nv=20;thick=.0015;z0=.014+i*.036+skin*.0036
  for back in range(2):
   for j in range(nu+1):
    t=j/nu;width=.035+.965*math.sin(math.pi*t)
    for k in range(nv+1):
     w=k/nv;bulge=left*(1-w)+right*w;xy=A.lerp(D,t)+side*bulge*width
     z=z0-.026*math.sin(math.pi*t)*math.sin(math.pi*w)+(back-.5)*thick
     vs.append((xy.x,xy.y,z));uv.append((t*3,w*.45))
  stride=(nu+1)*(nv+1)
  for j in range(nu):
   for k in range(nv):
    v=j*(nv+1)+k;quad=(v,v+1,v+nv+2,v+nv+1);fs.extend([quad[::-1],tuple(x+stride for x in quad)])
  boundary=list(range(nv+1))+[j*(nv+1)+nv for j in range(1,nu+1)]+[nu*(nv+1)+k for k in range(nv-1,-1,-1)]+[j*(nv+1) for j in range(nu-1,0,-1)]
  for j,a in enumerate(boundary):
   c=boundary[(j+1)%len(boundary)];fs.append((a,c,c+stride,a+stride))
  o=mesh_obj('IAM_Eyelid_%d_%s'%(i,'skin' if skin==0 else 'backing'),vs,fs,mat if skin==0 else dark,uv=uv)
  leaves.append(o.name)
  # Paired roots meet the visible upper and lower lugs in REST. Guide trajectory remains unrigged.
  for j,pole in enumerate([A,D]):
   bpy.ops.mesh.primitive_cylinder_add(vertices=48,radius=.0115,depth=.006,location=(pole.x,pole.y,z0))
   eye=bpy.context.object;eye.name='IAM_EyelidRoot_%d_%d_%d'%(i,skin,j);eye.data.materials.append(nickel)
   for c in list(eye.users_collection):c.objects.unlink(eye)
   col.objects.link(eye);eye.parent=mouth;finish(eye)
# Fixed rear pin seats support the stacked roots. These do not claim a validated retracting linkage.
for i,(pole,leaf_z) in enumerate(poles):
 bottom=leaf_z+.004;top=.224
 bpy.ops.mesh.primitive_cylinder_add(vertices=64,radius=.0135,depth=top-bottom,location=(pole.x,pole.y,(top+bottom)/2))
 o=bpy.context.object;o.name='IAM_EyelidStackSeat_'+str(i);o.data.materials.append(dark)
 for c in list(o.users_collection):c.objects.unlink(o)
 col.objects.link(o);o.parent=mouth;finish(o)
 bpy.ops.mesh.primitive_cylinder_add(vertices=64,radius=.018,depth=.006,location=(pole.x,pole.y,leaf_z-.003))
 o=bpy.context.object;o.name='IAM_EyelidCaptiveHead_'+str(i);o.data.materials.append(nickel)
 for c in list(o.users_collection):c.objects.unlink(o)
 col.objects.link(o);o.parent=mouth;finish(o)
# Continuous backing ring carries every root; it is behind the foil and grille lip.
profile=[(.734,.214),(.835,.214),(.837,.220),(.834,.230),(.735,.230)];vs=[];fs=[];n=192
for r,z in profile:
 for k in range(n):a=k*math.tau/n;vs.append((r*math.cos(a),r*math.sin(a),z))
for j in range(len(profile)):
 for k in range(n):fs.append((j*n+k,j*n+(k+1)%n,((j+1)%len(profile))*n+(k+1)%n,((j+1)%len(profile))*n+k))
mesh_obj('IAM_EyelidFixedCarrier',vs,fs,liner)
scene=bpy.context.scene;scene.frame_start=1;scene.frame_end=1;scene.frame_set(1)
for o in bpy.data.objects:
 if o.animation_data:o.animation_data_clear()
bpy.ops.wm.save_as_mainfile(filepath=str(target));bpy.ops.object.select_all(action='DESELECT');root=bpy.data.objects['IAM_MODULE']
for o in [root]+list(root.children_recursive):o.select_set(True)
bpy.context.view_layer.objects.active=root;component=ROOT/'app/assets/collection/components/I_part_a_shutter_r2.glb'
bpy.ops.export_scene.gltf(filepath=str(component),export_format='GLB',use_selection=True,export_apply=False,export_animations=False,export_extras=True)
data={'source':str(target.relative_to(ROOT)),'source_sha256':sha(target),'component':str(component.relative_to(ROOT)),'component_sha256':sha(component),'reference':'production/I_refinement/part_a_mouth/shutter_r2/shutter_motion_r2.png','seed_source_sha256':report['source_sha256'],'shutter_meshes':leaves,'motion_implemented':False,'scope':'Asymmetric curved overlapping eyelid REST silhouette candidate; 3 visible formed skins with 3 backing skins. Retained improved collar/grille/finish. No validated retracting linkage, no OPEN animation, no whole-conch/App integration.'}
(OUT/'build.json').write_text(json.dumps(data,indent=2)+'\n');print('I_SHUTTER_R2_REST_BUILT')
