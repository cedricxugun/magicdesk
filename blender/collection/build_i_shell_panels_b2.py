"""Six actual thin ceramic shells, derived from the current B form envelope."""
import bpy,bmesh,math,json,hashlib
import numpy as np
from pathlib import Path
from mathutils import Vector,Matrix
from mathutils.kdtree import KDTree
ROOT=Path(__file__).resolve().parents[2];OUT=ROOT/'review/I_refinement/part_b_shell/panels_b2';OUT.mkdir(parents=True,exist_ok=True)
seed=json.loads((ROOT/'review/I_refinement/part_b_shell/form_b1/build.json').read_text());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
source=ROOT/seed['source'];assert sha(source)==seed['source_sha256'];target=ROOT/'blender/collection/I_shell_panels_b2.blend'
if target.exists():
    previous=json.loads((OUT/'build.json').read_text());assert sha(target)==previous['source_sha256'],'Unrecorded panel edits'
    (target.parent/'checkpoints'/('I-shell-panels-b2-'+sha(target)[:12]+'.blend')).write_bytes(target.read_bytes())
bpy.ops.wm.open_mainfile(filepath=str(source));scene=bpy.context.scene;scene.frame_set(1);bpy.context.view_layer.update()
col=bpy.data.collections.new('I_B_PANELS_B2');scene.collection.children.link(col)
root=bpy.data.objects.new('IB2_Module',None);col.objects.link(root)
outer_mat=bpy.data.materials['Collection_A_Ivory'];inner_mat=bpy.data.materials['Collection_A_Satin']
controls=np.array(seed['profile_controls']);center=Vector(seed['mouth_blender_center']);front=Vector(seed['mouth_blender_forward']);back=-front
up=(Vector((0,0,1))-back*back.z).normalized();right=up.cross(back).normalized();basis=Matrix((right,up,back)).transposed()
clearance=json.loads((ROOT/'review/I_refinement/part_b_shell/form_b1/mouth_clearance_profile.json').read_text());cp=np.array(clearance['profile']+[[.85,clearance['profile'][-1][1]]])
def profile(z):
    j=min(len(controls)-2,max(0,int(np.searchsorted(controls[:,0],z)-1)));a=controls[j];b=controls[j+1];h=b[0]-a[0];t=(z-a[0])/h
    lo=max(0,j-1);hi=min(len(controls)-1,j+2)
    ma=(controls[j+1,1:]-controls[lo,1:])/(controls[j+1,0]-controls[lo,0]);mb=(controls[hi,1:]-controls[j,1:])/(controls[hi,0]-controls[j,0])
    v=(2*t**3-3*t*t+1)*a[1:]+(t**3-2*t*t+t)*h*ma+(-2*t**3+3*t*t)*b[1:]+(t**3-t*t)*h*mb;v[2:]=np.maximum(v[2:],.004);return v
def finish(o):
    bm=bmesh.new();bm.from_mesh(o.data);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(o.data);bm.free();o.data.update()
    for f in o.data.polygons:f.use_smooth=True
def mesh_obj(name,verts,faces,mat=outer_mat):
    m=bpy.data.meshes.new(name+'Mesh');m.from_pydata(verts,[],faces);m.update();o=bpy.data.objects.new(name,m);col.objects.link(o);o.parent=root;m.materials.append(mat);finish(o);return o
def boolean(o,tool,operation):
    bpy.context.view_layer.update();bpy.context.view_layer.objects.active=o;mod=o.modifiers.new('Panel machining','BOOLEAN');mod.operation=operation;mod.solver='EXACT';mod.object=tool
    bpy.ops.object.modifier_apply(modifier=mod.name);bpy.data.objects.remove(tool,do_unlink=True);finish(o)
# Reconstruct only the documented pre-clearance exterior, never execute/save B1.
verts=[];faces=[];n=160;zs=np.linspace(1.02,3.43,110)
for z in zs:
    x,y,rx,ry=profile(z);u=(z-1.02)/2.41
    for k in range(n):
        a=k*math.tau/n;relief=1.+.025*max(0.,math.sin(math.pi*u))**.35*math.cos(math.tau*(5.4*u**1.3+a/math.tau+.12))
        verts.append((x+rx*relief*math.cos(a),y+ry*relief*math.sin(a),z))
