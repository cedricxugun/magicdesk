import bpy,json,math
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
bpy.ops.wm.open_mainfile(filepath=str(ROOT/'blender/collection/S.blend'))
bpy.context.scene.frame_set(1);bpy.context.view_layer.update();deps=bpy.context.evaluated_depsgraph_get()
report=[]
for i in range(6):
    root=bpy.data.objects['S_C_Plaque'+str(i)];points=[]
    for obj in root.children_recursive:
        if obj.type!='MESH':continue
        evaluated=obj.evaluated_get(deps);mesh=evaluated.to_mesh()
        points.extend(evaluated.matrix_world@v.co for v in mesh.vertices);evaluated.to_mesh_clear()
    radius=[math.hypot(p.x,p.y) for p in points];angle=[math.degrees(math.atan2(p.y,p.x)) for p in points]
    item={'slot':i,'radius':[min(radius),max(radius)],'angle':[min(angle),max(angle)],'height':[min(p.z for p in points),max(p.z for p in points)]}
    item['inside_pocket']=item['radius'][0]>.70 and item['radius'][1]<1.347 and item['angle'][0]>-140 and item['angle'][1]<-105 and item['height'][0]>.469 and item['height'][1]<.616
    report.append(item)
result={'cards':report,'all_inside':all(x['inside_pocket'] for x in report)}
(ROOT/'tests/collection/selector_storage.json').write_text(json.dumps(result,indent=2));print('SELECTOR_STORAGE',json.dumps(result),flush=True)
