"""Bounded authored membrane morphs with pinned seams and actual fixture clearance."""
import bpy,bmesh,json,hashlib,struct,math,heapq,shutil
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
ROOT=Path(__file__).resolve().parents[2];OUT=ROOT/'review/I_refinement/nautilus_r1/chamber_motion_r36';OUT.mkdir(parents=True,exist_ok=True);ART=ROOT/'app/assets/collection/art/I/chamber_motion_r36';ART.mkdir(parents=True,exist_ok=True);parent=ROOT/'review/I_refinement/nautilus_r1/chamber_response_r35';s=json.loads((parent/'build.json').read_text());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();assert sha(ROOT/s['source'])==s['source_sha256'];bpy.ops.wm.open_mainfile(filepath=str(ROOT/s['source']));scene=bpy.context.scene;scene.frame_set(1);bpy.context.view_layer.update();root=bpy.data.objects['IN1_BodyRoot'];C=Vector((.12,.16,1.96));R=Vector((1.01,.67,1.10));films=[bpy.data.objects[r['diaphragm']]for r in s['acoustic_cells']]
def fingerprint(o):
    h=hashlib.sha256();m=o.data;m.calc_loop_triangles()
    for v in m.vertices:h.update(struct.pack('<3f',*v.co))
    for t in m.loop_triangles:h.update(struct.pack('<3I',*t.vertices))
    for n in m.corner_normals:h.update(struct.pack('<3f',*n.vector))
    return [h.hexdigest(),[list(r)for r in o.matrix_world]]
original={o.name:fingerprint(o)for o in bpy.data.objects if o.type=='MESH'};vertices=[];triangles=[];fixture_bounds=[]
for o in bpy.data.objects:
    if o.type!='MESH'or o in films:continue
    o.data.calc_loop_triangles();offset=len(vertices);vertices.extend(o.matrix_world@v.co for v in o.data.vertices);triangles.extend(tuple(offset+i for i in t.vertices)for t in o.data.loop_triangles)
    if any(token in o.name for token in ['UpperClamp','LowerStand','Backing','InnerWasher']):
        points=[o.matrix_world@Vector(v)for v in o.bound_box];fixture_bounds.append(([min(p[k]for p in points)-.008 for k in range(3)],[max(p[k]for p in points)+.008 for k in range(3)]))
obstacles=BVHTree.FromPolygons(vertices,triangles,all_triangles=True);print('MEMBRANE_OBSTACLES',len(triangles),flush=True);del vertices,triangles
rows=[]
def smooth(value):
    t=max(0.,min(1.,value));return t*t*(3-2*t)
for index,(o,cell)in enumerate(zip(films,s['acoustic_cells'])):
    assert o.data.shape_keys is None;world=o.matrix_world;inverse=world.to_3x3().inverted();bm=bmesh.new();bm.from_mesh(o.data);bm.normal_update();bm.verts.ensure_lookup_table();bm.verts.index_update();pinned=set()
    # Caps, cut ends and bore walls keep both their vertices and neighbors fixed.
    normal_matrix=world.to_3x3().inverted().transposed()
    for face in bm.faces:
        p=world@face.calc_center_median()-C;radial=Vector((p[k]/((R[k]-.102)**2)for k in range(3))).normalized()
        if abs((normal_matrix@face.normal).normalized().dot(radial))<.65:pinned.update(v.index for v in face.verts)
    points=[world@v.co for v in bm.verts]
    cut_ends=[r for r in s.get('core_termination',[])if r['part']==o.name and 'depth'in r]
    mouth_matrix=bpy.data.objects['IAM_MODULE'].matrix_world;mouth_origin=mouth_matrix.translation;mouth_axis=mouth_matrix.to_3x3().col[2].normalized();cut_pins=set()
    for cut in cut_ends:
        # These faces cap the throat-side cut and are fixed terminations, not
        # elastic diaphragm surface. Their normal need not be radial.
        for i,p in enumerate(points):
            if abs((p-mouth_origin).dot(mouth_axis)-float(cut['depth']))<.006:cut_pins.add(i)
    pinned|=cut_pins
    for face in bm.faces:
        low=[min(points[v.index][k]for v in face.verts)for k in range(3)];high=[max(points[v.index][k]for v in face.verts)for k in range(3)]
        if any(all(high[k]>=a[k]and low[k]<=b[k]for k in range(3))for a,b in fixture_bounds):pinned.update(v.index for v in face.verts)
    for edge in bm.edges:
        if edge.calc_length()<.0001:pinned.update(v.index for v in edge.verts)
    pinned|={e.other_vert(bm.verts[i]).index for i in list(pinned)for e in bm.verts[i].link_edges}
    distance_to_pin=[float('inf')]*len(points);pending=[];neighbors=[[]for p in points]
    for e in bm.edges:
        a,b=[v.index for v in e.verts];length=(points[a]-points[b]).length;neighbors[a].append((b,length));neighbors[b].append((a,length))
    for i in pinned:distance_to_pin[i]=0.;heapq.heappush(pending,(0.,i))
    while pending:
        distance,index_vertex=heapq.heappop(pending)
        if distance>distance_to_pin[index_vertex]:continue
        for j,length in neighbors[index_vertex]:
            candidate=distance+length
            if candidate<distance_to_pin[j]:distance_to_pin[j]=candidate;heapq.heappush(pending,(candidate,j))
    bm.free()
    basis=o.shape_key_add(name='Basis',from_mix=False);positive=o.shape_key_add(name='MusicPressure',from_mix=False);negative=o.shape_key_add(name='MusicRebound',from_mix=False);a,b=cell['theta'];mid=(a+b)/2;changes=[];clearances=[]
    for i,v in enumerate(o.data.vertices):
        world_point=world@v.co;p=world_point-C;phi=math.acos(max(-1.,min(1.,-p.y/(R.y-.109))));angle=math.atan2(p.z/(R.z-.109),p.x/(R.x-.109));theta=angle-1.12*math.cos(phi)
        for _ in range(8):theta=angle-1.12*math.cos(phi)-.10*math.sin(phi)**2*math.sin(theta+1.)
        theta=mid+(theta-mid+math.pi)%math.tau-math.pi;q=(theta-a)/(b-a)
        distance=obstacles.find_nearest(world_point,.08)[3];distance=.08 if distance is None else distance
        weight=smooth((q-.12)/.18)*smooth((.88-q)/.18)*smooth((phi-.35)/.22)*smooth((math.pi-.35-phi)/.22)*smooth((distance-.012)/.025)
        if i in pinned:weight=0.
        amplitude=min(.003,.15*distance)*weight*smooth(distance_to_pin[i]/.045)
        direction=Vector((p[k]/((R[k]-.109)**2)for k in range(3))).normalized();delta=inverse@(direction*amplitude)
        positive.data[i].co=v.co+delta;negative.data[i].co=v.co-delta
        if amplitude>1e-7:changes.append({'vertex':i,'delta_local':list(delta),'world_amplitude':amplitude,'fixture_clearance':distance});clearances.append(distance)
    positive.value=0.;negative.value=0.;assert changes
    row={'mesh':o.name,'pressure_key':'MusicPressure','rebound_key':'MusicRebound','max_world_stroke':max(r['world_amplitude']for r in changes),'pinned_vertices':len(pinned),'throat_cut_pinned_vertices':len(cut_pins),'unchanged_vertices':len(o.data.vertices)-len(changes),'vertex_count':len(o.data.vertices),'minimum_fixture_clearance_of_moving_vertices':min(clearances),'moving':changes,'band':index%3,'natural_frequency_hz':2.2+(index%3)*.8,'damping_ratio':.45};rows.append(row);print('MEMBRANE_MORPHS',o.name,len(changes),row['max_world_stroke'],flush=True)
