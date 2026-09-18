"""Current-source deep cowl candidate. Explicit config; preserves authored morphs and art."""
import bpy,bmesh,json,math,hashlib,sys,struct,shutil
from pathlib import Path
from mathutils import Vector
ROOT=Path(__file__).resolve().parents[2];args=sys.argv[sys.argv.index('--')+1:]if '--'in sys.argv else [];config_path=next((a.split('=',1)[1]for a in args if a.startswith('--config=')),None);config=json.loads((ROOT/config_path).read_text())if config_path else {};OUT=ROOT/config.get('out','review/I_refinement/nautilus_r1/clean_cowl_r23');OUT.mkdir(parents=True,exist_ok=True);TARGET_SOURCE=ROOT/config.get('source','blender/collection/I_nautilus_clean_cowl_r23.blend');TARGET_COMPONENT=ROOT/config.get('component','app/assets/collection/components/I_nautilus_clean_cowl_r23.glb');s=json.loads((ROOT/config.get('base_report','review/I_refinement/nautilus_r1/cowl_rims_r22/build.json')).read_text());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();assert sha(ROOT/s['source'])==s['source_sha256'];assert not config.get('expected_parent_source_sha256')or s['source_sha256']==config['expected_parent_source_sha256']
bpy.ops.wm.open_mainfile(filepath=str(ROOT/s['source']));bpy.context.scene.frame_set(1);bpy.context.view_layer.update();root=bpy.data.objects['IN1_BodyRoot'];mouth=bpy.data.objects['IAM_MODULE'].matrix_world;o=bpy.data.objects['IN1_PorcelainPanel_%02d'%int(config.get('panel',1))];world=o.matrix_world;inverse=world.inverted();back=mouth.to_3x3().col[2].normalized();right=mouth.to_3x3().col[0].normalized();up=mouth.to_3x3().col[1].normalized();center=mouth.translation;end_depth=float(config['end_depth']);front_depth=-.035
def fingerprint(obj):
    digest=hashlib.sha256();m=obj.data;m.calc_loop_triangles()
    for v in m.vertices:digest.update(struct.pack('<3f',*v.co))
    for t in m.loop_triangles:digest.update(struct.pack('<3I',*t.vertices))
    for n in m.corner_normals:digest.update(struct.pack('<3f',*n.vector))
    for uv in m.uv_layers:
        digest.update(uv.name.encode())
        for v in uv.data:digest.update(struct.pack('<2f',*v.uv))
    if m.shape_keys:
        for key in m.shape_keys.key_blocks:
            digest.update(key.name.encode())
            for v in key.data:digest.update(struct.pack('<3f',*v.co))
    return [digest.hexdigest(),[list(r)for r in obj.matrix_world],[mat.name if mat else None for mat in m.materials],[f.material_index for f in m.polygons]]
assert o.data.users==1
fixed_cheek=bpy.data.objects.get(config.get('fixed_cheek_name',''))
protected={ob.name:fingerprint(ob)for ob in bpy.data.objects if ob.type=='MESH'and ob!=o and ob!=fixed_cheek}
bm=bmesh.new();bm.from_mesh(o.data);bm.normal_update();plane=center+back*end_depth
bmesh.ops.bisect_plane(bm,geom=list(bm.verts)+list(bm.edges)+list(bm.faces),plane_co=inverse@plane,plane_no=world.to_3x3().transposed()@back,dist=1e-8,clear_inner=True)
bm.normal_update();cut_zero_edges=[e for e in bm.edges if len(e.link_faces)==1 and tuple(world@e.verts[0].co)==tuple(world@e.verts[1].co)];cut_parents={}
def cut_root(v):
    cut_parents.setdefault(v,v)
    if cut_parents[v]!=v:cut_parents[v]=cut_root(cut_parents[v])
    return cut_parents[v]
for e in cut_zero_edges:
    a,b=[cut_root(v)for v in e.verts]
    if a!=b:cut_parents[b]=a
cut_targets={v:cut_root(v)for v in cut_parents if cut_root(v)!=v};cut_coordinates={v:v.co.copy()for v in set(cut_targets.values())};cut_before={tuple(world@v.co)for v in bm.verts}
if cut_targets:
    bmesh.ops.weld_verts(bm,targetmap=cut_targets)
    for v,co in cut_coordinates.items():
        if v.is_valid:v.co=co
