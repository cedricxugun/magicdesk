"""Independent double-precision separating-axis evidence for raw BVH contacts."""
import bpy,json,hashlib,sys
import numpy as np
from pathlib import Path
def separation(a,b):
    a=np.asarray(a,dtype=np.float64);b=np.asarray(b,dtype=np.float64);ea=np.roll(a,-1,axis=0)-a;eb=np.roll(b,-1,axis=0)-b;na=np.cross(ea[0],ea[1]);nb=np.cross(eb[0],eb[1]);common=any(np.array_equal(x,y)for x in a for y in b)
    axes=[na,nb,a.mean(axis=0)-b.mean(axis=0)]+[np.cross(x,y)for x in ea for y in eb]+[np.cross(na,x)for x in ea]+[np.cross(nb,x)for x in eb]
    for axis in axes:
        norm=np.linalg.norm(axis)
        if norm<1e-14:continue
        axis=axis/norm;pa=np.einsum('ij,j->i',a,axis);pb=np.einsum('ij,j->i',b,axis);gap=max(float(pb.min()-pa.max()),float(pa.min()-pb.max()));wa=float(pa.max()-pa.min());wb=float(pb.max()-pb.min())
        if gap>1e-10:return {'kind':'strictly_separated','axis':axis.tolist(),'gap':gap,'interval_a':[float(pa.min()),float(pa.max())],'interval_b':[float(pb.min()),float(pb.max())]}
        if common and gap>=-1e-12 and min(wa,wb)>1e-9:return {'kind':'proved_shared_boundary_only','axis':axis.tolist(),'gap':gap,'interval_a':[float(pa.min()),float(pa.max())],'interval_b':[float(pb.min()),float(pb.max())]}
    return None
# Counterexamples: separation, a shared point, coplanar area overlap, and a
# crossing with a shared vertex must not be treated as equivalent.
a=[[0,0,0],[1,0,0],[0,1,0]]
assert separation(a,[[2,0,0],[3,0,0],[2,1,0]])['kind']=='strictly_separated'
assert separation(a,[[0,0,0],[-1,0,0],[0,-1,0]])['kind']=='proved_shared_boundary_only'
assert separation(a,[[.1,.1,0],[.7,.1,0],[.1,.7,0]])is None
assert separation(a,[[0,0,0],[.5,.5,-1],[.5,.5,1]])is None
ROOT=Path(__file__).resolve().parents[2];args=sys.argv[sys.argv.index('--')+1:]if '--'in sys.argv else [];report=ROOT/next((a.split('=',1)[1]for a in args if a.startswith('--report=')),'review/I_refinement/nautilus_r1/clean_cowl_r23/build.json');s=json.loads(report.read_text());raw=json.loads((report.parent/'self_contacts.json').read_text());assert raw['source_sha256']==s['source_sha256'];assert hashlib.sha256((ROOT/s['source']).read_bytes()).hexdigest()==s['source_sha256'];bpy.ops.wm.open_mainfile(filepath=str(ROOT/s['source']));rows=[]
for row in raw['rows']:
    o=bpy.data.objects[row['mesh']];v=[tuple(o.matrix_world@p.co)for p in o.data.vertices];classified=[];unresolved=[]
    for pair in row['contacts']:
        proof=separation([v[i]for i in pair['vertices'][0]],[v[i]for i in pair['vertices'][1]])
        if proof:classified.append({**pair,'proof':proof})
        else:unresolved.append(pair)
    rows.append({'mesh':row['mesh'],'raw_contacts':row['contact_count'],'classified':classified,'unresolved':unresolved,'passed':not unresolved});print('CONTACT_CERTIFICATION',row['mesh'],len(classified),len(unresolved),flush=True)
(report.parent/'self_contact_certification.json').write_text(json.dumps({'source_sha256':s['source_sha256'],'passed':all(r['passed']for r in rows),'rows':rows,'synthetic_counterexamples_passed':True,'scope':'Explicit double-precision projection separation or shared-boundary-only proof for each raw BVH pair. Unproved pairs remain unresolved. Does not validate the rest of the model, continuous transforms or final visual quality.'},indent=2)+'\n')
