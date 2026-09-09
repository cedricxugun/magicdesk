extends Control
## Compact, labelled operation plaque below the real pedestal. Native mouse
## events are routed explicitly so they also work in the transparent desktop EXE.
var service:Node3D
var panel:=Rect2()
var entries:Array=[]
var held:=""
var pressed:=""
var point:=Vector2(-10000,-10000)
var font:Font
var title_font:Font
var feedback:=""
var feedback_time:=0.0
var styles:Dictionary={}
var layout_ready:=false
const NAMES:=["左前","左中","左后","右前","右中","右后"]
const TITLES:=["钟塔","机械蝶","帆船","花园","星轨仪","阶梯"]

func is_archive()->bool:return service.current!=null and service.current.data.has("g_archive")
func is_record_player()->bool:return service.current!=null and service.current.data.has("record_player")

func setup(owner:Node3D)->void:
	service=owner;mouse_filter=Control.MOUSE_FILTER_IGNORE
	font=service.host.tooltip.get_theme_font("font");title_font=font
	set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT);hide()

func available()->bool:
	return not is_record_player() and service.active_id=="G" and service.current!=null and service.current.play.g_instrument!=null and service.state=="idle" and service.selector_amount<.01 and not service.closing

func layout()->void:
	if not layout_ready:
		var points:Array[Vector2]=[];service._screen_points(service.base_display,points)
		var base:Rect2=service.control_band()
		for p in points:base=base.expand(p)
		var width:=572.0 if is_record_player() else 660.0;var height:=187.0
		panel=Rect2(Vector2(clampf(base.get_center().x-width*.5,10,service.host.canonical_size.x-width-10),minf(base.end.y+10,service.host.canonical_size.y-height-8)),Vector2(width,height));layout_ready=true
	entries.clear()
	var rotating:bool=service.current.play.g_instrument.spin_enabled if is_record_player() else service.host.rotation_enabled
	add_entry("rotate",Rect2(panel.position+Vector2(panel.size.x-214,9),Vector2(118,29)),("停止慢转" if rotating else "开始慢转") if is_record_player() else ("暂停旋转" if rotating else "旋转展示"))
	add_entry("front",Rect2(panel.position+Vector2(panel.size.x-88,9),Vector2(78,29)),"回正面")
	var stride:float=93 if is_record_player() else 107;var button_width:float=stride-8
	for i in range(6):
		add_entry("page_"+str(i),Rect2(panel.position+Vector2(10+i*stride,47),Vector2(button_width,32)),str(i+1)+" · "+(TITLES[i] if is_archive() else NAMES[i]))
	var expanded:bool=service.current.open_target>.5 and service.current.explode_target<.01
	var labels:Array=["合上书匣" if expanded else "展开书匣","对准本组","按住写入","拆解","组装","退出"]
	var ids:Array=["open","align","write","explode","assemble","exit"]
	if is_archive():
		var item:Dictionary=service.current.data.g_archive.contents[service.current.play.g_instrument.selected]
		labels=["收回休眠" if expanded else "展开播放","继续播放" if service.current.play.g_instrument.playback_paused else "暂停播放","按住"+str(item.action),"拆解","组装","退出"]
		ids=["open","play","write","explode","assemble","exit"]
		add_entry("parameter",Rect2(panel.position+Vector2(10,86),Vector2(350,29)),str(item.parameter))
	for i in range(6):add_entry(ids[i],Rect2(panel.position+Vector2(10+i*stride,123),Vector2(button_width,34)),labels[i])

func add_entry(id:String,rect:Rect2,label:String)->void:entries.append({"id":id,"rect":rect,"label":label})

func hit(p:Vector2)->String:
	if not visible:return ""
	for item in entries:
		if item.rect.has_point(p):return item.id
	return ""

func notify(text:String)->void:feedback=text;feedback_time=2.5

func cancel()->void:
	if held=="write" and service.current:service.current.play.input("imprint",0.0,"cancel")
	held="";pressed="";queue_redraw()

