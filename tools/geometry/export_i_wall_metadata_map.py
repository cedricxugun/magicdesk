import bpy,json,hashlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];path=ROOT/'review/I_refinement/nautilus_r1/wall_metadata_r5/build.json';spec=json.loads(path.read_text());assert hashlib.sha256((ROOT/spec['source']).read_bytes()).hexdigest()==spec['source_sha256']
bpy.ops.wm.open_mainfile(filepath=str(ROOT/spec['source']))
rows={o.name:o.data.name for o in bpy.data.objects if o.type=='MESH' and 'formed_wall_fraction' in o.data.attributes}
(path.parent/'object_meshes.json').write_text(json.dumps({'source_sha256':spec['source_sha256'],'objects':rows},indent=2)+'\n');print(json.dumps(rows))
