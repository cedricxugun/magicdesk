"""Author attached guide bearings and open return channels on the retained mouth.

Artwork: cassette/front_guides/guide_return_detail_r1.png. Dimensions and mounts
come from the evaluated source, not numbers or perspective in the generated art.
"""
import bpy,bmesh,json,hashlib,sys,math
import numpy as np
from pathlib import Path
from mathutils import Vector,Matrix
from mathutils.bvhtree import BVHTree
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(Path(__file__).parent))
import i_machined_geometry as P
from i_tongue_path import TonguePath
from geometry import reparent_preserving_world
OUT=ROOT/'review/I_refinement/part_a_mouth/shutter_r2/front_guides';OUT.mkdir(parents=True,exist_ok=True)
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
seed=json.loads((OUT.parent/'cassettes/build.json').read_text());source=ROOT/seed['source'];assert sha(source)==seed['source_sha256']
bpy.ops.wm.open_mainfile(filepath=str(source));scene=bpy.context.scene;scene.frame_set(1);bpy.context.view_layer.update()
target=ROOT/'blender/collection/I_front_guides.blend'
if target.exists():
    old=json.loads((OUT/'build.json').read_text());assert sha(target)==old['source_sha256'],'Unrecorded guide edits'
    (target.parent/'checkpoints'/('I-front-guides-'+sha(target)[:12]+'.blend')).write_bytes(target.read_bytes())
mouth=bpy.data.objects['IAM_Mouth'];col=bpy.data.collections['MODULE_IAM'];P.configure(col)
liner=bpy.data.objects['IAM_IrisOuterCase_Fitted'];inv=mouth.matrix_world.inverted();deps=bpy.context.evaluated_depsgraph_get()
e=liner.evaluated_get(deps);m=e.to_mesh();m.calc_loop_triangles()
wall=BVHTree.FromPolygons([inv@e.matrix_world@v.co for v in m.vertices],[tuple(t.vertices) for t in m.loop_triangles],all_triangles=True);e.to_mesh_clear()
mounts=[];guide_specs=[];return_specs=[]
modified_parts=[liner.name]

def mesh(name,vertices,faces,parent=mouth,material='A_Nickel',bevel=0):
    data=bpy.data.meshes.new(name+'Mesh');data.from_pydata(vertices,[],faces);data.update()
    o=bpy.data.objects.new(name,data);col.objects.link(o)
    return P.finish(o,name,parent,(0,0,0),material,bevel)

def radius(angle,z):
    direction=Vector((math.cos(angle),math.sin(angle),0));hit=wall.ray_cast(Vector((0,0,z)),direction,2)
    assert hit[0] is not None,(angle,z)
    return hit[0].xy.length

def saddle(name,angle,z,half_width=.019,half_height=.021):
    # A curved, closed patch following the actual liner at every grid vertex.
    n=12;verts=[];faces=[];center_radius=radius(angle,z)
    for offset in [-.005,-.0008]:
        for j in range(n+1):
            zz=z+(j/n*2-1)*half_height
            for k in range(n+1):
                aa=angle+(k/n*2-1)*half_width/center_radius;r=radius(aa,zz)+offset
                verts.append((r*math.cos(aa),r*math.sin(aa),zz))
    stride=(n+1)**2
    for j in range(n):
        for k in range(n):
            a=j*(n+1)+k;q=(a,a+1,a+n+2,a+n+1);faces.extend([q,tuple(x+stride for x in q[::-1])])
    edge=list(range(n+1))+[j*(n+1)+n for j in range(1,n+1)]+[n*(n+1)+k for k in range(n-1,-1,-1)]+[j*(n+1) for j in range(n-1,0,-1)]
    for a,b in zip(edge,edge[1:]+edge[:1]):faces.append((a,b,b+stride,a+stride))
    foot=mesh(name,verts,faces)
    for f in foot.data.polygons:f.use_smooth=True
    # Real radial fasteners bridge the small assembly clearance into bored liner.
    for sign in [-1,1]:
        zz=z+sign*half_height*.62;rr=radius(angle,zz);direction=Vector((math.cos(angle),math.sin(angle),0))
        center=Vector((direction.x*(rr-.001),direction.y*(rr-.001),zz))
        P.drill(liner,.0017,.017,mouth,center,direction)
        P.drill(foot,.0017,.017,mouth,center,direction)
        P.cylinder(name+'FastenerStem'+str(sign),.0015,.013,mouth,center,'A_Bronze',direction,0)
        head=Vector((direction.x*(rr-.007),direction.y*(rr-.007),zz))
        P.screw(name+'FastenerHead'+str(sign),mouth,head,.0038,-direction)
    mounts.append({'name':name,'angle':angle,'z':z,'liner_clearance':.0008,'fastener_radial_clearance':.0002})
    return foot