func consume(event:InputEvent)->bool:
	if not available():
		if not held.is_empty():cancel()
		return false
	if event is InputEventMouseMotion:
		point=event.position
		if held=="parameter":set_parameter(point.x,"change");return true
		return not held.is_empty() or panel.has_point(point)
	if not event is InputEventMouseButton:return false
	point=event.position
	if event.button_index in [MOUSE_BUTTON_WHEEL_UP,MOUSE_BUTTON_WHEEL_DOWN] and event.pressed and panel.has_point(point):
		var target:=hit(point)
		if target.begins_with("page_"):
			var page:int=service.current.play.g_instrument.selected
			select_page(posmod(page+(1 if event.button_index==MOUSE_BUTTON_WHEEL_UP else -1),6))
		elif target=="parameter":
			pause();var before:float=service.current.play.number("fold");service.current.play.input("fold",clampf(before+(.02 if event.shift_pressed else .08)*(1 if event.button_index==MOUSE_BUTTON_WHEEL_UP else -1),0,1),"begin")
		return true
	if event.button_index!=MOUSE_BUTTON_LEFT:return panel.has_point(point)
	if event.pressed:
		pressed=hit(point)
		if pressed.is_empty():return panel.has_point(point)
		service.host.tooltip.hide();service.help_since_ms=Time.get_ticks_msec()
		if pressed=="write":
			held="write";pause();service.current.play.input("imprint",1.0,"begin")
		elif pressed=="parameter":held="parameter";pause();set_parameter(point.x,"begin")
		return true
	if not held.is_empty():
		if held=="parameter":set_parameter(point.x,"release");held="";pressed="";return true
		service.current.play.input("imprint",0.0,"release");held="";pressed="";notify("已停笔，进度保留；继续按住即可续写。");return true
	if not pressed.is_empty():
		var action:=pressed;pressed=""
		if action==hit(point):activate(action)
		return true
	return panel.has_point(point)

func pause()->void:
	service.host.rotation_enabled=false
	if is_record_player():service.current.play.g_instrument.pause_spin()
	service.host.tooltip.hide()

func set_parameter(x:float,event:String)->void:
	service.current.play.input("fold",clampf((x-panel.position.x-136)/214.0,0,1),event)

func select_page(i:int)->void:
	pause();service.sleep_pending=false;service.current.play.input("leaf",float(i),"begin");service.current.play.input("leaf",float(i),"release")
	notify("已选第 %d 页（%s），页面上的金色边标与它对应。"%[i+1,NAMES[i]])
	if is_archive():notify("第 %d 页：%s。读头会自动读取，并在前方展示台播放。"%[i+1,str(service.current.data.g_archive.contents[i].title)])
	if is_record_player():notify("已选 %d 号唱片：%s。自动取片、读取并打印。"%[i+1,str(service.current.data.g_archive.contents[i].title)])
	service.host.sound("click",1.0)

func activate(id:String)->void:
	if id.begins_with("page_"):select_page(int(id.trim_prefix("page_")));return
	if id=="rotate":service.toggle_rotation();return
	pause()
	match id:
		"front":service.host.angle=0;notify("已回到正面，旋转暂停。")
		"open":
			if is_archive():
				if service.current.open_target>.5:service.current.stow();service.sleep_pending=true
				else:select_page(service.current.play.g_instrument.selected)
			else:service.current.activate(1);service.host.power_target=1
		"play":
			if service.current.open_target<.5:select_page(service.current.play.g_instrument.selected)
			else:
				service.current.play.g_instrument.playback_paused=not service.current.play.g_instrument.playback_paused
				if is_record_player():
					service.current.play.g_instrument.spin_enabled=not service.current.play.g_instrument.playback_paused
					service.current.play.values.spin=1.0 if service.current.play.g_instrument.spin_enabled else 0.0
		"align":
			var instrument:RefCounted=service.current.play.g_instrument
			var chosen:int=instrument.selected;var bank:int=0 if chosen<3 else 3
			for i in range(bank,bank+3):instrument.folds[i]=.5
			service.current.play.values.fold=.5
			service.current.play.input("leaf",float(chosen),"begin");service.current.play.input("leaf",float(chosen),"release")
			notify("本组三页正在对准；显示“已对准”后按住写入。")
		"explode":service.sleep_pending=false;service.host.power_target=1;service.current.activate(3)
		"assemble":service.sleep_pending=false;service.host.power_target=1;service.current.stow()
		"exit":service.request_shutdown()
	service.host.sound("click",.95)

func update_state(delta:float)->void:
	visible=available()
	if not visible:
		layout_ready=false
		if not held.is_empty():cancel()
		return
	feedback_time=maxf(0,feedback_time-delta);point=service.pointer_position();layout();queue_redraw()

