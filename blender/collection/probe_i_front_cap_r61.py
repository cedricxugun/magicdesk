"""Read actual mouth-axis end-face planes; never infer them from artwork."""
import bpy, json, hashlib, collections
from pathlib import Path
from mathutils import Vector
ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'review/I_refinement/nautilus_r1/curved_returns_r61'
s=json.loads((OUT/'input.json').read_text())
assert hashlib.sha256((ROOT/s['source']).read_bytes()).hexdigest()==s['source_sha256']
bpy.ops.wm.open_mainfile(filepath=str(ROOT/s['source']))
bpy.context.scene.frame_set(1);bpy.context.view_layer.update()
mouth=bpy.data.objects['IAM_MODULE'].matrix_world
origin=mouth.translation;basis=[mouth.to_3x3().col[i].normalized() for i in range(3)]
o=bpy.data.objects['IN1_PorcelainPanel_05'];m=o.data
world=[o.matrix_world@v.co for v in m.vertices]
local=[Vector(tuple((p-origin).dot(a) for a in basis)) for p in world]
depths=collections.Counter(round(p.z,6) for p in local)
planes=[]
for z,count in depths.most_common(15):
    selected=[p.index for p in m.polygons if all(abs(local[i].z-z)<5e-7 for i in p.vertices)]
    planes.append({'depth':z,'vertices_near':count,'polygons':len(selected)})
(OUT/'front_planes.json').write_text(json.dumps({'source_sha256':s['source_sha256'],'mesh':o.name,'planes':planes,'frame_origin':list(origin),'frame_axes':[list(v) for v in basis]},indent=2)+'\n')
print('FRONT_PLANES',planes,flush=True)
z=-.035
selected={p.index for p in m.polygons if all(abs(local[i].z-z)<5e-7 for i in p.vertices)}
assert len(selected)>100
edge_counts=collections.Counter(m.loops[li].edge_index for index in selected for li in m.polygons[index].loop_indices)
edges=[m.edges[i] for i,n in edge_counts.items() if n==1];adj={}
for e in edges:
    a,b=e.vertices;adj.setdefault(a,[]).append(b);adj.setdefault(b,[]).append(a)
assert all(len(v)==2 for v in adj.values())
unseen=set(adj);loops=[]
while unseen:
    first=min(unseen);current=first;prior=None;chain=[]
    while True:
        chain.append(current);unseen.discard(current);next_v=next(v for v in adj[current] if v!=prior)
        if next_v==first:break
        prior,current=current,next_v
    points=[local[i] for i in chain]
    loops.append({'source_vertices':chain,'points_world':[list(v) for v in points],'coordinate_space':'mouth-end orthonormal frame, not scene world'})
m.calc_loop_triangles()
triangles=[{'vertices':list(t.vertices),'world':[list(world[i]) for i in t.vertices]} for t in m.loop_triangles if t.polygon_index in selected]
profile={'source':s['source'],'source_sha256':s['source_sha256'],'mesh':o.name,'plane_z':z,'outward_sign':-1,'gap':None,'loops':loops,'triangles':triangles,'frame_origin':list(origin),'frame_axes':[list(v) for v in basis],'coordinate_space':'All points_world in loops are generator plane-frame coordinates. triangles.world are true scene coordinates. Must transform generated trim before installation.','cap_polygons':len(selected),'plane_residual_max':max(abs(local[i].z-z) for index in selected for i in m.polygons[index].vertices)}
(OUT/'profile.json').write_text(json.dumps(profile,indent=2)+'\n')
print('FRONT_PROFILE',len(selected),[len(l['source_vertices']) for l in loops],profile['plane_residual_max'],flush=True)
