"""Continuous bent thin-wall acoustic core and short rear metal coupling.

Starts from the checked C2 candidate. Does not move A or rebuild the base.
"""
import bpy,bmesh,math,json,hashlib,sys
import numpy as np
from pathlib import Path
from mathutils import Vector,Matrix
from mathutils.bvhtree import BVHTree
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'blender/collection'))
import i_machined_geometry as h
OUT=ROOT/'review/I_refinement/part_c_core/continuous_c3';OUT.mkdir(parents=True,exist_ok=True)
seed=json.loads((ROOT/'review/I_refinement/part_c_core/support_c2/build.json').read_text());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
assert seed['source_sha256']==sha(ROOT/seed['source'])
TARGET=ROOT/'blender/collection/I_continuous_core_c3.blend'
if TARGET.exists():
    previous=json.loads((OUT/'build.json').read_text());assert previous['source_sha256']==sha(TARGET),'Unrecorded C3 source edits'
    (TARGET.parent/'checkpoints'/('I-continuous-core-c3-'+sha(TARGET)[:12]+'.blend')).write_bytes(TARGET.read_bytes())
bpy.ops.wm.open_mainfile(filepath=str(ROOT/seed['source']));scene=bpy.context.scene;scene.frame_set(1);bpy.context.view_layer.update()
col=bpy.data.collections.new('I_C_CORE_C3');scene.collection.children.link(col);h.configure(col);root=h.empty('IC3_Module',None)
mount=h.empty('IC3_CouplingMount',root);mount.matrix_world=bpy.data.objects['IAM_MODULE'].matrix_world.copy();placement=mount.matrix_world.copy()
back=(placement.to_3x3()@Vector((0,0,1))).normalized();first=(placement.to_3x3()@Vector((1,0,0))).normalized()

def capsule(name,parent,length,radius=.016,depth=.022,bore=.0105):
    outline=[];n=32
    for end,start_angle in [(length,-math.pi/2),(0,math.pi/2)]:
        for i in range(n+1):
            angle=start_angle+i*math.pi/n;outline.append((end+radius*math.cos(angle),radius*math.sin(angle)))
    count=len(outline);vs=[(x,y,z) for z in [-depth/2,depth/2] for x,y in outline]
    fs=[tuple(range(count-1,-1,-1)),tuple(range(count,2*count))]+[(i,(i+1)%count,(i+1)%count+count,i+count) for i in range(count)]
    mesh=bpy.data.meshes.new(name+'Mesh');mesh.from_pydata(vs,[],fs);mesh.update();obj=bpy.data.objects.new(name,mesh);col.objects.link(obj);h.finish(obj,name,parent,(0,0,0),'A_Nickel',.0007)
    if bore is not None:h.drill(obj,bore,depth+.02,parent,(0,0,0))
    return obj

def replace_rail(name,points,parent,radius,curved=False):
    old=bpy.data.objects.get(name)
    if old:bpy.data.objects.remove(old,do_unlink=True)
    curve=bpy.data.curves.new(name+'Curve','CURVE');curve.dimensions='3D';curve.bevel_depth=radius;curve.bevel_resolution=4;curve.use_fill_caps=True
    if curved:
        curve.resolution_u=16;spline=curve.splines.new('BEZIER');spline.bezier_points.add(len(points)-1)
        for i,(p,co) in enumerate(zip(spline.bezier_points,points)):
            previous=points[max(0,i-1)];following=points[min(len(points)-1,i+1)];tangent=(following-previous).normalized()
            distances=[(co-q).length for q in [previous,following] if (co-q).length>.000001];handle=min(distances)*.22
            p.co=co;p.handle_left_type='FREE';p.handle_right_type='FREE';p.handle_left=co-tangent*handle;p.handle_right=co+tangent*handle
    else:
        spline=curve.splines.new('POLY');spline.points.add(len(points)-1)
        for p,co in zip(spline.points,points):p.co=(*co,1)
    obj=bpy.data.objects.new(name,curve);col.objects.link(obj);obj.parent=parent;curve.materials.append(bpy.data.materials['Collection_A_Dark'])
    bpy.ops.object.select_all(action='DESELECT');obj.select_set(True);bpy.context.view_layer.objects.active=obj;bpy.ops.object.convert(target='MESH')
    bm=bmesh.new();bm.from_mesh(obj.data);bmesh.ops.remove_doubles(bm,verts=list(bm.verts),dist=.000001);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(obj.data);bm.free();h.parts.append(name)
    return obj

