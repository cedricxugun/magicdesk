"""Read actual saved screw seats, bead contact, and telescopic overlap through operation."""
import bpy,bmesh,json,hashlib
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
ROOT=Path(__file__).resolve().parents[2];OUT=ROOT/'review/I_refinement/assembly_r5'
info=json.loads((OUT/'build.json').read_text());source=ROOT/info['source'];bpy.ops.wm.open_mainfile(filepath=str(source));scene=bpy.context.scene;scene.frame_set(1)
def geometry(obj):
    ev=obj.evaluated_get(bpy.context.evaluated_depsgraph_get());m=ev.to_mesh();m.calc_loop_triangles();v=[p.co.copy() for p in m.vertices];f=[tuple(t.vertices) for t in m.loop_triangles];ev.to_mesh_clear();return v,f
shells={};topology=[]
for row in info['fastener_seats']:
    if row['shell'] in shells:continue
    shell=bpy.data.objects[row['shell']];v,f=geometry(shell);shells[shell.name]=BVHTree.FromPolygons([shell.matrix_world@p for p in v],f,all_triangles=True)
    bm=bmesh.new();bm.from_mesh(shell.data);topology.append({'name':shell.name,'nonmanifold_edges':sum(not e.is_manifold for e in bm.edges),'volume':bm.calc_volume(signed=True)});bm.free()
seat_errors=[]
for row in info['fastener_seats']:
    head=bpy.data.objects[row['head']];axis=(head.parent.matrix_world.to_3x3()@Vector(row['axis'])).normalized()
    expected=head.matrix_world.translation-axis*.0065*row['scale']
    point,normal,index,d=shells[row['shell']].ray_cast(head.matrix_world.translation,-axis)
    seat_errors.append({'head':head.name,'error':(point-expected).length if point is not None else None})
beads=[]
for i in range(6):
    panel=bpy.data.objects['IH1_FrontPanel'+str(i)];shell=next(o for o in panel.children if 'FrontPorcelain'+str(i)+'_' in o.name)
    for obj in panel.children:
        if obj.type!='CURVE' or not any(s in obj.name for s in ['RolledPanelLip','SidePanelLip']):continue
        ratios=[]
        for p in obj.data.splines[0].points:
            location=obj.matrix_world@Vector(p.co[:3]);nearest,normal,index,d=shells[shell.name].find_nearest(location)
            ratios.append(d/(obj.data.bevel_depth*p.radius))
        beads.append({'name':obj.name,'maximum_distance_in_bead_radii':max(ratios)})
guides=json.loads((ROOT/'review/I_refinement/r1/guide_manifest.json').read_text());cache={}
for row in guides:
    for name in [row['rod'],row['barrel']]:cache[name]=geometry(bpy.data.objects[name])[0]
panels=[bpy.data.objects['IH1_FrontPanel'+str(i)] for i in range(6)]
for panel in panels:panel.animation_data_clear()
mount_checks=[]
for mount in info.get('guide_mounts',[]):
    trees={}
    for key in (['barrel','rail','fused'] if 'fused' in mount else ['barrel','rail','clamp','saddle','web']):
        obj=bpy.data.objects[mount[key]];v,f=geometry(obj);trees[key]=BVHTree.FromPolygons([obj.matrix_world@p for p in v],f,all_triangles=True)
    if 'fused' in mount:
        bm=bmesh.new();bm.from_mesh(bpy.data.objects[mount['fused']].data);pending=set(bm.verts);components=0
        while pending:
            components+=1;stack=[pending.pop()]
            while stack:
                for edge in stack.pop().link_edges:
                    for vertex in edge.verts:
                        if vertex in pending:pending.remove(vertex);stack.append(vertex)
        row={'barrel':mount['barrel'],'fused_barrel':len(trees['fused'].overlap(trees['barrel'])),'fused_rail':len(trees['fused'].overlap(trees['rail'])),'components':components,'nonmanifold_edges':sum(not e.is_manifold for e in bm.edges)};bm.free()
        row['passed']=row['fused_barrel']==0 and row['fused_rail']==0 and row['components']==1 and row['nonmanifold_edges']==0;mount_checks.append(row);continue
    mount_checks.append({'barrel':mount['barrel'],'web_barrel':len(trees['web'].overlap(trees['barrel'])),'web_rail':len(trees['web'].overlap(trees['rail'])),'web_clamp':len(trees['web'].overlap(trees['clamp'])),'web_saddle':len(trees['web'].overlap(trees['saddle']))})
    r=mount_checks[-1];r['passed']=r['web_barrel']==0 and r['web_rail']==0 and r['web_clamp']>0 and r['web_saddle']>0
guide_rows=[]
for step in range(21):
    opening=step/20
    for panel in panels:panel.location=Vector(panel['open_direction'])*panel['stroke']*opening
    bpy.context.view_layer.update()
    for row in guides:
        rod=bpy.data.objects[row['rod']];barrel=bpy.data.objects[row['barrel']]
        axis=barrel.matrix_world.to_3x3().col[2].normalized()
        rv=[(rod.matrix_world@v).dot(axis) for v in cache[rod.name]];bv=[(barrel.matrix_world@v).dot(axis) for v in cache[barrel.name]]
        overlap=min(max(rv),max(bv))-max(min(rv),min(bv))
        radial_error=(rod.matrix_world.translation-barrel.matrix_world.translation).cross(axis).length
        guide_rows.append({'opening':opening,'rod':rod.name,'overlap':overlap,'minimum':.054*row['scale'],'radial_error':radial_error})
passed=all(r['error'] is not None and r['error']<.00002 for r in seat_errors) and all(r['nonmanifold_edges']==0 and r['volume']>0 for r in topology) and all(r['maximum_distance_in_bead_radii']<1. for r in beads) and all(r['overlap']>=r['minimum'] and r['radial_error']<.00002 for r in guide_rows)
result={'passed':passed,'source_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'screw_seats':seat_errors,'shell_topology':topology,'bead_contact':beads,'guide_samples':guide_rows,'scope':'Actual saved screw rear seats, closed bored ceramic, bead contact and guide coaxial overlap at21 operating openings. Not full scene collision, service detachment path, or native visual acceptance.'}
result['guide_mount_checks']=mount_checks;result['passed']=passed and all(r['passed'] for r in mount_checks)
passed=result['passed']
(OUT/'manufacturing_check.json').write_text(json.dumps(result,indent=2)+'\n');print('I_MANUFACTURING',passed,'seat_max',max((r['error'] or 0) for r in seat_errors),'bead_max',max(r['maximum_distance_in_bead_radii'] for r in beads),'guide_min',min(r['overlap']-r['minimum'] for r in guide_rows),flush=True)
if not passed:raise SystemExit(1)
