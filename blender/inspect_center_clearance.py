import bpy,json,pathlib,math
from mathutils import Matrix,Vector,Quaternion
from mathutils.bvhtree import BVHTree
ROOT=pathlib.Path(__file__).resolve().parents[1];M=json.loads((ROOT/'app/assets/mechanism.json').read_text(encoding='utf8'));S=bpy.context.scene;S.frame_set(1)
C=Matrix(((1,0,0,0),(0,0,1,0),(0,-1,0,0),(0,0,0,1)))
def tr(d):
 q=d['q'];return C.inverted()@Matrix.LocRotScale(Vector(d['p']),Quaternion((q[3],q[0],q[1],q[2])),Vector(d['s']))@C
def pose(op,phase,explode):
 for c in M['controls']:bpy.data.objects[c['name']].matrix_basis=tr(c['samples'][round(op*100)])
 for p in M['parts']:bpy.data.objects[p['name']].matrix_basis=tr(p['home'])
 bpy.data.objects['TURNTABLE'].rotation_euler=(0,0,0)
 for n,a,axis in [('GYRO_OUTER',.2+phase*.65,2),('GYRO_MIDDLE',.6+math.sin(phase*.55)*.9,0),('GYRO_INNER',.7+phase,2),('CORE_ROTOR',phase*.8,0)]:
  o=bpy.data.objects[n];o.rotation_mode='XYZ';o.rotation_euler=(0,0,0);o.rotation_euler[axis]=a
 bpy.context.view_layer.update()
 for p in M['parts']:
  u=max(0,min(1,(explode-p['stage'])/.7));u=u*u*(3-2*u);o=bpy.data.objects[p['name']];off=C.inverted().to_3x3()@Vector(p['offset']);base=tr(p['home']);loc,rot,sc=base.decompose()
  o.location=loc+o.parent.matrix_world.to_3x3().inverted()@off*u;o.rotation_mode='QUATERNION';o.rotation_quaternion=rot@Quaternion((0,0,1),p['spin']*u);o.scale=sc
 bpy.context.view_layer.update()
def tree(name,material=None):
 verts=[];faces=[]
 for o in bpy.data.objects[name].children_recursive:
  if o.type!='MESH':continue
  ids=[]
  for p in o.data.polygons:
   ma=o.material_slots[p.material_index].material
   if material and material not in ma.name:continue
   face=[]
   for ix in p.vertices:face.append(len(verts));verts.append(o.matrix_world@o.data.vertices[ix].co)
   faces.append(tuple(face))
 return BVHTree.FromPolygons(verts,faces),verts
names=[p['name']for p in M['parts'] if any(x in p['name']for x in ['Gimbal','Trunnion','Solar','Support','Bottom_Bearing','Thermal','Stator','Socket'])]
pose(1,0,0)
for name in ['P_Thermal_Valve_1','P_Thermal_Valve_2']:
 _,v=tree(name,'Ivory')
 g=[C.to_3x3()@p for p in v]
 print('PORCELAIN',name,'GodotBounds',tuple(round(min(p[i]for p in g),4)for i in range(3)),tuple(round(max(p[i]for p in g),4)for i in range(3)),flush=True)
rows=[]
for op,phase,ex in [(0,0,0),(1,0,0),(1,2,0),(0,2,.5),(0,2,1)]:
 pose(op,phase,ex);trees={n:tree(n)[0]for n in names};pairs=[]
 for i,a in enumerate(names):
  for b in names[i+1:]:
   count=len(trees[a].overlap(trees[b]))
   if count:pairs.append([a,b,count])
 rows.append({'open':op,'phase':phase,'explosion':ex,'pairs':pairs})
 print('COLLISIONS',op,phase,ex,pairs,flush=True)
(ROOT/'tests/center_collision_before.json').write_text(json.dumps(rows,indent=2))