def actual_wall_patch(panel,center,axis,radial,ru=.035,rv=.031):
    m=panel.data;m.calc_loop_triangles();vertices=[panel.matrix_world@v.co for v in m.vertices];points=[];faces=[]
    for tri in m.loop_triangles:
        p=[vertices[i] for i in tri.vertices]
        if (p[1]-p[0]).cross(p[2]-p[0]).normalized().dot(radial)>-.01:continue
        polygon=[np.r_[tuple(v),(v-center).dot(axis)/ru,(v-center).z/rv] for v in p]
        if max(v[3] for v in polygon)<-1 or min(v[3] for v in polygon)>1 or max(v[4] for v in polygon)<-1 or min(v[4] for v in polygon)>1:continue
        if min(abs((v-center).dot(radial)) for v in p)>.12:continue
        for i in range(48):
            angle=i*math.tau/48;cut=[]
            if not polygon:break
            previous=polygon[-1];fp=1-previous[3]*math.cos(angle)-previous[4]*math.sin(angle)
            for current in polygon:
                fc=1-current[3]*math.cos(angle)-current[4]*math.sin(angle)
                if (fc>=0)!=(fp>=0):cut.append(previous+(current-previous)*(fp/(fp-fc)))
                if fc>=0:cut.append(current)
                previous=current;fp=fc
            polygon=cut
        if len(polygon)<3:continue
        base=len(points);points.extend(tuple(p[:3]) for p in polygon)
        faces.extend((base,base+i,base+i+1) for i in range(1,len(polygon)-1))
    mesh=bpy.data.meshes.new('ActualWallPatchTemporary');mesh.from_pydata(points,[],faces);mesh.update();bm=bmesh.new();bm.from_mesh(mesh)
    bmesh.ops.remove_doubles(bm,verts=list(bm.verts),dist=.000001);bmesh.ops.dissolve_degenerate(bm,edges=list(bm.edges),dist=.0000005)
    loose=[v for v in bm.verts if not v.link_faces]
    if loose:bmesh.ops.delete(bm,geom=loose,context='VERTS')
    bm.verts.ensure_lookup_table();bm.verts.index_update()
    points=[v.co.copy() for v in bm.verts];faces=[tuple(v.index for v in f.verts) for f in bm.faces];boundary=[tuple(v.index for v in e.verts) for e in bm.edges if e.is_boundary]
    bm.free();bpy.data.meshes.remove(mesh);assert points and boundary
    return points,faces,boundary

def patch_solid(name,patch,parent,radial,lo,hi,material='A_Dark'):
    points,faces,boundary=patch;n=len(points);vs=[tuple(p+radial*offset) for offset in [lo,hi] for p in points]
    fs=list(faces)+[tuple(i+n for i in reversed(f)) for f in faces]+[(a,b,b+n,a+n) for a,b in boundary]
    mesh=bpy.data.meshes.new(name+'Mesh');mesh.from_pydata(vs,[],fs);mesh.update();obj=bpy.data.objects.new(name,mesh);col.objects.link(obj);h.finish(obj,name,parent,(0,0,0),material)
    bm=bmesh.new();bm.from_mesh(mesh)
    if bm.calc_volume(signed=True)<0:bmesh.ops.reverse_faces(bm,faces=list(bm.faces))
    bm.to_mesh(mesh);bm.free()
    for f in mesh.polygons:f.use_smooth=True
    return obj

