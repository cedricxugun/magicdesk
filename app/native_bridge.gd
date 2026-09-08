extends Node

var host: Node3D
var tcp := StreamPeerTCP.new()
var receive_buffer := PackedByteArray()
var sequence := 0
var ready_to_send := false
var transmitting := false
var last_mouse := Vector2.ZERO
var pending_reads:=0
var next_read_id:=0
var last_sent_id:=-1
var image_format:=Image.FORMAT_RGBA8
var async_enabled:=true
var format_reported:=false
var bridge_dead:=false

func setup(owner_node: Node3D, port: int) -> void:
	host=owner_node
	for arg in OS.get_cmdline_user_args():
		if arg=="--sync-readback":async_enabled=false
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
		if host.drag_kind==2:host.angle+=(pt.x-last_mouse.x)*.008
		last_mouse=pt;host.native_cursor=pt
	elif kind=="down":
		var pt:=Vector2(float(command.x),float(command.y))
		last_mouse=pt;host.native_cursor=pt
		host.pressed=host.hit_button(pt)
		if host.pressed<0:host.drag_kind=2 if bool(command.get("upper",false)) else 1
	elif kind=="up":
		var pt:=Vector2(float(command.x),float(command.y))
		if host.pressed>=0 and host.hit_button(pt)==host.pressed:host.activate(host.pressed)
		host.pressed=-1;host.drag_kind=0;host.native_cursor=pt
	elif kind=="leave":host.native_cursor=Vector2(-10000,-10000)
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
	for b in host.buttons:
		var pt:Vector2=host.camera.unproject_position(b.mount.global_position)
		points.append(int(pt.x));points.append(int(pt.y))
	var snapshot:={"base_y":int(base_pt.y),"points":points,"fade":int(host.display_fade*255),"id":next_read_id,"size":size}
	next_read_id+=1
	return snapshot

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
	var frame:=Image.create_from_data(size.x,size.y,false,format,data)
	_publish(frame,snapshot)

func _publish(frame:Image,snapshot:Dictionary)->void:
	transmitting=true
	frame.convert(Image.FORMAT_RGBA8)
	var used: Rect2i=frame.get_used_rect()
	if used.size.x<4 or used.size.y<4:
		transmitting=false;return
	used=used.grow(2).intersection(Rect2i(Vector2i.ZERO,frame.get_size()))
	var pixels: PackedByteArray=frame.get_region(used).get_data()
	var header:=PackedByteArray();header.resize(96)
	var fields:Array[int]=[0x484C5333,used.size.x,used.size.y,used.position.x,used.position.y,frame.get_width(),frame.get_height(),int(snapshot.base_y),sequence,int(snapshot.fade)]
	for value in snapshot.points:fields.append(value)
	for i in range(fields.size()):header.encode_s32(i*4,fields[i])
	var err:=tcp.put_data(header)
	if err==OK:err=tcp.put_data(pixels)
	if err!=OK:get_tree().quit()
	sequence+=1
	last_sent_id=int(snapshot.id)
	transmitting=false

func _exit_tree()->void:
	bridge_dead=true
	if RenderingServer.frame_post_draw.is_connected(_send_frame):RenderingServer.frame_post_draw.disconnect(_send_frame)
