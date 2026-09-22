"""A surface-fitted rooted connection tree around actual R89 apertures.
Routing evidence only; final swept meshes need their own contact checks."""
import bpy,json,math,sys,heapq,hashlib
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
R=Path(__file__).resolve().parents[2];sys.path.insert(0,str(Path(__file__).parent))
from i_formed_coil_surface import FormedCoilSurface
BASE=R/'review/I_refinement/nautilus_reset_r82';OUT=BASE/'network_r90';OUT.mkdir(exist_ok=True)
visible_priority='--visible' in sys.argv
spec=json.loads((BASE/'chambers_r89/built_r3/build.json').read_text());assert hashlib.sha256((R/spec['source']).read_bytes()).hexdigest()==spec['source_sha256']
bpy.ops.wm.open_mainfile(filepath=str(R/spec['source']));scene=bpy.context.scene;scene.frame_set(1);bpy.context.view_layer.update()
surface=FormedCoilSurface(json.loads((BASE/'mechanism_r9/build.json').read_text())['shape_parameters'],bpy.data.objects['IAM_Mouth'].matrix_world.inverted(),spec['formed_liner_return'])
def tree(objects):
 vs=[];fs=[]
 for o in objects:
  if o.type not in ['MESH','CURVE']:continue
  ev=o.evaluated_get(bpy.context.evaluated_depsgraph_get());me=ev.to_mesh();me.calc_loop_triangles();off=len(vs);vs.extend(ev.matrix_world@v.co for v in me.vertices);fs.extend(tuple(off+i for i in t.vertices)for t in me.loop_triangles);ev.to_mesh_clear()
 return BVHTree.FromPolygons(vs,fs,all_triangles=True)
liner=bpy.data.objects['R82_Acoustic_Chamber_Liner'];stock=tree([liner]);exclude={'I_MoonlightStaff','I_CentralReadingLine','I_TipReadingRay_0','I_TipReadingRay_1','I_TipReadingRay_2'}
objects=set(bpy.data.objects['R82_COIL_ROOT'].children_recursive)|set(bpy.data.objects['IAM_MODULE'].children_recursive)
block=tree([o for o in objects if o!=liner and o.name not in exclude])
ta=6.6;tb=surface.T-.10;ua=.10;ub=math.pi-.10;step=.025;nt=round((tb-ta)/step);nu=round((ub-ua)/step)
grid={};lookup={}
for i in range(nt+1):
 t=ta+(tb-ta)*i/nt
 for j in range(nu+1):
  u=ua+(ub-ua)*j/nu;p=surface.point(t,u);n=surface.normal(t,u)
  if stock.find_nearest(p)[3]>.0015:continue
  clearance=block.find_nearest(p+n*.0045)[3]
  if clearance<.007:continue
  key=i*(nu+1)+j;grid[key]={'t':t,'u':u,'p':p,'n':n,'clearance':clearance};lookup[(i,j)]=key
 if i%40==0:print('R90_GRID',i,len(grid),flush=True)