# A translation along a four-bar's own rotation axis leaves its carried shell
# transform unchanged. Repackage the obstructing drives, then refit each saddle
# to the actual wall; do not simply translate old curved pads into empty space.
packaging=[]
for index,distance in [(4,.160),(5,-.100)]:
    row=seed['rig'][index-1];axis=Vector(row['axis']);delta=axis*distance;panel=bpy.data.objects[row['mesh']]
    ab_extra=.100 if index==5 else 0.
    row['ab_axis_offset']=ab_extra
    mesh=panel.data;mesh.calc_loop_triangles();tree=BVHTree.FromPolygons([panel.matrix_world@v.co for v in mesh.vertices],[tuple(t.vertices) for t in mesh.loop_triangles],all_triangles=True)
    fixed=bpy.data.objects[row['fixed_carrier']];pivot=bpy.data.objects[row['panel_pivot']]
    for child in fixed.children:child.location+=delta+(axis*ab_extra if ('_%02d_AB'%index) in child.name else Vector())
    for child in pivot.children:
        if ('_%02d_'%index) in child.name and not child.name.startswith('IB3_Saddle_'):child.location+=delta+(axis*ab_extra if ('_%02d_AB'%index) in child.name else Vector())
    bpy.data.objects['IB3_RailBoss_%02d'%index].location+=delta
    for key in ['a','d','b0','c0','surface_b','surface_c']:row[key]=list(Vector(row[key])+delta)
    radial=Vector((math.cos(row['azimuth']),math.sin(row['azimuth']),0))
    for label,key in [('AB','b0'),('DC','c0')]:
        if index==5 and label=='AB':
            # The AB bearing stays at its original, already fitted location on
            # one side of the release seam. Only its virtual plane is offset.
            row['surface_b']=list(Vector(row['surface_b'])+axis*ab_extra)
            fixed_point=Vector(row['a'])+axis*ab_extra
            pre='IB3_Pin_05_AB_Fixed'
            for suffix in ['', '_Thrust_-1','_Thrust_1','_Retainer_-1','_Retainer_1']:
                bpy.data.objects.remove(bpy.data.objects[pre+suffix],do_unlink=True)
            low,high=-.069,.0255
            h.cylinder(pre,.0068,high-low,fixed,fixed_point+axis*((low+high)/2),'A_Nickel',axis,.0003)
            for sign,washer,head in [(-1,-.066,-.069),(1,.0225,.0255)]:
                h.sleeve(pre+'_Thrust_'+str(sign),.013,.00715,.002,fixed,fixed_point+axis*washer,'A_Satin',axis)
                h.screw(pre+'_Retainer_'+str(sign),fixed,fixed_point+axis*head,.010,axis*sign)
            h.sleeve('IC3_AB5DriveSpacer',.013,.00715,.028,fixed,fixed_point-axis*.0355,'A_Satin',axis)
            continue
        saddle=bpy.data.objects['IB3_Saddle_%02d_%s'%(index,label)];count=len(saddle.data.vertices)//2;projected=[]
        for vertex in list(saddle.data.vertices)[:count]:
            query=vertex.co+delta+radial*2.;outer=tree.ray_cast(query,-radial,4.)
            assert outer[0] is not None,('Repacked saddle misses shell',index,label)
            inner=tree.ray_cast(outer[0]-radial*.00005,-radial,.25)
            assert inner[0] is not None and inner[1].dot(radial)<0,('Repacked saddle has no inner wall',index,label)
            projected.append(inner[0])
        for i,point in enumerate(projected):
            saddle.data.vertices[i].co=point-radial*.0006;saddle.data.vertices[count+i].co=point-radial*.0076
        saddle.data.update();bm=bmesh.new();bm.from_mesh(saddle.data);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(saddle.data);bm.free()
        endpoint=Vector(row[key]);direction=(projected[0]-endpoint).normalized();frame=bpy.data.objects['IB3_LugFrame_%02d_%s'%(index,label)]
        frame.location=endpoint;frame.rotation_mode='QUATERNION';frame.rotation_quaternion=Matrix((direction,axis.cross(direction),axis)).transposed().to_quaternion()
        name='IB3_Lug_%02d_%s'%(index,label);bpy.data.objects.remove(bpy.data.objects[name],do_unlink=True)
        lug=capsule(name,frame,max(.004,(projected[0]-endpoint).length-.020))
        row['surface_b' if label=='AB' else 'surface_c']=list(projected[0])
    row['core_packaging_axis_offset']=distance;packaging.append({'index':index,'axis_offset':distance,'ab_axis_offset':ab_extra,'delta':list(delta)})
