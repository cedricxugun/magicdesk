"""Static B form study around the checked A mouth; no final shell animation."""
import bpy,bmesh,math,json,hashlib,sys
import numpy as np
from pathlib import Path
from mathutils import Vector,Matrix
from mathutils.bvhtree import BVHTree
ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'review/I_refinement/part_b_shell/form_b1';OUT.mkdir(parents=True,exist_ok=True)
TARGET=ROOT/'blender/collection/I_shell_form_b1.blend'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
spec=json.loads((ROOT/'review/I_refinement/part_a_mouth/shutter_r2/collar_clamps/build.json').read_text())
assert sha(ROOT/spec['source'])==spec['source_sha256'] and sha(ROOT/spec['component'])==spec['component_sha256']
if TARGET.exists():
    old=json.loads((OUT/'build.json').read_text());assert sha(TARGET)==old['source_sha256'],'Unrecorded B form edits'
    (TARGET.parent/'checkpoints'/('I-shell-form-b1-'+sha(TARGET)[:12]+'.blend')).write_bytes(TARGET.read_bytes())
bpy.ops.wm.read_factory_settings(use_empty=True);scene=bpy.context.scene
collection=bpy.data.collections.new('I_B_FORM_B1');scene.collection.children.link(collection)
def material(name,color,metal=0.,rough=.4):
    m=bpy.data.materials.new(name);m.use_nodes=True;p=next(n for n in m.node_tree.nodes if n.type=='BSDF_PRINCIPLED')
    p.inputs['Base Color'].default_value=(*color,1);p.inputs['Metallic'].default_value=metal;p.inputs['Roughness'].default_value=rough
    return m
clay=material('IB1_FormIvory',(.64,.61,.55),0,.37);metal=material('IB1_SupportStudy',(.13,.14,.14),.65,.36);red=material('IB1_ApexMarker',(.28,.012,.006),.2,.28)
def empty(name):
    o=bpy.data.objects.new(name,None);collection.objects.link(o);return o
root=empty('IB1_BodyRoot');support=empty('IB1_SupportStudy');support.parent=root
center=Vector((-.20,-.65,2.05));front=Vector((-.62,-.765,.17)).normalized();back=-front
up=(Vector((0,0,1))-back*back.z).normalized();right=up.cross(back).normalized();basis=Matrix((right,up,back)).transposed();scale=.85
placement=basis.to_4x4();placement.translation=center;placement=placement@Matrix.Diagonal((scale,scale,scale,1.))
# Appending is only for the Blender study; the runtime composes the unchanged A GLB.
with bpy.data.libraries.load(str(ROOT/spec['source']),link=False) as (src,dst):dst.collections=['MODULE_IAM']
mouth_collection=dst.collections[0];scene.collection.children.link(mouth_collection)
mouth_root=bpy.data.objects['IAM_MODULE'];mouth_root.matrix_world=placement
def own(o,name,mat,parent=root):
    o.name=name
    for c in list(o.users_collection):c.objects.unlink(o)
    collection.objects.link(o);o.parent=parent;o.data.materials.clear();o.data.materials.append(mat)
    return o
def finish(o):
    bm=bmesh.new();bm.from_mesh(o.data);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(o.data);bm.free()
    for face in o.data.polygons:face.use_smooth=True
    o.data.update()
def inspect_stage(o,label):
    bm=bmesh.new();bm.from_mesh(o.data);stats={'stage':label,'nonmanifold':sum(not e.is_manifold for e in bm.edges),'volume':bm.calc_volume(signed=True)};bm.free();print('FORM_STAGE',stats,flush=True)
def boolean(o,tool,op):
    bpy.context.view_layer.update();bpy.context.view_layer.objects.active=o;m=o.modifiers.new('Form volume '+op,'BOOLEAN');m.operation=op;m.solver='EXACT';m.object=tool
    inspect_stage(o,'before_'+op);inspect_stage(tool,'tool_'+op)
    bpy.ops.object.modifier_apply(modifier=m.name);bpy.data.objects.remove(tool,do_unlink=True);inspect_stage(o,'after_'+op)
