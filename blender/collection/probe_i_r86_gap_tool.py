"""Locate the visible gap on the uncut analytic liner and compare the receiving tool."""
import bpy,json,math,sys
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
R=Path(__file__).resolve().parents[2];sys.path.insert(0,str(Path(__file__).parent))
from i_r82_coil_surface import CoilSurface
OUT=R/'review/I_refinement/nautilus_reset_r82/finish_r86'
args=sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else []
extended='--extended' in args
spec=json.loads((R/'review/I_refinement/nautilus_reset_r82/outer_hinge_r2/build.json').read_text())
pars=json.loads((R/'review/I_refinement/nautilus_reset_r82/mechanism_r9/build.json').read_text())['shape_parameters'];surf=CoilSurface(pars)
bpy.ops.wm.open_mainfile(filepath=str(R/spec['source']));s=bpy.context.scene;s.frame_set(205);s.render.resolution_x=1000;s.render.resolution_y=1100;bpy.context.view_layer.update()
vs=[];fs=[];NT=600;NU=96
for i in range(NT+1):
 t=.01+(surf.T-.01)*i/NT
 for j in range(NU+1):vs.append(surf.point(t,.06+(math.pi-.12)*j/NU))
for i in range(NT):
 for j in range(NU):
  k=i*(NU+1)+j;fs.append((k,k+1,k+NU+2,k+NU+1))
tree=BVHTree.FromPolygons(vs,fs)
cam=s.camera;frame=cam.data.view_frame(scene=s);xmin=min(p.x for p in frame);xmax=max(p.x for p in frame);ymin=min(p.y for p in frame);ymax=max(p.y for p in frame);direction=cam.matrix_world.to_quaternion()@Vector((0,0,-1))
inv=bpy.data.objects['IAM_Mouth'].matrix_world.inverted();rows=[]
profile=[(-.16,.851),(-.09,.851),(.20,.873),(.24,.880),(.43,.858),(.48,.62),(.62,.50)]
for x,y in ([(313,598),(311,614),(319,627),(310,590),(320,610),(309,624),(312,633),(316,619)] if extended else [(327,578),(330,588),(337,572),(345,577),(360,548)]):
 origin=cam.matrix_world@Vector((xmin+(x+.5)/1000*(xmax-xmin),ymax-(y+.5)/1100*(ymax-ymin),0))
 p,n,idx,dist=tree.ray_cast(origin,direction,30)
 if p is None:continue
 local=inv@p;radius=(local.x**2+local.y**2)**.5;cutradius=None
 for (za,ra),(zb,rb)in zip(profile,profile[1:]):
  if za<=local.z<=zb:cutradius=ra+(rb-ra)*(local.z-za)/(zb-za)
 # Face index comes from the regular chart; get an approximate chart address.
 ti=idx//NU;ui=idx%NU;t=.01+(surf.T-.01)*(ti+.5)/NT;u=.06+(math.pi-.12)*(ui+.5)/NU
 row={'pixel':[x,y],'world':list(p),'mouth':list(local),'radius':radius,'cutter_radius':cutradius,'inside_receiver_tool':cutradius is not None and radius<cutradius,'chart_approx':[t,u]}
 if extended:
  row['outward_radial_samples']=[{'world_shift':h,'radius':math.hypot((inv@(p+n*h)).x,(inv@(p+n*h)).y),'z':(inv@(p+n*h)).z}for h in [0.,.005,.01,.015,.02]]
 rows.append(row);print(row,flush=True)
(OUT/('gap_tool_extended.json' if extended else 'gap_tool_diagnosis.json')).write_text(json.dumps(rows,indent=2)+'\n')
