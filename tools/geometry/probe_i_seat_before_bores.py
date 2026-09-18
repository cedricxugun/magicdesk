import bpy,json,sys
from pathlib import Path
from mathutils import Matrix
from mathutils.bvhtree import BVHTree
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'blender/collection'));import i_fitted_surface as fitted;import i_fitted_laminate as laminate
p=ROOT/'review/I_refinement/nautilus_r1/chamber_seats_r9';current=json.loads((p/'build.json').read_text());seed=json.loads((ROOT/'review/I_refinement/nautilus_r1/receiver_pocket_r8/build.json').read_text());plan=json.loads((p/'layout_candidates.json').read_text());bpy.ops.wm.open_mainfile(filepath=str(ROOT/seed['source']));bpy.context.scene.frame_set(1);bpy.context.view_layer.update()
def geo(o):
    o.data.calc_loop_triangles();return BVHTree.FromPolygons([o.matrix_world@v.co for v in o.data.vertices],[tuple(t.vertices) for t in o.data.loop_triangles],all_triangles=True)
core=bpy.data.objects['IN3_ContinuousThroat'];film=bpy.data.objects['IN1_CellDiaphragm_01'];frame=bpy.data.objects['IN1_CellFrame_01'];ct,mt,ft=geo(core),geo(film),geo(frame);rows=[]
for seat in current['chamber_seats']:
    row=next(r for r in plan['candidates'] if r['cell']==1 and r['side']==seat['side'] and r['phi']==seat['phi']);matrix=Matrix(row['matrix']);outline=row['outline']
    fu=fitted.clipped_surface([frame],outline,frame=matrix,from_positive=False,normal_limit=.8,with_planes=True);mf=fitted.clipped_surface([film],outline,frame=matrix,from_positive=True,normal_limit=.8,with_planes=True);mb=fitted.clipped_surface([film],outline,frame=matrix,from_positive=False,normal_limit=.8,with_planes=True);cf=fitted.clipped_surface([core],outline,frame=matrix,from_positive=True,normal_limit=.8,with_planes=True)
    for tag,a,b in [('upper',fu,mf),('lower',mb,cf)]:
        vs,fs,fit=laminate.between(a,b);m=bpy.data.meshes.new('RawSeat');m.from_pydata(vs,[],fs);m.update();m.calc_loop_triangles();tree=BVHTree.FromPolygons([matrix@v.co for v in m.vertices],[tuple(t.vertices) for t in m.loop_triangles],all_triangles=True);rows.append({'seat':seat['frame'],'part':tag,'core':len(tree.overlap(ct)),'film':len(tree.overlap(mt)),'frame':len(tree.overlap(ft)),'surface_deviations':fit['surface_deviations']});bpy.data.meshes.remove(m)
(p/'before_bores_probe.json').write_text(json.dumps(rows,indent=2)+'\n');print(json.dumps(rows),flush=True)
