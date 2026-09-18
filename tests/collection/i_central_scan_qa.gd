extends SceneTree
## Real catalog edge/tile crossings, fixed scanner and paused clock behavior.
func _initialize()->void:run.call_deferred()
func run()->void:
    var layout_path:="res://assets/collection/art/I/moonlight_candidate/central_scan_r1/layout.json"
    var output_path:="res://../review/I_refinement/moonlight/central_scan_r1/qa.json"
    for arg in OS.get_cmdline_user_args():
        if arg.begins_with("--layout="):layout_path=arg.trim_prefix("--layout=")
        elif arg.begins_with("--out="):output_path=arg.trim_prefix("--out=")
    var spec:Dictionary=JSON.parse_string(FileAccess.get_file_as_string("res://../review/I_refinement/part_a_mouth/shutter_r2/collar_clamps/build.json"))
    var asset:Node3D=load("res://"+str(spec.component).trim_prefix("app/")).instantiate();root.add_child(asset)
    var staff=load("res://collection/i_moonlight_staff.gd").new();root.add_child(staff)
    staff.setup(asset,str(spec.component_sha256),layout_path)
    var samples:Array=[]
    for movement in [1,2,3]:
        var row:Dictionary=staff.catalog.movements[movement-1]
        var quarter_samples:Array=[0.,float(row.anchors[-1].quarter)]
        # Sample both sides of several actual tile-boundary crossings.
        for anchor in row.anchors:
            var offset:float=float(anchor.x)-float(row.height)*staff.layout.width/staff.layout.height*.5
            if fposmod(offset,row.tile_width)<22.:quarter_samples.append(float(anchor.quarter))
        for quarter in quarter_samples:
            for attempt in range(120):
                staff.set_score_position(movement,quarter,1.)
                await process_frame
                if staff.status.ready:break
            assert(staff.status.ready)
            assert(absf((staff.status.note_x-staff.status.offset)/staff.status.width-.5)<.000001)
            assert(staff.cache.size()<=4)
            if quarter==0.:
                assert(staff.status.first_tile==-1 and staff.status.valid_tiles[0]==0.,"Leading blank must not wrap to the last tile")
            if quarter==float(row.anchors[-1].quarter):
                assert(staff.status.valid_tiles[1]==0. or staff.status.valid_tiles[2]==0.,"Trailing page must not duplicate the last tile")
            samples.append(staff.status.duplicate(true))
    var transport=load("res://collection/i_music_transport.gd").new();root.add_child(transport)
    transport.setup("res://assets/collection/art/I/moonlight_candidate/manifest.json")
    assert(transport.player.volume_db==0.)
    transport.play_complete();transport.pause();transport.seek_total(324.661406)
    for frame in range(20):
        staff.set_score_position(1,transport.score_quarter_estimate(),1.)
        await process_frame
    var before:Dictionary=staff.status.duplicate(true)
    for frame in range(20):
        staff.set_score_position(1,transport.score_quarter_estimate(),1.)
        staff.set_music_response(transport.response_level(),false)
        await process_frame
    assert(is_equal_approx(before.offset,staff.status.offset) and staff.status.scan_level==0. and not staff.status.scan_playing)
    assert(absf(transport.score_quarter_estimate()-270.)<.00001)
    var actual_motion:=asset.find_child("IAM_DiaphragmMotion",true,false) as Node3D
    var rest:=actual_motion.position
    for displacement in [-.006,0.,.006]:
        actual_motion.position=rest+Vector3(0,displacement,0)
        staff.set_music_response(.5,true)
        for index in range(staff.scan_tips.size()):
            var binding:Dictionary=staff.scan_tips[index]
            var ray:=staff.optics.find_child(str(staff.layout.scanner.tips[index].ray),true,false) as MeshInstance3D
            var arrays:Array=ray.mesh.surface_get_arrays(0)
            var points:PackedVector3Array=arrays[Mesh.ARRAY_VERTEX];var uv:PackedVector2Array=arrays[Mesh.ARRAY_TEX_UV]
            var center:=Vector3.ZERO;var count:=0
            for i in range(points.size()):
                if uv[i].y>.999:
                    center+=ray.transform*points[i];count+=1
            assert(count==2)
            center/=float(count)
            var delta:Vector3=staff.scan_materials[index+1].get_shader_parameter("tip_delta")
            var actual:Vector3=staff.mouth.to_local(binding.node.to_global(binding.local_point))
            assert((center+delta).distance_to(actual)<.000001,"Authored beam origin detached from moving physical tip")
    actual_motion.position=rest
    var result:Dictionary={"passed":true,"layout":layout_path,"optics_source_sha256":staff.layout.source_sha256,"optics_component_sha256":staff.layout.component_sha256,"samples":samples,"volume_db":transport.player.volume_db,"scope":"Fixed central score coordinate at actual catalog starts/ends/tile boundaries; transparent page padding, bounded cache and paused transport. One previously reviewed recording anchor. Actual ray/tine connections under displacement. No claim of all-note musical accuracy or final art."}
    FileAccess.open(output_path,FileAccess.WRITE).store_string(JSON.stringify(result,"  "))
    # The audio mix thread releases stopped Ogg playback on its next callback.
    transport.stop();await create_timer(.10).timeout
    staff.queue_free();transport.queue_free();asset.queue_free();await process_frame
    print("I_CENTRAL_SCAN_QA true samples=",samples.size());quit()
