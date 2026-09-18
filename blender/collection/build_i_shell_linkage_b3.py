"""Independent authored B linkage candidate, using measured B2 four-bar paths.

Preserves A and six panel meshes. Exported geometry and baked source motion;
clearance results are supplied by a separate check, never by this builder.
"""
import bpy,bmesh,math,json,hashlib,sys
import numpy as np
from pathlib import Path
from mathutils import Vector,Matrix
from mathutils.bvhtree import BVHTree
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'blender/collection'))
import i_machined_geometry as h
OUT=ROOT/'review/I_refinement/part_b_shell/linkage_b3';OUT.mkdir(parents=True,exist_ok=True)
seed=json.loads((ROOT/'review/I_refinement/part_b_shell/panels_b2/build.json').read_text())
motion=json.loads((ROOT/'review/I_refinement/part_b_shell/panels_b2/linkage_nested_sweep.json').read_text())
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
assert motion['selection_complete'] and motion['source_sha256']==seed['source_sha256']==sha(ROOT/seed['source'])
TARGET=ROOT/'blender/collection/I_shell_linkage_b3.blend'
if TARGET.exists():
    old=json.loads((OUT/'build.json').read_text());assert old['source_sha256']==sha(TARGET),'Unrecorded source edits'
    (TARGET.parent/'checkpoints'/('I-shell-linkage-b3-'+sha(TARGET)[:12]+'.blend')).write_bytes(TARGET.read_bytes())
bpy.ops.wm.open_mainfile(filepath=str(ROOT/seed['source']));scene=bpy.context.scene;scene.frame_set(1);bpy.context.view_layer.update()
col=bpy.data.collections['I_B_PANELS_B2'];h.configure(col);root=bpy.data.objects['IB2_Module']

def capsule(name,length,radius,depth,parent,material='A_Nickel',loc=(0,0,0),bores=()):
    n=32;profile=[]
    for a in np.linspace(-math.pi/2,math.pi/2,n+1):profile.append((length+radius*math.cos(a),radius*math.sin(a)))
    for a in np.linspace(math.pi/2,3*math.pi/2,n+1):profile.append((radius*math.cos(a),radius*math.sin(a)))
    count=len(profile);vs=[(x,y,z) for z in [-depth/2,depth/2] for x,y in profile]
    fs=[tuple(range(count-1,-1,-1)),tuple(range(count,2*count))]
    fs.extend((i,(i+1)%count,(i+1)%count+count,i+count) for i in range(count))
    m=bpy.data.meshes.new(name+'Mesh');m.from_pydata(vs,[],fs);m.update();o=bpy.data.objects.new(name,m);col.objects.link(o)
    h.finish(o,name,parent,loc,material,.0007)
    for x,r in bores:h.drill(o,r,depth+.02,parent,Vector(loc)+Vector((x,0,0)))
    for p in o.data.polygons:p.use_smooth=abs(p.normal.z)<.8
    return o

def oriented(name,parent,a,b,axis):
    d=(Vector(b)-Vector(a)).normalized();n=Vector(axis).normalized();v=n.cross(d).normalized()
    o=h.empty(name,parent,a);o.rotation_mode='QUATERNION';o.rotation_quaternion=Matrix((d,v,n)).transposed().to_quaternion();return o

def tube(name,points,radius,parent,material='A_Dark'):
    curve=bpy.data.curves.new(name+'Curve','CURVE');curve.dimensions='3D';curve.resolution_u=12;curve.bevel_depth=radius;curve.bevel_resolution=4;curve.use_fill_caps=True
    spline=curve.splines.new('POLY');spline.points.add(len(points)-1)
    for p,co in zip(spline.points,points):p.co=(*co,1)
    o=bpy.data.objects.new(name,curve);col.objects.link(o);o.parent=parent;curve.materials.append(bpy.data.materials['Collection_'+material])
    bpy.ops.object.select_all(action='DESELECT');o.select_set(True);bpy.context.view_layer.objects.active=o;bpy.ops.object.convert(target='MESH');h.parts.append(o.name)
    bm=bmesh.new();bm.from_mesh(o.data);bmesh.ops.remove_doubles(bm,verts=list(bm.verts),dist=.000001);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(o.data);bm.free()
    return o

