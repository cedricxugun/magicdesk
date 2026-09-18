"""Actual nonadjacent render-triangle contacts in the explicitly rebuilt skins."""
import bpy,json,hashlib,sys
from pathlib import Path
from mathutils.bvhtree import BVHTree
ROOT=Path(__file__).resolve().parents[2];args=sys.argv[sys.argv.index('--')+1:]if '--'in sys.argv else [];report=ROOT/next((a.split('=',1)[1]for a in args if a.startswith('--report=')),'review/I_refinement/nautilus_r1/clean_cowl_r23/build.json');s=json.loads(report.read_text());assert hashlib.sha256((ROOT/s['source']).read_bytes()).hexdigest()==s['source_sha256'];bpy.ops.wm.open_mainfile(filepath=str(ROOT/s['source']));rows=[]
requested=next((a.split('=',1)[1]for a in args if a.startswith('--meshes=')),None)
names=requested.split(',')if requested else s.get('clean_cowl',s.get('surface_finish',{}))['modified_meshes']
for name in names:
    o=bpy.data.objects[name];o.data.calc_loop_triangles();v=[o.matrix_world@p.co for p in o.data.vertices];f=[tuple(t.vertices)for t in o.data.loop_triangles];tree=BVHTree.FromPolygons(v,f,all_triangles=True);contacts=[]
    for i,j in tree.overlap(tree):
        if i>=j or set(f[i])&set(f[j]):continue
        contacts.append({'triangle_indices':[i,j],'vertices':[f[i],f[j]]})
    rows.append({'mesh':name,'contact_count':len(contacts),'contacts':contacts,'passed':not contacts});print('CLEAN_SELF',name,len(contacts),flush=True)
(report.parent/'self_contacts.json').write_text(json.dumps({'source_sha256':s['source_sha256'],'passed':all(r['passed']for r in rows),'rows':rows,'scope':'Actual BVH contacts between nonadjacent render triangles in the named rebuilt skins. Does not cover remaining old skins, all fixed interfaces, continuous runtime motion or final visual acceptance.'},indent=2)+'\n')
