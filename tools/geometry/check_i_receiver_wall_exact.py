"""Triangle-to-triangle receiver wall distance on the saved Blender mesh.

BVHTree overlap uses Blender's triangle intersection callback:
https://raw.githubusercontent.com/blender/blender/main/source/blender/python/mathutils/mathutils_bvhtree.cc
"""
import bpy,json,hashlib,sys,math
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
from mathutils.geometry import closest_point_on_tri
ROOT=Path(__file__).resolve().parents[2];args=sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else []
path=ROOT/next((a.split('=',1)[1] for a in args if a.startswith('--report=')),'review/I_refinement/nautilus_r1/core_bridge_r4/build.json');spec=json.loads(path.read_text());assert hashlib.sha256((ROOT/spec['source']).read_bytes()).hexdigest()==spec['source_sha256']
bpy.ops.wm.open_mainfile(filepath=str(ROOT/spec['source']));bpy.context.scene.frame_set(1);bpy.context.view_layer.update();obj=bpy.data.objects['IN1_PorcelainPanel_02'];m=obj.data;m.calc_loop_triangles()
wall=[a.value for a in m.attributes['formed_wall_fraction'].data];v=[obj.matrix_world@p.co for p in m.vertices];triangles=[tuple(t.vertices) for t in m.loop_triangles]
if 'IN3_receiver_region' in m.attributes:region=[a.value for a in m.attributes['IN3_receiver_region'].data]
else:
    inv=bpy.data.objects['IAM_MODULE'].matrix_world.inverted();region=[float(.53<(inv@p).z<.72) for p in v]
if 'IR6_wall_side' in m.attributes:
    sides=[a.value for a in m.attributes['IR6_wall_side'].data]
    outer_ids=[i for i,t in enumerate(m.loop_triangles) if sides[t.polygon_index]==0];inner_ids=[i for i,t in enumerate(m.loop_triangles) if sides[t.polygon_index]==1]
else:
    outer_ids=[i for i,f in enumerate(triangles) if max(wall[k] for k in f)<.001];inner_ids=[i for i,f in enumerate(triangles) if min(wall[k] for k in f)>.999 and max(region[k] for k in f)>.5]
assert len(inner_ids)>100
outer_faces=[triangles[i] for i in outer_ids];inner_faces=[triangles[i] for i in inner_ids];outer=BVHTree.FromPolygons(v,outer_faces,all_triangles=True);inner=BVHTree.FromPolygons(v,inner_faces,all_triangles=True)
intersections=inner.overlap(outer)
def segments(a,b,c,d):
    u=b-a;w=a-c;vv=d-c;aa=u.dot(u);bb=u.dot(vv);cc=vv.dot(vv);dd=u.dot(w);ee=vv.dot(w);den=aa*cc-bb*bb
    if aa<1e-20:s=0.;t=max(0.,min(1.,ee/max(cc,1e-20)))
    elif cc<1e-20:t=0.;s=max(0.,min(1.,-dd/aa))
    else:
        s=max(0.,min(1.,(bb*ee-cc*dd)/den)) if den>1e-20 else 0.;t=(bb*s+ee)/cc
        if t<0.:t=0.;s=max(0.,min(1.,-dd/aa))
        elif t>1.:t=1.;s=max(0.,min(1.,(bb-dd)/aa))
    p=a+u*s;q=c+vv*t;return (p-q).length_squared,p,q
def triangle_distance(a,b):
    result=(float('inf'),None,None)
    for p in a:
        q=closest_point_on_tri(p,*b);candidate=((p-q).length_squared,p,q)
        if candidate[0]<result[0]:result=candidate
    for q in b:
        p=closest_point_on_tri(q,*a);candidate=((p-q).length_squared,p,q)
        if candidate[0]<result[0]:result=candidate
    for i in range(3):
        for j in range(3):
            candidate=segments(a[i],a[(i+1)%3],b[j],b[(j+1)%3])
            if candidate[0]<result[0]:result=candidate
    return result
minimum=None;below=[];pairs=0;threshold=.006
if intersections:
    i,j=intersections[0];minimum={'distance':0.,'inner_triangle':inner_ids[i],'outer_triangle':outer_ids[j]}
else:
    cache={i:[v[k] for k in face] for i,face in enumerate(outer_faces)}
    for index,source_id in enumerate(inner_ids):
        a=[v[k] for k in triangles[source_id]];center=sum(a,Vector())/3.;radius=max((p-center).length for p in a);nearest=outer.find_nearest(center);bound=nearest[3]
        best=(float('inf'),None,None);best_id=None
        # A triangle lies inside this centroid ball. Any closer outer point
        # must be within radius + the known point-to-surface upper bound.
        for _,_,i,_ in outer.find_nearest_range(center,radius+bound+1e-6):
            candidate=triangle_distance(a,cache[i]);pairs+=1
            if candidate[0]<best[0]:best=candidate;best_id=i
        assert best_id is not None
        distance=math.sqrt(max(0.,best[0]));row={'distance':distance,'inner_triangle':source_id,'outer_triangle':outer_ids[best_id],'inner_point':list(best[1]),'outer_point':list(best[2])}
        if minimum is None or distance<minimum['distance']:minimum=row
        if distance<threshold:below.append(row)
        if index%2000==0:print('RECEIVER_EXACT_DISTANCE',index,len(inner_ids),minimum['distance'],flush=True)
result={'source_sha256':spec['source_sha256'],'minimum_requested_scene_units':threshold,'passed':not intersections and minimum is not None and minimum['distance']>=threshold,'inner_triangles':len(inner_ids),'outer_triangles':len(outer_ids),'tested_triangle_pairs':pairs,'intersection_pairs':len(intersections),'intersection_examples':[[inner_ids[i],outer_ids[j]] for i,j in intersections[:20]],'minimum':minimum,'below_minimum_count':len(below),'below_minimum':below,'worst':sorted(below,key=lambda r:r['distance'])[:20],'scope':'Triangle intersections and minimum vertex-face/edge-edge distances over all saved mesh triangles in the permanently tagged receiver region. BVH ball bound retains every potentially closer outer triangle. Floating-point geometry; no analytic smooth-surface, other shell regions, strength, imported LOD or continuous-motion claim.'}
(path.parent/'receiver_wall_exact.json').write_text(json.dumps(result,indent=2)+'\n');print('RECEIVER_EXACT_RESULT',json.dumps({k:result[k] for k in ['passed','intersection_pairs','minimum','below_minimum_count']}),flush=True)
