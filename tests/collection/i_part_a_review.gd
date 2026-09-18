extends SceneTree
var world:Node3D
var camera:Camera3D
var out:="res://../review/I_refinement/part_a_mouth/runtime/"
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
    var component:="res://assets/collection/components/I_part_a_mouth.glb";var asset:Node3D=load(component).instantiate();world.add_child(asset)
    var spec:Dictionary=JSON.parse_string(FileAccess.get_file_as_string("res://../review/I_refinement/part_a_mouth/build.json"))
    var leaves:Array=[]
    for row in spec.leaves:
        var node:Node3D=asset.find_child(row.name,true,false);leaves.append({"node":node,"home":node.transform,"travel":float(row.travel)})
    var cam:Node3D=asset.find_child(spec.cam,true,false);var cam_home:Transform3D=cam.transform
    for amount in [0.,.5,1.]:
        for row in leaves:row.node.transform=row.home;row.node.basis=row.home.basis*Basis(Vector3.UP,-row.travel*amount)
        cam.transform=cam_home;cam.basis=cam_home.basis*Basis(Vector3.UP,-.25*amount)
        await capture("rest" if amount==0 else "half" if amount<1 else "open")
    # Keep the original comparison camera above; add, never substitute, the art's oblique direction.
    camera.position=Vector3(2.55,-2.4,-.82);camera.look_at(Vector3(0,.13,0),Vector3.FORWARD)
    for amount in [0.,.5,1.]:
        for row in leaves:row.node.transform=row.home;row.node.basis=row.home.basis*Basis(Vector3.UP,-row.travel*amount)
        cam.transform=cam_home;cam.basis=cam_home.basis*Basis(Vector3.UP,-.25*amount)
        await capture("rest_oblique" if amount==0 else "half_oblique" if amount<1 else "open_oblique")
    camera.position=Vector3(1.65,2.35,-.7);camera.look_at(Vector3(0,.26,0),Vector3.FORWARD);await capture("rear")
    # Diagnostic cutaway: hide guarding screens and face-side iris/case so diaphragm and shaft are inspectable.
    for node in asset.find_children("*","MeshInstance3D",true,false):
        var n:String=node.name
        if "Porcelain" in n or "Iris" in n or "Guard" in n or "Retainer" in n or "Mask" in n or "Mouth" in n or "Edge" in n or "Cam" in n or "CollarLatch" in n or "Latch" in n or "ScreenBridge" in n:node.hide()
    camera.position=Vector3(1.4,-2.2,-.7);camera.look_at(Vector3(0,.22,0),Vector3.FORWARD);await capture("diagnostic_core")
    FileAccess.open(out+"review.json",FileAccess.WRITE).store_string(JSON.stringify({"source_sha256":spec.source_sha256,"component_sha256":FileAccess.get_sha256(component),"scope":"Actual Metal isolated Part A rest/half/open/rear and diagnostic-hidden-component view. Not complete conch, physical input, full collision or final art acceptance."},"  "));print("I_PART_A_REVIEW_FINISHED");world.queue_free();await process_frame;quit()
