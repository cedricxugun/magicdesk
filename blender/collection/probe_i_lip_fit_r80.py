import bpy,json,math
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
ROOT=Path(__file__).resolve().parents[2];OUT=ROOT/'review/I_refinement/nautilus_r1/base_dock_r80';OUT.mkdir(parents=True,exist_ok=True)
s=json.loads((ROOT/'review/I_refinement/nautilus_r1/coupling_repair_r76/build.json').read_text());bpy.ops.wm.open_mainfile(filepath=str(ROOT/s['source']));bpy.context.scene.frame_set(1)
import sys
sys.path.insert(0,str(Path(__file__).parent))
import i_dock_fitted_r79 as fit
for r in [.041,.042,.043]:
 try:
  v,f,e=fit.surface(bpy.data.objects['IN1_PorcelainPanel_02'],[(.26+r*math.cos(i*math.tau/64),.10+r*math.sin(i*math.tau/64)) for i in range(64)])
  print('R80_PORT',r,'OK',len(v),flush=True)
 except Exception as e:print('R80_PORT',r,str(e),flush=True)