rail_points=[(Vector(row['a'])+Vector(row['d']))*.5+Vector(row['axis'])*.043 for row in seed['rig'][:5]]
rail_route=rail_points[:4]+[Vector((.57,.30,2.47)),Vector((.37,.38,2.68)),Vector((.06,.38,2.86)),rail_points[4]]
replace_rail('IB3_DorsalRail',rail_route,bpy.data.objects['IB2_Module'],.021,True)
fifth,sixth=seed['rig'][4:6];tip_mid=(Vector(sixth['a'])+Vector(sixth['d']))*.5-Vector(sixth['axis'])*.031
replace_rail('IB3_NestedTipBridge',[Vector(fifth['b0'])+Vector(fifth['axis'])*float(fifth.get('ab_axis_offset',0.)),Vector(fifth['c0']),tip_mid],bpy.data.objects[fifth['panel_pivot']],.016)
bpy.context.view_layer.update()
start=placement@Vector((0,0,.6575))
control=np.array([start,start+back*.42,(.46,.40,2.05),(.40,.70,2.50),(.05,.21,2.77),(-.34,-.05,3.17),(-.56,-.06,3.31)],dtype=float)

def bezier(u,points=control):
    n=len(points)-1
    return sum(math.comb(n,i)*(1-u)**(n-i)*u**i*p for i,p in enumerate(points))
def derivative(u):return bezier(u,(len(control)-1)*np.diff(control,axis=0))
def second_derivative(u):return bezier(u,(len(control)-1)*(len(control)-2)*np.diff(control,n=2,axis=0))
def radius(u):return .020+.426*(1-u)**1.45

parameters=np.linspace(0,1,241);centers=[Vector(bezier(float(u))) for u in parameters];tangents=[Vector(derivative(float(u))).normalized() for u in parameters]
normals=[];binormals=[];normal=first.copy();last=tangents[0]
for tangent in tangents:
    normal=last.rotation_difference(tangent)@normal;normal=(normal-tangent*normal.dot(tangent)).normalized()
    normals.append(normal.copy());binormals.append(tangent.cross(normal).normalized());last=tangent
lengths=np.r_[0.,np.cumsum([(b-a).length for a,b in zip(centers,centers[1:])])];total_length=float(lengths[-1])
curvature=[]
for u in parameters:
    d=derivative(float(u));dd=second_derivative(float(u));k=float(np.linalg.norm(np.cross(d,dd))/np.linalg.norm(d)**3)
    curvature.append({'u':float(u),'curvature':k,'radius':radius(float(u)),'radius_times_curvature':k*radius(float(u))})

def sample(u,angle,offset=0.):
    u=max(0.,min(1.,float(u)));position=u*(len(parameters)-1);i=min(len(parameters)-2,int(position));fraction=position-i
    center=centers[i].lerp(centers[i+1],fraction);normal=normals[i].lerp(normals[i+1],fraction).normalized();binormal=binormals[i].lerp(binormals[i+1],fraction).normalized()
    return center+(normal*math.cos(angle)+binormal*math.sin(angle))*(radius(u)+offset)

