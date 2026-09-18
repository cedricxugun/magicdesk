"""Evaluate authored membrane vertices against actual surrounding triangles."""
import bpy,json,hashlib,sys
from pathlib import Path
from mathutils.bvhtree import BVHTree
ROOT=Path(__file__).resolve().parents[2];args=sys.argv[sys.argv.index('--')+1:]if '--'in sys.argv else [];source_frame=int(next((a.split('=',1)[1]for a in args if a.startswith('--frame=')),'1'));OUT=ROOT/'review/I_refinement/nautilus_r1/chamber_motion_r36';s=json.loads((OUT/'build.json').read_text());assert hashlib.sha256((ROOT/s['source']).read_bytes()).hexdigest()==s['source_sha256'];bpy.ops.wm.open_mainfile(filepath=str(ROOT/s['source']));bpy.context.scene.frame_set(source_frame);bpy.context.view_layer.update();films=[bpy.data.objects[r['mesh']]for r in s['membrane_motion']];static=[o for o in bpy.data.objects if o.type=='MESH'and o not in films]
def geometry(objects):
    points=[];faces=[];names=[]
    deps=bpy.context.evaluated_depsgraph_get()
    for o in objects:
        evaluated=o.evaluated_get(deps);m=evaluated.to_mesh();m.calc_loop_triangles();offset=len(points);points.extend(evaluated.matrix_world@v.co for v in m.vertices);faces.extend(tuple(offset+i for i in t.vertices)for t in m.loop_triangles);names.extend([o.name]*len(m.loop_triangles));evaluated.to_mesh_clear()
    return BVHTree.FromPolygons(points,faces,all_triangles=True),points,faces,names
static_tree,_,_,static_names=geometry(static);meshes=[]
for o,row in zip(films,s['membrane_motion']):
    m=o.data;m.calc_loop_triangles();faces=[tuple(t.vertices)for t in m.loop_triangles];basis=m.shape_keys.key_blocks['Basis'];positive=m.shape_keys.key_blocks[row['pressure_key']];negative=m.shape_keys.key_blocks[row['rebound_key']];changed={i for i in range(len(m.vertices))if tuple(positive.data[i].co)!=tuple(basis.data[i].co)or tuple(negative.data[i].co)!=tuple(basis.data[i].co)};moving_faces={i for i,t in enumerate(faces)if any(v in changed for v in t)}
    meshes.append({'object':o,'spec':row,'faces':faces,'basis':basis,'positive':positive,'negative':negative,'changed':changed,'moving_faces':moving_faces})
results=[];contacts=[];baseline_self={};source_fixtures={}
for pattern in [[0.]*12,[1.]*12,[-1.]*12,[.5]*12,[-.5]*12,[1. if i%2 else -1. for i in range(12)],[-1. if i%2 else 1. for i in range(12)]]:
    trees=[]
    for mesh,value in zip(meshes,pattern):
        o=mesh['object'];key=mesh['positive']if value>=0 else mesh['negative'];points=[o.matrix_world@(a.co.lerp(b.co,abs(value)))for a,b in zip(mesh['basis'].data,key.data)];tree=BVHTree.FromPolygons(points,mesh['faces'],all_triangles=True);trees.append(tree)
        hits={(a,b)for a,b in tree.overlap(tree)if a<b and not set(mesh['faces'][a])&set(mesh['faces'][b])};fixture={(a,b)for a,b in tree.overlap(static_tree)if a in mesh['moving_faces']}
        if value==0.:baseline_self[o.name]=hits;source_fixtures[o.name]=fixture
        new_self=hits-baseline_self.get(o.name,set());new_fixture=fixture-source_fixtures.get(o.name,set())
        if new_self:
            details=[]
            for a,b in sorted(new_self)[:30]:
                ids=list(mesh['faces'][a])+list(mesh['faces'][b]);pp=[points[i]for i in ids];details.append({'faces':[a,b],'vertices':[mesh['faces'][a],mesh['faces'][b]],'bounds_world':[[min(p[k]for p in pp)for k in range(3)],[max(p[k]for p in pp)for k in range(3)]],'maximum_face_vertex_displacement':max((points[i]-(o.matrix_world@mesh['basis'].data[i].co)).length for i in ids)})
            contacts.append({'mesh':o.name,'weight':value,'kind':'new_membrane_self_contact','count':len(new_self),'details':details})
        if new_fixture:
            grouped={}
            for a,b in new_fixture:grouped[static_names[b]]=grouped.get(static_names[b],0)+1
            contacts.append({'mesh':o.name,'weight':value,'kind':'new_moving_triangle_fixture_contact','pairs':grouped})
        maximum=max((points[i]-(o.matrix_world@mesh['basis'].data[i].co)).length for i in mesh['changed']);assert maximum<=mesh['spec']['max_world_stroke']+1e-6
        fixed_error=max(((points[i]-(o.matrix_world@mesh['basis'].data[i].co)).length for i in range(len(points))if i not in mesh['changed']),default=0.);assert fixed_error==0.
        results.append({'mesh':o.name,'weight':value,'actual_maximum_world_displacement':maximum,'fixed_vertex_error':fixed_error,'new_self_contacts':len(new_self),'new_fixture_contacts':len(new_fixture)})
    for i,a in enumerate(trees):
        for j,b in enumerate(trees[i+1:],i+1):
            hits=a.overlap(b)
            if hits:contacts.append({'mesh':films[i].name,'other':films[j].name,'kind':'between_membranes','pattern':pattern,'count':len(hits)})
    print('MEMBRANE_POSE',pattern[:3],len(contacts),flush=True)
d={'source_sha256':s['source_sha256'],'source_frame':source_frame,'passed':not contacts,'contacts':contacts,'samples':results,'baseline_self_contacts':{k:len(v)for k,v in baseline_self.items()},'baseline_fixture_contacts_on_moving_triangles':{k:len(v)for k,v in source_fixtures.items()},'scope':'Actual authored membrane vertices at zero, both extrema, half extrema and alternating extrema against evaluated surroundings at the explicit source frame, plus each other. Fixed vertices exact; new self/fixture contacts relative to rest checked. Does not prove continuum, all cover/A motions, global thickness or final visual quality.'};(OUT/('morph_geometry_check.json'if source_frame==1 else 'morph_geometry_frame_%03d.json'%source_frame)).write_text(json.dumps(d,indent=2)+'\n')
