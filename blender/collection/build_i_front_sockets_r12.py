"""Chamber05 split front/rear frames: fitted through-bolted sockets with inner backing."""
import bpy,bmesh,json,hashlib,sys,shutil,struct,math
from pathlib import Path
from mathutils import Vector,Matrix
from mathutils.bvhtree import BVHTree
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(Path(__file__).parent))
import i_fitted_surface as fitted
import i_fitted_laminate as laminate
import i_machined_geometry as h
import i_boolean_residue as residue
args=sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else [];batch='--batch' in args;last_cell='--last-cell' in args;assert not(batch and last_cell);cells=[4] if last_cell else [6,7,8,9] if batch else [5]
stem='chamber04_r15' if last_cell else 'throat_sockets_r13' if batch else 'front_sockets_r12';source_stem='throat_terminations_r16/triangles' if last_cell else 'front_sockets_r12' if batch else 'throat_chambers_r11'
OUT=ROOT/('review/I_refinement/nautilus_r1/'+stem);OUT.mkdir(parents=True,exist_ok=True)
TARGET=ROOT/('blender/collection/I_nautilus_'+stem+'.blend');COMPONENT=ROOT/('app/assets/collection/components/I_nautilus_'+stem+'.glb')
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
seed_path=ROOT/('review/I_refinement/nautilus_r1/'+source_stem+'/build.json');seed=json.loads(seed_path.read_text());plan=json.loads((OUT/('layout_candidates.json' if batch or last_cell else 'c05_cap_candidates.json')).read_text())
assert sha(ROOT/seed['source'])==seed['source_sha256']==plan['source_sha256']
assert json.loads((seed_path.parent/'checkpoint.json').read_text())['source_sha256']==seed['source_sha256']
if TARGET.exists():
    old=json.loads((OUT/'build.json').read_text());assert sha(TARGET)==old['source_sha256'],'Unrecorded R12 edits'
    archive=OUT/'iterations'/old['source_sha256'][:12];archive.mkdir(parents=True,exist_ok=True)
    for p in OUT.glob('*.json'):shutil.copy2(p,archive/p.name)
    if (OUT/'views').exists():shutil.copytree(OUT/'views',archive/'views',dirs_exist_ok=True)
    (TARGET.parent/'checkpoints'/('I-front-sockets-'+old['source_sha256'][:12]+'.blend')).write_bytes(TARGET.read_bytes())
bpy.ops.wm.open_mainfile(filepath=str(ROOT/seed['source']));scene=bpy.context.scene;scene.frame_set(1);bpy.context.view_layer.update()
body=bpy.data.objects['IN1_BodyRoot'];core=bpy.data.objects['IN3_ContinuousThroat'];frame=bpy.data.objects['IN1_CellFrame_05'];film=bpy.data.objects['IN1_CellDiaphragm_05']
allowed={core.name}|{'IN1_Cell%s_%02d%s'%(kind,cell,suffix) for cell in cells for kind,suffix in [('Frame',''),('Diaphragm',''),('Land','_L'),('Land','_R')]}
edited=[core]+[bpy.data.objects['IN1_Cell%s_%02d'%(kind,cell)] for cell in cells for kind in ['Frame','Diaphragm']]
def fingerprint(o):
    d=hashlib.sha256()
    for v in o.data.vertices:d.update(struct.pack('<3f',*v.co))
    for f in o.data.polygons:d.update(struct.pack('<'+'I'*len(f.vertices),*f.vertices))
    return [d.hexdigest(),[list(r) for r in o.matrix_world],o.parent.name if o.parent else None,[m.name if m else None for m in o.data.materials]]
