extends SceneTree
var world:Node3D
var camera:Camera3D
var out:="res://../review/I_refinement/part_a_mouth/shutter_r2/collar_clamps/motion_r4/"
var report_path:="res://../review/I_refinement/part_a_mouth/shutter_r2/collar_clamps/build.json"
func _initialize()->void:run.call_deferred()
var timings:Dictionary={}
func capture(name:String)->void:
    var gpu:Array=[]
    for i in range(10):
        await RenderingServer.frame_post_draw
        if i>=5:gpu.append(RenderingServer.viewport_get_measured_render_time_gpu(root.get_viewport_rid()))
    timings[name]={"gpu_ms":gpu}
    root.get_texture().get_image().save_png(out+name+".png")
func run()->void:
    for argument in OS.get_cmdline_user_args():
        if argument.begins_with("--report="):
            report_path=argument.trim_prefix("--report=")
            out=report_path.get_base_dir()+"/studio/"
    root.size=Vector2i(1040,940);root.msaa_3d=Viewport.MSAA_4X;DirAccess.make_dir_recursive_absolute(out)
    world=Node3D.new();root.add_child(world)
    var env:=Environment.new();env.background_mode=Environment.BG_COLOR;env.background_color=Color(.030,.029,.026)
    var panorama:=PanoramaSkyMaterial.new();panorama.panorama=load("res://assets/studio_small_09_4k.exr");panorama.energy_multiplier=.20
    var sky:=Sky.new();sky.sky_material=panorama;env.sky=sky;env.ambient_light_source=Environment.AMBIENT_SOURCE_SKY;env.ambient_light_energy=.30;env.reflected_light_source=Environment.REFLECTION_SOURCE_SKY;env.tonemap_mode=Environment.TONE_MAPPER_AGX
    env.ssao_enabled=true;env.ssao_radius=.04;env.ssao_intensity=.6;env.glow_enabled=false
    var environment:=WorldEnvironment.new();environment.environment=env;world.add_child(environment)
    camera=Camera3D.new();world.add_child(camera);camera.fov=32.;camera.near=.02;camera.position=Vector3(1.3,-3.2,-.80);camera.look_at(Vector3(0,.13,0),Vector3.FORWARD)
    var lights:Array[AreaLight3D]=[]
    for row in [[Vector3(-2,-2,-2.5),5.,Vector2(1.5,2.3)],[Vector3(2,-.3,-.7),3.,Vector2(1.,2.)],[Vector3(-.5,2,-2),4.,Vector2(1.5,2.)]]:
        var light:=AreaLight3D.new();world.add_child(light);light.position=row[0];light.look_at(Vector3.ZERO,Vector3.FORWARD);light.light_energy=row[1];light.area_size=row[2];light.area_normalize_energy=true;light.area_range=10.;light.light_size=.25;light.shadow_enabled=true;light.shadow_normal_bias=.012;lights.append(light)
    var spec:Dictionary=JSON.parse_string(FileAccess.get_file_as_string(report_path))
    var component:String="res://"+str(spec.component).trim_prefix("app/");var asset:Node3D=load(component).instantiate();world.add_child(asset)
    assert(FileAccess.get_sha256(component)==spec.component_sha256)
    var driver=load("res://collection/i_tongue_set_driver.gd").new();driver.bind(asset,spec)



    var receipt:Dictionary=load("res://review/i_mouth_studio.gd").apply(root,env,lights)
    driver.set_opening(0.)
    var row:Dictionary=spec.collar_clamps[2];var pivot:Node3D=asset.find_child(row.pivot,true,false);var parent:Node3D=asset.find_child(row.root,true,false)
    var radial:Vector3=parent.global_basis*Vector3.RIGHT;var tangent:Vector3=parent.global_basis*Vector3.FORWARD
    var aim:Vector3=pivot.global_position+radial*.002+tangent*.014
    camera.position=aim+radial*.045+Vector3(0,-.175,0)+tangent*.065;camera.look_at(aim,radial)
    var home:Basis=pivot.basis;var samples:Array=[]
    for frame in range(300):
        var t:=float(frame)/60.;var release:=0.
        if t>=.6 and t<2.:release=smoothstep(0.,1.,(t-.6)/1.4)
        elif t>=2. and t<3.:release=1.
        elif t>=3. and t<4.4:release=1.-smoothstep(0.,1.,(t-3.)/1.4)
        pivot.basis=home*Basis(Vector3.FORWARD,deg_to_rad(float(row.service_release_degrees))*release)
        await RenderingServer.frame_post_draw
        if frame%30==0 or frame==299:
            samples.append({"frame":frame,"release":release,"pivot_origin":str(pivot.global_position),"pin_origin":str(asset.find_child(row.hinge_pin,true,false).global_position)})
            root.get_texture().get_image().save_png(out+"frame_%03d.png"%frame)
    FileAccess.open(out+"take.json",FileAccess.WRITE).store_string(JSON.stringify({"source_sha256":spec.source_sha256,"component_sha256":spec.component_sha256,"samples":samples,"scope":"Five-second actual current collar lever open/hold/close in one fixed camera, source-authored mesh and pivot. Silent mechanism diagnostic; no normal-operation shutter control, native input or full service acceptance."},"  "))
    print("I_COLLAR_MOTION_FINISHED");world.queue_free();await process_frame;quit()
