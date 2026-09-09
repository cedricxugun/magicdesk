extends Node

var host: Node3D
var tcp := StreamPeerTCP.new()
var receive_buffer := PackedByteArray()
var sequence := 0
var ready_to_send := false
var transmitting := false
var last_mouse := Vector2.ZERO
var collection_capture:=false
var qa_directory:=""
var pending_reads:=0
var next_read_id:=0
var last_sent_id:=-1
var image_format:=Image.FORMAT_RGBA8
var async_enabled:=true
var format_reported:=false
var bridge_dead:=false
var profile_path:=""
var profile_start:=0
var legacy_alpha_crop:=false
var profile_rows:=PackedStringArray(["wall_seconds,id,openness,activation_wall,steam_time,gpu_ms,render_cpu_ms,readback_ms,image_ms,convert_ms,alpha_scan_ms,crop_ms,tcp_ms,publish_ms"])

func setup(owner_node: Node3D, port: int) -> void:
	host=owner_node
	for arg in OS.get_cmdline_user_args():
		if arg.begins_with("--collection-qa="):qa_directory=arg.trim_prefix("--collection-qa=")
		if arg=="--sync-readback":async_enabled=false
		if arg=="--legacy-alpha-crop":legacy_alpha_crop=true
		if arg.begins_with("--profile="):profile_path=arg.trim_prefix("--profile=")
	profile_start=Time.get_ticks_usec()
	if not profile_path.is_empty():RenderingServer.viewport_set_measure_render_time(host.render_view.get_viewport_rid(),true)
	tcp.big_endian=false
	tcp.connect_to_host("127.0.0.1",port)
	RenderingServer.frame_post_draw.connect(_send_frame)

func _process(_delta: float) -> void:
	tcp.poll()
	if tcp.get_status()==StreamPeerTCP.STATUS_ERROR:
		get_tree().quit()
		return
	if tcp.get_status()!=StreamPeerTCP.STATUS_CONNECTED:return
	ready_to_send=true
	var available:=tcp.get_available_bytes()
	if available>0:
		var result:=tcp.get_data(available)
		if result[0]==OK:receive_buffer.append_array(result[1])
	while true:
		var newline:=receive_buffer.find(10)
		if newline<0:break
		var line:=receive_buffer.slice(0,newline).get_string_from_utf8()
		receive_buffer=receive_buffer.slice(newline+1)
		var command=JSON.parse_string(line)
		if command is Dictionary:_command(command)

func _command(command: Dictionary) -> void:
	var kind:String=command.get("type","")
	if kind=="action":host.activate(int(command.index))
	elif kind=="move":
		var pt:=Vector2(float(command.x),float(command.y))
		var event:=InputEventMouseMotion.new();event.position=pt;event.relative=pt-last_mouse
		var consumed:bool=host.collection!=null and host.collection.consume_input(event)
		if not consumed and host.drag_kind==2:host.angle+=(pt.x-last_mouse.x)*.008
		last_mouse=pt;host.native_cursor=pt
	elif kind=="down":
		var pt:=Vector2(float(command.x),float(command.y))
		last_mouse=pt;host.native_cursor=pt
		var event:=InputEventMouseButton.new();event.button_index=MOUSE_BUTTON_LEFT;event.position=pt;event.pressed=true
		collection_capture=host.collection!=null and host.collection.consume_input(event)
		if collection_capture:host.pressed=-1;host.drag_kind=0;return
		host.pressed=host.hit_button(pt)
		print("HELIOS_POINTER_DOWN hit=",host.pressed," position=",pt)
		if host.pressed<0:host.drag_kind=2 if bool(command.get("upper",false)) else 1
	elif kind=="up":
		var pt:=Vector2(float(command.x),float(command.y))
		var event:=InputEventMouseButton.new();event.button_index=MOUSE_BUTTON_LEFT;event.position=pt;event.pressed=false
		var consumed:bool=host.collection!=null and host.collection.consume_input(event)
		if not consumed and not collection_capture and host.pressed>=0 and host.hit_button(pt)==host.pressed:host.activate(host.pressed)
		collection_capture=false
		host.pressed=-1;host.drag_kind=0;host.native_cursor=pt
	elif kind=="wheel" and host.collection!=null:
		var event:=InputEventMouseButton.new();event.position=Vector2(float(command.x),float(command.y));event.pressed=true
		event.button_index=MOUSE_BUTTON_WHEEL_UP if int(command.delta)>0 else MOUSE_BUTTON_WHEEL_DOWN
		event.factor=maxf(1.0,absf(float(command.delta))/120.0);event.shift_pressed=bool(command.get("shift",false))
		host.collection.consume_input(event)
	elif kind=="selector" and host.collection!=null:host.collection.toggle_selector()
	elif kind=="rotation":
		if host.collection!=null:host.collection.toggle_rotation()
		else:host.rotation_enabled=not host.rotation_enabled
	elif kind=="leave":host.native_cursor=Vector2(-10000,-10000)
	elif kind=="probe" and not qa_directory.is_empty():_write_probe()
	elif kind=="mute":host.muted=bool(command.value)
	elif kind=="reset":host.angle=0;host.rotation_enabled=true
	elif kind=="quit":host.begin_shutdown()

