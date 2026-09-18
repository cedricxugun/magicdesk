"""Seat optical diffuser material in the existing curved nickel conduit faces.
Preserve all source positions, triangles, normals, transforms and membrane keys.
"""
import bpy,json,hashlib,struct,math
from pathlib import Path
from mathutils import Vector
ROOT=Path(__file__).resolve().parents[2];OUT=ROOT/'review/I_refinement/nautilus_r1/light_score_r40';ART=ROOT/'app/assets/collection/art/I/light_score_r40'
for p in [OUT,ART]:p.mkdir(parents=True,exist_ok=True)
s=json.loads((ROOT/'review/I_refinement/nautilus_r1/chamber_light_r39/channels/build.json').read_text());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();assert sha(ROOT/s['source'])==s['source_sha256'];bpy.ops.wm.open_mainfile(filepath=str(ROOT/s['source']));bpy.context.scene.frame_set(1);bpy.context.view_layer.update()
def geom(o):
 h=hashlib.sha256();m=o.data;m.calc_loop_triangles()
 for v in m.vertices:h.update(struct.pack('<3f',*v.co))
 for t in m.loop_triangles:h.update(struct.pack('<3I',*t.vertices))
 for n in m.corner_normals:h.update(struct.pack('<3f',*n.vector))
 if m.shape_keys:
  for key in m.shape_keys.key_blocks:
   h.update(key.name.encode())
   for v in key.data:h.update(struct.pack('<3f',*v.co))
 return [h.hexdigest(),[list(r)for r in o.matrix_world]]
protected={o.name:geom(o)for o in bpy.data.objects if o.type=='MESH'};C=Vector((.12,.16,1.96));R=Vector((1.01,.67,1.10));rows=[]
mat=bpy.data.materials.new('IN1_OpalConductor_R40');mat.diffuse_color=(.66,.53,.29,1);mat.use_nodes=True;bs=next(n for n in mat.node_tree.nodes if n.type=='BSDF_PRINCIPLED');bs.inputs['Base Color'].default_value=(.66,.53,.29,1);bs.inputs['Metallic'].default_value=.0;bs.inputs['Roughness'].default_value=.26
for o in sorted(bpy.data.objects,key=lambda o:o.name):
 if o.type!='MESH' or not o.name.startswith('IN1_ChamberRib_'):continue
 m=o.data;slot=len(m.materials);m.materials.append(mat);normal=o.matrix_world.to_3x3().inverted().transposed();selected=[]
 for p in m.polygons:
  pos=o.matrix_world@p.center;radial=Vector(((pos[i]-C[i])/(R[i]*R[i])for i in range(3))).normalized();n=(normal@p.normal).normalized()
  # Longitudinal cap faces remain nickel; outward window is the existing
  # rounded conduit face, with its original side/back carrier unchanged.
  if len(p.vertices)<=4 and n.dot(radial)>.52:p.material_index=slot;selected.append(p.index)
 assert selected and len(selected)<len(m.polygons)*.65,(o.name,len(selected),len(m.polygons))
 uv=m.uv_layers.new(name='OpalConductorUV') if not m.uv_layers else m.uv_layers[0]
 for loop in m.loops:
  p=o.matrix_world@m.vertices[loop.vertex_index].co-C;phi=math.acos(max(-1.,min(1.,-p.y/(R.y-.050))));uv.data[loop.index].uv=(phi/math.pi,.5)
 index=int(o.name.split('_')[2]);rows.append({'mesh':o.name,'runtime_mesh':o.name.replace('.','_'),'cell_index':index,'material':'IN1_OpalConductor_R40','diffuser_faces':len(selected),'metal_faces':len(m.polygons)-len(selected),'vertex_count':len(m.vertices)})
assert rows and all(geom(bpy.data.objects[n])==v for n,v in protected.items()),'Geometry or morph source changed'
source=ROOT/'blender/collection/I_nautilus_light_guides_r40.blend';component=ROOT/'app/assets/collection/components/I_nautilus_light_guides_r40.glb';assert not source.exists();bpy.ops.wm.save_as_mainfile(filepath=str(source),compress=True);root=bpy.data.objects['IN1_BodyRoot'];bpy.ops.object.select_all(action='DESELECT')
for o in [root,*root.children_recursive]:o.select_set(True)
bpy.context.view_layer.objects.active=root;bpy.ops.export_scene.gltf(filepath=str(component),export_format='GLB',use_selection=True,export_animations=False,export_morph=True,export_morph_normal=True,export_extras=True)
l=json.loads((ROOT/'app/assets/collection/art/I/chamber_light_r39/layout_r3.json').read_text());l.update(source_sha256=sha(source),component_sha256=sha(component));l['illumination'].update(physical_conductors=True,open_floor=.24,playing_floor=.64,emission_gain=5.,light_color=[1.,.42,.09],spill_gain=.38)
for cell in l['cells']:cell['diffusers']=[r for r in rows if r['cell_index']==cell['cell_index']]
l['scope']='Existing rounded conduit outward faces become opal diffuser; nickel backs/end caps remain. Source vertices, triangles, normals, transforms and morph keys preserved. Needs actual render review.';(ART/'chamber_layout.json').write_text(json.dumps(l,indent=2)+'\n');d={**s,'source':str(source.relative_to(ROOT)),'source_sha256':sha(source),'component':str(component.relative_to(ROOT)),'component_sha256':sha(component),'parent_source_sha256':s['source_sha256'],'chamber_response_layout':'res://assets/collection/art/I/light_score_r40/chamber_layout.json','conductor_faces':rows,'optical_glow':True,'status':'physical_diffuser_and_score_candidate_review_pending'};(OUT/'build.json').write_text(json.dumps(d,indent=2)+'\n');(OUT/'geometry_preservation.json').write_text(json.dumps({'passed':True,'source_sha256':d['source_sha256'],'protected_meshes':len(protected),'conduits':rows,'scope':'Exact source positions, render triangle indices, corner normals, transforms and all morph-key coordinates unchanged. Only conduit face material indices and UVs changed; no manufacturing or visual acceptance.'},indent=2)+'\n');print('R40_CONDUCTORS',len(rows),d['source_sha256'],flush=True)
