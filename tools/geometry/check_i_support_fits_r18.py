"""Measure actual shoe fits and retain source surfaces outside deliberate machining."""
import bpy,json,hashlib,struct,sys,math,numpy as np
from pathlib import Path
from mathutils import Vector,Matrix
from mathutils.bvhtree import BVHTree
sys.path.insert(0,str(Path(__file__).parent));from i_point_triangle_distance import distance_squared
ROOT=Path(__file__).resolve().parents[2];OUT=ROOT/'review/I_refinement/nautilus_r1/trunnion_support_r18';s=json.loads((OUT/'build.json').read_text());parent=json.loads((ROOT/'review/I_refinement/nautilus_r1/chamber04_r15/build.json').read_text());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();assert sha(ROOT/s['source'])==s['source_sha256'];assert sha(ROOT/parent['source'])==parent['source_sha256']==s['parent_source_sha256'];bpy.ops.wm.open_mainfile(filepath=str(ROOT/s['source']));bpy.context.scene.frame_set(1);bpy.context.view_layer.update()
def tree(o,matrix=None):
    matrix=o.matrix_world if matrix is None else matrix;o.data.calc_loop_triangles();return BVHTree.FromPolygons([matrix@v.co for v in o.data.vertices],[tuple(t.vertices) for t in o.data.loop_triangles],all_triangles=True)
def geometry_hash(mesh):
    h=hashlib.sha256()
    for v in mesh.vertices:h.update(struct.pack('<3f',*v.co))
    for f in mesh.polygons:h.update(struct.pack('<'+'I'*len(f.vertices),*f.vertices))
    return h.hexdigest()
parts=s['metal_supports'];names=parts['modified_meshes'];current={n:bpy.data.objects[n] for n in names};current_trees={n:tree(o) for n,o in current.items()}
with bpy.data.libraries.load(str(ROOT/parent['source']),link=False) as (src,dst):dst.objects=list(names)
old=dict(zip(names,dst.objects));preserved=[]
def machined(name,p):
    for port in parts['ports']:
        if name not in port['skins']:continue
        local=Matrix(port['matrix_blender']).inverted()@p
        if -.06<local.z<.70 and Vector((local.x,local.y,0)).length<port['cut_radius']+.0002:return True
    for bolt in parts['deck_fasteners']:
        if name==bolt['target'] and (Vector((p.x,p.y,0))-Vector((*bolt['xy'],0))).length<.0034 and p.z>bolt['expected_blind_floor_z']-.001:return True
    return False
for name in names:
    expected=parts['source_shapes'][name];assert geometry_hash(old[name].data)==expected[0];matrix=Matrix(expected[1]);assert max(abs(matrix[i][j]-current[name].matrix_world[i][j]) for i in range(4) for j in range(4))<1e-7;reference=tree(old[name],matrix);source_vertices=[tuple(matrix@v.co) for v in old[name].data.vertices];source_points=set(source_vertices);source_triangles=[[source_vertices[i] for i in t.vertices] for t in old[name].data.loop_triangles];bounds=np.array(source_triangles);low=bounds.min(axis=1);high=bounds.max(axis=1);o=current[name];points=[o.matrix_world@v.co for v in o.data.vertices];o.data.calc_loop_triangles();points.extend(sum((o.matrix_world@o.data.vertices[i].co for i in t.vertices),Vector())/3 for t in o.data.loop_triangles);maximum=0.;bad=[];count=0;identical=0;fallbacks=0
    for p in points:
        if machined(name,p):continue
        count+=1;q=tuple(p)
        if q in source_points:identical+=1;distance=0.
        else:
            hit=reference.find_nearest(p);assert hit[0] is not None;distance=math.sqrt(distance_squared(q,*source_triangles[hit[2]]))
            if distance>.000003:
                fallbacks+=1;radius=max(.000003,distance);indices=np.flatnonzero(np.all(low<=np.array(q)+radius,axis=1)&np.all(high>=np.array(q)-radius,axis=1))
                distance=min([distance]+[math.sqrt(distance_squared(q,*source_triangles[int(i)])) for i in indices])
        maximum=max(maximum,distance)
        if distance>.000003:bad.append({'point':list(p),'distance':distance})
    preserved.append({'mesh':name,'outside_machining_samples':count,'exact_original_vertex_matches':identical,'double_precision_bbox_fallbacks':fallbacks,'maximum_source_distance':maximum,'changed_samples':len(bad),'examples':bad[:8],'passed':not bad})
fits=[]
for support in parts['supports']:
    gasket=bpy.data.objects[support['shoe_gasket']];gasket.data.calc_loop_triangles();targets=[('gasket_to_deck',Vector((0,0,-1)),current_trees['IN1_DeckFoot']),('gasket_to_shoe',Vector((0,0,1)),tree(bpy.data.objects[support['shoe']]))]
    for tag,direction,target in targets:
        gaps=[];bad=[]
        for triangle in gasket.data.loop_triangles:
            a,b,c=[gasket.matrix_world@gasket.data.vertices[i].co for i in triangle.vertices];normal=(b-a).cross(c-a).normalized()
            if normal.dot(direction)<.4:continue
            for weights in [(1/3,1/3,1/3),(.6,.2,.2),(.2,.6,.2),(.2,.2,.6)]:
                p=a*weights[0]+b*weights[1]+c*weights[2];hit=target.ray_cast(p-direction*.00003,direction,.010);gap=hit[3]-.00003 if hit[0] is not None else None
                if gap is not None:gaps.append(gap)
                if gap is None or not -.00002<gap<.0005:bad.append({'point':list(p),'gap':gap,'triangle':triangle.index})
        fits.append({'support':support['anchor'],'fit':tag,'samples':len(gaps)+sum(r['gap'] is None for r in bad),'minimum_gap':min(gaps) if gaps else None,'maximum_gap':max(gaps) if gaps else None,'bad_count':len(bad),'examples':bad[:8],'passed':bool(gaps) and not bad})
r={'source_sha256':s['source_sha256'],'parent_source_sha256':parent['source_sha256'],'passed':all(r['passed'] for r in preserved+fits),'source_surface_checks':preserved,'shoe_fit_checks':fits,'scope':'Actual new source vertices/triangle interiors outside documented port and bolt cylinders versus original geometry; sampled gasket contact faces against real deck and formed shoe. Does not prove every continuous surface point, loads, all new-part containment, full motion, final art or native interaction.'};(OUT/'fitted_surfaces.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps({'passed':r['passed'],'preservation':[(x['mesh'],x['maximum_source_distance'],x['changed_samples']) for x in preserved],'fits':[(x['support'],x['fit'],x['bad_count'],x['maximum_gap']) for x in fits]}),flush=True)
