import pathlib,json
from mathutils.bvhtree import BVHTree
ROOT=pathlib.Path(__file__).resolve().parents[1]
exec(compile((ROOT/'blender/repair_center_mechanism.py').read_text(encoding='utf8'),str(ROOT/'blender/repair_center_mechanism.py'),'exec'))
s=(ROOT/'blender/inspect_center_clearance.py').read_text(encoding='utf8');a=s.index('def tree(');b=s.index('names=',a);exec(s[a:b])
moving=[p['name']for p in M['parts']if any(x in p['name']for x in ['Gimbal_','Solar','Support_Post','Bottom_Bearing'])]
external=[p['name']for p in M['parts']if any(x in p['name']for x in ['Petal_','Actuator_','Thermal_'])]
results=[]
for ex in [.2,.35,.5,.65,.8,1.0]:
 for op in [0,max(0,1-ex*2.5)]:
  pose(op,2.0,ex);ext={n:tree(n)[0]for n in external};pairs=[]
  for a in moving:
   t=tree(a)[0]
   for b,tb in ext.items():
    n=len(t.overlap(tb))
    if n:pairs.append([a,b,n])
  print('CENTER_EXTERNAL',ex,op,pairs,flush=True);results.append({'explosion':ex,'open':op,'pairs':pairs})
(ROOT/'tests/center_external_candidate.json').write_text(json.dumps(results,indent=2))
