"""Shared cassette construction; source IO/export is the caller's responsibility."""
import bpy,bmesh,math
from mathutils import Vector,Matrix
from mathutils.bvhtree import BVHTree
import i_machined_geometry as P
import i_fitted_surface as fitted
import i_render_triangle_cleanup as render_triangles

def build_cassette(seed,panel_number,scene):
    prefix='IN2_Cassette%02d'%panel_number
    guide_prefix='IN2_Guide%02d'%panel_number
    col=bpy.data.collections.new('NAUTILUS_SLIDE_HINGE_%02d'%panel_number);scene.collection.children.link(col);P.configure(col)
    root=bpy.data.objects['IN1_BodyRoot'];row=seed['form_panels'][panel_number-1];cover=bpy.data.objects[row['node']];assert row['active'] and 'mechanism' not in row
    pivot=Vector(row['pivot_blender']);H=Vector(row['axis_blender']).normalized();travel=Vector(row['lift_blender']);stroke=travel.length;D=travel.normalized()
    X=(H-D*H.dot(D)).normalized();Y=D.cross(X).normalized();basis=Matrix((X,Y,D)).transposed();matrix=basis.to_4x4();matrix.translation=pivot;inverse=matrix.inverted()
    frame=P.empty(prefix+'_Frame',root);frame.matrix_world=matrix
    carriage=P.empty(prefix+'_Carriage',frame);rotor=P.empty(prefix+'_Rotor',carriage)
    local_h=basis.inverted()@H
    # Keep the mounting ray near the hinge's radial plane; following a fixed world-Y
    # offset would push a narrow rear cover's shoe across its spiral seam.
    def mount_hint(phi):
        C=Vector((.12,.16,1.96));radial=Vector((pivot.x-C.x,0,pivot.z-C.z)).normalized()
        radius=1/math.sqrt((radial.x/1.01)**2+(radial.z/1.10)**2)
        return C+radial*(radius*math.sin(phi))+Vector((0,-.59*math.cos(phi),0))
    old_pin=bpy.data.objects.get('IN1_Hinge_%02d'%panel_number)
    if old_pin:bpy.data.objects.remove(old_pin,do_unlink=True)
    def tidy(o):
        bm=bmesh.new();bm.from_mesh(o.data);bmesh.ops.remove_doubles(bm,verts=list(bm.verts),dist=1e-8);bmesh.ops.dissolve_degenerate(bm,edges=list(bm.edges),dist=1e-9);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(o.data);bm.free()
    def own_mesh(name,vertices,faces,parent,material='A_Nickel'):
        m=bpy.data.meshes.new(name+'Mesh');m.from_pydata(vertices,[],faces);m.update();o=bpy.data.objects.new(name,m);col.objects.link(o);P.finish(o,name,parent,(0,0,0),material);tidy(o)
        for f in m.polygons:f.use_smooth=True
        return o
    def merge(a,b):
        bpy.context.view_layer.update();bpy.context.view_layer.objects.active=a
        mod=a.modifiers.new('Continuous formed metal joint','BOOLEAN');mod.operation='UNION';mod.solver='EXACT';mod.object=b;bpy.ops.object.modifier_apply(modifier=mod.name)
        if b.name in P.parts:P.parts.remove(b.name)
        bpy.data.objects.remove(b,do_unlink=True);tidy(a)
    def shoe(name,source_mesh,guess,parent,width,height):
        m=source_mesh.data;m.calc_loop_triangles();vv=[source_mesh.matrix_world@v.co for v in m.vertices];tt=[tuple(t.vertices) for t in m.loop_triangles]
        tree=BVHTree.FromPolygons(vv,tt,all_triangles=True);center=Vector((.12,.16,1.96));direction=(guess-center).normalized();hit=tree.ray_cast(center+direction*3,-direction,5.);assert hit[0] is not None
        normal=hit[1].normalized();xx=(H-normal*H.dot(normal)).normalized();yy=normal.cross(xx).normalized();f=Matrix((xx,yy,normal)).transposed().to_4x4();f.translation=hit[0]
        outline=[(width*.5*math.cos(math.tau*k/32),height*.5*math.sin(math.tau*k/32)) for k in range(32)]
        points,polygons,edges=fitted.clipped_surface([source_mesh],outline,frame=f,from_positive=True)
        vs,fs=fitted.extruded_patch(points,polygons,edges,.009,bottom_offset=.0002)
        obj=own_mesh(name,[tuple(inverse@f@Vector(v)) for v in vs],fs,parent)
        return obj,inverse@(hit[0]+normal*.009),basis.inverted()@normal,{'surface':source_mesh.name,'center':list(hit[0]),'normal':list(normal),'vertices':len(points),'gap':.0002},(points,polygons,edges,f)
    def formed_arm(name,start,control,end,parent,width=.047,thickness=.020,control2=None):
        points=[];verts=[];faces=[];sections=20;corners=[];rounding=.003
        for cx,cy,a in [(width/2-rounding,thickness/2-rounding,0),(-width/2+rounding,thickness/2-rounding,math.pi/2),(-width/2+rounding,-thickness/2+rounding,math.pi),(width/2-rounding,-thickness/2+rounding,3*math.pi/2)]:
            for k in range(4):
                t=a+k*math.pi/6;corners.append((cx+rounding*math.cos(t),cy+rounding*math.sin(t)))
        count=len(corners)
        for i in range(sections+1):
            t=i/sections
            if control2 is None:
                p=(1-t)**2*start+2*(1-t)*t*control+t*t*end;direction=(2*(1-t)*(control-start)+2*t*(end-control)).normalized()
            else:
                p=(1-t)**3*start+3*(1-t)**2*t*control+3*(1-t)*t*t*control2+t**3*end
                direction=(3*(1-t)**2*(control-start)+6*(1-t)*t*(control2-control)+3*t*t*(end-control2)).normalized()
            xx=(local_h-direction*local_h.dot(direction)).normalized();yy=direction.cross(xx).normalized()
            verts += [tuple(p+xx*x+yy*y) for x,y in corners]
        for i in range(sections):
            for k in range(count):faces.append((i*count+k,i*count+(k+1)%count,(i+1)*count+(k+1)%count,(i+1)*count+k))
        faces += [tuple(range(count-1,-1,-1)),tuple(sections*count+k for k in range(count))]
        return own_mesh(name,verts,faces,parent)

    # Sleeved guides stay fixed; polished rods retract into them with retained overlap.
    guides=[];guide_y=.130 if panel_number==6 else .070;fixed_lo=-stroke-.125;fixed_hi=-.040
    for sign in [-1,1]:
        x=sign*.047;length=fixed_hi-fixed_lo;center=Vector((x,guide_y,(fixed_lo+fixed_hi)/2))
        sleeve=P.sleeve(guide_prefix+'Bronze'+str(sign),.0115,.0085,length,frame,center,'A_Bronze')
        P.sleeve(guide_prefix+'Jacket'+str(sign),.018,.0117,length,frame,center,'A_Nickel')
        rod_lo=-stroke-.105;rod_hi=.012
        rod=P.cylinder(guide_prefix+'Rod'+str(sign),.008,rod_hi-rod_lo,carriage,(x,guide_y,(rod_lo+rod_hi)/2),'A_Nickel',bevel=.00025)
        guides.append({'sleeve':sleeve.name,'rod':rod.name,'fixed_z':[fixed_lo,fixed_hi],'rod_z':[rod_lo,rod_hi]})
    fixed_block=P.box(prefix+'BackBlock',(.150,.071,.042),frame,(0,guide_y,fixed_lo+.018),'A_Nickel',.007)
    head=P.box(prefix+'Crosshead',(.150,.078,.055),carriage,(0,guide_y,.020),'A_Nickel',.007)
    # One solid crosshead/fork, with real through-bores and separate bronze bushings.
    for sign in [-1,1]:
        extension=guide_y-.070
        cheek=P.box(prefix+'ForkUnion'+str(sign),(.024,.095+extension,.058),carriage,local_h*(sign*.052)+Vector((0,.027+extension/2,0)),'A_Nickel',.005)
        cheek.rotation_mode='QUATERNION';cheek.rotation_quaternion=Vector((1,0,0)).rotation_difference(local_h);merge(head,cheek)
    # Machine complete ports through the welded fork, with a rear shoulder and a
    # front retaining screw. The former short blind bore did not clear the fork.
    for sign in [-1,1]:
        x=sign*.047;P.drill(head,.0082,.120,carriage,(x,guide_y,0.))
        P.drill(head,.0145,.060,carriage,(x,guide_y,-.055))
        P.drill(head,.0155,.030,carriage,(x,guide_y,.0585))
        rod=bpy.data.objects[guide_prefix+'Rod'+str(sign)]
        flange=P.cylinder(guide_prefix+'FlangeUnion'+str(sign),.014,.005,carriage,(x,guide_y,-.0277),'A_Nickel',bevel=.0002);merge(rod,flange)
        P.drill(rod,.0027,.021,carriage,(x,guide_y,.0025))
        P.sleeve(guide_prefix+'RetainingWasher'+str(sign),.014,.0029,.002,carriage,(x,guide_y,.0447),'A_Nickel')
        bolt=P.cylinder(guide_prefix+'RetainingBolt'+str(sign),.0025,.0505,carriage,(x,guide_y,.02125),'A_Nickel',bevel=.0001)
        bolt_head=P.screw(guide_prefix+'RetainingHeadUnion'+str(sign),carriage,(x,guide_y,.0479),.010);merge(bolt,bolt_head)
    P.drill(head,.0124,.19,carriage,(0,0,0),local_h)
    for sign in [-1,1]:P.sleeve(prefix+'PinBush'+str(sign),.0122,.0084,.024,carriage,local_h*(sign*.052),'A_Bronze',local_h)
    pin=P.cylinder(prefix+'CaptivePin',.008,.132,carriage,(0,0,0),'A_Nickel',local_h,bevel=.0002)
    for sign in [-1,1]:
        P.sleeve(prefix+'ThrustWasher'+str(sign),.015,.0084,.0016,carriage,local_h*(sign*.065),'A_Bronze',local_h)
        P.screw(prefix+'PinHead'+str(sign),carriage,local_h*(sign*.068),.014,local_h*sign)
    # Weld solid stock first, then drill one bearing bore. Recutting the exact
    # original sleeve radius after welding leaves coincident partial bore faces.
    rotor_body=P.cylinder(prefix+'RotatingTongue',.020,.073,rotor,(0,0,0),'A_Nickel',local_h,bevel=.0004)
    front_shoe,front_point,front_normal,front_record,front_patch=shoe(prefix+'CoverShoe',bpy.data.objects[row['mesh']],mount_hint(1.42),rotor,.110,.080)
    arm=formed_arm(prefix+'TongueUnion',Vector((0,0,0)),Vector((0,0,.080)),front_point-front_normal*.004,rotor,control2=front_point+front_normal*.040)
    merge(rotor_body,arm);merge(rotor_body,front_shoe)
    points,polygons,edges,shoe_frame=front_patch
    vv,ff=fitted.extruded_patch(points,polygons,edges,.00018,bottom_offset=-.06)
    tool=own_mesh('IN2_CoverContactClearanceTool',[tuple(inverse@shoe_frame@Vector(v)) for v in vv],ff,rotor)
    bpy.context.view_layer.update();bpy.context.view_layer.objects.active=rotor_body
    mod=rotor_body.modifiers.new('Source-exact lower shoe surface','BOOLEAN');mod.operation='DIFFERENCE';mod.solver='EXACT';mod.object=tool;bpy.ops.object.modifier_apply(modifier=mod.name)
    P.parts.remove(tool.name);bpy.data.objects.remove(tool,do_unlink=True);tidy(rotor_body)
    # Reopen the bearing after welding the formed arm through its root.
    P.drill(rotor_body,.0086,.16,rotor,(0,0,0),local_h)
    rear_shoe,rear_point,rear_normal,rear_record,_rear_patch=shoe(prefix+'BodyShoe',bpy.data.objects['IN1_FixedRearShell_%02d'%panel_number],mount_hint(1.74),frame,.135,.100)
    back_end=Vector((0,guide_y,fixed_lo+.018))
    spine=formed_arm(prefix+'BackSpineUnion',rear_point-rear_normal*.004,rear_point+rear_normal*.045,back_end,frame,.060,.025,control2=back_end+Vector((0,.040,.025)))
    merge(fixed_block,spine);merge(fixed_block,rear_shoe)
    for sign in [-1,1]:P.drill(fixed_block,.0182,fixed_hi-fixed_lo+.040,frame,(sign*.047,guide_y,(fixed_lo+fixed_hi)/2))

    def anchor_shoe(source_mesh,metal,patch,parent,label,spacing):
        _,_,_,f=patch;normal=f.to_3x3().col[2].normalized();axis=basis.inverted()@normal;records=[]
        for sign in [-1,1]:
            bpy.context.view_layer.update();m=source_mesh.data;m.calc_loop_triangles()
            tree=BVHTree.FromPolygons([source_mesh.matrix_world@v.co for v in m.vertices],[tuple(t.vertices) for t in m.loop_triangles],all_triangles=True)
            origin=f@Vector((sign*spacing,0,.20));outer=tree.ray_cast(origin,-normal,.50);assert outer[0] is not None
            inner=tree.ray_cast(outer[0]-normal*.0002,-normal,.15);assert inner[0] is not None
            depth=(outer[0]-inner[0]).dot(normal);assert .008<depth<.060
            p=inverse@outer[0];q=inverse@inner[0]
            # Actual through-holes in the source porcelain and the welded metal shoe.
            P.drill(source_mesh,.0038,depth+.040,parent,(p+q)*.5,axis,solver='MANIFOLD')
            P.drill(metal,.0025,depth+.060,parent,p,axis)
            # Match the upper edge of the actual porcelain bore liner; the
            # bolt-sized bore alone can leave the formed shoe across its lip.
            P.drill(metal,.0038,depth+.0018,parent,(p+q)*.5,axis)
            # Real flat bearing seats prevent flat washers cutting into curved
            # porcelain or the formed outer shoe. Keep the remaining wall explicit.
            recess=.0015
            P.drill(source_mesh,.0092,.016,parent,q+axis*(recess-.008),axis,solver='MANIFOLD')
            q+=axis*recess;working_depth=depth-recess
            P.drill(metal,.0092,.032,parent,p+axis*.024,axis)
            prefix=label+str(sign)
            P.sleeve(prefix+'BoreLiner',.0036,.0023,working_depth-.0002,parent,(p+q)*.5,'A_Bronze',axis)
            P.sleeve(prefix+'InnerWasher',.008,.0023,.002,parent,q-axis*.0012,'A_Nickel',axis)
            P.sleeve(prefix+'ThreadedInsert',.0055,.0023,.006,parent,q-axis*.0054,'A_Bronze',axis)
            P.sleeve(prefix+'OuterWasher',.008,.0023,.0018,parent,p+axis*.0091,'A_Nickel',axis)
            a=q-axis*.0084;b=p+axis*.0112
            bolt=P.cylinder(prefix+'Bolt',.002,(b-a).length,parent,(a+b)*.5,'A_Nickel',axis,bevel=.0001)
            bolt_head=P.screw(prefix+'HeadUnion',parent,p+axis*.0122,.006,axis);merge(bolt,bolt_head)
            records.append({'source_mesh':source_mesh.name,'outer':list(outer[0]),'inner':list(inner[0]),'original_thickness':depth,'bearing_recess':recess,'remaining_thickness':working_depth,'axis_world':list(normal),'thread_detail':'simplified internal insert and shank; fine thread flanks not yet modeled'})
        return records
    anchors=anchor_shoe(bpy.data.objects[row['mesh']],rotor_body,front_patch,rotor,prefix+'CoverBolt',.038)
    anchors+=anchor_shoe(bpy.data.objects['IN1_FixedRearShell_%02d'%panel_number],fixed_block,_rear_patch,frame,prefix+'BodyBolt',.040)
    for source_skin in [bpy.data.objects[row['mesh']],bpy.data.objects['IN1_FixedRearShell_%02d'%panel_number]]:
        bm=bmesh.new();bm.from_mesh(source_skin.data)
        bmesh.ops.remove_doubles(bm,verts=list(bm.verts),dist=1e-6);bmesh.ops.dissolve_degenerate(bm,edges=list(bm.edges),dist=1e-6)
        bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(source_skin.data);bm.free()

    mechanism={'panel_number':panel_number,'frame':frame.name,'carriage':carriage.name,'rotor':rotor.name,'axis_local_blender':list(local_h),'stroke':stroke,'guide_records':guides,'front_shoe':front_record,'rear_shoe':rear_record,'anchors':anchors,'scope':'One built cassette, guided translation followed by captive-pin rotation, drilled shoes and cover/back-shell anchors. Bearing/fastener interfaces, all-solid collisions, power drive and final artwork still require review.'}
    row['mechanism']=mechanism
    carriage.rotation_mode='QUATERNION';rotor.rotation_mode='QUATERNION'
    engagement=[]
    for number in range(1,302):
        scene.frame_set(number);bpy.context.view_layer.update()
        world=cover.matrix_world.copy();carriage.location=inverse@world.translation
        rotor.rotation_quaternion=(basis.inverted()@world.to_3x3()@basis).to_quaternion()
        carriage.keyframe_insert('location',frame=number);rotor.keyframe_insert('rotation_quaternion',frame=number)
        bpy.context.view_layer.update()
        if number in [1,31,61,121,181,211,271,301]:
            for guide in guides:
                rod=bpy.data.objects[guide['rod']];z=[(inverse@rod.matrix_world@v.co).z for v in rod.data.vertices]
                sleeve=bpy.data.objects[guide['sleeve']];fixed_z=[(inverse@sleeve.matrix_world@v.co).z for v in sleeve.data.vertices]
                overlap=min(max(z),max(fixed_z))-max(min(z),min(fixed_z));assert overlap>.06
                engagement.append({'frame':number,'rod':rod.name,'overlap':overlap,'rod_bounds': [min(z),max(z)],'sleeve_bounds':[min(fixed_z),max(fixed_z)]})
    scene.frame_set(1);bpy.context.view_layer.update()
    nickel=bpy.data.materials.get('IN2_CassetteSatinNickel')
    if nickel is None:nickel=bpy.data.materials['Collection_A_Nickel'].copy();nickel.name='IN2_CassetteSatinNickel'
    finish=nickel.node_tree.nodes.get('Principled BSDF');finish.inputs['Base Color'].default_value=(.48,.47,.43,1);finish.inputs['Metallic'].default_value=.85;finish.inputs['Roughness'].default_value=.28
    for o in list(col.objects):
        if o.type=='MESH':
            tidy(o)
            for index,material in enumerate(o.data.materials):
                if material and material.name=='Collection_A_Nickel':o.data.materials[index]=nickel
    new_solids=[]
    mechanism['render_triangle_repairs']=[]
    for o in [bpy.data.objects[row['mesh']],bpy.data.objects['IN1_FixedRearShell_%02d'%panel_number]]+[o for o in col.objects if o.type=='MESH']:
        repair=render_triangles.repair(o,connected_fins=True)
        if repair['removed_opposed_triangles']:mechanism['render_triangle_repairs'].append({'mesh':o.name,**repair})
    for o in col.objects:
        if o.type!='MESH':continue
        bm=bmesh.new();bm.from_mesh(o.data);defects=sum(not e.is_manifold for e in bm.edges);unseen=set(bm.verts);components=0
        while unseen:
            components+=1;stack=[unseen.pop()]
            while stack:
                vertex=stack.pop()
                for edge in vertex.link_edges:
                    other=edge.other_vert(vertex)
                    if other in unseen:unseen.remove(other);stack.append(other)
        volume=bm.calc_volume(signed=True);bm.free();new_solids.append({'name':o.name,'nonmanifold':defects,'components':components,'volume':volume})
    assert all(r['nonmanifold']==0 and r['components']==1 and r['volume']>0 for r in new_solids),[r for r in new_solids if r['nonmanifold'] or r['components']!=1 or r['volume']<=0]
    return mechanism,new_solids,engagement
