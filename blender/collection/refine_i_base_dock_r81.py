"""Bounded finish of the R80 dock: physical seam relief, adjacent-edge cleanup."""
import bpy,bmesh,json,sys,math,hashlib,collections,array
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(Path(__file__).parent))
import i_machined_geometry as h
OUT=ROOT/'review/I_refinement/nautilus_r1/base_dock_r81';OUT.mkdir(parents=True,exist_ok=True)
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
s=json.loads((ROOT/'review/I_refinement/nautilus_r1/base_dock_r80/build.json').read_text());assert sha(ROOT/s['source'])==s['source_sha256']
bpy.ops.wm.open_mainfile(filepath=str(ROOT/s['source']));bpy.context.scene.frame_set(1)
carrier=bpy.data.objects['ID80_Carrier'];trim=bpy.data.objects['IN1_PanelRim_1_1_0_-1410'];skin=bpy.data.objects['IN1_PorcelainPanel_02'];body=bpy.data.objects['IN1_BodyRoot'];base=bpy.data.objects['BASE_FIXED'];root=bpy.data.objects['ID80_Dock']
def digest(o):
 d=hashlib.sha256();m=o.data;m.calc_loop_triangles()
 for sequence,prop,size,kind in [(m.vertices,'co',3,'f'),(m.loop_triangles,'vertices',3,'I'),(m.corner_normals,'vector',3,'f')]:
  a=array.array(kind,[0])*(len(sequence)*size);sequence.foreach_get(prop,a);d.update(a.tobytes())
 for uv in m.uv_layers:
  a=array.array('f',[0])*(len(uv.data)*2);uv.data.foreach_get('uv',a);d.update(a.tobytes())
 if m.shape_keys:
  for k in m.shape_keys.key_blocks:
   a=array.array('f',[0])*(len(k.data)*3);k.data.foreach_get('co',a);d.update(a.tobytes())
 return [d.hexdigest(),[list(row) for row in o.matrix_world],[x.name if x else None for x in m.materials],[p.material_index for p in m.polygons]]
protected={o.name:digest(o) for o in bpy.data.objects if o.type=='MESH' and o not in [carrier,trim]}
assert trim.parent==skin.parent,(trim.parent.name,skin.parent.name)
col=bpy.data.collections['I_BASE_DOCK_R80'];h.configure(col)
bm=bmesh.new();bm.from_mesh(trim.data);volume_before=bm.calc_volume(signed=True);bm.free()
h.drill(trim,.0445,.7,root,(.26,.10,1.))
bm=bmesh.new();bm.from_mesh(trim.data);volume_after=bm.calc_volume(signed=True);trim_open=sum(not e.is_manifold for e in bm.edges);bm.free()
assert .5<volume_after/volume_before<1. and trim_open==0,(volume_before,volume_after,trim_open)
# Collapse only explicitly connected sub-float-precision Boolean edges. Never
# merge near surfaces or arbitrarily weld all vertices within a distance.
bm=bmesh.new();bm.from_mesh(carrier.data);bm.verts.ensure_lookup_table();bm.verts.index_update()
edges=[e for e in bm.edges if 0<e.calc_length()<2e-8];parent={v:v for e in edges for v in e.verts}
def find(v):
 while parent[v]!=v:v=parent[v]
 return v
for edge in edges:
 a,b=(find(v) for v in edge.verts)
 if a!=b:
  if a.index>b.index:a,b=b,a
  parent[b]=a
mapping={v:find(v) for v in parent if v!=find(v)}
movement=max(((carrier.matrix_world.to_3x3()@(v.co-t.co)).length for v,t in mapping.items()),default=0)
assert movement<2e-8
rows=[{'a':list(v.co),'b':list(t.co),'world_distance':(carrier.matrix_world.to_3x3()@(v.co-t.co)).length} for v,t in mapping.items()]
bmesh.ops.weld_verts(bm,targetmap=mapping);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(carrier.data);bm.free();carrier.data.update()
checks=[]
for o in [carrier,trim]:
 bm=bmesh.new();bm.from_mesh(o.data);checks.append({'name':o.name,'nonmanifold':sum(not e.is_manifold for e in bm.edges),'volume':bm.calc_volume(signed=True)});bm.free()
assert all(r['nonmanifold']==0 and r['volume']>0 for r in checks)
assert all(digest(bpy.data.objects[n])==value for n,value in protected.items())
proof={'parent_source_sha256':s['source_sha256'],'modified':[carrier.name,trim.name],'trim_relief':{'radius':.0445,'port_outer_radius':.043,'volume_before':volume_before,'volume_after':volume_after,'same_panel_parent':skin.parent.name},'adjacent_edge_collapse':rows,'max_world_displacement':movement,'protected_meshes':len(protected),'protected_unchanged':True,'solids':checks}
(OUT/'refinement.json').write_text(json.dumps(proof,indent=2)+'\n')
source=ROOT/'blender/collection/I_base_dock_r81.blend';component=ROOT/'app/assets/collection/components/I_base_dock_r81.glb'
assert not source.exists() and not component.exists();bpy.ops.wm.save_as_mainfile(filepath=str(source),compress=True)
bpy.ops.object.select_all(action='DESELECT')
for o in [body,*body.children_recursive]:o.select_set(True)
bpy.context.view_layer.objects.active=body;bpy.ops.export_scene.gltf(filepath=str(component),export_format='GLB',use_selection=True,export_animations=False,export_morph=True,export_morph_normal=True,export_extras=True)
d={**s,'source':source.relative_to(ROOT).as_posix(),'source_sha256':sha(source),'component':component.relative_to(ROOT).as_posix(),'component_sha256':sha(component),'status':'independent_refined_dock_candidate_checks_pending','dock_refinement':proof}
d['base_dock']['modified']=sorted(set(d['base_dock']['modified'])|{trim.name})
art=ROOT/'app/assets/collection/art/I/base_dock_r81';art.mkdir(parents=True,exist_ok=True)
layout=json.loads((ROOT/s['chamber_response_layout'].replace('res://','app/')).read_text());layout.update(source_sha256=d['source_sha256'],component_sha256=d['component_sha256'])
(art/'chamber_layout.json').write_text(json.dumps(layout,indent=2)+'\n');d['chamber_response_layout']='res://assets/collection/art/I/base_dock_r81/chamber_layout.json'
(OUT/'build.json').write_text(json.dumps(d,indent=2)+'\n');print('R81_SAVED',d['source_sha256'],len(rows),movement,flush=True)
