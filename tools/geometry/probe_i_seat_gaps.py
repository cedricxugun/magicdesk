import bpy,json,hashlib
from pathlib import Path
from mathutils import Matrix,Vector
from mathutils.bvhtree import BVHTree
ROOT=Path(__file__).resolve().parents[2];p=ROOT/'review/I_refinement/nautilus_r1/chamber_seats_r9';s=json.loads((p/'build.json').read_text());assert hashlib.sha256((ROOT/s['source']).read_bytes()).hexdigest()==s['source_sha256'];bpy.ops.wm.open_mainfile(filepath=str(ROOT/s['source']));bpy.context.scene.frame_set(1);bpy.context.view_layer.update()
def tree(name,inverse):
    o=bpy.data.objects[name];o.data.calc_loop_triangles();return BVHTree.FromPolygons([inverse@o.matrix_world@v.co for v in o.data.vertices],[tuple(t.vertices) for t in o.data.loop_triangles],all_triangles=True)
def hits(t,x,y):
    origin=Vector((x,y,3.));rows=[]
    for _ in range(12):
        hit=t.ray_cast(origin,Vector((0,0,-1)),6.)
        if hit[0] is None:break
        rows.append((hit[0].z,hit[1].z));origin=hit[0]-Vector((0,0,.000005))
    return rows
records=[]
for seat in s['chamber_seats']:
    inverse=Matrix(seat['matrix_blender']).inverted();names={'frame':'IN1_CellFrame_01','film':'IN1_CellDiaphragm_01','core':'IN3_ContinuousThroat','upper':seat['upper'],'lower':seat['lower']};trees={key:tree(name,inverse) for key,name in names.items()};gaps={key:[] for key in ['frame_upper','upper_film','film_lower','lower_core']}
    for x in [-.0098,-.008,-.004,0.,.004,.008,.0098]:
        for y in [-.020,-.016,-.007,0.,.007,.016,.020]:
            hh={key:hits(value,x,y) for key,value in trees.items()}
            def at(key,positive,near):
                candidates=[z for z,n in hh[key] if (n>.5 if positive else n<-.5)]
                return min(candidates,key=lambda z:abs(z-near)) if candidates else None
            up=at('upper',True,0.);ub=at('upper',False,-.03);lp=at('lower',True,-.045);lb=at('lower',False,-.11)
            if any(v is None for v in [up,ub,lp,lb]):continue
            f=at('frame',False,up);ff=at('film',True,ub);fb=at('film',False,lp);c=at('core',True,lb)
            if any(v is None for v in [f,ff,fb,c]):continue
            for key,gap in [('frame_upper',f-up),('upper_film',ub-ff),('film_lower',fb-lp),('lower_core',lb-c)]:gaps[key].append({'gap':gap,'x':x,'y':y})
    result={'seat':seat['frame'],'gaps':{key:{'min':min(value,key=lambda v:v['gap']),'max':max(value,key=lambda v:v['gap']),'count':len(value)} for key,value in gaps.items() if value}};records.append(result)
(p/'gap_probe.json').write_text(json.dumps({'source_sha256':s['source_sha256'],'rows':records,'scope':'Local ray samples with face orientation, excluding absent surface hits; diagnostic not full clearance.'},indent=2)+'\n');print(json.dumps(records),flush=True)
