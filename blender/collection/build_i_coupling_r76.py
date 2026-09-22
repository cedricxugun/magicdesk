"""Replace existing bore walls with continuous tapped walls; no stock union.

The source and all unmodified surfaces remain authoritative. Run with --save
only after the diagnostic checks pass; this never changes the active registry.
"""
import bpy, bmesh, array, hashlib, json, math, sys
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT/'review/I_refinement/nautilus_r1/coupling_repair_r76'
OUT.mkdir(parents=True, exist_ok=True)
s = json.loads((ROOT/'review/I_refinement/nautilus_r1/seam_release_r73/build.json').read_text())
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
assert sha(ROOT/s['source']) == s['source_sha256']
bpy.ops.wm.open_mainfile(filepath=str(ROOT/s['source']))
bpy.context.scene.frame_set(1)
bpy.context.view_layer.update()
mount = bpy.data.objects['IC1_MouthMount']
F = mount.matrix_world.copy()
inv = F.inverted()
allowed = {'IC1_CollarUpper', 'IC1_CollarLower'} | {'IN3_CouplingBolt_%02d'%i for i in range(6)}

def fingerprint(o):
    m=o.data; m.calc_loop_triangles(); h=hashlib.sha256()
    for c,p,w,k in [(m.vertices,'co',3,'f'),(m.loop_triangles,'vertices',3,'I'),(m.corner_normals,'vector',3,'f')]:
        a=array.array(k,[0])*(len(c)*w); c.foreach_get(p,a); h.update(a.tobytes())
    for uv in m.uv_layers:
        a=array.array('f',[0])*(len(uv.data)*2); uv.data.foreach_get('uv',a); h.update(a.tobytes())
    if m.shape_keys:
        for key in m.shape_keys.key_blocks:
            a=array.array('f',[0])*(len(key.data)*3); key.data.foreach_get('co',a); h.update(key.name.encode()); h.update(a.tobytes())
    return h.hexdigest(), [list(r) for r in o.matrix_world], [x.name if x else None for x in m.materials], [p.material_index for p in m.polygons]

protected = {o.name:fingerprint(o) for o in bpy.data.objects if o.type=='MESH' and o.name not in allowed}

def geo(o, space='world'):
    m=o.data; m.calc_loop_triangles()
    v=[o.matrix_world @ p.co if space=='world' else p.co.copy() for p in m.vertices]
    f=[tuple(t.vertices) for t in m.loop_triangles]
    return BVHTree.FromPolygons(v,f,all_triangles=True),v,f

def solid(o):
    bm=bmesh.new(); bm.from_mesh(o.data)
    bad=sum(not e.is_manifold for e in bm.edges)+sum(not v.is_manifold for v in bm.verts)
    volume=bm.calc_volume(signed=True); bm.free()
    t,v,f=geo(o); hits=sorted((a,b) for a,b in t.overlap(t) if a<b and not set(f[a])&set(f[b]))
    return {'name':o.name,'nonmanifold':bad,'volume':volume,'self_contacts':len(hits),'pairs':hits[:30],
            'examples':[[[list(v[k]) for k in f[j]] for j in pair] for pair in hits[:5]]}

def smooth(t):
    t=max(0.,min(1.,t)); return t*t*(3-2*t)

pitch=.0006; clearance=.00003; cut=.6352; tip=.628
# Integer tick stations avoid duplicate floating endpoints and are shared by
# the male and female runout surfaces.
stations=[(12704-i)/20000 for i in range(1,145)]

def male_radius(z,a):
    r=.00305+.00015*(.5+.5*math.cos(math.tau*((z-.6285)/pitch-a/math.tau)))
    r=.0032+(r-.0032)*smooth((.6348-z)/.0004)
    if z<.6285: r=r+(.0027-r)*smooth((.6285-z)/.0005)
    return r

def female_radius(z,a):
    r=male_radius(z,a)+clearance
    if z<.6286: r=r+(.0035-r)*smooth((.6286-z)/.0006)
    if z>.6338: r=r+(.0035-r)*smooth((z-.6338)/.0007)
    return r

