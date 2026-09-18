extends SceneTree
func _initialize()->void:run.call_deferred()
func run()->void:
    var first:AudioStream=load("res://assets/collection/art/I/moonlight_candidate/pitman_movement_3_original.mp3")
    var second:AudioStream=load("res://assets/collection/art/I/moonlight_candidate/pitman_movement_3_clean.mp3")
    var a:=first.instantiate_playback();var b:=second.instantiate_playback();a.start();b.start()
    var hash_a:=HashingContext.new();hash_a.start(HashingContext.HASH_SHA256)
    var hash_b:=HashingContext.new();hash_b.start(HashingContext.HASH_SHA256)
    var count_a:=0;var count_b:=0;var mismatched_blocks:=0;var peak_extra:=0.;var blocks:=0
    while (a.is_playing() or b.is_playing()) and blocks<20000:
        var left:PackedVector2Array=a.mix_audio(1.,2048) if a.is_playing() else PackedVector2Array()
        var right:PackedVector2Array=b.mix_audio(1.,2048) if b.is_playing() else PackedVector2Array()
        count_a+=left.size();count_b+=right.size()
        if not left.is_empty():hash_a.update(left.to_byte_array())
        if not right.is_empty():hash_b.update(right.to_byte_array())
        var common:=mini(left.size(),right.size())
        if left.slice(0,common).to_byte_array()!=right.slice(0,common).to_byte_array():mismatched_blocks+=1
        for index in range(common,left.size()):peak_extra=maxf(peak_extra,maxf(absf(left[index].x),absf(left[index].y)))
        for index in range(common,right.size()):peak_extra=maxf(peak_extra,maxf(absf(right[index].x),absf(right[index].y)))
        blocks+=1
        if blocks%256==0:await process_frame
    var report={"original_length":first.get_length(),"clean_length":second.get_length(),"mix_rate":AudioServer.get_mix_rate(),"original_frames":count_a,"clean_frames":count_b,"mismatched_common_blocks":mismatched_blocks,"extra_tail_peak":peak_extra,"original_pcm_sha256":hash_a.finish().hex_encode(),"clean_pcm_sha256":hash_b.finish().hex_encode(),"completed":blocks<20000,"scope":"Entire third movement decoded through actual Godot AudioStreamPlayback.mix_audio. Compares common frames and separately measures any additional tail; not real-time speaker playback or musical alignment."}
    FileAccess.open("res://../review/I_refinement/moonlight/mp3_clean/godot_pcm_check.json",FileAccess.WRITE).store_string(JSON.stringify(report,"  "))
    print("I_CLEAN_RECORDING_PCM_QA ",JSON.stringify(report));quit()
