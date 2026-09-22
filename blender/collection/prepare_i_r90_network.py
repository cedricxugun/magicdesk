"""Smooth the rooted network and assign one continuous physical-distance UV."""
import bpy,json,math,sys
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
R=Path(__file__).resolve().parents[2];sys.path.insert(0,str(Path(__file__).parent))
from i_formed_coil_surface import FormedCoilSurface
version='r3' if '--refined' in sys.argv else 'r2' if '--visible' in sys.argv else 'r1'
BASE=R/'review/I_refinement/nautilus_reset_r82';OUT=BASE/'network_r90';plan=json.loads((OUT/f'routing_{"r2" if version=="r3" else version}.json').read_text());spec=json.loads((BASE/'chambers_r89/built_r3/build.json').read_text())
bpy.ops.wm.open_mainfile(filepath=str(R/spec['source']));scene=bpy.context.scene;scene.frame_set(1);bpy.context.view_layer.update()
surface=FormedCoilSurface(json.loads((BASE/'mechanism_r9/build.json').read_text())['shape_parameters'],bpy.data.objects['IAM_Mouth'].matrix_world.inverted(),spec['formed_liner_return'])
def tree(objects):
 vs=[];fs=[]
 for o in objects:
  if o.type not in ['MESH','CURVE']:continue
  ev=o.evaluated_get(bpy.context.evaluated_depsgraph_get());me=ev.to_mesh();me.calc_loop_triangles();off=len(vs);vs.extend(ev.matrix_world@v.co for v in me.vertices);fs.extend(tuple(off+i for i in t.vertices)for t in me.loop_triangles);ev.to_mesh_clear()
 return BVHTree.FromPolygons(vs,fs,all_triangles=True)
liner=bpy.data.objects['R82_Acoustic_Chamber_Liner'];stock=tree([liner]);exclude={'I_MoonlightStaff','I_CentralReadingLine','I_TipReadingRay_0','I_TipReadingRay_1','I_TipReadingRay_2'}
objects=set(bpy.data.objects['R82_COIL_ROOT'].children_recursive)|set(bpy.data.objects['IAM_MODULE'].children_recursive);block=tree([o for o in objects if o!=liner and o.name not in exclude])
nodes={int(k):v for k,v in plan['nodes'].items()};root=plan['root'];children={k:[]for k in nodes}
for k,row in nodes.items():
 if row['parent']is not None:children[row['parent']].append(k)
port_nodes={r['port']['node']for r in plan['routes']};critical={k for k in nodes if len(children[k])!=1 or k in port_nodes or k==root}
def smooth(points):
 if len(points)<3:return points
 result=[points[0]]
 for a,b in zip(points,points[1:]):result.extend([a*.75+b*.25,a*.25+b*.75])
 result.append(points[-1]);return result
def sample(uv):
 t,u=uv;p=surface.point(t,u);n=surface.normal(t,u);clear=block.find_nearest(p+n*.0045)[3];h=.0002;jt=(surface.point(t+h,u)-surface.point(t-h,u))/(2*h);ju=(surface.point(t,u+h)-surface.point(t,u-h))/(2*h)
 return {'t':t,'u':u,'p':list(p),'n':list(n),'jt':list(jt),'ju':list(ju),'clearance':clear,'stock_error':stock.find_nearest(p)[3]}
def shortcut(points):
 result=[points[0]];i=0
 while i<len(points)-1:
  chosen=i+1
  for j in range(len(points)-1,i+1,-1):
   count=max(2,math.ceil((points[j]-points[i]).length/.012))
   good=True
   for k in range(1,count):
    uv=points[i].lerp(points[j],k/count);p=surface.point(uv.x,uv.y);n=surface.normal(uv.x,uv.y)
    if stock.find_nearest(p)[3]>.0015 or block.find_nearest(p+n*.0045)[3]<.0065:good=False;break
   if good:chosen=j;break
  result.append(points[chosen]);i=chosen
 return result
def densify(points):
 result=[points[0]]
 for a,b in zip(points,points[1:]):
  count=max(1,math.ceil((a-b).length/.018))
  result.extend(a.lerp(b,k/count)for k in range(1,count+1))
 return result