centers=[Vector((.502*math.cos(math.pi/6+i*math.tau/6), .502*math.sin(math.pi/6+i*math.tau/6),0)) for i in range(6)]
old_checks={n:solid(bpy.data.objects[n]) for n in ['IC1_CollarUpper','IC1_CollarLower']}
records=[]; topology=[]; seam_repair=None

for index, center in enumerate(centers):
    bolt=bpy.data.objects['IN3_CouplingBolt_%02d'%index]
    M=bolt.matrix_world.copy(); to_parent=inv@M; from_parent=M.inverted()@F
    bm=bmesh.new(); bm.from_mesh(bolt.data)
    bmesh.ops.bisect_plane(bm, geom=list(bm.verts)+list(bm.edges)+list(bm.faces),
        plane_co=from_parent@Vector((center.x,center.y,cut)),
        plane_no=M.to_3x3().transposed()@F.to_3x3().col[2].normalized(), dist=1e-9, clear_inner=True)
    edges=[e for e in bm.edges if e.is_boundary]; vertices={v for e in edges for v in e.verts}
    assert len(vertices)==len(edges) and len(vertices)>=32
    order=sorted(vertices,key=lambda v:math.atan2((to_parent@v.co).y-center.y,(to_parent@v.co).x-center.x))
    angles=[math.atan2((to_parent@v.co).y-center.y,(to_parent@v.co).x-center.x) for v in order]
    assert max(abs(math.hypot((to_parent@v.co).x-center.x,(to_parent@v.co).y-center.y)-.0032) for v in order)<1e-6
    for z in stations:
        ring=[bm.verts.new(from_parent@Vector((center.x+male_radius(z,a)*math.cos(a),center.y+male_radius(z,a)*math.sin(a),z))) for a in angles]
        for k in range(len(order)): bm.faces.new((order[k],order[(k+1)%len(order)],ring[(k+1)%len(order)],ring[k]))
        order=ring
    bm.faces.new(tuple(reversed(order))); bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces))
    bm.to_mesh(bolt.data); bm.free(); bolt.data.update()
    for p in bolt.data.polygons:p.use_smooth=len(p.vertices)==4
    collar_name='IC1_CollarUpper' if index<3 else 'IC1_CollarLower'
    records.append({'index':index,'bolt':bolt.name,'collar':collar_name,'center_parent':list(center),
        'axis_parent':[0,0,1],'pitch_parent':pitch,'radial_clearance_parent':clearance,
        'nominal_female_engagement_parent':[.6286,.6338], 'release_world_distance':.006,
        'release_parent_distance':.006/F.to_3x3().col[2].length})
    print('R76_MALE',index,flush=True)