func box(rect:Rect2,bg:Color,border:Color,roundness:int=7)->void:
	var key:String=bg.to_html()+border.to_html()+str(roundness)
	if not styles.has(key):
		var style:=StyleBoxFlat.new();style.bg_color=bg;style.border_color=border;style.set_border_width_all(1);style.set_corner_radius_all(roundness);styles[key]=style
	draw_style_box(styles[key],rect)

func line_text(text:String,pos:Vector2,size:int,color:Color,width:float=-1)->void:draw_string(font,pos,text,HORIZONTAL_ALIGNMENT_LEFT,width,size,color)

func _draw()->void:
	if not visible or service.current==null:return
	var instrument:RefCounted=service.current.play.g_instrument
	var ink:=Color(.94,.88,.75);var muted:=Color(.69,.66,.59);var gold:=Color(.95,.63,.27)
	box(panel,Color(.075,.073,.065,.98),Color(.40,.34,.23),10)
	line_text("选唱片 → 自动取放 → 同盘打印" if is_record_player() else "选一页，播放其中的机械藏品" if is_archive() else "选页 → 对准 → 按住写入",panel.position+Vector2(13,30),16 if is_record_player() else 19,ink)
	for item in entries:
		if item.id=="parameter":continue
		var selected:bool=item.id=="page_"+str(instrument.selected)
		var over:bool=item.rect.has_point(point)
		var down:bool=item.id==held or item.id==pressed
		var primary:bool=item.id=="write" and instrument.alignment>.93
		var bg:=Color(.19,.16,.11) if selected else Color(.16,.15,.125) if over else Color(.105,.105,.092)
		if down:bg=Color(.31,.22,.11)
		box(item.rect,bg,gold if selected or primary else Color(.42,.36,.25) if over else Color(.25,.25,.21),5)
		var label:String=item.label
		if item.id=="write" and not is_archive():label="正在写入…" if instrument.writing else "按住重写" if instrument.records[instrument.selected]>=1 else "按住续写" if instrument.records[instrument.selected]>.001 else "按住写入"
		var text_size:=14 if item.id=="write" else 16;var size:=font.get_string_size(label,HORIZONTAL_ALIGNMENT_LEFT,-1,text_size)
		line_text(label,item.rect.get_center()+Vector2(-size.x*.5,5),text_size,gold if selected else ink)
	var percent:int=roundi(instrument.records[instrument.selected]*100)
	var status:String="第 %d 页 · %s · 记录 %d%%"%[instrument.selected+1,NAMES[instrument.selected],percent]
	var next:String
	if is_record_player():next=""
	elif service.current.explosion>.01 or service.current.explode_target>.01:next="拆解展示中；点击“组装”恢复。"
	elif service.current.stowing or service.current.open_target<.01:next="点击“展开书匣”或任一页开始。"
	elif service.current.openness<.995:next="正在展开，先选好要写的页。"
	elif instrument.alignment<.93:
		var blocked_pages:Array=[];var bank:int=0 if instrument.selected<3 else 3
		for i in range(bank,bank+3):
			if absf(instrument.actual[i]-.5)>.10:blocked_pages.append(str(i+1))
		next="第 "+"、".join(blocked_pages)+" 页错位，点击“对准本组”。" if not blocked_pages.is_empty() else "正在对准，请稍候。"
	elif instrument.writing:next="正在刻写；松手停笔，进度会保留。"
	elif percent>=100:next="已完成，记忆已重建；可选下一页或按住重写。"
	else:next="已对准，按住下方“写入”按钮；松手可暂停。"
	if is_archive():
		var item:Dictionary=service.current.data.g_archive.contents[instrument.selected]
		var value:float=instrument.parameters[instrument.selected]
		line_text(str(item.parameter),panel.position+Vector2(12,106),15,ink)
		var a:=panel.position+Vector2(136,100);var b:=panel.position+Vector2(350,100)
		draw_line(a,b,Color(.28,.27,.22),5,true);draw_line(a,a.lerp(b,value),gold,5,true);draw_circle(a.lerp(b,value),7,gold)
		var state_text:String
		match instrument.stage:
			"playing":state_text=str(item.title)+" · 播放中"
			"paused":state_text="已暂停，点击“继续播放”"
			"reading":state_text="读取 "+str(item.title)+" "+str(roundi(instrument.read_progress*100))+"%"
			"reconstructing":state_text="正在重建藏品…"
			"changing_media":state_text="收回上一件，切换书页…"
			"positioning_page":state_text="翻开前页，定位所选书页…"
			"extending_platen":state_text="展台伸出并锁定…"
			"opening":state_text="开书、伸出展示台…"
			"stowing":state_text="收回藏品、抬读头、合书…"
			"sleep":state_text="已合书；选择一页即可播放"
			_:state_text="点任意一页开始播放"
		if is_record_player():
			var labels:Dictionary={"sleep":"选一张唱片开始","indexing":"盘匣正在定位","approaching_record":"夹爪对准取片口","lowering_gripper":"夹爪落到唱片边框","clamping_record":"夹紧边框","lifting_record":"提片离槽","levelling_record":"翻腕放平唱片","carrying_record":"转运至唱盘","placing_record":"唱片落盘","releasing_record":"松开边框","clearing_platter":"夹爪提起让位","parking_gripper":"夹爪停放","positioning_tonearm":"唱臂对位","lowering_tonearm":"唱臂落下","reading":"读取 "+str(roundi(instrument.read_progress*100))+"%","lifting_tonearm":"读取完成，唱臂提起","parking_tonearm":"唱臂让开打印区域","printing":"同盘打印 "+str(roundi(instrument.print_amount*100))+"%","erasing":"反向回收藏品","braking_record":"停盘准备归片","parking_magazine":"盘匣归位"}
			if labels.has(instrument.stage):state_text=labels[instrument.stage]
			elif str(instrument.stage).begins_with("return_"):state_text="将原唱片送回空槽…"
		line_text(state_text,panel.position+Vector2(376,106),13 if is_record_player() else 14,ink,panel.size.x-388)
		line_text("慢转约 60 秒一圈；调节或按住动作时停转，可随时重新开始。" if is_record_player() else "拖动滑条："+str(item.parameter)+"；按住按钮："+str(item.action)+"。换页自动读取，无需对孔。",panel.position+Vector2(12,177),13 if is_record_player() else 14,muted,panel.size.x-24)
	else:
		line_text(status+"   |   "+next,panel.position+Vector2(12,105),15,gold if instrument.writing else ink,636)
		line_text(feedback if feedback_time>0 else "底座也可操作：选页轮点击/滚轮，滑块拖动调角，写入压板按住。",panel.position+Vector2(12,177),14,muted,636)
	# One selected-leaf marker, not six permanent bubbles. Screen-space brackets
	# intentionally remain visible for rear leaves, whose faces are occluded.
	if not is_record_player() and service.current.openness>.95 and service.current.explosion<.01 and instrument.rig_ready:
		var face:Node3D=instrument.leaves[instrument.selected].face
		var corners:PackedVector2Array=[]
		var half_height:float=float(service.current.data.get("g_archive",{}).get("leaf_half_height",.66))
		for v in [Vector3(.11,-half_height,0),Vector3(.83,-half_height,0),Vector3(.83,half_height,0),Vector3(.11,half_height,0)]:corners.append(service.host.camera.unproject_position(face.to_global(v)))
		for i in range(4):
			var c:Vector2=corners[i];draw_line(c,c.lerp(corners[(i+1)%4],.18),gold,2,true);draw_line(c,c.lerp(corners[posmod(i-1,4)],.18),gold,2,true)
		var anchor:Vector2=(corners[2]+corners[3])*.5
		var badge:=Rect2(anchor+Vector2(-73,-37),Vector2(146,27))
		box(badge,Color(.08,.07,.05,.93),gold,5)
		line_text("第 %d 页 · %s"%[instrument.selected+1,TITLES[instrument.selected] if is_archive() else NAMES[instrument.selected]],badge.position+Vector2(12,19),16,gold)

func diagnostics()->Dictionary:
	var targets:Array=[]
	if visible:
		for item in entries:targets.append({"id":item.id,"label":item.label,"x":item.rect.get_center().x,"y":item.rect.get_center().y})
	return {"visible":visible,"rotation_enabled":service.current.play.g_instrument.spin_enabled if is_record_player() else service.host.rotation_enabled,"held":held,"targets":targets,"panel":[panel.position.x,panel.position.y,panel.size.x,panel.size.y]}
