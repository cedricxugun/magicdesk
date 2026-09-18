extends SceneTree
var world:Node3D
var camera:Camera3D
var out:="res://../review/I_refinement/part_a_mouth/shutter_r2/staff_current/"
var report_path:="res://../review/I_refinement/part_a_mouth/shutter_r2/diaphragm/build.json"
var layout_path:=""
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
        if argument.begins_with("--layout="):layout_path=argument.trim_prefix("--layout=")
        if argument.begins_with("--out="):out=argument.trim_prefix("--out=").trim_suffix("/")+"/"
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
    var driver=load("res://collection/i_tongue_set_driver.gd").new();driver.bind(asset,spec)




    load("res://review/i_mouth_studio.gd").apply(root,env,lights)
    if layout_path.is_empty():layout_path=str(spec.get("music_optics_layout","res://assets/collection/art/I/moonlight_candidate/current_mouth/layout.json"))
    var staff=load("res://collection/i_moonlight_staff.gd").new();world.add_child(staff);staff.setup(asset,str(spec.component_sha256),layout_path)
    driver.set_opening(1.)
    camera.position=Vector3(-1.0,-3.4,-.6);camera.look_at(Vector3(0,.03,0),Vector3.FORWARD)
    var samples:Array=[]
    for sample in [[1,0.],[1,32.],[2,0.],[2,320.],[3,0.],[3,640.]]:
        for frame in range(60):
            staff.set_score_position(sample[0],sample[1],1.)
            await RenderingServer.frame_post_draw
            if staff.status.ready:break
        assert(staff.status.ready,"Score tiles did not become ready")
        staff.set_music_response(.5,true)
        await capture("m%d_q%d"%[sample[0],int(sample[1])]);samples.append(staff.status.duplicate(true))
    FileAccess.open(out+"review.json",FileAccess.WRITE).store_string(JSON.stringify({"source_sha256":spec.source_sha256,"component_sha256":spec.component_sha256,"optics_sha256":staff.layout.component_sha256,"samples":samples,"scope":"Current IAM mouth with authored optics and real three-movement score tiles. Static placement/readability samples only, no audio sync/native acceptance."},"  "))
    print("I_CURRENT_STAFF_REVIEW_FINISHED");world.queue_free();await process_frame;quit()
