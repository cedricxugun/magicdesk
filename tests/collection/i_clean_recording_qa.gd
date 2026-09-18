extends SceneTree
func _initialize()->void:
    var original:AudioStream=load("res://assets/collection/art/I/moonlight_candidate/pitman_movement_3_original.mp3")
    var cleaned:AudioStream=load("res://assets/collection/art/I/moonlight_candidate/pitman_movement_3_clean.mp3")
    var difference:=absf(original.get_length()-cleaned.get_length())
    var pcm:Dictionary=JSON.parse_string(FileAccess.get_file_as_string("res://../review/I_refinement/moonlight/mp3_clean/report.json"))
    var complete_duration:=float(pcm.pcm_clean.bytes)/8./44100.
    var passed:=absf(cleaned.get_length()-complete_duration)<.0001
    FileAccess.open("res://../review/I_refinement/moonlight/mp3_clean/godot_check.json",FileAccess.WRITE).store_string(JSON.stringify({"original_length":original.get_length(),"clean_length":cleaned.get_length(),"difference":difference,"complete_pcm_duration":complete_duration,"passed":passed,"scope":"Clean Godot duration matches the independently decoded complete PCM frame count; original metadata duration is shorter and not treated as correctness baseline. Not musical alignment acceptance."},"  "))
    print("I_CLEAN_RECORDING_QA ",original.get_length()," ",cleaned.get_length()," difference ",difference);quit(0 if passed else 1)
