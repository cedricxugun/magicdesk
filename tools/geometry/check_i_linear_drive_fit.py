"""Measure pressure strokes and chamber walls from current rendered meshes."""
import bpy,bmesh,json,hashlib,math
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'review/I_refinement/nautilus_r1/linear_drives_r20'
s=json.loads((OUT/'build.json').read_text())
assert hashlib.sha256((ROOT/s['source']).read_bytes()).hexdigest()==s['source_sha256']
bpy.ops.wm.open_mainfile(filepath=str(ROOT/s['source']))
bpy.context.scene.frame_set(1);bpy.context.view_layer.update()
def geometry(name,inverse):
    o=bpy.data.objects[name];o.data.calc_loop_triangles()
    vertices=[inverse@o.matrix_world@v.co for v in o.data.vertices]
    return vertices,BVHTree.FromPolygons(vertices,[tuple(t.vertices) for t in o.data.loop_triangles],all_triangles=True)
def continuity(name):
    bm=bmesh.new();bm.from_mesh(bpy.data.objects[name].data)
    unseen=set(bm.verts);counts=[]
    while unseen:
        pending=[unseen.pop()];count=0
        while pending:
            v=pending.pop();count+=1
            for e in v.link_edges:
                w=e.other_vert(v)
                if w in unseen:unseen.remove(w);pending.append(w)
        counts.append(count)
    bad=sum(not e.is_manifold for e in bm.edges);bm.free()
    return {'mesh':name,'components':counts,'nonmanifold_edges':bad,'passed':len(counts)==1 and bad==0}
rows=[]
for d in s['linear_drives']['drives']:
    inv=bpy.data.objects[d['frame']].matrix_world.inverted();y=d['center_y']
    hv,tree=geometry(d['housing'],inv);pv,piston_tree=geometry(d['piston'],inv)
    sv,_=geometry(d['piston_seal'],inv);gv,_=geometry(d['gland_seal'],inv)
    piston=[v for v in pv if math.hypot(v.x,v.y-y)>.010]
    rest_lo=min(v.z for v in piston);rest_hi=max(v.z for v in piston)
    floor=[];ceiling=[];wall=[]
    probe_z=sum(d['inner_axial_bounds'])/2
    for i in range(64):
        angle=math.tau*(i+.5)/64;radial=Vector((math.cos(angle),math.sin(angle),0))
        origin=Vector((0,y,probe_z))+radial*.010
        low=tree.ray_cast(origin,Vector((0,0,-1)),.3)[0]
        high=tree.ray_cast(origin,Vector((0,0,1)),.3)[0]
        assert low is not None and high is not None
        floor.append(low.z);ceiling.append(high.z)
        for z in [rest_lo+.003,rest_hi+d['stroke']-.003]:
            point=tree.ray_cast(Vector((0,y,z)),radial,.05)[0];assert point is not None
            wall.append(math.hypot(point.x,point.y-y))
    seal_radius=max(math.hypot(v.x,v.y-y) for v in sv)
    gland_inner=min(math.hypot(v.x,v.y-y) for v in gv)*math.cos(math.pi/64)
    rod_radii=[]
    for i in range(64):
        radial=Vector((math.cos(math.tau*i/64),math.sin(math.tau*i/64),0))
        point=piston_tree.ray_cast(Vector((0,y,-.04)),radial,.03)[0];assert point is not None
        rod_radii.append(math.hypot(point.x,point.y-y))
    rod_radius=max(rod_radii)
    samples=[{'opening':f,'rear_margin':rest_lo+d['stroke']*f-max(floor),'front_margin':min(ceiling)-rest_hi-d['stroke']*f} for f in [0,.5,1,.35,0]]
    topology=[continuity(n) for n in [d['housing'],d['piston'],'IN2_Cassette%02dBackBlock'%d['panel_number'],'IN2_Cassette%02dCrosshead'%d['panel_number']]]
    passed=all(r['rear_margin']>.002 and r['front_margin']>.002 for r in samples) and min(wall)-seal_radius>.0001 and gland_inner-rod_radius>.0001 and all(r['passed'] for r in topology)
    rows.append({'panel_number':d['panel_number'],'samples':samples,'minimum_seal_wall_clearance':min(wall)-seal_radius,'minimum_rod_gland_clearance':gland_inner-rod_radius,'topology':topology,'passed':passed})
result={'source_sha256':s['source_sha256'],'passed':all(r['passed'] for r in rows),'rows':rows,'scope':'Actual mesh ray-cast chamber floors/walls, piston stroke bounds, gland/rod radial fit and one-piece mounting-spine continuity. Does not verify pressure seals under load, rotary power, cables, materials or final visual quality.'}
(OUT/'pressure_fit.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
