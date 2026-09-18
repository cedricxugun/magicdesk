"""Separable seam studs and blind-socket retainers on the existing C1 axes."""
import bpy,bmesh,json,hashlib,math,struct,array
from pathlib import Path
from mathutils import Vector,Matrix
from mathutils.bvhtree import BVHTree
ROOT=Path(__file__).resolve().parents[2];OUT=ROOT/'review/I_refinement/nautilus_r1/seam_release_r73';OUT.mkdir(parents=True,exist_ok=True)
s=json.loads((ROOT/'review/I_refinement/nautilus_r1/port_edge_r68/build.json').read_text());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
assert sha(ROOT/s['source'])==s['source_sha256'];bpy.ops.wm.open_mainfile(filepath=str(ROOT/s['source']));bpy.context.scene.frame_set(1);bpy.context.view_layer.update()
mount=bpy.data.objects['IC1_MouthMount'];allowed={'IC1_SeamCrossBolt_-1','IC1_SeamCrossBolt_1'}
def fingerprint(o):
    m=o.data;m.calc_loop_triangles();h=hashlib.sha256()
    for collection,prop,width,code in [(m.vertices,'co',3,'f'),(m.loop_triangles,'vertices',3,'I'),(m.corner_normals,'vector',3,'f')]:
        a=array.array(code,[0])*(len(collection)*width);collection.foreach_get(prop,a);h.update(a.tobytes())
    for uv in m.uv_layers:
        a=array.array('f',[0])*(len(uv.data)*2);uv.data.foreach_get('uv',a);h.update(a.tobytes())
    if m.shape_keys:
        for key in m.shape_keys.key_blocks:
            h.update(key.name.encode());a=array.array('f',[0])*(len(key.data)*3);key.data.foreach_get('co',a);h.update(a.tobytes())
    return [h.hexdigest(),[list(r)for r in o.matrix_world],[a.name if a else None for a in m.materials],[p.material_index for p in m.polygons]]
protected={o.name:fingerprint(o)for o in bpy.data.objects if o.type=='MESH'and o.name not in allowed};print('R73_PROTECTED',len(protected),flush=True)
def smooth(t):t=max(0,min(1,t));return t*t*(3-2*t)
def male_radius(y,theta):
    if y>=-.0678:return .0052
    r=.00495+.0002*(.5+.5*math.cos(math.tau*((y+.068)/.001-theta/math.tau)))
    r=.0052+(r-.0052)*smooth((-.0678-y)/.0003)
    if y<-.0758:r=r+(.0047-r)*smooth((-.0758-y)/.0002)
    if y<-.076:r=.0047+(.0042-.0047)*smooth((-.076-y)/.0003)
    return r
def tree(o):
    m=o.data;m.calc_loop_triangles();v=[o.matrix_world@x.co for x in m.vertices];f=[tuple(t.vertices)for t in m.loop_triangles]
    return BVHTree.FromPolygons(v,f,all_triangles=True),v,f
def check_solid(o):
    bm=bmesh.new();bm.from_mesh(o.data);assert all(e.is_manifold for e in bm.edges)and all(v.is_manifold for v in bm.verts);vol=bm.calc_volume(signed=True);bm.free();assert vol>0
    t,v,f=tree(o);hits=[(a,b)for a,b in t.overlap(t)if a<b and not set(f[a])&set(f[b])];assert not hits,(o.name,hits[:6])
    return {'mesh':o.name,'vertices':len(v),'triangles':len(f),'volume':vol,'self_contacts':0}
