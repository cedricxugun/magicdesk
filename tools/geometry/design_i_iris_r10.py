"""Circular-edge six-blade iris envelope design. Outputs candidates, not assembly acceptance."""
import math,json
from pathlib import Path
from shapely.geometry import Point
from shapely.affinity import rotate
from shapely.ops import unary_union
ROOT=Path(__file__).resolve().parents[2];OUT=ROOT/'production/I_refinement/mouth_r10';OUT.mkdir(exist_ok=True)
rows=[]
for aperture in [.50,.53,.55,.57]:
 for pivot in [.58,.60,.62,.65]:
  if pivot<aperture+.025:continue
  for travel in [1.05,1.20,1.35,1.50,1.65]:
   pocket=.86;region=Point(0,0).buffer(pocket,quad_segs=128)
   for j in range(65):
    a=travel*j/64;region=region.intersection(Point(pivot-pivot*math.cos(a),pivot*math.sin(a)).buffer(pocket,quad_segs=128))
   open_region=region.difference(Point(0,0).buffer(aperture+.0002,quad_segs=128))
   pieces=list(open_region.geoms) if hasattr(open_region,'geoms') else [open_region]
   pieces=[p for p in pieces if p.contains(Point(pivot,0))]
   if len(pieces)!=1:continue
   open_blade=pieces[0];closed=rotate(open_blade,travel,origin=(pivot,0),use_radians=True)
   union=unary_union([rotate(closed,j*math.tau/6,origin=(0,0),use_radians=True) for j in range(6)])
   face=Point(0,0).buffer(aperture-.005,quad_segs=128);uncovered=face.difference(union)
   row={'aperture':aperture,'pivot':pivot,'travel':travel,'pocket':pocket,'uncovered_closed_area':uncovered.area,'closed_visible_area':face.area,'uncovered_fraction':uncovered.area/face.area,'closed_outline':list(closed.exterior.coords)[:-1],'interior_rings':[list(r.coords) for r in closed.interiors],'scope':'65 sampled outer-envelope constraints and polygonal disk closure only; pivot/follower bores, 3D clearances and appearance not yet checked.'}
   rows.append(row)
 rows.sort(key=lambda r:(round(r['uncovered_fraction'],8),-r['aperture'],abs(r['pivot']-.6)))
 print('IRIS_CIRCULAR',aperture,[{k:v for k,v in r.items() if k not in ['closed_outline','interior_rings','scope']} for r in rows[:2]],flush=True)
(OUT/'curved_iris_candidates.json').write_text(json.dumps(rows,indent=2)+'\n')
if rows:(OUT/'curved_iris_candidate.json').write_text(json.dumps(rows[0],indent=2)+'\n')
