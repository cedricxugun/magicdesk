extends Node
## Opt-in full-work audio transport. Estimated alignment is exposed, never called accepted.
signal movement_changed(movement:int)
signal work_finished
var player:AudioStreamPlayer
var tracks:Array=[]
var index:=0
var state:="stopped"
var total_length:=0.
var local_clock:=0.
var alignment_status:="estimated_requires_musical_review"
var response_envelopes:Array=[]
var response_interval:=.01
var manifest_sha256:=""
var envelope_sha256:=""
var chamber_envelopes:Array=[]
var chamber_interval:=.02
var chamber_envelope_sha256:=""
var offline_capture_clock:=false
const DEFAULT_VOLUME_DB:=0.
func setup(manifest_path:String)->void:
    assert(player==null)
    var manifest:Dictionary=JSON.parse_string(FileAccess.get_file_as_string(manifest_path))
    manifest_sha256=FileAccess.get_sha256(manifest_path)
    player=AudioStreamPlayer.new();player.volume_db=DEFAULT_VOLUME_DB;add_child(player);player.finished.connect(_on_track_finished)
    for row in manifest.movements:
        var stream:AudioStream=load(row.audio)
        assert(stream!=null and stream.get_length()>0.)
        assert(FileAccess.get_sha256(row.audio)==row.audio_sha256)
        var alignment:Dictionary=JSON.parse_string(FileAccess.get_file_as_string(row.alignment))
        assert(alignment.recording_sha256==row.audio_sha256)
        tracks.append({"stream":stream,"duration":stream.get_length(),"start":total_length,"warp":alignment.warp})
        total_length+=stream.get_length()
    assert(tracks.size()==3)
    if manifest.has("response_envelope"):
        envelope_sha256=str(manifest.response_envelope_sha256)
        assert(FileAccess.get_sha256(manifest.response_envelope)==manifest.response_envelope_sha256)
        var envelope:Dictionary=JSON.parse_string(FileAccess.get_file_as_string(manifest.response_envelope))
        response_interval=float(envelope.interval_seconds);assert(response_interval>0.)
        assert(envelope.movements.size()==tracks.size())
        for i in range(tracks.size()):
            var row:Dictionary=envelope.movements[i]
            assert(int(row.movement)==i+1 and row.audio_sha256==manifest.movements[i].audio_sha256)
            assert(absf(float(row.decoded_seconds)-float(tracks[i].duration))<.05)
            var values:=PackedFloat32Array(row["values"])
            assert(values.size()*response_interval>=float(tracks[i].duration))
            response_envelopes.append(values)
    if manifest.has("chamber_response_envelope"):
        chamber_envelope_sha256=str(manifest.chamber_response_envelope_sha256)
        assert(FileAccess.get_sha256(str(manifest.chamber_response_envelope))==chamber_envelope_sha256)
        var envelope:Dictionary=JSON.parse_string(FileAccess.get_file_as_string(str(manifest.chamber_response_envelope)))
        chamber_interval=float(envelope.interval_seconds);assert(chamber_interval>0. and envelope.movements.size()==tracks.size())
        for i in range(tracks.size()):
            var row:Dictionary=envelope.movements[i];assert(row.audio_sha256==manifest.movements[i].audio_sha256)
            var values:PackedVector3Array=[]
            for entry in row["values"]:values.append(Vector3(entry[0],entry[1],entry[2]))
            assert(values.size()*chamber_interval>=float(tracks[i].duration)-.05)
            chamber_envelopes.append(values)
func _process(_delta:float)->void:
    if state=="playing" and player.playing:
        var clock:=player.get_playback_position()
        if not offline_capture_clock:clock+=AudioServer.get_time_since_last_mix()-AudioServer.get_output_latency()
        local_clock=clampf(maxf(local_clock,clock),0.,float(tracks[index].duration))
func _start_track(next_index:int,offset:float,paused:bool)->void:
    player.stop();player.stream_paused=false;index=next_index;player.stream=tracks[index].stream;local_clock=offset
    player.play(offset);player.stream_paused=paused;state="paused" if paused else "playing";movement_changed.emit(index+1)
func play_complete()->void:
    assert(not tracks.is_empty());_start_track(0,0.,false)
func pause()->void:
    if state!="playing":return
    _process(0.);player.stream_paused=true;state="paused"
func resume()->void:
    if state!="paused":return
    player.stream_paused=false;state="playing"
func stop()->void:
    if player!=null:player.stop();player.stream_paused=false
    state="stopped";index=0;local_clock=0.
func seek_total(seconds:float)->void:
    var target:=clampf(seconds,0.,total_length);var paused:=state=="paused"
    if target>=total_length:
        player.stop();index=tracks.size()-1;local_clock=tracks[index].duration;state="ended";return
    for i in range(tracks.size()):
        if target<float(tracks[i].start)+float(tracks[i].duration):
            _start_track(i,target-float(tracks[i].start),paused);return
func _on_track_finished()->void:
    if state!="playing":return
    if index+1<tracks.size():_start_track(index+1,0.,false)
    else:
        local_clock=tracks[index].duration;state="ended";work_finished.emit()
func position_seconds()->float:
    return float(tracks[index].start)+local_clock if not tracks.is_empty() else 0.
func response_level()->float:
    if state!="playing" or response_envelopes.is_empty():return 0.
    var values:PackedFloat32Array=response_envelopes[index]
    var cursor:=clampf(local_clock/response_interval,0.,float(values.size()-1))
    var first:=int(floor(cursor));var second:=mini(first+1,values.size()-1)
    return clampf(lerpf(values[first],values[second],cursor-float(first)),0.,1.)
func score_quarter_estimate()->float:
    if tracks.is_empty():return 0.
    var warp:Array=tracks[index].warp
    if local_clock<=float(warp[0].seconds):return float(warp[0].quarter)
    var lo:=0;var hi:=warp.size()-1
    while lo+1<hi:
        var mid:=(lo+hi)/2
        if float(warp[mid].seconds)<=local_clock:lo=mid
        else:hi=mid
    var a:Dictionary=warp[lo];var b:Dictionary=warp[hi]
    var amount:=clampf((local_clock-float(a.seconds))/maxf(.000001,float(b.seconds)-float(a.seconds)),0.,1.)
    return lerpf(float(a.quarter),float(b.quarter),amount)
func chamber_bands()->Vector3:
    if state!="playing"or chamber_envelopes.is_empty():return Vector3.ZERO
    var values:PackedVector3Array=chamber_envelopes[index]
    var cursor:=clampf(local_clock/chamber_interval,0.,float(values.size()-1));var first:=int(floorf(cursor));var second:=mini(first+1,values.size()-1)
    return values[first].lerp(values[second],cursor-float(first))
func snapshot()->Dictionary:
    return {"state":state,"movement":index+1,"local_seconds":local_clock,"clock_mode":"decoded_movie_audio"if offline_capture_clock else "realtime_audio_compensated","total_seconds":position_seconds(),"duration":total_length,"score_quarter_estimate":score_quarter_estimate(),"alignment_status":alignment_status,"manifest_sha256":manifest_sha256,"envelope_sha256":envelope_sha256}
