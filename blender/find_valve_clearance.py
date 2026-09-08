import pathlib
ROOT=pathlib.Path(__file__).resolve().parents[1]
s=(ROOT/'blender/inspect_center_clearance.py').read_text(encoding='utf8');exec(s[:s.index('names=')])
names=[p['name']for p in M['parts']if any(x in p['name']for x in ['Petal_','Actuator_','Gimbal_','Support_Post','Bottom_Bearing','Solar','Stator','Socket'])]
states=[]
for op in [0,.25,.5,.75,1]:
 for phase in [0,1.8]:
  pose(op,phase,0);states.append((op,phase,{n:tree(n)[0]for n in names}))
vbase={};polys={}
for j in [1,2]:
 name='P_Thermal_Valve_%d'%j;o=next(c for c in bpy.data.objects[name].children_recursive if c.type=='MESH');vbase[j]=[o.matrix_world@v.co for v in o.data.vertices];polys[j]=[tuple(p.vertices)for p in o.data.polygons]
best=[]
for r in [.22,.26,.30,.34]:
 for z in [1.17,1.20,1.23]:
  for scale in [.40,.48,.56]:
   total=0;pairs={}
   for j in [1,2]:
    old=bpy.data.objects['Thermal_Valve_Frame'+('.001'if j==1 else'.002')].matrix_world.translation.copy();rad=Vector((old.x,old.y,0)).normalized();new=rad*r+Vector((0,0,z));verts=[new+Vector(((p.x-old.x)*scale,(p.y-old.y)*scale,max(p.z-old.z,-.055)*scale))for p in vbase[j]];vt=BVHTree.FromPolygons(verts,polys[j])
    for op,phase,trees in states:
     for name,t in trees.items():
      n=len(vt.overlap(t));total+=n
      if n:pairs[name]=pairs.get(name,0)+n
   best.append((total,r,z,scale,pairs))
   if total==0:print('VALVE_CLEAR_CANDIDATE',r,z,scale,flush=True)
best.sort(key=lambda x:x[0]);print('VALVE_BEST',best[:8],flush=True)
(ROOT/'tests/valve_fit_candidates.json').write_text(json.dumps(best[:8],indent=2))
