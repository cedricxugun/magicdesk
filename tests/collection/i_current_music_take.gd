extends SceneTree
var world:Node3D
var camera:Camera3D
var out:="res://../review/I_refinement/part_a_mouth/shutter_r2/music_current_take/"
var report_path:="res://../review/I_refinement/part_a_mouth/shutter_r2/diaphragm/build.json"
var response_take:=false
var take_output:=""
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
        if argument=="--response-take":response_take=true
        if argument.begins_with("--take-output="):take_output=argument.trim_prefix("--take-output=")
        if argument.begins_with("--report="):
            report_path=argument.trim_prefix("--report=")
            out=report_path.get_base_dir()+"/studio/"
    if response_take:out="res://../review/I_refinement/moonlight/current_mouth/response/take_r1/"
    if not take_output.is_empty():out=take_output.trim_suffix("/")+"/"
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
    var aperture:Dictionary=JSON.parse_string(FileAccess.get_file_as_string("res://assets/collection/art/I/diaphragm/aperture_profile.json"))
    var rig=load("res://collection/i_mouth_response_rig.gd").new();rig.bind(asset,spec,aperture)





    load("res://review/i_mouth_studio.gd").apply(root,env,lights)

    var music=load("res://collection/i_moonlight_controller.gd").new();world.add_child(music);music.setup(asset,spec,rig)
    camera.position=Vector3(-1.0,-3.4,-.6);camera.look_at(Vector3(0,.03,0),Vector3.FORWARD)
    music.toggle();var samples:Array=[]
    var frame_count:=1440 if response_take else 1080
    for frame in range(frame_count):
        if response_take:
            if frame==600:
                music.seek(float(music.transport.tracks[2].start)+25.)
                camera.position=Vector3(-1.15,-1.45,-.28);camera.look_at(Vector3(0,.04,0),Vector3.FORWARD)
            if frame==960:music.toggle()
            if frame==1140:
                music.stop(true)
                camera.position=Vector3(-1.0,-3.4,-.6);camera.look_at(Vector3(0,.03,0),Vector3.FORWARD)
        music.tick(1./60.);rig.tick(1./60.)
        await RenderingServer.frame_post_draw
        if frame%60==0:
            samples.append({"frame":frame,"music":music.status.duplicate(true),"rig":rig.state()})
            root.get_texture().get_image().save_png(out+"frame_%03d.png"%frame)
    if response_take:assert(rig.stage=="closed" and rig.suspension.settled() and music.transport.state=="stopped")
    FileAccess.open(out+"take.json",FileAccess.WRITE).store_string(JSON.stringify({"source_sha256":spec.source_sha256,"component_sha256":spec.component_sha256,"optics_sha256":music.staff.layout.component_sha256,"samples":samples,"frames":frame_count,"response_take":response_take,"scope":"Actual audio-clock-driven Moonlight excerpts after current mouth/staff reveal; response take cuts to third movement and close camera, pauses then fades/closes. Real engraved tiles; global alignment remains estimated. Not full native music or complete-conch acceptance."},"  "))
    print("I_CURRENT_MUSIC_TAKE_FINISHED");world.queue_free();await process_frame;quit()
