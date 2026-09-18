"""Compare preserved 04 source geometry, rest transforms and parent identities."""
import bpy,json,hashlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];OUT=ROOT/'review/I_refinement/nautilus_r1/cassettes_r2'
old=json.loads((ROOT/'review/I_refinement/nautilus_r1/hinge_r1/build.json').read_text());new=json.loads((OUT/'build.json').read_text())
def read(spec):
    path=ROOT/spec['source'];assert hashlib.sha256(path.read_bytes()).hexdigest()==spec['source_sha256']
    bpy.ops.wm.open_mainfile(filepath=str(path));bpy.context.scene.frame_set(1);bpy.context.view_layer.update();out={}
    for o in bpy.data.objects:
        if not (o.name.startswith(('IN2_Cassette04','IN2_Guide04')) or o.name in ['IN1_PanelPivot_04','IN1_PorcelainPanel_04','IN1_FixedRearShell_04']):continue
        row={'parent':o.parent.name if o.parent else None,'matrix':[list(r) for r in o.matrix_world]}
        if o.type=='MESH':
            data={'vertices':[list(v.co) for v in o.data.vertices],'faces':[list(p.vertices) for p in o.data.polygons],'materials':[m.name if m else None for m in o.data.materials]}
            row['geometry_sha256']=hashlib.sha256(json.dumps(data,sort_keys=True).encode()).hexdigest()
        out[o.name]=row
    return out
a=read(old);b=read(new);failures=[];error=0.
assert set(a)==set(b)
for name,left in a.items():
    right=b[name]
    if left['parent']!=right['parent'] or left.get('geometry_sha256')!=right.get('geometry_sha256'):failures.append(name)
    delta=max(abs(x-y) for ra,rb in zip(left['matrix'],right['matrix']) for x,y in zip(ra,rb));error=max(error,delta)
    if delta>1e-6:failures.append(name)
result={'old_source_sha256':old['source_sha256'],'source_sha256':new['source_sha256'],'component_sha256':new['component_sha256'],'passed':not failures,'objects':len(a),'maximum_rest_matrix_error':error,'failures':failures,'scope':'Exact 04 mesh coordinate/face/material-name fingerprints and rest parents/transforms. Not cross-cassette clearance or whole artwork acceptance.'}
(OUT/'preserved_04_check.json').write_text(json.dumps(result,indent=2)+'\n');print('CASSETTE04_PRESERVED',result['passed'],error,failures,flush=True)
