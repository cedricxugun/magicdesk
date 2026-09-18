"""Relieve only the port-liner underside along its actual withdrawal path."""
import bpy,bmesh,json,hashlib,array
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
ROOT=Path(__file__).resolve().parents[2];OUT=ROOT/'review/I_refinement/nautilus_r1/cradle_release_r65/port_escape';OUT.mkdir(parents=True,exist_ok=True)
s=json.loads((ROOT/'review/I_refinement/nautilus_r1/curved_returns_r61/build.json').read_text());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();assert sha(ROOT/s['source'])==s['source_sha256'];bpy.ops.wm.open_mainfile(filepath=str(ROOT/s['source']));bpy.context.scene.frame_set(1);bpy.context.view_layer.update()
liner=bpy.data.objects['IS18_Leg01_PortLiner'];skin=bpy.data.objects['IN1_PorcelainPanel_02'];frame=bpy.data.objects['IS18_Leg01_PortFrame'];axis=frame.matrix_world.to_3x3().col[2].normalized()
def fp(o):
    m=o.data;m.calc_loop_triangles();h=hashlib.sha256()
    for c,p,w,k in [(m.vertices,'co',3,'f'),(m.loop_triangles,'vertices',3,'I'),(m.corner_normals,'vector',3,'f')]:
        a=array.array(k,[0])*(len(c)*w);c.foreach_get(p,a);h.update(a.tobytes())
    for uv in m.uv_layers:
        a=array.array('f',[0])*(len(uv.data)*2);uv.data.foreach_get('uv',a);h.update(a.tobytes())
    if m.shape_keys:
        for key in m.shape_keys.key_blocks:
            a=array.array('f',[0])*(len(key.data)*3);key.data.foreach_get('co',a);h.update(key.name.encode());h.update(a.tobytes())
    return [h.hexdigest(),[list(r)for r in o.matrix_world],[m.name if m else None for m in o.data.materials],[f.material_index for f in o.data.polygons]]
protected={o.name:fp(o)for o in bpy.data.objects if o.type=='MESH'and o!=liner}
def geometry(o):
    m=o.data;m.calc_loop_triangles();v=[o.matrix_world@x.co for x in m.vertices];f=[tuple(t.vertices)for t in m.loop_triangles];return BVHTree.FromPolygons(v,f,all_triangles=True),v,f
def topology(o):
    bm=bmesh.new();bm.from_mesh(o.data);assert all(e.is_manifold for e in bm.edges)and all(v.is_manifold for v in bm.verts);volume=bm.calc_volume(signed=True);todo=set(bm.verts);components=0
    while todo:
        components+=1;pending=[todo.pop()]
        while pending:
            for e in pending.pop().link_edges:
                for v in e.verts:
                    if v in todo:todo.remove(v);pending.append(v)
    bm.free();return volume,components
before_volume,before_components=topology(liner);before_tree,before_v,before_f=geometry(liner);samples=[]
before_hits=[(a,b)for a,b in before_tree.overlap(before_tree)if a<b and not set(before_f[a])&set(before_f[b])]
(OUT/'baseline_self.json').write_text(json.dumps({'pairs':before_hits,'triangles':[[[list(before_v[k])for k in before_f[a]],[list(before_v[k])for k in before_f[b]]]for a,b in before_hits]},indent=2)+'\n')
import math
for radius in [.0345,.0365,.039,.0405]:
    for i in range(96):
        angle=i*math.tau/96;origin=frame.matrix_world@Vector((radius*math.cos(angle),radius*math.sin(angle),.4));hit=before_tree.ray_cast(origin,-axis,.5)[0]
        if hit is not None:samples.append((origin,hit))
def boolean(target,tool,operation):
    bpy.context.view_layer.update();bpy.context.view_layer.objects.active=target;mod=target.modifiers.new('Measured withdrawal clearance','BOOLEAN');mod.operation=operation;mod.solver='MANIFOLD';mod.object=tool;bpy.ops.object.modifier_apply(modifier=mod.name)
