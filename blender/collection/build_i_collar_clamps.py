"""Fit six captive cam retainers to measured ceramic, retaining all other A work."""
import bpy,bmesh,math,json,hashlib,sys
import numpy as np
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(Path(__file__).parent))
import i_machined_geometry as P
OUT=ROOT/'review/I_refinement/part_a_mouth/shutter_r2/collar_clamps';OUT.mkdir(parents=True,exist_ok=True)
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
seed=json.loads((OUT.parent/'diaphragm/build.json').read_text());source=ROOT/seed['source'];assert sha(source)==seed['source_sha256']
bpy.ops.wm.open_mainfile(filepath=str(source));scene=bpy.context.scene;scene.frame_set(1);bpy.context.view_layer.update()
target=ROOT/'blender/collection/I_collar_clamps.blend'
if target.exists():
    old=json.loads((OUT/'build.json').read_text());assert sha(target)==old['source_sha256'],'Unrecorded collar edits'
    (target.parent/'checkpoints'/('I-collar-'+sha(target)[:12]+'.blend')).write_bytes(target.read_bytes())
mouth=bpy.data.objects['IAM_Mouth'];col=bpy.data.collections['MODULE_IAM'];P.configure(col)
shoe_finish=bpy.data.materials['Collection_A_Satin'].copy();shoe_finish.name='Collection_A_CollarShoe'
shoe_bsdf=next(n for n in shoe_finish.node_tree.nodes if n.type=='BSDF_PRINCIPLED')
grain=shoe_finish.node_tree.nodes.new('ShaderNodeTexImage');grain.image=bpy.data.images.load(str(ROOT/'production/I_refinement/part_a_mouth/material_r2/nickel_normal.png'),check_existing=True);grain.image.colorspace_settings.name='Non-Color';grain.image.pack()
grain_normal=shoe_finish.node_tree.nodes.new('ShaderNodeNormalMap');grain_normal.inputs['Strength'].default_value=.08
shoe_finish.node_tree.links.new(grain.outputs['Color'],grain_normal.inputs['Color']);shoe_finish.node_tree.links.new(grain_normal.outputs['Normal'],shoe_bsdf.inputs['Normal'])
old_names=[o.name for o in bpy.data.objects if any(t in o.name for t in ['CollarLatchSeat','EnamelLatchBar','LatchCaptiveHead','LatchSlottedCap'])]
ceramics=[o for o in bpy.data.objects if o.type=='MESH' and ('PorcelainUpper' in o.name or 'PorcelainLower' in o.name)]
carrier=bpy.data.objects['IAM_EyelidFixedCarrier'];allowed=set(old_names+[o.name for o in ceramics]+[carrier.name])
def fingerprint(o):
    h=hashlib.sha256();v=o.data.shape_keys.key_blocks[0].data if o.data.shape_keys else o.data.vertices
    a=np.zeros(len(v)*3,dtype=np.float32);v.foreach_get('co',a);a[a==0]=0.;h.update(a.tobytes())
    for f in o.data.polygons:h.update(np.asarray(f.vertices,dtype=np.uint32).tobytes())
    if o.data.shape_keys:
        for key in o.data.shape_keys.key_blocks:
            a=np.zeros(len(key.data)*3,dtype=np.float32);key.data.foreach_get('co',a);a[a==0]=0.;h.update(a.tobytes())
    h.update(np.asarray(o.matrix_world,dtype=np.float64).tobytes())
    return h.hexdigest()
retained={o.name:fingerprint(o) for o in bpy.data.objects if o.type=='MESH' and o.name not in allowed}
inv=mouth.matrix_world.inverted();trees={}
for o in ceramics:
    m=o.data;m.calc_loop_triangles();trees[o.name]=BVHTree.FromPolygons([inv@o.matrix_world@v.co for v in m.vertices],[tuple(t.vertices) for t in m.loop_triangles],all_triangles=True)
def shell_at(index,x,y,rear=False):
    a=.2+index*math.tau/6;xx=x*math.cos(a)-y*math.sin(a);yy=x*math.sin(a)+y*math.cos(a)
    origin=Vector((xx,yy,.5 if rear else -.5));direction=Vector((0,0,-1 if rear else 1))
    hits=[(name,tree.ray_cast(origin,direction,1.)) for name,tree in trees.items()]
    hits=[(name,r[0]) for name,r in hits if r[0] is not None];assert len(hits)==1,(index,x,y)
    return hits[0][1].z,hits[0][0]
for name in old_names:bpy.data.objects.remove(bpy.data.objects[name],do_unlink=True)

