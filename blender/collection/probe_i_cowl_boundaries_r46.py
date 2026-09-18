import bpy,bmesh,json,hashlib,math
from pathlib import Path
from mathutils import Vector
ROOT=Path(__file__).resolve().parents[2];s=json.loads((ROOT/'review/I_refinement/nautilus_r1/scan_caps_runtime_r43/readable/build.json').read_text());assert hashlib.sha256((ROOT/s['source']).read_bytes()).hexdigest()==s['source_sha256'];bpy.ops.wm.open_mainfile(filepath=str(ROOT/s['source']));bpy.context.scene.frame_set(1);bpy.context.view_layer.update();o=bpy.data.objects['IN1_PorcelainPanel_01'];M=o.matrix_world;inverse=M.inverted();mouth=bpy.data.objects['IAM_MODULE'].matrix_world;center=mouth.translation;back=mouth.to_3x3().col[2].normalized();right=mouth.to_3x3().col[0].normalized();up=mouth.to_3x3().col[1].normalized();rows=[]
for depth in [-.034,.0,.1,.2,.299,.4,.5,.6,.62]:
 bm=bmesh.new();bm.from_mesh(o.data);bmesh.ops.bisect_plane(bm,geom=list(bm.verts)+list(bm.edges)+list(bm.faces),plane_co=inverse@(center+back*depth),plane_no=M.to_3x3().transposed()@back,dist=1e-8,clear_inner=True);bm.normal_update();edges={e for e in bm.edges if len(e.link_faces)==1};points=set(v for e in edges for v in e.verts);components=[]
 while points:
  seed=points.pop();group={seed};pending=[seed]
  while pending:
   for e in pending.pop().link_edges:
    if e not in edges:continue
    v=e.other_vert(next(v for v in e.verts if v in group))if sum(v in group for v in e.verts)==1 else None
    if v is not None and v in points:points.remove(v);group.add(v);pending.append(v)
  coords=[M@v.co for v in group];angles=[math.atan2((p-center).dot(up),(p-center).dot(right))for p in coords];components.append({'count':len(group),'world':[[float(x)for x in p]for p in coords],'angle_range':[min(angles),max(angles)],'z_range':[min(p.z for p in coords),max(p.z for p in coords)]})
 rows.append({'depth':depth,'loops':components});print('R46_SECTION',depth,[(x['count'],x['z_range'])for x in components],flush=True);bm.free()
(ROOT/'review/I_refinement/nautilus_r1/cowl_boundaries_r46/sections.json').write_text(json.dumps({'source_sha256':s['source_sha256'],'mesh':o.name,'sections':rows},indent=2)+'\n')