# Crop a closed local source-skin tool to avoid unrelated geometry in Booleans.
tool=skin.copy();tool.data=skin.data.copy();liner.users_collection[0].objects.link(tool);tool.name='R65_LocalSkinTool'
bpy.ops.mesh.primitive_cube_add(size=1);box=bpy.context.object;box.matrix_world=frame.matrix_world;box.scale=Vector((.10,.10,.30));box.location=frame.matrix_world@Vector((0,0,.15));bpy.context.view_layer.update();boolean(tool,box,'INTERSECT');bpy.data.objects.remove(box,do_unlink=True)
clearance=.00015
original_tool=tool.copy();original_tool.data=tool.data.copy();liner.users_collection[0].objects.link(original_tool)
for direction in [frame.matrix_world.to_3x3().col[k].normalized()*sign for k in range(3)for sign in [-1,1]]:
    expanded=original_tool.copy();expanded.data=original_tool.data.copy();liner.users_collection[0].objects.link(expanded);pose=original_tool.matrix_world.copy();pose.translation+=direction*clearance;expanded.matrix_world=pose
    boolean(tool,expanded,'UNION');bpy.data.objects.remove(expanded,do_unlink=True)
bpy.data.objects.remove(original_tool,do_unlink=True)
home=tool.matrix_world.copy();sweep=None
for step in range(1,29):
    sample=tool.copy();sample.data=tool.data.copy();liner.users_collection[0].objects.link(sample);pose=home.copy();pose.translation-=axis*(step*.002);sample.matrix_world=pose
    if sweep is None:sweep=sample
    else:boolean(sweep,sample,'UNION');bpy.data.objects.remove(sample,do_unlink=True)
boolean(liner,sweep,'DIFFERENCE');bpy.data.objects.remove(sweep,do_unlink=True);bpy.data.objects.remove(tool,do_unlink=True);bpy.context.view_layer.update()
from mathutils.kdtree import KDTree
pre_cleanup=[liner.matrix_world@v.co for v in liner.data.vertices];bm=bmesh.new();bm.from_mesh(liner.data);welds=[];bound=1.5e-7
members={v:[liner.matrix_world@v.co]for v in bm.verts}
while True:
    choice=None
    for edge in bm.edges:
        if not edge.is_manifold or (liner.matrix_world.to_3x3()@(edge.verts[0].co-edge.verts[1].co)).length>bound:continue
        a,b=edge.verts;points=members[a]+members[b]
        if max((p-liner.matrix_world@a.co).length for p in points)<=bound:choice=(a,b,points);break
        if max((p-liner.matrix_world@b.co).length for p in points)<=bound:choice=(b,a,points);break
    if choice is None:break
    a,b,points=choice;pa=liner.matrix_world@a.co;pb=liner.matrix_world@b.co;welds.append({'from':list(pb),'to':list(pa),'world_distance':(pb-pa).length});members[a]=points;members.pop(b);bmesh.ops.weld_verts(bm,targetmap={b:a})
bmesh.ops.triangulate(bm,faces=list(bm.faces),quad_method='BEAUTY',ngon_method='BEAUTY');bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(liner.data);bm.free();liner.data.update()
kd=KDTree(len(liner.data.vertices))
for i,v in enumerate(liner.data.vertices):kd.insert(liner.matrix_world@v.co,i)
kd.balance();displacements=[kd.find(p)[2]for p in pre_cleanup]
(OUT/'precision_cleanup.json').write_text(json.dumps({'adjacent_edge_welds':welds,'world_bound':bound,'maximum_original_vertex_distance_after_cleanup':max(displacements),'triangulation':'BEAUTY; checked below against actual resulting triangles and visible surface rays'},indent=2)+'\n')
assert max(displacements)<=bound
volume,components=topology(liner);tree,v,f=geometry(liner);hits=[(a,b)for a,b in tree.overlap(tree)if a<b and not set(f[a])&set(f[b])]
bm=bmesh.new();bm.from_mesh(liner.data);bm.verts.ensure_lookup_table();todo=set(bm.verts);islands=[]
while todo:
    group={todo.pop()};pending=list(group)
    while pending:
        for edge in pending.pop().link_edges:
            for vertex in edge.verts:
                if vertex in todo:todo.remove(vertex);group.add(vertex);pending.append(vertex)
    points=[liner.matrix_world@x.co for x in group];indices={x.index for x in group};owned=[tri for tri in f if tri[0]in indices]
    origin=points[0];part_volume=abs(sum((v[a]-origin).dot((v[b]-origin).cross(v[c]-origin))/6 for a,b,c in owned))
    islands.append({'vertices':len(group),'triangles':len(owned),'volume':part_volume,'min':[min(p[k]for p in points)for k in range(3)],'max':[max(p[k]for p in points)for k in range(3)]})
