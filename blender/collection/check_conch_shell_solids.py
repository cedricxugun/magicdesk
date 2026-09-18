"""Check evaluated shell topology for a specified candidate; no fidelity claim."""
import bpy,bmesh,json,sys,hashlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];args=sys.argv[sys.argv.index('--')+1:];folder=ROOT/args[0];build=json.loads((folder/'build.json').read_text());source=ROOT/build['source'];assert hashlib.sha256(source.read_bytes()).hexdigest()==build['source_sha256']
bpy.ops.wm.open_mainfile(filepath=str(source));bpy.context.scene.frame_set(1);deps=bpy.context.evaluated_depsgraph_get();rows=[]
for row in build['shells']:
 o=bpy.data.objects[row['mesh']];e=o.evaluated_get(deps);mesh=e.to_mesh();bm=bmesh.new();bm.from_mesh(mesh)
 r={'name':o.name,'faces':len(bm.faces),'boundary_edges':sum(x.is_boundary for x in bm.edges),'nonmanifold_edges':sum(not x.is_manifold for x in bm.edges),'signed_volume':bm.calc_volume(signed=True)};rows.append(r);bm.free();e.to_mesh_clear()
result={'source_sha256':build['source_sha256'],'rows':rows,'passed':all(r['nonmanifold_edges']==0 and r['signed_volume']>0 for r in rows),'scope':'Six evaluated porcelain solids only. No surface intersection, whole assembly, source-art or animation acceptance.'};(folder/'shell_solids.json').write_text(json.dumps(result,indent=2)+'\n');print(result,flush=True)
