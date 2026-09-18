"""Four bolted clamp seats for chamber 01, using the real three surface layers."""
import bpy,bmesh,json,hashlib,sys,shutil,struct,math
from pathlib import Path
from mathutils import Vector,Matrix
from mathutils.bvhtree import BVHTree
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(Path(__file__).parent));import i_fitted_surface as fitted;import i_fitted_laminate as laminate;import i_machined_geometry as h
args=sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else [];batch='--batch' in args;cells=[2,3,10,11,12] if batch else [1]
OUT=ROOT/('review/I_refinement/nautilus_r1/chamber_seats_r10' if batch else 'review/I_refinement/nautilus_r1/chamber_seats_r9');OUT.mkdir(parents=True,exist_ok=True);TARGET=ROOT/('blender/collection/I_nautilus_chamber_seats_r10.blend' if batch else 'blender/collection/I_nautilus_chamber_seats_r9.blend');sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
seed=json.loads((ROOT/('review/I_refinement/nautilus_r1/chamber_seats_r9/build.json' if batch else 'review/I_refinement/nautilus_r1/receiver_pocket_r8/build.json')).read_text());plan=json.loads((ROOT/('review/I_refinement/nautilus_r1/chamber_seats_r10/layout_candidates.json' if batch else 'review/I_refinement/nautilus_r1/chamber_seats_r9/layout_candidates.json')).read_text());assert seed['source_sha256']==plan['source_sha256']==sha(ROOT/seed['source'])
if batch:assert json.loads((ROOT/'review/I_refinement/nautilus_r1/chamber_seats_r9/checkpoint.json').read_text())['source_sha256']==seed['source_sha256']
else:assert seed['source_sha256']==plan['source_sha256']
if TARGET.exists():
    old=json.loads((OUT/'build.json').read_text());assert sha(TARGET)==old['source_sha256'],'Unrecorded chamber-seat edits';archive=OUT/'iterations'/old['source_sha256'][:12];archive.mkdir(parents=True,exist_ok=True)
    for p in OUT.glob('*.json'):shutil.copy2(p,archive/p.name)
    if (OUT/'views').exists():shutil.copytree(OUT/'views',archive/'views',dirs_exist_ok=True)
    (TARGET.parent/'checkpoints'/('I-chamber-seats-'+old['source_sha256'][:12]+'.blend')).write_bytes(TARGET.read_bytes())
bpy.ops.wm.open_mainfile(filepath=str(ROOT/seed['source']));scene=bpy.context.scene;scene.frame_set(1);bpy.context.view_layer.update();body=bpy.data.objects['IN1_BodyRoot'];core=bpy.data.objects['IN3_ContinuousThroat'];frame=bpy.data.objects['IN1_CellFrame_01'];film=bpy.data.objects['IN1_CellDiaphragm_01']
allowed={core.name}|{name for cell in cells for name in ['IN1_CellFrame_%02d'%cell,'IN1_CellDiaphragm_%02d'%cell,'IN1_CellLand_%02d_L'%cell,'IN1_CellLand_%02d_R'%cell]}
def fingerprint(o):
    digest=hashlib.sha256()
    for v in o.data.vertices:digest.update(struct.pack('<3f',*v.co))
    for f in o.data.polygons:digest.update(struct.pack('<'+'I'*len(f.vertices),*f.vertices))
    return [digest.hexdigest(),[list(r) for r in o.matrix_world],o.parent.name if o.parent else None,[m.name if m else None for m in o.data.materials]]
