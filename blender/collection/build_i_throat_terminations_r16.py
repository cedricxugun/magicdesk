"""Local closed terminations around the fixed throat; preserve all installed seats."""
import bpy,bmesh,json,hashlib,sys,shutil,struct
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(Path(__file__).parent));import i_throat_keepout as keepout;import i_boolean_residue as residue
OUT=ROOT/'review/I_refinement/nautilus_r1/throat_terminations_r16';OUT.mkdir(parents=True,exist_ok=True);TARGET=ROOT/'blender/collection/I_nautilus_throat_terminations_r16.blend';COMPONENT=ROOT/'app/assets/collection/components/I_nautilus_throat_terminations_r16.glb';sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
parent_report=ROOT/'review/I_refinement/nautilus_r1/throat_sockets_r13/build.json';seed=json.loads(parent_report.read_text());assert sha(ROOT/seed['source'])==seed['source_sha256'];assert json.loads((parent_report.parent/'checkpoint.json').read_text())['source_sha256']==seed['source_sha256']
if TARGET.exists():
    old=json.loads((OUT/'build.json').read_text());assert sha(TARGET)==old['source_sha256'];archive=OUT/'iterations'/old['source_sha256'][:12];archive.mkdir(parents=True,exist_ok=True)
    for p in OUT.glob('*.json'):shutil.copy2(p,archive/p.name)
    if (OUT/'views').exists():shutil.copytree(OUT/'views',archive/'views',dirs_exist_ok=True)
    shutil.copy2(TARGET,TARGET.parent/'checkpoints'/('I-throat-termination-'+old['source_sha256'][:12]+'.blend'))
bpy.ops.wm.open_mainfile(filepath=str(ROOT/seed['source']));scene=bpy.context.scene;scene.frame_set(1);bpy.context.view_layer.update();body=bpy.data.objects['IN1_BodyRoot'];names=['IN1_CellDiaphragm_07','IN1_CellDiaphragm_08','IN1_CellDiaphragm_09','IN1_CellFrame_08','IN1_CellFrame_09']
def fingerprint(o):
    d=hashlib.sha256()
    for v in o.data.vertices:d.update(struct.pack('<3f',*v.co))
    for f in o.data.polygons:d.update(struct.pack('<'+'I'*len(f.vertices),*f.vertices))
    return [d.hexdigest(),[list(r) for r in o.matrix_world],o.parent.name if o.parent else None,[m.name if m else None for m in o.data.materials]]
protected={o.name:fingerprint(o) for o in bpy.data.objects if o.type=='MESH' and o.name not in names}
def mesh_tree(o):
    o.data.calc_loop_triangles();return BVHTree.FromPolygons([o.matrix_world@v.co for v in o.data.vertices],[tuple(t.vertices) for t in o.data.loop_triangles],all_triangles=True)
col=bpy.data.collections.new('I_THROAT_TERMINATION_WORK');scene.collection.children.link(col);placement=bpy.data.objects['IC1_MouthMount'].matrix_world.copy()
source_core=bpy.data.objects['IN3_ContinuousThroat'];inverse=placement.inverted();flange_points=[source_core.matrix_world@v.co for v in source_core.data.vertices if (inverse@source_core.matrix_world@v.co).z<.661]
core_tool=keepout.core_envelope(placement,col);collar_tool=keepout.collar_envelope([bpy.data.objects[n] for n in ['IC1_CollarUpper','IC1_CollarLower']],col,extra_points=flange_points);bpy.context.view_layer.update()
bpy.context.view_layer.objects.active=core_tool;mod=core_tool.modifiers.new('Single closed collar and core keepout','BOOLEAN');mod.operation='UNION';mod.solver='MANIFOLD';mod.object=collar_tool;bpy.ops.object.modifier_apply(modifier=mod.name);bpy.data.objects.remove(collar_tool,do_unlink=True)
envelope_checks=[]
for tool,sources in [(core_tool,['IN3_ContinuousThroat','IC1_CollarUpper','IC1_CollarLower'])]:
    bvh=mesh_tree(tool)
    for name in sources:
        o=bpy.data.objects[name];intersections=bvh.overlap(mesh_tree(o));nearest=[];unsigned=[];ambiguous=[]
        for v in o.data.vertices:
            p=o.matrix_world@v.co;hit=bvh.find_nearest(p);assert hit[0] is not None;nearest.append((p-hit[0]).dot(hit[1]));unsigned.append(hit[3])
            if nearest[-1]>=-.00015:ambiguous.append(p)
        # A nearest triangle's plane is not an inside test at a concave union
        # edge. Check closed-volume parity in three nonaligned directions.
        probes=ambiguous+[o.matrix_world@o.data.vertices[0].co];outside=[]
        for p in probes:
            votes=[]
            for axis in [(1.,.3917,.1731),(.2319,1.,.5173),(.3171,.1739,1.)]:
                direction=Vector(axis).normalized();start=p.copy();count=0
                for _ in range(24):
                    hit=bvh.ray_cast(start,direction,10.)
                    if hit[0] is None:break
                    count+=1;start=hit[0]+direction*.000001
                votes.append(count%2)
            if votes!=[1,1,1]:outside.append({'point':list(p),'votes':votes})
        envelope_checks.append({'envelope':tool.name,'source_mesh':name,'surface_intersections':len(intersections),'maximum_nearest_plane_sign':max(nearest),'minimum_unsigned_vertex_distance':min(unsigned),'concave_parity_probes':len(probes),'outside_probes':outside[:12]})
        assert not intersections and min(unsigned)>.00015 and not outside,('Envelope does not contain original geometry',envelope_checks[-1])
