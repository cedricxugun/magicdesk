import bpy,json,math,hashlib
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
R=Path(__file__).resolve().parents[2];s=json.loads((R/'review/I_refinement/nautilus_r1/scan_caps_runtime_r43/narrow/build.json').read_text());assert hashlib.sha256((R/s['source']).read_bytes()).hexdigest()==s['source_sha256'];bpy.ops.wm.open_mainfile(filepath=str(R/s['source']));bpy.context.scene.frame_set(1);bpy.context.view_layer.update();rest_matrices={o.name:o.matrix_world.copy()for o in bpy.data.objects if o.type=='MESH'};mouth=bpy.data.objects['IAM_MODULE'].matrix_world.copy();bpy.context.scene.frame_set(121);bpy.context.view_layer.update();deps=bpy.context.evaluated_depsgraph_get();trees=[]
for o in bpy.data.objects:
 if o.type!='MESH' or not(o.name.startswith('IN1_PorcelainPanel_')or o.name.startswith('IN1_FixedMouthCheek')):continue
 e=o.evaluated_get(deps);m=e.to_mesh();m.calc_loop_triangles();pts=[e.matrix_world@v.co for v in m.vertices];tri=[tuple(t.vertices)for t in m.loop_triangles];trees.append((o.name,BVHTree.FromPolygons(pts,tri,all_triangles=True)));e.to_mesh_clear()
eye=Vector((-3,-7.7,3.55));aim=Vector((0,0,1.66));forward=(aim-eye).normalized();right=forward.cross(Vector((0,0,1))).normalized();up=right.cross(forward).normalized();rows=[]
for x,y in [(400,340),(440,390),(525,440),(540,475),(560,510),(550,575),(580,600),(520,640),(640,615)]:
 ray=(forward+right*((x/1040-.5)*2*math.tan(math.radians(16)))+up*((.5-y/1040)*2*math.tan(math.radians(16)))).normalized();hits=[]
 for name,t in trees:
  p,n,i,d=t.ray_cast(eye,ray,20)
  if p is not None:
   rest=rest_matrices[name]@bpy.data.objects[name].matrix_world.inverted()@p;depth=(rest-mouth.translation).dot(mouth.to_3x3().col[2].normalized());hits.append({'mesh':name,'point_blender':list(p),'point_rest_blender':list(rest),'mouth_axial_depth_world_at_rest':depth,'normal_blender':list(n),'triangle':i,'distance':d})
 hits.sort(key=lambda h:h['distance']);rows.append({'pixel':[x,y],'front':hits[0]if hits else None})
(R/'review/I_refinement/nautilus_r1/cowl_surface_probe_r44/pixel_ownership_rest_depth.json').write_text(json.dumps({'source_sha256':s['source_sha256'],'source_frame':121,'scope':'Source evaluated frame121 with matching review camera rays; diagnostic ownership only, not pose/art acceptance.','rays':rows},indent=2)+'\n');print(json.dumps(rows),flush=True)
