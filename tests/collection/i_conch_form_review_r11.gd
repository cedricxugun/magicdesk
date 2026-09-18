extends SceneTree
var host:Node3D
var out:="res://../review/I_refinement/conch_r11/runtime/"
func _initialize()->void:run.call_deferred()
func capture(name:String)->void:
    for i in range(5):await RenderingServer.frame_post_draw
    host.render_view.get_texture().get_image().save_png(out+name+".png")
func run()->void:
    var contract_path:="res://../production/I_refinement/conch_r11/shape_contract.json"
    for arg in OS.get_cmdline_user_args():
        if arg.begins_with("--contract="):contract_path="res://../"+arg.trim_prefix("--contract=")
    var contract:Dictionary=JSON.parse_string(FileAccess.get_file_as_string(contract_path))
    out="res://../"+str(contract.build_report).get_base_dir()+"/runtime/"
    set_meta("collection_no_save",true);set_meta("collection_no_audio",true);set_meta("collection_skip_intro",true);DirAccess.make_dir_recursive_absolute(out)
    var scene:Node=load("res://main.tscn").instantiate();root.add_child(scene)
    for i in range(12):await process_frame
    host=scene.get_node("Render/HeliosDesktop");host.set_process(false);host.power=1.;host.power_target=1.;host.muted=true
    var shared:Node3D=host.collection;shared._legacy_set_visible(false);shared._set_base_frame("shared")
    host.env.ambient_light_energy=.30;var energies:Array=[20.,21.,4.];var n:=0
    for child in host.get_children():
        if child is AreaLight3D:child.light_energy=energies[n];child.light_size=.50;n+=1
    var component:String="res://"+str(contract.component).trim_prefix("app/");var asset:Node3D=load(component).instantiate();host.add_child(asset)
    var spec:Dictionary=JSON.parse_string(FileAccess.get_file_as_string("res://../"+str(contract.build_report)))
    var home:Transform3D=host.camera.global_transform;var fov:float=host.camera.fov
    await capture("closed_desktop")
    var focus:=Vector3(0,2.1,0)
    host.camera.position=Vector3(.55,3.10,6.0);host.camera.look_at(focus);host.camera.fov=38.;await capture("closed_hero")
    host.camera.position=Vector3(5.,2.8,.35);host.camera.look_at(focus);await capture("closed_side")
    host.camera.position=Vector3(-.7,3.0,-5.5);host.camera.look_at(focus);await capture("closed_rear")
    for leaf in spec.leaves:
        var node:Node3D=asset.find_child(leaf.name,true,false);node.rotate_y(-float(leaf.travel))
    host.camera.global_transform=home;host.camera.fov=fov;await capture("iris_open_only_desktop")
    host.camera.position=Vector3(.55,3.10,6.0);host.camera.look_at(focus);host.camera.fov=38.;await capture("iris_open_only_hero")
    FileAccess.open(out+"review.json",FileAccess.WRITE).store_string(JSON.stringify({"component":component,"sha256":FileAccess.get_sha256(component),"source_sha256":spec.source_sha256,"scope":"Actual Metal new closed-form conch and iris-open-only views on original shared base. Shell deployment, detailed assembly, full collision/native/audio/art acceptance not performed."},"  "))
    print("I_CONCH_FORM_REVIEW_FINISHED");host=null;scene.queue_free();await process_frame;quit()