for j in range(len(zs)-1):
    for k in range(n):faces.append((j*n+k,j*n+(k+1)%n,(j+1)*n+(k+1)%n,(j+1)*n+k))
faces.extend([tuple(range(n-1,-1,-1)),tuple((len(zs)-1)*n+k for k in range(n))])
envelope=mesh_obj('IB2_EnvelopeWorking',verts,faces)
bpy.ops.mesh.primitive_uv_sphere_add(segments=96,ring_count=64,radius=1);tool=bpy.context.object
for v in tool.data.vertices:
    if v.co.z>0:v.co.z*=1.55
tool.data.update();tool.matrix_world=basis.to_4x4();tool.location=center+back*.27;tool.scale=(.78,.78,.40)
bpy.context.view_layer.objects.active=tool;bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
boolean(envelope,tool,'UNION')
bpy.context.view_layer.objects.active=envelope;mod=envelope.modifiers.new('Same outer envelope','REMESH');mod.mode='VOXEL';mod.voxel_size=.022;mod.use_smooth_shade=True;bpy.ops.object.modifier_apply(modifier=mod.name)
mod=envelope.modifiers.new('Same form blend','SMOOTH');mod.factor=.55;mod.iterations=5;bpy.ops.object.modifier_apply(modifier=mod.name);finish(envelope)
# Keep the existing short shoulder fixed, rather than swinging a neck into A.
fixed=bpy.data.objects['IB1_OuterForm'].copy();fixed.data=fixed.data.copy();col.objects.link(fixed);fixed.parent=root;fixed.name='IB2_FixedThroatInterface'
bpy.ops.mesh.primitive_cylinder_add(vertices=160,radius=.90,depth=.695);tool=bpy.context.object;tool.rotation_mode='QUATERNION';tool.rotation_quaternion=back.to_track_quat('Z','Y');tool.location=center+back*(-.0525)
boolean(fixed,tool,'INTERSECT')
# q is periodic and monotone in height. Six closed partitions, not a rounded
# 5.4-turn guide index, are used. Annular pieces get an explicit rear release slit.
def qfield(p):
    u=max(0.,min(1.,(p[2]-1.02)/2.41));x,y,_,_=profile(p[2]);theta=math.atan2(p[1]-y,p[0]-x)
    return 6*u+.42*math.sin(math.pi*u)*math.sin(theta-math.tau*.6*u)
def attributes(p,norm):
    p=np.asarray(p);norm=np.asarray(norm);eps=.0001;grad=[]
    for k in range(3):
        delta=np.zeros(3);delta[k]=eps;grad.append((qfield(p+delta)-qfield(p-delta))/(2*eps))
    grad=np.array(grad);grad-=norm*np.dot(grad,norm);margin=min(.035,max(.001,np.linalg.norm(grad)*.0035))
    rel=Vector(p)-center;depth=rel.dot(back);radius=math.hypot(rel.dot(right),rel.dot(up))
    clear=radius-float(np.interp(depth,cp[:,0],cp[:,1]))-.027 if cp[0,0]<=depth<=cp[-1,0] else 1.
    x,y,_,_=profile(p[2]);thickness=min(.022,max(.003,math.hypot(p[0]-x,p[1]-y)*.24))
    inside=Vector(p)-Vector(norm)*thickness-center;inner_depth=inside.dot(back);inner_radius=math.hypot(inside.dot(right),inside.dot(up))
    collar=min(max(depth-.302,radius-.907),max(inner_depth-.302,inner_radius-.907))
    return np.r_[p,norm,qfield(p),margin,clear,collar,thickness,p[0]-x,p[1]-y]
def clip(poly,fn):
    if not poly:return []
    result=[];prev=poly[-1];fp=fn(prev)
    for cur in poly:
        fc=fn(cur)
        if (fc>=0)!=(fp>=0):result.append(prev+(cur-prev)*(fp/(fp-fc)))
        if fc>=0:result.append(cur)
        prev=cur;fp=fc
    return result
