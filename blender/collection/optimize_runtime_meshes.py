"""Batch meshes only within the same rigid parent; retain all rig empties.

Blender source stays unbatched and editable. Material slots, UVs, world-space
bounds and control hierarchies are preserved in the runtime GLB.
"""
import bpy,sys
from pathlib import Path
def optimize(path):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.gltf(filepath=str(path))
    groups={};before=sum(o.type=='MESH' for o in bpy.data.objects)
    vertices_before=sum(len(o.data.vertices) for o in bpy.data.objects if o.type=='MESH')
    polygons_before=sum(len(o.data.polygons) for o in bpy.data.objects if o.type=='MESH')
    for obj in list(bpy.data.objects):
        if obj.type=='MESH' and obj.parent and not obj.data.shape_keys:
            groups.setdefault(obj.parent,[]).append(obj)
    for parent,items in groups.items():
        if len(items)<2:continue
        bpy.ops.object.select_all(action='DESELECT')
        for obj in items:obj.select_set(True)
        # Imported screws/lenses share datablocks across different rig groups.
        # Joining must never mutate a datablock used by another rigid group.
        items[0].data=items[0].data.copy()
        bpy.context.view_layer.objects.active=items[0]
        bpy.ops.object.join()
        bpy.context.object.name=parent.name+'_RenderSurface'
    after=sum(o.type=='MESH' for o in bpy.data.objects)
    assert vertices_before==sum(len(o.data.vertices) for o in bpy.data.objects if o.type=='MESH'),'Batching changed vertex count'
    assert polygons_before==sum(len(o.data.polygons) for o in bpy.data.objects if o.type=='MESH'),'Batching changed polygon count'
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.export_scene.gltf(filepath=str(path),export_format='GLB',use_selection=True,export_apply=True,export_animations=False)
    print('RUNTIME_MESH_BATCH',path.name,before,'->',after,flush=True)
if __name__=='__main__':
    for ident in sys.argv[sys.argv.index('--')+1:]:
        optimize(Path(__file__).resolve().parents[2]/'app/assets/collection/models'/f'{ident}.glb')