def tidy(o,smooth=True):
    bm=bmesh.new();bm.from_mesh(o.data);bmesh.ops.remove_doubles(bm,verts=list(bm.verts),dist=1e-8)
    bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.normal_update()
    if smooth:
        for face in bm.faces:face.smooth=True
        for edge in bm.edges:edge.smooth=edge.is_manifold and edge.calc_face_angle()<.45
    bm.to_mesh(o.data);bm.free()
    if smooth:
        w=o.modifiers.new('Machined face normals','WEIGHTED_NORMAL');w.keep_sharp=True;w.weight=80
        bpy.context.view_layer.objects.active=o;bpy.ops.object.modifier_apply(modifier=w.name)
def boolean(o,tool,operation='DIFFERENCE',remove=True):
    bpy.context.view_layer.update();bpy.context.view_layer.objects.active=o
    m=o.modifiers.new('Actual fitted machining','BOOLEAN');m.solver='EXACT';m.operation=operation;m.object=tool
    bpy.ops.object.modifier_apply(modifier=m.name)
    if remove:
        if tool.name in P.parts:P.parts.remove(tool.name)
        bpy.data.objects.remove(tool,do_unlink=True)

STUD_R=.838

def clipped_surface(index,width,height):
    # Cut the actual post-drilling ceramic triangles, retaining their planes.
    # A sampled XY grid can intersect the ceramic between its sample vertices.
    root=roots[index];_,name=shell_at(index,STUD_R,0);o=bpy.data.objects[name]
    transform=root.matrix_world.inverted()@o.matrix_world;m=o.data;m.calc_loop_triangles()
    hx=width/2;hy=height/2;corner=.005;cx=.837;outline=[]
    for xc,yc,start in [(hx-corner,-hy+corner,-math.pi/2),(hx-corner,hy-corner,0),(-hx+corner,hy-corner,math.pi/2),(-hx+corner,-hy+corner,math.pi)]:
        for angle in np.linspace(start,start+math.pi/2,9):outline.append((cx+xc+corner*math.cos(angle),yc+corner*math.sin(angle)))
    def clip(poly,a,b):
        result=[];prev=poly[-1];fp=(b[0]-a[0])*(prev.y-a[1])-(b[1]-a[1])*(prev.x-a[0])
        for cur in poly:
            fc=(b[0]-a[0])*(cur.y-a[1])-(b[1]-a[1])*(cur.x-a[0]);inside=fc>=-1e-10
            if inside!=(fp>=-1e-10):result.append(prev.lerp(cur,fp/(fp-fc)))
            if inside:result.append(cur)
            prev=cur;fp=fc
        return result
    verts=[];faces=[]
    for tri in m.loop_triangles:
        poly=[transform@m.vertices[i].co for i in tri.vertices]
        if max(v.x for v in poly)<cx-hx or min(v.x for v in poly)>cx+hx or max(v.y for v in poly)<-hy or min(v.y for v in poly)>hy:continue
        n=(poly[1]-poly[0]).cross(poly[2]-poly[0]).normalized()
        if n.z>-.15:continue
        center=sum(poly,Vector())/3
        original_z,_=shell_at(index,center.x,center.y)
        if center.z>original_z+.002:continue  # Blind-hole floors are not the outer skin.
        for j,a in enumerate(outline):
            poly=clip(poly,a,outline[(j+1)%len(outline)])
            if len(poly)<3:break
        if len(poly)<3:continue
        base=len(verts);verts.extend(tuple(v) for v in poly)
        for j in range(1,len(poly)-1):faces.append((base,base+j,base+j+1))
    mesh=bpy.data.meshes.new('ClippedCeramicSurface');mesh.from_pydata(verts,[],faces);mesh.update()
    bm=bmesh.new();bm.from_mesh(mesh);bmesh.ops.remove_doubles(bm,verts=list(bm.verts),dist=1e-7);bmesh.ops.dissolve_degenerate(bm,edges=list(bm.edges),dist=1e-9)
    bm.verts.ensure_lookup_table();bm.verts.index_update()
    base_vertices=[tuple(v.co) for v in bm.verts];base_faces=[tuple(v.index for v in f.verts) for f in bm.faces]
    boundary=[tuple(v.index for v in e.verts) for e in bm.edges if e.is_boundary]
    bm.free();bpy.data.meshes.remove(mesh)
    assert base_faces and boundary
    return base_vertices,base_faces,boundary

def foot(index,name,parent,thickness,back_offset,width,height,material):
    base,polys,edges=clipped_surface(index,width,height);count=len(base)
    verts=[(x,y,z-back_offset) for x,y,z in base]+[(x,y,z-back_offset-thickness) for x,y,z in base]
    faces=[tuple(reversed(p)) for p in polys]+[tuple(v+count for v in p) for p in polys]+[(a,b,b+count,a+count) for a,b in edges]
    mesh=bpy.data.meshes.new(name+'Mesh');mesh.from_pydata(verts,[],faces);mesh.update();o=bpy.data.objects.new(name,mesh);col.objects.link(o)
    P.finish(o,name,parent,(0,0,0),material)
    uv=mesh.uv_layers.new(name='FittedPressureShoeUV')
    for poly in mesh.polygons:
        for li in poly.loop_indices:
            v=mesh.vertices[mesh.loops[li].vertex_index].co;uv.data[li].uv=((v.x-.837)/width+.5,v.y/height+.5)
    P.drill(o,.0044,.5,parent,(STUD_R,0,0));tidy(o)
    return o

