"""Preserve the corrected cowl; form one hollow throat/core and its real flange."""
import bpy,bmesh,json,hashlib,math,sys,struct,shutil
from pathlib import Path
from mathutils import Vector,Matrix
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(Path(__file__).parent))
import i_machined_geometry as h
from i_nautilus_receiver_recess import exterior_signature,form_recess
OUT=ROOT/'review/I_refinement/nautilus_r1/core_bridge_r4';OUT.mkdir(parents=True,exist_ok=True)
TARGET=ROOT/'blender/collection/I_nautilus_core_bridge_r4.blend'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
seed=json.loads((ROOT/'review/I_refinement/nautilus_r1/mouth_relation_r3/build.json').read_text())
donor=json.loads((ROOT/'review/I_refinement/part_c_core/continuous_c3/build.json').read_text())
for spec in [seed,donor]:assert sha(ROOT/spec['source'])==spec['source_sha256']
assert seed['source_sha256']=='d84b7d87421969e583fe6d6032e986c3ce2959c937d2a512c23ea12e14be8074'
if TARGET.exists():
    old=json.loads((OUT/'build.json').read_text());assert sha(TARGET)==old['source_sha256'],'Unrecorded core bridge edits'
    archive=OUT/'iterations'/old['source_sha256'][:12];archive.mkdir(parents=True,exist_ok=True)
    for p in OUT.glob('*.json'):shutil.copy2(p,archive/p.name)
    if (OUT/'views').exists():shutil.copytree(OUT/'views',archive/'views',dirs_exist_ok=True)
    (TARGET.parent/'checkpoints'/('I-nautilus-core-bridge-'+old['source_sha256'][:12]+'.blend')).write_bytes(TARGET.read_bytes())
bpy.ops.wm.open_mainfile(filepath=str(ROOT/seed['source']));scene=bpy.context.scene;scene.frame_set(1);bpy.context.view_layer.update()
body=bpy.data.objects['IN1_BodyRoot'];placement=bpy.data.objects['IAM_MODULE'].matrix_world.copy()
def fingerprint(o):
    digest=hashlib.sha256()
    for v in o.data.vertices:digest.update(struct.pack('<3f',*v.co))
    for f in o.data.polygons:digest.update(struct.pack('<I',len(f.vertices)));digest.update(struct.pack('<'+'I'*len(f.vertices),*f.vertices))
    return {'geometry':digest.hexdigest(),'matrix':[list(r) for r in o.matrix_world],'parent':o.parent.name if o.parent else None,'materials':[m.name if m else None for m in o.data.materials]}
protected={o.name:fingerprint(o) for o in bpy.data.objects if o.type=='MESH' and (o.name.startswith(('IAM_','IN1_Porcelain','IN1_Fixed','IN1_PanelRim','IN1_Hub','IN1_SpiralHub','IN1_FittedSaddle')) or o.name.startswith('BASE_FIXED'))}
recess_outer_before=exterior_signature(bpy.data.objects['IN1_PorcelainPanel_02'])
col=bpy.data.collections.new('I_NAUTILUS_CORE_BRIDGE_R4');scene.collection.children.link(col);h.configure(col);root=h.empty('IN3_CoreBridge',body)
# Reuse only the measured clamp, including the C3-drilled axial bolt pattern.
# None of the rejected conch body, legs, rails or prior throat is appended.
with bpy.data.libraries.load(str(ROOT/donor['source']),link=False) as (src,dst):dst.collections=['I_C_MOUNT_C1']
scene.collection.children.link(dst.collections[0]);clamp_root=bpy.data.objects['IC1_Module'];clamp_root.parent=root;clamp_root.matrix_world=Matrix.Identity(4)
mount=bpy.data.objects['IC1_MouthMount'];mount.matrix_world=placement
bpy.context.view_layer.update()
from i_nautilus_compact_clamp import rebuild_halves
clamp_profile=rebuild_halves(mount,col,h)
center=placement.translation.copy();n=(placement.to_3x3()@Vector((0,0,1))).normalized();right=(placement.to_3x3()@Vector((1,0,0))).normalized();up=(placement.to_3x3()@Vector((0,1,0))).normalized();scale=placement.to_scale().x
C=Vector((.12,.16,1.96));outer_radii=Vector((.83,.49,.92));inner_radii=outer_radii-Vector((.028,.028,.028))
front_depth=.6395*scale;back_depth=.6575*scale;section_depth=.70
N=160;LOFT=40;DOME=90;vertices=[];faces=[];material_indices=[]
def ring(points):
    ids=list(range(len(vertices),len(vertices)+N));vertices.extend(tuple(p) for p in points);return ids
def circle(radius,depth):return ring([center+n*depth+(right*math.cos(k*math.tau/N)+up*math.sin(k*math.tau/N))*radius for k in range(N)])
def stitch(a,b,inside=False,metal=0):
    for k in range(N):
        q=(a[k],a[(k+1)%N],b[(k+1)%N],b[k]);faces.append(q[::-1] if inside else q);material_indices.append(metal)
