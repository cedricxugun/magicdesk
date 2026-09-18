extends SceneTree
var world:Node3D
var camera:Camera3D
var out:="res://../review/I_refinement/part_a_mouth/shutter_r2/diaphragm/motion/"
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
    var driver=load("res://collection/i_tongue_set_driver.gd").new();driver.bind(asset,spec)




    var receipt:Dictionary=load("res://review/i_mouth_studio.gd").apply(root,env,lights)
    var response=load("res://collection/i_diaphragm_response.gd").new();response.bind(asset,spec.diaphragm)
    driver.set_opening(1.)

    # Side inspection of the connected suspension; casing is hidden explicitly
    # for this diagnostic take. It is not the complete app's opening animation.
    var keep:Dictionary={}
    var moving_node:=asset.find_child(str(spec.diaphragm.moving),true,false)
    for node in moving_node.find_children("*","MeshInstance3D",true,false):keep[str(node.name)]=true
    for name in spec.diaphragm.morphs:keep[str(name)]=true
    for row in spec.diaphragm.connections:keep[str(row.rear_seat)]=true
    for node in asset.find_children("*","MeshInstance3D",true,false):
        node.visible=keep.has(str(node.name)) or str(node.name).begins_with("IAM_Response")
    camera.position=Vector3(1.7,.7,-.35);camera.look_at(Vector3(0,.3,0),Vector3.FORWARD)
    var stamp:String=spec.source_sha256.substr(0,8)
    var directory:String=out+stamp+"/";DirAccess.make_dir_recursive_absolute(directory)
    for frame in range(330):
        if frame==36:response.set_load(1.)
        if frame==102:response.set_load(0.);response.impulse(.65)
        if frame==180:response.set_load(.65)
        if frame==216:response.quiet()
        response.tick(1./60.);await RenderingServer.frame_post_draw
        root.get_texture().get_image().save_png(directory+"frame_%04d.png"%frame)
    FileAccess.open(out+"take.json",FileAccess.WRITE).store_string(JSON.stringify({"source_sha256":spec.source_sha256,"component_sha256":spec.component_sha256,"frames":330,"fps":60,"directory":directory,"settled":response.settled(),"scope":"Actual Metal isolated suspension diagnostic: load, release, rebound, second load, quiet cancellation. Casing and guard deliberately hidden; not an operating full-conch or native input take."},"  "))
    print("I_DIAPHRAGM_MOTION_FINISHED");world.queue_free();await process_frame;quit()