for name in ['IC1_CollarUpper','IC1_CollarLower']:
    o=bpy.data.objects[name]; old=o.data; to_parent=inv@o.matrix_world; from_parent=to_parent.inverted()
    local=[p.co.copy() for p in old.vertices]; parent=[to_parent@p for p in local]
    removed=set(); rings_by_bore=[]
    for row in [r for r in records if r['collar']==name]:
        c=Vector(row['center_parent'])
        near={i for i,p in enumerate(parent) if math.hypot(p.x-c.x,p.y-c.y)<.00351 and .6269<p.z<.6381}
        wall=[p for p in old.polygons if set(p.vertices).issubset(near) and
              max(parent[i].z for i in p.vertices)-min(parent[i].z for i in p.vertices)>.01]
        assert 64<=len(wall)<=66, (name,row['index'],len(wall))
        edges={}
        for p in wall:
            for edge in p.edge_keys:edges[edge]=edges.get(edge,0)+1
        boundary=[e for e,count in edges.items() if count==1]
        ids={v for e in boundary for v in e}
        lower=sorted([i for i in ids if parent[i].z<.63],key=lambda i:math.atan2(parent[i].y-c.y,parent[i].x-c.x))
        upper=sorted([i for i in ids if parent[i].z>.63],key=lambda i:math.atan2(parent[i].y-c.y,parent[i].x-c.x))
        assert len(lower)==len(upper) and len(ids)==len(boundary), (name,len(lower),len(upper))
        # Preserve every original bore-edge identity; new walls meet exactly
        # these edges instead of nearly coincident Boolean stock boundaries.
        for ring in [lower,upper]:
            assert all(tuple(sorted((ring[k],ring[(k+1)%len(ring)]))) in boundary for k in range(len(ring)))
        removed.update(p.index for p in wall)
        rings_by_bore.append((row,c,lower,upper))
    faces=[]; old_face_indices=[]; source_loops=[]; normals=[]; mat=[]; smoothing=[]
    for p in old.polygons:
        if p.index in removed:continue
        polygons=[tuple(p.vertices)]
        if name=='IC1_CollarUpper' and p.index==3415:
            # The old tessellator spans three nearly collinear boundary edges
            # with a single chord plus two degenerate ears. The chord cuts the
            # neighboring socket face after the installed float transform.
            # Explicitly connect every boundary edge to the SAME existing
            # interior vertex; no vertex, bore, or silhouette is displaced.
            assert list(p.vertices)==[4315,4331,4332,4329,4330,2656,2652,5201,5205,5209,5208,5207,5206,5153]
            old.calc_loop_triangles()
            patch={(5207,5206,5153),(5208,5207,5153),(5208,5153,4332)}
            original=[tuple(t.vertices) for t in old.loop_triangles if t.polygon_index==p.index]
            assert patch.issubset(set(original))
            polygons=[tri for tri in original if tri not in patch]
            replacement=[(5208,5207,4332),(5207,5206,4332),(5206,5153,4332)]
            polygons.extend(replacement)
            old_tree=BVHTree.FromPolygons(local,list(patch),all_triangles=True)
            new_tree=BVHTree.FromPolygons(local,replacement,all_triangles=True)
            distances=[]
            for tri in replacement:
                for weights in [(1/3,1/3,1/3),(.5,.5,0),(.5,0,.5),(0,.5,.5)]:
                    point=sum((local[k]*w for k,w in zip(tri,weights)),Vector())
                    distances.append(old_tree.find_nearest(point)[3])
            seam_repair={'polygon':p.index,'removed_triangulation':list(patch),'replacement':replacement,
                         'vertex_displacement':0.,'sampled_surface_delta_local':max(distances),
                         'reason':'Retain intermediate boundary vertices instead of tessellator chord and degenerate ears.'}
            assert max(distances)<2e-7
        corner={v:i for v,i in zip(p.vertices,p.loop_indices)}
        for face in polygons:
            faces.append(face);old_face_indices.append(p.index)
            loops=[corner[v] for v in face];source_loops.append(loops)
            normals.extend(tuple(old.corner_normals[i].vector) for i in loops)
            mat.append(p.material_index);smoothing.append(p.use_smooth)
    old_loop_count=len(normals)
    for row,c,lower,upper in rings_by_bore:
        angles=[math.atan2(parent[i].y-c.y,parent[i].x-c.x) for i in upper]
        last=upper; n=len(last)
        z_values=[.6375,.636,.6352,.6345]+[z for z in stations if .628<=z<.6345]+[.6275]
        assert all(a>b for a,b in zip(z_values,z_values[1:]))
        for z in z_values:
            ring=[]
            for a in angles:
                r=female_radius(z,a); ring.append(len(local))
                local.append(from_parent@Vector((c.x+r*math.cos(a),c.y+r*math.sin(a),z)))
            for k in range(n):faces.append((last[k],ring[k],ring[(k+1)%n],last[(k+1)%n]));mat.append(0);smoothing.append(True)
            last=ring
        for k in range(n):faces.append((last[k],lower[k],lower[(k+1)%n],last[(k+1)%n]));mat.append(0);smoothing.append(True)
        topology.append({'collar':name,'index':row['index'],'original_boundary_vertices':2*n,'stations':len(z_values),
                         'method':'Replace old cylindrical wall, reuse original boundary indices, continuous threaded loft.'})
    mesh=bpy.data.meshes.new(name+'_R76Tapped'); mesh.from_pydata(local,[],faces); mesh.update()
    for material in old.materials:mesh.materials.append(material)
    for p,m,sm in zip(mesh.polygons,mat,smoothing):p.material_index=m;p.use_smooth=sm
    for layer in old.uv_layers:
        uv=mesh.uv_layers.new(name=layer.name)
        for p,loops in zip(mesh.polygons,source_loops):
            for a,b in zip(p.loop_indices,loops):uv.data[a].uv=layer.data[b].uv
    normals.extend(tuple(mesh.corner_normals[i].vector) for i in range(old_loop_count,len(mesh.loops)))
    mesh.normals_split_custom_set(normals); o.data=mesh
    # Geometry of every retained polygon is exactly unchanged in mesh space.
    assert all(tuple(mesh.vertices[i].co)==tuple(old.vertices[i].co) for i in range(len(old.vertices)))
    assert all(tuple(mesh.polygons[k].vertices)==tuple(old.polygons[j].vertices)
               for k,j in enumerate(old_face_indices) if not(name=='IC1_CollarUpper' and j==3415))
    print('R76_COLLAR',name,solid(o),flush=True)

