"""Scoped solids, assembled contacts, cam release and existing foil sweep audit."""
import bpy,bmesh,math,json,hashlib,itertools
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
ROOT=Path(__file__).resolve().parents[2];OUT=ROOT/'review/I_refinement/part_a_mouth/shutter_r2/collar_clamps'
spec=json.loads((OUT/'build.json').read_text());source=ROOT/spec['source'];assert hashlib.sha256(source.read_bytes()).hexdigest()==spec['source_sha256']
bpy.ops.wm.open_mainfile(filepath=str(source));scene=bpy.context.scene;scene.frame_set(1);bpy.context.view_layer.update()
new=[o for o in bpy.data.objects if o.type=='MESH' and o.name.startswith('IAM_Collar')]
changed=new+[bpy.data.objects[n] for n in spec['modified_fixed_meshes']]
solids=[]
for o in changed:
    bm=bmesh.new();bm.from_mesh(o.data);bm.verts.ensure_lookup_table()
    remaining=set(bm.verts);components=0
    while remaining:
        stack=[remaining.pop()];components+=1
        while stack:
            v=stack.pop()
            for edge in v.link_edges:
                other=edge.other_vert(v)
                if other in remaining:remaining.remove(other);stack.append(other)
    solids.append({'name':o.name,'nonmanifold':sum(not e.is_manifold for e in bm.edges),'volume':bm.calc_volume(signed=True),'connected_components':components})
    bm.free()
def surface(o):
    e=o.evaluated_get(bpy.context.evaluated_depsgraph_get());m=e.to_mesh();m.calc_loop_triangles()
    verts=[e.matrix_world@v.co for v in m.vertices];faces=[tuple(t.vertices) for t in m.loop_triangles]
    bounds=([min(v[k] for v in verts) for k in range(3)],[max(v[k] for v in verts) for k in range(3)])
    tree=BVHTree.FromPolygons(verts,faces,all_triangles=True);e.to_mesh_clear();return tree,bounds
def overlaps(a,b):
    if any(a[1][1][k]<b[1][0][k] or b[1][1][k]<a[1][0][k] for k in range(3)):return False
    return bool(a[0].overlap(b[0]))
def intended(a,b):
    # These interfaces are deliberately seated; retain them explicitly.
    pairs=[('FittedPressureShoe','SeatedGasket'),('FittedPressureShoe','ShoeLocator'),('CamAndSpine','RedEnamelGrip'),('RearLoadWasher','RearHexNut'),('HingeThrust','HingeCap')]
    return any((x in a and y in b) or (x in b and y in a) for x,y in pairs)
foil_names=[name for group in spec['tongues'] for name in group['mesh_names']]
all_meshes=[o for o in bpy.data.objects if o.type=='MESH']
cache={o.name:surface(o) for o in all_meshes}
contacts=[];seated=[]
for a in new:
    for b in all_meshes:
        if a==b or (b in new and b.name<a.name):continue
        if overlaps(cache[a.name],cache[b.name]):
            row=[a.name,b.name]
            (seated if intended(*row) else contacts).append(row)
print('COLLAR_REST_CONTACTS',len(contacts),'seated',len(seated),flush=True)
release_contacts=[];release_samples=[]
for step in range(17):
    amount=step/16
    for row in spec['collar_clamps']:
        pivot=bpy.data.objects[row['pivot']];pivot['service_release']=amount;pivot.update_tag()
    bpy.context.view_layer.update()
    for row in spec['collar_clamps']:
        pivot=bpy.data.objects[row['pivot']];actual=pivot.evaluated_get(bpy.context.evaluated_depsgraph_get()).rotation_euler.y
        assert abs(actual-math.radians(row['service_release_degrees'])*amount)<1e-6
        for name in [row['cam'],row['grip']]:
            current=surface(bpy.data.objects[name])
            for other in all_meshes:
                if other.name in [row['cam'],row['grip']]:continue
                if other.name.startswith('IAM_Collar') and not other.name.startswith('IAM_Collar%d_'%row['index']):continue
                if overlaps(current,cache[other.name]) and not intended(name,other.name):release_contacts.append({'release':amount,'pair':[name,other.name]})
        release_samples.append({'index':row['index'],'release':amount,'evaluated_angle':actual})
for row in spec['collar_clamps']:
    o=bpy.data.objects[row['pivot']];o['service_release']=0.;o.update_tag()
bpy.context.view_layer.update()
foil_contacts=[]
for frame in [1,25,55,85,115,145,175,205,235,265,295,325,355,385,415,433]:
    scene.frame_set(frame);bpy.context.view_layer.update()
    for name in foil_names:
        current=surface(bpy.data.objects[name])
        for hardware in new:
            if overlaps(current,cache[hardware.name]):foil_contacts.append({'frame':frame,'pair':[name,hardware.name]})
    print('COLLAR_FOIL_FRAME',frame,flush=True)
passed=not contacts and not release_contacts and not foil_contacts and all(s['nonmanifold']==0 and s['volume']>0 and s['connected_components']==1 for s in solids)
result={'source_sha256':spec['source_sha256'],'component_sha256':spec['component_sha256'],'passed':passed,'solids':solids,'unexpected_rest_surface_contacts':contacts,'intended_seated_contacts':seated,'release_contacts':release_contacts,'release_samples':release_samples,'foil_contacts':foil_contacts,'scope':'Changed solid topology, new hardware against existing REST surfaces, 17 refreshed cam-release poses and 16 existing foil source-animation samples. Seated interfaces listed separately; no continuous collision, containment, load-bearing certification or whole A/native acceptance.'}
(OUT/'collar_hardware_check.json').write_text(json.dumps(result,indent=2)+'\n');print('I_COLLAR_GEOMETRY_CHECK',passed,flush=True)
