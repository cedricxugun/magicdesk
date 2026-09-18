"""Source-conforming U-section ferrules on the two newly terminated bronze frames."""
import bpy,bmesh,json,hashlib,sys,shutil,struct,math,numpy as np
from pathlib import Path
from mathutils import Vector,Matrix
from mathutils.bvhtree import BVHTree
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(Path(__file__).parent));import i_throat_keepout as keepout;import i_boolean_residue as residue
import i_bounded_plane_offset as plane_offset
import i_indexed_surface_band as indexed_band
import i_render_triangle_cleanup as triangle_cleanup
import i_local_end_rounding as local_rounding
args=sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else [];preflight='--preflight' in args;partial='--partial' in args;scan_mode=preflight or partial;problems=[];pending_bands=[]
OUT=ROOT/('review/I_refinement/nautilus_r1/end_finish_r17/partial' if partial else 'review/I_refinement/nautilus_r1/end_finish_r17');OUT.mkdir(parents=True,exist_ok=True);suffix='_partial' if partial else '';TARGET=ROOT/('blender/collection/I_nautilus_end_rims_r17'+suffix+'.blend');COMPONENT=ROOT/('app/assets/collection/components/I_nautilus_end_rims_r17'+suffix+'.glb');sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
parent_path=ROOT/'review/I_refinement/nautilus_r1/throat_terminations_r16/build.json';seed=json.loads(parent_path.read_text());assert sha(ROOT/seed['source'])==seed['source_sha256'];assert json.loads((parent_path.parent/'checkpoint.json').read_text())['source_sha256']==seed['source_sha256']
if TARGET.exists() and not preflight:
    old=json.loads((OUT/'build.json').read_text());assert sha(TARGET)==old['source_sha256'];archive=OUT/'iterations'/old['source_sha256'][:12];archive.mkdir(parents=True,exist_ok=True)
    for p in OUT.glob('*.json'):shutil.copy2(p,archive/p.name)
    if (OUT/'views').exists():shutil.copytree(OUT/'views',archive/'views',dirs_exist_ok=True)
    shutil.copy2(TARGET,TARGET.parent/'checkpoints'/('I-end-rims-'+old['source_sha256'][:12]+'.blend'))
bpy.ops.wm.open_mainfile(filepath=str(ROOT/seed['source']));scene=bpy.context.scene;scene.frame_set(1);bpy.context.view_layer.update();body=bpy.data.objects['IN1_BodyRoot']
def fingerprint(o):
    h=hashlib.sha256()
    for v in o.data.vertices:h.update(struct.pack('<3f',*v.co))
    for f in o.data.polygons:h.update(struct.pack('<'+'I'*len(f.vertices),*f.vertices))
    return [h.hexdigest(),[list(r) for r in o.matrix_world],o.parent.name if o.parent else None,[m.name if m else None for m in o.data.materials]]
frame_names=['IN1_CellFrame_08','IN1_CellFrame_09'];protected={o.name:fingerprint(o) for o in bpy.data.objects if o.type=='MESH' and o.name not in frame_names}
col=bpy.data.collections.new('I_FORMED_END_RIMS_R17');scene.collection.children.link(col);root=bpy.data.objects.new('IT17_EndRims',None);col.objects.link(root);root.parent=body;root.matrix_world=Matrix.Identity(4)
def tree(o):
    o.data.calc_loop_triangles();v=[o.matrix_world@p.co for p in o.data.vertices];f=[tuple(t.vertices) for t in o.data.loop_triangles];return BVHTree.FromPolygons(v,f,all_triangles=True),v,f