segments=[];pending=[root];dist={root:0.}
for start in pending:
 for child in children[start]:
  chain=[start,child]
  while chain[-1]not in critical:chain.append(children[chain[-1]][0])
  end=chain[-1];pending.append(end);raw=[Vector((nodes[k]['t'],nodes[k]['u']))for k in chain];chosen=None
  if version=='r3':raw=shortcut(raw)
  for count in [2,1,0]:
   pts=raw
   for _ in range(count):pts=smooth(pts)
   if version=='r3':pts=densify(pts)
   samples=[sample(p)for p in pts]
   if all(p['stock_error']<.0015 and p['clearance']>.006 for p in samples):chosen=samples;break
  assert chosen is not None,(start,end)
  length=0.
  for i,p in enumerate(chosen):
   if i:length+=(Vector(p['p'])-Vector(chosen[i-1]['p'])).length
   p['distance']=dist[start]+length;p['width']=min(.014 if version=='r3' else .008,p['clearance']*.70);p['glass_radius']=min(.0024,p['width']*.30)
  dist[end]=dist[start]+length;segments.append({'id':len(segments),'start':start,'end':end,'samples':chosen,'length':length,'kind':'spine'});print('R90_SMOOTH_SEGMENT',start,end,len(chosen),flush=True)
ports=[]
for route in plan['routes']:
 node=route['port']['node'];c=spec['new_cells'][route['cell']]['surface_chart'];a=route['port']['angle'];s=1.10;t=c['t']+c['half_t']*s*(math.cos(a)+.1*math.sin(a)**2);u=c['u']+c['half_u']*s*math.sin(a)
 anchor=Vector(route['port']['anchor']);outward=Vector(route['port']['outward']);h=.0002;jt=(surface.point(t+h,u)-surface.point(t-h,u))/(2*h);ju=(surface.point(t,u+h)-surface.point(t,u-h))/(2*h);delta=outward*.0035
 aa=jt.dot(jt);bb=jt.dot(ju);cc=ju.dot(ju);dd=aa*cc-bb*bb;dt=(jt.dot(delta)*cc-ju.dot(delta)*bb)/dd;du=(ju.dot(delta)*aa-jt.dot(delta)*bb)/dd
 end=Vector((t+dt,u+du));start=Vector((nodes[node]['t'],nodes[node]['u']));samples=[];length=0.
 for i in range(17):
  f=i/16;p=sample(start.lerp(end,f));p['width']=min(.007,nodes[node]['clearance']*.70)*(1-f)+.0035*f;p['glass_radius']=.0020*(1-f)+.0012*f;p['height_scale']=1.-.5*f
  if i:length+=(Vector(p['p'])-Vector(samples[-1]['p'])).length
  p['distance']=dist[node]+length;samples.append(p)
 ports.append({**route['port'],'cell':route['cell'],'frame':route['frame'],'distance':dist[node]+length,'normal':list(surface.normal(t,u))})
 segments.append({'id':len(segments),'start':node,'end':'cell_'+str(route['cell']),'samples':samples,'length':length,'kind':'feed','cell':route['cell']})
# A trunk segment inherits the bands of every downstream cell.
for seg in segments:
 if seg['kind']=='feed':ids=[seg['cell']]
 else:
  ids=[]
  for route in plan['routes']:
   k=route['port']['node']
   while k is not None and k!=seg['end']:k=nodes[k]['parent']
   if k==seg['end']:ids.append(route['cell'])
 seg['cells']=ids;seg['bands']=sorted({spec['new_cells'][i]['band']for i in ids})
maxdist=max(p['distance']for p in ports)
for seg in segments:
 for p in seg['samples']:p['uv_distance']=p['distance']/maxdist
junctions=[]
for k in critical:
 p=sample(Vector((nodes[k]['t'],nodes[k]['u'])));p.update({'node':k,'radius':min(.013 if k==root or version=='r3' else .009,p['clearance']*.7),'distance':dist[k],'root':k==root});junctions.append(p)
(OUT/f'paths_{version}.json').write_text(json.dumps({'source_sha256':spec['source_sha256'],'root':root,'maximum_distance':maxdist,'segments':segments,'junctions':junctions,'ports':ports,'cells':[c['surface_chart']for c in spec['new_cells']],'scope':'Surface routes, fitted frame-face anchors and continuous source-to-cell physical-distance UV. Endpoint feed spans and final bodies still require actual geometry checks.'},indent=2)+'\n')
print('R90_PATHS_DONE',len(segments),len(junctions),maxdist,flush=True)
