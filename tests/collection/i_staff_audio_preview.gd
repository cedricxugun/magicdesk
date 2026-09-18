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
    var transport:Node=load("res://collection/i_music_transport.gd").new();asset.add_child(transport)
    transport.setup("res://assets/collection/art/I/moonlight_candidate/manifest.json")
    projection.set_score_position(1,0.)
    for i in range(5):await process_frame
    transport.play_complete();transport.seek_total(8.)
    var states:Array=[]
    for frame in range(300):
        await process_frame
        projection.set_score_position(transport.index+1,transport.score_quarter_estimate())
        if frame%30==0:states.append({"frame":frame,"transport":transport.snapshot(),"projection":projection.status.duplicate(true)})
    transport.stop()
    FileAccess.open("res://../review/I_refinement/moonlight/projection/audio_excerpt.json",FileAccess.WRITE).store_string(JSON.stringify({"samples":states,"scope":"10-second independent R9 score projection excerpt driven by actual audio transport and unaccepted estimated alignment. Mouth geometry, emitter animation and native UI unfinished."},"  "))
    print("I_STAFF_AUDIO_EXCERPT_FINISHED")
    host=null;scene.queue_free();await process_frame;quit()
