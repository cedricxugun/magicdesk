extends SceneTree
func _initialize()->void:run.call_deferred()
func run()->void:
	var rng:=RandomNumberGenerator.new();rng.seed=194761
	var records:Array=[]
	for i in range(96):
		var s:RefCounted=load("res://collection/f_dynamics.gd").new()
		s.length_scale=1.0 if i%2==0 else 1.2;s.trim=rng.randf_range(-.8,.8);s.polarity=(i%3)-1
		s.brake=.25 if i%3==0 else 0.0;s.parking=i%5==0
		s.yaw=rng.randf_range(-PI,PI);s.yaw_rate=rng.randf_range(-.4,.4);s.yaw_accel=rng.randf_range(-.7,.7)
		var theta:=deg_to_rad(rng.randf_range(-55,-33));var omega:=rng.randf_range(.08,.40)*(1 if i%2==0 else -1)
		var d:=Vector3(rng.randf_range(-.08,.08),0,rng.randf_range(-.08,.08));d.y=-sqrt(1-d.x*d.x-d.z*d.z)
		var e:=Vector3(rng.randf_range(-.08,.08),0,rng.randf_range(-.08,.08));e.y=-sqrt(1-e.x*e.x-e.z*e.z)
		var u:=Vector3(rng.randf_range(-.2,.2),0,rng.randf_range(-.2,.2));u.y=-(d.x*u.x+d.z*u.z)/d.y
		var v:=Vector3(rng.randf_range(-.2,.2),0,rng.randf_range(-.2,.2));v.y=-(e.x*v.x+e.z*v.z)/e.y
		var derivative:Array=s._derivative(theta,omega,d,u,e,v)
		records.append({"q":[theta,d.x,d.z,e.x,e.z],"velocity":[omega,u.x,u.z,v.x,v.z],"actual":[derivative[1],derivative[3].x,derivative[3].z,derivative[5].x,derivative[5].z],"yaw":s.yaw,"yaw_rate":s.yaw_rate,"yaw_accel":s.yaw_accel,"scale":s.length_scale,"left_mass":s.left_mass,"right_mass":s.right_mass,"inertia":s.shaft_inertia,"spring":s.spring,"shaft_drag":s.shaft_drag,"air_drag":s.air_drag,"trim":s.trim,"polarity":s.polarity,"brake":s.brake,"parking":s.parking})
	FileAccess.open(ProjectSettings.globalize_path("res://../review/F_complete/lagrange_samples.json"),FileAccess.WRITE).store_string(JSON.stringify(records))
	print("F_LAGRANGE_SAMPLES ",records.size());quit()
