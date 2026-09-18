"""Compare rendered geometry before/after the specific opposed-triangle repair."""
import bpy,json,hashlib,collections
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];OUT=ROOT/'review/I_refinement/nautilus_r1/throat_terminations_r16/triangles';s=json.loads((OUT/'build.json').read_text());parent=json.loads((ROOT/s['render_triangle_repair']['parent_report']).read_text());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();assert sha(ROOT/s['source'])==s['source_sha256'];assert sha(ROOT/parent['source'])==parent['source_sha256']==s['parent_source_sha256']
bpy.ops.wm.open_mainfile(filepath=str(ROOT/s['source']));bpy.context.scene.frame_set(1);bpy.context.view_layer.update();name=s['render_triangle_repair']['mesh'];current=bpy.data.objects[name]
with bpy.data.libraries.load(str(ROOT/parent['source']),link=False) as (src,dst):dst.objects=[name]
old=dst.objects[0]
def world(o):
    assert not o.constraints and o.animation_data is None
    return world(o.parent)@o.matrix_parent_inverse@o.matrix_basis if o.parent else o.matrix_basis.copy()
original_matrix=world(old);matrix_error=max(abs(original_matrix[i][j]-current.matrix_world[i][j]) for i in range(4) for j in range(4));assert matrix_error<1e-7
def triangles(o):
    o.data.calc_loop_triangles();result=collections.Counter()
    for t in o.data.loop_triangles:
        p=tuple(tuple(o.data.vertices[i].co) for i in t.vertices);oriented=min(p,p[1:]+p[:1],p[2:]+p[:2]);result[(oriented,o.data.polygons[t.polygon_index].material_index)]+=1
    return result
a=triangles(old);b=triangles(current);removed=list((a-b).elements());added=list((b-a).elements());pairs=collections.defaultdict(list)
for points,material in removed:pairs[(tuple(sorted(points)),material)].append(points)
opposed=all(len(rows)==2 and tuple(reversed(rows[0])) in [rows[1],rows[1][1:]+rows[1][:1],rows[1][2:]+rows[1][:2]] for rows in pairs.values())
r={'source_sha256':s['source_sha256'],'parent_source_sha256':parent['source_sha256'],'passed':not added and len(removed)==4 and len(pairs)==2 and opposed,'matrix_error':matrix_error,'added_render_triangles':len(added),'removed_render_triangles':len(removed),'opposed_zero_thickness_pairs':len(pairs),'retained_render_triangles':sum(b.values()),'scope':'Exact local-coordinate, winding and material-slot multiset comparison; only two opposed zero-thickness pairs removed, with unchanged world transform. Not complete art, all runtime normals/LOD, native interaction or device acceptance.'}
(OUT/'render_geometry_preservation.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(r),flush=True)