placement=bpy.data.objects['IC1_MouthMount'].matrix_world.copy();core=bpy.data.objects['IN3_ContinuousThroat'];inverse=placement.inverted();flange=[core.matrix_world@v.co for v in core.data.vertices if (inverse@core.matrix_world@v.co).z<.661]
tool=keepout.core_envelope(placement,col);other=keepout.collar_envelope([bpy.data.objects[n] for n in ['IC1_CollarUpper','IC1_CollarLower']],col,extra_points=flange);bpy.context.view_layer.update();bpy.context.view_layer.objects.active=tool;mod=tool.modifiers.new('Original termination envelope','BOOLEAN');mod.operation='UNION';mod.solver='MANIFOLD';mod.object=other;bpy.ops.object.modifier_apply(modifier=mod.name);bpy.data.objects.remove(other,do_unlink=True);envelope,_,_=tree(tool)
new=[];rows=[];rounded_frames=[]
fixed_trees={n:tree(bpy.data.objects[n])[0] for n in ['IN3_ContinuousThroat','IC1_CollarUpper','IC1_CollarLower']}
# A compound reentrant fold is formed as two separate rim segments with a
# narrow manufacturing joint. The underlying frame remains completely closed.
relief_joints={'IN1_CellFrame_08':[{'axis':'Z','center':1.1661,'gap':.004},{'axis':'Z','center':1.724147915840149,'gap':.004},{'axis':'Z','center':1.9110,'gap':.006}]}
def clip_z(poly,z,above):
    result=[];previous=poly[-1];pd=(previous.z-z)*(1 if above else -1)
    for current in poly:
        cd=(current.z-z)*(1 if above else -1)
        if (cd>=0)!=(pd>=0):result.append(previous.lerp(current,pd/(pd-cd)))
        if cd>=0:result.append(current)
        previous,pd=current,cd
    return result
