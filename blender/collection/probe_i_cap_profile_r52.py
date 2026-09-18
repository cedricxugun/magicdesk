import bpy,json,hashlib,math
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];s=json.loads((ROOT/'review/I_refinement/nautilus_r1/cowl_planes_r51/build.json').read_text());assert hashlib.sha256((ROOT/s['source']).read_bytes()).hexdigest()==s['source_sha256'];bpy.ops.wm.open_mainfile(filepath=str(ROOT/s['source']));bpy.context.scene.frame_set(1);bpy.context.view_layer.update();o=bpy.data.objects['IN1_PorcelainPanel_05'];m=o.data;world=o.matrix_world;vertices=[world@v.co for v in m.vertices];selected={p.index for p in m.polygons if all(abs(vertices[i].z-1.702)<2e-7 for i in p.vertices)};edge_counts={}
for i in selected:
 for li in m.polygons[i].loop_indices:
  e=m.loops[li].edge_index;edge_counts[e]=edge_counts.get(e,0)+1
edges=[m.edges[i]for i,c in edge_counts.items()if c==1];adj={}
for e in edges:
 a,b=e.vertices;adj.setdefault(a,[]).append(b);adj.setdefault(b,[]).append(a)
assert all(len(v)==2 for v in adj.values()),{i:len(v)for i,v in adj.items()if len(v)!=2}
unseen=set(adj);loops=[]
while unseen:
 first=min(unseen);current=first;prior=None;chain=[]
 while True:
  chain.append(current);unseen.discard(current);n=next(v for v in adj[current]if v!=prior)
  if n==first:break
  prior,current=current,n
 points=[vertices[i]for i in chain];lengths=[(points[(i+1)%len(points)]-p).length for i,p in enumerate(points)];area=sum(points[i].x*points[(i+1)%len(points)].y-points[(i+1)%len(points)].x*points[i].y for i in range(len(points)))/2
 loops.append({'source_vertices':chain,'points_world':[list(p)for p in points],'signed_area_xy':area,'minimum_edge_length':min(lengths),'length':sum(lengths)})
m.calc_loop_triangles();triangles=[{'vertices':list(t.vertices),'world':[list(vertices[i])for i in t.vertices]}for t in m.loop_triangles if t.polygon_index in selected]
r={'source_sha256':s['source_sha256'],'source':s['source'],'mesh':o.name,'plane_z':1.702,'fixed_cheek_z':1.698,'gap':.004,'cap_polygon_count':len(selected),'cap_triangle_count':len(triangles),'loops':loops,'triangles':triangles,'mesh_matrix_world':[list(r)for r in world],'scope':'Actual horizontal cut-face footprint. Read-only extraction; not a finished rim or clearance proof.'};(ROOT/'review/I_refinement/nautilus_r1/cap_profile_r52/profile.json').write_text(json.dumps(r,indent=2)+'\n');print('R52_CAP_PROFILE',{'polygons':len(selected),'triangles':len(triangles),'loops':[{'n':len(l['source_vertices']),'area':l['signed_area_xy'],'length':l['length'],'minimum_edge':l['minimum_edge_length']}for l in loops]},flush=True)