assert cut_before=={tuple(world@v.co)for v in bm.verts}
bm.normal_update();boundary=[e for e in bm.edges if len(e.link_faces)==1];assert boundary and all(abs((world@v.co-plane).dot(back))<2e-6 for e in boundary for v in e.verts)
C=Vector((.12,.16,1.96));radii=Vector((1.01,.67,1.10));qn=Vector((radii[i]**2*back[i]for i in range(3)));section_center=C+qn*((plane-C).dot(back)/back.dot(qn));normal_matrix=world.to_3x3().inverted().transposed();fraction={};confidence={}
for e in boundary:
    mid=world@((e.verts[0].co+e.verts[1].co)*.5);radial=Vector(((mid[i]-C[i])/(radii[i]**2)for i in range(3))).normalized();dot=(normal_matrix@e.link_faces[0].normal).normalized().dot(radial)
    if abs(dot)<.35:continue
    for v in e.verts:
        if abs(dot)>confidence.get(v,0):fraction[v]=0. if dot>0 else 1.;confidence[v]=abs(dot)
vertices=set(v for e in boundary for v in e.verts);neighbors={v:[e.other_vert(v)for e in v.link_edges if e in boundary]for v in vertices};assert all(len(v)==2 for v in neighbors.values())
unknown=vertices-set(fraction)
while unknown:
    seed=next(iter(unknown));component={seed};pending=[seed]
    while pending:
        for v in neighbors[pending.pop()]:
            if v in unknown and v not in component:component.add(v);pending.append(v)
    ends=[(v,w)for v in component for w in neighbors[v]if w in fraction];assert len(ends)==2
    current,previous=ends[0];chain=[previous]
    while current in component:
        chain.append(current);following=next(v for v in neighbors[current]if v!=previous);previous,current=current,following
    chain.append(current);lengths=[(world.to_3x3()@(b.co-a.co)).length for a,b in zip(chain,chain[1:])];total=sum(lengths);distance=0.
    for i,v in enumerate(chain[1:-1]):distance+=lengths[i];fraction[v]=fraction[chain[0]]+(fraction[chain[-1]]-fraction[chain[0]])*distance/total
    unknown-=component
loops=[];unvisited=set(vertices)
while unvisited:
    first=next(iter(unvisited));loop=[first];previous=None;current=first
    while True:
        following=next(v for v in neighbors[current]if v!=previous)
        if following==first:break
        loop.append(following);previous,current=current,following
    unvisited-=set(loop);loops.append(loop)
diagnostic=[]
for loop in loops:
    labels=[0 if fraction[v]<.25 else 1 if fraction[v]>.75 else 2 for v in loop]
    transitions=[i for i in range(len(loop))if labels[i]!=labels[(i-1)%len(loop)]]
    diagnostic.append({'vertices':len(loop),'transitions':[(i,labels[i])for i in transitions],'rows':[{'end':list(world@v.co),'wall_fraction':fraction[v]}for v in loop]})
(OUT/'section_diagnostic.json').write_text(json.dumps(diagnostic,indent=2)+'\n')
print('SECTION_LOOPS',[{'vertices':r['vertices'],'transitions':r['transitions']}for r in diagnostic],flush=True)
if '--inspect-section' in sys.argv:sys.exit(0)
existing=TARGET_SOURCE
if existing.exists():
    old=json.loads((OUT/'build.json').read_text());assert sha(existing)==old['source_sha256'];archive=OUT/'iterations'/old['source_sha256'][:12];archive.mkdir(parents=True,exist_ok=True)
    for p in OUT.glob('*.json'):shutil.copy2(p,archive/p.name)
    if (OUT/'views').exists():shutil.copytree(OUT/'views',archive/'views',dirs_exist_ok=True)
    shutil.copy2(existing,existing.parent/'checkpoints'/('I-clean-cowl-'+old['source_sha256'][:12]+'.blend'))
angles={};cap_loops=[]
def raw_angle(v):
    delta=world@v.co-section_center
    return math.atan2(delta.dot(up),delta.dot(right))