def saddle(name,panel_obj,parent,pivot,radial,axis):
    m=panel_obj.data;m.calc_loop_triangles();tree=BVHTree.FromPolygons([panel_obj.matrix_world@v.co for v in m.vertices],[tuple(t.vertices) for t in m.loop_triangles],all_triangles=True)
    radial=Vector(radial);axis=Vector(axis);vertical=Vector((0,0,1));points=[];N=48;R=5
    coordinates=[(0.,0.)]+[(math.cos(i*math.tau/N)*r/R*.035,math.sin(i*math.tau/N)*r/R*.031) for r in range(1,R+1) for i in range(N)]
    for u,v in coordinates:
        origin=Vector(pivot)+axis*u+vertical*v+radial*2.
        outer=tree.ray_cast(origin,-radial,4.)
        assert outer[0] is not None,('Saddle left actual shell',name,u,v)
        hit=tree.ray_cast(outer[0]-radial*.00005,-radial,.2)
        assert hit[0] is not None and hit[1].dot(radial)<0,('No inner wall for saddle',name,u,v)
        points.append(hit[0])
    faces=[(0,1+i,1+(i+1)%N) for i in range(N)]
    for r in range(R-1):
        a=1+r*N;b=a+N
        faces.extend((a+i,b+i,b+(i+1)%N,a+(i+1)%N) for i in range(N))
    count=len(points);vs=[tuple(p-radial*d) for d in [.0006,.0076] for p in points]
    fs=list(faces)+[tuple(i+count for i in reversed(f)) for f in faces]
    a=1+(R-1)*N;fs.extend((a+i,a+(i+1)%N,a+(i+1)%N+count,a+i+count) for i in range(N))
    mesh=bpy.data.meshes.new(name+'Mesh');mesh.from_pydata(vs,[],fs);mesh.update();o=bpy.data.objects.new(name,mesh);col.objects.link(o);h.finish(o,name,parent,(0,0,0),'A_Dark')
    for p in mesh.polygons:p.use_smooth=True
    return o,points[0]

