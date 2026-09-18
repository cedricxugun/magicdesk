"""Rounded metal underside generated inside the measured horizontal cap footprint."""
from pathlib import Path
import json,math,struct,collections,argparse
import shapely
from shapely.geometry import Polygon,Point
from shapely.ops import nearest_points
from shapely.geometry.polygon import orient
ROOT=Path(__file__).resolve().parents[2]
parser=argparse.ArgumentParser();parser.add_argument('--profile',default='review/I_refinement/nautilus_r1/cap_profile_r52/profile.json');parser.add_argument('--out');args=parser.parse_args()
profile=ROOT/args.profile;OUT=profile.parent;s=json.loads(profile.read_text());assert len(s['loops'])==1
P=orient(Polygon([(v[0],v[1])for v in s['loops'][0]['points_world']]),sign=1.);assert P.is_valid and not P.is_empty
r=.00075;tmin=.00025;z0=s['plane_z'];N=8
layers=[]
for j in range(N+1):
 theta=math.pi/2*j/N;d=r*(1-math.cos(theta));q=P if j==0 else P.buffer(-d,quad_segs=8,join_style='round');assert q.is_valid and not q.is_empty
 assert q.difference(P).area<1e-14
 layers.append((q,d,theta))
verts=[];front=[];lookup={};bands=[];quantization=[]
def f32(x):return struct.unpack('<f',struct.pack('<f',x))[0]
def add(p):
 xy=tuple(f32(float(v))for v in p);quantization.append(math.dist(xy,p))
 if xy not in lookup:
  d=P.boundary.distance(Point(xy));theta=math.acos(max(0.,min(1.,1-d/r)))if d<r else math.pi/2;z=z0-tmin-r*math.sin(theta)
  lookup[xy]=len(verts);verts.append([xy[0],xy[1],z])
 return lookup[xy]
for j in range(N+1):
 region=layers[j][0].difference(layers[j+1][0])if j<N else layers[j][0]
 triangles=list(shapely.constrained_delaunay_triangles(region).geoms);assert abs(sum(t.area for t in triangles)-region.area)<1e-11
 for tri in triangles:
  xy=list(tri.exterior.coords)[:3];ids=[add(p)for p in xy]
  if len(set(ids))<3:continue
  a,b,c=[verts[i]for i in ids];area=(b[0]-a[0])*(c[1]-a[1])-(b[1]-a[1])*(c[0]-a[0])
  if area==0:continue
  if area>0:ids.reverse()
  front.append(ids)
 bands.append({'band':j,'area':region.area,'triangles':len(triangles)})
edges=collections.defaultdict(list)
for f in front:
 for i in range(3):a,b=f[i],f[(i+1)%3];edges[tuple(sorted((a,b)))].append((a,b))
assert all(len(e)<=2 for e in edges.values())
boundary=[e[0]for e in edges.values()if len(e)==1]
interior_gaps=[]
for a,b in boundary:
 for i in [a,b]:
  if P.boundary.distance(Point(verts[i][:2]))>1e-7:interior_gaps.append(i)
assert not interior_gaps,('Internal triangulation boundary',len(interior_gaps))
# Source footprint points were float32 already; new offset vertices have the
# same storage precision as the eventual Blender mesh, with explicit bounds.
assert max(quantization)<1e-7
boundary_normals=collections.defaultdict(lambda:[0.,0.])
for a,b in boundary:
 p,q=verts[a],verts[b];dx=q[0]-p[0];dy=q[1]-p[1];length=math.hypot(dx,dy);n=(-dy/length,dx/length)
 for i in [a,b]:boundary_normals[i][0]+=n[0];boundary_normals[i][1]+=n[1]
normals=[]
for i,p in enumerate(verts):
 d=P.boundary.distance(Point(p[:2]));theta=math.acos(max(0.,min(1.,1-d/r)))if d<r else math.pi/2
 if i in boundary_normals:n=boundary_normals[i]
 else:
  q=nearest_points(P.boundary,Point(p[:2]))[0];n=[q.x-p[0],q.y-p[1]]
 length=math.hypot(*n)
 if length<1e-15:n=[0.,0.];length=1.
 normals.append([n[0]/length*math.cos(theta),n[1]/length*math.cos(theta),-math.sin(theta)])
count=len(verts);verts += [[p[0],p[1],z0]for p in verts[:count]];faces=list(front);corner_normals=[[normals[i]for i in f]for f in front];types=['front']*len(front)
for f in front:
 face=[i+count for i in reversed(f)];faces.append(face);corner_normals.append([[0.,0.,1.]]*3);types.append('back')
for a,b in boundary:
 face=[b,a,a+count,b+count];faces.append(face);cn=[]
 for i in [b,a,a,b]:
  n=boundary_normals[i];length=math.hypot(*n);cn.append([n[0]/length,n[1]/length,0.])
 corner_normals.append(cn);types.append('side')
all_edges=collections.Counter(tuple(sorted((f[i],f[(i+1)%len(f)])))for f in faces for i in range(len(f)));assert set(all_edges.values())=={2}
sign=int(s.get('outward_sign',-1));assert sign in [-1,1]
if sign==1:
    verts=[[p[0],p[1],2*z0-p[2]]for p in verts]
    faces=[list(reversed(f))for f in faces]
    corner_normals=[[[n[0],n[1],-n[2]]for n in reversed(row)]for row in corner_normals]
report={'source_sha256':s['source_sha256'],'target_mesh':s['mesh'],'plane_z':z0,'outward_sign':sign,'bevel_radius':r,'vertical_land':tmin,'maximum_depth':r+tmin,'source_gap':s['gap'],'vertices_world':verts,'faces':faces,'corner_normals_world':corner_normals,'face_types':types,'front_vertex_count':count,'boundary_edges':len(boundary),'bands':bands,'max_float32_xy_quantization':max(quantization),'footprint_area':P.area,'shapely':shapely.__version__,'scope':'Closed rounded trim entirely within the measured footprint up to explicit float32 rounding. Back face is nominal here and must be fitted to actual source triangles in Blender.'}
target=ROOT/args.out if args.out else OUT/'trim_mesh.json';target.write_text(json.dumps(report,indent=2)+'\n');print('TRIM_MESH',len(verts),len(faces),len(boundary),max(quantization))