def near_angle(value,reference):return reference+(value-reference+math.pi)%math.tau-math.pi
for loop in loops:
    tags=[0 if fraction[v]<.001 else 1 if fraction[v]>.999 else 2 for v in loop]
    start=next(i for i in range(len(loop))if tags[i]==0 and tags[(i-1)%len(loop)]!=0);outer=[];i=start
    while tags[i]==0:outer.append(loop[i]);i=(i+1)%len(loop)
    start=next(i for i in range(len(loop))if tags[i]==1 and tags[(i-1)%len(loop)]!=1);inner=[];i=start
    while tags[i]==1:inner.append(loop[i]);i=(i+1)%len(loop)
    inner.reverse();theta=[raw_angle(outer[0])]
    for v in outer[1:]:theta.append(near_angle(raw_angle(v),theta[-1]))
    first=(theta[0]+near_angle(raw_angle(inner[0]),theta[0]))/2;last=(theta[-1]+near_angle(raw_angle(inner[-1]),theta[-1]))/2
    for arc in [outer,inner]:
        lengths=[0.]
        for a,b in zip(arc,arc[1:]):lengths.append(lengths[-1]+max((world.to_3x3()@(b.co-a.co)).length,1e-8))
        for v,length in zip(arc,lengths):angles[v]=first+(last-first)*length/lengths[-1]
    caps=[]
    for a,b,exclude,value in [(outer[0],inner[0],outer[1],first),(outer[-1],inner[-1],outer[-2],last)]:
        chain=[a];previous=a;current=next(v for v in neighbors[a]if v!=exclude)
        while current!=b:
            assert current not in chain;chain.append(current);angles[current]=value;following=next(v for v in neighbors[current]if v!=previous);previous,current=current,following
        chain.append(b);caps.append(chain)
    assert all(v in angles for v in loop)
    cap_loops.append((outer,inner,caps))
uniform_record=None
if config.get('uniform_loft'):
    sys.path.insert(0,str(Path(__file__).parent))
    from i_uniform_cowl_loft import add as add_uniform_cowl
    obstacle=json.loads((ROOT/'review/I_refinement/nautilus_r1/cowl_fairing_r22/mouth_obstacle.json').read_text());assert obstacle['mouth_component_sha256']==s['mouth_component_sha256'];profile=obstacle['profile']
    def required_radius(z):
        for a,b in zip(profile,profile[1:]):
            if a[0]<=z<=b[0]:return (a[1]+(b[1]-a[1])*(z-a[0])/(b[0]-a[0]))*.70+.003
        raise AssertionError(('Outside measured A axial envelope',z))
    uniform_record=add_uniform_cowl(bm,world,inverse,center,back,right,up,cap_loops,angles,fraction,required_radius,front_depth,end_depth)
    records=uniform_record['paths'];bulge=uniform_record['bulge']
