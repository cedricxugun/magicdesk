extends Node3D
## Authored 3D carrier/mask and offline audio cues, timed by the mechanical rig.
var mouth:Node3D
var packets:Array=[]
var carrier:PackedScene
var crest:Texture2D
var voices:Array[AudioStreamPlayer3D]=[]
var indicators:Array=[]
var light:OmniLight3D
var receipt:Dictionary={}
var _sounds_enabled:=true
var _music_mode:=false
var _hearing_scale:=1.
var preserve_attachments_on_exit:=false
func set_music_mode(active:bool)->void:
    _music_mode=active
    if active:
        for packet in packets:packet.cancelled=true
func setup(asset:Node3D,sounds_enabled:bool=true,hearing_scale:float=1.)->void:
    mouth=asset.find_child("IAM_Mouth",true,false);assert(mouth!=null)
    carrier=load("res://assets/collection/art/I/echo_r2/wavefront.glb")
    crest=load("res://assets/collection/art/I/echo_r2/crest_mask.png")
    _sounds_enabled=sounds_enabled
    _hearing_scale=maxf(.01,hearing_scale)
    for name in ["IAM_TineEnamelAxial_0","IAM_TineEnamelAxial_1","IAM_TineEnamelAxial_2"]:
        var node:=asset.find_child(name,true,false) as MeshInstance3D
        var material:=node.get_active_material(0).duplicate() as BaseMaterial3D
        material.emission_enabled=true;material.emission=Color(1.,.32,.08);material.emission_energy_multiplier=0.
        node.set_surface_override_material(0,material);indicators.append(material)
    light=OmniLight3D.new();mouth.add_child(light);light.position=Vector3(0,-.23,0);light.omni_range=.55;light.omni_attenuation=2.;light.light_energy=0.;light.shadow_enabled=true
func play_cue(kind:String,gain:float)->void:
    if not _sounds_enabled or _music_mode:return
    var player:=AudioStreamPlayer3D.new();mouth.add_child(player);player.position=Vector3(0,-.18,0)
    player.stream=load("res://assets/collection/art/I/echo_r2/"+("send.wav" if kind=="outgoing" else "return.wav"))
    player.unit_size=3.*_hearing_scale;player.max_distance=8.*_hearing_scale;player.volume_db=linear_to_db(maxf(.0001,gain)) - 4.
    player.finished.connect(func():voices.erase(player);player.queue_free())
    voices.append(player);player.play()
func update(delta:float,rig:RefCounted,events:Array)->void:
    var time:float=rig.acoustics.clock
    for event in events:
        if _music_mode:continue
        if event.kind=="outgoing":
            var schedule:Array=rig.acoustics.return_schedule();assert(not schedule.is_empty())
            var echo:Dictionary=schedule.back();var node:Node3D=carrier.instantiate();mouth.add_child(node)
            var material:=ShaderMaterial.new();material.shader=load("res://collection/i_echo_wavefront.gdshader");material.set_shader_parameter("crest",crest)
            for mesh in node.find_children("*","MeshInstance3D",true,false):mesh.material_override=material;mesh.cast_shadow=GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
            packets.append({"node":node,"material":material,"start":float(event.time),"end":float(echo.due),"gain":float(event.gain),"return_gain":float(echo.gain),"cancelled":false,"fade":1.})
        play_cue(str(event.kind),float(event.gain))
    if not rig.wants_open or _music_mode:
        for packet in packets:packet.cancelled=true
        for voice in voices:voice.volume_db=move_toward(voice.volume_db,-60.,delta*140.)
    var visible_amount:=0.;var positions:Array=[]
    for packet in packets.duplicate():
        var duration:float=packet.end-packet.start;var age:float=time-packet.start
        if packet.cancelled:packet.fade=move_toward(float(packet.fade),0.,delta/.20)
        if age>duration+.18 or packet.fade<=0.:
            packet.node.queue_free();packets.erase(packet);continue
        var p:=clampf(age/duration,0.,1.);var outward:=p<.45
        var travel:=smoothstep(0.,.45,p) if outward else 1.-smoothstep(.45,1.,p)
        var intensity:float=lerpf(packet.gain,packet.return_gain,smoothstep(.38,.6,p))
        var envelope:float=smoothstep(0.,.09,age)*(1.-smoothstep(duration,duration+.18,age))
        var strength:float=intensity*envelope*float(packet.fade)
        packet.node.position=Vector3(0.,-.18-.42*travel,0.)
        packet.node.scale=Vector3.ONE*(.82+.12*travel)
        var tint:=Color(1.,.78,.48).lerp(Color(.71,.86,1.),smoothstep(.38,.62,p))
        packet.material.set_shader_parameter("tint",Vector3(tint.r,tint.g,tint.b));packet.material.set_shader_parameter("gain",strength*1.15)
        visible_amount=maxf(visible_amount,strength);positions.append({"p":p,"depth":packet.node.position.y,"strength":strength,"cancelled":packet.cancelled})
    var pulse:float=exp(-rig.event_age*9.) if rig.event_age<.7 else 0.
    for index in range(indicators.size()):
        var charge:float=rig.acoustics.compression*.08 if rig.wants_open else 0.
        var order:int=2-index if rig.last_event=="return" else index
        var age:float=rig.event_age-float(order)*.045
        var tip_pulse:float=exp(-age*9.) if age>=0. and age<.7 else 0.
        indicators[index].emission_energy_multiplier=charge+tip_pulse*.35
    light.light_color=Color(.65,.82,1.) if rig.last_event=="return" else Color(1.,.67,.35)
    light.light_energy=pulse*.035
    receipt={"live_packets":packets.size(),"positions":positions,"active_voices":voices.size(),"tip_pulse":pulse,"light_energy":light.light_energy}
func _exit_tree()->void:
    if preserve_attachments_on_exit:return
    for packet in packets:
        if is_instance_valid(packet.node):packet.node.queue_free()
    for voice in voices:
        if is_instance_valid(voice):voice.queue_free()
    if is_instance_valid(light):light.queue_free()
