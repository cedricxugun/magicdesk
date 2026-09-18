"""Measure fitted clamp faces against their frame/film substrates after termination."""
import bpy,json,hashlib,sys
from pathlib import Path
from mathutils import Vector,Matrix
from mathutils.bvhtree import BVHTree
ROOT=Path(__file__).resolve().parents[2];args=sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else [];report=ROOT/next((a.split('=',1)[1] for a in args if a.startswith('--report=')),'review/I_refinement/nautilus_r1/throat_terminations_r16/build.json');spec=json.loads(report.read_text());assert hashlib.sha256((ROOT/spec['source']).read_bytes()).hexdigest()==spec['source_sha256'];bpy.ops.wm.open_mainfile(filepath=str(ROOT/spec['source']));bpy.context.scene.frame_set(1);bpy.context.view_layer.update()
targets=set(spec.get('interface_trim',{}).get('targets',['IN1_CellDiaphragm_07','IN1_CellDiaphragm_08','IN1_CellDiaphragm_09','IN1_CellFrame_08','IN1_CellFrame_09']));trees={};rows=[]
for name in targets:
    o=bpy.data.objects[name];o.data.calc_loop_triangles();trees[name]=BVHTree.FromPolygons([o.matrix_world@v.co for v in o.data.vertices],[tuple(t.vertices) for t in o.data.loop_triangles],all_triangles=True)
for seat in spec['front_sockets']['seats']:
    matrix=Matrix(seat['matrix_blender']);axis=(matrix.to_3x3()@Vector((0,0,1))).normalized()
    for part_name,target_name,sign in [(seat['cap'],seat['source_frame'],-1),(seat['upper'],seat['source_frame'],1),(seat['upper'],seat['source_film'],-1),(seat['outer_stand'],seat['source_film'],1)]:
        if target_name not in targets:continue
        o=bpy.data.objects[part_name];o.data.calc_loop_triangles();direction=axis*sign;gaps=[];bad=[]
        for triangle in o.data.loop_triangles:
            a,b,c=[o.matrix_world@o.data.vertices[i].co for i in triangle.vertices];normal=(b-a).cross(c-a).normalized()
            if normal.dot(direction)<.5:continue
            for weights in [(1/3,1/3,1/3),(.6,.2,.2),(.2,.6,.2),(.2,.2,.6)]:
                p=a*weights[0]+b*weights[1]+c*weights[2];hit=trees[target_name].ray_cast(p-direction*.00005,direction,.05);gap=hit[3]-.00005 if hit[0] is not None else None
                if gap is not None:gaps.append(gap)
                if gap is None or gap<-.00002 or gap>.0006:bad.append({'triangle':triangle.index,'point':list(p),'gap':gap})
        rows.append({'seat':seat['frame'],'contact_part':part_name,'substrate':target_name,'samples':len(gaps)+sum(r['gap'] is None for r in bad),'minimum_gap':min(gaps) if gaps else None,'maximum_gap':max(gaps) if gaps else None,'bad_count':len(bad),'bad_samples':bad[:12],'passed':bool(gaps) and not bad})
result={'source_sha256':spec['source_sha256'],'passed':all(r['passed'] for r in rows),'rows':rows,'scope':'Four interior samples on every clamp triangle facing the affected frame/film. Checks installed seat gaps after trimming; does not prove complete continuous surface coverage, loads, full animation, native or art acceptance.'}
(report.parent/'seat_surface_preservation.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({'passed':result['passed'],'failures':[r for r in rows if not r['passed']],'sample_count':sum(r['samples'] for r in rows)}),flush=True)
