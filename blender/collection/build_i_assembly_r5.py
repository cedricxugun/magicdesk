"""Local manufacturing corrections derived from service R4, preserving its rig/take."""
import bpy,json,math,hashlib,shutil,sys,bmesh
from pathlib import Path
from mathutils import Vector,Matrix,Quaternion
from mathutils.bvhtree import BVHTree
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(Path(__file__).parent))
from geometry import Builder
SOURCE=ROOT/'blender/collection/I_service_r4.blend';TARGET=ROOT/'blender/collection/I_assembly_r5.blend'
OUT=ROOT/'review/I_refinement/assembly_r5';OUT.mkdir(parents=True,exist_ok=True)
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
source_spec=json.loads((ROOT/'review/I_refinement/service_r4/build.json').read_text())
assert sha(SOURCE)==source_spec['source_sha256']
if TARGET.exists():
    previous=json.loads((OUT/'build.json').read_text());assert sha(TARGET)==previous['source_sha256'],'Unrecorded assembly-source edit'
    backup=TARGET.parent/'checkpoints'/('I-assembly-'+sha(TARGET)[:12]+'.blend');backup.write_bytes(TARGET.read_bytes())
bpy.ops.wm.open_mainfile(filepath=str(SOURCE));scene=bpy.context.scene;scene.frame_set(1)
root=bpy.data.objects['IH1_MODULE']
P=[Vector(v) for v in [(-.38,-.53,2.25),(-.15,.62,2.10),(.45,.78,2.82),(.45,.74,3.38)]]
def center(t):return P[0]*(1-t)**3+P[1]*3*(1-t)**2*t+P[2]*3*(1-t)*t*t+P[3]*t**3
def tangent(t):return ((P[1]-P[0])*(1-t)**2+(P[2]-P[1])*2*(1-t)*t+(P[3]-P[2])*t*t).normalized()
def smooth(t):t=max(0.,min(1.,t));return t*t*(3-2*t)
R=[(0,.90),(.14,.89),(.28,.93),(.43,.85),(.60,.65),(.76,.39),(.9,.18),(1,.055)]
def radius(t):
    for (a,x),(c,y) in zip(R,R[1:]):
        if t<=c:return x+(y-x)*smooth((t-a)/(c-a))
    return R[-1][1]
frames=[];previous=tangent(0);normal=(Vector((0,0,1))-previous*previous.z).normalized()
for j in range(301):
    axis=tangent(j/300);normal=previous.rotation_difference(axis)@normal;normal=(normal-axis*normal.dot(axis)).normalized();frames.append((normal.copy(),axis.cross(normal).normalized()));previous=axis
def point(t,a):
    n,v=frames[min(300,max(0,round(t*300)))];return center(t)+(n*math.cos(a)+v*math.sin(a))*(radius(t)+.003)
