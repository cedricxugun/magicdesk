extends SceneTree
## Current physical cartridge + real transport/score and directional-head checks.
## Does not claim full-body art, continuous playback alignment or speaker quality.
var rig:RefCounted
var music:Node
var asset:Node3D
var spec:Dictionary
var output:String
var report:Dictionary={"checks":[]}
func _initialize()->void:run.call_deferred()
func ensure(value:bool,message:String)->bool:
    report.checks.append({"check":message,"passed":value})
    if not value:
        report["passed"]=false
        FileAccess.open(output,FileAccess.WRITE).store_string(JSON.stringify(report,"  "))
        push_error(message);quit(1)
    return value
func from_blender(v:Array)->Vector3:return Vector3(float(v[0]),float(v[2]),-float(v[1]))
func advance(frames:int)->void:
    for frame in range(frames):
        rig.tick(1./60.);music.tick(1./60.)
        await process_frame
func run()->void:
    var path:="res://../review/I_refinement/nautilus_reset_r82/music_interface_r1/optical_core_build_r2.json"
    output="res://../review/I_refinement/nautilus_reset_r82/music_interface_r1/runtime_qa_r2.json"
    for a in OS.get_cmdline_user_args():
        if a.begins_with("--spec="):path=a.trim_prefix("--spec=")
        if a.begins_with("--out="):output=a.trim_prefix("--out=")
    spec=JSON.parse_string(FileAccess.get_file_as_string(path))
    report["source_sha256"]=spec.source_sha256;report["component_sha256"]=spec.component_sha256
    asset=load("res://"+str(spec.component).trim_prefix("app/")).instantiate();root.add_child(asset)
    rig=load("res://collection/i_mouth_response_rig.gd").new()
    rig.bind(asset,spec,JSON.parse_string(FileAccess.get_file_as_string(spec.aperture_profile)))
    music=load("res://collection/i_moonlight_controller.gd").new();root.add_child(music);music.setup(asset,spec,rig)
    music.toggle();await advance(260)
    if not ensure(music.transport.state=="playing" and music.staff.status.ready,"Ready score before playback"):return
    if not ensure(music.staff.layout.optical_backing==0.,"No opaque score backing"):return
    var camera:=Camera3D.new();root.add_child(camera);root.size=Vector2i(1000,900)
    var layout:Dictionary=music.staff.layout
    var mouth:Node3D=asset.find_child(str(layout.mouth_node),true,false)
    var normal:=from_blender(layout.reading_normal_blender) if layout.has("reading_normal_blender") else Vector3(0,-1,0)
    var up:=from_blender(layout.reveal_axis_blender) if layout.has("reveal_axis_blender") else Vector3.FORWARD
    normal=(mouth.global_basis*normal).normalized();up=(mouth.global_basis*up).normalized()
    var focus:Vector3=mouth.to_global(from_blender(layout.scanner.focus))
    camera.position=focus+normal*3.;camera.look_at(focus,up);camera.current=true
    if not ensure(music.staff.pointer_target(camera,camera.unproject_position(focus))=="staff","Authored reading-plane pointer projection"):return
    camera.position=focus-normal*3.;camera.look_at(focus,up)
    if not ensure(music.staff.pointer_target(camera,camera.unproject_position(focus)).is_empty(),"Rear-side optical hit rejection"):return
    camera.queue_free()
    var witnesses:Array=[]
    if layout.get("oriented_reveal",false):
        for stroke in [-rig.suspension.max_stroke,0.,rig.suspension.max_stroke]:
            rig.suspension.set_displacement(stroke)
            music.staff.set_music_response(.5,true,true)
            for i in range(music.staff.scan_tips.size()):
                var binding:Dictionary=music.staff.scan_tips[i]
                var lens:MeshInstance3D=binding.finish_node
                var arrays:Array=lens.mesh.surface_get_arrays(0)
                var vertices:PackedVector3Array=arrays[Mesh.ARRAY_VERTEX]
                var nearest:=INF
                for v in vertices:nearest=minf(nearest,v.distance_to(binding.local_point))
                var actual_lens:Vector3=lens.to_global(binding.local_point)
                var head:Node3D=binding.head
                var axis:Vector3=(head.global_basis*binding.head_forward).normalized()
                var aim:=axis.dot((focus-head.global_position).normalized())
                var ray:MeshInstance3D=music.staff.optics.find_child(layout.scanner.tips[i].ray,true,false)
                var arr:Array=ray.mesh.surface_get_arrays(0)
                var uv:PackedVector2Array=arr[Mesh.ARRAY_TEX_UV]
                var positions:PackedVector3Array=arr[Mesh.ARRAY_VERTEX]
                var start:=Vector3.ZERO
                var count:=0
                for k in range(uv.size()):
                    if uv[k].y>.999:
                        start+=positions[k];count+=1
                if not ensure(count==2,"Two authored start-edge vertices per reading beam"):return
                start/=float(count)
                var delta:Vector3=music.staff.scan_materials[i+1].get_shader_parameter("tip_delta")
                var endpoint:Vector3=ray.to_global(start+delta)
                var error:=endpoint.distance_to(actual_lens)
                witnesses.append({"stroke":stroke,"lens":str(lens.name),"surface_vertex_error":nearest,"axis_dot_focus":aim,"beam_lens_error":error,"actual_lens_world":[actual_lens.x,actual_lens.y,actual_lens.z]})
                if not ensure(nearest<.000002 and aim>.99999 and error<.00001,"Beam follows real lens surface under diaphragm motion"):return
        report["head_witnesses"]=witnesses
        for i in range(3):
            var first:Array=witnesses[i].actual_lens_world
            var last:Array=witnesses[i+6].actual_lens_world
            var travel:=Vector3(first[0],first[1],first[2]).distance_to(Vector3(last[0],last[1],last[2]))
            if not ensure(travel>.009,"Reading lens actually moves with the driven diaphragm"):return
    rig.suspension.set_displacement(0.)
    music.toggle();music.tick(0.)
    var paused:float=music.transport.position_seconds()
    var quarter:float=music.staff.status.quarter_estimate
    await create_timer(.20).timeout;music.tick(.1)
    if not ensure(music.transport.state=="paused" and absf(music.transport.position_seconds()-paused)<.0001 and absf(music.staff.status.quarter_estimate-quarter)<.0001,"Pause freezes audio clock and real score position"):return
    var samples:Array=[]
    for seconds in [20.,350.,490.,920.]:
        music.seek(seconds);await advance(20)
        if not ensure(music.transport.state=="paused" and absf(music.transport.position_seconds()-seconds)<.002 and music.staff.status.ready and music.staff.status.movement==music.transport.index+1,"Paused seek across complete work at "+str(seconds)):return
        samples.append(music.status.duplicate(true))
    report["movement_samples"]=samples
    music.toggle();await advance(10)
    if not ensure(music.transport.state=="playing","Resume from paused seek"):return
    music.stop(true);await advance(360)
    if not ensure(music.transport.state=="stopped" and rig.stage=="closed" and rig.suspension.settled(),"Fade, remove projection, settle and close throat"):return
    report["passed"]=true
    report["scope"]="Actual new or legacy core, six foil runtime bindings, complete-work transport/seek/pause/close, transparent score and real reading-lens/ribbon geometry under pressure extremes. Dummy audio; no speaker audition, whole-body fit, final art or exact musical alignment proof."
    FileAccess.open(output,FileAccess.WRITE).store_string(JSON.stringify(report,"  "))
    print("R83_MUSIC_RUNTIME_QA true")
    music.transport.stop();music.queue_free();asset.queue_free()
    await process_frame;await process_frame;quit()