assert all(fingerprint(bpy.data.objects[n])==v for n,v in original.items())
source=ROOT/'blender/collection/I_nautilus_chamber_motion_r36.blend';component=ROOT/'app/assets/collection/components/I_nautilus_chamber_motion_r36.glb'
if source.exists():
    old=json.loads((OUT/'build.json').read_text());assert sha(source)==old['source_sha256'];archive=OUT/'iterations'/old['source_sha256'][:12];archive.mkdir(parents=True,exist_ok=True)
    for p in OUT.glob('*.json'):shutil.copy2(p,archive/p.name)
    if (OUT/'views').exists():shutil.copytree(OUT/'views',archive/'views',dirs_exist_ok=True)
    shutil.copy2(source,source.parent/'checkpoints'/('I-chamber-motion-'+old['source_sha256'][:12]+'.blend'))
bpy.ops.wm.save_as_mainfile(filepath=str(source),compress=True);bpy.ops.object.select_all(action='DESELECT')
for o in [root,*root.children_recursive]:o.select_set(True)
bpy.context.view_layer.objects.active=root;bpy.ops.export_scene.gltf(filepath=str(component),export_format='GLB',use_selection=True,export_animations=False,export_morph=True,export_morph_normal=True,export_extras=True)
layout=json.loads((ROOT/'app/assets/collection/art/I/chamber_response_r35/layout.json').read_text());layout['source_sha256']=sha(source);layout['component_sha256']=sha(component)
for cell,motion in zip(layout['cells'],rows):cell['membrane_motion']={k:v for k,v in motion.items()if k!='moving'}
layout['scope']='Existing chamber emission plus authored signed membrane shapes. Frame/clamp regions pinned and rest geometry retained; dynamic clearance and runtime pose still require validation.';(ART/'layout.json').write_text(json.dumps(layout,indent=2)+'\n')
d={**s,'source':str(source.relative_to(ROOT)),'source_sha256':sha(source),'component':str(component.relative_to(ROOT)),'component_sha256':sha(component),'parent_source_sha256':s['source_sha256'],'chamber_response_layout':'res://assets/collection/art/I/chamber_motion_r36/layout.json','membrane_motion':rows,'status':'authored_membrane_morph_candidate_checks_pending'};(OUT/'build.json').write_text(json.dumps(d,indent=2)+'\n');(OUT/'rest_preservation.json').write_text(json.dumps({'source_sha256':d['source_sha256'],'passed':True,'protected_mesh_count':len(original),'scope':'Rest vertices, actual triangles, corner normals and transforms unchanged; pressure/rebound shape keys added only to twelve membranes.'},indent=2)+'\n');print('CHAMBER_MOTION_SOURCE',d['source_sha256'],flush=True)
