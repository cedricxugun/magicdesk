import bpy,json,pathlib
from mathutils import Vector
from mathutils.bvhtree import BVHTree
ROOT=pathlib.Path(__file__).resolve().parents[1];S=bpy.context.scene
S.frame_set(1);bpy.context.view_layer.update()
h=bpy.data.objects['PETAL_HINGE_00'];r=bpy.data.objects['ACTUATOR_00_ROD'];attach=h.matrix_world.inverted()@(r.matrix_world@Vector((0,0,.3)))
names=['P_Petal_%02d_Enamel'%i for i in range(6)]
meshes=[]
for name in names:meshes.extend([o for o in bpy.data.objects[name].children if o.type=='MESH'])
records=[];errors=[]
for frame in range(50,151,3):
 S.frame_set(frame);bpy.context.view_layer.update()
 vv=[];pp=[]
 for o in meshes:
  off=len(vv);vv.extend([o.matrix_world@v.co for v in o.data.vertices]);pp.extend([tuple(off+k for k in p.vertices) for p in o.data.polygons])
 shell=BVHTree.FromPolygons(vv,pp);count=0
 for i in range(6):
  h=bpy.data.objects['PETAL_HINGE_%02d'%i];r=bpy.data.objects['ACTUATOR_%02d_ROD'%i]
  errors.append(((h.matrix_world@attach)-(r.matrix_world@Vector((0,0,.3)))).length)
  for group in ['P_Actuator_%02d_Barrel'%i,'P_Actuator_%02d_Rod'%i]:
   for o in bpy.data.objects[group].children:
    if o.type!='MESH':continue
    bv=BVHTree.FromPolygons([o.matrix_world@v.co for v in o.data.vertices],[tuple(p.vertices) for p in o.data.polygons])
    count+=len(shell.overlap(bv))
 records.append({'frame':frame,'triangle_intersections':count})
report={'frames_sampled':len(records),'actuators':6,'maximum_joint_animation_error':max(errors),'total_triangle_intersections':sum(x['triangle_intersections'] for x in records),'states':records,'passed':max(errors)<.001 and sum(x['triangle_intersections'] for x in records)==0}
(ROOT/'tests/animation_sweep.json').write_text(json.dumps(report,indent=2));print('ANIMATION_SWEEP',json.dumps({k:v for k,v in report.items() if k!='states'}),flush=True)
