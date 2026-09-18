extends RefCounted
## Display-only sizing: never scales shared-base or device geometry.
static func target_base_points(usable_pixels:Vector2i, backing_scale:float)->float:
	var logical:=Vector2(usable_pixels)/maxf(1.0,backing_scale)
	return clampf(minf(logical.x*.28,logical.y*.39),260.0,400.0)

static func base_width_pixels(host:Node3D)->float:
	var low:=INF;var high:=-INF
	# BASE_FIXED's D=2.74/H=.670608 contract excludes interchangeable
	# control recesses/cowl geometry, which must not change calibration.
	for y in [.005,.675608]:
		for i in range(96):
			var a:float=i*TAU/96.0
			var point:Vector3=host.fixed_base.to_global(Vector3(1.37*cos(a),y,1.37*sin(a)))
			var screen:Vector2=host.camera.unproject_position(point)
			low=minf(low,screen.x);high=maxf(high,screen.x)
	return high-low if is_finite(high-low) else 0.0

static func apply(host:Node3D,initial:bool=false)->void:
	if not host.mac_desktop:return
	var screen:int=host.get_window().current_screen
	var backing:=maxf(1.0,DisplayServer.screen_get_scale(screen))
	if initial:
		var usable:=DisplayServer.screen_get_usable_rect(screen)
		var current:=base_width_pixels(host)
		if current<=0.0:return
		host.desktop_base_points=target_base_points(usable.size,backing)
		host.desktop_unit_focal=host.reference_focal_pixels*host.desktop_base_points*backing/current
	host.reference_focal_pixels=host.desktop_unit_focal*host.zoom
	host.camera.fov=rad_to_deg(2.0*atan(host.canonical_size.y/(2.0*host.reference_focal_pixels)))