def surface_mesh(polygons,name):
    vertices=[];normals=[];thickness=[];faces=[];lookup={}
    for poly in polygons:
        if len(poly)<3:continue
        ids=[]
        for v in poly:
            key=tuple(round(float(x),7) for x in v[:3])
            if key not in lookup:
                lookup[key]=len(vertices);vertices.append(tuple(v[:3]));normals.append(tuple(v[3:6]));thickness.append(float(v[10]))
            ids.append(lookup[key])
        for k in range(1,len(ids)-1):
            if len({ids[0],ids[k],ids[k+1]})==3:faces.append((ids[0],ids[k],ids[k+1]))
    # Clipping can leave microunit sliver clusters. Weld before thickening so
    # the outer and inner topology remain identical, rather than deleting faces.
    kd=KDTree(len(vertices))
    for i,p in enumerate(vertices):kd.insert(p,i)
    kd.balance();parents=list(range(len(vertices)))
    def parent(i):
        while parents[i]!=i:parents[i]=parents[parents[i]];i=parents[i]
        return i
    for i,p in enumerate(vertices):
        for co,j,distance in kd.find_range(p,.000003):
            a=parent(i);b=parent(j)
            if a!=b:parents[max(a,b)]=min(a,b)
    groups={}
    for i in range(len(vertices)):groups.setdefault(parent(i),[]).append(i)
    ids={};merged=[];new_normals=[];new_thickness=[]
    for group in groups.values():
        index=len(merged);merged.append(tuple(np.mean([vertices[i] for i in group],axis=0)))
        new_normals.append(tuple(np.mean([normals[i] for i in group],axis=0)));new_thickness.append(float(np.mean([thickness[i] for i in group])))
        for i in group:ids[i]=index
    new_faces=[]
    for f in faces:
        mapped=tuple(ids[i] for i in f)
        if len(set(mapped))==3:new_faces.append(mapped)
    vertices=merged;normals=new_normals;thickness=new_thickness;faces=new_faces
    m=bpy.data.meshes.new(name);m.from_pydata(vertices,[],faces);m.update()
    return m,vertices,normals,thickness
def surface_info(m):
    bm=bmesh.new();bm.from_mesh(m);bm.verts.ensure_lookup_table();remaining=set(bm.verts);components=[]
    while remaining:
        stack=[remaining.pop()];seen=set(stack)
        while stack:
            v=stack.pop()
            for e in v.link_edges:
                w=e.other_vert(v)
                if w in remaining:remaining.remove(w);seen.add(w);stack.append(w)
        components.append(len(seen))
    edges={e for e in bm.edges if e.is_boundary};loops=0
    while edges:
        stack=list(edges.pop().verts);loops+=1
        while stack:
            v=stack.pop()
            for e in v.link_edges:
                if e in edges:edges.remove(e);stack.extend(e.verts)
    counts={'surface_components':components,'boundary_loops':loops,'nonmanifold_interior_edges':sum(not e.is_manifold and not e.is_boundary for e in bm.edges)};bm.free();return counts