def mesh_object(name,vs,fs,material='A_Nickel',uvs=None):
    m=bpy.data.meshes.new(name+'Mesh');m.from_pydata(vs,[],fs);m.update();o=bpy.data.objects.new(name,m);col.objects.link(o);h.finish(o,name,root,(0,0,0),material)
    for f in m.polygons:f.use_smooth=True
    if uvs:
        uv=m.uv_layers.new(name='CoreFabricationUV')
        for f in m.polygons:
            for li in f.loop_indices:uv.data[li].uv=uvs[m.loops[li].vertex_index]
    return o

# Short, actually bored coupling fastens into the C1 metal ring, outside A's
# existing flange diameter. A's original flange is neither moved nor drilled.
coupling=h.sleeve('IC3_CouplingFlange',.605,.480,.018,mount,(0,0,.6485),'A_Satin')
h.sleeve('IC3_CouplingSeal',.605,.565,.0007,mount,(0,0,.63905),'A_Rubber')
fasteners=[]
for i in range(6):
    angle=math.pi/6+i*math.tau/6;p=Vector((.592*math.cos(angle),.592*math.sin(angle),.639))
    for o in [coupling,bpy.data.objects['IC1_CollarUpper' if p.y>=0 else 'IC1_CollarLower'],bpy.data.objects['IC3_CouplingSeal']]:h.drill(o,.0042,.10,mount,p)
    name='IC3_CouplingBolt_%02d'%i;fasteners.append(name)
    h.cylinder(name,.0038,.060,mount,(p.x,p.y,.632),'A_Nickel')
    h.sleeve(name+'_Washer',.0073,.0043,.0018,mount,(p.x,p.y,.659),'A_Bronze')
    h.screw(name+'_Head',mount,(p.x,p.y,.662),.0065)

# Replace the old bare rod into A with a bored, visibly connected load bridge.
# Its flange clevis is integral to C3; the rail end uses the existing fixed boss
# with a real cross bore and spacer. No original shell pivot moves here.
anchor_angle=-math.pi/2+.28
a=placement@Vector((.590*math.cos(anchor_angle),.590*math.sin(anchor_angle),.655))
b=rail_points[1];direction=(b-a).normalized();joint_axis=direction.cross(Vector((0,0,1))).normalized();bridge_offset=.065;a+=joint_axis*bridge_offset;plate_b=b+joint_axis*bridge_offset
bridge_frame=h.empty('IC3_LoadBridgeFrame',root,a);bridge_frame.rotation_mode='QUATERNION';bridge_frame.rotation_quaternion=Matrix((direction,joint_axis.cross(direction),joint_axis)).transposed().to_quaternion()
bridge=capsule('IC3_LoadBridge',bridge_frame,(plate_b-a).length,.024,.014,.0074)
h.drill(bridge,.0074,.040,bridge_frame,((plate_b-a).length,0,0))
for fraction in [.32,.50,.68]:h.drill(bridge,.008,.040,bridge_frame,((plate_b-a).length*fraction,0,0))
bridge.data.materials[0]=bpy.data.materials['Collection_A_Dark']
fixed_frame=h.empty('IC3_CouplerForkFrame',root,a+Vector((0,0,.033)));fixed_frame.rotation_mode='QUATERNION';down=Vector((0,0,-1));fixed_frame.rotation_quaternion=Matrix((down,joint_axis.cross(down),joint_axis)).transposed().to_quaternion()
for sign in [-1,1]:
    ear=capsule('IC3_CouplerForkTool',fixed_frame,.033,.017,.008,None);ear.location.z=sign*.018
    # The terminal bore is centred on a; the existing helper bore at the other
    # end becomes a small relief inside the integral lug.
    h.drill(ear,.0074,.040,fixed_frame,(.033,0,sign*.018))
    bpy.context.view_layer.update();bpy.context.view_layer.objects.active=coupling;mod=coupling.modifiers.new('Integral load clevis','BOOLEAN');mod.operation='UNION';mod.solver='EXACT';mod.object=ear;bpy.ops.object.modifier_apply(modifier=mod.name)
    h.parts.remove(ear.name);bpy.data.objects.remove(ear,do_unlink=True)