func _send_frame() -> void:
	if not ready_to_send or transmitting or bridge_dead:return
	if async_enabled:
		if pending_reads>=4:return
		var view:SubViewport=host.render_view
		var snapshot:=_capture_header(view.size)
		pending_reads+=1
		RenderingServer.call_on_render_thread(_request_gpu_copy.bind(view.get_texture().get_rid(),view.size,snapshot))
	else:
		var frame:Image=host.render_view.get_texture().get_image()
		_publish(frame,_capture_header(frame.get_size()))

func _capture_header(size:Vector2i)->Dictionary:
	var base_pt:Vector2=host.camera.unproject_position(Vector3(0,.62,1.0))
	var points:PackedInt32Array=[]
	for i in range(host.buttons.size()):
		var b:Dictionary=host.buttons[i]
		var anchor:Vector3=host.collection.action_anchor(i) if host.collection!=null and host.collection.current!=null and i in range(1,6) else b.cap.to_global(Vector3(0,.008,0))
		var pt:Vector2=host.camera.unproject_position(anchor)
		points.append(int(pt.x));points.append(int(pt.y))
	var snapshot:={"base_y":int(base_pt.y),"points":points,"fade":int(host.display_fade*255),"id":next_read_id,"size":size}
	snapshot["regions"]=host.collection.native_regions.duplicate() if host.collection!=null else []
	if not profile_path.is_empty():
		snapshot["requested_us"]=Time.get_ticks_usec()
		snapshot["openness"]=host.openness
		snapshot["activation_wall"]=host.activation_display_time
		snapshot["steam_time"]=host.effects.pressure.physics_time
		snapshot["gpu_ms"]=RenderingServer.viewport_get_measured_render_time_gpu(host.render_view.get_viewport_rid())
		snapshot["render_cpu_ms"]=RenderingServer.viewport_get_measured_render_time_cpu(host.render_view.get_viewport_rid())
	next_read_id+=1
	return snapshot

