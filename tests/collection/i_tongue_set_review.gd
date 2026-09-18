extends SceneTree
var world:Node3D
var camera:Camera3D
var out:="res://../review/I_refinement/part_a_mouth/shutter_r2/tongue_set/runtime/"
var report_path:="res://../review/I_refinement/part_a_mouth/shutter_r2/tongue_set/build.json"
func _initialize()->void:run.call_deferred()
func capture(name:String)->void:
    for i in range(6):await RenderingServer.frame_post_draw
    root.get_texture().get_image().save_png(out+name+".png")
func run()->void:
    for argument in OS.get_cmdline_user_args():
        if argument.begins_with("--report="):
            report_path=argument.trim_prefix("--report=")
            out=report_path.get_base_dir()+"/runtime/"
    root.size=Vector2i(1200,1000);root.msaa_3d=Viewport.MSAA_4X;DirAccess.make_dir_recursive_absolute(out)
    world=Node3D.new();root.add_child(world)
    var env:=Environment.new();env.background_mode=Environment.BG_COLOR;env.background_color=Color(.030,.029,.026)
    var panorama:=PanoramaSkyMaterial.new();panorama.panorama=load("res://assets/studio_small_09_4k.exr");panorama.energy_multiplier=.20
    var sky:=Sky.new();sky.sky_material=panorama;env.sky=sky;env.ambient_light_source=Environment.AMBIENT_SOURCE_SKY;env.ambient_light_energy=.30;env.reflected_light_source=Environment.REFLECTION_SOURCE_SKY;env.tonemap_mode=Environment.TONE_MAPPER_AGX
    env.ssao_enabled=true;env.ssao_radius=.04;env.ssao_intensity=.6;env.glow_enabled=false
    var environment:=WorldEnvironment.new();environment.environment=env;world.add_child(environment)
    camera=Camera3D.new();world.add_child(camera);camera.fov=32.;camera.near=.02;camera.position=Vector3(1.3,-3.2,-.80);camera.look_at(Vector3(0,.13,0),Vector3.FORWARD)
    for row in [[Vector3(-2,-2,-2.5),5.,Vector2(1.5,2.3)],[Vector3(2,-.3,-.7),3.,Vector2(1.,2.)],[Vector3(-.5,2,-2),4.,Vector2(1.5,2.)]]:
        var light:=AreaLight3D.new();world.add_child(light);light.position=row[0];light.look_at(Vector3.ZERO,Vector3.FORWARD);light.light_energy=row[1];light.area_size=row[2];light.area_normalize_energy=true;light.area_range=10.;light.light_size=.25;light.shadow_enabled=true;light.shadow_normal_bias=.012
    var spec:Dictionary=JSON.parse_string(FileAccess.get_file_as_string(report_path))
    var component:String="res://"+str(spec.component).trim_prefix("app/");var asset:Node3D=load(component).instantiate();world.add_child(asset)
    assert(FileAccess.get_sha256(component)==spec.component_sha256)
    var driver=load("res://collection/i_tongue_set_driver.gd").new();driver.bind(asset,spec)
    for view in ["original","reference"]:
        camera.position=Vector3(2.55,-2.4,-.82) if view=="original" else Vector3(-2.55,-2.4,-.82);camera.look_at(Vector3(0,.13,0),Vector3.FORWARD)
        for k in [0,25,50,75,100]:
            driver.set_opening(float(k)/100.);await capture(view+"_%03d"%k)
    camera.position=Vector3(1.70,2.7,-1.1);camera.look_at(Vector3(0,.28,-.12),Vector3.FORWARD)
    for k in [0,50,100]:
        driver.set_opening(float(k)/100.);await capture("rear_%03d"%k)
    if spec.has("guide_interfaces"):
        camera.position=Vector3(.1,-.7,-.2);camera.look_at(Vector3(.47,.05,-.61),Vector3.FORWARD)
        driver.set_opening(.15);await capture("front_guide_detail")
        camera.position=Vector3(-.20,-.6,.16);camera.look_at(Vector3(-.49,.02,.565),Vector3.FORWARD)
        for amount in [0.,.02,.05]:
            driver.set_opening(amount);await capture("return_detail_%03d"%int(amount*1000))
        driver.set_opening(1.)
    for node in asset.find_children("*","MeshInstance3D",true,false):
        if "Porcelain" in str(node.name) or "IrisOuterCase" in str(node.name):node.hide()
    camera.position=Vector3(1.25,1.8,-1.35);camera.look_at(Vector3(.0,.30,-.4),Vector3.FORWARD);await capture("three_cassettes_diagnostic")
    if spec.has("hardware"):
        var keep:Dictionary={}
        var carriage:=asset.find_child(str(spec.tongues[0].carriage),true,false)
        for node in carriage.find_children("*","MeshInstance3D",true,false):keep[str(node.name)]=true
        for node in asset.find_children("*","MeshInstance3D",true,false):
            node.visible=keep.has(str(node.name)) or str(node.name).begins_with("IAM_Cassette0_")
        camera.position=Vector3(1.04,1.0,-.69);camera.look_at(Vector3(.44,.36,-.60),Vector3.FORWARD)
        await capture("cassette_0_isolated")
        asset.find_child("IAM_TongueSpoolCore",true,false).hide()
        await capture("cassette_0_motor_cutaway")
    FileAccess.open(out+"review.json",FileAccess.WRITE).store_string(JSON.stringify({"source_sha256":spec.source_sha256,"component_sha256":FileAccess.get_sha256(component),"fields":driver.receipts,"scope":"Actual Metal three-tongue closed/quarter/half/three-quarter/open; two fixed cameras. Diagnostic casing removal is not a normal operating state. Full art/drive/hardware/native acceptance pending."},"  "))
    print("I_TONGUE_SET_REVIEW_FINISHED");world.queue_free();await process_frame;quit()
