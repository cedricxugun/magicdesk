"""Larger graduated resonators using the actual R88 opening/projection.
Only layout evidence; model contacts and final art remain separate gates."""
import bpy,json,math,sys,hashlib
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
R=Path(__file__).resolve().parents[2];sys.path.insert(0,str(Path(__file__).parent))
from i_r82_coil_surface import CoilSurface
OUT=R/'review/I_refinement/nautilus_reset_r82/chambers_r89';OUT.mkdir(exist_ok=True)
fill_treble='--fill-treble' in sys.argv
spec=json.loads((R/'review/I_refinement/nautilus_reset_r82/back_hardware_r88/built_r4/build.json').read_text());assert hashlib.sha256((R/spec['source']).read_bytes()).hexdigest()==spec['source_sha256']
surface=CoilSurface(json.loads((R/'review/I_refinement/nautilus_reset_r82/mechanism_r9/build.json').read_text())['shape_parameters'])
bpy.ops.wm.open_mainfile(filepath=str(R/spec['source']));scene=bpy.context.scene;scene.frame_set(205);bpy.context.view_layer.update()
excluded={'R82_Acoustic_Chamber_Liner','I_MoonlightStaff','I_CentralReadingLine','I_TipReadingRay_0','I_TipReadingRay_1','I_TipReadingRay_2'}
objects=set(bpy.data.objects['R82_COIL_ROOT'].children_recursive)|set(bpy.data.objects['IAM_MODULE'].children_recursive)
vs=[];fs=[]
for o in objects:
 if o.type not in ['MESH','CURVE'] or o.name in excluded or o.name.startswith('I84_Cell_'):continue
 ev=o.evaluated_get(bpy.context.evaluated_depsgraph_get());me=ev.to_mesh();me.calc_loop_triangles();off=len(vs);vs.extend(ev.matrix_world@v.co for v in me.vertices);fs.extend(tuple(off+i for i in t.vertices)for t in me.loop_triangles);ev.to_mesh_clear()
occluders=BVHTree.FromPolygons(vs,fs,all_triangles=True);inv=bpy.data.objects['IAM_Mouth'].matrix_world.inverted();view=(Vector((-4,-7,3.65))-Vector((0,0,1.57))).normalized()
profile=spec['liner_receiver_profile'];sector=spec['receiver_sector_clearance']
def smooth(a,b,x):
 x=max(0.,min(1.,(x-a)/(b-a)));return x*x*(3-2*x)
def receiver_cut(p):
 local=inv@p;z=local.z;radius=math.hypot(local.x,local.y)
 for (za,ra),(zb,rb)in zip(profile,profile[1:]):
  if za<=z<=zb:
   r=ra+(rb-ra)*(z-za)/(zb-za);angle=math.atan2(local.y,local.x);aa,ab,ac,ad=sector['angle'];da,db,dc,dd=sector['depth'];w=smooth(aa,ab,angle)*(1-smooth(ac,ad,angle))*smooth(da,db,z)*(1-smooth(dc,dd,z));r+=(min(r,sector['radius'])-r)*w
   return radius<r+.014
 return False
checks=[(0.,0.)]+[(s*math.cos(math.tau*k/16),s*math.sin(math.tau*k/16))for s in [.48,.93]for k in range(16)]
def metrics(c):
 visible=0
 for x,y in checks:
  t=c['t']+c['half_t']*(x+.1*y*y);u=c['u']+c['half_u']*y;p=surface.point(t,u);n=surface.normal(t,u)
  if n.dot(view)>.12 and occluders.ray_cast(p+n*.003,view,20)[0]is None:visible+=1
 fraction=visible/len(checks);t=c['t'];u=c['u'];h=.001;dt=(surface.point(t+h,u)-surface.point(t-h,u))/(2*h);du=(surface.point(t,u+h)-surface.point(t,u-h))/(2*h)
 return fraction,math.pi*c['half_t']*c['half_u']*abs(dt.cross(du).dot(view))
rows=[]
for i in range(67 if fill_treble else 57):
 t=surface.T-(9.6 if fill_treble else 8.2)+i*.14
 for j in range(15):
  u=.42+j*.16
  for ht,hu in ([(.20,.32)]+[(.28,.42),(.36,.56),(.44,.68)] if fill_treble else [(.28,.42),(.36,.56),(.44,.68)]):
   if t+ht*1.15>surface.T-.09 or u-hu*1.15<.075 or u+hu*1.15>math.pi-.075:continue
   ring=[surface.point(t+ht*1.15*(math.cos(a)+.1*math.sin(a)**2),u+hu*1.15*math.sin(a))for a in [math.tau*k/24 for k in range(24)]]
   if any(receiver_cut(p)for p in ring):continue
   c={'t':t,'u':u,'half_t':ht,'half_u':hu,'radius':surface.frame(t)[0]};vis,area=metrics(c)
   if vis<(.35 if ht==.20 else .58):continue
   c.update({'visibility':vis,'projected_area':area,'score':area*vis*vis,'centre':list(surface.point(t,u))});rows.append(c)
 print('R89_LAYOUT_ROWS',i,len(rows),flush=True)
def separate(a,b):
 return ((a['t']-b['t'])/((a['half_t']+b['half_t'])*1.15+.035))**2+((a['u']-b['u'])/((a['half_u']+b['half_u'])*1.15+.045))**2>1.06
selected=json.loads((OUT/'layout_r1.json').read_text())['selected'] if fill_treble else []
# Outer-to-inner prioritization prevents small high-visibility cells consuming
# the most useful large outer acoustic areas.
for sector_index in ([] if fill_treble else range(5,-1,-1)):
 low=surface.T-8.15+sector_index*1.31;high=low+1.31
 options=[x for x in rows if low<=x['t']<high]
 for slot in range(2):
  valid=[x for x in options if all(separate(x,y)for y in selected)]
  if not valid:break
  selected.append(max(valid,key=lambda x:x['score']))
for c in sorted(rows,key=lambda x:x['score'],reverse=True):
 if len(selected)>=12:break
 if all(separate(c,y)for y in selected):selected.append(c)
selected.sort(key=lambda x:x['t']);baseline=[]
for row in spec['new_cells']:
 c=row['surface_chart'];v,a=metrics(c);baseline.append({'visibility':v,'projected_area':a,'visible_area':a*v})
report={'source':spec['source'],'source_sha256':spec['source_sha256'],'selected':selected,'candidates':rows,'baseline':baseline,'new_visible_area':sum(x['projected_area']*x['visibility']for x in selected),'old_visible_area':sum(x['visible_area']for x in baseline),'scope':'Orthographic actual-open-pose occlusion from R88; excludes old cells and replaces old apertures conceptually. Uses physical receiver exclusion and chart spacing. Not model contact/animation/source fit or art approval.'}
(OUT/('layout_r2.json' if fill_treble else 'layout_r1.json')).write_text(json.dumps(report,indent=2)+'\n');print('R89_LAYOUT_SELECTED',len(selected),report['old_visible_area'],report['new_visible_area'],flush=True)
if fill_treble:
 selected_report={k:v for k,v in report.items()if k!='candidates'};selected_report['candidate_count']=len(rows)
 (OUT/'layout_selected.json').write_text(json.dumps(selected_report,indent=2)+'\n')
assert len(selected)==12
