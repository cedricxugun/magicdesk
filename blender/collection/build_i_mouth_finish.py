"""Refine only perforated guard topology and metal finish on the checked A source."""
import bpy,bmesh,json,hashlib,math,sys
from pathlib import Path
from mathutils import Vector
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(Path(__file__).parent))
OUT=ROOT/'review/I_refinement/part_a_mouth/shutter_r2/metal_finish';OUT.mkdir(parents=True,exist_ok=True)
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
seed=json.loads((OUT.parent/'front_guides/build.json').read_text());source=ROOT/seed['source'];assert sha(source)==seed['source_sha256']
bpy.ops.wm.open_mainfile(filepath=str(source));scene=bpy.context.scene;scene.frame_set(1);bpy.context.view_layer.update()
target=ROOT/'blender/collection/I_mouth_finish.blend'
if target.exists():
    old=json.loads((OUT/'build.json').read_text());assert sha(target)==old['source_sha256'],'Unrecorded finish edits'
    (target.parent/'checkpoints'/('I-mouth-finish-'+sha(target)[:12]+'.blend')).write_bytes(target.read_bytes())

def fingerprint(o):
    import numpy as np
    h=hashlib.sha256()
    # Blender updates mesh.vertices from active shape-key evaluation during an
    # operator. For keyed meshes the authored source is Basis plus all keys;
    # compare those, not the transient evaluated vertex buffer.
    vertices=o.data.shape_keys.key_blocks[0].data if o.data.shape_keys else o.data.vertices
    a=np.zeros(len(vertices)*3,dtype=np.float32);vertices.foreach_get('co',a);a[a==0]=0.;h.update(a.tobytes())
    for p in o.data.polygons:h.update(bytes(__import__('array').array('I',p.vertices)))
    if o.data.shape_keys:
        for key in o.data.shape_keys.key_blocks:
            a=np.zeros(len(key.data)*3,dtype=np.float32);key.data.foreach_get('co',a);a[a==0]=0.;h.update(a.tobytes())
    return h.hexdigest()

retained={o.name:fingerprint(o) for o in bpy.data.objects if o.type=='MESH' and not any(x in o.name for x in ['OuterGuard','MiddleGuard','InnerGuard'])}
import numpy as np
probe=bpy.data.objects['IAM_TongueFoil_0']
probe_keys=[]
for key in probe.data.shape_keys.key_blocks:
    a=np.zeros(len(key.data)*3,dtype=np.float32);key.data.foreach_get('co',a);probe_keys.append(a)
probe_faces=[tuple(p.vertices) for p in probe.data.polygons]
material_root=ROOT/'production/I_refinement/part_a_mouth/material_r2'
materials={}
for ident,color,roughness in [('Guard',(.25,.26,.245),.34),('Recess',(.075,.08,.072),.39)]:
    mat=bpy.data.materials['Collection_A_Satin' if ident=='Guard' else 'Collection_A_Dark'].copy();mat.name='Collection_A_Finished'+ident
    shader=next(n for n in mat.node_tree.nodes if n.type=='BSDF_PRINCIPLED')
    shader.inputs['Base Color'].default_value=(*color,1);shader.inputs['Roughness'].default_value=roughness
    tex=mat.node_tree.nodes.new('ShaderNodeTexImage');tex.image=bpy.data.images.load(str(material_root/'nickel_normal.png'),check_existing=True);tex.image.colorspace_settings.name='Non-Color';tex.image.pack()
    normal=mat.node_tree.nodes.new('ShaderNodeNormalMap');normal.inputs['Strength'].default_value=.16
    mat.node_tree.links.new(tex.outputs['Color'],normal.inputs['Color']);mat.node_tree.links.new(normal.outputs['Normal'],shader.inputs['Normal'])
    materials[ident]=mat

