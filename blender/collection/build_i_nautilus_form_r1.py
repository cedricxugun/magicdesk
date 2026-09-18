"""Round planispiral form candidate, before detailed manufacture. Keeps A/base."""
import bpy,bmesh,math,json,hashlib,sys,shutil
from pathlib import Path
from mathutils import Vector,Matrix,Quaternion
from mathutils.bvhtree import BVHTree
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(Path(__file__).parent))
args=sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else []
config_path=next((a.split('=',1)[1] for a in args if a.startswith('--shape-config=')),None)
CONFIG=json.loads((ROOT/config_path).read_text()) if config_path else {}
OUT=ROOT/CONFIG.get('out','review/I_refinement/nautilus_r1');OUT.mkdir(parents=True,exist_ok=True)
TARGET=ROOT/CONFIG.get('source','blender/collection/I_nautilus_form_r1.blend');sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
if CONFIG:assert TARGET.name!='I_nautilus_form_r1.blend','Shape variants must preserve the checked source'
spec=json.loads((ROOT/'review/I_refinement/part_a_mouth/shutter_r2/collar_clamps/build.json').read_text())
assert sha(ROOT/spec['source'])==spec['source_sha256']
if TARGET.exists():
    old=json.loads((OUT/'build.json').read_text());assert sha(TARGET)==old['source_sha256'],'Unrecorded source edits'
    checkpoint=OUT/'iterations'/old['source_sha256'][:12];checkpoint.mkdir(parents=True,exist_ok=True)
    (checkpoint/'build.json').write_text(json.dumps(old,indent=2)+'\n')
    if (OUT/'views').exists():shutil.copytree(OUT/'views',checkpoint/'views',dirs_exist_ok=True)
    for check in OUT.glob('*check.json'):shutil.copy2(check,checkpoint/check.name)
    (TARGET.parent/'checkpoints'/('I-nautilus-form-'+old['source_sha256'][:12]+'.blend')).write_bytes(TARGET.read_bytes())
bpy.ops.wm.read_factory_settings(use_empty=True);scene=bpy.context.scene
col=bpy.data.collections.new('I_NAUTILUS_FORM');scene.collection.children.link(col)
def mat(name,color,metal,rough,coat=0):
    m=bpy.data.materials.new(name);m.use_nodes=True;p=m.node_tree.nodes.get('Principled BSDF');p.inputs['Base Color'].default_value=(*color,1);p.inputs['Metallic'].default_value=metal;p.inputs['Roughness'].default_value=rough;p.inputs['Coat Weight'].default_value=coat;p.inputs['Coat Roughness'].default_value=.19;return m
ivory=mat('IN1_Porcelain',(.73,.69,.60),0,.23,.55);nickel=mat('IN1_Nickel',(.40,.39,.34),.88,.25);bronze=mat('IN1_AcousticBronze',(.24,.125,.042),.83,.31);dark=mat('IN1_DarkAcoustic',(.055,.043,.03),.50,.36);red=mat('IN1_EnamelRed',(.24,.008,.003),.10,.25,.4)
def empty(name,parent=None):
    o=bpy.data.objects.new(name,None);col.objects.link(o);o.parent=parent;return o
root=empty('IN1_BodyRoot')
def mesh(name,verts,faces,material,parent=root):
    m=bpy.data.meshes.new(name+'Mesh');m.from_pydata(verts,[],faces);m.update();o=bpy.data.objects.new(name,m);col.objects.link(o);o.parent=parent;m.materials.append(material)
    bm=bmesh.new();bm.from_mesh(m);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(m);bm.free()
    for p in m.polygons:p.use_smooth=True
    return o
def cylinder(name,radius,depth,loc,axis,material,parent=root):
    bpy.ops.mesh.primitive_cylinder_add(vertices=64,radius=radius,depth=depth);o=bpy.context.object;o.name=name
    for c in list(o.users_collection):c.objects.unlink(o)
    col.objects.link(o);o.parent=parent;o.location=loc;o.rotation_mode='QUATERNION';o.rotation_quaternion=Vector(axis).to_track_quat('Z','Y');o.data.materials.append(material)
    bevel=o.modifiers.new('Soft machined edge','BEVEL');bevel.width=.006;bevel.segments=3;bpy.context.view_layer.objects.active=o;bpy.ops.object.modifier_apply(modifier=bevel.name)
    for p in o.data.polygons:p.use_smooth=abs(p.normal.z)<.999
    return o
