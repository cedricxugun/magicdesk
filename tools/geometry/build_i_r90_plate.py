"""Planar union/CDT for one connected milled network backbone.
Blender later maps these shared parameter vertices to the actual coiled wall."""
import json,math,sys
from pathlib import Path
import numpy as np
from shapely import constrained_delaunay_triangles
from shapely.geometry import Polygon,MultiPoint
from shapely.ops import unary_union
version='r4' if '--manifolds' in sys.argv else 'r3' if '--refined' in sys.argv else 'r2' if '--visible' in sys.argv else 'r1'
R=Path(__file__).resolve().parents[2];OUT=R/'review/I_refinement/nautilus_reset_r82/network_r90';d=json.loads((OUT/f'paths_{"r3" if version=="r4" else version}.json').read_text())
def disk(p,r,n=20):
 jt=np.array(p['jt']);ju=np.array(p['ju']);normal=np.array(p['n']);x=jt/np.linalg.norm(jt);y=np.cross(normal,x);y/=np.linalg.norm(y);j=np.stack([jt,ju],axis=1);inverse=np.linalg.inv(j.T@j)@j.T
 return [(p['t']+v[0],p['u']+v[1])for v in [inverse@(r*(x*math.cos(math.tau*k/n)+y*math.sin(math.tau*k/n)))for k in range(n)]]
outer=[];grooves=[]
for seg in d['segments']:
 od=[disk(p,p['width'])for p in seg['samples']];gd=[disk(p,p['glass_radius']*1.30)for p in seg['samples']]
 for a,b in zip(od,od[1:]):outer.append(MultiPoint(a+b).convex_hull)
 for a,b in zip(gd,gd[1:]):grooves.append(MultiPoint(a+b).convex_hull)
outer +=[Polygon(disk(p,p['radius'],32))for p in d['junctions']]
caps=[];occupied=[]
if version=='r4':
 for j in sorted(d['junctions'],key=lambda x:(not x['root'],-x['clearance'])):
  if not j['root'] and j['clearance']<.015:continue
  p=np.array(j['p']);head=.008 if j['root']else .0045;shaft=.0026 if j['root']else .0016
  if any(np.linalg.norm(p-q)<head+r+.008 for q,r in occupied):continue
  ring=shaft+.0034
  # A cap must not trap a nonincident optical route beneath its screw.
  conflict=False
  for seg in d['segments']:
   if seg['start']==j['node'] or seg['end']==j['node']:continue
   if any(np.linalg.norm(np.array(s['p'])-p)<ring+.001 for s in seg['samples']):conflict=True;break
  if conflict:continue
  occupied.append((p,head));caps.append({**j,'head_radius':head,'shaft_radius':shaft,'ring_radius':ring,'ring_glass_radius':.0013})
body=unary_union(outer)
exclusions=[]
for c in d['cells']:
 exclusions.append(Polygon([(c['t']+c['half_t']*1.105*(math.cos(a)+.10*math.sin(a)**2),c['u']+c['half_u']*1.105*math.sin(a))for a in [math.tau*k/96 for k in range(96)]]))
body=body.difference(unary_union(exclusions));assert body.is_valid and body.geom_type=='Polygon',body.geom_type
inset=body.buffer(-.0015,join_style='round');assert inset.is_valid
groove=unary_union(grooves)
if version=='r4':
 for j in caps:
  width=j['ring_glass_radius']*1.30;inside=Polygon(disk(j,j['ring_radius']-width,64));outside=Polygon(disk(j,j['ring_radius']+width,64));groove=groove.difference(inside).union(outside.difference(inside))
groove=groove.intersection(inset.buffer(-.001));opening=groove.buffer(.0015,join_style='round').intersection(inset.buffer(-.0004))
if version=='r4':
 for j in caps:opening=opening.difference(Polygon(disk(j,j['shaft_radius']+.0011,64)))
groove=groove.intersection(opening)
assert groove.is_valid and opening.is_valid
vertices=[];faces=[];tags=[];mapping={}
def vertex(x,y,h):
 key=(round(float(x),10),round(float(y),10),round(float(h),10))
 if key not in mapping:mapping[key]=len(vertices);vertices.append(key)
 return mapping[key]
def polygons(g):return [g]if g.geom_type=='Polygon'else list(g.geoms)
def triangulate(g,height,tag):
 if g.is_empty:return
 for poly in polygons(g):
  if poly.area<1e-14:continue
  for tri in constrained_delaunay_triangles(poly).geoms:
   points=list(tri.exterior.coords)[:3];faces.append([vertex(x,y,height(x,y)if callable(height)else height)for x,y in points]);tags.append(tag)
from shapely.geometry import Point
triangulate(body,-.0004,'bottom')
triangulate(inset.difference(opening),.0065,'top')
floor_height=.0024 if version=='r4' else .0028 if version=='r3' else .0032
triangulate(groove,floor_height,'floor')
triangulate(body.difference(inset),lambda x,y:.0058 if body.boundary.distance(Point(x,y))<1e-8 else .0065,'outer_bevel')
triangulate(opening.difference(groove),lambda x,y:.0065 if opening.boundary.distance(Point(x,y))<1e-8 else floor_height,'groove_bevel')
for ring in [body.exterior,*body.interiors]:
 points=list(ring.coords)
 for (x,y),(xx,yy)in zip(points,points[1:]):
  a=vertex(x,y,-.0004);b=vertex(xx,yy,-.0004);c=vertex(xx,yy,.0058);e=vertex(x,y,.0058);faces.extend([[a,b,c],[a,c,e]]);tags.extend(['side','side'])
kept=[(f,t)for f,t in zip(faces,tags)if len(set(f))==3];collapsed_triangles=len(faces)-len(kept);faces=[x[0]for x in kept];tags=[x[1]for x in kept]
edges={}
for face in faces:
 for a,b in zip(face,face[1:]+face[:1]):
  key=tuple(sorted([a,b]));edges[key]=edges.get(key,0)+1
bad=[(k,v)for k,v in edges.items()if v!=2]
(OUT/f'plate_parameters_{version}.json').write_text(json.dumps({'vertices':vertices,'triangles':faces,'tags':tags,'parameter_area':body.area,'nonmanifold_edges':bad,'collapsed_triangles_removed':collapsed_triangles,'caps':caps,'scope':'Shared-index closed parameter solid from explicit outer/groove unions and constrained triangulations, before curved-surface refinement.'},indent=2)+'\n')
print('R90_PLATE',len(vertices),len(faces),'bad_edges',len(bad));assert not bad,bad[:20]
