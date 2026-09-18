extends SceneTree
const Physics=preload("res://collection/f_dynamics.gd")
func _initialize()->void:run.call_deferred()
func run()->void:
	var samples:Array=[]
	for preload_scale in [1.0,.35,.20]:
		for bias_scale in [1.0,.40]:
			for polarity in [-1.0,0.0,1.0]:
				for trim in [-1.0,-.5,0.,.5,1.0]:
					var p=Physics.new();p.length_scale=1.2;p.release();p.trim=trim*preload_scale;p.polarity=polarity*bias_scale
					var minimum:=INF;var maximum:=-INF;var at_stop:=0;var speed_sum:=0.;var settled_angle:=0.
					for frame in range(1200):
						p.advance(1./60.,0.)
						minimum=minf(minimum,p.theta);maximum=maxf(maximum,p.theta)
						if frame>=900:
							if absf(p.theta-deg_to_rad(-58.))<.0005 or absf(p.theta-deg_to_rad(-30.))<.0005:at_stop+=1
							speed_sum+=absf(p.omega);settled_angle+=p.theta
					var net_low:float=p._derivative(deg_to_rad(-58.),0.,Vector3.DOWN,Vector3.ZERO,Vector3.DOWN,Vector3.ZERO)[1]
					var net_high:float=p._derivative(deg_to_rad(-30.),0.,Vector3.DOWN,Vector3.ZERO,Vector3.DOWN,Vector3.ZERO)[1]
					samples.append({"preload_scale":preload_scale,"bias_scale":bias_scale,"trim":trim,"polarity":polarity,"angle_min":rad_to_deg(minimum),"angle_max":rad_to_deg(maximum),"settled_angle":rad_to_deg(settled_angle/300.),"mean_final_speed":speed_sum/300.,"stop_fraction_last_5s":at_stop/300.,"stop_contacts":p.stop_contacts,"has_interior_equilibrium":net_low*net_high<0.})
	var report:={"physics_source_sha256":FileAccess.get_sha256("res://collection/f_dynamics.gd"),"samples":samples,"scope":"20-second real solver responses, fixed yaw, display length scale1.2. Candidate scales remap input only; production parameters unchanged. Last 5s stop occupancy, interior equilibrium and speed measured."}
	FileAccess.open("res://../review/F_complete/revision_20260911/control_response_baseline.json",FileAccess.WRITE).store_string(JSON.stringify(report,"  "))
	print("F_CONTROL_SWEEP ",samples.size());quit()
