import pathlib,json
from mathutils.bvhtree import BVHTree
ROOT=pathlib.Path(__file__).resolve().parents[1]
exec(compile((ROOT/'blender/repair_center_mechanism.py').read_text(encoding='utf8'),str(ROOT/'blender/repair_center_mechanism.py'),'exec'))
s=(ROOT/'blender/inspect_center_clearance.py').read_text(encoding='utf8');a=s.index('def tree(');b=s.index('names=',a);exec(s[a:b])
names=[p['name']for p in M['parts']if any(x in p['name']for x in ['Petal_','Actuator_','Gimbal_','Support_Post','Bottom_Bearing','Solar','Stator','Socket'])]
normal=[]
for op in [0,.1,.25,.5,.75,.9,1]:
 for ph in [0,1.8,3.6]:
  pose(op,ph,0);trees={n:tree(n)[0]for n in names};pairs=[]
  for v in ['P_Thermal_Valve_1','P_Thermal_Valve_2']:
   vt=tree(v)[0]
   for n,t in trees.items():
    count=len(vt.overlap(t))
    if count:pairs.append([v,n,count])
  if pairs:print('NORMAL_INTERSECTIONS',op,ph,pairs,flush=True)
  normal.append({'open':op,'phase':ph,'pairs':pairs})
center=[p['name']for p in M['parts']if any(x in p['name']for x in ['Gimbal_','Trunnion','Solar','Support_Post','Bottom_Bearing','Stator','Socket'])]
exploded=[]
for ex in [.18,.30,.4,.5,.6,.7,.8,.9,1]:
 pose(0,2,ex);trees={n:tree(n)[0]for n in center};pairs=[]
 for i,a in enumerate(center):
  for b in center[i+1:]:
   count=len(trees[a].overlap(trees[b]))
   if count:pairs.append([a,b,count])
 print('CENTER_PATH',ex,pairs,flush=True);exploded.append({'explosion':ex,'pairs':pairs})
(ROOT/'tests/center_repair_candidate.json').write_text(json.dumps({'normal':normal,'center':exploded,'valves':fixes},indent=2))
