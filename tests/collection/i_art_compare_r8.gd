extends SceneTree
var host:Node3D
var out:="res://../review/I_refinement/art_r8/visual/"
func _initialize()->void:run.call_deferred()
func capture(label:String)->void:
    for i in range(5):await RenderingServer.frame_post_draw
    host.render_view.get_texture().get_image().save_png(out+label+".png")
func run()->void:
    set_meta("collection_no_save",true);set_meta("collection_no_audio",true);set_meta("collection_skip_intro",true)
    DirAccess.make_dir_recursive_absolute(out)
    var scene:Node=load("res://main.tscn").instantiate();root.add_child(scene)
    for i in range(12):await process_frame
    host=scene.get_node("Render/HeliosDesktop");host.set_process(false);host.power=1.;host.power_target=1.;host.muted=true
    var shared:Node3D=host.collection;shared._legacy_set_visible(false);shared._set_base_frame("shared")
    host.env.ambient_light_energy=.35;var energies:Array=[24.,25.,4.];var n:=0
    for child in host.get_children():
        if child is AreaLight3D:child.light_energy=energies[n];child.light_size=.35;n+=1
    var camera_home:Transform3D=host.camera.global_transform;var fov:float=host.camera.fov;var reports:Array=[]
    for variant in ["before","after"]:
        var path:="res://assets/collection/components/I_service_r7_motion.glb" if variant=="before" else "res://assets/collection/components/I_art_r8.glb"
        var asset:Node3D=load(path).instantiate();host.add_child(asset)
        var driver:Node=load("res://collection/i_runtime.gd").new();asset.add_child(driver);driver.setup(asset,"res://assets/collection/i_service_rig_r7.json","res://assets/collection/i_runtime_rig_r7.json")
        driver.apply_state(driver.simulation.state(),0.);driver.service.amount=.5;driver.service.apply()
        var console:Node3D=load("res://collection/i_console.gd").new();shared.add_child(console);console.setup(shared)
        for i in range(4):await physics_frame
        console.seat_captions();console.update(0.,driver.simulation,[])
        host.camera.global_transform=camera_home;host.camera.fov=fov
        await capture(variant+"_inspection_open")
        var mouth:Node3D=driver.node("IH1_Mouth");var iris:Node3D=driver.node("IS4_IrisCartridge");var perforated:Node3D=driver.node("IH1_PerforatedAcousticPlate_0230");iris.hide();perforated.hide()
        var core_meshes:Array=[];var hidden_for_core:Array=[]
        for name in ["IS4_PerforatedCartridge","IS4_DiaphragmCartridge","IS4_ReservoirCartridge"]:core_meshes.append_array(driver.node(name).find_children("*","MeshInstance3D",true,false))
        core_meshes.append(driver.node("IP2_HollowPressureConnector_0040"))
        for mesh in asset.find_children("*","MeshInstance3D",true,false):
            if mesh.visible and not core_meshes.has(mesh):hidden_for_core.append(mesh);mesh.hide()
        host.camera.global_position=mouth.global_position+Vector3(2.2,.45,2.4);host.camera.look_at(mouth.global_position+Vector3(0,.08,0));host.camera.fov=34.
        await capture(variant+"_core_cutaway")
        for mesh in hidden_for_core:mesh.show()
        iris.show();perforated.show()
        var cage:Node3D=driver.node("IS7_CageLeft");var keep:Array=cage.find_children("*","MeshInstance3D",true,false)
        var bounds:=AABB();var first:=true
        for mesh in keep:
            var box:AABB=mesh.global_transform*mesh.get_aabb()
            bounds=box if first else bounds.merge(box);first=false
        for mesh in asset.find_children("*","MeshInstance3D",true,false):
            if not keep.has(mesh):mesh.hide()
        host.camera.global_position=bounds.get_center()+Vector3(1.5,.25,2.3).normalized()*4.2;host.camera.look_at(bounds.get_center());host.camera.fov=40.
        await capture(variant+"_cage_isolated")
        reports.append({"variant":variant,"component":path,"sha256":FileAccess.get_sha256(path)})
        driver=null;asset.queue_free();console.queue_free();await process_frame;await process_frame
    FileAccess.open(out+"comparison.json",FileAccess.WRITE).store_string(JSON.stringify({"variants":reports,"service_amount":.5,"scope":"Matched lighting and views at cage-open state before core extraction. Core cutaway isolates core and hides iris/perforated sheet; isolated cage hides other body meshes and fits its bounds. Diagnostic views, not native App or full acceptance."},"  "))
    host=null;shared=null;scene.queue_free();await process_frame;quit()
