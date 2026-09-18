import math,json
from shapely.geometry import LineString
from pathlib import Path
from shapely.geometry import Point, Polygon
from shapely.affinity import rotate
from shapely.ops import unary_union
rows=[]
leaf_count=9
for aperture in [.60,.62,.64]:
 for pivot in [.66,.68,.7]:
  for travel in [1.1,1.25,1.4,1.55,1.7]:
   pocket=.813;region=Point(0,0).buffer(pocket,quad_segs=128)
   for j in range(81):
    a=travel*j/80;region=region.intersection(Point(pivot-pivot*math.cos(a),pivot*math.sin(a)).buffer(pocket,quad_segs=128))
   op=region.difference(Point(0,0).buffer(aperture+.0003,quad_segs=128));parts=list(op.geoms) if hasattr(op,'geoms') else [op];parts=[p for p in parts if p.contains(Point(pivot,0))]
   if len(parts)!=1:continue
   closed=rotate(parts[0],travel,origin=(pivot,0),use_radians=True)
   # Leaves sit BEHIND the head: the shaft, not the front cap, is the swept obstruction.
   hubpath=unary_union([Point(pivot-pivot*math.cos(travel*j/80),-pivot*math.sin(travel*j/80)).buffer(.034,quad_segs=64) for j in range(81)])
   closed=closed.difference(hubpath)
   if closed.geom_type!='Polygon' or closed.interiors:continue
   visible=Point(0,0).buffer(aperture-.004,quad_segs=128).difference(Point(0,0).buffer(.093,quad_segs=128))
   union=unary_union([rotate(closed,j*math.tau/leaf_count,origin=(0,0),use_radians=True) for j in range(leaf_count)]);gap=visible.difference(union).area/visible.area
   rows.append({'leaf_count':leaf_count,'shaft_clearance':.034,'aperture':aperture,'pivot':pivot,'travel':travel,'pocket':pocket,'closed_gap_fraction':gap,'profile':list(closed.exterior.coords)[:-1]})
rows.sort(key=lambda r:(round(r['closed_gap_fraction'],8),-r['aperture'],abs(r['travel']-1.3)))
out=Path('production/I_refinement/part_a_mouth');(out/'iris_design_candidates.json').write_text(json.dumps(rows,indent=2)+'\n')
# Swept fixed pins and the rear-going followers must not pass through neighbouring leaves.
best=rows[0];p=best['pivot'];travel=best['travel'];cuts=[]
for k in range(1,leaf_count):
 a=k*math.tau/leaf_count;dx=p*math.cos(a)-p;dy=p*math.sin(a)
 for kind,radius in [('pin',.0079),('follower',.0064)]:
  ox,oy=(0,0) if kind=='pin' else (.035*math.cos(a)-.077*math.sin(a),.035*math.sin(a)+.077*math.cos(a))
  pts=[]
  for j in range(161):
   t=travel*j/160;pts.append((p+dx*math.cos(t)-dy*math.sin(t)+ox,dx*math.sin(t)+dy*math.cos(t)+oy))
  cuts.append(LineString(pts).buffer(radius,quad_segs=24))
shape=Polygon(best['profile']).difference(unary_union(cuts))
parts=list(shape.geoms) if hasattr(shape,'geoms') else [shape];parts=[s for s in parts if s.contains(Point(p,0))]
assert len(parts)==1 and not parts[0].interiors
best['profile']=list(parts[0].exterior.coords)[:-1]
visible=Point(0,0).buffer(best['aperture']-.004,quad_segs=128).difference(Point(0,0).buffer(.093,quad_segs=128))
cover=unary_union([rotate(parts[0],k*math.tau/leaf_count,origin=(0,0),use_radians=True) for k in range(leaf_count)])
best['closed_gap_fraction']=visible.difference(cover).area/visible.area
best['relief_scope']='Swept neighbouring fixed pivot pins and all rear followers, 161 samples, buffered tool paths. Detached scrap removed.'
(out/'iris_design.json').write_text(json.dumps(best,indent=2)+'\n');print({k:v for k,v in best.items() if k!='profile'})

best=rows[0];pts=[]
for j in range(161):
 t=-.03+1.06*j/160;phi=-best['travel']*t;x=best['pivot']+.035*math.cos(phi)-.077*math.sin(phi);y=.035*math.sin(phi)+.077*math.cos(phi);a=.25*t;pts.append((x*math.cos(a)-y*math.sin(a),x*math.sin(a)+y*math.cos(a)))
shape=LineString(pts).buffer(.0075,quad_segs=32);assert shape.geom_type=='Polygon' and not shape.interiors
(out/'cam_slot_profile.json').write_text(json.dumps({'points':list(shape.exterior.coords)[:-1],'half_width':.0075,'path':pts,'depth_half':.025},indent=2)+'\n')