protected={o.name:fingerprint(o) for o in bpy.data.objects if o.type=='MESH' and o.name not in allowed}
construction_cleanup=[]
if last_cell:
    o=bpy.data.objects['IN1_CellFrame_04'];bm=bmesh.new();bm.from_mesh(o.data);bm.verts.ensure_lookup_table();bm.verts.index_update();unseen=set(bm.verts);pieces=[]
    while unseen:
        stack=[unseen.pop()];piece=set()
        while stack:
            v=stack.pop();piece.add(v)
            for e in v.link_edges:
                other=e.other_vert(v)
                if other in unseen:unseen.remove(other);stack.append(other)
        points=[o.matrix_world@v.co for v in piece];center=sum(points,Vector())/len(points);faces={f for v in piece for f in v.link_faces};volume=0.
        for f in faces:
            p=[o.matrix_world@v.co-center for v in f.verts]
            for i in range(1,len(p)-1):volume+=p[0].dot(p[i].cross(p[i+1]))/6.
        low=Vector(tuple(min(p[i] for p in points) for i in range(3)));high=Vector(tuple(max(p[i] for p in points) for i in range(3)));pieces.append((piece,points,volume,low,high))
    assert len(pieces)==2
    tiny=[r for r in pieces if len(r[0])<=16 and abs(r[2])<1e-9 and (r[4]-r[3]).length<.005];assert len(tiny)==1
    piece,points,volume,low,high=tiny[0];mouth_inverse=bpy.data.objects['IAM_MODULE'].matrix_world.inverted();axial=[(mouth_inverse@p).z for p in points];assert max(abs(v-.34/.7) for v in axial)<.001
    camera=Vector((-3.,-7.70,3.55));forward=(Vector((0,0,1.66))-camera).normalized();right=forward.cross(Vector((0,0,1))).normalized();up=right.cross(forward);pixels=[]
    for p in points:
        relative=p-camera;depth=relative.dot(forward);pixels.append((520+520*relative.dot(right)/depth/math.tan(math.radians(16)),520-520*relative.dot(up)/depth/math.tan(math.radians(16))))
    construction_cleanup.append({'mesh':o.name,'removed_components':1,'original_vertex_indices':sorted(v.index for v in piece),'removed_vertex_count':len(piece),'volume':volume,'bounds_min':list(low),'bounds_max':list(high),'diagonal':(high-low).length,'mouth_axial_range':axial and [min(axial),max(axial)],'projected_pixel_span':[max(p[i] for p in pixels)-min(p[i] for p in pixels) for i in range(2)],'reason':'Measured tiny closed remnant on the original throat cutting plane; the authored chamber04 start was intended to avoid this detached tip. The large frame and all other chamber pieces are retained.'})
    bmesh.ops.delete(bm,geom=list(piece),context='VERTS');bm.to_mesh(o.data);bm.free()
for o in edited:
    assert not o.modifiers
    old=o.data;old.calc_loop_triangles();triangles=list(old.loop_triangles);m=bpy.data.meshes.new(o.name+'_R12Machining')
    m.from_pydata([tuple(v.co) for v in old.vertices],[],[tuple(t.vertices) for t in triangles]);m.update()
    for material in old.materials:m.materials.append(material)
    for p,t in zip(m.polygons,triangles):p.material_index=old.polygons[t.polygon_index].material_index;p.use_smooth=old.polygons[t.polygon_index].use_smooth
    for layer in old.uv_layers:
        uv=m.uv_layers.new(name=layer.name)
        for i,t in enumerate(triangles):
            for j,loop in enumerate(t.loops):uv.data[i*3+j].uv=layer.data[loop].uv
    m.normals_split_custom_set([old.corner_normals[i].vector.copy() for t in triangles for i in t.loops]);o.data=m
col=bpy.data.collections.new('I_CHAMBER04_SOCKETS_R15' if last_cell else 'I_THROAT_SOCKETS_R13' if batch else 'I_FRONT_SOCKETS_R12');scene.collection.children.link(col);h.configure(col);root=h.empty('IF15_Chamber04Sockets' if last_cell else 'IF13_ThroatSockets' if batch else 'IF12_FrontSockets',body)
def own(name,vs,fs,parent):
    m=bpy.data.meshes.new(name+'Mesh');m.from_pydata(vs,[],fs);m.update();o=bpy.data.objects.new(name,m);col.objects.link(o);h.finish(o,name,parent,(0,0,0),'A_Satin')
    bm=bmesh.new();bm.from_mesh(o.data)
    if bm.calc_volume(signed=True)<0:bmesh.ops.reverse_faces(bm,faces=list(bm.faces));bm.to_mesh(o.data)
    assert not any(not e.is_manifold for e in bm.edges),(name,'Nonmanifold fitted solid');bm.free();return o
