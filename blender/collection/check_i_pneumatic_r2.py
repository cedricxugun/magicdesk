"""Evaluate pneumatic connections and moving parts on the real recorded source."""
import bpy,json,hashlib,math
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
ROOT=Path(__file__).resolve().parents[2];OUT=ROOT/'review/I_refinement/r2'
report_in=json.loads((OUT/'build.json').read_text());source=ROOT/report_in['source'];bpy.ops.wm.open_mainfile(filepath=str(source));scene=bpy.context.scene
take=json.loads((OUT/'pneumatic_take.json').read_text());mouth=bpy.data.objects['IH1_Mouth'];bell=bpy.data.objects['IH1_Bellows'];dia=bpy.data.objects['IH1_Diaphragm'];front=bpy.data.objects[report_in['front_group']]
tube=bpy.data.objects[report_in['feed_tube']];connector=bpy.data.objects[report_in['connector']];cup=bpy.data.objects[report_in['cup']]
membrane=next(o for o in dia.children if 'DomedDiaphragm' in o.name)
front_plate=next(o for o in front.children if 'FrontBellowsPlate' in o.name)
apex=bpy.data.objects['IH1_Apex'];tail=next(o for o in bpy.data.objects['IH1_FrontPanel5'].children if 'FrontPorcelain' in o.name)
springs=[bpy.data.objects[n] for n in report_in['springs']];wall=bpy.data.objects[report_in['bellows_wall']]
def geometry(o):
    ev=o.evaluated_get(bpy.context.evaluated_depsgraph_get());m=ev.to_mesh();m.calc_loop_triangles();v=[o.matrix_world@p.co for p in m.vertices];f=[tuple(t.vertices) for t in m.loop_triangles];ev.to_mesh_clear();return v,f
def tree(o):
    v,f=geometry(o);return BVHTree.FromPolygons(v,f,all_triangles=True)
collisions=[];seating=[];spring_errors=[];spring_rows=[];motion_error=0.;frames=list(range(1,362,6))
for frame in frames:
    scene.frame_set(frame);bpy.context.view_layer.update();sample=take['samples'][frame-1];state=sample['state']
    wanted=max(-.014,min(.014,state['diaphragm']*40.))
    motion_error=max(motion_error,abs(front.location.z-(-.23+.132*state['compression'])),abs(dia.location.z-(.235-wanted)))
    pairs=[(tube,front_plate),(connector,membrane),(cup,membrane)]
    for item in apex.children:
        if item.type=='MESH':pairs.append((tail,item))
    for a,b in pairs:
        count=len(tree(a).overlap(tree(b)))
        if count:collisions.append({'frame':frame,'a':a.name,'b':b.name,'triangles':count})
    v,_=geometry(wall);v=[bell.matrix_world.inverted()@p for p in v];relative=min(p.z for p in v)-front.location.z
    seating.append(relative)
    for spring in springs:
        v,_=geometry(spring);v=[mouth.matrix_world.inverted()@p for p in v]
        error=max(abs(max(p.z for p in v)-.330),abs(min(p.z for p in v)-(dia.location.z+.013)));spring_errors.append(error)
        spring_rows.append({'frame':frame,'spring':spring.name,'value':spring.data.shape_keys.key_blocks['Travel'].value,'min':min(p.z for p in v),'max':max(p.z for p in v),'front_seat':dia.location.z+.013,'error':error})
result={'source_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'frames':frames,'surface_intersections':collisions,'maximum_recorded_motion_error':motion_error,'wall_front_inside_seat_range':[min(seating),max(seating)],'spring_end_seating_error':max(spring_errors),'worst_spring':max(spring_rows,key=lambda row:row['error']),'passed':not collisions and motion_error<.000003 and min(seating)>-.02 and max(seating)<.018 and max(spring_errors)<.0002,'scope':'Recorded pneumatic motion; unexpected tube/cup/membrane and tail/apex intersections, front wall seating and spring end planes. Bonded rubber surround, unions, other shell/metal interfaces and unsampled continuous volumes excluded.'}
(OUT/'pneumatic_check.json').write_text(json.dumps(result,indent=2)+'\n');print('I_PNEUMATIC_CHECK',result['passed'],'intersections',len(collisions),'spring_error',max(spring_errors),'seat',[min(seating),max(seating)],flush=True)
if not result['passed']:raise SystemExit(1)
