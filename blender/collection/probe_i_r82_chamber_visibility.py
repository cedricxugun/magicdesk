"""Visibility-guided resonator placement on the actual current open shell."""
import bpy,json,math,sys
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
R=Path(__file__).resolve().parents[2];sys.path.insert(0,str(Path(__file__).parent))
from i_r82_coil_surface import CoilSurface
CONCERT='--concert' in sys.argv
OUT=R/'review/I_refinement/nautilus_reset_r82'/('chambers_r2' if CONCERT else 'chambers_r1');OUT.mkdir(parents=True,exist_ok=True)
spec=json.loads((OUT/'mechanism.json').read_text()) if CONCERT else json.loads((R/'review/I_refinement/nautilus_reset_r82/music_interface_r1/installed_r5/build.json').read_text())
pars=json.loads((R/'review/I_refinement/nautilus_reset_r82/mechanism_r9/build.json').read_text())['shape_parameters'];surface=CoilSurface(pars)
bpy.ops.wm.open_mainfile(filepath=str(R/spec['source']));bpy.context.scene.frame_set(205);bpy.context.view_layer.update()
def collect(objects):
 vs=[];fs=[]
 for o in objects:
  if o.type not in ['MESH','CURVE']:continue
  ev=o.evaluated_get(bpy.context.evaluated_depsgraph_get());me=ev.to_mesh();me.calc_loop_triangles();off=len(vs)
  vs.extend(ev.matrix_world@v.co for v in me.vertices);fs.extend(tuple(off+i for i in t.vertices)for t in me.loop_triangles);ev.to_mesh_clear()
 return BVHTree.FromPolygons(vs,fs,all_triangles=True)
excluded={'R82_Acoustic_Chamber_Liner','I_MoonlightStaff','I_CentralReadingLine','I_TipReadingRay_0','I_TipReadingRay_1','I_TipReadingRay_2'}
objects=set(bpy.data.objects['R82_COIL_ROOT'].children_recursive)|set(bpy.data.objects['IAM_MODULE'].children_recursive)
occluders=collect([o for o in objects if o.name not in excluded])
stock=collect([bpy.data.objects['R82_Acoustic_Chamber_Liner']])
camera=Vector((-4,-7,3.65))
def visible(t,u):
 p=surface.point(t,u);normal=surface.normal(t,u)
 if normal.dot((camera-p).normalized())<.18:return False
 nearest=stock.find_nearest(p)
 if nearest[0] is None or nearest[3]>.004:return False
 start=p+normal*.003;direction=camera-start
 return occluders.ray_cast(start,direction.normalized(),direction.length)[0] is None
rows=[]
for i in range(80 if CONCERT else 75):
 t=surface.T-8.0+i*.10
 for j in range(15):
  u=.44+j*.16
  dt=.28 if CONCERT else .18;du=.40 if CONCERT else .28
  if t+dt*1.16>surface.T-.015:continue
  if u+du*1.16>math.pi-.07:continue
  checks=[(0,0)]+[(math.cos(math.tau*k/12),math.sin(math.tau*k/12))for k in range(12)]
  if any(stock.find_nearest(surface.point(t+dt*x*1.16,u+du*y*1.16))[3]>.004 for x,y in checks):continue
  score=sum(visible(t+dt*x,u+du*y)for x,y in checks)/len(checks)
  if score<.30:continue
  r=surface.frame(t)[0]
  rows.append({'t':t,'u':u,'half_t':dt,'half_u':du,'visibility':score,'radius':r,'centre':list(surface.point(t,u))})
selected=[]
# Pick across the growing outer turn, with spacing in the surface chart.
gap_t=.66 if CONCERT else .43;gap_u=.94 if CONCERT else .65
for sector in range(6):
 low=surface.T-7.8+sector*1.25;high=low+1.25
 options=[r for r in rows if low<=r['t']<high]
 for unused in range(2):
  options=[r for r in options if all(((r['t']-p['t'])/gap_t)**2+((r['u']-p['u'])/gap_u)**2>1 for p in selected)]
  if not options:break
  best=max(options,key=lambda r:r['visibility']+.05*min(r['radius'],.8))
  selected.append(best)
for row in sorted(rows,key=lambda r:r['visibility']+.05*r['radius'],reverse=True):
 if len(selected)>=12:break
 if all(((row['t']-p['t'])/(gap_t+.02))**2+((row['u']-p['u'])/(gap_u+.02))**2>1 for p in selected):selected.append(row)
(OUT/'visibility.json').write_text(json.dumps({'source':spec['source'],'source_sha256':spec['source_sha256'],'frame':205,'camera':list(camera),'candidates':rows,'selected':selected,'scope':'Actual open-pose camera occlusion and existing liner location. This is placement evidence only, not cell collision or final visibility across rotation.'},indent=2)+'\n')
print('VISIBLE_PATCHES',len(rows),'SELECTED',len(selected),flush=True)
for row in selected:print({k:v for k,v in row.items()if k!='centre'},flush=True)