def tree(o,matrix):
    bpy.context.view_layer.update();o.data.calc_loop_triangles();inverse=matrix.inverted()
    return BVHTree.FromPolygons([inverse@o.matrix_world@v.co for v in o.data.vertices],[tuple(t.vertices) for t in o.data.loop_triangles],all_triangles=True)
def crossings(bvh,x,y):
    p=Vector((x,y,5));hits=[]
    for _ in range(8):
        hit=bvh.ray_cast(p,Vector((0,0,-1)),10.)
        if hit[0] is None:break
        hits.append(float(hit[0].z));p=hit[0]+Vector((0,0,-.00001))
    return hits
selected=[]
for cell in cells:
    for side in ['L','R']:
        if last_cell:
            for slot,phi in enumerate([1.05,1.55] if side=='L' else [1.55,2.1]):
                row=next(r for r in plan['candidates'] if r['cell']==cell and r['side']==side and r['phi']==phi);selected.append({**row,'seat_label':'Fore' if slot==0 else 'Aft'})
        elif batch:
            candidates=[r for r in plan['candidates'] if r['cell']==cell and r['side']==side]
            front=[r for r in candidates if r['phi']<1.1];rear=[r for r in candidates if r['phi']>2.0];assert front and rear,('Missing full front/rear footprint',cell,side)
            selected.extend([min(front,key=lambda r:abs(r['phi']-.28)),min(rear,key=lambda r:abs(r['phi']-2.1))])
        else:
            for phi in [.28,2.1]:
                row=next(r for r in plan['candidates'] if r['cell']==5 and r['side']==side and r['phi']==phi);assert row['joining_method']=='through_bolt_with_fitted_inside_backing_and_nut';selected.append(row)
seats=[]
for index,row in enumerate(selected):
    cell=row['cell'];frame=bpy.data.objects[row['frame']];film=bpy.data.objects[row['film']]
    prefix='IF12_C%02d_%s_%s_'%(cell,row['side'],row.get('seat_label','Front' if row['phi']<1.1 else 'Rear'));matrix=Matrix(row['matrix']);mount=h.empty(prefix+'Mount',root);mount.matrix_world=matrix;outline=row['outline'];bpy.context.view_layer.update()
    upper_surface=fitted.clipped_surface([frame],outline,frame=matrix,from_positive=False,normal_limit=.80,with_planes=True)
    frame_front=fitted.clipped_surface([frame],outline,frame=matrix,from_positive=True,normal_limit=.15)
    film_front=fitted.clipped_surface([film],outline,frame=matrix,from_positive=True,normal_limit=.80,with_planes=True)
    film_back=fitted.clipped_surface([film],outline,frame=matrix,from_positive=False,normal_limit=.80,with_planes=True)
    core_front=fitted.clipped_surface([core],outline,frame=matrix,from_positive=True,normal_limit=.80,with_planes=True)
    core_inner=fitted.clipped_surface([core],outline,frame=matrix,from_positive=False,normal_limit=.50,ray_from_positive=True,visible_layer=1)
    uv,uf,fit_top=laminate.between(upper_surface,film_front);lv,lf,fit_bottom=laminate.between(film_back,core_front)
    top=own(prefix+'UpperClamp',uv,uf,mount);stand=own(prefix+'OuterStand',lv,lf,mount)
    cv,cf=fitted.extruded_patch(*frame_front,top_offset=.005,bottom_offset=.0002)
    cap=own(prefix+'VisibleCap',cv,cf,mount)
    nut_plane=min(p.z for p in core_inner[0])-.008
    iv,iff=fitted.extruded_patch(*core_inner,top_offset=-.0002,bottom_z=nut_plane);inside=own(prefix+'InnerBacking',iv,iff,mount)
    bolts=[]
    for i,y in enumerate([-.010,.010]):
        ft=tree(cap,matrix);ct=tree(core,matrix)
        samples=[crossings(ft,.0062*math.cos(k*math.tau/24),y+.0062*math.sin(k*math.tau/24))[0] for k in range(24)]
        seat_z=min(samples)-.0006;hits=crossings(ct,0,y);assert len(hits)>=2;outer,inner=hits[:2];assert outer-inner>.006
        h.drill(cap,.0062,.050,mount,(0,y,seat_z+.025),solver='MANIFOLD')
        cut_top=seat_z+.015;cut_bottom=nut_plane-.010
        for o in [cap,frame,top,film,stand,core,inside]:
            h.drill(o,.00245,cut_top-cut_bottom,mount,(0,y,(cut_top+cut_bottom)/2),solver='MANIFOLD' if o in [cap,top,stand,inside] else 'EXACT')
        washer=h.sleeve(prefix+'Bolt%d_Washer'%i,.0055,.00255,.0012,mount,(0,y,seat_z+.0007),'A_Bronze')
        inside_washer=h.sleeve(prefix+'Bolt%d_InnerWasher'%i,.0055,.00255,.0012,mount,(0,y,nut_plane-.0007),'A_Bronze')
        bpy.ops.mesh.primitive_cylinder_add(vertices=6,radius=.0058,depth=.004)
        nut=h.finish(bpy.context.object,prefix+'Bolt%d_Nut'%i,mount,(0,y,nut_plane-.0035),'A_Nickel',.00025)
        h.drill(nut,.00245,.010,mount,(0,y,nut_plane-.0035))
        bottom=nut_plane-.007;head_z=seat_z+.0034
        shank=h.cylinder(prefix+'Bolt%d'%i,.0022,head_z-bottom,mount,(0,y,(head_z+bottom)/2),'A_Nickel',bevel=.0001);head=h.screw(prefix+'Bolt%d_Head'%i,mount,(0,y,head_z),.0048)
        bpy.context.view_layer.update();bpy.context.view_layer.objects.active=shank;mod=shank.modifiers.new('One-piece through bolt','BOOLEAN');mod.operation='UNION';mod.solver='EXACT';mod.object=head;bpy.ops.object.modifier_apply(modifier=mod.name);h.parts.remove(head.name);bpy.data.objects.remove(head,do_unlink=True)
        bolts.append({'mesh':shank.name,'washer':washer.name,'inner_washer':inside_washer.name,'nut':nut.name,'xy':[0,y],'frame_seat_z':seat_z,'core_outer_z':outer,'core_inner_z':inner,'nut_seat_z':nut_plane,'shaft_bottom_z':bottom,'bore_radius':.00245})
    seats.append({'cell':cell,'side':row['side'],'phi':row['phi'],'frame':mount.name,'matrix_blender':[list(r) for r in matrix],'cap':cap.name,'upper':top.name,'outer_stand':stand.name,'inner_backing':inside.name,'source_frame':frame.name,'source_film':film.name,'fit_top':fit_top,'fit_bottom':fit_bottom,'bolts':bolts})
    print('THROUGH_SOCKET_BUILT',index+1,flush=True)
