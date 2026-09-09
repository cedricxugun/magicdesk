extends RefCounted
## Pointer capture and continuous control intent. Model responses are owned by
## module/play_state, so a hold or drag never masquerades as repeated click events.

var service:Node3D
var definitions:Dictionary={}
var active:Dictionary={}
var index:=-1
var last_pointer:=Vector2.ZERO
var start_pointer:=Vector2.ZERO
var origin_value:Variant=0.0
var drag_value:=0.0
var changed:=false

func setup(owner:Node3D)->void:
	service=owner
	definitions=JSON.parse_string(FileAccess.get_file_as_string("res://assets/collection/control_profiles.json")).models

func profile(slot:int)->Dictionary:
	if service.active_id=="G" and service.current and service.current.data.has("record_player") and slot==1:return {"index":1,"key":"leaf","label":"选片","gesture":"rotary","min":0.0,"max":5.0,"default":0.0,"steps":6,"cyclic":true,"hint":"单击选下一张，滚轮双向选片；机身编号与选片轮对应。"}
	if service.active_id=="G" and service.current and service.current.data.has("record_player") and slot==3:return {"index":3,"key":"spin","label":"唱片慢转 / 停转","gesture":"detent","axis":"x","min":0.0,"max":1.0,"default":1.0,"steps":2,"tap_toggle":true,"hint":"单击切换慢转与停转；唱片和藏品同转，约一分钟一圈。"}
	if service.active_id=="G" and service.current and service.current.data.has("g_archive"):
		var definition:Dictionary=service.current.data.g_archive.contents[service.current.play.g_instrument.selected]
		if slot==2:return {"index":2,"key":"fold","label":definition.parameter,"gesture":"slider","axis":"x","min":0.0,"max":1.0,"default":.5,"hint":"拖动或滚轮："+str(definition.parameter)+"。效果直接作用于当前藏品。"}
		if slot==5:return {"index":5,"key":"imprint","label":definition.action,"gesture":"hold","min":0.0,"max":1.0,"default":0.0,"hint":"按住："+str(definition.action)+"；松手后平缓恢复。"}
		if slot==3:return {"index":3,"key":"gauge","label":"读取 / 动作状态","gesture":"gauge","min":0.0,"max":1.0,"default":0.0,"readonly":true,"hint":"读盘时显示进度，播放时响应藏品的动作强度。"}
	if service.active_id=="G" and slot==3:return {"index":3,"key":"gauge","label":"光路对准表","gesture":"gauge","min":0.0,"max":1.0,"default":0.0,"readonly":true,"hint":"向右表示三页光孔已对准；折角回到中央可对准，再按住写入。"}
	if service.active_id=="F" and slot==3:return {"index":3,"key":"gauge","label":"合衡表","gesture":"gauge","min":0.0,"max":1.0,"default":0.0,"readonly":true,"hint":"指针越靠左，平衡越稳定；稳定后自动校准。"}
	if service.active_id!="B" and slot==3:return {"index":3,"key":"gauge","label":"状态仪表","gesture":"gauge","min":0.0,"max":1.0,"default":0.0,"readonly":true,"hint":"显示装置当前状态，无需点击"}
	if service.active_id!="B" and slot==4:return {"index":4,"key":"service","label":"拆装拨杆","gesture":"service","axis":"x","min":-1.0,"max":1.0,"default":0.0,"hint":"向左拖动拆解，向右拖动组装；松手回中"}
	for item in definitions.get(service.active_id,[]):
		if int(item.index)==slot:return item
	return {}

func held(slot:int)->bool:return index==slot