def pipe(name,points,radius,material,parent=root,profile=None):
    curve=bpy.data.curves.new(name+'Curve','CURVE');curve.dimensions='3D';curve.resolution_u=1;curve.bevel_depth=radius;curve.bevel_resolution=3;curve.use_fill_caps=True
    spline=curve.splines.new('POLY');spline.points.add(len(points)-1)
    for i,(p,v) in enumerate(zip(spline.points,points)):
        p.co=(*v,1)
        if profile is not None:p.radius=profile[i]
    o=bpy.data.objects.new(name,curve);col.objects.link(o);o.parent=parent;curve.materials.append(material)
    bpy.ops.object.select_all(action='DESELECT');bpy.context.view_layer.objects.active=o;o.select_set(True);bpy.ops.object.convert(target='MESH');o.select_set(False)
    # Blender curve caps have coincident independent loops: weld the actual ends.
    bm=bmesh.new();bm.from_mesh(o.data);bmesh.ops.remove_doubles(bm,verts=list(bm.verts),dist=1e-6);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(o.data);bm.free()
    return o
center=Vector(CONFIG.get('mouth_center',[-.52,-.52,1.61]));front=Vector(CONFIG.get('mouth_normal',[-.34,-.935,.10])).normalized();back=-front
up=(Vector((0,0,1))-back*back.z).normalized();right=up.cross(back).normalized();basis=Matrix((right,up,back)).transposed();scale=.70
placement=basis.to_4x4();placement.translation=center;placement=placement@Matrix.Diagonal((scale,scale,scale,1.))
with bpy.data.libraries.load(str(ROOT/spec['source']),link=False) as (src,dst):dst.collections=['MODULE_IAM']
scene.collection.children.link(dst.collections[0]);bpy.data.objects['IAM_MODULE'].matrix_world=placement
# Measured A envelope from the earlier mouth-only study, rescaled uniformly.
profile=json.loads((ROOT/'review/I_refinement/part_b_shell/form_b1/mouth_clearance_profile.json').read_text())
assert profile['source_sha256']==spec['source_sha256']
ratio=scale/float(profile['uniform_scale']);cut_profile=[(d*ratio,r*ratio+.008) for d,r in profile['profile']]
def interpolate_profile(rows,depth):
    if depth<=rows[0][0]:return rows[0][1]
    for (a,x),(b,y) in zip(rows,rows[1:]):
        if depth<=b:return x+(y-x)*(depth-a)/(b-a)
    return rows[-1][1]
# Include the fixed formed shoulder, whose back flare exceeded the old A-only
# cavity between profile samples. Keep its measured axial/radial dimensions.
shoulder_outer=[(.105*ratio,.735*ratio),(.145*ratio,.748*ratio),(.220*ratio,.771*ratio)]
depths=sorted(set([d for d,r in cut_profile]+[shoulder_outer[0][0]-.006+i*.003 for i in range(38)]))
expanded=[]
for depth in depths:
    radius=interpolate_profile(cut_profile,depth)
    if shoulder_outer[0][0]-.006<=depth<=shoulder_outer[-1][0]+.006:radius=max(radius,interpolate_profile(shoulder_outer,depth)+.006)
    expanded.append((depth,radius))
cut_profile=expanded
cut_profile=[(-1.,cut_profile[0][1])]+cut_profile+[(cut_profile[-1][0]+.02,cut_profile[-1][1])]
vs=[];fs=[];n=128
for depth,radius in cut_profile:
    for k in range(n):
        a=math.tau*k/n;vs.append(tuple(center+right*(radius*math.cos(a))+up*(radius*math.sin(a))+back*depth))
for j in range(len(cut_profile)-1):
    for k in range(n):fs.append((j*n+k,j*n+(k+1)%n,(j+1)*n+(k+1)%n,(j+1)*n+k))
fs.extend([tuple(range(n-1,-1,-1)),tuple((len(cut_profile)-1)*n+k for k in range(n))])
cutter=mesh('IN1_MeasuredMouthTool',vs,fs,dark)
def cut(o):
    bpy.context.view_layer.update();bpy.context.view_layer.objects.active=o
    modifier=o.modifiers.new('Actual A clearance','BOOLEAN');modifier.operation='DIFFERENCE';modifier.solver='EXACT';modifier.object=cutter;bpy.ops.object.modifier_apply(modifier=modifier.name)
