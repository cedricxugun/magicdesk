"""Canonical reusable specimen source, without the rejected book enclosure."""
import bpy,json,pathlib
from mathutils import Matrix
ROOT=pathlib.Path(__file__).resolve().parents[2]
bpy.ops.wm.open_mainfile(filepath=str(ROOT/'blender/collection/G_archive_detail.blend'))
source=json.loads((ROOT/'app/assets/collection/models/G_archive_detail.json').read_text(encoding='utf-8'))
catalog=source['g_archive']['contents'];keep=set()
for item in catalog:
    node=bpy.data.objects[item['root']];keep.update([node]+list(node.children_recursive));node.parent=None;node.matrix_world=Matrix.Identity(4)
for obj in list(bpy.data.objects):
    if obj not in keep:bpy.data.objects.remove(obj,do_unlink=True)
for obj in keep:obj.animation_data_clear();obj.hide_render=False;obj.hide_viewport=False;obj.hide_set(False)
bpy.context.scene.name='G_Curiosities';bpy.context.scene.frame_set(1)
(ROOT/'blender/collection/G_curiosities.json').write_text(json.dumps({'contents':catalog,'source':'Six authored, rigged curiosities reused by the record player'},ensure_ascii=False,indent=2),encoding='utf-8')
bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'blender/collection/G_curiosities.blend'))