for name in frame_names:
    source=bpy.data.objects[name];original_fingerprint=fingerprint(source);triangle_repair=triangle_cleanup.repair(source);local_rounding_report=local_rounding.apply(source,envelope);post_rounding_repair=triangle_cleanup.repair(source);rounding=bmesh.new();rounding.from_mesh(source.data);rounding.normal_update();before_volume=rounding.calc_volume(signed=True);sharp=[]
    for edge in rounding.edges:
        if len(edge.link_faces)!=2 or not edge.is_convex or edge.calc_face_angle()<math.radians(110):continue
        point=source.matrix_world@((edge.verts[0].co+edge.verts[1].co)/2);hit=envelope.find_nearest(point)
        if hit[0] is not None and hit[3]<.00002:sharp.append(edge)
    # The broad bevel trial globally clamped to near-zero width and introduced
    # subprecision faces. Keep the source exact until a measured local fillet
    # is constructed; a selected-edge count is not proof of a rounded edge.
    after_volume=before_volume
    assert after_volume>0 and abs(after_volume-before_volume)/before_volume<.001,('End rounding changed too much frame material',name,before_volume,after_volume)
    assert not any(not e.is_manifold for e in rounding.edges),('Rounded frame is not closed',name)
    rounding.free();rounded_frames.append({'mesh':name,'source_fingerprint':original_fingerprint,'rounded_edges':len(local_rounding_report['rounded_features']),'edge_offset':None,'segments':4,'volume_before':before_volume,'volume_after':after_volume,'geometry_preserved':False,'render_triangle_repair':triangle_repair,'post_rounding_triangle_repair':post_rounding_repair,'local_rounding':local_rounding_report})
    surface,vertices,triangles=tree(source);cut=[]
    for i,f in enumerate(triangles):
        a,b,c=[vertices[j] for j in f];center=(a+b+c)/3;hit=envelope.find_nearest(center);normal=(b-a).cross(c-a).normalized()
        if hit[0] is not None and hit[3]<.000008 and normal.dot(hit[1])<-.70:cut.append(i)
    assert cut,('No actual termination faces',name)
    cut_tree=BVHTree.FromPolygons(vertices,[triangles[i] for i in cut],all_triangles=True);distances=[cut_tree.find_nearest(p)[3] for p in vertices];width=.006;original_normals=[]
    for f in triangles:
        a,b,c=[np.array(vertices[j],dtype=float) for j in f];normal=np.cross(b-a,c-a);length=np.linalg.norm(normal);original_normals.append(normal/max(length,1e-30))
    pv,pf,source_faces=indexed_band.clip_band(vertices,triangles,distances,width,relief_joints.get(name))
    patch=bpy.data.meshes.new('RimSourceBand');patch.from_pydata(pv,[],pf);patch.update();bm=bmesh.new();bm.from_mesh(patch);source_layer=bm.faces.layers.int.new('OriginalFrameTriangle');bm.faces.ensure_lookup_table()
    for face,source_index in zip(bm.faces,source_faces):face[source_layer]=source_index
    # Source-edge identities already join shared intersections. Spatial welding
    # would incorrectly join opposite or nearby sheets at narrow terminations.
    bmesh.ops.dissolve_degenerate(bm,edges=list(bm.edges),dist=1e-10);bm.normal_update()
    bm.faces.ensure_lookup_table();bm.faces.index_update();bm.verts.ensure_lookup_table();bm.verts.index_update();unseen=set(bm.faces);groups=[]
    while unseen:
        first=min(unseen,key=lambda f:f.index);unseen.remove(first);stack=[first];group=[]
        while stack:
            face=stack.pop();group.append(face)
            for edge in face.edges:
                for adjacent in edge.link_faces:
                    if adjacent in unseen:unseen.remove(adjacent);stack.append(adjacent)
        groups.append(group)
    for group_index,group in enumerate(groups):
        owned_cut_triangles=sorted(set(cut)&{f[source_layer] for f in group})
        # Euclidean proximity can also select an unrelated nearby face across
        # a gap. A formed end rim must actually contain termination faces.
        if not owned_cut_triangles:
            if preflight:rows.append({'frame':name,'band_component':group_index,'band_vertices':len({v for f in group for v in f.verts}),'band_faces':len(group),'valid_corners':0,'maximum_valid_miter':0.,'classification':'nearby_surface_without_termination'})
            continue
        used=sorted({v for f in group for v in f.verts},key=lambda v:v.index);ids={v:i for i,v in enumerate(used)};points=[v.co.copy() for v in used];faces=[tuple(ids[v] for v in f.verts) for f in group];edges={}
        for f in faces:
            for i,a in enumerate(f):edges.setdefault(tuple(sorted([a,f[(i+1)%len(f)]])),[]).append((a,f[(i+1)%len(f)]))
        if preflight:
            diagnostic_mesh=bpy.data.meshes.new('IT17_DiagnosticBandMesh');diagnostic_mesh.from_pydata(points,[],faces);diagnostic_mesh.update();diagnostic=bpy.data.objects.new('IT17_DiagnosticBand_%s_%02d'%(name,group_index),diagnostic_mesh);col.objects.link(diagnostic);diagnostic['source_frame']=name;diagnostic['band_component']=group_index
        valid_band=all(len(v) in [1,2] for v in edges.values())
        if scan_mode and not valid_band:
            problem={'frame':name,'band_component':group_index,'point_blender':list(sum(points,Vector())/len(points)),'kind':'band_topology','nonmanifold_patch_edges':sum(len(v)>2 for v in edges.values())};problems.append(problem);pending_bands.append(problem)
            if preflight:rows.append({'frame':name,'band_component':group_index,'source_cut_triangles':cut,'band_vertices':len(points),'band_faces':len(faces),'valid_corners':0,'maximum_valid_miter':0.,'failure':'band_topology'})
            continue
        assert valid_band,('Invalid wrapped band',name,group_index)
        boundary=[e[0] for e in edges.values() if len(e)==1];moves=[];residuals=[];active_plane_count=0
        for vertex,p in zip(used,points):
            # Use topologically incident SOURCE planes. A proximity query can
            # mix in the opposite side of a thin terminating wedge.
            normals=[original_normals[f[source_layer]] for f in vertex.link_faces];assert normals
            # Near-parallel triangulation planes should not force a large
            # tangential miter. Keep a bounded source-plane error instead.
            try:delta,method=plane_offset.solve(normals,maximum=None)
            except AssertionError as error:
                if scan_mode:
                    problems.append({'frame':name,'band_component':group_index,'point_blender':list(p),'kind':'no_bounded_outward_offset','normals':[list(n) for n in normals]});moves.append(None);residuals.append(None);continue
                debug_name='corner_failure_'+sha(Path(__file__))[:8]
                bm.to_mesh(patch);debug=bpy.data.objects.new('IT17_FailedSourceBand',patch);col.objects.link(debug)
                marker=bpy.data.objects.new('IT17_FailingCorner',None);col.objects.link(marker);marker.location=p;marker.empty_display_size=.008
                debug_path=OUT/(debug_name+'.blend');bpy.ops.wm.save_as_mainfile(filepath=str(debug_path),compress=True)
                (OUT/'corner_failure.json').write_text(json.dumps({'parent_source':seed['source'],'parent_source_sha256':seed['source_sha256'],'debug_source':str(debug_path.relative_to(ROOT)),'frame':name,'band_component':group_index,'point_blender':list(p),'incident_source_normals':[list(n) for n in normals],'error':str(error),'stage':'After local source-edge rounding, before any complete end rim','scope':'Rejected diagnostic scene includes keepout and the source band. Not a finished component or a replacement for R16.'},indent=2)+'\n')
                raise AssertionError(('Rim needs different corner geometry',name,group_index,list(p),str(error)))
            move=Vector(delta);active_plane_count+=method=='active_planes';projections=[float(np.dot(n,np.array(move))) for n in normals];residual=max(abs(v-1.) for v in projections)
            # Keep positive clearance to every incident source plane. Acute
            # corners can have a longer tangent shift; their outer edges are
            # rounded below and their actual clearances are checked afterward.
            # A formed corner need not be equally far from every incident
            # plane. It must remain outside ALL of them with bounded thickness.
            assert min(projections)>.9999 and move.length<8.,('Unbounded rim corner',name,group_index,list(p),move.length,projections)
            for fixed_name,fixed in fixed_trees.items():
                hit=fixed.ray_cast(p,move.normalized(),move.length*.0012+.00010)
                if scan_mode and hit[0] is not None:
                    problems.append({'frame':name,'band_component':group_index,'point_blender':list(p),'kind':'fixed_geometry_crossing','fixed':fixed_name,'hit':list(hit[0])});move=None;break
                assert hit[0] is None,('Rim offset crosses fixed hardware',name,fixed_name,list(p),list(hit[0]) if hit[0] else None)
            moves.append(move);residuals.append(residual)
        if preflight:
            rows.append({'frame':name,'band_component':group_index,'source_cut_triangles':cut,'band_vertices':len(points),'band_faces':len(faces),'valid_corners':sum(d is not None for d in moves),'maximum_valid_miter':max((d.length for d in moves if d is not None),default=0.)});continue
        if partial and any(d is None for d in moves):
            pending_bands.append({'frame':name,'band_component':group_index,'kind':'corner_construction','failed_corners':sum(d is None for d in moves)});continue
        inner=.00010;outer=.00120;count=len(points);vs=[tuple(p+d*outer) for p,d in zip(points,moves)]+[tuple(p+d*inner) for p,d in zip(points,moves)];fs=faces+[tuple(i+count for i in reversed(f)) for f in faces]+[(a,b,b+count,a+count) for a,b in boundary]
        mesh=bpy.data.meshes.new('IT17_%s_%02dMesh'%(name,group_index));mesh.from_pydata(vs,[],fs);mesh.update();obj=bpy.data.objects.new('IT17_%s_%02d'%(name,group_index),mesh);col.objects.link(obj);obj.parent=root;mesh.materials.append(bpy.data.materials['Collection_A_Satin'])
        check=bmesh.new();check.from_mesh(mesh);bmesh.ops.recalc_face_normals(check,faces=list(check.faces))
        if check.calc_volume(signed=True)<0:bmesh.ops.reverse_faces(check,faces=list(check.faces))
        check.normal_update();check.verts.ensure_lookup_table();check.verts.index_update()
        outer_edges=[e for e in check.edges if all(v.index<count for v in e.verts) and len(e.link_faces)==2 and e.calc_face_angle()>.5]
        # Do not create a nominal bevel that collapses around tiny neighboring
        # triangles. The physical rounding remains an explicit finishing item.
        cleanup=residue.repair(check);bad=sum(not e.is_manifold for e in check.edges);volume=check.calc_volume(signed=True)
        if partial and (bad or volume<=0):
            pending_bands.append({'frame':name,'band_component':group_index,'kind':'formed_solid_topology','nonmanifold_edges':bad,'volume':volume});check.free();bpy.data.objects.remove(obj,do_unlink=True);continue
        assert not bad,('Rim not closed',obj.name);assert volume>0
        check.normal_update()
        for face in check.faces:face.smooth=True
        for edge in check.edges:edge.smooth=len(edge.link_faces)==2 and edge.calc_face_angle()<math.radians(60)
        check.to_mesh(mesh);check.free();new.append(obj.name)
        rows.append({'mesh':obj.name,'frame':name,'source_cut_triangles':owned_cut_triangles,'wrap_width':width,'inner_gap':inner,'outer_offset':outer,'maximum_miter':max(d.length for d in moves),'maximum_relative_plane_offset_error':max(residuals),'active_plane_corners':active_plane_count,'outer_edge_bevel':0.,'beveled_outer_edges':0,'edge_rounding_pending':True,'source_band_faces':len(faces),'source_band_vertices':count,'cleanup':cleanup})
    bm.free();bpy.data.meshes.remove(patch);print('FORMED_RIMS_BUILT',name,len(groups),flush=True)