def soften_panel(o):
    o.data.materials.append(nickel)
    bm=bmesh.new();bm.from_mesh(o.data);bm.normal_update()
    for edge in bm.edges:
        if len(edge.link_faces)==2:edge.smooth=edge.calc_face_angle()<.40
    bm.to_mesh(o.data);bm.free()
    bpy.context.view_layer.objects.active=o
    if not CONFIG.get('formed_throat'):
        m=o.modifiers.new('Ceramic cut-edge metal binding','BEVEL');m.width=.0035;m.segments=3;m.limit_method='ANGLE';m.angle_limit=.35;m.harden_normals=True;m.material=1
        bpy.ops.object.modifier_apply(modifier=m.name)
    m=o.modifiers.new('Broad ceramic corner normals','WEIGHTED_NORMAL');m.keep_sharp=True;m.weight=30
    bpy.ops.object.modifier_apply(modifier=m.name)
C=Vector(CONFIG.get('body_center',[.12,.16,1.96]));radii=Vector(CONFIG.get('body_radii',[1.01,.59,1.10]))
throat_rows=[]
def point(phi,theta,inset=0.):
    # Broad coiled chamber divisions. No tower or elongated conical apex.
    a=theta+1.12*math.cos(phi)+.10*math.sin(phi)**2*math.sin(theta+1.)
    rx=radii.x-inset;ry=radii.y-inset;rz=radii.z-inset
    return C+Vector((rx*math.sin(phi)*math.cos(a),-ry*math.cos(phi),rz*math.sin(phi)*math.sin(a)))
def patch(name,a,b,material,inset=0.,thickness=.024,fullness=.055,phi0=.14,phi1=math.pi-.14):
    nu=52;nv=64;verts=[];faces=[]
    for depth in [inset,inset+thickness]:
        for i in range(nu+1):
            phi=phi0+(phi1-phi0)*i/nu
            for j in range(nv+1):
                theta=a+(b-a)*j/nv;v=j/nv;p=point(phi,theta,depth)
                if material==ivory:
                    direction=(p-C).normalized();p+=direction*(fullness*math.sin(math.pi*v)**1.4*math.sin(phi))
                verts.append(tuple(p))
    stride=nv+1;count=(nu+1)*stride
    for layer in range(2):
        base=layer*count
        for i in range(nu):
            for j in range(nv):
                q=(base+i*stride+j,base+i*stride+j+1,base+(i+1)*stride+j+1,base+(i+1)*stride+j)
                faces.append(q if layer==0 else q[::-1])
    perimeter=list(range(stride))+[i*stride+nv for i in range(1,nu+1)]+[nu*stride+j for j in range(nv-1,-1,-1)]+[i*stride for i in range(nu-1,0,-1)]
    for i,x in enumerate(perimeter):
        y=perimeter[(i+1)%len(perimeter)];faces.append((x,y,y+count,x+count))
    o=mesh(name,verts,faces,material)
    if CONFIG.get('formed_throat'):
        from i_nautilus_formed_throat import extend_skin
        formed=extend_skin(o,center,back,right,up,C,radii,lambda d:interpolate_profile(cut_profile,d) if d<=cut_profile[-1][0] else -1.)
        if formed:
            throat_rows.append(formed)
            bm=bmesh.new();bm.from_mesh(o.data)
            print('FORMED_BEFORE_CLEARANCE',name,len(bm.faces),bm.calc_volume(),sum(not e.is_manifold for e in bm.edges),flush=True);bm.free()
    # The formed source already encloses the measured A envelope. Reapplying
    # its old axial Boolean tears almost tangent thin lofts into fragments.
    # Renewed actual-mesh clearance checks, not another Boolean, verify the fit.
    if not CONFIG.get('formed_throat'):cut(o)
    return o
def chamber_skin(name,a,b,material,inset,thickness,windows=False,corrugation=False,periodic=False,segments=24,start_phi=.20):
    nu=64;nv=segments if not periodic else 144;stride=nv if periodic else nv+1
    verts=[];quads=[];edges={}
    for depth in [inset,inset+thickness]:
        for i in range(nu+1):
            phi=start_phi+(math.pi-.20-start_phi)*i/nu
            for j in range(stride):
                v=j/nv;d=depth
                if corrugation:d+=.010*math.cos(phi*48.)*math.sin(math.pi*v)**2
                verts.append(tuple(point(phi,a+(b-a)*v,d)))
    count=(nu+1)*stride
    for i in range(nu):
        phi=start_phi+(math.pi-.20-start_phi)*(i+.5)/nu
        for j in range(nv):
            v=(j+.5)/nv
            opening=windows and ((.33<phi<1.43 or 1.70<phi<2.80) and .25<v<.75)
            vent=windows and i%4==1 and (.35<phi<1.45 or 1.70<phi<2.80) and j in [2,3,20,21]
            if opening or vent:continue
            nj=(j+1)%stride;q=(i*stride+j,i*stride+nj,(i+1)*stride+nj,(i+1)*stride+j);quads.append(q)
            for k,x in enumerate(q):
                y=q[(k+1)%4];key=tuple(sorted((x,y)))
                edges.setdefault(key,[]).append((x,y))
    faces=quads+[tuple(x+count for x in q[::-1]) for q in quads]
    for pairs in edges.values():
        if len(pairs)==1:
            x,y=pairs[0];faces.append((x,y,y+count,x+count))
    o=mesh(name,verts,faces,material);cut(o)
    if windows and len(o.data.polygons):
        o.data.materials.append(nickel);bpy.context.view_layer.objects.active=o
        bevel=o.modifiers.new('Formed vent lips','BEVEL');bevel.width=.0012;bevel.segments=2;bevel.limit_method='ANGLE';bevel.angle_limit=.50;bevel.material=1
        bpy.ops.object.modifier_apply(modifier=bevel.name)
    return o
