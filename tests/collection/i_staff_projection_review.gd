extends SceneTree
var host:Node3D
var out:="res://../review/I_refinement/moonlight/projection/"
func _initialize()->void:run.call_deferred()
func capture(name:String)->void:
    for i in range(5):await RenderingServer.frame_post_draw
    host.render_view.get_texture().get_image().save_png(out+name+".png")
func run()->void:
    set_meta("collection_no_save",true);set_meta("collection_no_audio",true);set_meta("collection_skip_intro",true);DirAccess.make_dir_recursive_absolute(out)
    var scene:Node=load("res://main.tscn").instantiate();root.add_child(scene)
    for i in range(12):await process_frame
    host=scene.get_node("Render/HeliosDesktop");host.set_process(false);host.power=1.;host.power_target=1.;host.muted=true
    var shared:Node3D=host.collection;shared._legacy_set_visible(false);shared._set_base_frame("shared")
    host.env.ambient_light_energy=.35;var energies:Array=[24.,25.,4.];var n:=0
    for child in host.get_children():
        if child is AreaLight3D:child.light_energy=energies[n];child.light_size=.35;n+=1
    var asset:Node3D=load("res://assets/collection/components/I_restore_r9.glb").instantiate();host.add_child(asset)
    var motion:RefCounted=load("res://collection/i_restore_motion.gd").new();motion.setup(asset);motion.apply(1.,1.)
    var projection:Node3D=load("res://collection/i_staff_projection.gd").new();asset.add_child(projection);projection.setup(asset)
    var home:Transform3D=host.camera.global_transform;var fov:float=host.camera.fov;var rows:Array=[]
    for test in [{"m":1,"q":0.},{"m":1,"q":32.},{"m":2,"q":0.},{"m":2,"q":328.},{"m":3,"q":0.},{"m":3,"q":640.}]:
        projection.set_score_position(test.m,test.q);host.camera.global_transform=home;host.camera.fov=fov
        await capture("m"+str(test.m)+"_q"+str(int(test.q))+"_desktop")
        var mouth:Node3D=asset.find_child("IH1_Mouth",true,false)
        host.camera.global_position=mouth.global_position+Vector3(1.8,.35,2.6);host.camera.look_at(mouth.global_position);host.camera.fov=36.
        await capture("m"+str(test.m)+"_q"+str(int(test.q))+"_close")
        rows.append(projection.status.duplicate(true))
    var result:={"samples":rows,"component_sha256":FileAccess.get_sha256("res://assets/collection/components/I_restore_r9.glb"),"scope":"Actual Metal sampled placement of real score tiles on R9 mouth. Not a final mouth model, animated emitter effect, audio sync, native input or final readability/performance acceptance."}
    FileAccess.open(out+"review.json",FileAccess.WRITE).store_string(JSON.stringify(result,"  "));print("I_STAFF_PROJECTION_REVIEW ",rows.size());host=null;scene.queue_free();await process_frame;quit()
