import bpy,bmesh,sys,math,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'blender/collection'))
import i_fitted_surface as fitted
s=json.loads((ROOT/'review/I_refinement/nautilus_r1/build.json').read_text());bpy.ops.wm.open_mainfile(filepath=str(ROOT/s['source']));bpy.context.scene.frame_set(1);bpy.context.view_layer.update()
skins=[o for o in bpy.data.objects if o.type=='MESH' and (o.name.startswith('IN1_FixedRearShell_') or o.name in ['IN1_PorcelainPanel_01','IN1_PorcelainPanel_02'])]
rows=[]
for cx,cy in [(-.18,.10),(.18,.04)]:
    outline=[(cx+.045*math.cos(math.tau*k/32),cy+.045*math.sin(math.tau*k/32)) for k in range(32)]
    p,f,e=fitted.clipped_surface(skins,outline,z_limit=1.2)
    vv,ff=fitted.extruded_patch(p,f,e,-.0002,bottom_offset=-.0062)
    m=bpy.data.meshes.new('SeatAudit');m.from_pydata(vv,[],ff);m.update()
    for epsilon in [0.,1e-8,1e-7,1e-6]:
        bm=bmesh.new();bm.from_mesh(m)
        if epsilon:
            bmesh.ops.remove_doubles(bm,verts=list(bm.verts),dist=epsilon);bmesh.ops.dissolve_degenerate(bm,edges=list(bm.edges),dist=epsilon)
        rows.append({'center':[cx,cy],'epsilon':epsilon,'defects':[(len(edge.link_faces),edge.calc_length()) for edge in bm.edges if not edge.is_manifold]});bm.free()
    bpy.data.meshes.remove(m)
(ROOT/'review/I_refinement/nautilus_r1/fitted_seat_audit.json').write_text(json.dumps(rows,indent=2)+'\n');print(json.dumps(rows),flush=True)
