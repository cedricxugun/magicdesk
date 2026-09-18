extends SceneTree
var world:Node3D
var camera:Camera3D
var out:="res://../review/I_refinement/part_a_mouth/shutter_r2/tongue_probe/runtime/"
func _initialize()->void:run.call_deferred()
func capture(name:String)->void:
    for i in range(6):await RenderingServer.frame_post_draw
    root.get_texture().get_image().save_png(out+name+".png")
func run()->void:
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
    var component:="res://assets/collection/components/I_tongue_probe.glb";var asset:Node3D=load(component).instantiate();world.add_child(asset)
    var spec:Dictionary=JSON.parse_string(FileAccess.get_file_as_string("res://../review/I_refinement/part_a_mouth/shutter_r2/tongue_probe/build.json"))
    var driver=load("res://collection/i_tongue_fields.gd").new();driver.bind(asset,spec)
    camera.position=Vector3(2.55,-2.4,-.82);camera.look_at(Vector3(0,.13,0),Vector3.FORWARD)
    var take_index:=0
    for k in [0,16,32,48,64,0]:
        driver.set_feed(float(k)/64.)
        await capture("returned_rest" if take_index==5 else "feed_%02d"%k)
        take_index+=1
    if OS.get_environment("MAGICDESK_TONGUE_LIGHT_AUDIT")=="1":
        for mode in ["no_shadows","no_ssao","neither"]:
            env.ssao_enabled=mode=="no_shadows"
            for node in world.get_children():
                if node is Light3D:node.shadow_enabled=mode=="no_ssao"
            for k in [0,16,32,48,64]:
                driver.set_feed(float(k)/64.);await capture(mode+"_%02d"%k)
        env.ssao_enabled=true
        for node in world.get_children():
            if node is Light3D:node.shadow_enabled=true
        camera.position=Vector3(-2.55,-2.4,-.82);camera.look_at(Vector3(0,.13,0),Vector3.FORWARD)
        for k in [0,32,64]:
            driver.set_feed(float(k)/64.);await capture("reference_side_%02d"%k)
    if OS.get_environment("MAGICDESK_TONGUE_VIDEO")=="1":
        var view:=OS.get_environment("MAGICDESK_TONGUE_VIDEO_VIEW")
        camera.position=Vector3(-2.55,-2.4,-.82) if view=="reference" else Vector3(2.55,-2.4,-.82)
        camera.look_at(Vector3(0,.13,0),Vector3.FORWARD)
        var frames_dir:String=out+"video_frames_"+str(spec.source_sha256).substr(0,10)+("_reference" if view=="reference" else "_original")+"/";DirAccess.make_dir_recursive_absolute(frames_dir)
        for frame in range(180):
            var time:=float(frame)/30.;var v:=clampf((time-.3)/2.,0.,1.) if time<3.3 else 1.-clampf((time-3.3)/2.,0.,1.)
            driver.set_feed(v*v*(3.-2.*v))
            for i in range(2):await RenderingServer.frame_post_draw
            root.get_texture().get_image().save_png(frames_dir+"frame_%04d.png"%frame)
    driver.set_feed(1.)
    for node in asset.find_children("*","MeshInstance3D",true,false):
        if "Porcelain" in str(node.name) or "IrisOuterCase" in str(node.name):node.hide()
    camera.position=Vector3(1.25,1.8,-1.35);camera.look_at(Vector3(.2,.30,-.4),Vector3.FORWARD);await capture("stored_cassette_diagnostic")
    FileAccess.open(out+"review.json",FileAccess.WRITE).store_string(JSON.stringify({"source_sha256":spec.source_sha256,"component_sha256":FileAccess.get_sha256(component),"motion_fields":driver.receipts,"scope":"Actual Metal one-tongue 0/25/50/75/100 percent and return. Other two tongues static. Cassette frame hides casing for diagnostics, not a normal OPEN state. No art or full device acceptance."},"  "))
    print("I_TONGUE_REVIEW_FINISHED");world.queue_free();await process_frame;quit()
