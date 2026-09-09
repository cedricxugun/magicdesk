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
	if service.active_id!="B" and slot==3:return {"index":3,"key":"gauge","label":"状态仪表","gesture":"gauge","min":0.0,"max":1.0,"default":0.0,"readonly":true,"hint":"显示装置当前状态，无需点击"}
	if service.active_id!="B" and slot==4:return {"index":4,"key":"service","label":"拆装拨杆","gesture":"service","axis":"x","min":-1.0,"max":1.0,"default":0.0,"hint":"向左拖动拆解，向右拖动组装；松手回中"}
	for item in definitions.get(service.active_id,[]):
		if int(item.index)==slot:return item
	return {}

func held(slot:int)->bool:return index==slot

func consume(event:InputEvent)->bool:
	if service.current==null:return false
	if event is InputEventMouseMotion and index>=0:
		var point:Vector2=event.position
		var relative:Vector2=point-last_pointer
		var kind:String=active.gesture
		if kind in ["rotary","crank"]:
			var center:Vector2=service.host.camera.unproject_position(service.action_anchor(index))
			var a:=last_pointer-center;var b:=point-center
			var turn:=wrapf(b.angle()-a.angle(),-PI,PI) if minf(a.length(),b.length())>12 else (relative.x-relative.y)*.016
			drag_value+=turn/TAU*(1.0 if kind=="crank" else float(active.max)-float(active.min))
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
		drag_value=clampf(float(value),float(active.min),float(active.max))
		accepted=drag_value
		if active.has("steps"):
			var step:float=(float(active.max)-float(active.min))/maxf(1.0,float(active.steps)-1.0)
			accepted=roundf((drag_value-float(active.min))/step)*step+float(active.min)
	service.current.play.input(str(active.key),accepted,phase)
	changed=changed or phase=="change"
	for control in service.custom_controls:
		if int(control.index)!=index:continue
		control["input_value"]=accepted
		if accepted is Vector2:continue
		control.turn_target=float(accepted)*TAU if active.gesture=="crank" else inverse_lerp(float(active.min),float(active.max),float(accepted))*PI*1.6
		control.press=float(accepted) if active.gesture=="hold" else 1.0 if phase=="begin" else .25

func cancel()->void:
	if index>=0 and service.current!=null:
		if active.gesture in ["hold","pump","service"]:service.current.play.input(str(active.key),0.0,"cancel")
		elif active.gesture=="joystick":service.current.play.input(str(active.key),Vector2.ZERO,"cancel")
	index=-1;active={}
