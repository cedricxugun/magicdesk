"""Cut bounded service pockets from the authoritative mesh with exact CSG.

Only internal service apertures change. Source GLB and external dimensions are
retained. Full boundary triangles are generated, not dropped by centroid.
"""
import bpy,math,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'app/assets/collection'
def sector(name,r0,r1,a0,a1,z0,z1):
    verts=[];faces=[];steps=max(8,int(a1-a0));n=steps+1
    for z in [z0,z1]:
        for r in [r0,r1]:
            for i in range(n):
                a=math.radians(a0+(a1-a0)*i/steps);verts.append((r*math.cos(a),r*math.sin(a),z))
    for i in range(steps):faces.extend([(i,n+i,n+i+1,i+1),(2*n+i,2*n+i+1,3*n+i+1,3*n+i),(i,i+1,2*n+i+1,2*n+i),(n+i,3*n+i,3*n+i+1,n+i+1)])
    faces.extend([(0,2*n,3*n,n),(n-1,2*n-1,4*n-1,3*n-1)])
    mesh=bpy.data.meshes.new(name);mesh.from_pydata(verts,[],faces)
    import bmesh
    bm=bmesh.new();bm.from_mesh(mesh);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(mesh);bm.free()
    o=bpy.data.objects.new(name,mesh);bpy.context.scene.collection.objects.link(o);return o
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=str(ROOT/'app/assets/helios_model.glb'))
source=bpy.data.objects['BASE_FIXED_DisplayMesh']
source_matrix=source.matrix_world.copy()
report={'source':'res://assets/helios_model.glb','source_node':source.name,'variants':{}}
for kind in ['helios','shared']:
    obj=source.copy();obj.data=source.data.copy();bpy.context.scene.collection.objects.link(obj);obj.parent=None;obj.matrix_world=source_matrix;obj.name='FRAME_'+kind
    cutters=[sector('DrawerPocket',.70,1.347,-140,-105,.465,.635)]
    if kind=='shared':cutters.append(sector('OperationCassettePocket',1.30,1.65,-136,-44,.162,.460))
    for cutter in cutters:
        modifier=obj.modifiers.new('Exact service pocket','BOOLEAN');modifier.operation='DIFFERENCE';modifier.solver='EXACT';modifier.object=cutter
        bpy.context.view_layer.objects.active=obj
        bpy.ops.object.modifier_apply(modifier=modifier.name)
        bpy.data.objects.remove(cutter,do_unlink=True)
    repaired=obj.data.validate(verbose=False,clean_customdata=False);obj.data.update()
    bpy.ops.object.select_all(action='DESELECT');obj.select_set(True);bpy.context.view_layer.objects.active=obj
    path=OUT/('frame_'+kind+'.glb')
    bpy.ops.export_scene.gltf(filepath=str(path),export_format='GLB',use_selection=True,export_apply=True,export_animations=False)
    report['variants'][kind]={'scene':'res://assets/collection/'+path.name,'node':obj.name,'material_names':[m.name if m else '' for m in obj.data.materials],'vertices':len(obj.data.vertices),'polygons':len(obj.data.polygons)}
    print('EXACT_BASE_FRAME',kind,len(obj.data.vertices),len(obj.data.polygons),'repaired_degenerate_edges',repaired,flush=True)
(OUT/'base_csg_source.json').write_text(json.dumps(report,indent=2))