func _write_probe()->void:
	var info:Dictionary=host.collection.diagnostics() if host.collection!=null else {}
	info["angle"]=host.angle;info["power"]=host.power;info["drag_kind"]=host.drag_kind
	info["time_ms"]=Time.get_ticks_msec();info["buttons"]=_capture_header(host.render_view.size).points
	info["tooltip_visible"]=host.tooltip.visible;info["tooltip_rect"]=[host.tooltip.position.x,host.tooltip.position.y,host.tooltip.size.x,host.tooltip.size.y]
	if host.collection!=null:
		var band:Rect2=host.collection.control_band();info["control_band"]=[band.position.x,band.position.y,band.size.x,band.size.y]
	var targets:Array=[]
	if host.collection!=null:
		var service:Node3D=host.collection
		info["held"]=service.control_driver.index
		for label in service.selector_data.get("click_surfaces",[]):
			var node:Node3D=service.selector.find_child(label,true,false)
			if node==null:continue
			var points:Array[Vector2]=[];service._screen_points(node,points)
			if points.is_empty():continue
			var box:=Rect2(points[0],Vector2.ZERO)
			for point in points:box=box.expand(point)
			# Find an actually visible entry hit within the projected mesh; an AABB
			# midpoint may land in empty space for a curved cowl.
			for y in range(1,10):
				for x in range(1,10):
					var point:=box.position+box.size*Vector2(x/10.0,y/10.0)
					var hit:Dictionary=service._selector_ray(point)
					if not hit.is_empty() and hit.collider.has_meta("entry"):
						targets.append({"kind":"entry","x":point.x,"y":point.y});break
				if not targets.is_empty():break
			if not targets.is_empty():break
		if service.selector_amount>.95:
			for i in range(service.card_nodes.size()):
				var p:Vector2=host.camera.unproject_position(service.card_nodes[i].node.to_global(Vector3(0,.21,.02)))
				var hit:Dictionary=service._selector_ray(p)
				targets.append({"kind":"card","id":str(service.registry[(service.browse_start+i)%service.registry.size()].id),"slot":i,"x":p.x,"y":p.y,"hit":not hit.is_empty() and int(hit.collider.get_meta("card_slot",-1))==i})
		info["targets"]=targets
		info["region_count"]=service.native_regions.size()
		info["control_hits"]={}
		if service.current!=null:
			for i in range(1,6):
				var point:Vector2=host.camera.unproject_position(service.action_anchor(i))
				info.control_hits[str(i)]=service.hit_control(point)
	DirAccess.make_dir_recursive_absolute(qa_directory)
	FileAccess.open(qa_directory.path_join("collection_probe.json"),FileAccess.WRITE).store_string(JSON.stringify(info,"  "))

func _request_gpu_copy(texture:RID,size:Vector2i,snapshot:Dictionary)->void:
	var rd:=RenderingServer.get_rendering_device()
	var resource:=RenderingServer.texture_get_rd_texture(texture)
	if rd==null or not resource.is_valid():
		_readback_failed.call_deferred("Missing rendering device texture")
		return
	var format:=rd.texture_get_format(resource)
	var result_format:int=Image.FORMAT_RGBA8
	if format.format==RenderingDevice.DATA_FORMAT_R16G16B16A16_SFLOAT:result_format=Image.FORMAT_RGBAH
	elif format.format not in [RenderingDevice.DATA_FORMAT_R8G8B8A8_UNORM,RenderingDevice.DATA_FORMAT_R8G8B8A8_SRGB]:
		_readback_failed.call_deferred("Unsupported texture format "+str(format.format));return
	var error:=rd.texture_get_data_async(resource,0,_gpu_copy_ready.bind(size,result_format,snapshot))
	if error!=OK:_readback_failed.call_deferred("Readback returned "+str(error))

func _gpu_copy_ready(data:PackedByteArray,size:Vector2i,format:int,snapshot:Dictionary)->void:
	_receive_gpu_copy.call_deferred(data,size,format,snapshot)

func _readback_failed(reason:String)->void:
	pending_reads=maxi(0,pending_reads-1)
	if async_enabled:
		push_warning("Native async readback: "+reason+"; using synchronous fallback")
		async_enabled=false