controls=np.array([
    [1.02,.32,.24,.015,.015],[1.12,.34,.22,.36,.38],[1.45,.38,.18,.68,.63],
    [1.90,.32,.18,.84,.74],[2.32,.21,.19,.79,.70],[2.68,.02,.19,.58,.54],
    [2.98,-.31,.13,.37,.35],[3.22,-.53,.02,.20,.19],[3.38,-.59,-.03,.065,.07],
    [3.43,-.60,-.06,.008,.008]],dtype=float)
def profile(z):
    j=min(len(controls)-2,max(0,int(np.searchsorted(controls[:,0],z)-1)));a=controls[j];b=controls[j+1];h=b[0]-a[0];t=(z-a[0])/h
    lo=max(0,j-1);hi=min(len(controls)-1,j+2)
    ma=(controls[j+1,1:]-controls[lo,1:])/(controls[j+1,0]-controls[lo,0])
    mb=(controls[hi,1:]-controls[j,1:])/(controls[hi,0]-controls[j,0])
    value=(2*t**3-3*t*t+1)*a[1:]+(t**3-2*t*t+t)*h*ma+(-2*t**3+3*t*t)*b[1:]+(t**3-t*t)*h*mb
    value[2:]=np.maximum(value[2:],.004);return value
def pear(name,inner=False):
    zs=np.linspace(1.07 if inner else 1.02,3.28 if inner else 3.43,110);n=160;verts=[];faces=[]
    for z in zs:
        x,y,rx,ry=profile(z)
        if inner:rx=max(.008,rx-.048);ry=max(.008,ry-.048)
        for k in range(n):
            angle=k*math.tau/n;u=(z-1.02)/(3.43-1.02);phase=5.4*u**1.3+angle/math.tau+.12
            relief=1.+.025*max(0.,math.sin(math.pi*u))**.35*math.cos(math.tau*phase)
            verts.append((x+rx*relief*math.cos(angle),y+ry*relief*math.sin(angle),z))
    for j in range(len(zs)-1):
        for k in range(n):faces.append((j*n+k,j*n+(k+1)%n,(j+1)*n+(k+1)%n,(j+1)*n+k))
    faces.extend([tuple(range(n-1,-1,-1)),tuple((len(zs)-1)*n+k for k in range(n))])
    mesh=bpy.data.meshes.new(name+'Mesh');mesh.from_pydata(verts,[],faces);mesh.update();o=bpy.data.objects.new(name,mesh);collection.objects.link(o);o.parent=root;mesh.materials.append(clay);finish(o);return o
def throat(name,radius,depth):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=96,ring_count=64,radius=1)
    o=own(bpy.context.object,name,clay)
    for vertex in o.data.vertices:
        if vertex.co.z>0:vertex.co.z*=1.55
    o.data.update();o.matrix_world=basis.to_4x4();o.location=center+back*.27;o.scale=(radius,radius,depth)
    bpy.context.view_layer.objects.active=o;bpy.ops.object.transform_apply(location=False,rotation=False,scale=True);finish(o);return o
body=pear('IB1_OuterForm');boolean(body,throat('IB1_ThroatVolume',.78,.40),'UNION')
bpy.context.view_layer.objects.active=body
remesh=body.modifiers.new('Unified form skin','REMESH');remesh.mode='VOXEL';remesh.voxel_size=.022;remesh.use_smooth_shade=True
bpy.ops.object.modifier_apply(modifier=remesh.name)
smooth=body.modifiers.new('Blend throat into belly','SMOOTH');smooth.factor=.55;smooth.iterations=5;bpy.ops.object.modifier_apply(modifier=smooth.name)
finish(body)
# This first form pass only clears A; final inner walls belong to the panel stage.
clearance=json.loads((OUT/'mouth_clearance_profile.json').read_text())
assert clearance['source_sha256']==spec['source_sha256'] and clearance['uniform_scale']==scale
cut_profile=clearance['profile']+[[.85,clearance['profile'][-1][1]]]
vs=[];fs=[];n=160
for depth,radius in cut_profile:
    for k in range(n):
        a=k*math.tau/n;vs.append(tuple(center+right*(radius*math.cos(a))+up*(radius*math.sin(a))+back*depth))