removed=[]
for name in ['IN1_CellLand_%02d_%s'%(cell,side) for cell in cells for side in ['L','R']]:
    o=bpy.data.objects[name];removed.append({'name':name,'fingerprint':fingerprint(o),'reason':'Both actual front/rear pieces now receive paired frame-film-core through clamps, fitted inner backing and nuts. Border capture remains incomplete.'});bpy.data.objects.remove(o,do_unlink=True)
cleanup=[]
for o in edited+[bpy.data.objects[n] for n in h.parts]:
    bm=bmesh.new();bm.from_mesh(o.data);bmesh.ops.remove_doubles(bm,verts=list(bm.verts),dist=1e-6);bmesh.ops.dissolve_degenerate(bm,edges=list(bm.edges),dist=3e-6)
    flaps=[f for f in bm.faces if f.calc_area()<1e-10 and any(len(e.link_faces)>2 for e in f.edges)]
    if flaps:bmesh.ops.delete(bm,geom=flaps,context='FACES_ONLY')
    # Exact Boolean can leave an opposed duplicate triangle pair attached to
    # the bore edge. Both faces share the same vertices and enclose no volume.
    # Remove only those proved zero-thickness spurs, retaining the two actual
    # wall faces on their four-face edge.
    bm.normal_update();bm.verts.ensure_lookup_table();bm.verts.index_update();groups={}
    for f in bm.faces:groups.setdefault(tuple(sorted(v.index for v in f.verts)),[]).append(f)
    opposed=[]
    for group in groups.values():
        if len(group)==2 and group[0].normal.dot(group[1].normal)<-.99999 and any(len(e.link_faces)==4 for e in group[0].edges):opposed.extend(group)
    if opposed:
        before=bm.calc_volume(signed=True);bmesh.ops.delete(bm,geom=opposed,context='FACES_ONLY');assert abs(bm.calc_volume(signed=True)-before)<1e-9
        loose=[e for e in bm.edges if not e.link_faces]
        if loose:bmesh.ops.delete(bm,geom=loose,context='EDGES')
        loose_vertices=[v for v in bm.verts if not v.link_edges]
        if loose_vertices:bmesh.ops.delete(bm,geom=loose_vertices,context='VERTS')
    residue_report=residue.repair(bm)
    bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces))
    if bm.calc_volume(signed=True)<0:bmesh.ops.reverse_faces(bm,faces=list(bm.faces))
    cleanup.append({'name':o.name,'nonmanifold':sum(not e.is_manifold for e in bm.edges),'volume':bm.calc_volume(signed=True),'removed_opposed_zero_volume_faces':len(opposed),**residue_report})
    bm.to_mesh(o.data);bm.free()
