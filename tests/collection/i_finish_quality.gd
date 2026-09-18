extends SceneTree
var world:Node3D
var camera:Camera3D
var out:="res://../review/I_refinement/part_a_mouth/shutter_r2/finish_quality/"
var report_path:="res://../review/I_refinement/part_a_mouth/shutter_r2/front_guides/build.json"
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


    RenderingServer.viewport_set_measure_render_time(root.get_viewport_rid(),true)
    var variants=["base","ultra","ultra_atlas4k","ultra_atlas8k","ultra_small","ultra_taa","full_mesh"]
    for variant in variants:
        var high:bool=variant!="base"
        RenderingServer.positional_soft_shadow_filter_set_quality(RenderingServer.SHADOW_QUALITY_SOFT_ULTRA if high else RenderingServer.SHADOW_QUALITY_SOFT_LOW)
        root.use_taa=variant=="ultra_taa"
        root.positional_shadow_atlas_size=8192 if variant=="ultra_atlas8k" else 4096
        for quadrant in range(4):root.set_positional_shadow_atlas_quadrant_subdiv(quadrant,[2,2,3,4][quadrant])
        if variant in ["ultra_atlas4k","ultra_atlas8k"]:
            for quadrant in range(3):root.set_positional_shadow_atlas_quadrant_subdiv(quadrant,Viewport.SHADOW_ATLAS_QUADRANT_SUBDIV_1)
        root.mesh_lod_threshold=0. if variant=="full_mesh" else 1.
        for light in lights:light.light_size=.06 if variant=="ultra_small" else .25
        camera.position=Vector3(-.20,-.6,.16);camera.look_at(Vector3(-.49,.02,.565),Vector3.FORWARD);driver.set_opening(.05)
        await capture(variant+"_close")
        camera.position=Vector3(-2.55,-2.4,-.82);camera.look_at(Vector3(0,.13,0),Vector3.FORWARD);driver.set_opening(.5)
        await capture(variant+"_whole")
    FileAccess.open(out+"audit.json",FileAccess.WRITE).store_string(JSON.stringify({"source_sha256":spec.source_sha256,"component_sha256":spec.component_sha256,"variants":variants,"gpu_timings":timings,"scope":"Current Metal renderer sampling/atlas/LOD/PCSS size and temporal candidate comparison. GPU timings are per-view measured samples, not whole App performance acceptance."},"  "))
    print("I_FINISH_QUALITY_FINISHED");world.queue_free();await process_frame;quit()
