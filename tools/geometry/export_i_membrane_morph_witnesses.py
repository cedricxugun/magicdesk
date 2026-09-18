import bpy,json,hashlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];OUT=ROOT/'review/I_refinement/nautilus_r1/chamber_motion_r36';s=json.loads((OUT/'build.json').read_text());assert hashlib.sha256((ROOT/s['source']).read_bytes()).hexdigest()==s['source_sha256'];bpy.ops.wm.open_mainfile(filepath=str(ROOT/s['source']));bpy.context.scene.frame_set(1);bpy.context.view_layer.update();rows=[]
def godot(p):return [p.x,p.z,-p.y]
for spec in s['membrane_motion']:
    o=bpy.data.objects[spec['mesh']];keys=o.data.shape_keys.key_blocks;moving={v['vertex']for v in spec['moving']};fixed=[i for i in range(len(o.data.vertices))if i not in moving];ids=sorted(moving)[::max(1,len(moving)//24)]+fixed[::max(1,len(fixed)//12)];points=[]
    for i in ids:points.append({'local_rest':godot(keys['Basis'].data[i].co),'world_rest':godot(o.matrix_world@keys['Basis'].data[i].co),'world_pressure':godot(o.matrix_world@keys[spec['pressure_key']].data[i].co),'world_rebound':godot(o.matrix_world@keys[spec['rebound_key']].data[i].co)})
    rows.append({'mesh':o.name,'pressure':spec['pressure_key'],'rebound':spec['rebound_key'],'points':points})
(OUT/'morph_witnesses.json').write_text(json.dumps({'source_sha256':s['source_sha256'],'component_sha256':s['component_sha256'],'meshes':rows},indent=2)+'\n');print('MORPH_WITNESSES',sum(len(r['points'])for r in rows),flush=True)