panels={};rig_rows=[];fixed_groups=[];attachment_groups=[]
for row in motion['panels']:
    k=row['index'];panel=bpy.data.objects[row['mesh']];parent=panels[5] if k==6 else root
    # Stagger the complete first mechanism along its hinge axis. An axial
    # translation preserves the shell transform, while separating adjacent forks.
    if k==1:
        offset=Vector(row['axis'])*(-.020)
        for key in ['a','d','b0','c0','surface_b','surface_c']:row[key]=list(Vector(row[key])+offset)
        row['packaging_axis_offset']=-.020
    pivot=h.empty('IB3_PanelPivot_%02d'%k,parent);panels[k]=pivot
    world=panel.matrix_world.copy();panel.parent=pivot;panel.matrix_world=world
    if k==6:
        for name in ['IB1_ApexStud','IB1_ApexRedMarker']:
            obj=bpy.data.objects[name];world=obj.matrix_world.copy();obj.parent=pivot;obj.matrix_world=world
    fixed=h.empty('IB3_FixedCarrier_%02d'%k,parent);fixed_groups.append(fixed.name)
    axis=Vector(row['axis']);radial=Vector((math.cos(row['azimuth']),math.sin(row['azimuth']),0))
    # A/D backbone plate is offset from the fork cheeks along the pin axis.
    a,d=Vector(row['a']),Vector(row['d']);basis=oriented('IB3_BackPlateFrame_%02d'%k,fixed,a,d,axis)
    plate_offset=-.031 if k==6 else .043
    plate=capsule('IB3_BackPlate_%02d'%k,(d-a).length,.015 if k in [1,6] else .029,.009 if k==6 else .014,basis,'A_Dark',(0,0,plate_offset),[(0,.0071),((d-a).length,.0071)])
    arm_names=[];pin_names=[];saddle_names=[]
    for label,first,last in [('AB','a','b0'),('DC','d','c0')]:
        start=Vector(row[first]);end=Vector(row[last]);length=(end-start).length
        arm=oriented('IB3_LinkPivot_%02d_%s'%(k,label),fixed,start,end,axis);arm_names.append(arm.name)
        for sign in [-1,1]:
            capsule('IB3_Fork_%02d_%s_%s'%(k,label,'L' if sign<0 else 'R'),length,.018,.008,arm,'A_Nickel',(0,0,sign*.017),[(0,.0105),(length,.0105)])
            for x,tag in [(0,'Fixed'),(length,'Moving')]:
                h.sleeve('IB3_Bush_%02d_%s_%s_%s'%(k,label,tag,sign),.01035,.0071,.008,arm,(x,0,sign*.017),'A_Bronze')
        # One through-pin per joint, with explicit retaining ends and actual bores.
        for location,tag,pin_parent in [(start,'Fixed',fixed),(end,'Moving',pivot)]:
            name='IB3_Pin_%02d_%s_%s'%(k,label,tag);pin_names.append(name)
            fixed_length=.064 if k==6 else .091;fixed_center=-.005 if k==6 else .0105
            h.cylinder(name,.0068,fixed_length if tag=='Fixed' else .063,pin_parent,location+axis*(fixed_center if tag=='Fixed' else 0.),'A_Nickel',axis,.0003)
            for sign in [-1,1]:
                h.sleeve(name+'_Thrust_'+str(sign),.013,.00715,.002,pin_parent,location+axis*(sign*.023),'A_Satin',axis)
                retain_distance=((- .039 if sign<0 else .030) if k==6 else (-.038 if sign<0 else .059)) if tag=='Fixed' else sign*.034
                h.screw(name+'_Retainer_'+str(sign),pin_parent,location+axis*retain_distance,.009 if k==6 and tag=='Fixed' else .011,axis*sign)
        surface=row['surface_b'] if label=='AB' else row['surface_c']
        pad,pad_center=saddle('IB3_Saddle_%02d_%s'%(k,label),panel,pivot,Vector(surface),radial,axis);saddle_names.append(pad.name)
        lug_frame=oriented('IB3_LugFrame_%02d_%s'%(k,label),pivot,end,pad_center,axis)
        lug=capsule('IB3_Lug_%02d_%s'%(k,label),max(.004,(pad_center-end).length-.020),.016,.022,lug_frame,'A_Nickel',(0,0,0),[(0,.0105)])
        h.sleeve('IB3_LugBush_%02d_%s'%(k,label),.01035,.0071,.022,pivot,end,'A_Bronze',axis)
        attachment_groups.append({'panel':panel.name,'saddle':pad.name,'lug':lug.name,'pin':pin_names[-1]})
    rig_rows.append({**row,'panel_pivot':pivot.name,'fixed_carrier':fixed.name,'link_pivots':arm_names,'pin_names':pin_names,'saddle_names':saddle_names})
    print('B3_LINKAGE_BUILT',k,flush=True)

# A continuous fixed structural rail joins the first five local carrier plates.
# This is B's hinge support, not the final C acoustic inner core.
rail_points=[]
for row in rig_rows[:5]:
    p=(Vector(row['a'])+Vector(row['d']))*.5+Vector(row['axis'])*.043
    rail_points.append(p)
rail=tube('IB3_DorsalRail',rail_points,.021,root)
for k,row in enumerate(rig_rows[:5]):
    middle=(Vector(row['a'])+Vector(row['d']))*.5+Vector(row['axis'])*.043
    h.cylinder('IB3_RailBoss_%02d'%(k+1),.032,.024,root,middle,'A_Nickel',Vector(row['axis']))
# Upper carrier is mounted on the fifth shell's moving saddle frame.
tip_row=rig_rows[5];fifth=rig_rows[4]
tip_mid=(Vector(tip_row['a'])+Vector(tip_row['d']))*.5-Vector(tip_row['axis'])*.031
tube('IB3_NestedTipBridge',[Vector(fifth['b0']),Vector(fifth['c0']),tip_mid],.016,panels[5])

# Replace only the old explicitly provisional wide mast/legs. Keep the real base.
for name in ['IB1_ProvisionalMount','IB1_BraceStudy-1','IB1_BraceStudy1','IB1_BraceFootStudy-1','IB1_BraceFootStudy1']:
    o=bpy.data.objects.get(name)
    if o:bpy.data.objects.remove(o,do_unlink=True)
center=Vector(seed['mouth_blender_center']);front=Vector(seed['mouth_blender_forward']);back=-front
up=(Vector((0,0,1))-back*back.z).normalized();right=up.cross(back).normalized()
support_names=[]
for sign in [-1,1]:
    foot=center+right*(sign*.50)-back*.23;foot.z=.62
    mount=center+back*.08-up*.73+right*(sign*.18)
    o=tube('IB3_ProvisionalFrontStrut_'+str(sign),[foot,mount],.035,root,'A_Nickel');support_names.append(o.name)
    h.cylinder('IB3_ProvisionalFoot_'+str(sign),.075,.05,root,foot-Vector((0,0,.025)),'A_Dark')