for j in range(len(cut_profile)-1):
    for k in range(n):fs.append((j*n+k,j*n+(k+1)%n,(j+1)*n+(k+1)%n,(j+1)*n+k))
fs.extend([tuple(range(n-1,-1,-1)),tuple((len(cut_profile)-1)*n+k for k in range(n))])
m=bpy.data.meshes.new('IB1_MeasuredCavityToolMesh');m.from_pydata(vs,[],fs);m.update();cutter=bpy.data.objects.new('IB1_MouthOpeningTool',m);collection.objects.link(cutter);cutter.parent=root;m.materials.append(clay);finish(cutter)
boolean(body,cutter,'DIFFERENCE');finish(body)
# Short external shoulder joins behind A's rim; never extends into its throat.
shoulder_profile=[(.735,.105),(.748,.145),(.771,.22),(.746,.22),(.728,.145),(.724,.105)]
vs=[];fs=[];n=192
for radius,depth in shoulder_profile:
    for k in range(n):
        a=k*math.tau/n;vs.append(tuple(center+right*(radius*math.cos(a))+up*(radius*math.sin(a))+back*depth))
for j in range(len(shoulder_profile)):
    for k in range(n):fs.append((j*n+k,j*n+(k+1)%n,((j+1)%len(shoulder_profile))*n+(k+1)%n,((j+1)%len(shoulder_profile))*n+k))
m=bpy.data.meshes.new('IB1_ShortShoulderMesh');m.from_pydata(vs,[],fs);m.update();shoulder=bpy.data.objects.new('IB1_ShortShoulder',m);collection.objects.link(shoulder);shoulder.parent=root;m.materials.append(clay);finish(shoulder)
boolean(body,shoulder,'UNION');finish(body)
# Surface-projected spiral parting guides for visual planning, not separated panels.
guide_mat=material('IB1_PartingGuide',(.055,.044,.03),.72,.34)
body.data.calc_loop_triangles();surface=BVHTree.FromPolygons([body.matrix_world@v.co for v in body.data.vertices],[tuple(t.vertices) for t in body.data.loop_triangles],all_triangles=True)
inverse_a=placement.inverted();guide_records=[]
for level in range(1,7):
    pieces=[];current=[]
    for angle in np.linspace(0,math.tau,241):
        raw=(level-angle/math.tau-.12)/5.4
        hit=None
        if 0.<raw<1.:
            u=raw**(1/1.3);z=1.02+(3.43-1.02)*u;x,y,rx,ry=profile(z);axis=Vector((x,y,z));direction=Vector((math.cos(angle),math.sin(angle),0))
            p,norm,index,dist=surface.ray_cast(axis+direction*2.,-direction,4.)
            if p is not None and norm.dot(direction)>.1:
                local=inverse_a@p
                if not (local.z<.35 and math.hypot(local.x,local.y)<.93):hit=p+norm*.007
        if hit is None or (current and (hit-current[-1]).length>.15):
            if len(current)>2:pieces.append(current)
            current=[]
        if hit is not None:current.append(hit)
    if len(current)>2:pieces.append(current)
    for segment,points in enumerate(pieces):
        curve=bpy.data.curves.new('PartingGuideCurve','CURVE');curve.dimensions='3D';curve.bevel_depth=.005;curve.bevel_resolution=2;curve.use_fill_caps=True
        spline=curve.splines.new('POLY');spline.points.add(len(points)-1)
        for point,co in zip(spline.points,points):point.co=(*co,1)
        o=bpy.data.objects.new('IB1_PartingGuide_%d_%d'%(level,segment),curve);collection.objects.link(o);o.parent=root;curve.materials.append(guide_mat)
        bpy.ops.object.select_all(action='DESELECT');o.select_set(True);bpy.context.view_layer.objects.active=o;bpy.ops.object.convert(target='MESH')
        guide_records.append({'level':level,'segment':segment,'points':len(points),'name':bpy.context.object.name})
