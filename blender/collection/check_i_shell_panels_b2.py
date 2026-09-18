"""Actual thin-shell topology, self/pair contacts and current A fit."""
import bpy,bmesh,json,hashlib,itertools
from pathlib import Path
from mathutils.bvhtree import BVHTree
ROOT=Path(__file__).resolve().parents[2];OUT=ROOT/'review/I_refinement/part_b_shell/panels_b2';spec=json.loads((OUT/'build.json').read_text())
assert hashlib.sha256((ROOT/spec['source']).read_bytes()).hexdigest()==spec['source_sha256']
bpy.ops.wm.open_mainfile(filepath=str(ROOT/spec['source']));scene=bpy.context.scene;scene.frame_set(1);bpy.context.view_layer.update()
panels=[bpy.data.objects[row['mesh']] for row in spec['panels']]
def geometry(o):
    e=o.evaluated_get(bpy.context.evaluated_depsgraph_get());m=e.to_mesh();m.calc_loop_triangles();p=[e.matrix_world@v.co for v in m.vertices];tri=[tuple(t.vertices) for t in m.loop_triangles];e.to_mesh_clear()
    return BVHTree.FromPolygons(p,tri,all_triangles=True),tri
surfaces={o.name:geometry(o) for o in panels};topology=[];self_hits=[];pairs=[]
for o in panels:
    bm=bmesh.new();bm.from_mesh(o.data);left=set(bm.verts);components=0
    while left:
        stack=[left.pop()];components+=1
        while stack:
            v=stack.pop()
            for e in v.link_edges:
                w=e.other_vert(v)
                if w in left:left.remove(w);stack.append(w)
    topology.append({'mesh':o.name,'components':components,'nonmanifold_edges':sum(not e.is_manifold for e in bm.edges),'nonmanifold_vertices':sum(not v.is_manifold for v in bm.verts),'zero_area_faces':sum(f.calc_area()<1e-12 for f in bm.faces),'volume':bm.calc_volume(signed=True)});bm.free()
    tree,tri=surfaces[o.name];count=sum(a<b and not set(tri[a]).intersection(tri[b]) for a,b in tree.overlap(tree))
    if count:self_hits.append({'mesh':o.name,'nonadjacent_intersections':count})
for a,b in itertools.combinations(panels,2):
    hits=surfaces[a.name][0].overlap(surfaces[b.name][0])
    if hits:pairs.append({'a':a.name,'b':b.name,'triangles':len(hits)})
fixed=geometry(bpy.data.objects[spec['fixed_collar']])[0];fixed_hits=[]
for o in panels:
    hits=surfaces[o.name][0].overlap(fixed)
    if hits:fixed_hits.append({'panel':o.name,'triangles':len(hits)})
mouth_spec=json.loads((ROOT/spec['mouth_report']).read_text());layout=json.loads((ROOT/'app'/mouth_spec['music_optics_layout'].removeprefix('res://')).read_text())
with bpy.data.libraries.load(str(ROOT/layout['source']),link=False) as (src,dst):dst.objects=[name for name in src.objects if name.startswith('I_')]
loaded=[o for o in dst.objects if o is not None]
for o in loaded:bpy.context.collection.objects.link(o)
next(o for o in loaded if o.name=='I_MusicOptics').parent=bpy.data.objects['IAM_Mouth']
mouth=[o for o in bpy.data.collections['MODULE_IAM'].all_objects if o.type=='MESH']+[o for o in loaded if o.type=='MESH' and o.name!=layout['sheet']]
mouth_hits=[]
for frame in [1,49,103,145,181,217,265,337,433]:
    scene.frame_set(frame);bpy.context.view_layer.update()
    for other in mouth:
        tree=geometry(other)[0]
        for panel in panels:
            hits=tree.overlap(surfaces[panel.name][0])
            if hits:mouth_hits.append({'frame':frame,'panel':panel.name,'against':other.name,'triangles':len(hits)})
    print('B2_MOUTH_FIT',frame,len(mouth_hits),flush=True)
passed=not self_hits and not pairs and not fixed_hits and not mouth_hits and all(t['components']==1 and t['nonmanifold_edges']==0 and t['nonmanifold_vertices']==0 and t['zero_area_faces']==0 and t['volume']>0 for t in topology)
report={'source_sha256':spec['source_sha256'],'component_sha256':spec['component_sha256'],'passed':passed,'topology':topology,'self_contacts':self_hits,'panel_pair_contacts':pairs,'fixed_collar_contacts':fixed_hits,'mouth_contacts':mouth_hits,'scope':'Actual six thickened panels in REST: topology/self/pair/fixed-collar checks and current A plus physical optics over nine source poses. No opening sweep, support/base, containment or art acceptance.'}
(OUT/'geometry_check.json').write_text(json.dumps(report,indent=2)+'\n');print('B2_PANEL_GEOMETRY',passed,flush=True)