protected={o.name:fingerprint(o) for o in bpy.data.objects if o.type=='MESH' and o.name not in allowed}
triangulation=[]
edited=[core]+[bpy.data.objects[name] for cell in cells for name in ['IN1_CellFrame_%02d'%cell,'IN1_CellDiaphragm_%02d'%cell]]
for o in edited:
    assert not o.modifiers,'Freeze evaluated geometry before machining'
    old=o.data;old.calc_loop_triangles();triangles=list(old.loop_triangles);points=[tuple(v.co) for v in old.vertices];faces=[tuple(t.vertices) for t in triangles];normals=[old.corner_normals[i].vector.copy() for t in triangles for i in t.loops]
    data=bpy.data.meshes.new(o.name+'_MachiningTriangles');data.from_pydata(points,[],faces);data.update()
    for material in old.materials:data.materials.append(material)
    for polygon,t in zip(data.polygons,triangles):polygon.material_index=old.polygons[t.polygon_index].material_index;polygon.use_smooth=old.polygons[t.polygon_index].use_smooth
    for layer in old.uv_layers:
        uv=data.uv_layers.new(name=layer.name)
        for i,t in enumerate(triangles):
            for j,loop in enumerate(t.loops):uv.data[i*3+j].uv=layer.data[loop].uv
    data.normals_split_custom_set(normals);o.data=data;triangulation.append({'mesh':o.name,'source_vertices':len(points),'source_triangles':len(faces),'outer_geometry':'Original loop triangles and corner normals frozen before bores'})
col=bpy.data.collections.new('I_CHAMBER_SEATS_R10' if batch else 'I_CHAMBER_SEATS_R9');scene.collection.children.link(col);h.configure(col);root=h.empty('IS10_ChamberSeats' if batch else 'IS9_ChamberSeats',body)
def own_mesh(name,vs,fs,parent):
    m=bpy.data.meshes.new(name+'Mesh');m.from_pydata(vs,[],fs);m.update();o=bpy.data.objects.new(name,m);col.objects.link(o);h.finish(o,name,parent,(0,0,0),'A_Satin')
    bm=bmesh.new();bm.from_mesh(o.data);bad=sum(not e.is_manifold for e in bm.edges);volume=bm.calc_volume(signed=True)
    if volume<0:bmesh.ops.reverse_faces(bm,faces=list(bm.faces));volume=-volume;bm.to_mesh(o.data)
    bm.free();assert not bad and volume>1e-8,(name,bad,volume)
    return o
def local_tree(o,matrix):
    bpy.context.view_layer.update();o.data.calc_loop_triangles();inverse=matrix.inverted();v=[inverse@o.matrix_world@p.co for p in o.data.vertices];f=[tuple(t.vertices) for t in o.data.loop_triangles];return BVHTree.FromPolygons(v,f,all_triangles=True)
def crossings(tree,x,y):
    p=Vector((x,y,5));result=[]
    for _ in range(12):
        hit=tree.ray_cast(p,Vector((0,0,-1)),10.)
        if hit[0] is None:break
        result.append(hit[0].z);p=hit[0]+Vector((0,0,-.00001))
    return result
selected=[]
for cell in cells:
    for side in ['L','R']:
        candidates=[r for r in plan['candidates'] if r['cell']==cell and r['side']==side]
        front=[r for r in candidates if r['phi']<=1.6];rear=[r for r in candidates if r['phi']>=1.8];assert front and rear,('Missing complete seat footprint',cell,side)
        selected.extend([min(front,key=lambda r:abs(r['phi']-1.0)),min(rear,key=lambda r:abs(r['phi']-2.2))])
