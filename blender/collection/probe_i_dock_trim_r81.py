import bpy,math,json,sys,collections
from pathlib import Path
from mathutils import Matrix
from mathutils.bvhtree import BVHTree
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(Path(__file__).parent))
import i_machined_geometry as h
import i_trunnion_support_geometry as g
import i_dock_fitted_r79 as fit
import i_fitted_surface as ext
OUT=ROOT/'review/I_refinement/nautilus_r1/base_dock_r80'
s=json.loads((ROOT/'review/I_refinement/nautilus_r1/coupling_repair_r76/build.json').read_text());bpy.ops.wm.open_mainfile(filepath=str(ROOT/s['source']));bpy.context.scene.frame_set(1)
col=bpy.data.collections.new('DockLipProbe');bpy.context.scene.collection.children.link(col);h.configure(col);root=h.empty('ProbeRoot',None);root.matrix_world=Matrix.Identity(4)
def tree(objects):
 v=[];f=[];names=[]
 for o in objects:
  o.data.calc_loop_triangles();off=len(v);v.extend(o.matrix_world@p.co for p in o.data.vertices);f.extend(tuple(off+i for i in t.vertices) for t in o.data.loop_triangles);names.extend([o.name]*len(o.data.loop_triangles))
 return BVHTree.FromPolygons(v,f,all_triangles=True),names
allmeshes=[o for o in bpy.data.objects if o.type=='MESH' and not o.name.startswith(('IN1_FittedSaddle','IN1_LowSaddle')) and o.name!='IN1_PorcelainPanel_02']
other,names=tree(allmeshes);rows=[]
for r in [.043,.042,.041,.0405]:
 pts,faces,edges=fit.surface(bpy.data.objects['IN1_PorcelainPanel_02'],[(.26+r*math.cos(i*math.tau/64),.10+r*math.sin(i*math.tau/64)) for i in range(64)])
 vv,ff=ext.extruded_patch(pts,faces,edges,-.0006,bottom_offset=-.0048)
 lip=g.own('ProbeLip',vv,ff,root,'A_Nickel');h.drill(lip,.035,.7,root,(.26,.10,1.))
 t,_=tree([lip]);contacts=dict(collections.Counter(names[b] for a,b in t.overlap(other)));rows.append({'outer_radius':r,'contacts':contacts});print(rows[-1],flush=True)
 bpy.data.objects.remove(lip,do_unlink=True)
(OUT/'lip_trim_probe.json').write_text(json.dumps(rows,indent=2)+'\n')
