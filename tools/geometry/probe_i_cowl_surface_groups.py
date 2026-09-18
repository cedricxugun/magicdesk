import bpy,bmesh,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];s=json.loads((ROOT/'review/I_refinement/nautilus_r1/mouth_finish_r21/build.json').read_text());bpy.ops.wm.open_mainfile(filepath=str(ROOT/s['source']))
rows=[]
for n in [1,5,6]:
    o=bpy.data.objects['IN1_PorcelainPanel_%02d'%n];bm=bmesh.new();bm.from_mesh(o.data);bm.normal_update();bm.faces.index_update();groups=[];remaining=set(bm.faces)
    while remaining:
        f=remaining.pop();component={f};pending=[f]
        while pending:
            for e in pending.pop().edges:
                if not e.is_manifold or e.calc_face_angle()>.80:continue
                for other in e.link_faces:
                    if other in remaining:remaining.remove(other);component.add(other);pending.append(other)
        groups.append({'faces':len(component),'area':sum(f.calc_area()for f in component),'face_indices':[f.index for f in component]})
    groups.sort(key=lambda g:g['area'],reverse=True);rows.append({'mesh':o.name,'groups':groups});print(o.name,[{'faces':g['faces'],'area':g['area']}for g in groups[:8]],flush=True);bm.free()
(ROOT/'review/I_refinement/nautilus_r1/cowl_fairing_r22/surface_groups.json').write_text(json.dumps(rows,separators=(',',':'))+'\n')