roots=[]
for index in range(6):
    root=P.empty('IAM_Collar%d_Root'%index,mouth);root.rotation_euler.z=.2+index*math.tau/6;roots.append(root)
    front,name=shell_at(index,STUD_R,0);pin_front,_=shell_at(index,.861,0)
    P.drill(bpy.data.objects[name],.00425,.45,root,(STUD_R,0,.03))
    P.drill(bpy.data.objects[name],.0018,.018,root,(.861,0,pin_front+.005))
    ear=P.box('CarrierEarUnion%d'%index,(.040,.024,.016),root,(STUD_R,0,.222),'A_Dark',bevel=.0012)
    boolean(carrier,ear,'UNION');P.drill(carrier,.00425,.04,root,(STUD_R,0,.222))
bpy.context.view_layer.update()

records=[]
for index in range(6):
    pre='IAM_Collar%d_'%index;a=.2+index*math.tau/6;root=roots[index]
    radius=STUD_R;front,ceramic_name=shell_at(index,radius,0);rear,_=shell_at(index,radius,0,True)
    pin_front,_=shell_at(index,.861,0)
    liner=P.sleeve(pre+'PorcelainBoreLiner',.004,.003,rear-front-.0002,root,(radius,0,(rear+front)/2),'A_Bronze')
    gasket=foot(index,pre+'SeatedGasket',root,.0012,.00005,.077,.055,'A_Rubber')
    shoe=foot(index,pre+'FittedPressureShoe',root,.003,.00125,.076,.054,'A_CollarShoe')
    # Two flat bearing lands distribute cam load onto the curved pressure shoe.
    land_z=min(shell_at(index,radius+x,y)[0]-.00425 for x in [-.016,-.006,.006,.016] for y in [-.015,0,.015])-.0005
    for sign in [-1,1]:
        pad=P.box(pre+'PressureLand'+str(sign),(.010,.030,1.),root,(radius+sign*.011,0,0),'A_Nickel',bevel=0)
        for vertex in pad.data.vertices:
            x=pad.location.x+vertex.co.x;y=vertex.co.y;surface,_=shell_at(index,x,y)
            vertex.co.z=land_z if vertex.co.z<0 else surface-.00425+.0003
        pad.data.update();pad.update_tag();bpy.context.view_layer.update()
        bevel=pad.modifiers.new('Bearing land edge','BEVEL');bevel.width=.00025;bevel.segments=2;bpy.context.view_layer.objects.active=pad;bpy.ops.object.modifier_apply(modifier=bevel.name)
        boolean(shoe,pad,'UNION')
    tidy(shoe)
    axis_z=land_z-.016-.00008
    pivot=P.empty(pre+'CamPivot',root,(radius,0,axis_z));pivot.rotation_euler.z=math.pi/2;pivot['service_release']=0.
    d=pivot.driver_add('rotation_euler',1).driver;d.type='SCRIPTED';v=d.variables.new();v.name='release';v.type='SINGLE_PROP';v.targets[0].id=pivot;v.targets[0].data_path='["service_release"]';d.expression='release*'+str(math.radians(65))
    lobes=[]
    for sign in [-1,1]:
        lobe=P.cylinder(pre+('CamLeft' if sign<0 else 'CamRight'),.012,.010,pivot,(0,sign*.011,.004),'A_Nickel',axis=(0,1,0),bevel=.0004)
        P.drill(lobe,.0029,.014,pivot,(0,sign*.011,0),axis=(0,1,0));lobes.append(lobe)
    spine=P.box(pre+'LeverSpine',(.048,.028,.008),pivot,(.030,0,-.001),'A_Nickel',bevel=.003)
    def shape_grip(o):
        for vertex in o.data.vertices:
            u=vertex.co.x+o.location.x;t=max(0,min(1,(u-.006)/.048))
            vertex.co.y*=.65+.35*t
            vertex.co.z+=.003*t*t
        o.data.update();o.update_tag();bpy.context.view_layer.update()
    shape_grip(spine)
    boolean(lobes[0],spine,'UNION');boolean(lobes[0],lobes[1],'UNION');cam=lobes[0];cam.name=pre+'CamAndSpine';tidy(cam)
    grip=P.box(pre+'RedEnamelGrip',(.039,.020,.005),pivot,(.0345,0,-.007),'A_Red',bevel=.002)
    shape_grip(grip)
    pocket=grip.copy();pocket.data=grip.data.copy();col.objects.link(pocket);pocket.name=pre+'GripPocketTool'
    for vertex in pocket.data.vertices:vertex.co.x*=1.01;vertex.co.y*=1.01
    pocket.data.update();pocket.update_tag()
    boolean(cam,pocket);tidy(cam);tidy(grip)
    eye=P.sleeve(pre+'DrawStudEye',.0055,.0029,.0072,root,(radius,0,axis_z),'A_Nickel',axis=(1,0,0))
    shaft_start=axis_z+.0045;shaft_end=.245
    shaft=P.cylinder(pre+'DrawStudShaft',.0026,shaft_end-shaft_start,root,(radius,0,(shaft_end+shaft_start)/2),'A_Nickel',bevel=.0001)
    boolean(eye,shaft,'UNION');eye.name=pre+'ContinuousDrawStud';tidy(eye)
    hinge=P.cylinder(pre+'TransverseHingePin',.0026,.0382,root,(radius,0,axis_z),'A_Bronze',axis=(1,0,0),bevel=.00015)
    for sign in [-1,1]:
        P.sleeve(pre+'HingeThrust'+str(sign),.0048,.0029,.0015,root,(radius+sign*.01685,0,axis_z),'A_Bronze',axis=(1,0,0))
        P.sleeve(pre+'HingeCap'+str(sign),.0044,.00265,.0015,root,(radius+sign*.01835,0,axis_z),'A_Nickel',axis=(1,0,0))
    P.sleeve(pre+'CarrierInsert',.004,.0029,.018,root,(radius,0,.222),'A_Bronze')
    P.sleeve(pre+'RearLoadWasher',.009,.00425,.0025,root,(radius,0,.2313),'A_Nickel')
    bpy.ops.mesh.primitive_cylinder_add(vertices=6,radius=.0075,depth=.006)
    nut=P.finish(bpy.context.object,pre+'RearHexNut',root,(radius,0,.23555),'A_Bronze',bevel=.0006)
    P.drill(nut,.0029,.010,root,(radius,0,.23555));tidy(nut,False)
    locator=P.cylinder(pre+'ShoeLocator',.0015,.0147,root,(.861,0,pin_front+.003),'A_Nickel',bevel=.0001)
    locator_head=P.cylinder(pre+'LocatorHead',.0031,.0015,root,(.861,0,pin_front-.005),'A_Nickel',bevel=.0002)
    boolean(locator,locator_head,'UNION');tidy(locator)
    records.append({'index':index,'root':root.name,'angle':a,'pivot':pivot.name,'service_release_degrees':65,'stud_radius':radius,'ceramic_front_z':front,'ceramic_rear_z':rear,'hinge_axis_z':axis_z,'hinge_axis_local':[1,0,0],'lever_plane_rotation':math.pi/2,'bearing_land_z':land_z,'cam':cam.name,'grip':grip.name,'shoe':shoe.name,'gasket':gasket.name,'stud':eye.name,'hinge_pin':hinge.name,'liner':liner.name,'ceramic':ceramic_name})
    print('COLLAR_BUILT',index,'axis',axis_z,flush=True)

