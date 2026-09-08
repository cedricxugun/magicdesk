import pathlib
ROOT=pathlib.Path(__file__).resolve().parents[1]
s=(ROOT/'blender/inspect_center_clearance.py').read_text(encoding='utf8');exec(s[:s.index('names=')])
vals=['P_Thermal_Valve_1','P_Thermal_Valve_2'];others=[p['name']for p in M['parts']if any(x in p['name']for x in ['Petal_','Actuator_','Gimbal_','Support_Post'])]
report=[]
for step in range(11):
 pose(step/10,0,0);vt={n:tree(n)[0]for n in vals};ot={n:tree(n)[0]for n in others};pairs=[]
 for v in vals:
  for other,t in ot.items():
   n=len(vt[v].overlap(t))
   if n:pairs.append([v,other,n])
 print('VALVE_SWEEP',step/10,pairs,flush=True);report.append({'open':step/10,'pairs':pairs})
(ROOT/'tests/valve_sweep_before.json').write_text(json.dumps(report,indent=2))