for group in seed['tongues']:
    i=group['tongue_index'];path=TonguePath(i);prefix='IAM_FrontGuide%d_'%i
    guide=bpy.data.objects['IAM_TongueGuideRoller' if i==0 else 'IAM_Tongue%d_GuideRoller'%i]
    flanges=sorted([o for o in guide.children if 'GuideFlange' in o.name],key=lambda o:o.location.z)
    mandrel=next(o for o in guide.children if 'GuideMandrel' in o.name);half=abs(flanges[-1].location.z)
    # The first guide's old flange crowded the liner saddle. Its retained rim
    # is fitted to the measured envelope before machining the spindle bore.
    if i==0:
        for flange in flanges:
            for vertex in flange.data.vertices:
                vertex.co.x*=.0195/.023;vertex.co.y*=.0195/.023
    rotor=P.empty(prefix+'Rotor',guide)
    for o in [mandrel,*flanges]:
        modified_parts.append(o.name)
        P.drill(o,.0063,2*half+.055,guide,(0,0,0))
        reparent_preserving_world(o,rotor)
    shaft=P.cylinder(prefix+'Shaft',.006,2*half+.046,guide,(0,0,0),'A_Nickel')
    for sign in [-1,1]:
        suffix='L' if sign<0 else 'R';z=sign*(half+.013)
        P.sleeve(prefix+'RollerShoulder'+suffix,.012,.0063,.013,rotor,(0,0,sign*(half-.0065)),'A_Nickel')
        bearing=P.sleeve(prefix+'Bearing'+suffix,.010,.0063,.010,guide,(0,0,z),'A_Bronze')
        P.sleeve(prefix+'CaptiveCollar'+suffix,.008,.0063,.004,guide,(0,0,sign*(half+.0205)),'A_Nickel')
        bpy.context.view_layer.update();point=inv@guide.matrix_world@Vector((0,0,z));direction=Vector(path.outward)
        hit=wall.ray_cast(point,direction,.2);assert hit[0] is not None
        reach=hit[3]-.0025
        cheek=P.box(prefix+'Cheek'+suffix,(reach+.013,.032,.012),guide,((reach-.013)/2,0,z),'A_Nickel',.004)
        P.drill(cheek,.0102,.030,guide,(0,0,z))
        angle=math.atan2(hit[0].y,hit[0].x);foot=saddle(prefix+'LinerSaddle'+suffix,angle,point.z)
        P.cylinder(prefix+'EnamelWitness'+suffix,.0022,.001,guide,(reach-.009,-.0165,z),'A_Red',(0,-1,0),.0002)
        guide_specs.append({'index':i,'guide':guide.name,'rotor':rotor.name,'shaft':shaft.name,'bearing':bearing.name,'cheek':cheek.name,'saddle':foot.name,'radial_clearance':.0003,'bearing_bore':.0063,'reach':reach})
    group['guide_roll']={'rotor':rotor.name,'travel':path.open_travel,'radius':.012,'spin_sign':-float(group['spin_sign'])}

    # Distal leaf enters this open-top U channel along the existing curved path.
    # The terminal section remains fixed and does not snap or hide the leaf.
    width=.020 if i==0 else .018;steps=18;length=.025
    q_values=np.linspace(path.length-length,path.length+.003,steps+1)
    tangent_end=Vector(path.front_derivative(np.array([1.]))[0]).normalized()
    tip=Vector(path.front(np.array([1.]))[0]);side=Vector(path.side);normal=Vector((0,0,1))
    # The mouth faces -Z. Keep the U open to the viewer, with its backing
    # behind both foils (+Z), not an opaque floor hiding the channel in front.
    floor=.0036+.00075+.0015
    bottom=floor+.0034
    profile=[(-width-.0035,bottom),(width+.0035,bottom),(width+.0035,-.008),(width,-.008),(width,floor+.0004),(-width,floor+.0004),(-width,-.008),(-width-.0035,-.008)]
    vertices=[];faces=[]
    for q in q_values:
        center=Vector(path.front(np.array([np.interp(min(q,path.length),path.front_s,path.front_t)]))[0]) if q<=path.length else tip+tangent_end*(q-path.length)
        for w,h in profile:vertices.append(tuple(center+side*w+normal*h))
    count=len(profile)
    for j in range(steps):
        for k in range(count):faces.append((j*count+k,j*count+(k+1)%count,(j+1)*count+(k+1)%count,(j+1)*count+k))
    faces.extend([tuple(range(count-1,-1,-1)),tuple(steps*count+k for k in range(count))])
    channel=mesh(prefix+'ReturnChannel',vertices,faces,material='A_Nickel',bevel=.0007)
    # Dark floor remains below the foil's actual back surface; it is not a mask.
    floor_points=[]
    for q in q_values:
        center=Vector(path.front(np.array([np.interp(min(q,path.length),path.front_s,path.front_t)]))[0]) if q<=path.length else tip+tangent_end*(q-path.length)
        floor_points.append(center)
    vv=[];ff=[]
    for c in floor_points:
        for w,h in [(-width,floor),(width,floor),(width,floor+.0004),(-width,floor+.0004)]:vv.append(tuple(c+side*w+normal*h))
    for j in range(steps):
        for k in range(4):ff.append((j*4+k,j*4+(k+1)%4,(j+1)*4+(k+1)%4,(j+1)*4+k))
    ff.extend([(3,2,1,0),tuple(steps*4+k for k in range(4))]);mesh(prefix+'ReturnLiner',vv,ff,material='A_Dark')
    radial=Vector((tip.x,tip.y,0)).normalized();angle=math.atan2(tip.y,tip.x);z=tip.z+bottom+.0035
    foot=saddle(prefix+'ReturnSaddle',angle,z,.022,.018)
    wall_r=radius(angle,z);start=tip.xy.length+.002;end=wall_r-.003
    bridge=P.box(prefix+'ReturnBridge',(end-start,.026,.007),mouth,((start+end)/2*radial.x,(start+end)/2*radial.y,z),'A_Nickel',.0025)
    bridge.rotation_euler.z=angle
    # A low distal bumper leaves the upper channel open and stands beyond the tip.
    stop=P.box(prefix+'ReturnStop',(.003,2*(width+.0035),.014),mouth,tip+tangent_end*.005+normal*.001,'A_Nickel',.001)
    stop.rotation_euler.z=math.atan2(tangent_end.y,tangent_end.x)
    return_specs.append({'index':i,'channel':channel.name,'saddle':foot.name,'bridge':bridge.name,'tip_rest':list(tip),'length':length,'floor':floor,'nominal_floor_clearance':.0015})

