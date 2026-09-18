"""Evaluate small guided-release + rear-hinge alternatives; shell pairs only."""
import bpy,json,math
from pathlib import Path
from mathutils import Matrix,Vector,Quaternion
from mathutils.bvhtree import BVHTree
ROOT=Path(__file__).resolve().parents[2];OUT=ROOT/'review/I_refinement/opening_r14';spec=json.loads((OUT/'build.json').read_text());bpy.ops.wm.open_mainfile(filepath=str(ROOT/spec['source']));bpy.context.scene.frame_set(1);bpy.context.view_layer.update();deps=bpy.context.evaluated_depsgraph_get();body=bpy.data.objects['IC11_ConchBody']
def smooth(t):t=max(0,min(1,t));return t*t*(3-2*t)
parts=[]
for row,shell in zip(spec['rig'][:6],spec['shells']):
 node=bpy.data.objects[row['name']];mesh=bpy.data.objects[shell['mesh']];e=mesh.evaluated_get(deps);m=e.to_mesh();m.calc_loop_triangles();mat=node.matrix_world.inverted()@mesh.matrix_world
 vertices=[mat@v.co for v in m.vertices];faces=[tuple(t.vertices) for t in m.loop_triangles];e.to_mesh_clear();parts.append((row,vertices,faces))
results=[]
for step in [.07,.075,.08]:
 for phase_split in [True]:
  hits=[];max_top=0.;max_width=0.
  for sample in range(11):
   amount=sample/10;trees=[];points=[]
   for i,(row,v,f) in enumerate(parts):
    turn=smooth((amount-(.30 if phase_split else 0)-i*.05)/(.45 if phase_split else .675));release=smooth(amount/.30) if phase_split else turn
    mat=body.matrix_world@Matrix.Translation(Vector((0,0,i*step*release)))@Matrix(row['home_matrix'])@Quaternion(Vector((0,0,1)),row['angle']*turn).to_matrix().to_4x4()
    pp=[mat@p for p in v];points.extend(pp);trees.append(BVHTree.FromPolygons(pp,f,all_triangles=True))
   max_top=max(max_top,max(p.z for p in points)/2.74);max_width=max(max_width,(max(p.x for p in points)-min(p.x for p in points))/2.74)
   for i in range(6):
    for j in range(i+1,6):
     pairs=trees[i].overlap(trees[j])
     if pairs:hits.append({'amount':amount,'pair':[i,j],'triangles':len(pairs)})
  result={'release_step':step,'release_before_turn':phase_split,'contact_samples':len(hits),'max_skin_top_D':max_top,'max_skin_width_D':max_width,'contacts':hits};results.append(result);print({k:v for k,v in result.items() if k!='contacts'},flush=True)
(OUT/'release_options_fine.json').write_text(json.dumps({'source_sha256':spec['source_sha256'],'options':results,'scope':'11 opening samples, porcelain shell pairs only. No fixed core/lip/support, reverse, continuous clearance or final mechanism validation. Motion alternatives require guided carriers.'},indent=2)+'\n')