seats=[]
for index,row in enumerate(selected):
    cell=row['cell'];frame=bpy.data.objects[row['frame']];film=bpy.data.objects[row['film']]
    prefix='IS9_C%02d_%s_%02d_'%(cell,row['side'],index);matrix=Matrix(row['matrix']);seat=h.empty(prefix+'SeatFrame',root);seat.matrix_world=matrix;outline=row['outline'];bpy.context.view_layer.update()
    frame_under=fitted.clipped_surface([frame],outline,frame=matrix,from_positive=False,normal_limit=.80,with_planes=True);film_front=fitted.clipped_surface([film],outline,frame=matrix,from_positive=True,normal_limit=.80,with_planes=True);film_back=fitted.clipped_surface([film],outline,frame=matrix,from_positive=False,normal_limit=.80,with_planes=True);core_front=fitted.clipped_surface([core],outline,frame=matrix,from_positive=True,normal_limit=.80,with_planes=True)
    uv,uf,upper_fit=laminate.between(frame_under,film_front);lv,lf,lower_fit=laminate.between(film_back,core_front);upper=own_mesh(prefix+'UpperClamp',uv,uf,seat);lower=own_mesh(prefix+'LowerStand',lv,lf,seat)
    bolts=[]
    for bolt_index,y in enumerate([-.012,.012]):
        tree_frame=local_tree(frame,matrix);tree_core=local_tree(core,matrix);samples=[]
        for k in range(24):
            a=k*math.tau/24;hits=crossings(tree_frame,.0062*math.cos(a),y+.0062*math.sin(a));assert len(hits)>=2; samples.append(hits[0])
        seat_z=min(samples)-.0006;core_hits=crossings(tree_core,0.,y);assert len(core_hits)>=2
        core_outer,core_inner=core_hits[:2];wall=core_outer-core_inner;blind_depth=min(.016,wall*.60);assert blind_depth>.008,(cell,row['side'],row['phi'],bolt_index,core_hits[:4])
        # Real flat head seat, through stack bores, and a blind core thread.
        h.drill(frame,.0062,.050,seat,(0,y,seat_z+.025))
        through_bottom=core_outer-.004;through_top=seat_z+.015
        for obj in [frame,upper,film,lower]:h.drill(obj,.00245,through_top-through_bottom,seat,(0,y,(through_top+through_bottom)/2),solver='MANIFOLD' if obj in [upper,lower] else 'EXACT')
        h.drill(core,.00245,blind_depth+.002,seat,(0,y,core_outer+(.002-blind_depth)/2))
        washer=h.sleeve(prefix+'Bolt%d_Washer'%bolt_index,.0055,.00255,.0012,seat,(0,y,seat_z+.0007),'A_Bronze')
        head_z=seat_z+.0034;start=core_outer-blind_depth+.001
        shank=h.cylinder(prefix+'Bolt%d'%bolt_index,.0022,head_z-start,seat,(0,y,(head_z+start)/2),'A_Nickel',bevel=.0001);head=h.screw(prefix+'Bolt%d_Head'%bolt_index,seat,(0,y,head_z),.0048)
        bpy.context.view_layer.update();bpy.context.view_layer.objects.active=shank;mod=shank.modifiers.new('One-piece fastener','BOOLEAN');mod.operation='UNION';mod.solver='EXACT';mod.object=head;bpy.ops.object.modifier_apply(modifier=mod.name);h.parts.remove(head.name);bpy.data.objects.remove(head,do_unlink=True)
        bolts.append({'mesh':shank.name,'washer':washer.name,'local_xy':[0,y],'head_seat_z':seat_z,'head_center_z':head_z,'shaft_bottom_z':start,'shaft_top_z':head_z,'core_outer_z':core_outer,'core_inner_z':core_inner,'blind_depth':blind_depth,'remaining_core_wall_on_axis':wall-blind_depth,'shaft_radius':.0022,'bore_radius':.00245})
        assert all(len(o.data.vertices)>20 and len(o.data.polygons)>20 for o in [upper,lower]),'A bore removed a clamp solid'
    seats.append({'cell':cell,'source_frame':frame.name,'source_film':film.name,'side':row['side'],'phi':row['phi'],'frame':seat.name,'matrix_blender':[list(r) for r in matrix],'upper':upper.name,'lower':lower.name,'upper_fit':upper_fit,'lower_fit':lower_fit,'bolts':bolts})
    print('REAL_CHAMBER_SEAT_BUILT',index+1,len(selected),flush=True)
removed=[]
for name in [name for cell in cells for name in ['IN1_CellLand_%02d_L'%cell,'IN1_CellLand_%02d_R'%cell]]:
    o=bpy.data.objects[name];removed.append({'name':name,'fingerprint':fingerprint(o),'reason':'Replaced by four source-fitted bolted frame/film/core clamps; continuous border finishing remains pending'});bpy.data.objects.remove(o,do_unlink=True)