records=[]
for token,ri,ro,depth,rows,material in [('OuterGuard',.444,.597,.065,3,'Guard'),('MiddleGuard',.29,.419,.104,3,'Recess'),('InnerGuard',.099,.267,.135,4,'Guard')]:
    o=next(o for o in bpy.data.objects if token in o.name);before={'vertices':len(o.data.vertices),'matrix':list(sum((list(row) for row in o.matrix_world),[]))}
    verts=[];faces=[];uv=[];n=48;holes=[]
    for row in range(rows):
        low=ri+(ro-ri)*row/rows;high=ri+(ro-ri)*(row+1)/rows;mid=(low+high)/2;pitch=high-low
        count=round(math.tau*((ri+ro)/2)/pitch);da=math.pi/count
        for k in range(count):
            a=(k+.5)*math.tau/count;center=Vector((mid*math.cos(a),mid*math.sin(a)));off=len(verts);hole_r=min(pitch*.34,mid*math.sin(da)*.69)
            holes.append({'center':list(center),'radius':hole_r})
            for back in [False,True]:
                for hole in [False,True]:
                    for j in range(n):
                        theta=j*math.tau/n;dx=math.cos(theta);dy=math.sin(theta)
                        if hole:p=center+Vector((math.cos(a)*dx-math.sin(a)*dy,math.sin(a)*dx+math.cos(a)*dy))*hole_r
                        else:
                            scale=1/max(abs(dx),abs(dy));radius=mid+dx*scale*pitch*.5;angle=a+dy*scale*da;p=Vector((radius*math.cos(angle),radius*math.sin(angle)))
                        z=depth+.014*(p.length/ro)**2+(.007 if back else 0)
                        verts.append((p.x,p.y,z));uv.append((p.x/ro*2,p.y/ro*2))
            for j in range(n):
                q=(j+1)%n
                for d,rev in [(0,False),(2*n,True)]:
                    f=(off+d+j,off+d+q,off+d+n+q,off+d+n+j);faces.append(f[::-1] if rev else f)
                faces.append((off+n+j,off+n+q,off+3*n+q,off+3*n+j))
                aa=verts[off+j];bb=verts[off+q];ra=math.hypot(aa[0],aa[1]);rb=math.hypot(bb[0],bb[1])
                if (row==0 and abs(ra-ri)<1e-6 and abs(rb-ri)<1e-6) or (row==rows-1 and abs(ra-ro)<1e-6 and abs(rb-ro)<1e-6):faces.append((off+j,off+2*n+j,off+2*n+q,off+q))
    mesh=bpy.data.meshes.new(o.name+'MachinedMesh');mesh.from_pydata(verts,[],faces);mesh.update()
    layer=mesh.uv_layers.new(name='GuardBrushingUV')
    for face in mesh.polygons:
        for li in face.loop_indices:layer.data[li].uv=uv[mesh.loops[li].vertex_index]
    mesh.materials.append(materials[material]);o.data=mesh
    bm=bmesh.new();bm.from_mesh(mesh);bmesh.ops.remove_doubles(bm,verts=list(bm.verts),dist=1e-7);bmesh.ops.dissolve_degenerate(bm,edges=list(bm.edges),dist=1e-8)
    bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(mesh);bm.free()
    bpy.context.view_layer.objects.active=o
    bevel=o.modifiers.new('Machined rounded bore lips','BEVEL');bevel.width=.00065;bevel.segments=3;bevel.limit_method='ANGLE';bevel.angle_limit=.65;bevel.use_clamp_overlap=True
    bpy.ops.object.modifier_apply(modifier=bevel.name)
    bm=bmesh.new();bm.from_mesh(o.data);bm.normal_update()
    for face in bm.faces:face.smooth=True
    for edge in bm.edges:edge.smooth=edge.is_manifold and edge.calc_face_angle()<.55
    bm.to_mesh(o.data);bm.free()
    # Weight the broad sheet faces instead of averaging their normals equally
    # with every tiny bore/bevel face, which creates false pillow reflections.
    weighted=o.modifiers.new('Planished sheet normals','WEIGHTED_NORMAL');weighted.keep_sharp=True;weighted.weight=100
    bpy.context.view_layer.objects.active=o;bpy.ops.object.modifier_apply(modifier=weighted.name)
    records.append({'name':o.name,'before':before,'vertices':len(o.data.vertices),'holes':holes,'bore_segments':n,'lip_bevel':.00065,'finish':materials[material].name})
    print('GUARD_FINISH',o.name,len(o.data.vertices),flush=True)

# Curved return shoes already have authored micro-bevels. Smooth only within
# the tangent-continuous surfaces and preserve their sharp section transitions.
for o in bpy.data.objects:
    if o.type!='MESH' or 'ReturnChannel' not in o.name:continue
    bm=bmesh.new();bm.from_mesh(o.data);bm.normal_update()
    for face in o.data.polygons:face.use_smooth=True
    sharp=o.data.attributes.get('sharp_edge') or o.data.attributes.new('sharp_edge','BOOLEAN','EDGE')
    for edge in bm.edges:sharp.data[edge.index].value=not edge.is_manifold or edge.calc_face_angle()>=.55
    bm.free()

drift=[name for name,digest in retained.items() if fingerprint(bpy.data.objects[name])!=digest]
if drift:
    for index,key in enumerate(probe.data.shape_keys.key_blocks):
        a=np.zeros(len(key.data)*3,dtype=np.float32);key.data.foreach_get('co',a)
        if not np.array_equal(a,probe_keys[index]):print('KEY_DRIFT',index,float(np.max(np.abs(a-probe_keys[index]))),flush=True)
    print('FACE_DRIFT',probe_faces==[tuple(p.vertices) for p in probe.data.polygons],flush=True)
assert not drift,('Non-guard geometry drift',drift)
bpy.context.view_layer.update();scene.frame_set(1);bpy.ops.wm.save_as_mainfile(filepath=str(target),compress=True)
bpy.ops.object.select_all(action='DESELECT');root=bpy.data.objects['IAM_MODULE']
for o in [root,*root.children_recursive]:o.select_set(True)
bpy.context.view_layer.objects.active=root;component=ROOT/'app/assets/collection/components/I_mouth_finish.glb'
bpy.ops.export_scene.gltf(filepath=str(component),export_format='GLB',use_selection=True,export_animations=False,export_morph=False,export_apply=False,export_extras=True)
report={**seed,'source':str(target.relative_to(ROOT)),'source_sha256':sha(target),'component':str(component.relative_to(ROOT)),'component_sha256':sha(component),'seed_source_sha256':seed['source_sha256'],'guard_refinement':records,'unchanged_geometry_fingerprints':retained,'new_parts':list(dict.fromkeys(seed['new_parts']+[r['name'] for r in records])),'scope':'Local perforated guard bore topology, micro-bevel and authored material refinement. Non-guard geometry including all foil keys preserved. Scoped geometry and visual checks pending; no full A/main App acceptance.'}
(OUT/'build.json').write_text(json.dumps(report,indent=2)+'\n');print('I_MOUTH_FINISH_BUILT',flush=True)
