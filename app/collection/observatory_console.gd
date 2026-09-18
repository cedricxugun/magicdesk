extends RefCounted
## Readout is mounted on existing enamel plates, with ordinary depth occlusion.
var service:Node3D
var title_labels:Array=[]
var original_titles:Array=[]
var readout:Label3D
var readout_text:=""
func label(parent:Node3D,text:String,position:Vector3,size:float)->Label3D:
	var node:=Label3D.new();var font:=SystemFont.new();font.font_names=PackedStringArray(["PingFang SC","Helvetica Neue"])
	node.font=font;node.font_size=64;node.pixel_size=size/64.;node.text=text;node.position=position
	node.modulate=Color(.30,.045,.018);node.outline_size=0;node.no_depth_test=false;node.billboard=BaseMaterial3D.BILLBOARD_DISABLED
	parent.add_child(node);return node
func setup(owner:Node3D)->void:
	service=owner
	for control in service.custom_controls:
		if int(control.index) not in [2,5]:continue
		var socket:Node3D=control.node.find_child("WidgetSocket*",true,false)
		if not socket:continue
		for child in socket.get_children():
			if str(child.name).begins_with("Legend_"):original_titles.append(child)
		title_labels.append(label(socket,"调 时" if control.index==2 else "按住共鸣",Vector3(0,-.121,.0305),.029))
		if control.index==2:readout=label(socket,"归零",Vector3(0,.071,.034),.025)
	tick(0.)
func tick(_delta:float)->void:
	var player:RefCounted=service.current.play.g_instrument
	var selected:bool=player.selected==0
	for node in title_labels:node.visible=selected
	for node in original_titles:node.visible=not selected
	if not readout:return
	readout.visible=selected
	var minutes:float=(player.observatory_parameter-.5)*60.
	var text:="装载中" if player.loaded_index!=0 or player.stage not in ["playing","paused"] else "归零" if absf(minutes)<.05 else ("+" if minutes>0 else "−")+str(snappedf(absf(minutes),.1))+"分"
	if text!=readout_text:readout_text=text;readout.text=text
func state()->Dictionary:return {"text":readout_text,"visible":readout!=null and readout.visible}
