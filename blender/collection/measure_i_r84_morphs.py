"""Independent source morph witnesses for twelve R84 diaphragms."""
import bpy,json,hashlib,sys
from pathlib import Path
from mathutils import Vector
R=Path(__file__).resolve().parents[2];OUT=R/'review/I_refinement/nautilus_reset_r82/chambers_r3'
args=sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else []
report=next((a.split('=',1)[1]for a in args if a.startswith('--report=')),None)
if report:OUT=(R/report).parent
s=json.loads((OUT/'build.json').read_text());bpy.ops.wm.open_mainfile(filepath=str(R/s['source']));bpy.context.scene.frame_set(1)
assert hashlib.sha256((R/s['source']).read_bytes()).hexdigest()==s['source_sha256']
def cv(p):return [p.x,p.z,-p.y]
rows=[]
for c in s['new_cells']:
 o=bpy.data.objects[c['diaphragm']];keys=o.data.shape_keys.key_blocks
 ids=sorted(set([0,len(o.data.vertices)-1]+[int((len(o.data.vertices)-1)*k/23)for k in range(24)]))
 points=[]
 for i in ids:
  a=keys['Basis'].data[i].co;b=keys['MusicPressure'].data[i].co;d=keys['MusicRebound'].data[i].co
  points.append({'local_rest':cv(a),'world_rest':cv(o.matrix_world@a),'world_pressure':cv(o.matrix_world@b),'world_rebound':cv(o.matrix_world@d)})
 rows.append({'mesh':o.name,'pressure':'MusicPressure','rebound':'MusicRebound','points':points})
(OUT/'morph_witnesses.json').write_text(json.dumps({'source_sha256':s['source_sha256'],'component_sha256':s['component_sha256'],'meshes':rows},indent=2)+'\n')
print('R84_MORPH_WITNESSES',sum(len(r['points'])for r in rows),flush=True)
