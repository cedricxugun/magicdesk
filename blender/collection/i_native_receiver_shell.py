"""Fixed source triangles, explicit shell provenance and authored thickness."""
import bpy,math
from collections import Counter
from mathutils.kdtree import KDTree
from mathutils.bvhtree import BVHTree
from mathutils import Vector

def rebuild(cowl,source,reinforcement=None):
    matrix=cowl.matrix_world.copy();materials=list(cowl.data.materials);source.calc_loop_triangles();values=[a.value for a in source.attributes['formed_wall_fraction'].data]
    selected={p.index for p in source.polygons if max(values[i] for i in p.vertices)<.001};triangles=[t for t in source.loop_triangles if t.polygon_index in selected];used=sorted({i for t in triangles for i in t.vertices});index={v:i for i,v in enumerate(used)}
    kd=KDTree(len(cowl.data.vertices))
    for v in cowl.data.vertices:kd.insert(v.co,v.index)
    kd.balance();match=max(kd.find(source.vertices[i].co)[2] for i in used);assert match<.000002
    vertices=[tuple(source.vertices[i].co) for i in used];faces=[tuple(index[i] for i in t.vertices) for t in triangles];data=bpy.data.meshes.new(cowl.name+'_ConsistentWallMesh');data.from_pydata(vertices,[],faces);data.update()
    for material in materials+materials+[materials[0]]:data.materials.append(material)
    normal_reference={}
    for face,t in zip(data.polygons,triangles):
        old=source.polygons[t.polygon_index];face.material_index=old.material_index;face.use_smooth=old.use_smooth
        normal_reference[tuple(sorted(face.vertices))]={index[old_index]:source.corner_normals[loop].vector.copy() for old_index,loop in zip(t.vertices,t.loops)}
    source_index=data.attributes.new('IR6_source_vertex','INT','POINT')
    for v in data.vertices:source_index.data[v.index].value=v.index
    cowl.data=data;data.calc_loop_triangles();reference_points=[matrix@v.co for v in data.vertices];reference_faces=[tuple(t.vertices) for t in data.loop_triangles];reference=BVHTree.FromPolygons(reference_points,reference_faces,all_triangles=True)
    bpy.context.view_layer.objects.active=cowl;mod=cowl.modifiers.new('Consistent inward formed wall','SOLIDIFY');mod.solidify_mode='NON_MANIFOLD';mod.nonmanifold_thickness_mode='CONSTRAINTS';mod.nonmanifold_boundary_mode='NONE';mod.nonmanifold_merge_threshold=.0000001;mod.thickness=.0085;mod.offset=-1.;mod.use_rim=True;mod.material_offset=len(materials);mod.material_offset_rim=2*len(materials)
    if reinforcement:
        group=cowl.vertex_groups.new(name='AuthoredHeelThickness');mod.vertex_group=group.name;mod.thickness=.020;group.add(list(range(len(vertices))),.425,'REPLACE');center=Vector(reinforcement['center']);radius=reinforcement['radius']
        for i,p in enumerate(reference_points):
            weight=.425+.575*math.exp(-((p-center).length/radius)**4)
            if weight>.425001:group.add([i],weight,'REPLACE')
    actual_settings={name:getattr(mod,name) for name in ['solidify_mode','nonmanifold_thickness_mode','nonmanifold_boundary_mode','nonmanifold_merge_threshold','thickness','offset','vertex_group']};bpy.ops.object.modifier_apply(modifier=mod.name);cowl.data.update()
    ids=[a.value for a in cowl.data.attributes['IR6_source_vertex'].data];copies={i:[] for i in range(len(vertices))}
    for i,old in enumerate(ids):copies[old].append(i)
    assert all(len(v)==2 for v in copies.values()),(cowl.name,'Source ancestry lost')
    adjacency={i:set() for i in range(len(ids))}
    for face in cowl.data.polygons:
        if len({ids[i] for i in face.vertices})!=len(face.vertices):continue
        for k,a in enumerate(face.vertices):b=face.vertices[(k+1)%len(face.vertices)];adjacency[a].add(b);adjacency[b].add(a)
    unseen=set(adjacency);sheets=[]
    while unseen:
        stack=[unseen.pop()];sheet=[]
        while stack:
            i=stack.pop();sheet.append(i)
            for j in adjacency[i]:
                if j in unseen:unseen.remove(j);stack.append(j)
        sheets.append(sheet)
    pairs={}
    for sheet in sheets:pairs.setdefault(tuple(sorted(ids[i] for i in sheet)),[]).append(sheet)
    outer=set()
    for pair in pairs.values():
        assert len(pair)==2,(cowl.name,'Unpaired sheet')
        distance=lambda sheet:sum(((matrix@cowl.data.vertices[i].co)-reference_points[ids[i]]).length_squared for i in sheet)
        outer.update(min(pair,key=distance))
    assert len(outer)==len(vertices)
    restored=max(((matrix@cowl.data.vertices[i].co)-reference_points[ids[i]]).length for i in outer)
    for i in outer:cowl.data.vertices[i].co=vertices[ids[i]]
    cowl.data.update();side=cowl.data.attributes.new('IR6_wall_side','INT','FACE');inside=set()
    for face in cowl.data.polygons:
        flags=[i in outer for i in face.vertices];role=0 if all(flags) else 1 if not any(flags) else 2;side.data[face.index].value=role
        if role==1:inside.update(face.vertices)
    wall=cowl.data.attributes.new('formed_wall_fraction','FLOAT','POINT');region=cowl.data.attributes.new('IN3_receiver_region','FLOAT','POINT')
    for v in cowl.data.vertices:wall.data[v.index].value=0. if v.index in outer else 1. if v.index in inside else .5;region.data[v.index].value=float(v.index in inside)
    cowl.data.calc_loop_triangles();normals=[n.vector.copy() for n in cowl.data.corner_normals];restored_normals=0
    for face in cowl.data.polygons:
        if side.data[face.index].value!=0:continue
        key=tuple(sorted(ids[i] for i in face.vertices));assert key in normal_reference,(cowl.name,'Source triangle changed')
        for loop in face.loop_indices:normals[loop]=normal_reference[key][ids[cowl.data.loops[loop].vertex_index]];restored_normals+=1
    cowl.data.normals_split_custom_set(normals);cowl.data.update();cowl.data.calc_loop_triangles()
    points=[matrix@v.co for v in cowl.data.vertices];outer_faces=[tuple(t.vertices) for t in cowl.data.loop_triangles if side.data[t.polygon_index].value==0];current=BVHTree.FromPolygons(points,outer_faces,all_triangles=True)
    def compare(vs,fs,other):
        error=0.;area=0.
        for f in fs:
            a,b,c=[vs[i] for i in f];area+=(b-a).cross(c-a).length/2.
            for p in [a,b,c,(a+b+c)/3.,(a+b)/2.,(b+c)/2.,(c+a)/2.]:error=max(error,other.find_nearest(p)[3])
        return error,area
    a,area0=compare(reference_points,reference_faces,current);b,area1=compare(points,outer_faces,reference)
    canonical=lambda f:min(tuple(f[i:]+f[:i]) for i in range(len(f)))
    expected=Counter(canonical(list(f)) for f in reference_faces)
    actual=Counter(canonical([ids[i] for i in f]) for f in outer_faces)
    maximum_vertex_error=max((cowl.data.vertices[i].co-Vector(vertices[ids[i]])).length for i in outer)
    assert expected==actual and maximum_vertex_error==0.,(cowl.name,'Original triangle identity changed')
    assert cowl.matrix_world==matrix
    return {'mesh':cowl.name,'actual_settings':actual_settings,'reinforcement':reinforcement,'source_match_maximum':match,'original_side_restoration_maximum':restored,'source_triangles':len(reference_faces),'triangle_identity_preserved':expected==actual,'maximum_exterior_vertex_error':maximum_vertex_error,'restored_outer_corner_normals':restored_normals,'sheet_sizes':[len(s) for s in sheets],'old_to_new_bvh_diagnostic':a,'new_to_old_bvh_diagnostic':b,'area_ratio':area1/area0,'scope':'Exact source triangle multiplicity/winding and vertex coordinates retained. Outer corner normals transferred; inner/rim wall regenerated. BVH diagnostics may be noisy on skinny faces; actual wall and joint clearance require independent checks.'}
