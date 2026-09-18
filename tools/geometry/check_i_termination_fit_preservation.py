"""Before/after preservation of the source's actual fitted clamp face witnesses."""
import bpy,json,hashlib,sys,struct
from pathlib import Path
from mathutils import Vector,Matrix
from mathutils.bvhtree import BVHTree
ROOT=Path(__file__).resolve().parents[2];args=sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else [];report=ROOT/next((a.split('=',1)[1] for a in args if a.startswith('--report=')),'review/I_refinement/nautilus_r1/throat_terminations_r16/build.json');spec=json.loads(report.read_text());operation=spec['end_finishes'] if 'end_finishes' in spec else spec['interface_trim'];parent=json.loads((ROOT/operation['parent_report']).read_text());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();assert sha(ROOT/spec['source'])==spec['source_sha256'];assert sha(ROOT/parent['source'])==parent['source_sha256']==spec['parent_source_sha256']
bpy.ops.wm.open_mainfile(filepath=str(ROOT/spec['source']));bpy.context.scene.frame_set(1);bpy.context.view_layer.update();fingerprints={r['mesh']:r['source_fingerprint'] for r in operation.get('rounded_frames',operation.get('trim_rows',[]))};names=list(fingerprints);current={n:bpy.data.objects[n] for n in names}
with bpy.data.libraries.load(str(ROOT/parent['source']),link=False) as (src,dst):dst.objects=list(names)
old=dict(zip(names,dst.objects))
def mesh_fingerprint(m):
    h=hashlib.sha256()
    for v in m.vertices:h.update(struct.pack('<3f',*v.co))
    for f in m.polygons:h.update(struct.pack('<'+'I'*len(f.vertices),*f.vertices))
    return h.hexdigest()
def tree(mesh,matrix):
    mesh.calc_loop_triangles();return BVHTree.FromPolygons([matrix@v.co for v in mesh.vertices],[tuple(t.vertices) for t in mesh.loop_triangles],all_triangles=True)
before={};after={}
for n in names:
    assert old[n] is not None and mesh_fingerprint(old[n].data)==fingerprints[n][0]
    matrix=Matrix(fingerprints[n][1]);assert max(abs(matrix[i][j]-current[n].matrix_world[i][j]) for i in range(4) for j in range(4))<1e-7
    before[n]=tree(old[n].data,matrix);after[n]=tree(current[n].data,current[n].matrix_world)
rows=[]
for seat in spec['front_sockets']['seats']:
    axis=(Matrix(seat['matrix_blender']).to_3x3()@Vector((0,0,1))).normalized()
    for part_name,n,sign in [(seat['cap'],seat['source_frame'],-1),(seat['upper'],seat['source_frame'],1),(seat['upper'],seat['source_film'],-1),(seat['outer_stand'],seat['source_film'],1)]:
        if n not in names:continue
        part=bpy.data.objects[part_name];part.data.calc_loop_triangles();direction=axis*sign;tested=0;fitted_count=0;differences=[];changed=[]
        for triangle in part.data.loop_triangles:
            a,b,c=[part.matrix_world@part.data.vertices[i].co for i in triangle.vertices]
            if (b-a).cross(c-a).normalized().dot(direction)<.5:continue
            for weights in [(1/3,1/3,1/3),(.6,.2,.2),(.2,.6,.2),(.2,.2,.6)]:
                p=a*weights[0]+b*weights[1]+c*weights[2];start=p-direction*.00005;original=before[n].ray_cast(start,direction,.05);tested+=1
                gap=original[3]-.00005 if original[0] is not None else None
                # Direction alone includes some edge, bore and opposite-layer
                # faces. Membership comes from the unchanged SOURCE substrate,
                # never from whether the trimmed candidate happens to fit.
                if gap is None or gap<-.00002 or gap>.0006:continue
                fitted_count+=1;current_hit=after[n].ray_cast(start,direction,.05);new_gap=current_hit[3]-.00005 if current_hit[0] is not None else None
                if new_gap is not None:differences.append(abs(new_gap-gap))
                if new_gap is None or abs(new_gap-gap)>.00001:changed.append({'triangle':triangle.index,'point':list(p),'original_gap':gap,'current_gap':new_gap})
        rows.append({'part':part_name,'substrate':n,'direction_samples':tested,'source_fitted_samples':fitted_count,'source_non_contact_direction_samples':tested-fitted_count,'maximum_gap_change':max(differences) if differences else None,'changed_source_fit_count':len(changed),'changed_source_fits':changed[:12],'passed':fitted_count>0 and not changed})
result={'source_sha256':spec['source_sha256'],'parent_source_sha256':parent['source_sha256'],'passed':all(r['passed'] for r in rows),'rows':rows,'scope':'Compares candidate against original source at identical protected clamp-face sample points. Only points fitting the ORIGINAL substrate define bearing witnesses; reports all direction-filtered noncontact points separately. Does not assert every direction-filtered face is a bearing face or prove unsampled continuous coverage, loads, full motion/native or art acceptance.'}
(report.parent/'fit_preservation.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({'passed':result['passed'],'source_fitted_samples':sum(r['source_fitted_samples'] for r in rows),'changed':[(r['part'],r['changed_source_fit_count']) for r in rows if not r['passed']]}),flush=True)
