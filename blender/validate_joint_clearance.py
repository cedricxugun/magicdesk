import bpy,json,math,pathlib
from mathutils import Matrix,Vector,Quaternion
from mathutils.bvhtree import BVHTree
ROOT=pathlib.Path(__file__).resolve().parents[1]
S=bpy.context.scene;S.frame_set(1)
meta=json.loads((ROOT/'app/assets/mechanism.json').read_text(encoding='utf-8'))
C=Matrix(((1,0,0,0),(0,0,1,0),(0,-1,0,0),(0,0,0,1)))
def tr(d):
 q=d['q'];return C.inverted()@Matrix.LocRotScale(Vector(d['p']),Quaternion((q[3],q[0],q[1],q[2])),Vector(d['s']))@C
for p in meta['parts']:bpy.data.objects[p['name']].matrix_basis=tr(p['home'])
turn=bpy.data.objects['TURNTABLE'];turn.rotation_euler=(0,0,0)
records=[];minimum=100;min_pivot=100;pair_errors=[];mesh_crossings=[]
shells=[bpy.data.objects.get('P_Petal_%02d_Enamel_DisplayMesh'%i) for i in range(6)]
if not all(shells):shells=[next(o for o in bpy.data.objects[p['name']].children if o.type=='MESH') for p in meta['parts'] if p['name'].endswith('_Enamel') and 'Petal' in p['name']]
for j in range(101):
 for c in meta['controls']:bpy.data.objects[c['name']].matrix_basis=tr(c['samples'][j])
 bpy.context.view_layer.update()
 verts=[];polys=[]
 for o in shells:
  offset=len(verts);verts.extend([o.matrix_world@v.co for v in o.data.vertices]);polys.extend([tuple(offset+k for k in po.vertices) for po in o.data.polygons])
 tree=BVHTree.FromPolygons(verts,polys,all_triangles=False)
 th=-math.pi/2;A=Vector((0,-1.25,.67))
 rod=bpy.data.objects['ACTUATOR_00_ROD'];B=rod.matrix_world@Vector((0,0,.3));d=B-A;L=d.length;u=d.normalized()
 barrel=bpy.data.objects['ACTUATOR_00_BARREL'];gland=barrel.matrix_world@Vector((0,0,.244*.65))
 # Fixed pivot to outer gland, sampled as a conservative capped cylinder.
 gaps=[]
 for k in range(41):
  x=.025+(.3086-.025)*k/40;pt=A+u*x
  nearest=tree.find_nearest(pt)
  if nearest:gaps.append(nearest[3]-.112)
 # The moving ram has tapered stages, with its largest radius at the base.
 for k in range(61):
  t=k/60;x=.10+(L-.10)*t;pt=A+u*x
  rad=.052 if t<.58 else .044 if t<.75 else .037
  nearest=tree.find_nearest(pt)
  if nearest:gaps.append(nearest[3]-rad)
 minimum=min(minimum,min(gaps));min_pivot=min(min_pivot,L)
 collisions=0
 for name in ['P_Actuator_00_Barrel','P_Actuator_00_Rod']:
  parent=bpy.data.objects[name]
  for ob in parent.children:
   if ob.type!='MESH':continue
   vt=[ob.matrix_world@v.co for v in ob.data.vertices];fc=[tuple(po.vertices) for po in ob.data.polygons]
   mechanism_tree=BVHTree.FromPolygons(vt,fc,all_triangles=False)
   collisions+=len(tree.overlap(mechanism_tree))
 mesh_crossings.append(collisions)
 records.append({'openness':j/100,'axis_distance':L,'barrel_to_upper_pivot':L-.3036,'min_shell_clearance':min(gaps),'triangle_intersections':collisions})
 # Every actual rod endpoint remains at the clevis axis in all six orientations.
 for i in range(6):
  hh=bpy.data.objects['PETAL_HINGE_%02d'%i]
  # The first endpoint establishes the shared local clevis socket.
  if j==0 and i==0:attach=hh.matrix_world.inverted()@B
  rr=bpy.data.objects['ACTUATOR_%02d_ROD'%i]
  end=rr.matrix_world@Vector((0,0,.3));target=hh.matrix_world@attach
  pair_errors.append((end-target).length)
report={'samples':101,'petals':6,'part_count':meta['part_count'],'minimum_shell_clearance':minimum,'minimum_pivot_distance':min_pivot,'maximum_endpoint_error':max(pair_errors),'actual_geometry_triangle_intersections':sum(mesh_crossings),'states':records,'passed':minimum>0 and max(pair_errors)<1e-5 and sum(mesh_crossings)==0}
(ROOT/'tests/joint_clearance.json').write_text(json.dumps(report,indent=2))
print('JOINT_CLEARANCE',json.dumps({k:v for k,v in report.items() if k!='states'}),flush=True)