bpy.context.view_layer.update()
checks=[solid(bpy.data.objects[n]) for n in sorted(allowed)]
fit=[]
for row in records:
    a,_,_=geo(bpy.data.objects[row['bolt']]);b,_,_=geo(bpy.data.objects[row['collar']])
    fit.append({'bolt':row['bolt'],'collar':row['collar'],'contacts':len(a.overlap(b))})
protected_ok=all(fingerprint(bpy.data.objects[n])==v for n,v in protected.items())
proof={'parent_source_sha256':s['source_sha256'],'changed_meshes':sorted(allowed), 'protected_meshes':len(protected),
       'protected_unchanged':protected_ok,'threads':records,'solids':checks,'closed_fit':fit,'bore_topology':topology,
       'baseline_solids':old_checks,'seam_tessellation_repair':seam_repair,
       'scope':'Continuous six tapped bore walls and explicit boundary-respecting triangulation of one old seam polygon. Source static checks only; motion/import/visual checks remain separate.'}
(OUT/'build_check.json').write_text(json.dumps(proof,indent=2)+'\n')
print('R76_RESULT',[(c['name'],c['nonmanifold'],c['self_contacts'],c['volume']) for c in checks],fit,protected_ok,flush=True)
if '--save' not in sys.argv:sys.exit(0)
assert all(c['nonmanifold']==0 and c['volume']>0 and c['self_contacts']==0 for c in checks)
assert all(r['contacts']==0 for r in fit) and protected_ok
source=ROOT/'blender/collection/I_nautilus_coupling_r76.blend'
component=ROOT/'app/assets/collection/components/I_nautilus_coupling_r76.glb'
assert not source.exists() and not component.exists()
bpy.ops.wm.save_as_mainfile(filepath=str(source),compress=True)
body=bpy.data.objects['IN1_BodyRoot'];bpy.ops.object.select_all(action='DESELECT')
for o in [body,*body.children_recursive]:o.select_set(True)
bpy.context.view_layer.objects.active=body
bpy.ops.export_scene.gltf(filepath=str(component),export_format='GLB',use_selection=True,export_animations=False,
    export_morph=True,export_morph_normal=True,export_extras=True)
ART=ROOT/'app/assets/collection/art/I/coupling_r76';ART.mkdir(parents=True,exist_ok=True)
layout=json.loads((ROOT/s['chamber_response_layout'].replace('res://','app/')).read_text())
layout.update(source_sha256=sha(source),component_sha256=sha(component))
(ART/'chamber_layout.json').write_text(json.dumps(layout,indent=2)+'\n')
d={**s,'source':str(source.relative_to(ROOT)).replace('\\','/'),'source_sha256':sha(source),
   'component':str(component.relative_to(ROOT)).replace('\\','/'),'component_sha256':sha(component),
   'coupling_threads':proof,'chamber_response_layout':'res://assets/collection/art/I/coupling_r76/chamber_layout.json',
   'status':'coupling_candidate_motion_import_art_pending'}
(OUT/'build.json').write_text(json.dumps(d,indent=2)+'\n')
print('R76_SAVED',d['source_sha256'],flush=True)