h.drill(coupling,.028,.022,root,a,joint_axis)
h.drill(coupling,.0074,.100,root,a,joint_axis)
for sign in [-1,1]:h.drill(coupling,.0123,.080,root,a+joint_axis*(sign*.0622),joint_axis)
h.cylinder('IC3_CouplerLoadPin',.0066,.053,root,a,'A_Nickel',joint_axis)
for sign in [-1,1]:
    h.sleeve('IC3_CouplerLoadWasher_'+str(sign),.011,.0071,.002,root,a+joint_axis*(sign*.0235),'A_Bronze',joint_axis)
    h.screw('IC3_CouplerLoadCap_'+str(sign),root,a+joint_axis*(sign*.0265),.0095,joint_axis*sign)
for name in ['IB3_DorsalRail','IB3_BackPlate_02','IB3_RailBoss_02']:
    h.drill(bpy.data.objects[name],.0074,.055,root,b+joint_axis*.016,joint_axis)
for name in ['IB3_DorsalRail','IB3_RailBoss_02']:
    h.drill(bpy.data.objects[name],.0135,.100,root,b+joint_axis*.067,joint_axis)
spacer_length=bridge_offset-.007-.017
h.sleeve('IC3_RailLoadSpacer',.013,.0071,spacer_length,root,b+joint_axis*(.017+spacer_length/2),'A_Satin',joint_axis)
pin_front=bridge_offset+.0115;pin_back=-.008
h.cylinder('IC3_RailLoadPin',.0066,pin_front-pin_back,root,b+joint_axis*((pin_front+pin_back)/2),'A_Nickel',joint_axis)
h.sleeve('IC3_RailLoadWasher_Front',.012,.0071,.002,root,b+joint_axis*(bridge_offset+.0085),'A_Bronze',joint_axis)
h.screw('IC3_RailLoadCap_Front',root,b+joint_axis*pin_front,.010,joint_axis)
old_root=bpy.data.objects['IB3_RailRootStudy'];bpy.data.objects.remove(old_root,do_unlink=True)
seed['hardware'].remove('IB3_RailRootStudy')
trim=h.box('IC3_FrontMateTrimTool',(3,3,2),mount,(0,0,-.36055),'A_Dark',0)
bpy.context.view_layer.update()
for target_part in [coupling,bridge]:
    bpy.context.view_layer.objects.active=target_part;mod=target_part.modifiers.new('Machine front mating plane','BOOLEAN');mod.operation='DIFFERENCE';mod.solver='EXACT';mod.object=trim;bpy.ops.object.modifier_apply(modifier=mod.name)
h.parts.remove(trim.name);bpy.data.objects.remove(trim,do_unlink=True)
coupling_cleanup=[]
for obj in [coupling,bridge,bpy.data.objects['IC3_CouplingSeal'],bpy.data.objects['IC1_CollarUpper'],bpy.data.objects['IC1_CollarLower'],bpy.data.objects['IB3_DorsalRail']]:
    bm=bmesh.new();bm.from_mesh(obj.data);before=sum(not e.is_manifold for e in bm.edges)
    bmesh.ops.remove_doubles(bm,verts=list(bm.verts),dist=.000003);bmesh.ops.dissolve_degenerate(bm,edges=list(bm.edges),dist=.000001)
    boundary={e for e in bm.edges if e.is_boundary};fills=0
    while boundary:
        seed_edge=boundary.pop();group={seed_edge};stack=[seed_edge]
        while stack:
            e=stack.pop()
            for v in e.verts:
                for other in v.link_edges:
                    if other in boundary:boundary.remove(other);group.add(other);stack.append(other)
        if len(group)==3 and max(e.calc_length() for e in group)<.020:
            bmesh.ops.holes_fill(bm,edges=list(group),sides=3);fills+=1
    bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces))
    coupling_cleanup.append({'name':obj.name,'nonmanifold_before':before,'triangular_boolean_holes_filled':fills,'nonmanifold_after':sum(not e.is_manifold for e in bm.edges)})
    bm.to_mesh(obj.data);bm.free()
