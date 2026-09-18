extends Node
## Opt-in, read-only native review telemetry. Never drives input or playback.
var host:Node3D
var output:FileAccess
var started:=0
var previous:=0
var flush_age:=0.0
func setup(owner:Node3D,path:String)->void:
	host=owner;DirAccess.make_dir_recursive_absolute(path.get_base_dir());output=FileAccess.open(path,FileAccess.WRITE)
	assert(output!=null,"Cannot open review profile")
	output.store_line("wall_s,interval_ms,delta_ms,gpu_ms,render_cpu_ms,model,collection_state,curiosity,stage,print,aperture,energy")
	started=Time.get_ticks_usec();previous=started
	RenderingServer.viewport_set_measure_render_time(host.render_view.get_viewport_rid(),true)
	var info:={"executable":OS.get_executable_path(),"engine":Engine.get_version_info().string,"device":RenderingServer.get_video_adapter_name(),"os":OS.get_name(),"setup_at_ms":started/1000.0,"movie_writer":OS.get_cmdline_args().has("--write-movie"),"scope":"Wall frame intervals and measured render viewport timings after scene setup. Zero GPU timings may mean unavailable. Capture/IO and OS scheduling can affect intervals."}
	FileAccess.open(path+".json",FileAccess.WRITE).store_string(JSON.stringify(info,"  "))
func _process(delta:float)->void:
	if output==null:return
	var now:=Time.get_ticks_usec();var interval:float=(now-previous)/1000.0;previous=now
	var id:="B";var state:="";var index:=-1;var stage:="";var amount:=0.;var aperture:=0.;var energy:=0.
	if host.collection:
		var service:Node3D=host.collection;id=service.active_id;state=service.state
		if service.current and service.current.play.g_instrument:
			var player:RefCounted=service.current.play.g_instrument;index=player.loaded_index;stage=player.stage;amount=player.print_amount;energy=player.action_energy
			if player.get("butterfly_drive"):aperture=player.butterfly_drive.aperture
	var viewport:RID=host.render_view.get_viewport_rid()
	output.store_line("%.6f,%.4f,%.4f,%.4f,%.4f,%s,%s,%d,%s,%.5f,%.5f,%.5f"%[(now-started)/1000000.0,interval,delta*1000.,RenderingServer.viewport_get_measured_render_time_gpu(viewport),RenderingServer.viewport_get_measured_render_time_cpu(viewport),id,state,index,stage,amount,aperture,energy])
	flush_age+=delta
	if flush_age>=2.:output.flush();flush_age=0.
func _exit_tree()->void:
	if output:output.flush();output=null