cleanup=[]
for name in [o.name for o in edited]+list(h.parts):
    o=bpy.data.objects.get(name)
    if o is None or o.type!='MESH':continue
    bm=bmesh.new();bm.from_mesh(o.data);before=sum(not e.is_manifold for e in bm.edges);bmesh.ops.remove_doubles(bm,verts=list(bm.verts),dist=1e-6);bmesh.ops.dissolve_degenerate(bm,edges=list(bm.edges),dist=3e-6)
    flaps=[f for f in bm.faces if f.calc_area()<1e-10 and any(len(e.link_faces)>2 for e in f.edges)]
    if flaps:bmesh.ops.delete(bm,geom=flaps,context='FACES_ONLY')
    loose=[e for e in bm.edges if not e.link_faces]
    if loose:bmesh.ops.delete(bm,geom=loose,context='EDGES')
    dissolved=0
    for _ in range(64):
        bm.normal_update();choice=None
        for face in bm.faces:
            if face.calc_area()>=1e-12:continue
            for edge in sorted(face.edges,key=lambda e:e.calc_length(),reverse=True):
                if len(edge.link_faces)!=2:continue
                other=next(f for f in edge.link_faces if f!=face)
                if other.calc_area()<1e-10:continue
                origin=other.verts[0].co
                if max(abs((v.co-origin).dot(other.normal)) for v in face.verts)<1e-6:choice=edge;break
            if choice:break
        if choice is None:break
        bmesh.ops.dissolve_edges(bm,edges=[choice],use_verts=False,use_face_split=False);dissolved+=1
    bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces))
    if bm.calc_volume(signed=True)<0:bmesh.ops.reverse_faces(bm,faces=list(bm.faces))
    cleanup.append({'name':name,'nonmanifold_before':before,'removed_boolean_flaps':len(flaps),'collapsed_subprecision_faces':dissolved,'nonmanifold_after':sum(not e.is_manifold for e in bm.edges)});bm.to_mesh(o.data);bm.free()
bpy.context.view_layer.update();changed=[name for name,value in protected.items() if fingerprint(bpy.data.objects[name])!=value];assert not changed,changed
bpy.ops.wm.save_as_mainfile(filepath=str(TARGET),compress=True);bpy.ops.object.select_all(action='DESELECT')
for o in [body,*body.children_recursive]:o.select_set(True)
bpy.context.view_layer.objects.active=body;component=ROOT/('app/assets/collection/components/I_nautilus_chamber_seats_r10.glb' if batch else 'app/assets/collection/components/I_nautilus_chamber_seats_r9.glb');bpy.ops.export_scene.gltf(filepath=str(component),export_format='GLB',use_selection=True,export_animations=False,export_morph=False,export_extras=True)
result={**seed,'source':str(TARGET.relative_to(ROOT)),'source_sha256':sha(TARGET),'component':str(component.relative_to(ROOT)),'component_sha256':sha(component),'parent_source_sha256':seed['source_sha256'],'chamber_seats':seats,'new_seat_meshes':list(h.parts),'replaced_unfitted_webs':removed,'seat_cleanup':cleanup,'status':'first_chamber_clamp_candidate_checks_pending','review_scope':'R8 exterior/A/rear fixture preserved. Chamber01 now has four actual paired-surface upper clamps/lower stands, frame and film bores, blind core bores and eight real tie bolts. Source fitting, full contacts, border capture/finish, remaining chambers and native/art acceptance are still pending.'}
result['machining_triangulation']=triangulation
if batch:
    result['chamber_seats']=seed['chamber_seats']+seats;result['new_seat_meshes']=seed['new_seat_meshes']+list(h.parts);result['replaced_unfitted_webs']=seed['replaced_unfitted_webs']+removed
    result['status']='six_chamber_clamp_candidate_checks_pending';result['review_scope']='Preserves verified chamber01 and adds four actual clamp seats to each of chambers02/03/10/11/12. Current core surface is refitted and blind holes remeasured. Remaining throat-side chamber ends, continuous border capture, base load path, upper-cover mechanisms and native/art acceptance remain incomplete.'
result['newly_seated_cells']=cells;result['audit_new_seat_meshes']=list(h.parts)
(OUT/'build.json').write_text(json.dumps(result,indent=2)+'\n');(OUT/'protected_geometry.json').write_text(json.dumps({'source_sha256':result['source_sha256'],'passed':not changed,'count':len(protected),'changed':changed,'allowed_changes':sorted(allowed)},indent=2)+'\n');print('REAL_CHAMBER_SEATS_BUILT',flush=True)