panels=[];boundaries=[math.radians(a) for a in [-176,-133,-80,-8,76,144,184]]
fullness_values=[.035,.065,.090,.115,.095,.050]
for index,(a,b) in enumerate(zip(boundaries,boundaries[1:])):
    active=index+1 in CONFIG.get('active_panels',[3,4,5,6])
    o=patch(f'IN1_PorcelainPanel_{index+1:02d}',a+.011,b-.011,ivory,fullness=fullness_values[index],phi0=.19,phi1=math.pi/2-.015 if active else math.pi-.19)
    if index==4 and CONFIG.get('fixed_mouth_cheek_below_z'):
        # The lower throat cheek is part of the fixed collar, not the upper
        # hood. Keeping it on the hood catches the lip at the mouth equator.
        fixed=o.copy();fixed.data=o.data.copy();fixed.name='IN1_FixedMouthCheek05';col.objects.link(fixed)
        height=CONFIG['fixed_mouth_cheek_below_z']
        for part,plane_z,keep_upper in [(o,height+.002,True),(fixed,height-.002,False)]:
            bm=bmesh.new();bm.from_mesh(part.data)
            bmesh.ops.bisect_plane(bm,geom=list(bm.verts)+list(bm.edges)+list(bm.faces),dist=1e-8,plane_co=Vector((0,0,plane_z)),plane_no=Vector((0,0,1)),clear_inner=keep_upper,clear_outer=not keep_upper)
            edges=[e for e in bm.edges if len(e.link_faces)==1 and all(abs(v.co.z-plane_z)<2e-6 for v in e.verts)]
            bmesh.ops.holes_fill(bm,edges=edges,sides=0);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(part.data);bm.free()
    if index!=4 or CONFIG.get('formed_throat'):soften_panel(o)
    if active:
        rear=patch(f'IN1_FixedRearShell_{index+1:02d}',a+.011,b-.011,ivory,fullness=fullness_values[index],phi0=math.pi/2+.015,phi1=math.pi-.19)
        soften_panel(rear)
    # Source motion is a broad form study; detailed links/stops are downstream.
    mid=(a+b)*.5
    outer_axis=point(math.pi/2,mid)-C;outer_axis.y=0;outer_axis.normalize()
    # The pin sits outside the real domed porcelain, not inside the bare ellipsoid.
    pivot=point(math.pi/2,mid)+outer_axis*(fullness_values[index]+.035)
    axis=(point(math.pi/2,mid-.001)-point(math.pi/2,mid+.001)).normalized()
    carrier=empty(f'IN1_PanelPivot_{index+1:02d}',root);carrier.location=pivot
    o.parent=carrier;o.location=-pivot
    test_point=point(.90,mid);direction=(test_point-C).normalized()
    sign=1 if axis.cross(test_point-pivot).dot(direction)>0 else -1
    angle=math.radians([0,0,25,28,25,22][index])*sign if active else 0.
    radial=point(math.pi/2,mid)-C;radial.y=0;radial.normalize()
    radial_travel=.080 if index==5 else .055
    forward_travel=.065 if index==5 else .085
    lift=radial*radial_travel+Vector((0,-forward_travel,0)) if active else Vector((0,0,0))
    if active and str(index+1) in CONFIG.get('panel_lifts',{}):lift=Vector(CONFIG['panel_lifts'][str(index+1)])
    if index==4 and not CONFIG.get('formed_throat'):
        # The fixed shoulder has a back flare. Machine the small withdrawing
        # cover edge against its actual straight-lift envelope, avoiding a hook.
        zs=[shoulder_outer[0][0]-.006,*[d for d,r in shoulder_outer],shoulder_outer[-1][0]+.006]
        vv=[];ff=[];segments=96
        for depth in zs:
            radius=interpolate_profile(shoulder_outer,depth)+.006
            for k in range(segments):
                angle0=math.tau*k/segments;vv.append(tuple(center+right*(radius*math.cos(angle0))+up*(radius*math.sin(angle0))+back*depth))
        for j in range(len(zs)-1):
            for k in range(segments):ff.append((j*segments+k,j*segments+(k+1)%segments,(j+1)*segments+(k+1)%segments,(j+1)*segments+k))
        ff += [tuple(range(segments-1,-1,-1)),tuple((len(zs)-1)*segments+k for k in range(segments))]
        # One convex swept solid avoids cascading almost-coincident cuts on a
        # thin beveled cover. The shoulder/straight-lift envelope is convex.
        hull=bmesh.new()
        for v in vv:
            hull.verts.new(v);hull.verts.new(Vector(v)-lift)
        bmesh.ops.convex_hull(hull,input=list(hull.verts))
        used=list({v for face in hull.faces for v in face.verts});indices={v:i for i,v in enumerate(used)}
        hull_vertices=[tuple(v.co) for v in used];hull_faces=[tuple(indices[v] for v in face.verts) for face in hull.faces];hull.free()
        allowance=mesh('IN1_TemporaryShoulderAllowance',hull_vertices,hull_faces,dark)
        bpy.context.view_layer.update();protected_z=max((o.matrix_world@v.co).z for v in o.data.vertices)
        assert protected_z>max((allowance.matrix_world@v.co).z for v in allowance.data.vertices)+.10
        bpy.context.view_layer.objects.active=o
        mod=o.modifiers.new('Withdrawable shoulder edge','BOOLEAN');mod.operation='DIFFERENCE';mod.solver='EXACT';mod.object=allowance;bpy.ops.object.modifier_apply(modifier=mod.name)
        assert len(o.data.polygons)>64 and max((o.matrix_world@v.co).z for v in o.data.vertices)>protected_z-.00001,'Shoulder cut removed protected cover geometry'
        bpy.data.objects.remove(allowance,do_unlink=True)
        soften_panel(o)
    for boundary in [a+.014,b-.014]:
        end_phi=math.pi/2-.02 if active else math.pi-.20
        points=[point(.20+(end_phi-.20)*j/90,boundary,-.004) for j in range(91)]
        # Mouth region cuts the sweep; keep only uninterrupted segments outside A.
        segments=[];segment=[];inv=placement.inverted()
        for p in points:
            local=inv@p;rho=math.hypot(local.x,local.y)
            outside=(rho>.92 or local.z>1.7) and (not CONFIG.get('formed_throat') or (p-center).dot(back)>.585)
            if index==4 and CONFIG.get('fixed_mouth_cheek_below_z'):outside=outside and p.z>CONFIG['fixed_mouth_cheek_below_z']+.004
            if outside:segment.append(p)
            elif segment:
                if len(segment)>1:segments.append(segment)
                segment=[]
        if len(segment)>1:segments.append(segment)
        for number,segment in enumerate(segments):
            profile=[min(1.,math.hypot((p.x-C.x)/(radii.x+.004),(p.z-C.z)/(radii.z+.004))) for p in segment]
            rim=pipe(f'IN1_PanelRim_{index}_{len(panels)}_{number}_{int(boundary*1000)}',segment,.005,nickel,carrier,profile);rim.location=-pivot
    if active:cylinder(f'IN1_Hinge_{index+1:02d}',.024,.13,(0,0,0),axis,nickel,carrier)
    carrier.rotation_mode='QUATERNION'
    for frame,value in [(1,0.),(31,.20),(121,1.),(181,1.),(271,.20),(301,0.)]:
        clear=min(1.,value/.20);turn=max(0.,(value-.20)/.80)
        carrier.location=pivot+lift*clear;carrier.rotation_quaternion=Quaternion(axis,angle*turn)
        carrier.keyframe_insert('location',frame=frame);carrier.keyframe_insert('rotation_quaternion',frame=frame)
    panels.append({'node':carrier.name,'mesh':o.name,'pivot_blender':list(pivot),'axis_blender':list(axis),'lift_blender':list(lift),'lift_fraction':.20,'angle':angle,'active':active})