bridge_contract={'coupler_pin_center':list(a),'rail_pin_center':list(b),'plate_rail_center':list(plate_b),'axis':list(joint_axis),'bridge_axis_offset':bridge_offset,'rail_spacer_length':spacer_length,'rail_fastener_type':'blind seated bolt with machined spotface','replaces':'IB3_RailRootStudy','requires_finite_interface_checks':True}
mates=[{'positive':'IC3_LoadBridge','negative':'IC3_RailLoadSpacer','point':list(b+joint_axis*(bridge_offset-.007)),'normal':list(joint_axis),'purpose':'flat bridge/spacer seat'},
       {'positive':'IC3_RailLoadSpacer','negative':'IB3_DorsalRail','point':list(b+joint_axis*.017),'normal':list(joint_axis),'purpose':'machined rail spotface'},
       {'positive':'IC3_RailLoadCap_Front','negative':'IC3_RailLoadWasher_Front','point':list(b+joint_axis*(bridge_offset+.0095)),'normal':list(joint_axis),'purpose':'bolt head/washer seat'}]
for sign in [-1,1]:mates.append({'positive':'IC3_CouplerLoadCap_'+str(sign),'negative':'IC3_CouplerLoadWasher_'+str(sign),'point':list(a+joint_axis*(sign*.0245)),'normal':list(joint_axis*sign),'purpose':'retaining head/washer seat'})

n=128;rows=len(parameters);vs=[];uvs=[];fs=[]
for side in [0,1]:
    for row,u in enumerate(parameters):
        wall=min(.010,max(.0025,radius(float(u))*.20))
        for j in range(n):
            vs.append(tuple(sample(float(u),j*math.tau/n,-wall if side else 0.)));uvs.append((j/n,lengths[row]*6.))
    offset=side*rows*n
    for row in range(rows-1):
        for j in range(n):
            face=(offset+row*n+j,offset+row*n+(j+1)%n,offset+(row+1)*n+(j+1)%n,offset+(row+1)*n+j)
            fs.append(face[::-1] if side else face)
for row in [0,rows-1]:
    for j in range(n):
        f=(row*n+j,row*n+(j+1)%n,rows*n+row*n+(j+1)%n,rows*n+row*n+j)
        fs.append(f if row else f[::-1])
body=mesh_object('IC3_ContinuousLiner',vs,fs,'A_Nickel',uvs)
for f in body.data.polygons[-2*n:]:f.use_smooth=False

# One uninterrupted machined helical ribbon lies on the continuous liner.
# Its edges follow the analytic surface, rather than floating independent rings.
count=1201;turns=12.;vs=[];uvs=[];fs=[]
for i,s in enumerate(np.linspace(.025,.975,count)):
    u=float(np.interp(s,lengths/total_length,parameters));angle=math.tau*turns*s+.25
    half_width=min(.014,radius(u)*.14);du=half_width/max(.05,float(np.linalg.norm(derivative(u))))
    for side,raise_by in [(-1,.0012),(1,.0012),(1,.007),(-1,.007)]:
        vs.append(tuple(sample(u+side*du,angle,raise_by)));uvs.append((s*turns,(side+1)/2))
for i in range(count-1):
    for j in range(4):fs.append((i*4+j,i*4+(j+1)%4,(i+1)*4+(j+1)%4,(i+1)*4+j))
fs.extend([(3,2,1,0),tuple((count-1)*4+j for j in range(4))])
rib=mesh_object('IC3_ContinuousHelicalRib',vs,fs,'A_Satin',uvs)
rib.data.materials.append(bpy.data.materials['Collection_A_Bronze'])
for face in rib.data.polygons:
    if face.index<(count-1)*4 and face.index%4==1:face.material_index=1