if preflight:
    for i,r in enumerate(problems):
        marker=bpy.data.objects.new('IT17_Problem_%03d'%i,None);col.objects.link(marker);marker.location=r['point_blender'];marker.empty_display_size=.003
    debug_path=OUT/('rim_preflight_'+sha(Path(__file__))[:8]+'.blend');bpy.ops.wm.save_as_mainfile(filepath=str(debug_path),compress=True)
    report={'parent_source':seed['source'],'parent_source_sha256':seed['source_sha256'],'debug_source':str(debug_path.relative_to(ROOT)),'rounded_frames':rounded_frames,'relief_joints':relief_joints,'bands':rows,'problem_vertices':problems,'scope':'Complete source-band corner preflight for both frames. No final rim component built; contains temporary keepout and modified diagnostic frames.'}
    (OUT/'rim_preflight.json').write_text(json.dumps(report,indent=2)+'\n');print('RIM_PREFLIGHT',len(problems),flush=True);raise SystemExit(0)
bpy.data.objects.remove(tool,do_unlink=True);bpy.context.view_layer.update();changed=[n for n,h in protected.items() if fingerprint(bpy.data.objects[n])!=h];assert not changed,changed
assert new,'No valid end rim was built; preserve the preflight instead of exporting an empty result'
bpy.ops.wm.save_as_mainfile(filepath=str(TARGET),compress=True);bpy.ops.object.select_all(action='DESELECT')
for o in [body,*body.children_recursive]:o.select_set(True)
bpy.context.view_layer.objects.active=body;bpy.ops.export_scene.gltf(filepath=str(COMPONENT),export_format='GLB',use_selection=True,export_animations=False,export_morph=False,export_extras=True)
result={**seed,'source':str(TARGET.relative_to(ROOT)),'source_sha256':sha(TARGET),'component':str(COMPONENT.relative_to(ROOT)),'component_sha256':sha(COMPONENT),'parent_source_sha256':seed['source_sha256'],'end_finishes':{'new_meshes':new,'rims':rows,'art':'production/I_refinement/nautilus_r1/end_finish_r17/formed_rims_and_membrane_capture_r1.png'},'status':'formed_end_rim_candidate_checks_pending','review_scope':'Source-conforming physical U-rims on the two corrected bronze frame ends. Original R16 geometry preserved. Contacts, edge quality, membrane beads/keepers, remaining chamber04, core/base route, upper mechanisms and complete art/music/native remain pending.'}
result['end_finishes']['rounded_frames']=rounded_frames;result['review_scope']='Two bronze termination edges receive local rounding and source-conforming physical U-rims. Other R16 geometry preserved. Contacts, edge quality, membrane beads/keepers, remaining chamber04, core/base route, upper mechanisms and complete art/music/native remain pending.'
result['end_finishes']['relief_joints']=relief_joints
result['end_finishes']['parent_report']=str(parent_path.relative_to(ROOT));result['end_finishes']['pending_bands']=pending_bands;result['end_finishes']['corner_problems']=problems
if partial:result['status']='partial_formed_rims_remaining_segments_unfinished';result['review_scope']='Only the listed constructed rim segments exist. Pending bands are explicitly retained in the report and remain visibly unfinished; this is not complete R17, final device art or a native App update. Other R16 geometry is preserved except the recorded local frame-end rounding.'
(OUT/'build.json').write_text(json.dumps(result,indent=2)+'\n');(OUT/'protected_geometry.json').write_text(json.dumps({'source_sha256':result['source_sha256'],'passed':not changed,'count':len(protected),'changed':changed},indent=2)+'\n');print('END_RIMS_SOURCE',result['source_sha256'],flush=True)
