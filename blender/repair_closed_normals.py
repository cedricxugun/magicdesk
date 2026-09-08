import bpy,bmesh,pathlib,json
ROOT=pathlib.Path(__file__).resolve().parents[1]
S=bpy.context.scene;S.frame_set(1);fixed=[]
for o in bpy.data.collections['HELIOS_ASSET'].objects:
 if o.type!='MESH':continue
 bm=bmesh.new();bm.from_mesh(o.data);pending=set(bm.faces);count=0
 while pending:
  first=pending.pop();comp=[first];stack=[first]
  while stack:
   f=stack.pop()
   for edge in f.edges:
    for ff in edge.link_faces:
     if ff in pending:pending.remove(ff);stack.append(ff);comp.append(ff)
  if not all(len(e.link_faces)==2 for f in comp for e in f.edges):continue
  vol=0
  for f in comp:
   vv=[v.co for v in f.verts]
   for k in range(1,len(vv)-1):vol+=vv[0].dot(vv[k].cross(vv[k+1]))/6
  if vol < -1e-10:
   for f in comp:f.normal_flip()
   count+=1
 if count:
  bm.to_mesh(o.data);o.data.update();fixed.append({'mesh':o.name,'components':count})
 bm.free()
bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'blender/Helios_Incubator.blend'),compress=True)
(ROOT/'tests/closed_normal_repair.json').write_text(json.dumps({'fixed_components':sum(x['components'] for x in fixed),'meshes':fixed},indent=2))
print('CLOSED_NORMAL_REPAIR',json.dumps(fixed),flush=True)
