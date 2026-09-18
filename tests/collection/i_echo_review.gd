extends SceneTree
var world:Node3D
var camera:Camera3D
var out:="res://../review/I_refinement/part_a_mouth/shutter_r2/echo_r2/runtime/"
var report_path:="res://../review/I_refinement/part_a_mouth/shutter_r2/diaphragm/build.json"
func _initialize()->void:run.call_deferred()
var timings:Dictionary={}
func capture(name:String)->void:
    var gpu:Array=[]
    for i in range(30):
        await RenderingServer.frame_post_draw
        if i>=10:gpu.append(RenderingServer.viewport_get_measured_render_time_gpu(root.get_viewport_rid()))
    timings[name]={"gpu_ms":gpu}
    root.get_texture().get_image().save_png(out+name+".png")
func run()->void:
    for argument in OS.get_cmdline_user_args():
        if argument.begins_with("--report="):
            report_path=argument.trim_prefix("--report=")
            out=report_path.get_base_dir()+"/studio/"
    root.size=Vector2i(1200,1000);root.msaa_3d=Viewport.MSAA_4X;DirAccess.make_dir_recursive_absolute(out)
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
    var aperture:Dictionary=JSON.parse_string(FileAccess.get_file_as_string("res://assets/collection/art/I/diaphragm/aperture_profile.json"))
    var rig=load("res://collection/i_mouth_response_rig.gd").new();rig.bind(asset,spec,aperture)





    load("res://review/i_mouth_studio.gd").apply(root,env,lights)
    var presentation=load("res://collection/i_echo_presentation.gd").new();world.add_child(presentation);presentation.setup(asset,false)
    camera.position=Vector3(-2.55,-2.4,-.82);camera.look_at(Vector3(0,.0,0),Vector3.FORWARD)
    rig.set_pressed(true)
    var samples:Array=[];var emitted:Array=[]
    for frame in range(360):
        if frame==60:rig.set_pressed(false)
        rig.tick(1./60.);var events:Array=rig.drain_events();emitted.append_array(events);presentation.update(1./60.,rig,events)
        await RenderingServer.frame_post_draw
        if frame in [30,108,125,140,160,175,185,200,250,359]:
            root.get_texture().get_image().save_png(out+"frame_%03d.png"%frame)
            samples.append({"frame":frame,"rig":rig.state(),"presentation":presentation.receipt.duplicate(true)})
    assert(emitted.size()==2 and presentation.packets.is_empty())
    # Mid-flight closing invalidates the packet; reopening cannot revive it.
    rig.set_pressed(true)
    for frame in range(180):rig.tick(1./60.);presentation.update(1./60.,rig,rig.drain_events())
    rig.set_pressed(false)
    for frame in range(60):rig.tick(1./60.);presentation.update(1./60.,rig,rig.drain_events())
    assert(presentation.packets.size()==1)
    rig.set_open(false)
    for frame in range(6):rig.tick(1./60.);presentation.update(1./60.,rig,rig.drain_events())
    assert(presentation.packets.size()==1 and presentation.packets[0].cancelled)
    rig.set_open(true)
    for frame in range(60):rig.tick(1./60.);presentation.update(1./60.,rig,rig.drain_events())
    assert(presentation.packets.is_empty())
    FileAccess.open(out+"review.json",FileAccess.WRITE).store_string(JSON.stringify({"source_sha256":spec.source_sha256,"component_sha256":spec.component_sha256,"samples":samples,"events":emitted,"cancel_fade_passed":true,"scope":"Actual Metal authored wavefront/mask with one mechanical/audio-scheduler clock; silent visual take. Wave returns at scheduler event and cancels without revival. Audio listening/native/final-art not certified."},"  "))
    print("I_ECHO_REVIEW_FINISHED");world.queue_free();await process_frame;quit()
