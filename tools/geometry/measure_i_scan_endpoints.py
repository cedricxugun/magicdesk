"""Read current mouth tip geometry, without saving or modifying the source."""
import bpy,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
bpy.ops.wm.open_mainfile(filepath=str(ROOT/'blender/collection/I_collar_clamps.blend'))
bpy.context.scene.frame_set(1);bpy.context.view_layer.update()
mouth=bpy.data.objects['IAM_Mouth'];inverse=mouth.matrix_world.inverted();rows=[]
for o in bpy.data.objects:
    if 'Tine' not in o.name or o.type!='MESH':continue
    points=[inverse@o.matrix_world@v.co for v in o.data.vertices]
    rows.append({'name':o.name,'min':[min(v[i] for v in points) for i in range(3)],'max':[max(v[i] for v in points) for i in range(3)],'parent':o.parent.name if o.parent else None})
p=ROOT/'review/I_refinement/moonlight/central_scan_r1/tip_measurements.json';p.write_text(json.dumps(rows,indent=2)+'\n');print('I_SCAN_TIPS_MEASURED',len(rows))
