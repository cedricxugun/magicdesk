"""Inspect the real clamp assemblies, their bores and blind core ends."""
import bpy,json,hashlib,sys
from pathlib import Path
from mathutils import Vector,Matrix
from mathutils.bvhtree import BVHTree
ROOT=Path(__file__).resolve().parents[2];args=sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else [];report=ROOT/next((a.split('=',1)[1] for a in args if a.startswith('--report=')),'review/I_refinement/nautilus_r1/chamber_seats_r9/build.json');OUT=report.parent;spec=json.loads(report.read_text());assert hashlib.sha256((ROOT/spec['source']).read_bytes()).hexdigest()==spec['source_sha256']
sys.path.insert(0,str(Path(__file__).parent));from i_triangle_separation import prepare,separated_prepared,self_check
self_check();separation_stats={'candidate_pairs':0,'separated_pairs':0,'native_overlap_pairs_rejected':0}
bpy.ops.wm.open_mainfile(filepath=str(ROOT/spec['source']));scene=bpy.context.scene;scene.frame_set(1);bpy.context.view_layer.update();deps=bpy.context.evaluated_depsgraph_get()
def geometry(objects):
    vertices=[];faces=[]
    for o in objects:
        e=o.evaluated_get(deps);m=e.to_mesh();m.calc_loop_triangles();offset=len(vertices);vertices.extend(e.matrix_world@v.co for v in m.vertices);faces.extend(tuple(offset+i for i in t.vertices) for t in m.loop_triangles);e.to_mesh_clear()
    return {'vertices':vertices,'faces':faces,'prepared':{},'tree':BVHTree.FromPolygons(vertices,faces,all_triangles=True),'min':[min(p[i] for p in vertices) for i in range(3)],'max':[max(p[i] for p in vertices) for i in range(3)]}
def prepared(geometry,index):
    if index not in geometry['prepared']:geometry['prepared'][index]=prepare([geometry['vertices'][i] for i in geometry['faces'][index]])
    return geometry['prepared'][index]
def contact(a,b):
    if any(a['max'][i]<b['min'][i] or b['max'][i]<a['min'][i] for i in range(3)):return None
    if len(a['faces'])>len(b['faces']):a,b=b,a
    native=set(a['tree'].overlap(b['tree']));pairs=[]
    for i,f in enumerate(a['faces']):
        triangle=[a['vertices'][k] for k in f];center=sum(triangle,Vector())/3.;radius=max((p-center).length for p in triangle)
        for _,_,j,_ in b['tree'].find_nearest_range(center,radius+.00005):
            separation_stats['candidate_pairs']+=1;proof=separated_prepared(prepared(a,i),prepared(b,j))
            if proof:
                separation_stats['separated_pairs']+=1
                if (i,j) in native:separation_stats['native_overlap_pairs_rejected']+=1
            else:pairs.append((i,j))
    if not pairs:return None
    points=[]
    for i,j in pairs:
        points.extend(a['vertices'][k] for k in a['faces'][i]);points.extend(b['vertices'][k] for k in b['faces'][j])
    def area(geometry,index):
        x,y,z=[geometry['vertices'][i] for i in geometry['faces'][index]];return (y-x).cross(z-x).length/2
    thin=sum(area(a,i)<1e-10 or area(b,j)<1e-10 for i,j in pairs)
    return {'pairs':len(pairs),'pairs_involving_tiny_triangles':thin,'min':[min(p[i] for p in points) for i in range(3)],'max':[max(p[i] for p in points) for i in range(3)]}
hub_mode='--hub' in args
socket_mode='--sockets' in args
end_mode='--ends' in args
support_mode='--supports' in args
interface_mode='--interfaces' in args
interface_pairs=set()
if interface_mode:
    if (OUT/'core_contacts.json').exists():
        prior=json.loads((OUT/'core_contacts.json').read_text());assert prior['source_sha256']==spec['source_sha256']
        interface_pairs={frozenset([r['fixture'],r['chamber']]) for r in prior['unfinished_attachment_contacts']}
    else:assert spec.get('interface_trim',{}).get('reference_interfaces'),'No current or source interface pair list'
    reference=spec.get('interface_trim',{}).get('reference_interfaces')
    if reference:
        original=json.loads((ROOT/reference).read_text());operation_parent=json.loads((ROOT/spec['interface_trim']['parent_report']).read_text());assert original['source_sha256']==operation_parent['source_sha256']
        interface_pairs.update(frozenset([r['a'],r['b']]) for r in original['contacts'])