# Continuous metal underbody, with a separate shallow center hub at each pole.
core=chamber_skin('IN1_ContinuousAcousticChamber',-math.pi,math.pi,dark,inset=.18,thickness=.028,periodic=True)
membrane_mat=mat('IN1_FoldedDiaphragm',(.026,.024,.021),.32,.34)
cells=[]
for index in range(12):
    a=math.tau*index/12+.014;b=math.tau*(index+1)/12-.014
    # The mouth interrupts cell 4 near the hub: terminate the whole cell before
    # that intersection, instead of leaving the small detached clipped cap.
    start_phi=.42 if index==3 else .20
    membrane=chamber_skin(f'IN1_CellDiaphragm_{index+1:02d}',a,b,membrane_mat,.102,.014,corrugation=True,start_phi=start_phi)
    frame=chamber_skin(f'IN1_CellFrame_{index+1:02d}',a+.005,b-.005,bronze,.052,.022,windows=True,start_phi=start_phi)
    for suffix,lo,hi in [('L',a+.005,a+.040),('R',b-.040,b-.005)]:
        chamber_skin(f'IN1_CellLand_{index+1:02d}_{suffix}',lo,hi,dark,.074,.106,segments=4,start_phi=.44)
    cells.append({'frame':frame.name,'diaphragm':membrane.name,'theta':[a,b]})