tube('IB3_RailRootStudy',[center+back*.43-up*.38,rail_points[1]],.025,root)

def solve(row,u):
    axis=Vector(row['axis']);radial=Vector((math.cos(row['azimuth']),math.sin(row['azimuth']),0));up=Vector((0,0,1))
    a=Vector(row['a']);d=Vector(row['d']);b0=Vector(row['b0']);c0=Vector(row['c0'])
    theta=row['theta0']+row['travel']*u
    b=a+radial*(row['length_ab']*math.cos(theta))+up*(row['length_ab']*math.sin(theta))
    delta=d-b;distance=delta.length;direction=delta/distance
    along=(row['length_bc']**2-row['length_dc']**2+distance**2)/(2*distance)
    height=math.sqrt(max(0.,row['length_bc']**2-along**2))
    side=axis.cross(direction)
    c=b+direction*along+side*(height if row['branch']==0 else -height)
    initial=c0-b0;actual=c-b
    angle=math.atan2(axis.dot(initial.cross(actual)),initial.dot(actual))
    matrix=Matrix.Rotation(angle,4,axis);matrix.translation=b-matrix.to_3x3()@b0
    return matrix,b,c

pose_records=[]
for frame in range(1,418):
    release=min(1.,(frame-1)/192) if frame<=225 else max(0.,1.-(frame-225)/192)
    for row in rig_rows:
        u=min(1.,max(0.,release*6-(row['index']-1)));u=u*u*(3.-2.*u);matrix,b,c=solve(row,u)
        pivot=bpy.data.objects[row['panel_pivot']];pivot.matrix_basis=matrix;pivot.rotation_mode='QUATERNION'
        pivot.keyframe_insert('location',frame=frame,group='B Shell Opening');pivot.keyframe_insert('rotation_quaternion',frame=frame,group='B Shell Opening')
        for name,first,last in zip(row['link_pivots'],[Vector(row['a']),Vector(row['d'])],[b,c]):
            o=bpy.data.objects[name];direction=(last-first).normalized();axis=Vector(row['axis']);other=axis.cross(direction)
            o.location=first;o.rotation_quaternion=Matrix((direction,other,axis)).transposed().to_quaternion()
            o.keyframe_insert('rotation_quaternion',frame=frame,group='B Shell Links')
    if frame in list(range(1,194,8))+[225,241,273,305,337,369,401,417]:
        scene.frame_set(frame);bpy.context.view_layer.update()
        pose_records.append({'frame':frame,'release':release,'panel_world_matrices':{row['mesh']:[list(v) for v in bpy.data.objects[row['mesh']].matrix_world] for row in rig_rows}})
scene.frame_end=417;scene.render.fps=60;scene.frame_set(1);bpy.context.view_layer.update()
bpy.ops.wm.save_as_mainfile(filepath=str(TARGET),compress=True)
bpy.ops.object.select_all(action='DESELECT')
for o in col.objects:o.select_set(True)
bpy.context.view_layer.objects.active=root
component=ROOT/'app/assets/collection/components/I_shell_linkage_b3.glb'
bpy.ops.export_scene.gltf(filepath=str(component),export_format='GLB',use_selection=True,export_animations=False,export_extras=True)
report={**seed,'source':str(TARGET.relative_to(ROOT)),'source_sha256':sha(TARGET),'component':str(component.relative_to(ROOT)),'component_sha256':sha(component),'seed_source_sha256':seed['source_sha256'],'rig':rig_rows,'hardware':list(h.parts),'attachments':attachment_groups,'pose_records':pose_records,'provisional_supports':support_names,'status':'finite_linkage_candidate_requires_checks','scope':'Six thin panels and real two-cheek bored four-bars, conforming saddles, dorsal rail, nested cap carrier and baked source motion. No finite-hardware clearance or art acceptance yet. New front supports are provisional; C acoustic core is not built. A music module preserved and separate.'}
report['review_scope']=report['scope']
(OUT/'build.json').write_text(json.dumps(report,indent=2)+'\n')
print('B3_BUILD_COMPLETE',len(h.parts),flush=True)
