extends RefCounted
## Review-only playback of the Blender-authored rigid motion, including screw rotation.
var subject:Node3D
var motion:Node3D
var player:AnimationPlayer
var bindings:Array=[]
var ordered:Array=[]
var duration:=0.
var time:=0.
var target:=0.
var velocity:=0.

func bind(body:Node3D,nodes:Dictionary,spec:Dictionary,manifest:Dictionary)->bool:
	if spec.source_sha256!=manifest.body_source_sha256 or spec.component_sha256!=manifest.body_component_sha256:return false
	if FileAccess.get_sha256(manifest.motion_asset)!=manifest.motion_asset_sha256:return false
	subject=body;duration=float(manifest.duration)
	motion=load(manifest.motion_asset).instantiate();subject.add_child(motion)
	var players:=motion.find_children("*","AnimationPlayer",true,false)
	if players.size()!=1:return false
	player=players[0];player.play(manifest.clip);player.pause();player.seek(0.,true)
	var claimed:Dictionary={}
	for g in manifest.groups:
		var marker:=motion.find_child(g.marker,true,false)as Node3D
		if marker==null:return false
		var row:={"marker":marker,"initial_inverse":marker.transform.affine_inverse(),"items":[]}
		for name in g.roots:
			if not nodes.has(name) or claimed.has(nodes[name]):return false
			var node:Node3D=nodes[name];claimed[node]=true
			var item:={"node":node,"original":node.transform,"home_in_body":body.global_transform.affine_inverse()*node.global_transform,"binding":bindings.size()}
			row.items.append(item);ordered.append(item)
		bindings.append(row)
	ordered.sort_custom(func(a,b):return a.node.get_path().get_name_count()<b.node.get_path().get_name_count())
	apply();return true

func seek(seconds:float)->void:
	time=clampf(seconds,0.,duration);target=time;velocity=0.;apply()
func request(extracted:bool)->void:target=duration if extracted else 0.
func tick(delta:float)->void:
	var remaining:=maxf(delta,0.)
	while remaining>.0000001:
		var step:=minf(remaining,1./120.);remaining-=step
		velocity=move_toward(velocity,clampf((target-time)*6.,-1.,1.),step*4.)
		time=clampf(time+velocity*step,0.,duration)
		if absf(target-time)<.00001 and absf(velocity)<.001:time=target;velocity=0.
	apply()
func apply()->void:
	player.seek(time,true)
	var deltas:Array[Transform3D]=[]
	for row in bindings:deltas.append(row.marker.transform*row.initial_inverse)
	for item in ordered:item.node.global_transform=subject.global_transform*deltas[item.binding]*item.home_in_body
func stowed()->bool:return time==0. and target==0. and velocity==0.
func release()->void:
	for item in ordered:
		if is_instance_valid(item.node):item.node.transform=item.original
	ordered.clear();bindings.clear()
	if is_instance_valid(motion):motion.queue_free()