changed=[]
seat_rows=[]
for i in range(6):
    panel=bpy.data.objects['IH1_FrontPanel'+str(i)];lo=i/6+.003;hi=(i+1)/6-.003
    shell=next(o for o in panel.children if 'FrontPorcelain'+str(i)+'_' in o.name)
    shell.data=shell.data.copy();ev=shell.evaluated_get(bpy.context.evaluated_depsgraph_get());mesh=ev.to_mesh();mesh.calc_loop_triangles()
    surface=BVHTree.FromPolygons([shell.matrix_local@v.co for v in mesh.vertices],[tuple(t.vertices) for t in mesh.loop_triangles],all_triangles=True);ev.to_mesh_clear()
    def seated_bead(t,a):
        n,v=frames[min(300,max(0,round(t*300)))];axis=(n*math.cos(a)+v*math.sin(a)).normalized()
        hit,normal,index,d=surface.ray_cast(center(t)+axis*(radius(t)+.08),-axis)
        # At the exact boundary the triangle ray is ambiguous; inset in angle slightly.
        if hit is None:
            a*=.999;n,v=frames[round(t*300)];axis=(n*math.cos(a)+v*math.sin(a)).normalized();hit,normal,index,d=surface.ray_cast(center(t)+axis*(radius(t)+.08),-axis)
        assert hit is not None,(i,t,a)
        return hit+axis*(.0007*min(1.,radius(t)/.5))
    low=lo+.012;high=hi-(.022 if i==1 else .012)
    rolls=sorted([o for o in panel.children if 'RolledPanelLip' in o.name],key=lambda o:o.name)
    sides=sorted([o for o in panel.children if 'SidePanelLip' in o.name],key=lambda o:o.name)
    assert len(rolls)==2 and len(sides)==2
    for obj,t in zip(rolls,[low,high]):
        assert obj.type=='CURVE';obj.data=obj.data.copy();obj.data.bevel_depth=.007;obj.data.use_fill_caps=True
        points=obj.data.splines[0].points
        for j,p in enumerate(points):
            p.co=(*(obj.matrix_local.inverted()@seated_bead(t,math.radians(-76+152*j/(len(points)-1)))),1);p.radius=min(1.,radius(t)/.5)
        changed.append(obj.name)
    for obj,a in zip(sides,[math.radians(-76),math.radians(76)]):
        obj.data=obj.data.copy();obj.data.bevel_depth=.007;obj.data.use_fill_caps=True;points=obj.data.splines[0].points
        for j,p in enumerate(points):
            t=low+(high-low)*j/(len(points)-1);p.co=(*(obj.matrix_local.inverted()@seated_bead(t,a)),1);p.radius=min(1.,radius(t)/.5)
        changed.append(obj.name)
    heads=[o for o in panel.children if '_Screw_' in o.name];slots=[o for o in panel.children if '_ScrewSlot_' in o.name];assert len(heads)==4 and len(slots)==4
    for head in heads:
        slot=min(slots,key=lambda o:(o.location-head.location).length)
        old_choices=[(t,a) for t in [lo+.02*(hi-lo),hi-.02*(hi-lo)] for a in [-.96,.96]]
        old_t,a=min(old_choices,key=lambda pair:((point(*pair)+(frames[round(pair[0]*300)][0]*math.cos(pair[1])+frames[round(pair[0]*300)][1]*math.sin(pair[1]))*.006)-head.location).length)
        t=lo+.032 if old_t<(lo+hi)*.5 else hi-.032
        scale=min(1.,radius(t)/.5);n,v=frames[round(t*300)];location=center(t)+(n*math.cos(a)+v*math.sin(a))*(radius(t)+.008)
        axis=Vector(panel['open_direction'])
        hit,normal,triangle,d=surface.ray_cast(location+axis*.08,-axis)
        assert hit is not None,(head.name,'surface miss')
        head.location=hit+axis*.0045*scale;head.scale=Vector((scale,scale,scale))
        slot.location=head.location+axis*.007*scale;slot.scale=Vector((scale,scale,scale))
        # Seat the head on a bored flat, instead of embedding it in the curved ceramic.
        n=48;q=axis.to_track_quat('Z','Y');r=.0125*scale
        vertices=[hit+q@Vector((r*math.cos(k*math.tau/n),r*math.sin(k*math.tau/n),z*scale)) for z in [-.002,.030] for k in range(n)]
        faces=[tuple(range(n-1,-1,-1)),tuple(range(n,n*2))]+[(k,(k+1)%n,(k+1)%n+n,k+n) for k in range(n)]
        data=bpy.data.meshes.new('FastenerSeatTool');data.from_pydata(vertices,[],faces);tool=bpy.data.objects.new('FastenerSeatTool',data);panel.users_collection[0].objects.link(tool);tool.parent=panel
        bpy.context.view_layer.update();bpy.context.view_layer.objects.active=shell;mod=shell.modifiers.new('Captive screw seating counterbore','BOOLEAN');mod.operation='DIFFERENCE';mod.object=tool;bpy.ops.object.modifier_apply(modifier=mod.name);bpy.data.objects.remove(tool,do_unlink=True)
        seat_rows.append({'head':head.name,'shell':shell.name,'surface':list(hit),'axis':list(axis),'scale':scale,'bottom_plane_offset':-.002*scale,'bore_radius':r})
        changed.extend([head.name,slot.name])
    changed.append(shell.name)
# Find a real free lane for each telescopic guide without changing its axis/stroke.
# Both rod and barrel translate together; rebuild the small clevis to its original joint.
guide_spec=json.loads((ROOT/'review/I_refinement/r1/guide_manifest.json').read_text())
sample_frames=[1,39,151,170,189,208]
guide_names={row[key] for row in guide_spec for key in ['rod','barrel']}
obstacles=[o for o in root.children_recursive if o.type in ['MESH','CURVE'] and o.name not in guide_names]
def geometry(obj):
    ev=obj.evaluated_get(bpy.context.evaluated_depsgraph_get());m=ev.to_mesh();m.calc_loop_triangles();result=([v.co.copy() for v in m.vertices],[tuple(t.vertices) for t in m.loop_triangles]);ev.to_mesh_clear();return result