else:
    paths={};steps=48;records=[];point_paths={}
    for v in vertices:
        end=world@v.co;angle=angles[v];radius=(.962158*(1-fraction[v])+.927872*fraction[v])*.70;begin=center+back*front_depth+(right*math.cos(angle)+up*math.sin(angle))*radius;path=[]
        # Shared axial handle lengths avoid the independent inner/outer tangent
        # overshoot that folded the previous thin loft back through itself.
        c1=begin+back*(end_depth-front_depth)*.30;c2=end-back*(end_depth-front_depth)*.30
        for j in range(steps):
            t=j/steps;p=begin*(1-t)**3+c1*(3*(1-t)**2*t)+c2*(3*(1-t)*t*t)+end*t**3;path.append(p)
        point_paths[v]=path;records.append({'end':list(end),'start':list(begin),'wall_fraction':fraction[v]})
    obstacle=json.loads((ROOT/'review/I_refinement/nautilus_r1/cowl_fairing_r22/mouth_obstacle.json').read_text());assert obstacle['mouth_component_sha256']==s['mouth_component_sha256'];profile=obstacle['profile']
    def required_radius(z):
        for a,b in zip(profile,profile[1:]):
            if a[0]<=z<=b[0]:return (a[1]+(b[1]-a[1])*(z-a[0])/(b[0]-a[0]))*.70+.003
        raise AssertionError(('Outside measured A axial envelope',z))
    bulge=0.
    for j in range(1,steps):
        points=[path[j]for v,path in point_paths.items()if fraction[v]>.75];axial=(points[0]-center).dot(back);minimum=min((p-center-back*axial).length for p in points);needed=max(0.,required_radius(axial/.70)-minimum);bulge=max(bulge,needed/math.sin(math.pi*j/steps)**2)
    for v,points in point_paths.items():
        path=[]
        for j,p in enumerate(points):
            radial=p-center-back*(p-center).dot(back);p=p+radial.normalized()*bulge*math.sin(math.pi*j/steps)**2;path.append(bm.verts.new(inverse@p))
        path.append(v);paths[v]=path
    for e in boundary:
        a,b=e.verts
        for j in range(steps):bm.faces.new((paths[a][j],paths[b][j],paths[b][j+1],paths[a][j+1]))
    front=[e for e in bm.edges if len(e.link_faces)==1];assert all(abs((world@v.co-center).dot(back)-front_depth)<2e-6 for e in front for v in e.verts)
    # Zip the two monotone arcs explicitly. A large concave n-gon cap can
    # triangulate across the aperture when its boundary doubles back.
    for outer,inner,caps in cap_loops:
        i=j=0;triangles=[]
        while i<len(outer)-1 or j<len(inner)-1:
            span=angles[outer[-1]]-angles[outer[0]]
            a=(angles[outer[i+1]]-angles[outer[0]])/span if i<len(outer)-1 else 2.;b=(angles[inner[j+1]]-angles[inner[0]])/span if j<len(inner)-1 else 2.
            if a<=b:triangles.append([outer[i],outer[i+1],inner[j]]);i+=1
            else:triangles.append([outer[i],inner[j+1],inner[j]]);j+=1
        for triangle in triangles:
            expanded=[triangle]
            for cap_chain in caps:
                if len(cap_chain)==2:continue
                result=[]
                for face in expanded:
                    cut=next((k for k in range(3)if {face[k],face[(k+1)%3]}=={cap_chain[0],cap_chain[-1]}),None)
                    if cut is None:result.append(face);continue
                    sequence=cap_chain if face[cut]==cap_chain[0]else list(reversed(cap_chain));third=face[(cut+2)%3]
                    result.extend([a,b,third]for a,b in zip(sequence,sequence[1:]))
                expanded=result
            for face in expanded:bm.faces.new([paths[v][0]for v in face])
zero_edges=[e for e in bm.edges if tuple(world@e.verts[0].co)==tuple(world@e.verts[1].co)and all((world@v.co-center).dot(back)<=end_depth+1e-6 for v in e.verts)]
parents={}
def representative(v):
    parents.setdefault(v,v)
    if parents[v]!=v:parents[v]=representative(parents[v])
    return parents[v]
for e in zero_edges:
    a,b=[representative(v)for v in e.verts]
    if a!=b:
        if b in vertices and a not in vertices:a,b=b,a
        parents[b]=a
targets={v:representative(v)for v in parents if representative(v)!=v};before_world={tuple(world@v.co)for v in bm.verts};target_coordinates={v:v.co.copy()for v in set(targets.values())};incident_area={p:0. for p in before_world}
for triangle in bm.calc_loop_triangles():
    points=[world@loop.vert.co for loop in triangle];area=(points[1]-points[0]).cross(points[2]-points[0]).length/2
    for p in points:incident_area[tuple(p)]+=area
if targets:
    bmesh.ops.weld_verts(bm,targetmap=targets)
    for v,co in target_coordinates.items():
        if v.is_valid:v.co=co