bm.free();(OUT/'islands.json').write_text(json.dumps({'islands':islands,'self_contact_triangles':hits,'geometry_vertices_world':[list(p)for p in v],'geometry_triangles':f},indent=2)+'\n')
def contact_signature(vertices,faces,pair):return tuple(sorted(tuple(sorted(tuple(vertices[k])for k in faces[i]))for i in pair))
old_signatures={contact_signature(before_v,before_f,pair)for pair in before_hits}
new_hits=[pair for pair in hits if contact_signature(v,f,pair)not in old_signatures]
(OUT/'self_comparison.json').write_text(json.dumps({'before_count':len(before_hits),'after_count':len(hits),'exact_unchanged_contact_pairs':len(hits)-len(new_hits),'new_or_retriangulated_contact_pairs':new_hits,'triangles':[[[list(v[k])for k in f[a]],[list(v[k])for k in f[b]]]for a,b in new_hits]},indent=2)+'\n')
errors=[]
for origin,expected in samples:
    actual=tree.ray_cast(origin,-axis,.5)[0];errors.append((actual-expected).length if actual is not None else 100.)
proof={'parent_source_sha256':s['source_sha256'],'target':liner.name,'original_volume':before_volume,'new_volume':volume,'removed_fraction':(before_volume-volume)/before_volume,'components_before':before_components,'components_after':components,'self_contacts':len(hits),'visible_axial_surface_samples':len(samples),'maximum_visible_surface_change':max(errors),'scope':'Finite sampled swept relief of liner only. Visible-face rays must preserve the original exterior; original skins/base/hardware protected. Not continuous clearance or full assembly acceptance.'}
proof['tool_clearance_axis_offsets']=clearance
(OUT/'build_check.json').write_text(json.dumps(proof,indent=2)+'\n');print('PORT_ESCAPE_CHECK',proof,flush=True)
assert not hits and components==before_components and volume>0 and (before_volume-volume)/before_volume<.03
assert max(errors)<5e-7,'Visible formed surface changed; do not adopt this relief'
assert all(fp(bpy.data.objects[n])==value for n,value in protected.items())
source=ROOT/'blender/collection/I_nautilus_port_escape_r65.blend';component=ROOT/'app/assets/collection/components/I_nautilus_port_escape_r65.glb';assert not source.exists();bpy.ops.wm.save_as_mainfile(filepath=str(source),compress=True)
body=bpy.data.objects['IN1_BodyRoot'];bpy.ops.object.select_all(action='DESELECT')
for o in [body,*body.children_recursive]:o.select_set(True)
bpy.context.view_layer.objects.active=body;bpy.ops.export_scene.gltf(filepath=str(component),export_format='GLB',use_selection=True,export_animations=False,export_morph=True,export_morph_normal=True,export_extras=True)
ART=ROOT/'app/assets/collection/art/I/port_escape_r65';ART.mkdir(parents=True,exist_ok=True);layout=json.loads((ROOT/s['chamber_response_layout'].replace('res://','app/')).read_text());layout.update(source_sha256=sha(source),component_sha256=sha(component));(ART/'chamber_layout.json').write_text(json.dumps(layout,indent=2)+'\n')
d={**s,'source':str(source.relative_to(ROOT)),'source_sha256':sha(source),'component':str(component.relative_to(ROOT)),'component_sha256':sha(component),'chamber_response_layout':'res://assets/collection/art/I/port_escape_r65/chamber_layout.json','port_escape':proof,'status':'liner_escape_candidate_sweep_visual_pending'};(OUT/'build.json').write_text(json.dumps(d,indent=2)+'\n');print('PORT_ESCAPE_SOURCE',d['source_sha256'])
