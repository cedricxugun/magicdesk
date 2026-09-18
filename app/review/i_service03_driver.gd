extends RefCounted
## Review-stage overlay of the authored service03 clip on the actual body.
## Bind only after ordinary cover opening has reached its prepared pose.
var body:Node3D
var motion:Node3D
var player:AnimationPlayer
var bindings:Array=[]
var duration:=0.
var time:=0.
var target:=0.
var velocity:=0.
func bind(subject:Node3D,body_spec:Dictionary,manifest:Dictionary)->void:
	assert(body_spec.source_sha256==manifest.body_source_sha256 and body_spec.component_sha256==manifest.body_component_sha256)
	assert(FileAccess.get_sha256(manifest.motion_asset)==manifest.motion_asset_sha256)
	body=subject;duration=manifest.duration
	motion=load(manifest.motion_asset).instantiate();body.add_child(motion)
	player=motion.find_children("*","AnimationPlayer",true,false)[0]
	assert(player.has_animation(manifest.clip));player.play(manifest.clip);player.pause()
	var targets:Array[Node]=[]
	for group in manifest.groups:
		var marker:=motion.find_child(group.marker,true,false)as Node3D;assert(marker!=null)
		var row:={"marker":marker,"targets":[]}
		for name in group.roots:
			var node:=body.find_child(name,true,false)as Node3D;assert(node!=null)
			for i in range(manifest.local_points.size()):
				var p:Array=manifest.local_points[i];var expected:Array=manifest.source_witnesses[0].points[name][i]
				assert(node.to_global(Vector3(p[0],p[1],p[2])).distance_to(body.to_global(Vector3(expected[0],expected[1],expected[2])))<.00001,"Service binding requires the authored prepared pose: "+name)
			for old in targets:assert(not old.is_ancestor_of(node) and not node.is_ancestor_of(old) and old!=node)
			targets.append(node);row.targets.append({"node":node,"home":node.transform})
		bindings.append(row)
	seek(0.)
func seek(seconds:float)->void:
	time=clampf(seconds,0.,duration);target=time;velocity=0.;apply()
func request(extracted:bool)->void:target=duration if extracted else 0.
func tick(delta:float)->void:
	var remaining:=maxf(0.,delta)
	while remaining>.0000001:
		var dt:=minf(remaining,1./120.);remaining-=dt
		var desired:=clampf((target-time)*6.,-1.,1.)
		velocity=move_toward(velocity,desired,dt*4.)
		time=clampf(time+velocity*dt,0.,duration)
		if absf(target-time)<.00001 and absf(velocity)<.001:time=target;velocity=0.
	apply()
func apply()->void:
	player.seek(time,true)
	for binding in bindings:
		var delta:Vector3=body.global_basis*binding.marker.position
		for item in binding.targets:
			var pose:Transform3D=item.home
			pose.origin+=item.node.get_parent().global_basis.inverse()*delta
			item.node.transform=pose
func stowed()->bool:return time==0. and target==0. and velocity==0.
func release()->void:
	for binding in bindings:
		for item in binding.targets:
			if is_instance_valid(item.node):item.node.transform=item.home
	bindings.clear()
	if is_instance_valid(motion):motion.queue_free()