# Add the substantial visible piston housings shown in the C fabrication study.
# The already fitted neck and port sections keep their measured diameters.
support_finish=[]
for index,row in enumerate(seed['support_layout']):
    top=Vector(row['top']);knee=Vector(row['knee']);direction=(knee-top).normalized();axis=Vector(row['axis']);other=direction.cross(axis).normalized()
    t0=.420;t1=(knee-top).length-.100
    assert t1-t0>.16
    profile=[(.027,t0),(.0385,t0),(.0415,t0+.005),(.0415,t0+.018),(.039,t0+.025),(.039,t1-.025),(.0415,t1-.018),(.0415,t1-.005),(.0385,t1),(.027,t1)]
    vs=[];fs=[];uvs=[];n=64
    for radius,t in profile:
        for j in range(n):
            angle=j*math.tau/n;vs.append(tuple(top+direction*t+(axis*math.cos(angle)+other*math.sin(angle))*radius));uvs.append((j/n,(t-t0)*12.))
    for k in range(len(profile)):
        for j in range(n):fs.append((k*n+j,k*n+(j+1)%n,((k+1)%len(profile))*n+(j+1)%n,((k+1)%len(profile))*n+j))
    housing=mesh_object('IC3_PistonHousing_%02d'%(index+1),vs,fs,'A_Satin',uvs);housing.data.materials.append(bpy.data.materials['Collection_A_Dark'])
    for face in housing.data.polygons:
        if face.index//n==4:face.material_index=1
    support_finish.append({'name':housing.name,'axis_start':list(top),'axis_direction':list(direction),'profile':profile,'existing_port_neck_unchanged':True})
unused=bpy.data.objects.get('IB1_BaseSocketStudy')
if unused:bpy.data.objects.remove(unused,do_unlink=True)

bpy.context.view_layer.update();bpy.ops.wm.save_as_mainfile(filepath=str(TARGET),compress=True)
bpy.ops.object.select_all(action='DESELECT')
for name in ['I_B_PANELS_B2','I_C_MOUNT_C1','I_C_SUPPORT_C2','I_C_CORE_C3']:
    for o in bpy.data.collections[name].objects:o.select_set(True)
bpy.context.view_layer.objects.active=root;component=ROOT/'app/assets/collection/components/I_continuous_core_c3.glb'
bpy.ops.export_scene.gltf(filepath=str(component),export_format='GLB',use_selection=True,export_animations=False,export_extras=True)
report={**seed,'source':str(TARGET.relative_to(ROOT)),'source_sha256':sha(TARGET),'component':str(component.relative_to(ROOT)),'component_sha256':sha(component),'seed_source_sha256':seed['source_sha256'],'core_hardware':list(h.parts),'hardware':list(dict.fromkeys(seed['hardware']+list(h.parts))),'core_control_points':control.tolist(),'core_length':total_length,'core_curvature':curvature,'core_max_radius_times_curvature':max(r['radius_times_curvature'] for r in curvature),'core_meshes':[body.name,rib.name],'coupling_fasteners':fasteners,'core_drive_packaging':packaging,'load_bridge':bridge_contract,'coupling_mating_planes':mates,'coupling_cleanup':coupling_cleanup,'status':'continuous_core_form_candidate_requires_fit','scope':'Actual continuous bent thin-wall liner, one helical ribbon, bored rear coupling and connected load bridge replacing the old rail-root rod. Drives 4/5 offset on their own axes with refitted pads; shell trajectory mathematically unchanged but fresh checks required. A/base preserved. Core, new coupling interfaces, full motion and art require validation.'}
report['support_finish']=support_finish;report['removed_unconnected_study']=['IB1_BaseSocketStudy'];report['review_scope']=report['scope'];(OUT/'build.json').write_text(json.dumps(report,indent=2)+'\n')
print('C3_CONTINUOUS_CORE_BUILT','curvature radius max',report['core_max_radius_times_curvature'],flush=True)
