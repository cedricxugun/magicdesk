"""Compare an outer-edge hinge interpretation against the concert middle-hinge
study. Geometry-only diagnostic; existing actuator hardware is not claimed fitted."""
import bpy,json,math,sys
from pathlib import Path
from mathutils import Vector,Matrix,Quaternion
from mathutils.bvhtree import BVHTree
R=Path(__file__).resolve().parents[2];sys.path.insert(0,str(Path(__file__).parent))
from i_r82_coil_surface import CoilSurface
OUT=R/'review/I_refinement/nautilus_reset_r82/chambers_r3/hinge_study';OUT.mkdir(exist_ok=True)
spec=json.loads((OUT.parent/'build.json').read_text());old=json.loads((R/'review/I_refinement/nautilus_reset_r82/mechanism_r9/build.json').read_text());surface=CoilSurface(old['shape_parameters'])
bpy.ops.wm.open_mainfile(filepath=str(R/spec['source']));scene=bpy.context.scene;scene.frame_set(1)
def raw(o,relative=None):
 ev=o.evaluated_get(bpy.context.evaluated_depsgraph_get());me=ev.to_mesh();me.calc_loop_triangles()
 M=ev.matrix_world if relative is None else relative@ev.matrix_world
 vs=[M@v.co for v in me.vertices];tri=[tuple(t.vertices)for t in me.loop_triangles];ev.to_mesh_clear();return vs,tri
def tree(vs,tri):
 return BVHTree.FromPolygons(vs,tri,all_triangles=True),[min(v[k]for v in vs)for k in range(3)],[max(v[k]for v in vs)for k in range(3)]
def hit(a,b):return all(a[1][k]<=b[2][k]and b[1][k]<=a[2][k]for k in range(3)) and bool(a[0].overlap(b[0]))
parts=[]
for p in spec['panels']:
 node=bpy.data.objects[p['node']];ob=bpy.data.objects[p['mesh']]
 vs,tri=raw(ob,node.matrix_world.inverted())
 tm=(p['ta']+p['tb'])/2;newp=surface.point(tm,.02,-.023)
 parts.append((p,vs,tri,newp))
fixed=[tree(*raw(o))for o in bpy.data.objects if o.name.startswith('I84_Cell_')and o.type=='MESH']
results=[];winner=None
for deg,depth,radial_offset in [(45.,.06,.02),(45.,.06,.04),(45.,.10,.04),(55.,.10,.05)]:
 contacts=0;poses=[];pairs=[]
 for phase in [i/40 for i in range(41)]:
  tc=min(1.,phase/.25);tr=max(0.,(phase-.25)/.75);tr=tr*tr*(3-2*tr);shapes=[];matrices=[]
  for p,vs,tri,pivot in parts:
   if p['id']==1:
    base=old['panels'][0];pivot=Vector(base['pivot']);D=Vector(base['translation']);angle=base['angle']
   else:
    tm=(p['ta']+p['tb'])/2;radial=surface.frame(tm)[1]
    D=Vector((0,-depth,0))+radial*radial_offset;angle=math.radians(deg)
   rot=Quaternion(Vector(p['axis']),angle*tr).to_matrix().to_4x4()
   M=Matrix.Translation(pivot+D*tc)@rot@Matrix.Translation(Vector(p['pivot'])-pivot)
   matrices.append(M);shapes.append(tree([M@v for v in vs],tri))
  for i,a in enumerate(shapes):
   for j,b in enumerate(shapes[i+1:],i+1):
    if hit(a,b):contacts+=1;pairs.append({'phase':phase,'cover':i+1,'other_cover':j+1})
   for j,b in enumerate(fixed):
    if hit(a,b):contacts+=1;pairs.append({'phase':phase,'cover':i+1,'cell_mesh_index':j})
  if phase==1.:poses=matrices
  if contacts:break
 row={'degrees':deg,'unseat':depth,'radial_offset':radial_offset,'contact_pair_states':contacts,'first_contacts':pairs};results.append(row);print('HINGE_STUDY',row,flush=True)
 if not contacts:winner=(row,poses);break
(OUT/'study_release.json').write_text(json.dumps({'results':results,'selected':winner[0] if winner else None,'scope':'41-phase ceramic/cell and ceramic/ceramic surface checks only, existing actuator hardware not fitted. Outer-edge hinge with slight radial release, not accepted design.'},indent=2)+'\n')
if winner:
 for (p,*_),M in zip(parts,winner[1]):
  node=bpy.data.objects[p['node']];node.animation_data_clear();node.matrix_world=M
 # Hide obsolete actuator hardware for the explicitly labelled geometry-only study.
 for ob in bpy.data.objects:
  if ob.name.startswith(('R82_R3_Guide_','R82_R3_Slider_','R82_R3_Crosshead_','R82_R3_Rotating_Pin_','R82_R3_Pin_Stop_','R82_R5_Short_Rotor','R82_R5_Cover_Pad','I84_Extension')):ob.hide_render=True
 try:
  pref=bpy.context.preferences.addons['cycles'].preferences;pref.compute_device_type='CUDA';pref.get_devices()
  for dv in pref.devices:dv.use=dv.type=='CUDA'
  scene.cycles.device='GPU'
 except:pass
 scene.cycles.samples=40;scene.render.resolution_x=1000;scene.render.resolution_y=1100
 scene.render.filepath=str(OUT/'outer_hinge_release_geometry_only.png');bpy.ops.render.render(write_still=True)