records=[]
for sign in [-1,1]:
    pin=bpy.data.objects['IC1_SeamCrossBolt_'+str(sign)];M=pin.matrix_world.copy();to_parent=mount.matrix_world.inverted()@M;from_parent=M.inverted()@mount.matrix_world
    cx=sign*.601;cz=.590;cut=-.0665;bm=bmesh.new();bm.from_mesh(pin.data)
    bmesh.ops.bisect_plane(bm,geom=list(bm.verts)+list(bm.edges)+list(bm.faces),plane_co=from_parent@Vector((cx,cut,cz)),plane_no=M.to_3x3().transposed()@(mount.matrix_world.to_3x3()@Vector((0,1,0))).normalized(),dist=1e-9,clear_inner=True)
    bm.normal_update();boundary=[e for e in bm.edges if len(e.link_faces)==1];vs={v for e in boundary for v in e.verts};assert len(vs)==len(boundary) and len(vs)>=32
    assert all(sum(e in boundary for e in v.link_edges)==2 for v in vs)
    order=sorted(vs,key=lambda v:math.atan2((to_parent@v.co).z-cz,(to_parent@v.co).x-cx));angles=[math.atan2((to_parent@v.co).z-cz,(to_parent@v.co).x-cx)for v in order]
    assert max(abs(math.hypot((to_parent@v.co).x-cx,(to_parent@v.co).z-cz)-.0052)for v in order)<1e-6
    for i in range(1,99):
        y=cut+(-.0763-cut)*i/98.;ring=[bm.verts.new(from_parent@Vector((cx+male_radius(y,a)*math.cos(a),y,cz+male_radius(y,a)*math.sin(a))))for a in angles]
        for j in range(len(order)):bm.faces.new((order[j],order[(j+1)%len(order)],ring[(j+1)%len(order)],ring[j]))
        order=ring
    bm.faces.new(tuple(reversed(order)));bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(pin.data);bm.free();pin.data.update()
    # New inner surfaces only at the changed stud; the original positive head remains.
    for f in pin.data.polygons:f.use_smooth=len(f.vertices)==4
    N=96;angles2=[math.tau*i/N for i in range(N)];verts=[];faces=[];rings=[]
    def ring(y,radius):
        ids=[]
        for a in angles2:
            rr=radius(a)if callable(radius)else radius;ids.append(len(verts));verts.append((cx+rr*math.cos(a),y,cz+rr*math.sin(a)))
        rings.append(ids);return ids
    def join(a,b):
        for i in range(N):faces.append((a[i],a[(i+1)%N],b[(i+1)%N],b[i]))
    entry=ring(-.067,.00565);last=entry
    for y,radius in [(-.067,.00815),(-.06735,.0085),(-.07865,.0085),(-.079,.00815)]:n=ring(y,radius);join(last,n);last=n
    def hex_radius(a):return (.0042*math.cos(math.pi/6))/math.cos((a+math.pi/6)%(math.pi/3)-math.pi/6)
    n=ring(-.079,hex_radius);join(last,n);last=n;n=ring(-.0773,hex_radius);join(last,n)
    center=len(verts);verts.append((cx,-.0773,cz))
    for i in range(N):faces.append((n[i],n[(i+1)%N],center))
    last=entry
    # Match the actual male axial breakpoints at the tapered runout. The
    # previous independent grids chorded across that transition and intersected
    # even when their ideal radial functions were separated.
    inner_stations=sorted({cut+(-.0763-cut)*i/98. for i in range(1,99)if cut+(-.0763-cut)*i/98.<-.067}|{-.0764,-.0765,-.0766},reverse=True)
    for y in inner_stations:
        def inner(a):
            r=male_radius(y,a)+.00004
            if y>-.0678:r=r+(.00565-r)*smooth((y+.0678)/.0008)
            if y<-.076:r=r+(.00565-r)*smooth((-.076-y)/.0003)
            return r
        n=ring(y,inner);join(n,last);last=n
    center=len(verts);verts.append((cx,-.0766,cz))
    for i in range(N):faces.append((last[(i+1)%N],last[i],center))
    mesh=bpy.data.meshes.new('IC73_SeamSocketMesh_'+str(sign));mesh.from_pydata(verts,[],faces);mesh.update();cap=bpy.data.objects.new('IC73_SeamSocket_'+str(sign),mesh);pin.users_collection[0].objects.link(cap);cap.parent=mount;mesh.materials.append(pin.data.materials[0])
    bm=bmesh.new();bm.from_mesh(mesh);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(mesh);bm.free();mesh.update()
    for f in mesh.polygons:f.use_smooth=abs(f.normal.y)<.95
    bpy.context.view_layer.update();pr=check_solid(pin);cr=check_solid(cap)
    pt,pv,pf=tree(pin);ct,cv,cf=tree(cap);pairs=pt.overlap(ct)
    if pairs:
        inv=mount.matrix_world.inverted();examples=[]
        for a,b in pairs[:20]:examples.append({'male':[list(inv@pv[i])for i in pf[a]],'female':[list(inv@cv[i])for i in cf[b]]})
        (OUT/'closed_contact_diagnostic.json').write_text(json.dumps({'sign':sign,'count':len(pairs),'examples':examples},indent=2)+'\n')
    assert not pairs,('Stud/socket overlap',sign,len(pairs))
    records.append({'sign':sign,'pin':pr,'socket':cr,'axis_parent':[0,1,0],'center_parent':[cx,0,cz],'socket_bounds_parent_y':[-.079,-.067],'thread_pitch':.001,'nominal_thread_radial_clearance':.00004,'radial_thread_depth':.0002,'radial_interlock':.00016,'blind_wall_thickness':.0007,'pin_socket_contacts':len(pairs)})
    print('R73_SEPARABLE_PAIR',sign,pr,cr,flush=True)
