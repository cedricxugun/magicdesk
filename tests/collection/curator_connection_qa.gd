extends SceneTree
var issues:Array=[]
func _initialize()->void:run.call_deferred()
func run()->void:
	var data:Dictionary=JSON.parse_string(FileAccess.get_file_as_string("res://assets/collection/models/G_optical_curator.json"))
	var host:=Node3D.new();root.add_child(host)
	var model:Node3D=load("res://collection/module.gd").new();host.add_child(model);model.data=data
	model.asset=load("res://assets/collection/models/G_optical_curator.glb").instantiate();model.add_child(model.asset)
	model.play=load("res://collection/play_state.gd").new();model.play.values={"leaf":0.,"fold":.5,"imprint":0.,"spin":1.}
	var player:RefCounted=load("res://collection/optical_curator.gd").new();player.setup(model);model.play.g_instrument=player;model.power=1;model.open_target=1
	var max_joint_error:=0.;var min_piston_overlap:=100.;var max_iris_link_error:=0.;var max_neck_pivot_error:=0.;var samples:=0
	for selection in range(6):
		player.changed("leaf",0.,float(selection),"begin")
		for i in range(1600):
			player.tick(1./60);player.apply();samples+=1
			var elbow:Vector3=player.upper.to_global(Vector3(0,data.record_player.lengths[0],0));var wrist:Vector3=player.fore.to_global(Vector3(0,data.record_player.lengths[1],0))
			max_joint_error=maxf(max_joint_error,elbow.distance_to(player.fore.global_position));max_joint_error=maxf(max_joint_error,wrist.distance_to(player.wrist.global_position))
			var bottom:float=player.tone.position.y-.315;min_piston_overlap=minf(min_piston_overlap,.935-bottom)
			for link in player.follower_links:
				max_iris_link_error=maxf(max_iris_link_error,link.node.global_position.distance_to(link.blade_pin.global_position))
				max_iris_link_error=maxf(max_iris_link_error,link.node.to_global(Vector3.UP).distance_to(link.cam_pin.global_position))
			var pivot:Vector3=model.v3(data.optical_curator.get("face_pivot",[0,0,0]))
			max_neck_pivot_error=maxf(max_neck_pivot_error,player.face.to_global(pivot).distance_to(player.carrier.to_global(player.face_home.origin+pivot)))
			if player.loaded_index>=0:
				var disc:Node3D=player.media[player.loaded_index]
				if not disc.scale.is_equal_approx(Vector3.ONE*data.record_player.record_scale):issues.append("record scale changed")
			if player.stage=="playing" and player.loaded_index==selection:break
	issues.append_array(["joint endpoint disconnect"] if max_joint_error>.00001 else [])
	issues.append_array(["reader piston exits sleeve"] if min_piston_overlap<.04 else [])
	issues.append_array(["iris follower disconnect"] if max_iris_link_error>.00001 else [])
	issues.append_array(["neck pivot slips while head moves"] if max_neck_pivot_error>.00001 else [])
	var report:={"passed":issues.is_empty(),"samples":samples,"max_joint_endpoint_error":max_joint_error,"min_reader_piston_overlap":min_piston_overlap,"max_iris_link_error":max_iris_link_error,"max_neck_pivot_error":max_neck_pivot_error,"issues":issues.slice(0,10),"scope":"Endpoints, neck pivot, iris followers, sleeve engagement and disc scale; does not prove all mesh clearance"}
	FileAccess.open("res://../review/G_optical_curator/connection_report.json",FileAccess.WRITE).store_string(JSON.stringify(report,"  "));print(JSON.stringify(report));host.free();quit(0 if report.passed else 2)