for sign in [-1,1]:
    suffix='Front' if sign<0 else 'Rear'
    cylinder('IN1_SpiralHub'+suffix,.17,.065,C+Vector((0,sign*.535,0)),(0,1,0),nickel)
    cylinder('IN1_HubCeramic'+suffix,.143,.049,C+Vector((0,sign*.574,0)),(0,1,0),ivory)
    cylinder('IN1_HubRing'+suffix,.108,.038,C+Vector((0,sign*.602,0)),(0,1,0),nickel)
    cylinder('IN1_HubRecess'+suffix,.083,.017,C+Vector((0,sign*.619,0)),(0,1,0),dark)
    cylinder('IN1_HubInset'+suffix,.062,.014,C+Vector((0,sign*.628,0)),(0,1,0),red)
# Rolled cell-edge conduits are seated on the same curved carrier as the frames.
for index in range(12):
    a=math.tau*index/12;pts=[]
    for j in range(60):
        phi=.23+2.68*j/59;p=point(phi,a,.050);local=placement.inverted()@p
        if math.hypot(local.x,local.y)>.93:pts.append(p)
        elif pts:
            if len(pts)>1:pipe(f'IN1_ChamberRib_{index}_A',pts,.008,nickel)
            pts=[]
    if len(pts)>1:pipe(f'IN1_ChamberRib_{index}_B',pts,.008,nickel)
bpy.data.objects.remove(cutter,do_unlink=True)
core_termination=[]
if CONFIG.get('formed_throat'):
    # The old forward cell tips occupied the volume that now becomes the swept
    # throat. Terminate actual solids behind it, retaining the rear chambers.
    # Caps are physical faces, not hidden meshes in the renderer.
    plane=center+back*.34
    for o in list(root.children_recursive):
        if o.type!='MESH' or not o.name.startswith(('IN1_Cell','IN1_ChamberRib_','IN1_ContinuousAcousticChamber')):continue
        bm=bmesh.new();bm.from_mesh(o.data)
        ds=[(v.co-plane).dot(back) for v in bm.verts]
        if min(ds)>=-1e-8:bm.free();continue
        if max(ds)<=1e-8:
            core_termination.append({'part':o.name,'operation':'removed obsolete forward rib inside new throat'});bm.free();bpy.data.objects.remove(o,do_unlink=True);continue
        bmesh.ops.bisect_plane(bm,geom=list(bm.verts)+list(bm.edges)+list(bm.faces),dist=1e-8,plane_co=plane,plane_no=back,clear_inner=True)
        boundary=[e for e in bm.edges if len(e.link_faces)==1 and all(abs((v.co-plane).dot(back))<2e-6 for v in e.verts)]
        bmesh.ops.holes_fill(bm,edges=boundary,sides=0);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(o.data);bm.free()
        core_termination.append({'part':o.name,'operation':'sectioned with solid end faces','depth':.34,'remaining':'Formed end seats and throat load interface still need construction'})
# Short collar behind the existing A lip, preserving its proven local envelope.
shoulder=[(.735,.105),(.748,.145),(.771,.22),(.746,.22),(.728,.145),(.724,.105)]
verts=[];faces=[];n=160
for radius,depth in shoulder:
    for k in range(n):
        a=math.tau*k/n;verts.append(tuple(center+right*(radius*ratio*math.cos(a))+up*(radius*ratio*math.sin(a))+back*(depth*ratio)))