selected=set(spec['metal_supports']['new_meshes']) if support_mode else set(spec['end_finishes']['new_meshes']) if end_mode else set().union(*interface_pairs) if interface_mode else set(spec['front_sockets'].get('audit_socket_meshes',spec['front_sockets']['new_meshes'])) if socket_mode else set(spec['hub_backing']['new_meshes']+spec['hub_backing']['modified_meshes'])-{'IN3_ContinuousThroat'} if hub_mode else {o.name for o in bpy.data.objects if o.name.startswith('IS9_')}
parts=[o for o in bpy.data.objects['IN1_BodyRoot'].children_recursive if o.type=='MESH'];new=[o for o in parts if o.name in selected];geo={o.name:geometry([o]) for o in parts};contacts=[]
for i,a in enumerate(parts):
    for b in parts[i+1:]:
        if interface_mode and frozenset([a.name,b.name]) not in interface_pairs:continue
        if not(a.name in selected or b.name in selected):continue
        hit=contact(geo[a.name],geo[b.name])
        if hit:contacts.append({'a':a.name,'b':b.name,**hit})
mouth=[o for o in bpy.data.objects if o.type=='MESH' and o.name.startswith('IAM_')];mouth_contacts=[]
for frame in ([] if interface_mode else [1,181]):
    scene.frame_set(frame);bpy.context.view_layer.update();m=geometry(mouth)
    for part in new:
        hit=contact(geo[part.name],m)
        if hit:mouth_contacts.append({'frame':frame,'part':part.name,**hit})
scene.frame_set(1);bpy.context.view_layer.update();core=geo['IN3_ContinuousThroat'];bores=[]
for seat in ([] if hub_mode or socket_mode or interface_mode or end_mode or support_mode else spec['chamber_seats']):
    matrix=Matrix(seat['matrix_blender']);direction=-(matrix.to_3x3()@Vector((0,0,1))).normalized();inverse=matrix.inverted()
    for bolt in seat['bolts']:
        x,y=bolt['local_xy'];start=matrix@Vector((x,y,bolt['core_outer_z']+.020));hit=core['tree'].ray_cast(start,direction,1.)
        assert hit[0] is not None
        floor=(inverse@hit[0]).z;expected=bolt['core_outer_z']-bolt['blind_depth'];next_hit=core['tree'].ray_cast(hit[0]+direction*.00001,direction,1.);assert next_hit[0] is not None
        inner=(inverse@next_hit[0]).z;bores.append({'bolt':bolt['mesh'],'expected_floor_z':expected,'actual_floor_z':floor,'floor_error':abs(floor-expected),'remaining_actual_wall_on_axis':floor-inner,'passed':abs(floor-expected)<.00001 and floor-inner>.005})
if hub_mode:
    backing=spec['hub_backing'];matrix=Matrix(backing['matrix_blender']);inverse=matrix.inverted();direction=-(matrix.to_3x3()@Vector((0,0,1))).normalized()
    for bolt in backing['core_anchors']+backing['hub_fasteners']:
        x,y=bolt['xy'];target=geo[bolt['target']];start=matrix@Vector((x,y,bolt['outer_z']+.020));hit=target['tree'].ray_cast(start,direction,1.);assert hit[0] is not None
        floor=(inverse@hit[0]).z;following=target['tree'].ray_cast(hit[0]+direction*.00001,direction,1.);assert following[0] is not None
        inner=(inverse@following[0]).z;bores.append({'bolt':bolt['mesh'],'target':bolt['target'],'expected_floor_z':bolt['expected_floor_z'],'actual_floor_z':floor,'remaining_actual_wall_on_axis':floor-inner,'passed':abs(floor-bolt['expected_floor_z'])<.00001 and floor-inner>.004})
