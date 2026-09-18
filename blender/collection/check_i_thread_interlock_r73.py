"""Test actual thread interlock and signed helical motion, independent of staging."""
import bpy,json,hashlib,math
from pathlib import Path
from mathutils import Vector,Quaternion
from mathutils.bvhtree import BVHTree
ROOT=Path(__file__).resolve().parents[2];OUT=ROOT/'review/I_refinement/nautilus_r1/seam_release_r73';s=json.loads((OUT/'build.json').read_text());assert hashlib.sha256((ROOT/s['source']).read_bytes()).hexdigest()==s['source_sha256'];bpy.ops.wm.open_mainfile(filepath=str(ROOT/s['source']));bpy.context.scene.frame_set(1);bpy.context.view_layer.update();mount=bpy.data.objects['IC1_MouthMount'];axis_delta=mount.matrix_world.to_3x3().col[1];axis=axis_delta.normalized()
def geo(o):
 m=o.data;m.calc_loop_triangles();v=[o.matrix_world@p.co for p in m.vertices];f=[tuple(t.vertices)for t in m.loop_triangles];return v,f
results=[]
for row in s['seam_fasteners']['pairs']:
 sign=row['sign'];pin=bpy.data.objects['IC1_SeamCrossBolt_'+str(sign)];cap=bpy.data.objects['IC73_SeamSocket_'+str(sign)];pv,pf=geo(pin);cv,cf=geo(cap);pt=BVHTree.FromPolygons(pv,pf,all_triangles=True);center=mount.matrix_world@Vector(row['center_parent']);pitch=row['thread_pitch']
 def contacts(distance,twist):
  q=Quaternion(axis,twist);v=[center+q@(p-center)+axis_delta*distance for p in cv];return len(BVHTree.FromPolygons(v,cf,all_triangles=True).overlap(pt))
 samples=[]
 for i in range(101):
  distance=row['cap_side']*.014*i/100
  # theta=atan2(z,x) decreases under positive Y rotation. Therefore positive
  # axial advance requires negative right-hand Y twist for this modeled helix.
  samples.append({'distance':distance,'twist':-math.tau*distance/pitch,'contacts':contacts(distance,-math.tau*distance/pitch)})
 distance=row['cap_side']*pitch*.25
 results.append({'sign':sign,'closed_contacts':contacts(0.,0.),'helical_samples':samples,'quarter_pitch_axial_only_contacts':contacts(distance,0.),'quarter_turn_only_contacts':contacts(0.,math.pi/2)})
passed=all(r['closed_contacts']==0 and all(p['contacts']==0 for p in r['helical_samples'])and r['quarter_pitch_axial_only_contacts']>0 and r['quarter_turn_only_contacts']>0 for r in results)
r={'source_sha256':s['source_sha256'],'passed':passed,'axis_install_scale':axis_delta.length,'pitch_coordinate_space':'IC1_MouthMount local','results':results,'scope':'Two actual male/female meshes, 101 helical positions each, closed mating and deliberate axial-only / twist-only interference witnesses. Not whole-assembly clearance, continuous collision, torque/load or final art acceptance.'};(OUT/'thread_interlock.json').write_text(json.dumps(r,indent=2)+'\n');print('THREAD_INTERLOCK_RESULT',passed,[(x['sign'],sum(y['contacts']for y in x['helical_samples']),x['quarter_pitch_axial_only_contacts'],x['quarter_turn_only_contacts'])for x in results]);assert passed
