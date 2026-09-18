import bpy,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];OUT=ROOT/'review/I_refinement/nautilus_r1/chamber_motion_r36';s=json.loads((OUT/'build.json').read_text());d=json.loads((OUT/'morph_geometry_check.json').read_text());bpy.ops.wm.open_mainfile(filepath=str(ROOT/s['source']))
for r in d['contacts'][:1]:
    o=bpy.data.objects[r['mesh']];o.data.calc_loop_triangles()
    for detail in r['details']:
        for i in detail['faces']:
            t=o.data.loop_triangles[i];f=o.data.polygons[t.polygon_index];print(o.name,i,'material',f.material_index,o.data.materials[f.material_index].name,'normal',list(f.normal),flush=True)