func consume(event:InputEvent)->bool:
	if service.current==null:return false
	if event is InputEventMouseButton and event.pressed and event.button_index in [MOUSE_BUTTON_WHEEL_UP,MOUSE_BUTTON_WHEEL_DOWN] and index<0 and service.state=="idle" and service.selector_amount<.01:
		var slot:int=service.hit_control(event.position)
		var definition:=profile(slot)
		if not definition.is_empty() and definition.get("gesture","") in ["rotary","crank","slider","detent"]:
			active=definition;index=slot
			var before:float=service.current.play.number(str(active.key))
			var amount:float=(float(active.max)-float(active.min))*.045
			if active.gesture=="crank":amount=1.0/12.0
			if active.has("steps"):amount=(float(active.max)-float(active.min))/maxf(1.0,float(active.steps)-1.0)
			elif event.shift_pressed:amount*=.2
			amount*=maxf(1.0,event.factor)*(1 if event.button_index==MOUSE_BUTTON_WHEEL_UP else -1)
			service.current.play.input(str(active.key),before,"begin")
			_set_value(before+amount,"change")
			service.current.play.input(str(active.key),service.current.play.value(str(active.key)),"release")
			service.host.tooltip.hide();service.help_since_ms=Time.get_ticks_msec();service.host.sound("click",1.08)
			index=-1;active={};return true
	if event is InputEventMouseMotion and index>=0:
		var point:Vector2=event.position
		var relative:Vector2=point-last_pointer
		var kind:String=active.gesture
		if kind in ["rotary","crank"]:
			# A screen-space drag remains comfortable when the 3D dial is seen
			# obliquely. No tiny circular gesture or perspective correction.
			var movement:float=relative.x-relative.y*.35
			drag_value+=movement/180.0*(1.0 if kind=="crank" else float(active.max)-float(active.min))
			_set_value(drag_value,"change")
		elif kind in ["slider","detent","pump","service"]:
			var movement:float=relative.x if active.get("axis","y")=="x" else -relative.y
			drag_value+=movement/130.0*(float(active.max)-float(active.min))
			_set_value(drag_value,"change")
		elif kind=="joystick":
			var v:Vector2=(point-start_pointer)/80.0
			_set_value(Vector2(clampf(v.x,-1,1),clampf(-v.y,-1,1)),"change")
		last_pointer=point;return true
	if not event is InputEventMouseButton or event.button_index!=MOUSE_BUTTON_LEFT:return false
	if not event.pressed and index>=0:
		if active.gesture=="service" and service.current.data.has("record_player") and event.position.distance_to(start_pointer)<6 and not changed:
			_set_value(-1.0 if service.control_local_point(index,event.position).x<0 else 1.0,"change")
		if active.get("tap_toggle",false) and event.position.distance_to(start_pointer)<6 and not changed:_set_value(1.0-float(origin_value),"change")
		if service.active_id=="G" and active.key=="leaf" and event.position.distance_to(start_pointer)<6 and not changed:
			_set_value(float(posmod(int(roundf(float(origin_value)))+1,6)),"change")
		if active.gesture in ["hold","pump","service"]:_set_value(0.0,"release")
		elif active.gesture=="joystick":_set_value(Vector2.ZERO,"release")
		else:_set_value(service.current.play.value(str(active.key)),"release")
		index=-1;active={};return true
	if event.pressed and service.state=="idle" and service.selector_amount<.01 and not service.selector_wait:
		var slot:int=service.hit_control(event.position)
		var definition:=profile(slot)
		if definition.is_empty():return false
		if definition.get("readonly",false):return true
		active=definition;index=slot;start_pointer=event.position;last_pointer=event.position;changed=false
		service.host.tooltip.hide()
		origin_value=service.current.play.value(str(active.key))
		drag_value=float(origin_value) if origin_value is float or origin_value is int else 0.0
		_set_value(1.0 if active.gesture=="hold" else origin_value,"begin")
		service.host.sound("click",.85)
		return true
	return false

func _set_value(value:Variant,phase:String)->void:
	if service.current==null:return
	var accepted:Variant=value
	if not value is Vector2:
		drag_value=wrapf(float(value),float(active.min),float(active.max)+1.0) if active.get("cyclic",false) else clampf(float(value),float(active.min),float(active.max))
		accepted=drag_value
		if active.has("steps"):
			var step:float=(float(active.max)-float(active.min))/maxf(1.0,float(active.steps)-1.0)
			accepted=roundf((drag_value-float(active.min))/step)*step+float(active.min)
			if active.get("cyclic",false):accepted=float(posmod(roundi(accepted),int(active.steps)))
	service.current.play.input(str(active.key),accepted,phase)
	changed=changed or phase=="change"
	for control in service.custom_controls:
		if int(control.index)!=index:continue
		control["input_value"]=accepted
		if service.current.data.has("record_player") and active.gesture=="service" and absf(float(accepted))>.5:
			control.rocker_target=float(accepted);control.rocker_hold=.20
		if accepted is Vector2:continue
		control.turn_target=float(accepted)*TAU if active.gesture=="crank" else inverse_lerp(float(active.min),float(active.max),float(accepted))*PI*1.6
		if active.get("cyclic",false):control.turn_target=control.turn+angle_difference(control.turn,float(accepted)*TAU/float(active.steps))
		if service.active_id=="F" and active.gesture=="rotary":control.turn_target-=PI*.8
		control.press=float(accepted) if active.gesture=="hold" else 1.0 if phase=="begin" else .25

func cancel()->void:
	if index>=0 and service.current!=null:
		if active.gesture in ["hold","pump","service"]:service.current.play.input(str(active.key),0.0,"cancel")
		elif active.gesture=="joystick":service.current.play.input(str(active.key),Vector2.ZERO,"cancel")
	index=-1;active={}
