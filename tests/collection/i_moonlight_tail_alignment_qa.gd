extends SceneTree
func _initialize()->void:run.call_deferred()
func run()->void:
    var transport=load("res://collection/i_music_transport.gd").new();root.add_child(transport);transport.setup("res://assets/collection/art/I/moonlight_candidate/manifest.json");transport.play_complete();transport.pause()
    var review:Dictionary=JSON.parse_string(FileAccess.get_file_as_string("res://../review/I_refinement/moonlight/onset_refinement/applied_tail_anchors.json"));var samples:Array=[]
    for patch in review.patches:
        var index:int=int(patch.movement)-1
        for anchor in patch.anchors:
            var target:float=float(transport.tracks[index].start)+float(anchor.candidate_seconds)
            transport.seek_total(target)
            var error:=absf(transport.score_quarter_estimate()-float(anchor.quarter));assert(error<.00001)
            samples.append({"movement":patch.movement,"quarter":anchor.quarter,"seconds":anchor.candidate_seconds,"runtime_quarter_error":error})
            await create_timer(.03).timeout
    transport.stop();await create_timer(.10).timeout;transport.queue_free();transport=null;await process_frame
    FileAccess.open("res://../review/I_refinement/moonlight/onset_refinement/runtime_tail_check.json",FileAccess.WRITE).store_string(JSON.stringify({"passed":true,"samples":samples,"scope":"Actual transport selects the expected engraved quarter at the four locally reviewed anchors. Does not certify the rest of the estimated warp or audible timing."},"  "))
    print("I_MOONLIGHT_TAIL_ALIGNMENT_QA true");quit()
