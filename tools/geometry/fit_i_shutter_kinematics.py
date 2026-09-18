"""Fit real rigid peripheral-pivot paths to the asymmetric REST candidates.

This is a geometric feasibility search, never an original-art accuracy score.
"""
import json,math
from pathlib import Path
from shapely.geometry import Point,Polygon,LineString
from shapely.affinity import rotate,scale
from shapely.ops import unary_union,nearest_points
ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'review/I_refinement/part_a_mouth/shutter_r2/kinematic_fit';OUT.mkdir(parents=True,exist_ok=True)
bands=[((.46,.59),(-.47,-.57),-.12,-.43),((.05,.745),(-.56,-.49),-.025,-.30),((-.29,.685),(-.67,-.28),-.025,-.245)]
targets=[]
for aa,dd,left,right in bands:
 dx=dd[0]-aa[0];dy=dd[1]-aa[1];length=math.hypot(dx,dy);side=(-dy/length,dx/length);edge=[]
 for bulge,seq in [(left,range(81)),(right,range(80,-1,-1))]:
  for j in seq:
   t=j/80;w=.035+.965*math.sin(math.pi*t);edge.append((aa[0]+dx*t+side[0]*bulge*w,aa[1]+dy*t+side[1]*bulge*w))
 targets.append(Polygon(edge))
results=[[] for _ in targets]
aperture=.645;pocket=.775
for pivot in [.705,.73,.748,.76]:
 for travel in [.75,.9,1.05,1.2,1.35,1.5,1.65,1.8]:
  region=Point(0,0).buffer(pocket,quad_segs=96)
  for j in range(61):
   a=travel*j/60;region=region.intersection(Point(pivot-pivot*math.cos(a),pivot*math.sin(a)).buffer(pocket,quad_segs=96))
  op=region.difference(Point(0,0).buffer(aperture+.001,quad_segs=96))
  parts=list(op.geoms) if hasattr(op,'geoms') else [op];parts=[s for s in parts if s.geom_type=='Polygon' and s.contains(Point(pivot,0))]
  if len(parts)!=1:continue
  feasible=rotate(parts[0],travel,origin=(pivot,0),use_radians=True)
  hub=unary_union([Point(pivot-pivot*math.cos(travel*j/60),-pivot*math.sin(travel*j/60)).buffer(.034,quad_segs=24) for j in range(61)])
  feasible=feasible.difference(hub)
  for idx,target in enumerate(targets):
   angles=[]
   for end in bands[idx][:2]:
    home=math.atan2(end[1],end[0])
    angles.extend(home+d for d in [-.08,-.04,0,.04,.08])
   for angle in angles:
    for hand in [-1,1]:
     base=scale(feasible,xfact=1,yfact=hand,origin=(0,0));world=rotate(base,angle,origin=(0,0),use_radians=True)
     cut=world.intersection(target);pieces=list(cut.geoms) if hasattr(cut,'geoms') else [cut];pieces=[x for x in pieces if x.geom_type=='Polygon' and not x.is_empty and x.area>1e-8]
     if not pieces:continue
     cut=max(pieces,key=lambda p:p.area)
     root=Point(pivot*math.cos(angle),pivot*math.sin(angle));distance=cut.distance(root)
     if distance>.045:continue
     nearest=nearest_points(cut,root)[0];neck=LineString([nearest,root]).buffer(.010,quad_segs=16)
     body=cut.union(neck).intersection(world)
     if body.geom_type!='Polygon' or body.interiors or not body.covers(root):continue
     score=cut.area/target.area
     results[idx].append({'reference_area_coverage':score,'pivot':list(root.coords)[0],'pivot_radius':pivot,'home_angle':angle,'travel':-travel*hand,'aperture':aperture,'pocket':pocket,'root_neck_distance':distance,'profile':list(body.exterior.coords)[:-1]})
for rows in results:rows.sort(key=lambda r:-r['reference_area_coverage'])
report={'scope':'Feasible rigid 2D leaf profiles against circular storage envelope and open aperture, compared only with current unaccepted REST mesh footprint. Not original-art accuracy or full 3D collision/drive validation.','candidates':[[r for r in rows[:5]] for rows in results]}
(OUT/'fits.json').write_text(json.dumps(report,indent=2)+'\n')
for i,rows in enumerate(results):print(i,[{k:v for k,v in r.items() if k!='profile'} for r in rows[:2]],flush=True)
