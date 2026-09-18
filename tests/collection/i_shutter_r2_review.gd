extends SceneTree
var world:Node3D
var camera:Camera3D
var out:="res://../review/I_refinement/part_a_mouth/shutter_r2/runtime/"
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
    var component:="res://assets/collection/components/I_part_a_shutter_r2.glb";var asset:Node3D=load(component).instantiate();world.add_child(asset)
    var spec:Dictionary=JSON.parse_string(FileAccess.get_file_as_string("res://../review/I_refinement/part_a_mouth/shutter_r2/build.json"))
    await capture("rest")
    camera.position=Vector3(2.55,-2.4,-.82);camera.look_at(Vector3(0,.13,0),Vector3.FORWARD);await capture("rest_oblique")
    if OS.get_environment("MAGICDESK_MOUTH_DIAGNOSTICS")=="1":
        for part in ["Porcelain","IrisOuterCase","ConcaveMachinedMask"]:
            var hidden:Array=[]
            for node in asset.find_children("*","MeshInstance3D",true,false):
                if part in str(node.name):node.hide();hidden.append(node)
            await capture("diagnostic_without_"+part)
            for node in hidden:node.show()
        for node in world.get_children():
            if node is Light3D:node.shadow_enabled=false
        await capture("diagnostic_no_light_shadows")
        env.ssao_enabled=false
        await capture("diagnostic_no_shadows_or_ssao")
    for name in spec.shutter_meshes:asset.find_child(name,true,false).hide()
    await capture("grille_diagnostic_shutters_hidden")
    FileAccess.open(out+"review.json",FileAccess.WRITE).store_string(JSON.stringify({"source_sha256":spec.source_sha256,"component_sha256":FileAccess.get_sha256(component),"motion_implemented":false,"scope":"REST-only Metal silhouette review. Hidden-shutter frame is an anatomy diagnostic, not implemented OPEN. No final art acceptance or main App integration."},"  "))
    print("I_SHUTTER_R2_REVIEW_FINISHED");world.queue_free();await process_frame;quit()