func _receive_gpu_copy(data:PackedByteArray,size:Vector2i,format:int,snapshot:Dictionary)->void:
	pending_reads=maxi(0,pending_reads-1)
	if bridge_dead or not is_inside_tree() or int(snapshot.id)<=last_sent_id:return
	var expected:=size.x*size.y*(8 if format==Image.FORMAT_RGBAH else 4)
	if data.size()!=expected:
		_readback_failed("Unexpected copy size "+str(data.size()));return
	if not format_reported:
		format_reported=true;print("HELIOS_ASYNC_READBACK_READY ",size," bytes=",data.size())
	var received_us:=Time.get_ticks_usec()
	var frame:=Image.create_from_data(size.x,size.y,false,format,data)
	snapshot["readback_ms"]=(received_us-int(snapshot.get("requested_us",received_us)))/1000.0
	snapshot["image_ms"]=(Time.get_ticks_usec()-received_us)/1000.0
	_publish(frame,snapshot)

func _publish(frame:Image,snapshot:Dictionary)->void:
	transmitting=true
	var t0:=Time.get_ticks_usec()
	frame.convert(Image.FORMAT_RGBA8)
	var t1:=Time.get_ticks_usec()
	# Image.get_used_rect decodes 2.7 million Color values on the main thread.
	# The native receive worker can inspect alpha bytes directly while Godot renders.
	var used:Rect2i=frame.get_used_rect() if legacy_alpha_crop else Rect2i(Vector2i.ZERO,frame.get_size())
	var t2:=Time.get_ticks_usec()
	if used.size.x<4 or used.size.y<4:
		transmitting=false;return
	if legacy_alpha_crop:used=used.grow(2).intersection(Rect2i(Vector2i.ZERO,frame.get_size()))
	var pixels:PackedByteArray=frame.get_region(used).get_data() if legacy_alpha_crop else frame.get_data()
	var t3:=Time.get_ticks_usec()
	var header:=PackedByteArray();header.resize(96)
	var fields:Array[int]=[0x484C5333 if legacy_alpha_crop else 0x484C5335,used.size.x,used.size.y,used.position.x,used.position.y,frame.get_width(),frame.get_height(),int(snapshot.base_y),sequence,int(snapshot.fade)]
	for value in snapshot.points:fields.append(value)
	for i in range(fields.size()):header.encode_s32(i*4,fields[i])
	var err:=tcp.put_data(header)
	if err==OK and not legacy_alpha_crop:
		var region_data:=PackedByteArray();var regions:Array=snapshot.get("regions",[])
		region_data.resize(4+regions.size()*16);region_data.encode_s32(0,regions.size())
		for i in range(regions.size()):
			var r:Rect2i=regions[i]
			for j in range(4):region_data.encode_s32(4+i*16+j*4,[r.position.x,r.position.y,r.size.x,r.size.y][j])
		err=tcp.put_data(region_data)
	if err==OK:err=tcp.put_data(pixels)
	var t4:=Time.get_ticks_usec()
	if not profile_path.is_empty() and profile_rows.size()<12000:
		profile_rows.append("%.5f,%d,%.5f,%.5f,%.5f,%.3f,%.3f,%.3f,%.3f,%.3f,%.3f,%.3f,%.3f,%.3f"%[(t0-profile_start)/1000000.0,int(snapshot.id),float(snapshot.openness),float(snapshot.activation_wall),float(snapshot.steam_time),float(snapshot.gpu_ms),float(snapshot.render_cpu_ms),float(snapshot.get("readback_ms",0)),float(snapshot.get("image_ms",0)),(t1-t0)/1000.0,(t2-t1)/1000.0,(t3-t2)/1000.0,(t4-t3)/1000.0,(t4-t0)/1000.0])
	if err!=OK:
		push_error("HELIOS_TRANSPORT_SEND_FAILED code="+str(err)+" sequence="+str(sequence))
		get_tree().quit()
	sequence+=1
	last_sent_id=int(snapshot.id)
	transmitting=false

func _exit_tree()->void:
	bridge_dead=true
	if RenderingServer.frame_post_draw.is_connected(_send_frame):RenderingServer.frame_post_draw.disconnect(_send_frame)
	if not profile_path.is_empty():
		DirAccess.make_dir_recursive_absolute(profile_path)
		FileAccess.open(profile_path.path_join("bridge_trace.csv"),FileAccess.WRITE).store_string("\n".join(profile_rows))
