"""Reuse the independently authored observatory in assembly generators."""
import bpy,json,math
from pathlib import Path
from mathutils import Matrix
ROOT=Path(__file__).resolve().parents[2]
def replace_observatory(catalog,print_root,target_collection=None):
    folder=ROOT/'app/assets/collection/components'
    entry=json.loads((folder/'G_observatory_r2.json').read_text())
    old=bpy.data.objects[catalog[0]['root']]
    for obj in list(old.children_recursive)+[old]:bpy.data.objects.remove(obj,do_unlink=True)
    before=set(bpy.data.objects);bpy.ops.import_scene.gltf(filepath=str(folder/'G_observatory_r2.glb'));added=set(bpy.data.objects)-before
    root=next(o for o in added if o.name==entry['root']);root.parent=print_root
    yaw=json.loads((ROOT/'production/G_optical_curator/observatory_r2/playback_alignment.json').read_text())['mount_yaw'];offset=entry['mount_offset_y'];entry['mount_yaw']=yaw
    root.matrix_basis=Matrix.Translation((0,0,offset))@Matrix.Rotation(yaw,4,'Z')
    keep={root,*root.children_recursive}
    for obj in added-keep:bpy.data.objects.remove(obj,do_unlink=True)
    if target_collection:
        for obj in keep:
            for collection in list(obj.users_collection):collection.objects.unlink(obj)
            target_collection.objects.link(obj)
    def mount(point):
        x,y,z=point;return [math.cos(yaw)*x+math.sin(yaw)*z,y+offset,-math.sin(yaw)*x+math.cos(yaw)*z]
    entry['structure_edges']=[[mount(p) for p in edge] for edge in entry['structure_edges']]
    for guide in entry['build_guides']:guide['points']=[mount(p) for p in guide['points']]
    catalog[0]=entry;return root