# Weld exact coincident bore seams after Boolean machining; never touch foil
# shape keys or collapse meaningful wall thicknesses to pass a topology check.
for name in list(dict.fromkeys(P.parts+modified_parts)):
    o=bpy.data.objects.get(name)
    if o is None or o.type!='MESH' or o.data.shape_keys:continue
    bm=bmesh.new();bm.from_mesh(o.data)
    bmesh.ops.remove_doubles(bm,verts=list(bm.verts),dist=1e-7)
    bmesh.ops.dissolve_degenerate(bm,edges=list(bm.edges),dist=1e-8)
    loose=[e for e in bm.edges if not e.link_faces]
    if loose:bmesh.ops.delete(bm,geom=loose,context='EDGES')
    bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(o.data);bm.free()

# Match the existing source feed at each authored frame. Runtime uses the same
# normalized feed directly, so reversing halfway cannot leave a guide spinning.
for frame in range(scene.frame_start,scene.frame_end+1):
    scene.frame_set(frame)
    for group in seed['tongues']:
        spec=group['guide_roll'];rotor=bpy.data.objects[spec['rotor']]
        amount=float(bpy.data.objects[group['drive']]['feed'])
        rotor.rotation_euler.z=spec['spin_sign']*spec['travel']*amount/spec['radius'];rotor.keyframe_insert('rotation_euler',frame=frame)
scene.frame_set(1);bpy.context.view_layer.update();bpy.ops.wm.save_as_mainfile(filepath=str(target),compress=True)
bpy.ops.object.select_all(action='DESELECT');root=bpy.data.objects['IAM_MODULE']
for o in [root,*root.children_recursive]:o.select_set(True)
bpy.context.view_layer.objects.active=root;component=ROOT/'app/assets/collection/components/I_front_guides.glb'
bpy.ops.export_scene.gltf(filepath=str(component),export_format='GLB',use_selection=True,export_animations=False,export_morph=False,export_apply=False,export_extras=True)
report={**seed,'source':str(target.relative_to(ROOT)),'source_sha256':sha(target),'component':str(component.relative_to(ROOT)),'component_sha256':sha(component),'seed_source_sha256':seed['source_sha256'],'new_parts':list(dict.fromkeys(seed['new_parts']+P.parts+modified_parts)),'front_parts':P.parts,'guide_interfaces':guide_specs,'return_interfaces':return_specs,'liner_mounts':mounts,'scope':'Attached guide bearings, retained rolling shafts and open return shoes candidate. New geometry and runtime checks pending; not full A or main App acceptance.'}
(OUT/'build.json').write_text(json.dumps(report,indent=2)+'\n');print('I_FRONT_GUIDES_BUILT',len(P.parts),flush=True)