assert grid
scene.frame_set(205);bpy.context.view_layer.update();visible_tree=tree([o for o in objects if o.name not in exclude]);view=(Vector((-4,-7,3.65))-Vector((0,0,1.57))).normalized()
for row in grid.values():row['visible']=row['n'].dot(view)>.10 and visible_tree.ray_cast(row['p']+row['n']*.008,view,20)[0] is None
desired=surface.point(14.46,.50) if visible_priority else surface.point(14.02,1.44)
root=min((k for k in grid if grid[k]['clearance']>(.014 if visible_priority else .018) and (grid[k]['visible']or not visible_priority)),key=lambda k:(grid[k]['p']-desired).length)
print('R90_ROOT_CHOICE',grid[root]['t'],grid[root]['u'],(grid[root]['p']-desired).length,grid[root]['clearance'],flush=True)
assert (grid[root]['p']-desired).length<.15
ports=[]
for c in spec['new_cells']:
 chart=c['surface_chart'];frame=bpy.data.objects[c['frame']];options=[]
 for k in range(24):
  index=k*4;ids=[index,(index+1)%96,96+(index+1)%96,96+index];v=[frame.matrix_world@frame.data.vertices[x].co for x in ids]
  anchor=(v[0]+v[2])/2;outward=(v[1]-v[0]).cross(v[3]-v[0]).normalized();centre=surface.point(chart['t'],chart['u'])
  if outward.dot(anchor-centre)<0:outward=-outward
  a=math.tau*(index+.5)/96
  desired=anchor+outward*.018
  # Nearby atlas nodes around this rim sector, followed by physical distance.
  t=chart['t']+chart['half_t']*1.25*(math.cos(a)+.1*math.sin(a)**2);u=chart['u']+chart['half_u']*1.25*math.sin(a)
  ii=round((t-ta)/(tb-ta)*nt);jj=round((u-ua)/(ub-ua)*nu);local=[]
  for di in range(-5,6):
   for dj in range(-5,6):
    node=lookup.get((ii+di,jj+dj))
    if node is not None:
     distance=(grid[node]['p']+grid[node]['n']*.003-anchor).length
     if .008<distance<.065 and (grid[node]['p']-anchor).dot(outward)>0:local.append((node,distance))
  if local:
   node,distance=min(local,key=lambda x:(grid[x[0]]['p']-desired).length)
   normal=surface.normal(c['surface_chart']['t'],c['surface_chart']['u']) if 'surface_chart'in c else surface.normal(chart['t'],chart['u'])
   port_visible=visible_tree.ray_cast(anchor+normal*.010+outward*.002,view,20)[0] is None
   options.append({'node':node,'anchor':list(anchor),'outward':list(outward),'angle':a,'distance':distance,'visible':port_visible})
 assert options,c['frame']
 ports.append({'cell':c['cell_index'],'frame':c['frame'],'options':options})
parent={root:None};distance={root:0.};tree_nodes={root};routes=[]
neighbors=[(a,b)for a in [-1,0,1]for b in [-1,0,1]if a or b]
# Inner destination first creates the main spine; later cells attach to it.
for port in ports:
 targets={x['node']:x for x in sorted(port['options'],key=lambda x:x.get('visible',False))};cost={x:0. for x in tree_nodes};previous={};queue=[(0.,x)for x in tree_nodes];heapq.heapify(queue);found=None;best=float('inf')
 while queue:
  value,node=heapq.heappop(queue)
  if value!=cost[node]:continue
  if value>=best:break
  if node in targets:
   terminal=value+(.35 if visible_priority and not targets[node]['visible'] else 0.)
   if terminal<best:found=node;best=terminal
   if not visible_priority:break
  i,j=divmod(node,nu+1)
  for di,dj in neighbors:
   other=lookup.get((i+di,j+dj))
   if other is None:continue
   if di and dj and ((i+di,j)not in lookup or(i,j+dj)not in lookup):continue
   length=(grid[node]['p']-grid[other]['p']).length;clear=min(grid[node]['clearance'],grid[other]['clearance']);visibility_cost=1.+(3. if visible_priority and not(grid[node]['visible']and grid[other]['visible'])else 0.);candidate=value+length*(1.+.015/(clear+.003))*visibility_cost
   if candidate<cost.get(other,float('inf')):cost[other]=candidate;previous[other]=node;heapq.heappush(queue,(candidate,other))
 assert found is not None,port['frame']
 chain=[found]
 while chain[-1]not in tree_nodes:chain.append(previous[chain[-1]])
 chain.reverse()
 for a,b in zip(chain,chain[1:]):parent[b]=a;distance[b]=distance[a]+(grid[a]['p']-grid[b]['p']).length;tree_nodes.add(b)
 endpoint=targets[found];routes.append({'cell':port['cell'],'frame':port['frame'],'nodes':chain,'port':endpoint})
 print('R90_ROUTE',port['cell'],len(chain),distance[found],flush=True)
nodes={str(k):{'t':grid[k]['t'],'u':grid[k]['u'],'point':list(grid[k]['p']),'normal':list(grid[k]['n']),'clearance':grid[k]['clearance'],'visible':grid[k]['visible'],'distance':distance[k],'parent':parent[k]}for k in tree_nodes}
(OUT/('routing_r2.json'if visible_priority else 'routing_r1.json')).write_text(json.dumps({'source':spec['source'],'source_sha256':spec['source_sha256'],'root':root,'nodes':nodes,'routes':routes,'scope':'Closed-source actual liner/obstacle clearance; optional actual-open-view visibility cost and frame port preference. Rooted atlas routing only, not final mesh/dynamic/junction/art acceptance.'},indent=2)+'\n');print('R90_ROUTING_DONE',len(nodes),flush=True)
