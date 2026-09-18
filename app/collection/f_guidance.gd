extends RefCounted
## Read-only guidance tied to the actual instrument, never a simulated success.
static func next_step(module:Node3D)->Dictionary:
	var f:RefCounted=module.play.instrument
	if module.explosion>.01 or module.explode_target>.01:
		return {"code":"assemble","text":"先把最右侧拆装杆向右拨，装回机构。"}
	match f.calibration_reason:
		"transport":return {"code":"release","text":"轻触左侧预载轮释放机构，再观察合衡表。"}
		"brake":return {"code":"release_brake","text":"松开制动压板，让机构自由稳定；刹住不算校准。"}
		"adjusting":return {"code":"release_control","text":"调好后松手，等预载机构到位。"}
		"motion":return {"code":"wait_motion","text":"配重还在摆，先等它慢下来；短按制动可以减摆，随后松开。"}
		"calibrated":return {"code":"complete","text":"已校准。拨动红色磁偏置杆改变受力，再用预载轮找回平衡。"}
		"settling":return {"code":"wait_settle","text":"已经接近平衡。保持松手，等琥珀灯亮起，观察校准光场。"}
	var error:float=f.physics.theta-f.physics.REST
	if absf(error)<.020:
		return {"code":"wait_motion","text":"指针已接近中线，等两只配重都停稳。"}
	return {"code":"trim_down" if error>0 else "trim_up","text":"指针偏右：预载轮往 − 方向微调。" if error>0 else "指针偏左：预载轮往 + 方向微调。"}

static func hint(module:Node3D,index:int)->String:
	var action:=""
	match index:
		1:action="左右拖动或滚轮调预载，Shift＋滚轮微调。"
		2:action="按住奶白压板减缓摆动，松手释放。"
		3:action="目标：指针回中、松手、等琥珀灯亮。"
		4:action="最右侧拨杆：左拨拆解，右拨组装并收回。"
		5:action="红杆上下拨动或滚轮切换 −／0／+ 磁偏置。"
	return action+"\n"+str(next_step(module).text)
