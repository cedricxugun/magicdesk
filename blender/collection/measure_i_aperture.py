"""Measure front-path clear aperture from the actual evaluated three-tongue source."""
import bpy,json,hashlib,math
from pathlib import Path
import sys
from mathutils import Vector
from mathutils.bvhtree import BVHTree
ROOT=Path(__file__).resolve().parents[2];args=sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else [];OUT=ROOT/(args[0] if args else 'review/I_refinement/part_a_mouth/shutter_r2/diaphragm');spec=json.loads((OUT/'build.json').read_text());source=ROOT/spec['source'];assert hashlib.sha256(source.read_bytes()).hexdigest()==spec['source_sha256']
bpy.ops.wm.open_mainfile(filepath=str(source));scene=bpy.context.scene;scene.frame_set(1);bpy.context.view_layer.update();deps=bpy.context.evaluated_depsgraph_get();mouth=bpy.data.objects['IAM_Mouth'];inv=mouth.matrix_world.inverted()
foils=[bpy.data.objects[name] for g in spec['tongues'] for name in g['mesh_names']]
for g in spec['tongues']:bpy.data.objects[g['drive']].animation_data_clear()
radius=.735;center_exclusion=.095;front_z=-.36;rear_z=.149

def tree():
 vertices=[];triangles=[]
 for o in foils:
  e=o.evaluated_get(deps);m=e.to_mesh();m.calc_loop_triangles();offset=len(vertices);vertices.extend(inv@e.matrix_world@v.co for v in m.vertices);triangles.extend(tuple(offset+i for i in t.vertices) for t in m.loop_triangles);e.to_mesh_clear()
 return BVHTree.FromPolygons(vertices,triangles,all_triangles=True)

def aperture(t,n):
 count=0;clear=0;cell=2*radius/n
 for y in range(n):
  yy=(y+.5)*cell-radius
  for x in range(n):
   xx=(x+.5)*cell-radius;r2=xx*xx+yy*yy
   if not center_exclusion**2<r2<radius**2:continue
   count+=1
   if t.ray_cast(Vector((xx,yy,front_z)),Vector((0,0,1)),rear_z-front_z)[0] is None:clear+=1
 return {'grid':n,'rays':count,'clear_rays':clear,'clear_fraction':clear/count,'projected_clear_area':clear*cell*cell}

samples=[];convergence=[]
for k in range(33):
 opening=k/32
 for g in spec['tongues']:
  lo,hi=g['window'];t=max(0,min(1,(opening-lo)/(hi-lo)));bpy.data.objects[g['drive']]['feed']=float(t*t*(3-2*t));bpy.data.objects[g['drive']].update_tag()
 bpy.context.view_layer.update()
 for g in spec['tongues']:
  keys=bpy.data.objects[g['mesh_names'][0]].data.shape_keys.key_blocks
  feed=sum(index*float(key.value)/256 for index,key in enumerate(keys) if index>0)
  assert abs(feed-float(bpy.data.objects[g['drive']]['feed']))<1e-5,('Stale foil evaluation',g['tongue_index'],feed)
 bvh=tree();value=aperture(bvh,128);samples.append({'opening':opening,**value})
 if k in [0,8,16,24,32]:convergence.append({'opening':opening,'coarse':value,'fine':aperture(bvh,256)})
 print('APERTURE',k,value['clear_fraction'],flush=True)
report={'source_sha256':spec['source_sha256'],'component_sha256':spec['component_sha256'],'samples':samples,'convergence':convergence,'radius':radius,'center_exclusion_radius':center_exclusion,'ray_front_z':front_z,'ray_end_z':rear_z,'scope':'Projected unoccluded axial path before the fixed grille, measured on all six evaluated foil surfaces. Excludes a fixed central core disk. Does not model grille porosity, fluid/acoustic losses or full physical conductance.'}
(OUT/'aperture_measurement.json').write_text(json.dumps(report,indent=2)+'\n');print('I_APERTURE_MEASURED',flush=True)