envelope.data.calc_loop_triangles();cache=[attributes(v.co,v.normal) for v in envelope.data.vertices];triangles=[tuple(t.vertices) for t in envelope.data.loop_triangles]
panels=[]
for part in range(6):
    polygons=[]
    for tri in triangles:
        poly=[cache[i] for i in tri]
        if part>0:poly=clip(poly,lambda v:v[6]-part-v[7])
        if part<5:poly=clip(poly,lambda v:part+1-v[6]-v[7])
        poly=clip(poly,lambda v:v[8]);poly=clip(poly,lambda v:v[9])
        if len(poly)>=3:polygons.append(poly)
    m,points,normals,thickness=surface_mesh(polygons,'IB2_Surface%d'%part);info=surface_info(m)
    rear_split=info['boundary_loops']>1
    if rear_split:
        divided=[]
        for poly in polygons:
            fore=clip(poly,lambda v:-v[12]);aft=clip(poly,lambda v:v[12])
            if len(fore)>=3:divided.append(fore)
            for sign in [-1,1]:
                side=clip(aft,lambda v:sign*v[11]-.004)
                if len(side)>=3:divided.append(side)
        bpy.data.meshes.remove(m);polygons=divided;m,points,normals,thickness=surface_mesh(polygons,'IB2_Surface%d'%part);info=surface_info(m)
    p=np.asarray(points);normal=np.asarray(normals);normal/=np.maximum(np.linalg.norm(normal,axis=1)[:,None],1e-9);count=len(p)
    inner=p-normal*np.asarray(thickness)[:,None];faces=[tuple(f.vertices) for f in m.polygons];edge_use={}
    for f in faces:
        for a,b in zip(f,f[1:]+f[:1]):edge_use.setdefault(tuple(sorted((a,b))),[]).append((a,b))
    boundary=[use[0] for use in edge_use.values() if len(use)==1]
    solid_faces=faces+[tuple(v+count for v in reversed(f)) for f in faces]+[(b,a,a+count,b+count) for a,b in boundary]
    o=mesh_obj('IB2_Shell_%02d'%(part+1),np.vstack([p,inner]).tolist(),solid_faces)
    o.data.materials.append(inner_mat)
    for i,f in enumerate(o.data.polygons):
        if i>=len(faces):f.material_index=1
    # Preserve the envelope's smooth outer normals across clipped triangles;
    # side walls get their actual face normals instead of pulling the rim flat.
    split_normals=[]
    for f in o.data.polygons:
        for li in f.loop_indices:
            vi=o.data.loops[li].vertex_index
            if f.index<len(faces):n=normal[vi]
            elif f.index<2*len(faces):n=-normal[vi-count]
            else:n=f.normal
            split_normals.append(tuple(n))
    o.data.normals_split_custom_set(split_normals)
    bpy.data.meshes.remove(m)
    bm=bmesh.new();bm.from_mesh(o.data);stats={'nonmanifold':sum(not e.is_manifold for e in bm.edges),'volume':bm.calc_volume(signed=True)};bm.free()
    panels.append({'index':part+1,'mesh':o.name,'rear_split':rear_split,'surface':info,'solid':stats,'nominal_thickness':.022,'outer_vertices':count})
    print('SHELL_PANEL',part+1,info,stats,flush=True)
bpy.data.objects.remove(envelope,do_unlink=True)
# Remove only the preceding form skin and guide curves; retain A and the clearly
# identified provisional support/apex shapes as references for later stages.
for o in list(bpy.data.objects):
    if o.name=='IB1_OuterForm' or o.name.startswith('IB1_PartingGuide_'):bpy.data.objects.remove(o,do_unlink=True)
for o in list(bpy.data.collections['I_B_FORM_B1'].objects):
    if o.type=='MESH':
        for c in list(o.users_collection):c.objects.unlink(o)
        col.objects.link(o)
bpy.context.view_layer.update();bpy.ops.wm.save_as_mainfile(filepath=str(target),compress=True)
bpy.ops.object.select_all(action='DESELECT')
for o in col.objects:o.select_set(True)
bpy.context.view_layer.objects.active=root;component=ROOT/'app/assets/collection/components/I_shell_panels_b2.glb'
bpy.ops.export_scene.gltf(filepath=str(component),export_format='GLB',use_selection=True,export_animations=False,export_extras=True)
report={**seed,'source':str(target.relative_to(ROOT)),'source_sha256':sha(target),'component':str(component.relative_to(ROOT)),'component_sha256':sha(component),'seed_source_sha256':seed['source_sha256'],'panels':panels,'fixed_collar':fixed.name,'status':'six_panel_construction_candidate_requires_geometry_review','scope':'Six actual thickened surface partitions plus fixed throat interface, reconstructed from the documented B1 envelope. Connectivity, wall clearance and art still require review; hinge geometry and opening are not yet implemented. Provisional support is not C.'}
report.pop('parting_guides',None);report.pop('form_topology',None)
report['review_scope']='Six constructed thin panel candidate in REST with unchanged A on actual shared base. Static source-to-runtime appearance only; hinges/opening and final C support/core are not yet built. Mouth-open image is not shell ACTIVE.'
(OUT/'build.json').write_text(json.dumps(report,indent=2)+'\n');print('I_SHELL_PANELS_B2_BUILT',flush=True)