def section(radii,depth,angle):
    qn=Vector(tuple(radii[i]**2*n[i] for i in range(3)));h2=n.dot(qn);c0=(C-center).dot(n)
    radial=right*math.cos(angle)+up*math.sin(angle);w=sum((radial[i]/radii[i])**2 for i in range(3));e=1.-(depth-c0)**2/h2
    assert e>=-1e-8
    p=C+qn*((depth-c0)/h2)+radial*math.sqrt(max(0.,e)/w)
    derivative=qn/h2-radial*((depth-c0)/(h2*math.sqrt(max(e,1e-10)*w)))
    return p,derivative
first=[];section_rows=[]
for inside,radii,neck_radius in [(False,outer_radii,.490*scale),(True,inner_radii,.460*scale)]:
    rings=[circle((.460 if inside else .565)*scale,front_depth),circle((.460 if inside else .510)*scale,back_depth)]
    if not inside:rings.append(circle(neck_radius,back_depth))
    first.append(rings[0]);begin=[center+n*back_depth+(right*math.cos(k*math.tau/N)+up*math.sin(k*math.tau/N))*neck_radius for k in range(N)]
    ends=[section(radii,section_depth,k*math.tau/N) for k in range(N)];span=section_depth-back_depth
    for j in range(1,LOFT+1):
        t=j/LOFT;t2=t*t;t3=t2*t;points=[]
        for p,(end,derivative) in zip(begin,ends):
            points.append((2*t3-3*t2+1)*p+(t3-2*t2+t)*n*span+(-2*t3+3*t2)*end+(t3-t2)*derivative*span)
        rings.append(ring(points))
    c0=(C-center).dot(n);qn=Vector(tuple(radii[i]**2*n[i] for i in range(3)));extent=math.sqrt(n.dot(qn));a0=math.asin((section_depth-c0)/extent)
    for j in range(1,DOME):
        a=a0+(math.pi/2-a0)*j/DOME;depth=c0+extent*math.sin(a)
        rings.append(ring([section(radii,depth,k*math.tau/N)[0] for k in range(N)]))
    for j,(a,b) in enumerate(zip(rings,rings[1:])):stitch(a,b,inside,1 if j<(1 if inside else 2) else 0)
    tip=len(vertices);vertices.append(tuple(C+qn/extent))
    for k in range(N):
        q=(rings[-1][k],rings[-1][(k+1)%N],tip);faces.append(q[::-1] if inside else q);material_indices.append(0)
    section_rows.append({'wall':'inner' if inside else 'outer','radius':list(radii),'section_depth':section_depth,'flange_front':front_depth,'neck_start':back_depth,'neck_radius':neck_radius,'rings':len(rings)})
stitch(first[1],first[0],False,1)
m=bpy.data.meshes.new('IN3_ContinuousThroatMesh');m.from_pydata(vertices,[],faces);m.update();core=bpy.data.objects.new('IN3_ContinuousThroat',m);col.objects.link(core);core.parent=root
bronze=bpy.data.materials['IN1_AcousticBronze'].copy();bronze.name='IN3_InnerBronze';bsdf=bronze.node_tree.nodes.get('Principled BSDF');bsdf.inputs['Base Color'].default_value=(.115,.052,.02,1.);bsdf.inputs['Roughness'].default_value=.34
m.materials.append(bronze);m.materials.append(bpy.data.materials['Collection_A_Satin'])
for polygon,index in zip(m.polygons,material_indices):polygon.material_index=index;polygon.use_smooth=index==0
bm=bmesh.new();bm.from_mesh(m);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));assert not any(not e.is_manifold for e in bm.edges);bm.to_mesh(m);bm.free()
# Physical bores and fasteners use the preserved collar's actual local pattern.
fasteners=[]
seal=h.sleeve('IN3_CouplingSeal',.564,.479,.0007,mount,(0,0,.63905),'A_Rubber')
for i in range(6):
    angle=math.pi/6+i*math.tau/6;p=Vector((.502*math.cos(angle),.502*math.sin(angle),.639))
    h.drill(core,.0035,.026,mount,(p.x,p.y,.649))
    h.drill(seal,.0035,.020,mount,p)
    h.drill(bpy.data.objects['IC1_CollarUpper' if p.y>=0 else 'IC1_CollarLower'],.0035,.020,mount,(p.x,p.y,.633))
    prefix='IN3_CouplingBolt_%02d'%i
    shaft=h.cylinder(prefix,.0032,.034,mount,(p.x,p.y,.645),'A_Nickel')
    h.sleeve(prefix+'_Washer',.0065,.00365,.0018,mount,(p.x,p.y,.659),'A_Bronze')
    head=h.screw(prefix+'_Head',mount,(p.x,p.y,.662),.0055)
    bpy.context.view_layer.update();bpy.context.view_layer.objects.active=shaft
    mod=shaft.modifiers.new('One-piece bolt head and shank','BOOLEAN');mod.operation='UNION';mod.solver='EXACT';mod.object=head;bpy.ops.object.modifier_apply(modifier=mod.name);h.parts.remove(head.name);bpy.data.objects.remove(head,do_unlink=True)
    fasteners.append({'name':prefix,'mouth_local':list(p),'bore_radius':.0035,'shaft_radius':.0032,'shaft_interval':[.628,.662]})
