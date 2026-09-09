"""Measure intersecting porcelain surfaces through sampled authored poses.

This is geometric evidence, not a visual-quality verdict. Coincident surface
contacts are reported for review rather than silently treated as clearance.
"""
import bpy,json,sys,math
from pathlib import Path
from mathutils import Matrix,Vector,Quaternion
from mathutils.bvhtree import BVHTree
ROOT=Path(__file__).resolve().parents[2]
C=Matrix(((1,0,0,0),(0,0,1,0),(0,-1,0,0),(0,0,0,1)))
def transform(p):
    return C.inverted()@Matrix.LocRotScale(Vector(p['p']),Quaternion((p['q'][3],*p['q'][:3])),Vector(p['s']))@C
def group(obj):
    while obj:
        if '_C_' in obj.name or '_P_' in obj.name:return obj.name
        obj=obj.parent
    return ''
def mesh_info(obj,depsgraph):
    evaluated=obj.evaluated_get(depsgraph);mesh=evaluated.to_mesh();mesh.calc_loop_triangles()
    vertices=[evaluated.matrix_world@v.co for v in mesh.vertices]
    faces=[tuple(t.vertices) for t in mesh.loop_triangles]
    tree=BVHTree.FromPolygons(vertices,faces,all_triangles=True,epsilon=0)
    mins=Vector([min(v[k] for v in vertices) for k in range(3)])
    maxs=Vector([max(v[k] for v in vertices) for k in range(3)])
    evaluated.to_mesh_clear()
    return tree,mins,maxs
ids=sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else list('FGIJKLMN')
for ident in ids:
    bpy.ops.wm.open_mainfile(filepath=str(ROOT/'blender/collection'/f'{ident}.blend'))
    data=json.loads((ROOT/'app/assets/collection/models'/f'{ident}.json').read_text())
    for obj in bpy.data.objects:obj.animation_data_clear()
    objects=[o for o in bpy.data.objects if o.type=='MESH' and o.name.startswith(ident+'_') and any(m and m.name.startswith('Collection_Ivory') for m in o.data.materials)]
    controls=[(bpy.data.objects[c['name']],[transform(p) for p in c['samples']]) for c in data['controls']]
    parts=[(bpy.data.objects[p['name']],transform(p['home']),C.inverted()@Vector(p['offset']).to_4d(),p['stage'],p.get('route',[])) for p in data['parts']]
    collisions={};lowest=100.;samples=0
    for mode in ['open','explode']:
        for step in range(0,101,5):
            samples+=1
            for obj,poses in controls:obj.matrix_basis=poses[step if mode=='open' else 0]
            for obj,home,offset,stage,route in parts:
                obj.matrix_basis=home
                if mode=='explode':
                    t=max(0,min(1,(step/100-stage*.25)/(1-stage*.25)))
                    if route:
                        for first,last in zip(route,route[1:]):
                            if step/100<=last['at']:
                                u=max(0,min(1,(step/100-first['at'])/(last['at']-first['at'])))
                                obj.location+=(C.inverted()@Vector(first['offset']).lerp(Vector(last['offset']),u*u*(3-2*u)).to_4d()).xyz
                                break
                    else:obj.location+=offset.xyz*t*t*(3-2*t)
            bpy.context.view_layer.update();depsgraph=bpy.context.evaluated_depsgraph_get()
            infos=[mesh_info(obj,depsgraph) for obj in objects]
            lowest=min(lowest,min(info[1].z for info in infos))
            for i,a in enumerate(objects):
                tree,lo,hi=infos[i]
                for j in range(i+1,len(objects)):
                    b=objects[j]
                    if group(a)==group(b):continue
                    other,l2,h2=infos[j]
                    if any(hi[k]<l2[k]-1e-5 or lo[k]>h2[k]+1e-5 for k in range(3)):continue
                    hits=tree.overlap(other)
                    if not hits:continue
                    key=a.name+' / '+b.name
                    if key not in collisions:collisions[key]={'a':a.name,'b':b.name,'first':{'mode':mode,'t':step/100},'samples':0,'max_triangle_pairs':0}
                    collisions[key]['samples']+=1;collisions[key]['max_triangle_pairs']=max(len(hits),collisions[key]['max_triangle_pairs'])
    report={'id':ident,'sample_count':samples,'porcelain_objects':len(objects),'lowest_porcelain_z':lowest,'intersections':list(collisions.values()),'scope':'porcelain against porcelain; same rigid group excluded; contact is reported, not automatically failure','all_clear':len(collisions)==0}
    out=ROOT/'tests/collection/clearance';out.mkdir(parents=True,exist_ok=True)
    (out/f'{ident}.json').write_text(json.dumps(report,indent=2))
    print('CLEARANCE',ident,'pairs',len(collisions),'lowest',lowest,flush=True)