rows=[]
for name in names:
    o=bpy.data.objects[name];before=fingerprint(o);bm=bmesh.new();bm.from_mesh(o.data);volume_before=bm.calc_volume(signed=True);bm.free()
    # The source already has frozen triangles after its bore machining.
    o.data.calc_loop_triangles();old=o.data;triangles=list(old.loop_triangles);m=bpy.data.meshes.new(name+'_R16SourceTriangles');m.from_pydata([tuple(v.co) for v in old.vertices],[],[tuple(t.vertices) for t in triangles]);m.update()
    for material in old.materials:m.materials.append(material)
    for p,t in zip(m.polygons,triangles):p.material_index=old.polygons[t.polygon_index].material_index;p.use_smooth=old.polygons[t.polygon_index].use_smooth
    for layer in old.uv_layers:
        uv=m.uv_layers.new(name=layer.name)
        for i,t in enumerate(triangles):
            for j,loop in enumerate(t.loops):uv.data[i*3+j].uv=layer.data[loop].uv
    m.normals_split_custom_set([old.corner_normals[i].vector.copy() for t in triangles for i in t.loops]);o.data=m
    bpy.context.view_layer.objects.active=o;mod=o.modifiers.new('Closed throat termination','BOOLEAN');mod.operation='DIFFERENCE';mod.solver='EXACT';mod.object=core_tool;bpy.ops.object.modifier_apply(modifier=mod.name)
    bm=bmesh.new();bm.from_mesh(o.data);bmesh.ops.remove_doubles(bm,verts=list(bm.verts),dist=1e-7);bmesh.ops.dissolve_degenerate(bm,edges=list(bm.edges),dist=1e-7);cleanup=residue.repair(bm);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces))
    if bm.calc_volume(signed=True)<0:bmesh.ops.reverse_faces(bm,faces=list(bm.faces))
    volume_after=bm.calc_volume(signed=True);assert volume_after>0 and volume_after/volume_before>.60,('Termination removed too much material',name,volume_after/volume_before)
    rows.append({'mesh':name,'source_fingerprint':before,'volume_before':volume_before,'volume_after':volume_after,'retained_volume_fraction':volume_after/volume_before,'nonmanifold_edges':sum(not e.is_manifold for e in bm.edges),**cleanup});bm.to_mesh(o.data);bm.free();print('THROAT_END_TRIM',name,volume_after/volume_before,flush=True)
bpy.data.objects.remove(core_tool,do_unlink=True);bpy.context.view_layer.update();changed=[n for n,f in protected.items() if fingerprint(bpy.data.objects[n])!=f];assert not changed,changed
bpy.ops.wm.save_as_mainfile(filepath=str(TARGET),compress=True);bpy.ops.object.select_all(action='DESELECT')
for o in [body,*body.children_recursive]:o.select_set(True)
bpy.context.view_layer.objects.active=body;bpy.ops.export_scene.gltf(filepath=str(COMPONENT),export_format='GLB',use_selection=True,export_animations=False,export_morph=False,export_extras=True)
result={**seed,'source':str(TARGET.relative_to(ROOT)),'source_sha256':sha(TARGET),'component':str(COMPONENT.relative_to(ROOT)),'component_sha256':sha(COMPONENT),'parent_source_sha256':seed['source_sha256'],'status':'throat_termination_shape_candidate_checks_pending','interface_trim':{'targets':names,'keepout_margin':.004,'envelope_checks':envelope_checks,'trim_rows':rows,'protected_mesh_count':len(protected)},'review_scope':'Preserved original mouth/body/core/collar and installed support geometry. Only five old chamber pieces receive closed local terminations around a filled clearance envelope. Actual contacts, fitted seat preservation, retained components, edge capture and visual correspondence still require checks. Not finished I or native App.'}
result['interface_trim']['parent_report']=str(parent_report.relative_to(ROOT));result['interface_trim']['reference_interfaces']=str((parent_report.parent/'remaining_interfaces.json').relative_to(ROOT));result['socket_parent_topology']=str((parent_report.parent/'topology_check.json').relative_to(ROOT))
(OUT/'build.json').write_text(json.dumps(result,indent=2)+'\n');(OUT/'protected_geometry.json').write_text(json.dumps({'source_sha256':result['source_sha256'],'passed':not changed,'count':len(protected),'changed':changed,'allowed_meshes':names},indent=2)+'\n');print('THROAT_TERMINATION_BUILT',result['source_sha256'],flush=True)
