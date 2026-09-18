"""Inspect the actual rendered triangles, not only the polygon mesh topology."""
import bpy,json,hashlib,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];args=sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else [];requested=next((a.split('=',1)[1] for a in args if a.startswith('--report=')),None);report=ROOT/(requested or 'review/I_refinement/nautilus_r1/throat_terminations_r16/build.json');OUT=report.parent if requested else ROOT/'review/I_refinement/nautilus_r1/end_finish_r17';s=json.loads(report.read_text());assert hashlib.sha256((ROOT/s['source']).read_bytes()).hexdigest()==s['source_sha256'];bpy.ops.wm.open_mainfile(filepath=str(ROOT/s['source']));rows=[]
names=[r['name'] for r in s['new_cassette_solids']]+list(s.get('cassette_source_skins',{})) if 'new_cassette_solids' in s else s['metal_supports']['new_meshes']+s['metal_supports']['modified_meshes'] if 'metal_supports' in s else ['IN1_CellFrame_08','IN1_CellFrame_09']
if 'linear_drives' in s:
    names=list(dict.fromkeys(names+s['linear_drives']['new_meshes']+s['linear_drives']['modified_meshes']))
if 'cowl_finish' in s:
    names=s['cowl_finish']['modified_meshes']
for name in names:
    o=bpy.data.objects[name];o.data.calc_loop_triangles();triangles=list(o.data.loop_triangles);edges={};faces={}
    for i,t in enumerate(triangles):
        f=tuple(t.vertices);faces.setdefault(tuple(sorted(f)),[]).append(i)
        for j,a in enumerate(f):edges.setdefault(tuple(sorted([a,f[(j+1)%3]])),[]).append(i)
    bad=[]
    for edge,ids in edges.items():
        if len(ids)==2:continue
        bad.append({'edge':edge,'points':[list(o.data.vertices[i].co) for i in edge],'triangle_indices':ids,'triangles':[{'vertices':list(triangles[i].vertices),'polygon':triangles[i].polygon_index} for i in ids]})
    rows.append({'mesh':name,'triangles':len(triangles),'bad_edges':bad,'duplicate_triangles':[{'vertices':f,'indices':ids} for f,ids in faces.items() if len(ids)>1]})
(OUT/('render_triangulation.json' if requested else 'source_triangulation_probe.json')).write_text(json.dumps({'source_sha256':s['source_sha256'],'passed':all(not r['bad_edges'] and not r['duplicate_triangles'] for r in rows),'rows':rows},indent=2)+'\n');print(json.dumps(rows,indent=2),flush=True)