obstacle_geometry={o.name:geometry(o) for o in obstacles}
guide_geometry={name:geometry(bpy.data.objects[name]) for guide in guide_spec for name in [guide['rod'],guide['barrel']]}
frames_cache={}
for frame in sample_frames:
    scene.frame_set(frame);bpy.context.view_layer.update();vertices=[];faces=[];owners=[]
    for obj in obstacles:
        vs,fs=obstacle_geometry[obj.name];offset=len(vertices);vertices.extend(obj.matrix_world@v for v in vs);faces.extend(tuple(offset+j for j in face) for face in fs);owners.extend([obj]*len(fs))
    frames_cache[frame]={'tree':BVHTree.FromPolygons(vertices,faces,all_triangles=True),'owners':owners,'poses':{name:bpy.data.objects[name].matrix_world.copy() for name in guide_geometry},'panels':{row['panel']:bpy.data.objects[row['panel']].matrix_world.copy() for row in guide_spec}}
scene.frame_set(1);bpy.context.view_layer.update();guide_rows=[]
for guide in guide_spec:
    panel=bpy.data.objects[guide['panel']];rod=bpy.data.objects[guide['rod']];barrel=bpy.data.objects[guide['barrel']]
    index=int(panel.name[-1]);axis=Vector(guide['axis']);lane=tangent((index+.5)/6);lane=(lane-axis*lane.dot(axis)).normalized()
    rod_points,_=guide_geometry[rod.name];local_z=max(v.z for v in rod_points)
    old_tip=rod.matrix_local@Vector((0,0,local_z))
    clevis=min([o for o in panel.children if 'GuideClevis' in o.name],key=lambda o:(o.location-old_tip).length)
    cv,cf=geometry(clevis);ends=[clevis.matrix_local@Vector((0,0,z)) for z in [min(v.z for v in cv),max(v.z for v in cv)]]
    saddle=max(ends,key=lambda p:(p-old_tip).length)
    cross_lane=axis.cross(lane).normalized();world_basis=bpy.data.objects['IH1_FixedChamber'].matrix_world.to_3x3()
    def score(delta):
        collisions=[]
        tip=old_tip+delta;link_axis=saddle-tip;q=link_axis.to_track_quat('Z','Y');n=16
        link_vertices=[p+q@Vector((.0145/math.cos(math.pi/n)*math.cos(k*math.tau/n),.0145/math.cos(math.pi/n)*math.sin(k*math.tau/n),0)) for p in [tip,saddle] for k in range(n)]
        link_faces=[tuple(range(n-1,-1,-1)),tuple(range(n,n*2))]+[(k,(k+1)%n,(k+1)%n+n,k+n) for k in range(n)]
        for frame,cache in frames_cache.items():
            for obj in [rod,barrel]:
                vs,fs=guide_geometry[obj.name];matrix=cache['poses'][obj.name].copy();matrix.translation+=world_basis@delta
                hits=BVHTree.FromPolygons([matrix@v for v in vs],fs,all_triangles=True).overlap(cache['tree'])
                names=set(cache['owners'][j].name for _,j in hits if cache['owners'][j]!=clevis and not (obj==rod and cache['owners'][j].parent==panel))
                collisions.extend((frame,obj.name,name) for name in names)
            vs,fs=guide_geometry[barrel.name];matrix=cache['poses'][barrel.name].copy();matrix.translation+=world_basis@delta
            fixed_barrel=BVHTree.FromPolygons([matrix@v for v in vs],fs,all_triangles=True)
            if delta.length<1e-8:link=BVHTree.FromPolygons([cache['panels'][panel.name]@clevis.matrix_local@v for v in cv],cf,all_triangles=True)
            else:link=BVHTree.FromPolygons([cache['panels'][panel.name]@v for v in link_vertices],link_faces)
            if link.overlap(fixed_barrel):collisions.append((frame,clevis.name,barrel.name))
        return collisions
    primary=[0.]+[sign*value for value in [.012,.024,.036,.048,.060,.072,.084] for sign in [-1.,1.]]
    secondary=[0.,-.012,.012,-.024,.024,-.036,.036]
    choices=[lane*a+cross_lane*b for a in primary for b in secondary if a*a+b*b<=.090*.090]
    scored=[(len(hits:=score(delta)),delta.length,delta,hits) for delta in choices]
    baseline=scored[0];baseline_pairs=set(baseline[3])
    eligible=[row for row in scored if set(row[3]).issubset(baseline_pairs)]
    best=min(eligible,key=lambda row:(row[0],row[1]))
    delta=best[2];guide_rows.append({'rod':rod.name,'barrel':barrel.name,'shift':list(delta),'shift_length':delta.length,'initial_contact_count':baseline[0],'remaining_contact_count':best[0],'remaining':best[3]})
    if delta.length<1e-8:continue
    new_tip=old_tip+delta
    rod.location+=delta;barrel.location+=delta
    # Four-ring cylinder gives the link a small, physical edge break.
    vector=saddle-new_tip;length=vector.length;rr=.014;n=32;bevel=min(.001,length*.1)
    profile=[(rr-bevel,-length/2),(rr,-length/2+bevel),(rr,length/2-bevel),(rr-bevel,length/2)]
    vertices=[(r*math.cos(j*math.tau/n),r*math.sin(j*math.tau/n),z) for r,z in profile for j in range(n)]
    faces=[tuple(range(n-1,-1,-1)),tuple(range(3*n,4*n))]+[(i*n+j,i*n+(j+1)%n,(i+1)*n+(j+1)%n,(i+1)*n+j) for i in range(3) for j in range(n)]
    data=bpy.data.meshes.new(clevis.name+'_LaneLink');data.from_pydata(vertices,[],faces)
    for material in clevis.data.materials:data.materials.append(material)
    for polygon in data.polygons:polygon.use_smooth=len(polygon.vertices)==4
    clevis.data=data;clevis.location=(new_tip+saddle)*.5;clevis.rotation_mode='QUATERNION';clevis.rotation_quaternion=vector.to_track_quat('Z','Y')
    changed.extend([rod.name,barrel.name,clevis.name])
