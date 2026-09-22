"""Measure actual swept cartridge radius in the sector of the visible gap."""
import bpy,json,math,sys
from pathlib import Path
from mathutils import Vector
R=Path(__file__).resolve().parents[2];OUT=R/'review/I_refinement/nautilus_reset_r82/finish_r86'
spec=json.loads((OUT/'build.json').read_text());bpy.ops.wm.open_mainfile(filepath=str(R/spec['source']));scene=bpy.context.scene
module=bpy.data.objects['IAM_MODULE'];mouth=bpy.data.objects['IAM_Mouth']
exclude={'I_MoonlightStaff','I_CentralReadingLine','I_TipReadingRay_0','I_TipReadingRay_1','I_TipReadingRay_2'}
objects=[o for o in module.children_recursive if o.type in ['MESH','CURVE']and o.name not in exclude]
wide='--wide' in sys.argv
angle=(-.3,.65) if wide else (.1,.6)
bins=[(.245,.27),(.27,.30),(.30,.34),(.34,.38),(.38,.42),(.42,.45)]
rows=[{'z_range':[a,b],'maximum_radius':0.,'owner':None}for a,b in bins]
for f in [1,20,40,60,78,145,205,217,260,350,390,430]:
 scene.frame_set(f);bpy.context.view_layer.update();inv=mouth.matrix_world.inverted()
 for o in objects:
  ev=o.evaluated_get(bpy.context.evaluated_depsgraph_get());me=ev.to_mesh();me.calc_loop_triangles();verts=[inv@ev.matrix_world@v.co for v in me.vertices]
  for tri in me.loop_triangles:
   pts=[verts[i]for i in tri.vertices];lo=min(p.z for p in pts);hi=max(p.z for p in pts)
   if hi<.245 or lo>.45:continue
   angles=[math.atan2(p.y,p.x)for p in pts]
   if max(angles)-min(angles)<math.pi and (max(angles)<angle[0] or min(angles)>angle[1]):continue
   radius=max(math.hypot(p.x,p.y)for p in pts)
   for row in rows:
    a,b=row['z_range']
    if lo<=b and hi>=a and radius>row['maximum_radius']:row.update({'maximum_radius':radius,'owner':o.name,'frame':f})
  ev.to_mesh_clear()
 print('SECTOR_SWEEP',f,flush=True)
(OUT/('gap_sector_wide.json' if wide else 'gap_sector_envelope.json')).write_text(json.dumps({'angle_range':list(angle),'samples':rows,'scope':'Conservative triangle angular/Z-bounds on actual physical core through 12 source poses; excludes projection meshes. Radius bounds use complete triangles, not isolated vertices.'},indent=2)+'\n')
print(rows,flush=True)