bm=bmesh.new();bm.from_mesh(core.data);bmesh.ops.remove_doubles(bm,verts=list(bm.verts),dist=1e-7);bmesh.ops.dissolve_degenerate(bm,edges=list(bm.edges),dist=1e-8);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(core.data);bm.free()
old_core=bpy.data.objects['IN1_ContinuousAcousticChamber'];removed={'name':old_core.name,**fingerprint(old_core)};bpy.data.objects.remove(old_core,do_unlink=True)
cleanup=[]
for obj in list(body.children_recursive):
    if obj.type!='MESH' or not obj.name.startswith(('IN3_','IC1_')):continue
    bm=bmesh.new();bm.from_mesh(obj.data);before_nm=sum(not e.is_manifold for e in bm.edges)
    bmesh.ops.remove_doubles(bm,verts=list(bm.verts),dist=.000002);bmesh.ops.dissolve_degenerate(bm,edges=list(bm.edges),dist=.0000001)
    boundary={e for e in bm.edges if e.is_boundary};fills=0
    while boundary:
        edge=boundary.pop();group={edge};stack=[edge]
        while stack:
            e=stack.pop()
            for v in e.verts:
                for other in v.link_edges:
                    if other in boundary:boundary.remove(other);group.add(other);stack.append(other)
        lengths=[e.calc_length() for e in group]
        if len(group)==3 and (max(lengths)<.0015 or (max(lengths)<.040 and min(lengths)<max(lengths)*.05)):
            bmesh.ops.holes_fill(bm,edges=list(group),sides=3);fills+=1
    bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));cleanup.append({'name':obj.name,'nonmanifold_before':before_nm,'tiny_triangles_closed':fills,'nonmanifold_after':sum(not e.is_manifold for e in bm.edges)});bm.to_mesh(obj.data);bm.free()
recess=form_recess(bpy.data.objects['IN1_PorcelainPanel_02'],placement)
scene.frame_set(1);bpy.context.view_layer.update()
changed=[name for name,before in protected.items() if name!='IN1_PorcelainPanel_02' and fingerprint(bpy.data.objects[name])!=before]
assert recess_outer_before==exterior_signature(bpy.data.objects['IN1_PorcelainPanel_02'])
recess_after=fingerprint(bpy.data.objects['IN1_PorcelainPanel_02'])
assert all(recess_after[key]==protected['IN1_PorcelainPanel_02'][key] for key in ['matrix','parent','materials'])
assert not changed,('Protected outer/A source changed',changed)
bpy.ops.wm.save_as_mainfile(filepath=str(TARGET),compress=True)
bpy.ops.object.select_all(action='DESELECT')
for o in [body,*body.children_recursive]:o.select_set(True)
bpy.context.view_layer.objects.active=body;component=ROOT/'app/assets/collection/components/I_nautilus_core_bridge_r4.glb'
bpy.ops.export_scene.gltf(filepath=str(component),export_format='GLB',use_selection=True,export_animations=False,export_morph=False,export_extras=True)
result={**seed,'source':str(TARGET.relative_to(ROOT)),'source_sha256':sha(TARGET),'component':str(component.relative_to(ROOT)),'component_sha256':sha(component),'parent_source_sha256':seed['source_sha256'],'core_bridge':{'mesh':core.name,'clamp_donor_source_sha256':donor['source_sha256'],'clamp_root':clamp_root.name,'mount_node':mount.name,'section_rows':section_rows,'fasteners':fasteners,'new_hardware':list(h.parts),'removed_core':removed,'protected_meshes':len(protected)},'status':'continuous_throat_candidate_fit_pending','review_scope':'Preserves d84b7d87 outer/A geometry and poses. New integral hollow throat, machined flange and ellipsoid inner housing; measured C1 split clamp relocated with A. New fits, chamber-end seats, base load path, animation/optics and final art still require review. No native export.'}
result['core_bridge']['clamp_profile']=clamp_profile
result['core_bridge']['receiver_recess']=recess
result['core_bridge']['boolean_cleanup']=cleanup
result['core_bridge']['clamp_revision']='Measured A grip/seam hardware retained; tapered rear with a wider inward lip, smaller inboard bolt circle and shorter one-piece bolts. Old C3 axial holes are not retained.'
(OUT/'build.json').write_text(json.dumps(result,indent=2)+'\n');(OUT/'protected_geometry.json').write_text(json.dumps({'source_sha256':result['source_sha256'],'seed_source_sha256':seed['source_sha256'],'passed':not changed,'count':len(protected),'changed':changed,'receiver_recess':recess,'scope':'All protected source meshes exact except 02 inner pocket; 02 exterior face coordinates, winding and materials are exact. Not animation/lighting/art acceptance.'},indent=2)+'\n')
print('NAUTILUS_CONTINUOUS_THROAT_BUILT',flush=True)