for j in range(len(shoulder)):
    for k in range(n):faces.append((j*n+k,j*n+(k+1)%n,((j+1)%len(shoulder))*n+(k+1)%n,((j+1)%len(shoulder))*n+k))
mesh('IN1_MouthShoulder',verts,faces,ivory)
# Low broad saddle. No long legs. Seat outline is a shape-study interface.
cylinder('IN1_DeckFoot',.61,.105,(.08,.13,.7275),(0,0,1),nickel)
cylinder('IN1_LowSaddle',.48,.15,(.08,.13,.846),(0,0,1),dark)
# The former two arched study bars are replaced by the four real fitted seats.
scene.frame_set(1);bpy.context.view_layer.update()
# The original common base is imported only for source composition, never edited/exported.
before=set(bpy.data.objects);bpy.ops.import_scene.gltf(filepath=str(ROOT/'app/assets/helios_model.glb'))
imported=set(bpy.data.objects)-before;base=next(o for o in imported if o.name=='BASE_FIXED');keep={base,*base.children_recursive}
base_matrix=base.matrix_world.copy();base.parent=None;base.matrix_world=base_matrix
for o in list(imported-keep):
    if o.name in bpy.data.objects:bpy.data.objects.remove(o,do_unlink=True)
bpy.context.view_layer.update();deck_vertices=[];deck_faces=[]
for o in keep:
    if o.type!='MESH':continue
    o.data.calc_loop_triangles();offset=len(deck_vertices)
    deck_vertices += [o.matrix_world@v.co for v in o.data.vertices]
    deck_faces += [tuple(offset+i for i in t.vertices) for t in o.data.loop_triangles]
tree=BVHTree.FromPolygons(deck_vertices,deck_faces,all_triangles=True);heights=[]
for radius in [0.,.20,.40,.60]:
    for k in range(64):
        x=.08+radius*math.cos(math.tau*k/64);y=.13+radius*math.sin(math.tau*k/64)
        hit=tree.ray_cast(Vector((x,y,2.)),Vector((0,0,-1)),4.)
        if hit[0] is not None:heights.append(hit[0].z)
assert heights;deck_top=max(heights);foot=bpy.data.objects['IN1_DeckFoot'];foot.location.z=deck_top+.0525
saddle_top=deck_top+.235
saddle=bpy.data.objects['IN1_LowSaddle'];saddle.scale.z=.13/.15;saddle.location.z=deck_top+.105+.065
bpy.context.view_layer.update()
# Four load seats use the actual downward-facing fixed-cowl triangles. Their
# curved tops preserve the source planes, instead of interpolating a sampled grid.
import i_fitted_surface as fitted
fixed_cowl_names={r['mesh'] for r in panels if not r['active']}
fixed_skins=[o for o in root.children_recursive if o.type=='MESH' and (o.name.startswith('IN1_FixedRearShell_') or o.name in fixed_cowl_names)]
seat_rows=[]
seat_rubber=mat('IN1_SaddleElastomer',(.018,.016,.013),0.,.52)
for index,(cx,cy) in enumerate([(-.18,.10),(.18,.04),(.17,.34),(-.20,.32)]):
    print('FITTED_SEAT',index,cx,cy,flush=True)
    outline=[(cx+.045*math.cos(math.tau*k/32),cy+.045*math.sin(math.tau*k/32)) for k in range(32)]
    points,polygons,edges=fitted.clipped_surface(fixed_skins,outline,z_limit=1.20)
    vv,ff=fitted.extruded_patch(points,polygons,edges,-.0062,bottom_z=saddle_top-.001)
    assert min(p[2] for p in vv[:len(points)])>saddle_top
    mesh(f'IN1_FittedSaddleSeat_{index+1}',vv,ff,nickel)
    vv,ff=fitted.extruded_patch(points,polygons,edges,-.0002,bottom_offset=-.0062)
    mesh(f'IN1_FittedSaddleGasket_{index+1}',vv,ff,seat_rubber)
    seat_rows.append({'center':[cx,cy],'vertices':len(points),'source_gap_z':.0002,'min_z':min(p.z for p in points),'max_z':max(p.z for p in points)})
