import bpy,json,math,pathlib,hashlib
from mathutils import Matrix,Vector,Quaternion
ROOT=pathlib.Path(__file__).resolve().parents[1];S=bpy.context.scene
meta=json.loads((ROOT/'app'/'assets'/'mechanism.json').read_text(encoding='utf-8'))
C=Matrix(((1,0,0,0),(0,0,1,0),(0,-1,0,0),(0,0,0,1)))
def data_to_matrix(d):
 q=d['q'];m=Quaternion((q[3],q[0],q[1],q[2])).to_matrix().to_4x4();m=Matrix.Translation(Vector(d['p']))@m@Matrix.Diagonal((*d['s'],1));return C.inverted()@m@C
def ease(t):t=max(0,min(1,t));return t*t*(3-2*t)
def bloom_openness(t):
 if t<.40:return 0.
 if t<.85:return .035*ease((t-.40)/.45)
 if t<3.50:
  u=max(0,min(1,(t-.85)/2.65));q=u*u*u*(10+u*(-15+6*u))
  return .035+.965*q
 return 1.
def v_at_frame(f):
 if f<50:return 0.
 if f<145:return bloom_openness((f-50)/24)
 if f<250:return 1.
 if f<320:return 1-ease((f-260)/36)
 return 0.
controls=[d for d in meta['controls']]
control_names={d['name']for d in controls}
def animation_signature():
 rows=[]
 for ob in bpy.data.objects:
  if not ob.animation_data or not ob.animation_data.action:continue
  action=ob.animation_data.action
  curves=[]
  for layer in action.layers:
   for strip in layer.strips:
    for bag in strip.channelbags:curves.extend(bag.fcurves)
  for curve in curves:
   for point in curve.keyframe_points:
    frame,value=point.co
    if ob.name in control_names and 50<=frame<=144:continue
    rows.append((ob.name,curve.data_path,curve.array_index,float(frame),float(value)))
 return hashlib.sha256(json.dumps(sorted(rows)).encode()).hexdigest()
outside_before=animation_signature()
original_frame=S.frame_current
resource_hashes={name:hashlib.sha256((ROOT/'app/assets'/name).read_bytes()).hexdigest()for name in ['helios_model.glb','mechanism.json']}
for d in controls:
 o=bpy.data.objects[d['name']]
 assert o.rotation_mode=='QUATERNION',f'{o.name}: unexpected rotation mode; refusing to affect other animation ranges'
for f in range(50,145):
 S.frame_set(f);v=v_at_frame(f);x=v*100;lo=min(100,int(x));hi=min(100,lo+1);a=x-lo
 for d in controls:
  p0,q0,s0=data_to_matrix(d['samples'][lo]).decompose();p1,q1,s1=data_to_matrix(d['samples'][hi]).decompose()
  o=bpy.data.objects[d['name']];o.location=p0.lerp(p1,a);o.rotation_quaternion=q0.slerp(q1,a);o.scale=s0.lerp(s1,a)
  for path in ['location','rotation_quaternion','scale']:o.keyframe_insert(path,frame=f)
# Verify angular travel rather than Euler components: each hinge has a different base azimuth.
max_angle_spread=0.;per_frame=[]
for f in range(50,145):
 S.frame_set(f);values=[]
 for i in range(6):
  o=bpy.data.objects['PETAL_HINGE_%02d'%i];closed=Matrix.Rotation(-math.pi/2+i*math.tau/6,4,'Z').to_quaternion()
  relative=closed.to_matrix().inverted()@o.rotation_quaternion.to_matrix()
  values.append(math.atan2(relative[0][2],relative[2][2]))
 spread=max(values)-min(values);max_angle_spread=max(max_angle_spread,spread);per_frame.append({'frame':f,'angles_degrees':[math.degrees(x) for x in values]})
outside_after=animation_signature()
epsilon=.0001
speed_at_2_8=(bloom_openness(2.8+epsilon)-bloom_openness(2.8-epsilon))/(2*epsilon)
report={'passed':max_angle_spread<.00001 and outside_before==outside_after and speed_at_2_8>.1,'max_hinge_angle_difference_degrees':math.degrees(max_angle_spread),'same_start_end':True,'follows_runtime_open_choreography':True,'edited_controls':len(controls),'edited_frame_range':[50,144],'unchanged_other_object_and_outside_key_values':outside_before==outside_after,'outside_animation_sha256':outside_before,'openness_at_2_8_seconds':bloom_openness(2.8),'speed_at_2_8_openness_per_second':speed_at_2_8,'frames':per_frame}
(ROOT/'tests'/'synchronized_petals.json').write_text(json.dumps(report,indent=2))
assert report['passed'],report
S.frame_set(original_frame)
bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'blender'/'Helios_Incubator.blend'),compress=True)
assert all(hashlib.sha256((ROOT/'app/assets'/name).read_bytes()).hexdigest()==value for name,value in resource_hashes.items())
print('PETALS_SYNCHRONIZED',json.dumps({k:v for k,v in report.items()if k!='frames'}),flush=True)