# Relocated fixed cylinders need a real frame mounting bracket, not a floating sleeve.
b=Builder.__new__(Builder);b.id='IS5';b.serial=0;b.root=root;b.upper=bpy.data.objects['IH1_FixedChamber']
b.col=bpy.data.collections.new('I_GUIDE_MOUNTS_R5');scene.collection.children.link(b.col)
b.mats={'GuideMetal':bpy.data.materials['Collection_HelixSupportNickel']}
ns={'bpy':bpy,'math':math,'Vector':Vector,'Matrix':Matrix,'Quaternion':Quaternion,'COL':b.col,'M':b.mats}
exec(compile((ROOT/'blender/fast_geometry.py').read_text(),str(ROOT/'blender/fast_geometry.py'),'exec'),ns);b.fast=ns
rails=[o for o in b.upper.children if o.type=='CURVE' and any(s in o.name for s in ['ChamberSpine','AcousticChamberRib'])]
mount_rows=[]
for row in guide_rows:
    if row['shift_length']<1e-8:continue
    guide=next(g for g in guide_spec if g['rod']==row['rod']);barrel=bpy.data.objects[row['barrel']]
    axis=Vector(guide['axis']);sc=guide['scale'];location=barrel.location-axis*(guide['stroke']+.08*sc)*.20
    candidates=[]
    for rail in rails:
        points=[rail.matrix_local@Vector(p.co[:3]) for p in rail.data.splines[0].points]
        for a,c in zip(points,points[1:]):
            span=c-a;t=max(0.,min(1.,(location-a).dot(span)/span.length_squared));hit=a+span*t
            candidates.append(((hit-location).length,rail,hit,span.normalized()))
    distance,rail,target,target_axis=min(candidates,key=lambda r:r[0])
    assert distance<.24,(barrel.name,'mount rail too remote',distance)
    collar=b.sleeve('GuideClamp',.038*sc,.026*sc,.024*sc,'GuideMetal',b.upper,location,64);collar.rotation_euler=axis.to_track_quat('Z','Y').to_euler();collar.modifiers[0].width=.0004*sc
    rr=rail.data.bevel_depth
    saddle=b.sleeve('FrameSaddle',rr+.005,rr,.018,'GuideMetal',b.upper,target,64);saddle.rotation_euler=target_axis.to_track_quat('Z','Y').to_euler();saddle.modifiers[0].width=.0004
    if distance-(.026*sc+rr)<.008:
        # Nearly touching tubes need one bored saddle; a separate web would cross a tube.
        for obj in [collar,saddle]:
            if obj.data.users>1:obj.data=obj.data.copy()
            bpy.context.view_layer.objects.active=obj
            for modifier in list(obj.modifiers):bpy.ops.object.modifier_apply(modifier=modifier.name)
        bpy.context.view_layer.update();bpy.context.view_layer.objects.active=collar
        mod=collar.modifiers.new('One-piece twin saddle','BOOLEAN');mod.operation='UNION';mod.object=saddle;bpy.ops.object.modifier_apply(modifier=mod.name);bpy.data.objects.remove(saddle,do_unlink=True)
        for center_,axis_,radius_,depth_ in [(barrel.location,axis,.026*sc+.0002,guide['stroke']+.08*sc+.06),(target,target_axis,rr+.0005,.16)]:
            tool=b.cyl('MountBoreTool',radius_,depth_,'GuideMetal',b.upper,center_,axis_.to_track_quat('Z','Y'),96)
            bpy.context.view_layer.update();bpy.context.view_layer.objects.active=collar
            mod=collar.modifiers.new('Actual tube envelope bore','BOOLEAN');mod.operation='DIFFERENCE';mod.object=tool;bpy.ops.object.modifier_apply(modifier=mod.name);bpy.data.objects.remove(tool,do_unlink=True)
        mount_rows.append({'barrel':barrel.name,'rail':rail.name,'fused':collar.name,'distance':distance,'clamp_center':list(location),'saddle_center':list(target)})
        continue
    toward=(target-location).normalized()
    radial=(toward-axis*toward.dot(axis)).normalized()
    first=location+radial*.033*sc;last=target-toward*(rr+.003)
    bridge=b.beam('GuideMountWeb',first,last,max(.003,.006*sc),'GuideMetal',b.upper)
    mount_rows.append({'barrel':barrel.name,'rail':rail.name,'clamp':collar.name,'saddle':saddle.name,'web':bridge.name,'distance':distance,'clamp_center':list(location),'saddle_center':list(target)})
