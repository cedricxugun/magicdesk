import bpy,bmesh,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];spec=json.loads((ROOT/'review/I_refinement/nautilus_r1/front_sockets_r12/build.json').read_text());bpy.ops.wm.open_mainfile(filepath=str(ROOT/spec['source']))
o=bpy.data.objects['IN1_CellDiaphragm_05'];bm=bmesh.new();bm.from_mesh(o.data);bm.verts.ensure_lookup_table();bm.verts.index_update();bm.faces.ensure_lookup_table();bm.faces.index_update()
rows=[]
for e in bm.edges:
    if e.is_manifold:continue
    rows.append({'edge':[v.index for v in e.verts],'faces':[{'index':f.index,'vertices':[v.index for v in f.verts],'area':f.calc_area(),'normal':list(f.normal)} for f in e.link_faces]})
print(json.dumps(rows,indent=2));bm.free()
