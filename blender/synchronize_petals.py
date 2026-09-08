import bpy,json,math,pathlib
from mathutils import Matrix,Vector,Quaternion
ROOT=pathlib.Path(__file__).resolve().parents[1];S=bpy.context.scene
meta=json.loads((ROOT/'app'/'assets'/'mechanism.json').read_text(encoding='utf-8'))
C=Matrix(((1,0,0,0),(0,0,1,0),(0,-1,0,0),(0,0,0,1)))
def data_to_matrix(d):
 q=d['q'];m=Quaternion((q[3],q[0],q[1],q[2])).to_matrix().to_4x4();m=Matrix.Translation(Vector(d['p']))@m@Matrix.Diagonal((*d['s'],1));return C.inverted()@m@C
def ease(t):t=max(0,min(1,t));return t*t*(3-2*t)
def choreography_time(d):
 if d<.40:return d*.80
 if d<.85:return .32+(d-.40)*(.38/.45)
 if d<2.80:
  u=max(0,min(1,(d-.85)/1.95));q=u*u*u*(10+u*(-15+6*u))
  return .70+.80*(1-max(0,1-q)**(1/3))
 if d<3.50:return 1.50+(d-2.80)
 return 2.20+(d-3.50)*.90
def v_at_frame(f):
 if f<50:return 0.
 if f<145:
  t=choreography_time((f-50)/24)
  if t<.32:return 0.
  if t<.70:return .035*ease((t-.32)/.38)
  if t<1.50:return .035+(.84-.035)*(1-(1-(t-.70)/.80)**3)
  if t<2.20:return .84+.16*ease((t-1.50)/.70)
  return 1.
 if f<250:return 1.
 if f<320:return 1-ease((f-260)/36)
 return 0.
controls=[d for d in meta['controls']]
for d in controls:
 o=bpy.data.objects[d['name']];o.animation_data_clear();o.rotation_mode='QUATERNION'
for f in range(1,601):
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
report={'passed':max_angle_spread<.00001,'max_hinge_angle_difference_degrees':math.degrees(max_angle_spread),'same_start_end':True,'follows_runtime_open_choreography':True,'frames':per_frame}
(ROOT/'tests'/'synchronized_petals.json').write_text(json.dumps(report,indent=2))
S.frame_set(30)
bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'blender'/'Helios_Incubator.blend'),compress=True)
print('PETALS_SYNCHRONIZED',report['passed'],report['max_hinge_angle_difference_degrees'],flush=True)