for o in root.children_recursive:
    if o.type!='MESH':continue
    bm=bmesh.new();bm.from_mesh(o.data)
    epsilon=1e-8 if o.name.startswith('IN1_FittedSaddle') else 1e-5 if o.name.startswith(('IN1_CellFrame_','IN1_PorcelainPanel_')) else 1e-6
    bmesh.ops.remove_doubles(bm,verts=list(bm.verts),dist=epsilon)
    bmesh.ops.dissolve_degenerate(bm,edges=list(bm.edges),dist=epsilon)
    # A Boolean/bevel sliver can attach a tiny extra triangle to a valid edge.
    # Remove only the measured three-edge flap, retaining the two real faces.
    flaps=[f for f in bm.faces if len(f.edges)==3 and sorted(len(e.link_faces) for e in f.edges)==[1,1,3] and max(e.calc_length() for e in f.edges)<.02 and f.calc_area()<1e-8]
    if flaps:bmesh.ops.delete(bm,geom=flaps,context='FACES')
    bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(o.data);bm.free()
for row in panels:
    cover_mesh=bpy.data.objects[row['mesh']].data
    bm=bmesh.new();bm.from_mesh(cover_mesh);volume=bm.calc_volume(signed=True);bm.free()
    assert len(cover_mesh.vertices)>128 and len(cover_mesh.polygons)>64 and volume>.0001,('Missing required porcelain cover',row['mesh'],volume)
bpy.ops.wm.save_as_mainfile(filepath=str(TARGET),compress=True)
bpy.ops.object.select_all(action='DESELECT')
for o in [root,*root.children_recursive]:o.select_set(True)
bpy.context.view_layer.objects.active=root;component=ROOT/CONFIG.get('component','app/assets/collection/components/I_nautilus_form_r1.glb')
bpy.ops.export_scene.gltf(filepath=str(component),export_format='GLB',use_selection=True,export_animations=False,export_morph=False,export_extras=True)
G=Matrix(((1,0,0,0),(0,0,1,0),(0,-1,0,0),(0,0,0,1)));gd=G@placement@G.inverted();p,q,s=gd.decompose()
all_points=[o.matrix_world@v.co for o in root.children_recursive if o.type=='MESH' for v in o.data.vertices]
report={'source':str(TARGET.relative_to(ROOT)),'source_sha256':sha(TARGET),'component':str(component.relative_to(ROOT)),'component_sha256':sha(component),'base_sha256':sha(ROOT/'app/assets/helios_model.glb'),'mouth_component':spec['component'],'mouth_component_sha256':spec['component_sha256'],'mouth_report':'review/I_refinement/part_a_mouth/shutter_r2/collar_clamps/build.json','mouth_placement':{'p':list(p),'q':[q.x,q.y,q.z,q.w],'s':list(s)},'form_panels':panels,'bounds_blender':{'min':[min(v[i] for v in all_points) for i in range(3)],'max':[max(v[i] for v in all_points) for i in range(3)]},'status':'unlocked_shape_candidate_before_visual_review','scope':'First round nautilus primary-volume and short-opening study. Retains original A and base; no final joints/feet fit/material/animation/AAA acceptance.'}
report['deck_sample']={'count':len(heights),'min':min(heights),'max':deck_top,'foot_bottom':deck_top,'scope':'Coarse planar foot envelope placement from real base; full machined seating remains pending.'}
report['music_optics_layout']='res://assets/collection/art/I/moonlight_candidate/central_scan_r1/layout.json'
report['acoustic_cells']=cells
report['fitted_saddle_seats']=seat_rows
report['shell_mouth_clearance_profile']=cut_profile
if CONFIG:report['shape_config']={'path':config_path,**CONFIG}
if throat_rows:report['formed_throat']=throat_rows
if core_termination:report['core_termination']=core_termination
if CONFIG.get('fixed_mouth_cheek_below_z'):report['fixed_mouth_cheek']={'mesh':'IN1_FixedMouthCheek05','height':CONFIG['fixed_mouth_cheek_below_z'],'joint_gap':.004,'scope':'Fixed lower cheek separated from the moving upper hood; physical support and seam finish remain pending.'}
report['review_scope']='Unlocked round-nautilus volume and four short-hinged porcelain panel form study, actual shared base and original A at declared placement. Music image is static composition only; new joints/trim/interior and full dynamic clearance remain incomplete.'
if CONFIG:
    report['review_scope']='Independent mouth position, orientation and swept-cowl correction against centered_r2 concept. Original A and centered optics travel together; common base unchanged. The lower/fore cowl is fixed; three upper covers remain an unpowered motion study. No native package or art acceptance; new throat end seats, cassette fittings, interior trim and full motion remain under review.'
(OUT/'build.json').write_text(json.dumps(report,indent=2)+'\n');print('I_NAUTILUS_FORM_BUILT',flush=True)