if socket_mode:
    for seat in spec['front_sockets']['seats']:
        matrix=Matrix(seat['matrix_blender']);direction=-(matrix.to_3x3()@Vector((0,0,1))).normalized()
        for bolt in seat['bolts']:
            x,y=bolt['xy'];start=matrix@Vector((x,y,bolt['frame_seat_z']+.010));end=matrix@Vector((x,y,bolt['shaft_bottom_z']-.001));checks=[]
            for name in [seat['cap'],seat['source_frame'],seat['upper'],seat['source_film'],seat['outer_stand'],'IN3_ContinuousThroat',seat['inner_backing'],bolt['nut']]:
                hit=geo[name]['tree'].ray_cast(start,direction,(end-start).length);checks.append({'mesh':name,'clear':hit[0] is None,'first_obstruction':list(hit[0]) if hit[0] is not None else None})
            bores.append({'bolt':bolt['mesh'],'axis_clear_checks':checks,'passed':all(r['clear'] for r in checks)})
if support_mode:
    for support in spec['metal_supports']['supports']:
        axis=Vector(support['pin_axis']).normalized()
        for tag,target,point in [('upper_eye',support['body'],support['top']),('lower_eye',support['body'],support['foot']),('foot_fork',support['shoe'],support['foot'])]:
            center=Vector(point);hit=geo[target]['tree'].ray_cast(center-axis*.038,axis,.076);bores.append({'joint':support['anchor']+'_'+tag,'mesh':target,'passed':hit[0] is None,'obstruction':list(hit[0]) if hit[0] else None})
    for bolt in spec['metal_supports']['deck_fasteners']:
        x,y=bolt['xy'];hit=geo[bolt['target']]['tree'].ray_cast(Vector((x,y,bolt['deck_top_z']+.03)),Vector((0,0,-1)),.2);floor=hit[0].z if hit[0] is not None else None
        bores.append({'bolt':bolt['mesh'],'expected_floor':bolt['expected_blind_floor_z'],'actual_floor':floor,'passed':floor is not None and abs(floor-bolt['expected_blind_floor_z'])<1e-5})
result={'source_sha256':spec['source_sha256'],'passed':not contacts and not mouth_contacts and all(r['passed'] for r in bores),'new_meshes':len(new),'contacts':contacts,'mouth_contacts':mouth_contacts,'bore_checks':bores,'separation_stats':separation_stats,'scope':('New through sockets, inside backings, washers, nuts and bolts' if socket_mode else 'New hub backing, bolts and machined nested hub pieces' if hub_mode else 'New clamp/bolt meshes')+' versus body and two A poses. BVH centroid balls gather candidate triangles, including coplanar cases; double-precision separating-axis witnesses reject separated candidates. No name-based contact exclusions. Also checks '+('clear bores through all seven stack parts' if socket_mode else 'actual blind-hole floors')+'. Does not cover all old pairs, containment, continuous motion, full film response, native inputs or art acceptance.'}
if not socket_mode:result['blind_bores']=bores
filename='socket_contacts.json' if socket_mode else 'hub_contacts.json' if hub_mode else 'seat_contacts.json'
if support_mode:
    filename='support_contacts.json';result['scope']='New metal supports, pins, washers, shoes and port parts against current body geometry and two A poses; also actual open bearing axes and deck blind-hole floors. No naming-based contact exclusions. Does not cover every old pair, containment, full continuous movement, final materials/native or art acceptance.'
if end_mode:
    filename='rim_contacts.json';result['scope']='New formed end rims against all body parts and two A poses, with independent triangle separation. No naming-based contact exclusions. Does not cover full continuous motion, containment, materials, native or art acceptance.'
if interface_mode:
    filename='remaining_interfaces.json';result['scope']='Independent triangle separation for the exact existing chamber/core/fixture pairs flagged by core_contacts.json. No pair is ignored by naming. This verifies the listed surface contacts only, not other body pairs, containment, motion, native or art acceptance.';result['listed_pairs']=[sorted(p) for p in interface_pairs]
version=OUT/'checks'/spec['source_sha256'][:12];version.mkdir(parents=True,exist_ok=True);(version/filename).write_text(json.dumps(result,indent=2)+'\n')
if json.loads((OUT/'build.json').read_text())['source_sha256']==spec['source_sha256']:(OUT/filename).write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps({'contacts':[(r['a'],r['b'],r['pairs']) for r in contacts],'mouth_contacts':len(mouth_contacts),'blind_bores':bores,'separation_stats':separation_stats}),flush=True)
