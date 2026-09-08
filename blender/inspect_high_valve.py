import pathlib,json
from mathutils.bvhtree import BVHTree
ROOT=pathlib.Path(__file__).resolve().parents[1]
s=(ROOT/'blender/inspect_center_clearance.py').read_text(encoding='utf8');exec(s[:s.index('names=')])
name='P_Thermal_Valve_0';others=[p['name']for p in M['parts']if any(x in p['name']for x in ['Petal_','Actuator_','Gimbal_','Support','Solar','Thermal_Valve_1','Thermal_Valve_2'])]
result=[]
for op in [0,.25,.5,.75,1]:
 pose(op,0,0);target=tree(name)[0];pairs=[]
 for other in others:
  n=len(target.overlap(tree(other)[0]))
  if n:pairs.append([other,n])
 result.append({'open':op,'pairs':pairs});print('HIGH_VALVE',op,pairs,flush=True)
(ROOT/'tests/high_valve_before.json').write_text(json.dumps(result,indent=2))