bpy.context.view_layer.update();changed=[name for name,value in protected.items() if fingerprint(bpy.data.objects[name])!=value];assert not changed,changed
bpy.ops.wm.save_as_mainfile(filepath=str(TARGET),compress=True);bpy.ops.object.select_all(action='DESELECT')
for o in [body,*body.children_recursive]:o.select_set(True)
bpy.context.view_layer.objects.active=body;bpy.ops.export_scene.gltf(filepath=str(COMPONENT),export_format='GLB',use_selection=True,export_animations=False,export_morph=False,export_extras=True)
result={**seed,'source':str(TARGET.relative_to(ROOT)),'source_sha256':sha(TARGET),'component':str(COMPONENT.relative_to(ROOT)),'component_sha256':sha(COMPONENT),'parent_source_sha256':seed['source_sha256'],'status':'chamber05_through_socket_candidate_checks_pending','front_sockets':{'seats':seats,'new_meshes':list(h.parts),'modified_meshes':[core.name,frame.name,film.name],'removed_unfitted_webs':removed,'cleanup':cleanup},'review_scope':'R11 mouth/shape/hub and six chamber assemblies preserved. Chamber05 front and rear pieces now receive four through-bolted clamp sockets with actual inside backings and nuts. Contacts, border capture, remaining throat-side chambers, base load path, upper mechanisms, full music/native/art acceptance pending.'}
result['front_sockets']['modified_meshes']=[o.name for o in edited];result['socket_parent_topology']=str((seed_path.parent/'topology_check.json').relative_to(ROOT))
if batch or last_cell:
    result['front_sockets']['seats']=seed['front_sockets']['seats']+seats
    result['front_sockets']['new_meshes']=seed['front_sockets']['new_meshes']+list(h.parts)
    result['front_sockets']['removed_unfitted_webs']=seed['front_sockets']['removed_unfitted_webs']+removed
    result['status']='five_throat_chambers_socket_candidate_checks_pending';result['review_scope']='R12 chamber05 and earlier six chamber/hub/mouth/base assets preserved. Adds real fitted through-bolt sockets to chambers06/07/08/09. Scoped checks, chamber04, border capture, core/base support, upper-cover mechanisms, final materials/music/native still pending.'
result['front_sockets']['audit_socket_meshes']=list(h.parts);result['front_sockets']['newly_seated_cells']=cells
if last_cell:
    result['construction_cleanup']=construction_cleanup;result['status']='twelve_chambers_have_clamp_candidate_checks_pending';result['review_scope']='Preserves R16b and previous eleven chamber clamps. Adds four real through-bolted seats to chamber04 at independently fitted positions, replacing its two old interfering webs and removing only the measured tiny cutting remnant. Full contacts, end finish, core/base route, upper mechanisms, music/material/native and art acceptance remain pending.'
(OUT/'build.json').write_text(json.dumps(result,indent=2)+'\n');(OUT/'protected_geometry.json').write_text(json.dumps({'source_sha256':result['source_sha256'],'passed':not changed,'count':len(protected),'changed':changed,'allowed_changes':sorted(allowed)},indent=2)+'\n')
print('FRONT_SOCKETS_BUILT',result['source_sha256'],flush=True)