def cylinder_between(name,a,b,r,mat):
    a=Vector(a);b=Vector(b);bpy.ops.mesh.primitive_cylinder_add(vertices=48,radius=r,depth=(b-a).length)
    o=own(bpy.context.object,name,mat,support);o.location=(a+b)/2;o.rotation_mode='QUATERNION';o.rotation_quaternion=(b-a).to_track_quat('Z','Y');finish(o);return o
cylinder_between('IB1_ProvisionalMount',(0,0,.67),(.27,.16,1.14),.16,metal)
cylinder_between('IB1_BaseSocketStudy',(0,0,.5625),(0,0,.66),.31,metal)
for sign in [-1,1]:
    cylinder_between('IB1_BraceStudy'+str(sign),(sign*.58,-.34,.60),(.27+sign*.22,.12,1.14),.045,metal)
    cylinder_between('IB1_BraceFootStudy'+str(sign),(sign*.58,-.34,.5625),(sign*.58,-.34,.6075),.10,metal)
cylinder_between('IB1_ApexStud',(-.60,-.06,3.41),(-.64,-.085,3.51),.032,metal)
bpy.ops.mesh.primitive_uv_sphere_add(segments=32,ring_count=16,radius=.038)
tip=own(bpy.context.object,'IB1_ApexRedMarker',red);tip.location=(-.64,-.085,3.51);finish(tip)
scene.frame_set(1);bpy.context.view_layer.update()
body_points=np.array([tuple(o.matrix_world@v.co) for o in collection.objects if o.type=='MESH' for v in o.data.vertices])
measurement={'min':body_points.min(axis=0).tolist(),'max':body_points.max(axis=0).tolist(),'size':np.ptp(body_points,axis=0).tolist()}
bm=bmesh.new();bm.from_mesh(body.data);topology={'vertices':len(bm.verts),'faces':len(bm.faces),'nonmanifold_edges':sum(not e.is_manifold for e in bm.edges),'volume':bm.calc_volume(signed=True)};bm.free()
bpy.ops.wm.save_as_mainfile(filepath=str(TARGET),compress=True)
bpy.ops.object.select_all(action='DESELECT')
for o in collection.objects:o.select_set(True)
bpy.context.view_layer.objects.active=root;component=ROOT/'app/assets/collection/components/I_shell_form_b1.glb'
bpy.ops.export_scene.gltf(filepath=str(component),export_format='GLB',use_selection=True,export_animations=False,export_extras=True)
convert=Matrix(((1,0,0,0),(0,0,1,0),(0,-1,0,0),(0,0,0,1)));godot_placement=convert@placement@convert.inverted();p,q,s=godot_placement.decompose()
report={'source':str(TARGET.relative_to(ROOT)),'source_sha256':sha(TARGET),'component':str(component.relative_to(ROOT)),'component_sha256':sha(component),'mouth_source_sha256':spec['source_sha256'],'mouth_component':spec['component'],'mouth_component_sha256':spec['component_sha256'],'mouth_report':'review/I_refinement/part_a_mouth/shutter_r2/collar_clamps/build.json','mouth_placement':{'p':list(p),'q':[q.x,q.y,q.z,q.w],'s':list(s)},'mouth_blender_center':list(center),'mouth_blender_forward':list(front),'mouth_uniform_scale':scale,'profile_controls':controls.tolist(),'spiral_relief':{'turns':5.4,'height_power':1.3,'amplitude':.025,'phase':.12},'shoulder_profile':shoulder_profile,'clearance_profile_sha256':sha(OUT/'mouth_clearance_profile.json'),'parting_guides':guide_records,'body_bounds_blender':measurement,'form_topology':topology,'base_sha256':sha(ROOT/'app/assets/helios_model.glb'),'status':'static_form_probe_unlocked','scope':'New plump curved body form and current A placement on an unchanged-base review. Static exterior volume with mouth clearance only; final inner walls and six shell segments, final support/core, animation and complete collision not built or accepted. No main/native App replacement.'}
(OUT/'build.json').write_text(json.dumps(report,indent=2)+'\n');print('I_SHELL_FORM_B1_BUILT',json.dumps(measurement),topology,flush=True)
