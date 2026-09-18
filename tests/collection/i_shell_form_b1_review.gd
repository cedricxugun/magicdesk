extends SceneTree
var camera:Camera3D
var world:Node3D
var out:="res://../review/I_refinement/part_b_shell/form_b1/views_r4/"
func _initialize()->void:run.call_deferred()
func capture(name:String)->void:
    for i in range(10):
        await process_frame
        RenderingServer.force_draw(false,1./60.)
    root.get_texture().get_image().save_png(out+name+".png")
func run()->void:
    var report_path:="res://../review/I_refinement/part_b_shell/form_b1/build.json"
    var motion_path:=""
    var relation_only:=false
    var throat_interfaces:=false
    var support_layout:=""
    var cowl_raster:=""
    var diagnostic_no_light_shadows:=false
    for argument in OS.get_cmdline_user_args():
        if argument.begins_with("--report="):
            report_path=argument.trim_prefix("--report=");out=report_path.get_base_dir()+"/views/"
        elif argument.begins_with("--motion="):
            motion_path=argument.trim_prefix("--motion=")
        elif argument=="--mouth-relation-only":relation_only=true
        elif argument=="--throat-interfaces":throat_interfaces=true
        elif argument.begins_with("--support-layout="):support_layout=argument.trim_prefix("--support-layout=")
        elif argument.begins_with("--cowl-raster="):cowl_raster=argument.trim_prefix("--cowl-raster=")
        elif argument=="--lighting-without-shadows":diagnostic_no_light_shadows=true
    if not motion_path.is_empty():out=motion_path.get_base_dir()+"/motion_views/"
    if not support_layout.is_empty():out=support_layout.get_base_dir()+"/layout_views/"
    if not cowl_raster.is_empty():out=report_path.get_base_dir()+"/raster_"+cowl_raster+"/"
    if diagnostic_no_light_shadows:out=out.trim_suffix("/")+"_lights_no_shadow/"
    var spec:Dictionary=JSON.parse_string(FileAccess.get_file_as_string(report_path))
    root.size=Vector2i(1040,1040);root.msaa_3d=Viewport.MSAA_4X;DirAccess.make_dir_recursive_absolute(out)
    RenderingServer.set_render_loop_enabled(false)
    RenderingServer.viewport_set_update_mode(root.get_viewport_rid(),RenderingServer.VIEWPORT_UPDATE_ALWAYS)
    world=Node3D.new();root.add_child(world)
    assert(FileAccess.get_sha256("res://assets/helios_model.glb")==spec.base_sha256)
    var donor:Node3D=load("res://assets/helios_model.glb").instantiate();world.add_child(donor)
    var base:Node3D=donor.find_child("BASE_FIXED",true,false);assert(base!=null);base.reparent(world,true);donor.queue_free()
    var base_points:=PackedVector3Array();var base_min:=Vector3(INF,INF,INF);var base_max:=-base_min
    var base_meshes:Array=base.find_children("*","MeshInstance3D",true,false)
    if base is MeshInstance3D:base_meshes.append(base)
    for mesh in base_meshes:
        for surface in range(mesh.mesh.get_surface_count()):
            for vertex in mesh.mesh.surface_get_arrays(surface)[Mesh.ARRAY_VERTEX]:
                var point:Vector3=mesh.global_transform*vertex;base_points.append(point);base_min=base_min.min(point);base_max=base_max.max(point)
    assert(absf(base_max.x-base_min.x-2.74)<.00001,"Shared base must keep its real diameter")
    var shell_path:String="res://"+str(spec.component).trim_prefix("app/");assert(FileAccess.get_sha256(shell_path)==spec.component_sha256)
    var shell:Node3D=load(shell_path).instantiate();world.add_child(shell)
    if spec.has("finish_profile"):
        var finish_record:Dictionary=load("res://collection/i_finish_r38.gd").apply(shell,str(spec.finish_profile))
        FileAccess.open(out+"finish_profile.json",FileAccess.WRITE).store_string(JSON.stringify(finish_record,"  "))
    var chamber_response:Variant=null
    if spec.has("chamber_response_layout"):
        chamber_response=load("res://collection/i_chamber_music_response.gd").new();chamber_response.bind(shell,spec)
    if not cowl_raster.is_empty():
        var raster_records:Array=load("res://../tests/collection/i_cowl_raster.gd").apply(shell,cowl_raster)
        FileAccess.open(out+"raster_mode.json",FileAccess.WRITE).store_string(JSON.stringify({"source_sha256":spec.source_sha256,"component_sha256":spec.component_sha256,"records":raster_records,"scope":"Same imported arrays and materials; explicit runtime LOD/shadow-proxy diagnostic, not an art acceptance."},"  "))
    if not support_layout.is_empty():
        var layout:Dictionary=JSON.parse_string(FileAccess.get_file_as_string(support_layout));assert(str(layout.source_sha256)==str(spec.source_sha256))
        for i in range(layout.envelopes.size()):
            var row:Dictionary=layout.envelopes[i];var surface:=SurfaceTool.new();surface.begin(Mesh.PRIMITIVE_TRIANGLES)
            for face in row.faces:
                for j in range(1,face.size()-1):
                    for index in [face[0],face[j],face[j+1]]:
                        var p:Array=row.vertices[int(index)];surface.add_vertex(Vector3(p[0],p[2],-p[1]))
            surface.generate_normals();var prototype:=MeshInstance3D.new();prototype.name="SupportLayout_%02d"%i;prototype.mesh=surface.commit();var material:=StandardMaterial3D.new();material.albedo_color=Color(.42,.44,.45);material.metallic=.8;material.roughness=.35;prototype.material_override=material;world.add_child(prototype)
    var shell_driver:Variant=null
    if spec.has("rig"):
        shell_driver=load("res://collection/i_shell_linkage_b3_driver.gd").new();shell_driver.bind(shell,spec)
    elif spec.has("form_panels"):
        shell_driver=load("res://collection/i_nautilus_form_driver.gd").new();shell_driver.bind(shell,spec)
    var mouth_path:String="res://"+str(spec.mouth_component).trim_prefix("app/");assert(FileAccess.get_sha256(mouth_path)==spec.mouth_component_sha256)
    var mouth:Node3D=load(mouth_path).instantiate();world.add_child(mouth)
    var p:Array=spec.mouth_placement.p;var q:Array=spec.mouth_placement.q;var s:Array=spec.mouth_placement.s
    mouth.transform=Transform3D(Basis(Quaternion(q[0],q[1],q[2],q[3])).scaled(Vector3(s[0],s[1],s[2])),Vector3(p[0],p[1],p[2]))
    var mouth_spec:Dictionary=JSON.parse_string(FileAccess.get_file_as_string("res://../"+str(spec.mouth_report)))
    var driver=load("res://collection/i_tongue_set_driver.gd").new();driver.bind(mouth,mouth_spec);driver.set_opening(0.)
    var optics_layout:String=str(spec.get("music_optics_layout",mouth_spec.music_optics_layout))
    var optics=load("res://collection/i_moonlight_staff.gd").new();world.add_child(optics);optics.setup(mouth,str(mouth_spec.component_sha256),optics_layout)
    var env:=Environment.new();env.background_mode=Environment.BG_COLOR;env.background_color=Color(.035,.033,.030)
    var panorama:=PanoramaSkyMaterial.new();panorama.panorama=load("res://assets/studio_small_09_4k.exr");panorama.energy_multiplier=.20
    var sky:=Sky.new();sky.sky_material=panorama;env.sky=sky;env.ambient_light_source=Environment.AMBIENT_SOURCE_SKY;env.ambient_light_energy=.35;env.reflected_light_source=Environment.REFLECTION_SOURCE_SKY;env.tonemap_mode=Environment.TONE_MAPPER_AGX
    env.ssao_enabled=true;env.ssao_radius=.08;env.ssao_intensity=.55;env.glow_enabled=false
    if spec.get("optical_glow",false):load("res://collection/i_optical_finish_r40.gd").apply(env)
    var environment:=WorldEnvironment.new();environment.environment=env;world.add_child(environment)
    for row in [[Vector3(-3,5,4),8.,Color(1.,.91,.80)],[Vector3(4,3,1),4.,Color(.84,.91,1.)],[Vector3(-2,4,-4),5.,Color(1.,.95,.86)]]:
        var light:=AreaLight3D.new();world.add_child(light);light.position=row[0];light.look_at(Vector3(0,1.8,0));light.light_energy=row[1];light.light_color=row[2];light.area_size=Vector2(2.5,3.);light.area_normalize_energy=true;light.area_range=12.;light.shadow_enabled=not diagnostic_no_light_shadows;light.light_size=.25
    RenderingServer.positional_soft_shadow_filter_set_quality(RenderingServer.SHADOW_QUALITY_SOFT_HIGH)
    camera=Camera3D.new();world.add_child(camera);camera.near=.03;camera.far=50.;camera.current=true
    var views:Dictionary={"front":Vector3(0,1.85,8),"side":Vector3(8,1.85,0),"rear":Vector3(0,1.85,-8),"top":Vector3(0,10,0)}
    var records:Array=[]
    camera.projection=Camera3D.PROJECTION_ORTHOGONAL;camera.size=4.0
    for view in views:
        camera.position=views[view];camera.look_at(Vector3(0,1.85,0),Vector3.FORWARD if view=="top" else Vector3.UP)
        var screen_min:=Vector2(INF,INF);var screen_max:=-screen_min
        for point in base_points:
            var screen:=camera.unproject_position(point);screen_min=screen_min.min(screen);screen_max=screen_max.max(screen)
        await capture(view);records.append({"name":view,"camera":str(camera.position),"projection":"orthographic","span":4.0,"base_pixel_bounds":[[screen_min.x,screen_min.y],[screen_max.x,screen_max.y]]})
    camera.projection=Camera3D.PROJECTION_PERSPECTIVE;camera.fov=32.;camera.position=Vector3(.65,3.95,7.65);camera.look_at(Vector3(0,1.92,0))
    if spec.has("form_panels"):
        camera.position=Vector3(.65,3.55,8.25);camera.look_at(Vector3(0,1.66,0))
    await capture("hero_rest");records.append({"name":"hero_rest","camera":str(camera.position),"target":[0,1.66,0] if spec.has("form_panels") else [0,1.92,0],"fov":32.})
    if relation_only:
        # Shared registration view is additional to, never a replacement for,
        # the unchanged orthographic and earlier hero cameras.
        camera.position=Vector3(-3.0,3.55,7.70);camera.look_at(Vector3(0,1.66,0))
        if spec.get("cowl_diagnostic",false):
            driver.set_opening(1.);shell_driver.set_opening(1.)
            if spec.has("diagnostic_target"):
                var target_values:Array=spec.diagnostic_target;var target:=Vector3(target_values[0],target_values[1],target_values[2])
                camera.position=target+(camera.position-target).normalized()*float(spec.get("diagnostic_distance",.95));camera.look_at(target)
            var diagnostic_lights:Array=world.find_children("*","Light3D",true,false)
            for state in [["baseline",true,true],["no_shadows",false,true],["no_ssao",true,false],["neither",false,false]]:
                for light in diagnostic_lights:light.shadow_enabled=state[1]
                env.ssao_enabled=state[2]
                await capture("cowl_"+str(state[0]))
            if spec.get("object_id_diagnostic",false):
                var ids:Dictionary={"IN1_PorcelainPanel_01":Color(.9,.03,.03),"IN1_PorcelainPanel_05":Color(.03,.9,.03),"IN1_FixedMouthCheek05":Color(.03,.03,.9),"IN1_PorcelainPanel_06":Color(.9,.03,.9),"IN1_PorcelainPanel_02":Color(.9,.9,.03)}
                for mesh in world.find_children("*","MeshInstance3D",true,false):
                    var id_material:=StandardMaterial3D.new();id_material.shading_mode=BaseMaterial3D.SHADING_MODE_UNSHADED;id_material.albedo_color=ids.get(str(mesh.name),Color(.15,.15,.15));mesh.material_override=id_material
                env.glow_enabled=false
                await capture("cowl_object_ids")
                var ray_records:Array=[]
                for pixel in [Vector2(465,630),Vector2(475,615),Vector2(490,590),Vector2(520,560),Vector2(540,590)]:
                    var origin:=camera.project_ray_origin(pixel);var direction:=camera.project_ray_normal(pixel);var best:=INF;var record:Dictionary={"pixel":[pixel.x,pixel.y]}
                    for mesh in shell.find_children("*","MeshInstance3D",true,false):
                        if not ids.has(str(mesh.name)):continue
                        var inverse:Transform3D=mesh.global_transform.affine_inverse();var local_origin:Vector3=inverse*origin;var local_direction:Vector3=inverse.basis*direction
                        var faces:PackedVector3Array=mesh.mesh.get_faces()
                        for triangle in range(0,faces.size(),3):
                            var hit:Variant=Geometry3D.ray_intersects_triangle(local_origin,local_direction,faces[triangle],faces[triangle+1],faces[triangle+2])
                            if hit==null:continue
                            var world_hit:Vector3=mesh.global_transform*hit;var distance:=world_hit.distance_to(origin)
                            if distance<best:
                                best=distance;record={"pixel":[pixel.x,pixel.y],"mesh":str(mesh.name),"world_godot":[world_hit.x,world_hit.y,world_hit.z],"mouth_axial_depth_world":(world_hit-mouth.global_position).dot(mouth.global_basis.y.normalized()),"triangle":triangle/3}
                    ray_records.append(record)
                FileAccess.open(out+"actual_pixel_depth.json",FileAccess.WRITE).store_string(JSON.stringify({"source_sha256":spec.source_sha256,"rays":ray_records,"scope":"Actual imported cowl geometry and runtime open transforms at the object-ID view pixels; no source-frame pose inference."},"  "))
            FileAccess.open(out+"diagnostic.json",FileAccess.WRITE).store_string(JSON.stringify({"source_sha256":spec.source_sha256,"component_sha256":spec.component_sha256,"states":["baseline","no_shadows","no_ssao","neither"],"scope":"Same actual source/camera/open pose and finish; independently toggle all local/main light shadows and screen-space ambient occlusion. Diagnostic images only, not adopted lighting."},"  "))
            print("I_COWL_SHADING_DIAGNOSTIC_FINISHED");quit();return
        await capture("relation_rest");records.append({"name":"relation_rest","camera":str(camera.position),"target":[0,1.66,0],"fov":32.})
        if spec.has("metal_supports"):
            var saved_metal_view:=camera.transform
            camera.position=Vector3(-1.7,1.75,2.0);camera.look_at(Vector3(-.38,1.0,-.20));await capture("supports_assembled_close")
            var metal_hidden:Array=[]
            for part in shell.find_children("*","MeshInstance3D",true,false):
                var n:String=str(part.name)
                if part.visible and (n.begins_with("IN1_PorcelainPanel_") or n.begins_with("IN1_FixedRearShell_") or n=="IN1_FixedMouthCheek05"):
                    metal_hidden.append(part);part.hide()
            mouth.hide();camera.fov=35.;camera.position=Vector3(-1.55,1.55,-1.6);camera.look_at(Vector3(-.43,1.02,-.23));await capture("supports_cutaway")
            for i in range(spec.metal_supports.supports.size()):
                var support:Dictionary=spec.metal_supports.supports[i]
                for tag in ["top","foot"]:
                    var joint_values:Array=support[tag];var target:=Vector3(joint_values[0],joint_values[2],-joint_values[1]);camera.position=target+(Vector3(-.32,.12,-.42) if tag=="top" else Vector3(-.40,.22,-.30));camera.look_at(target);await capture("support_%02d_"%i+tag)
            mouth.show()
            for part in metal_hidden:part.show()
            for i in range(spec.metal_supports.supports.size()):
                var support:Dictionary=spec.metal_supports.supports[i];var a:Array=support.top;var b:Array=support.foot;var top:=Vector3(a[0],a[2],-a[1]);var foot:=Vector3(b[0],b[2],-b[1]);var direction:Vector3=(foot-top).normalized();var axis_values:Array=support.pin_axis;var axis:=Vector3(axis_values[0],axis_values[2],-axis_values[1]);var port:Dictionary=spec.metal_supports.ports[i];var target:Vector3=top+direction*float(port.axial_limits[1]);camera.position=target+direction*.30-axis*.12+Vector3(0,.12,0);camera.look_at(target);await capture("support_%02d_port"%i)
            camera.transform=saved_metal_view;camera.fov=32.
        if not support_layout.is_empty():
            var saved_support_view:=camera.transform
            camera.position=Vector3(-1.7,1.75,2.0);camera.look_at(Vector3(-.38,1.0,-.20));await capture("support_layout_close")
            var hidden_support_skins:Array=[]
            for part in shell.find_children("*","MeshInstance3D",true,false):
                var n:String=str(part.name)
                if part.visible and (n.begins_with("IN1_PorcelainPanel_") or n.begins_with("IN1_FixedRearShell_") or n=="IN1_FixedMouthCheek05"):
                    hidden_support_skins.append(part);part.hide()
            mouth.hide();camera.position=Vector3(-1.55,1.55,-1.6);camera.look_at(Vector3(-.43,1.02,-.23));await capture("support_layout_cutaway")
            mouth.show()
            for part in hidden_support_skins:part.show()
            camera.transform=saved_support_view
        var inner_parts:Array=[]
        for part in shell.find_children("*","MeshInstance3D",true,false):
            var part_name:String=str(part.name)
            if part_name.begins_with("IN1_Cell") or part_name.begins_with("IN1_ChamberRib_") or part_name=="IN1_ContinuousAcousticChamber" or part_name.begins_with("IN3_") or part_name.begins_with("IC1_"):
                if part.visible:inner_parts.append(part);part.hide()
        await capture("relation_cowl_isolation")
        for part in inner_parts:part.show()
        driver.set_opening(1.)
        if shell_driver!=null:shell_driver.set_opening(1.)
        await capture("relation_open")
        if spec.has("cap_trim"):
            var trim:=shell.find_child(str(spec.cap_trim.new_mesh),true,false)as MeshInstance3D;assert(trim!=null)
            var saved_trim_view:=camera.transform
            var target:Vector3=trim.global_transform*trim.mesh.get_aabb().get_center()
            var outward:Vector3=trim.global_basis.y.normalized()*float(spec.cap_trim.get("outward_sign",-1.));var along:Vector3=trim.global_basis.x.normalized();var upward:Vector3=trim.global_basis.z.normalized()
            camera.position=target+outward*.60+along*.15;camera.look_at(target,upward)
            await capture("trim_fixed05_assembled_top" if float(spec.cap_trim.get("outward_sign",-1.))>0. else "trim05_assembled_underside")
            var isolated:=MeshInstance3D.new();world.add_child(isolated);isolated.mesh=trim.mesh;isolated.global_transform=trim.global_transform
            for surface in range(trim.mesh.get_surface_count()):isolated.set_surface_override_material(surface,trim.get_active_material(surface))
            shell.hide();mouth.hide();base.hide()
            await capture("trim_fixed05_isolated_top" if float(spec.cap_trim.get("outward_sign",-1.))>0. else "trim05_isolated_underside")
            shell.show();mouth.show();base.show();isolated.queue_free();camera.transform=saved_trim_view
        if spec.has("real_cassettes"):
            var saved_cassette_view:=camera.transform
            var camera_plan:Dictionary={}
            var camera_plan_path:String=report_path.get_base_dir()+"/cassette_review_cameras.json"
            if FileAccess.file_exists(camera_plan_path):
                camera_plan=JSON.parse_string(FileAccess.get_file_as_string(camera_plan_path));assert(str(camera_plan.source_sha256)==str(spec.source_sha256))
            for mechanism in spec.real_cassettes:
                var mount:Node3D=shell.find_child(str(mechanism.frame),true,false)
                var target:Vector3=mount.global_transform*Vector3(0,float(mechanism.stroke)*.25,-.025)
                camera.fov=36.;camera.position=target+mount.global_basis*Vector3(.30,.25,.32);camera.look_at(target,mount.global_basis.x)
                if not camera_plan.is_empty():
                    var selected:Dictionary=camera_plan.cameras.filter(func(c):return c.panel_number==mechanism.panel_number)[0]
                    var eye:Array=selected.eye;var aim:Array=selected.target;var upward:Array=selected.up;camera.position=Vector3(eye[0],eye[1],eye[2]);camera.fov=selected.fov;camera.look_at(Vector3(aim[0],aim[1],aim[2]),Vector3(upward[0],upward[1],upward[2]))
                for pose in [["closed",0.],["lifted",.2],["open",1.]]:
                    shell_driver.set_opening(pose[1]);await capture("cassette_%02d_"%int(mechanism.panel_number)+pose[0])
            shell_driver.set_opening(1.);camera.transform=saved_cassette_view;camera.fov=32.
        for frame in range(90):
            optics.set_score_position(1,32.,1.);optics.set_music_response(.5,true)
            await process_frame
            RenderingServer.force_draw(false,1./60.)
            if optics.status.ready:break
        assert(optics.status.ready);await capture("relation_music")
        if chamber_response!=null:
            chamber_response.update(Vector3(.55,.4,.25),12.,true,1.,1.)
            await capture("relation_music_chambers")
            if spec.get("chamber_light_review",false):
                chamber_response.update(Vector3(.16,.035,0.),12.,true,1.,4.)
                await capture("relation_chambers_quiet_music")
                chamber_response.update(Vector3.ZERO,12.,false,1.,4.)
                await capture("relation_chambers_open_idle")
                var saved_light_view:=camera.transform
                camera.position=Vector3(-1.30,2.85,2.75);camera.look_at(Vector3(.0,2.12,.05))
                chamber_response.update(Vector3(.16,.035,0.),12.,true,1.,4.)
                await capture("chambers_quiet_close")
                camera.position=Vector3(-2.05,2.40,2.50);camera.look_at(Vector3(-.83,1.60,.18))
                await capture("score_readability_close")
                if spec.get("scan_caps_review",false):
                    var tip:Node3D=optics.scan_tips[1].node
                    var axis:Vector3=-tip.global_basis.y.normalized();var lateral:Vector3=tip.global_basis.x.normalized();var upward:Vector3=-tip.global_basis.z.normalized()
                    var focus:Vector3=tip.global_position+axis*.006
                    camera.position=focus+axis*.16+lateral*.08+upward*.035;camera.look_at(focus,upward)
                    optics.set_music_response(0.,false,false);optics.sheet.hide()
                    await capture("scanner_caps_unlit_detail")
                    optics.sheet.show();optics.set_music_response(.5,true);optics.sheet.hide()
                    await capture("scanner_caps_lit_detail")
                    optics.sheet.show()
                camera.transform=saved_light_view
            chamber_response.update(Vector3.ZERO,12.,false,1.,4.)
        if throat_interfaces or spec.has("interface_trim"):
            optics.set_score_position(1,32.,0.);optics.set_music_response(0.,false,false)
            var saved_interface_view:=camera.transform
            var hidden_interface_parts:Array=[]
            for part in shell.find_children("*","MeshInstance3D",true,false):
                var n:String=str(part.name)
                if part.visible and (n.begins_with("IN1_PorcelainPanel_") or n.begins_with("IN1_FixedRearShell_") or n=="IN1_FixedMouthCheek05"):
                    hidden_interface_parts.append(part);part.hide()
            mouth.hide();camera.fov=38.
            var inspection_fill:=AreaLight3D.new();world.add_child(inspection_fill);inspection_fill.area_size=Vector2(.7,.9);inspection_fill.area_range=5.;inspection_fill.area_normalize_energy=true;inspection_fill.light_energy=1.8;inspection_fill.shadow_enabled=true
            for entry in [["coupling_interface_overview",Vector3(-.56,1.58,-.28),Vector3(-1.25,.55,-1.50)],["coupling_termination_upper",Vector3(-.70,1.93,-.37),Vector3(-.58,.30,-.63)],["coupling_termination_lower",Vector3(-.50,1.30,-.24),Vector3(-.65,.12,-.80)]]:
                camera.position=entry[1]+entry[2];camera.look_at(entry[1]);inspection_fill.position=camera.position+Vector3(.35,.35,0);inspection_fill.look_at(entry[1]);await capture(entry[0])
            if spec.has("end_finishes"):
                for i in range(spec.end_finishes.rims.size()):
                    var rim_spec:Dictionary=spec.end_finishes.rims[i]
                    var rim:=shell.find_child(str(rim_spec.mesh),true,false) as MeshInstance3D
                    var rim_center:Vector3=rim.global_transform*rim.get_aabb().get_center()
                    var distance:float=maxf(.45,rim.get_aabb().size.length()*2.2)
                    camera.position=rim_center+Vector3(-.60,.20,-.80).normalized()*distance;camera.look_at(rim_center);inspection_fill.position=camera.position+Vector3(.15,.25,0);inspection_fill.look_at(rim_center)
                    await capture("formed_rim_%02d"%i)
                    if i==0:
                        var rim_hidden:Array=[]
                        for part in shell.find_children("*","MeshInstance3D",true,false):
                            if part.visible and str(part.name)!=str(rim_spec.frame) and not str(part.name).begins_with("IT17_"):
                                rim_hidden.append(part);part.hide()
                        await capture("rim_parent_isolation")
                        for part in rim_hidden:part.show()
            inspection_fill.queue_free();mouth.show()
            for part in hidden_interface_parts:part.show()
            camera.transform=saved_interface_view;camera.fov=32.
        if spec.has("front_sockets"):
            optics.set_score_position(1,32.,0.);optics.set_music_response(0.,false,false)
            var saved_socket_view:=camera.transform
            var socket_hidden:Array=[]
            for part in shell.find_children("*","MeshInstance3D",true,false):
                var n:String=str(part.name)
                if part.visible and (n.begins_with("IN1_PorcelainPanel_") or n.begins_with("IN1_FixedRearShell_") or n=="IN1_FixedMouthCheek05"):
                    socket_hidden.append(part);part.hide()
            mouth.hide()
            var socket_cells:Array=spec.front_sockets.get("newly_seated_cells",[5])
            var socket_spec:Dictionary=spec.front_sockets.seats.filter(func(s):return s.cell==socket_cells[0])[0]
            var socket:Node3D=shell.find_child(str(socket_spec.frame),true,false)
            var socket_target:Vector3=socket.global_position-socket.global_basis.z.normalized()*.04
            camera.fov=40.;camera.position=socket_target-socket.global_basis.x.normalized()*.24+socket.global_basis.y.normalized()*.18+socket.global_basis.z.normalized()*.27;camera.look_at(socket_target,socket.global_basis.y.normalized())
            await capture("front_socket_inspection")
            for socket_cell in socket_cells:
                var cell_spec:Dictionary=spec.front_sockets.seats.filter(func(s):return s.cell==socket_cell)[0]
                var cell_mount:Node3D=shell.find_child(str(cell_spec.frame),true,false)
                var cell_target:Vector3=cell_mount.global_position-cell_mount.global_basis.z.normalized()*.04
                camera.position=cell_target-cell_mount.global_basis.x.normalized()*.24+cell_mount.global_basis.y.normalized()*.18+cell_mount.global_basis.z.normalized()*.27;camera.look_at(cell_target,cell_mount.global_basis.y.normalized())
                await capture("sockets_cell_%02d_front"%int(socket_cell))
            var inner_socket_hidden:Array=[]
            for part in shell.find_children("*","MeshInstance3D",true,false):
                var n:String=str(part.name)
                if part.visible and not (n.begins_with("IF12_C%02d_"%int(socket_spec.cell)) or n in [str(socket_spec.source_frame),str(socket_spec.source_film)]):
                    inner_socket_hidden.append(part);part.hide()
            camera.position=socket_target-socket.global_basis.x.normalized()*.28+socket.global_basis.y.normalized()*.12-socket.global_basis.z.normalized()*.20;camera.look_at(socket_target,socket.global_basis.y.normalized())
            await capture("inner_socket_inspection")
            for part in inner_socket_hidden:part.show()
            mouth.show()
            for part in socket_hidden:part.show()
            camera.transform=saved_socket_view;camera.fov=32.
        if spec.has("hub_backing"):
            optics.set_score_position(1,32.,0.);optics.set_music_response(0.,false,false)
            var saved_hub_view:=camera.transform
            var hub:Node3D=shell.find_child(str(spec.hub_backing.frame),true,false)
            var hub_target:Vector3=hub.global_position+Vector3(0,0,.035)
            camera.fov=38.;camera.position=hub_target+Vector3(.30,.16,.95);camera.look_at(hub_target)
            await capture("hub_assembled_detail")
            var hidden_hub_parts:Array=[]
            for part in shell.find_children("*","MeshInstance3D",true,false):
                var n:String=str(part.name)
                if part.visible and (n.begins_with("IN1_PorcelainPanel_") or n.begins_with("IN1_FixedRearShell_") or n=="IN1_FixedMouthCheek05" or n in ["IN1_SpiralHubFront","IN1_HubCeramicFront","IN1_HubRingFront","IN1_HubRecessFront","IN1_HubInsetFront"]):
                    hidden_hub_parts.append(part);part.hide()
            mouth.hide()
            camera.position=hub_target+Vector3(.40,.18,.70);camera.look_at(hub_target)
            await capture("hub_backing_inspection")
            for part in hidden_hub_parts:part.show()
            mouth.show();camera.transform=saved_hub_view;camera.fov=32.
        if spec.has("chamber_seats"):
            optics.set_score_position(1,32.,0.);optics.set_music_response(0.,false,false)
            var hidden_cowls:Array=[]
            for part in shell.find_children("*","MeshInstance3D",true,false):
                var part_name:String=str(part.name)
                if part.visible and (part_name.begins_with("IN1_PorcelainPanel_") or part_name.begins_with("IN1_FixedRearShell_") or part_name=="IN1_FixedMouthCheek05"):
                    hidden_cowls.append(part);part.hide()
            var saved:=camera.transform
            for i in [0,spec.chamber_seats.size()-1]:
                var seat:Node3D=shell.find_child(str(spec.chamber_seats[i].frame),true,false)
                var target:Vector3=seat.global_position-seat.global_basis.y.normalized()*.035
                var side_sign:float=-1. if str(spec.chamber_seats[i].side)=="L" else 1.
                camera.fov=40.;camera.position=target+seat.global_basis.x.normalized()*(.32*side_sign)+seat.global_basis.y.normalized()*.11-seat.global_basis.z.normalized()*.09;camera.look_at(target,seat.global_basis.y.normalized())
                await capture("chamber_seat_inspection_%02d"%i)
            camera.transform=saved;camera.fov=32.
            for part in hidden_cowls:part.show()
        if spec.has("core_bridge"):
            optics.set_score_position(1,32.,0.);optics.set_music_response(0.,false,false)
            mouth.hide()
            for part in shell.find_children("*","MeshInstance3D",true,false):
                if not str(part.name).begins_with("IN3_") and not str(part.name).begins_with("IC1_"):part.hide()
            var mount:Node3D=shell.find_child(str(spec.core_bridge.mount_node),true,false)
            var target:Vector3=mount.global_transform*Vector3(0,.70,0)
            var front:Vector3=-mount.global_basis.y.normalized()
            var side:Vector3=mount.global_basis.x.normalized()
            camera.position=target+front*2.7+Vector3(0,.45,0);camera.look_at(target)
            await capture("core_bridge_isolation_front")
            camera.position=target+side*2.5+front*.7+Vector3(0,.5,0);camera.look_at(target)
            await capture("core_bridge_isolation_side")
            if spec.has("receiver_shell") or spec.has("receiver_fit") or spec.has("consistent_shells"):
                for part in shell.find_children("*","MeshInstance3D",true,false):part.visible=str(part.name)=="IN1_PorcelainPanel_02"
                camera.fov=42.;camera.position=Vector3(.12,2.20,-1.75);camera.look_at(Vector3(-.62,1.55,-.40))
                var fill:=AreaLight3D.new();world.add_child(fill);fill.position=camera.position+Vector3(.8,.6,0);fill.look_at(Vector3(-.62,1.55,-.40));fill.area_size=Vector2(.7,.9);fill.area_range=5.;fill.area_normalize_energy=true;fill.light_energy=2.;fill.shadow_enabled=true
                await capture("receiver_inner_inspection")
        FileAccess.open(out+"relation_review.json",FileAccess.WRITE).store_string(JSON.stringify({"source_sha256":spec.source_sha256,"component_sha256":spec.component_sha256,"base_sha256":spec.base_sha256,"base_world_bounds":[[base_min.x,base_min.y,base_min.z],[base_max.x,base_max.y,base_max.z]],"views":records,"scope":"Same fixed views for mouth position/orientation/connection comparison. Additional reference-facing camera is approximate registration, not calibrated reconstruction. Static music composition, no native or whole animation acceptance."},"  "))
        print("I_MOUTH_RELATION_REVIEW_FINISHED");world.queue_free();await process_frame;quit();return
    driver.set_opening(1.);await capture("mouth_open_shell_static")
    if shell_driver!=null:
        for progress in [0.25,0.5,0.75,1.0]:
            shell_driver.set_opening(progress);await capture("linkage_open_%03d"%roundi(progress*100.))
        if spec.has("form_panels"):
            for frame in range(90):
                optics.set_score_position(1,32.,1.);optics.set_music_response(.5,true)
                await process_frame
                RenderingServer.force_draw(false,1./60.)
                if optics.status.ready:break
            assert(optics.status.ready)
            await capture("music_layout_candidate")
            optics.set_score_position(1,32.,0.);optics.set_music_response(0.,false,false)
        if spec.has("acoustic_cells"):
            var hidden_covers:Array=[]
            for node in shell.find_children("*","MeshInstance3D",true,false):
                var name:String=str(node.name)
                if name.begins_with("IN1_PorcelainPanel_") or name.begins_with("IN1_FixedRearShell_") or name.begins_with("IN1_PanelRim_"):
                    if node.visible:node.hide();hidden_covers.append(node)
            var saved_camera:=camera.global_transform
            camera.position=Vector3(.65,2.8,5.1);camera.look_at(Vector3(.05,2.0,0))
            await capture("acoustic_core_isolation")
            camera.global_transform=saved_camera
            for node in hidden_covers:node.show()
        if spec.has("real_cassettes"):
            var saved_camera:=camera.global_transform
            for cassette in spec.real_cassettes:
                var frame:Node3D=shell.find_child(str(cassette.frame),true,false)
                var target:Vector3=frame.global_position-frame.global_basis.z*.055-frame.global_basis.y*.08
                camera.position=target-frame.global_basis.z*.60+frame.global_basis.x*.70+frame.global_basis.y*.45
                camera.look_at(target,-frame.global_basis.x)
                for state in [["seated",0.],["lifted",.2],["open",1.]]:
                    shell_driver.set_opening(state[1]);await capture("cassette%02d_"%int(cassette.get("panel_number",4))+state[0])
            camera.global_transform=saved_camera
            shell_driver.set_opening(1.)
        camera.projection=Camera3D.PROJECTION_ORTHOGONAL;camera.size=4.6
        for view in ["side","rear"]:
            camera.position=views[view];camera.look_at(Vector3(0,1.85,0))
            await capture("linkage_open_"+view)
        camera.projection=Camera3D.PROJECTION_PERSPECTIVE;camera.fov=32.
        camera.position=Vector3(2.8,2.65,-3.0);camera.look_at(Vector3(.3,2.15,-.25));await capture("linkage_rear_detail")
        camera.position=Vector3(.9,3.6,-1.9);camera.look_at(Vector3(-.30,3.1,-.05));await capture("linkage_tip_detail")
        shell_driver.set_opening(0.)
        if spec.has("mount_hardware"):
            var hidden:Array=[]
            for mesh in shell.find_children("*","MeshInstance3D",true,false):
                if not str(mesh.name).begins_with("IC1_") and not str(mesh.name).begins_with("IC2_") and mesh.visible:
                    mesh.visible=false;hidden.append(mesh)
            var mount:Node3D=shell.find_child("IC1_MouthMount",true,false);assert(mount!=null)
            var target:Vector3=mount.global_transform*Vector3(0,.60,0)
            var back:Vector3=(mount.global_transform.basis*Vector3.UP).normalized()
            var side:Vector3=(mount.global_transform.basis*Vector3.RIGHT).normalized()
            camera.fov=42.;camera.position=target+back*1.65+side*.62+Vector3(0,.26,0);camera.look_at(target-Vector3(0,.14,0))
            var inspection_light:=AreaLight3D.new();world.add_child(inspection_light);inspection_light.position=camera.position-side*.65+Vector3(0,.7,0);inspection_light.look_at(target)
            inspection_light.area_size=Vector2(.5,1.8);inspection_light.light_energy=5.;inspection_light.area_normalize_energy=true;inspection_light.area_range=6.;inspection_light.shadow_enabled=true
            await capture("mount_isolation_rear")
            inspection_light.queue_free()
            for mesh in hidden:mesh.visible=true
        if spec.has("core_meshes"):
            var skins:Array=[]
            for row in spec.rig:
                var skin:Node3D=shell.find_child(row.mesh,true,false);skin.visible=false;skins.append(skin)
            camera.projection=Camera3D.PROJECTION_PERSPECTIVE;camera.fov=32.;camera.position=Vector3(.65,3.95,7.65);camera.look_at(Vector3(0,1.92,0));await capture("core_isolation_hero")
            camera.position=Vector3(3.2,3.2,-4.8);camera.look_at(Vector3(.1,2.,0));await capture("core_isolation_rear")
            for skin in skins:skin.visible=true
    if not motion_path.is_empty():
        var motion:Dictionary=JSON.parse_string(FileAccess.get_file_as_string(motion_path))
        assert(motion.source_sha256==spec.source_sha256)
        var convert:=Transform3D(Basis(Vector3(1,0,0),Vector3(0,0,-1),Vector3(0,1,0)),Vector3.ZERO)
        var rest_transforms:Dictionary={}
        for row in motion.panels:
            var mesh:Node3D=shell.find_child(row.mesh,true,false);assert(mesh!=null)
            rest_transforms[row.mesh]=mesh.global_transform
        for progress in [0.25,0.5,0.75,1.0]:
            var shell_transforms:Dictionary={}
            for index in range(motion.panels.size()):
                var row:Dictionary=motion.panels[index]
                var local:=clampf(progress*motion.panels.size()-index,0.,1.)
                var sample:int=roundi(local*32.);var m:Array=row.get("local_matrices",row.matrices)[sample]
                var transform:=Transform3D(Basis(Vector3(m[0][0],m[1][0],m[2][0]),Vector3(m[0][1],m[1][1],m[2][1]),Vector3(m[0][2],m[1][2],m[2][2])),Vector3(m[0][3],m[1][3],m[2][3]))
                if row.has("carrier_panel"):transform=shell_transforms[int(row.carrier_panel)]*transform
                shell_transforms[int(row.index)]=transform
                var mesh:Node3D=shell.find_child(row.mesh,true,false)
                mesh.global_transform=convert*transform*convert.inverse()*rest_transforms[row.mesh]
                if int(row.index)==6:
                    for name in ["IB1_ApexStud","IB1_ApexRedMarker"]:
                        var tip:Node3D=shell.find_child(name,true,false)
                        if tip!=null:
                            if not rest_transforms.has(name):rest_transforms[name]=tip.global_transform
                            tip.global_transform=convert*transform*convert.inverse()*rest_transforms[name]
            await capture("candidate_%d_panels_%03d"%[motion.panels.size(),roundi(progress*100.)])
        camera.projection=Camera3D.PROJECTION_ORTHOGONAL;camera.size=4.6
        for view in ["side","rear"]:
            camera.position=views[view];camera.look_at(Vector3(0,1.85,0))
            await capture("candidate_%d_panels_open_%s"%[motion.panels.size(),view])
    FileAccess.open(out+"review.json",FileAccess.WRITE).store_string(JSON.stringify({"source_sha256":spec.source_sha256,"component_sha256":spec.component_sha256,"mouth_component_sha256":spec.mouth_component_sha256,"base_sha256":spec.base_sha256,"base_world_bounds":[[base_min.x,base_min.y,base_min.z],[base_max.x,base_max.y,base_max.z]],"views":records,"scope":str(spec.get("review_scope","Static shell form study on one actual BASE_FIXED instance, unchanged A geometry at declared uniform placement, fixed camera set. Final supports/core/segmentation and active shell motion are not implemented. Mouth-open view is not shell ACTIVE or final App acceptance."))},"  "))
    print("I_SHELL_FORM_REVIEW_FINISHED");world.queue_free();await process_frame;quit()