tidy(carrier)
bpy.context.view_layer.update();scene.frame_set(1)
drift=[name for name,h in retained.items() if fingerprint(bpy.data.objects[name])!=h];assert not drift,('Non-collar geometry drift',drift)
bpy.ops.wm.save_as_mainfile(filepath=str(target),compress=True)
for group in seed['tongues']:
    for name in group['mesh_names']:bpy.data.objects[name].shape_key_clear()
bpy.ops.object.select_all(action='DESELECT');root=bpy.data.objects['IAM_MODULE']
for o in [root,*root.children_recursive]:o.select_set(True)
bpy.context.view_layer.objects.active=root;component=ROOT/'app/assets/collection/components/I_collar_clamps.glb'
bpy.ops.export_scene.gltf(filepath=str(component),export_format='GLB',use_selection=True,export_animations=False,export_morph=True,export_morph_normal=True,export_apply=False,export_extras=True)
report={**seed,'source':str(target.relative_to(ROOT)),'source_sha256':sha(target),'component':str(component.relative_to(ROOT)),'component_sha256':sha(component),'seed_source_sha256':seed['source_sha256'],'collar_clamps':records,'removed_old_clamp_objects':old_names,'modified_fixed_meshes':[o.name for o in ceramics]+[carrier.name],'retained_geometry_fingerprints':retained,'scope':'Independent six-collar cam-retainer candidate, fitted to actual ceramic with draw studs and bored rear-carrier mounting. Geometry/clearance/material/release review pending; service-release controls not integrated. All other geometry and tongue morphs retained.'}
(OUT/'build.json').write_text(json.dumps(report,indent=2)+'\n');print('I_COLLAR_CLAMPS_BUILT',flush=True)