# Use the accessible removable socket above the positive seam, preserving the
# existing clamp bores. The negative seam socket remains below its seam.
center=Vector((.601,0,.590));change=Matrix.Translation(center)@Matrix.Rotation(math.pi,4,'X')@Matrix.Translation(-center)
for name in ['IC1_SeamCrossBolt_1','IC73_SeamSocket_1']:bpy.data.objects[name].matrix_local=change@bpy.data.objects[name].matrix_local
bpy.context.view_layer.update()
for record in records:record['cap_side']=1 if record['sign']==1 else -1
assert all(fingerprint(bpy.data.objects[n])==v for n,v in protected.items())
source=ROOT/'blender/collection/I_nautilus_seam_release_r73.blend';component=ROOT/'app/assets/collection/components/I_nautilus_seam_release_r73.glb';assert not source.exists();bpy.ops.wm.save_as_mainfile(filepath=str(source),compress=True)
body=bpy.data.objects['IN1_BodyRoot'];bpy.ops.object.select_all(action='DESELECT')
for o in [body,*body.children_recursive]:o.select_set(True)
bpy.context.view_layer.objects.active=body;bpy.ops.export_scene.gltf(filepath=str(component),export_format='GLB',use_selection=True,export_animations=False,export_morph=True,export_morph_normal=True,export_extras=True)
ART=ROOT/'app/assets/collection/art/I/seam_release_r73';ART.mkdir(parents=True,exist_ok=True);layout=json.loads((ROOT/s['chamber_response_layout'].replace('res://','app/')).read_text());layout.update(source_sha256=sha(source),component_sha256=sha(component));(ART/'chamber_layout.json').write_text(json.dumps(layout,indent=2)+'\n')
proof={'source_sha256':sha(source),'parent_source_sha256':s['source_sha256'],'changed_meshes':sorted(allowed),'protected_meshes':len(protected),'pairs':records,'scope':'Separable stud/retainer with actual male/female relief and blind hex socket. Positive original heads retained, negative caps lengthened outward locally. Neighbor, motion, clamp unlock, import and visual checks pending; no load-bearing certification.'}
d={**s,'source':str(source.relative_to(ROOT)),'source_sha256':sha(source),'component':str(component.relative_to(ROOT)),'component_sha256':sha(component),'seam_fasteners':proof,'chamber_response_layout':'res://assets/collection/art/I/seam_release_r73/chamber_layout.json','status':'separable_fastener_candidate_checks_pending'}
(OUT/'build.json').write_text(json.dumps(d,indent=2)+'\n');(OUT/'build_check.json').write_text(json.dumps(proof,indent=2)+'\n');print('R73_SAVED',d['source_sha256'],flush=True)