after_world={tuple(world@v.co)for v in bm.verts};missing=before_world-after_world;added=after_world-before_world
weld_proof={'connected_zero_edges':len(zero_edges),'welded_vertices':len(targets),'added_world_points':len(added),'removed_world_points':[{'point':p,'old_incident_area':incident_area[p]}for p in missing]}
(OUT/'weld_diagnostic.json').write_text(json.dumps(weld_proof,indent=2)+'\n')
assert not added and all(incident_area[p]<=1e-14 for p in missing),(len(added),len(missing),max((incident_area[p]for p in missing),default=0.))
bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));assert all(e.is_manifold for e in bm.edges)and all(v.is_manifold for v in bm.verts)
for f in bm.faces:f.smooth=True
for e in bm.edges:e.smooth=e.is_manifold and e.calc_face_angle()<.65
bm.to_mesh(o.data);bm.free();o.data.update();o.data.normals_split_custom_set([(0.,0.,0.)]*len(o.data.loops))
split_record=None
if fixed_cheek is not None:
    assert int(config.get('panel',1))==5 and fixed_cheek.data.users==1
    original_mesh=o.data.copy();height=float(config['fixed_cheek_height']);gap=float(config.get('fixed_cheek_gap',.004));split_counts=[]
    for part,z,upper in [(o,height+gap/2,True),(fixed_cheek,height-gap/2,False)]:
        cut=bmesh.new();cut.from_mesh(original_mesh);plane_co=inverse@Vector((0,0,z));plane_no=world.to_3x3().transposed()@Vector((0,0,1))
        bmesh.ops.bisect_plane(cut,geom=list(cut.verts)+list(cut.edges)+list(cut.faces),plane_co=plane_co,plane_no=plane_no,dist=1e-8,clear_inner=upper,clear_outer=not upper)
        edge_list=[e for e in cut.edges if len(e.link_faces)==1];assert edge_list and all(abs((world@v.co).z-z)<2e-6 for e in edge_list for v in e.verts)
        cap=bmesh.ops.holes_fill(cut,edges=edge_list,sides=0)['faces'];bmesh.ops.triangulate(cut,faces=cap)
        transform=part.matrix_world.inverted()@world
        for v in cut.verts:v.co=transform@v.co
        bmesh.ops.recalc_face_normals(cut,faces=list(cut.faces));assert len(cut.verts)>100 and all(e.is_manifold for e in cut.edges)
        mesh=original_mesh.copy();cut.to_mesh(mesh);cut.free();part.data=mesh;part.data.update();part.data.normals_split_custom_set([(0.,0.,0.)]*len(part.data.loops));split_counts.append({'mesh':part.name,'vertices':len(mesh.vertices),'cut_plane_world_z':z})
    split_record={'height_world_z':height,'gap':gap,'parts':split_counts,'policy':'The lower cheek is rebuilt from the same complete new cowl, fixed to its original parent; the upper portion retains the existing moving carrier.'}
assert all(fingerprint(bpy.data.objects[n])==value for n,value in protected.items())
source=TARGET_SOURCE;component=TARGET_COMPONENT;bpy.ops.wm.save_as_mainfile(filepath=str(source),compress=True);bpy.ops.object.select_all(action='DESELECT')
for ob in [root,*root.children_recursive]:ob.select_set(True)
bpy.context.view_layer.objects.active=root;bpy.ops.export_scene.gltf(filepath=str(component),export_format='GLB',use_selection=True,export_animations=False,export_morph=True,export_morph_normal=True,export_extras=True)
modified=[o.name]+([fixed_cheek.name]if fixed_cheek is not None else [])
d={**s,'source':str(source.relative_to(ROOT)),'source_sha256':sha(source),'component':str(component.relative_to(ROOT)),'component_sha256':sha(component),'parent_source_sha256':s['source_sha256'],'clean_cowl':{'modified_meshes':modified,'section_depth_world':end_depth,'front_depth_world':front_depth,'section_center':list(section_center),'paths':records,'common_radial_bulge_world':bulge,'exact_zero_edge_vertices_welded':len(targets),'world_vertex_set_preserved_in_weld':not missing and not added,'zero_area_points_removed_in_weld':len(missing),'fixed_cheek_split':split_record,'uniform_loft':uniform_record,'construction':'Retained actual body section, monotone paired front arcs, explicit zipped cap and shared Bezier handles; smooth common radial bulge follows measured A clearance without changing endpoints. Only connected edges with componentwise-identical world coordinates are welded; any removed unique point must have zero incident surface area.'},'status':'first_clean_section_candidate_requires_clearance_and_visual_review'};d['cowl_finish']={**s['cowl_finish'],'modified_meshes':modified};art=ROOT/config['art'];art.mkdir(parents=True,exist_ok=True)
layout=json.loads((ROOT/str(s['chamber_response_layout']).replace('res://','app/')).read_text());assert layout['source_sha256']==s['source_sha256'];layout.update(source_sha256=d['source_sha256'],component_sha256=d['component_sha256']);(art/'chamber_layout.json').write_text(json.dumps(layout,indent=2)+'\n');d['chamber_response_layout']='res://'+str((art/'chamber_layout.json').relative_to(ROOT/'app'));d['deep_cowl_parent_geometry_preserved']=True
(OUT/'build.json').write_text(json.dumps(d,indent=2)+'\n');(OUT/'protected_geometry.json').write_text(json.dumps({'source_sha256':d['source_sha256'],'passed':True,'protected_mesh_count':len(protected),'modified_meshes':modified},indent=2)+'\n');print('CLEAN_COWL_SOURCE',d['source_sha256'],flush=True)