for obj in b.col.objects:
    if obj.type!='MESH':continue
    if obj.data.users>1:obj.data=obj.data.copy()
    bpy.context.view_layer.objects.active=obj
    for modifier in list(obj.modifiers):bpy.ops.object.modifier_apply(modifier=modifier.name)
    bm=bmesh.new();bm.from_mesh(obj.data);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(obj.data);bm.free()
for image in bpy.data.images:
    if image.source=='FILE' and image.filepath and not image.packed_file:image.filepath=bpy.path.relpath(bpy.path.abspath(image.filepath),start=str(TARGET.parent))
scene.frame_set(1);bpy.ops.wm.save_as_mainfile(filepath=str(TARGET))
bpy.ops.object.select_all(action='DESELECT')
for obj in [root]+list(root.children_recursive):obj.select_set(True)
bpy.context.view_layer.objects.active=root;component=ROOT/'app/assets/collection/components/I_assembly_r5.glb'
bpy.ops.export_scene.gltf(filepath=str(component),export_format='GLB',use_selection=True,export_apply=False,export_animations=False,export_morph=True,export_extras=True)
shutil.copy2(ROOT/'review/I_refinement/service_r4/take.json',OUT/'take.json')
result={'source':str(TARGET.relative_to(ROOT)),'source_sha256':sha(TARGET),'input_source_sha256':sha(SOURCE),'component':str(component.relative_to(ROOT)),'component_sha256':sha(component),'groups':source_spec['groups'],'changed_objects':changed,'fastener_seats':seat_rows,'guide_lanes':guide_rows,'guide_mounts':mount_rows,'scope':'Local front-shell bead/fastener seats and paired guide lane corrections with frame brackets; service/pressure animation retained from R4. Full assembly and transit inspection still required.'}
(OUT/'build.json').write_text(json.dumps(result,indent=2)+'\n');print('I_ASSEMBLY_R5',len(changed),'corrected objects',flush=True)
