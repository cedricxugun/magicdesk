extends RefCounted
## The signed balance needle is mechanical. This lens reports why it is waiting.
var service:Node3D
var lamp:StandardMaterial3D
var gain:=0.0
var legends:Array=[]
var setup_frames:=0
var projected:=false
var setup_physics_frame:=0
var projection_report:Dictionary={}
var descriptor:Dictionary={}
const CACHE_PATH:="res://assets/collection/f_console_mounts.json"
func setup(owner:Node3D)->void:
	service=owner;setup_physics_frame=Engine.get_physics_frames()
	for control in service.custom_controls:
		for patch in control.node.find_children("*LegendSurface*","Node3D",true,false):
			legends.append({"control":control.node,"patch":patch});patch.visible=false
		var source:Node3D=control.node.find_child("FCTRL_SettleLamp",true,false)
		if not source:continue
		lamp=StandardMaterial3D.new();lamp.albedo_color=Color(.19,.062,.015);lamp.metallic=.22;lamp.roughness=.17;lamp.clearcoat_enabled=true;lamp.clearcoat=.45;lamp.emission_enabled=true;lamp.emission=Color(1.,.40,.10)
		for mesh in source.find_children("*","MeshInstance3D",true,false):mesh.material_override=lamp
func tick(delta:float)->void:
	setup_frames+=1
	if not projected and setup_frames>=3 and Engine.get_physics_frames()>setup_physics_frame:
		setup_physics_frame=Engine.get_physics_frames();_seat_legends()
	if not lamp:return
	var module:Node3D=service.current;var f:RefCounted=module.play.instrument
	var target:=.025
	if f.calibration_reason=="settling":target=.08+f.charge*.55
	elif f.calibration_reason=="calibrated":target=.12+f.peak()*.7
	elif f.calibration_reason=="brake":target=.045
	gain=move_toward(gain,target,delta*2.)
	lamp.emission_energy_multiplier=gain*module.power*module.openness*(1.-module.explosion)

func _hash_mesh(mesh:Mesh)->String:
	var key:int=mesh.get_instance_id()
	if service.f_surface_hash_cache.has(key):return service.f_surface_hash_cache[key]
	var hash:=HashingContext.new();hash.start(HashingContext.HASH_SHA256)
	for i in range(mesh.get_surface_count()):
		var arrays:Array=mesh.surface_get_arrays(i)
		hash.update(arrays[Mesh.ARRAY_VERTEX].to_byte_array())
		if arrays[Mesh.ARRAY_INDEX]!=null:hash.update(arrays[Mesh.ARRAY_INDEX].to_byte_array())
	var result:String=hash.finish().hex_encode();service.f_surface_hash_cache[key]=result;return result

func _surface_signature()->String:
	var hash:=HashingContext.new();hash.start(HashingContext.HASH_SHA256)
	var meshes:Array=[service.base_display]
	var panel:Node3D=service.custom_panel.find_child("S_PANEL",true,false)
	if panel:
		if panel is MeshInstance3D:meshes.append(panel)
		meshes.append_array(panel.find_children("*","MeshInstance3D",true,false))
	for mesh in meshes:
		hash.update(var_to_bytes(mesh.global_transform));hash.update(_hash_mesh(mesh.mesh).to_utf8_buffer())
	return hash.finish().hex_encode()

func _apply_meshes(changes:Array)->void:
	for change in changes:
		var mesh:MeshInstance3D=change.mesh;var materials:Array=[]
		for i in range(mesh.mesh.get_surface_count()):materials.append(mesh.get_active_material(i))
		mesh.mesh=change.replacement
		for i in range(materials.size()):mesh.set_surface_override_material(i,materials[i])
		var key:int=mesh.mesh.get_instance_id()
		if not service.control_shape_cache.has(key):service.control_shape_cache[key]=mesh.mesh.create_trimesh_shape()
		for body in mesh.get_children():
			if body is StaticBody3D:
				for shape in body.get_children():
					if shape is CollisionShape3D:shape.shape=service.control_shape_cache[key]
	for item in legends:item.patch.visible=true
	projected=true

func _seat_legends()->void:
	var started:=Time.get_ticks_usec();var source_hashes:Dictionary={};var mount_frames:Dictionary={};var nodes:Array=[]
	for item in legends:
		mount_frames[str(item.control.name)]=str(item.control.global_transform)
		for mesh in item.patch.find_children("*","MeshInstance3D",true,false):
			nodes.append(mesh);source_hashes[str(mesh.name)]=_hash_mesh(mesh.mesh)
	descriptor={"algorithm":1,"surface_signature":_surface_signature(),"source_hashes":source_hashes,"mount_frames":mount_frames,"offset":.00035}
	if FileAccess.file_exists(CACHE_PATH):
		var saved:Variant=JSON.parse_string(FileAccess.get_file_as_string(CACHE_PATH))
		if saved is Dictionary and saved.get("algorithm")==1 and saved.get("surface_signature")==descriptor.surface_signature and saved.get("source_hashes")==source_hashes and saved.get("mount_frames")==mount_frames:
			var changes:Array=[];var vertex_count:=0
			for mesh in nodes:
				var path:String=saved.get("meshes",{}).get(str(mesh.name),"")
				if path.is_empty() or not ResourceLoader.exists(path):break
				if not service.f_legend_mesh_cache.has(path):service.f_legend_mesh_cache[path]=load(path)
				var replacement:ArrayMesh=service.f_legend_mesh_cache[path]
				if replacement.get_surface_count()!=mesh.mesh.get_surface_count():break
				for i in range(replacement.get_surface_count()):vertex_count+=replacement.surface_get_array_len(i)
				changes.append({"mesh":mesh,"replacement":replacement})
			if changes.size()==nodes.size():
				_apply_meshes(changes)
				projection_report={"elapsed_ms":(Time.get_ticks_usec()-started)/1000.,"unique_rays":0,"vertices":vertex_count,"misses":0,"offset":.00035,"cache_used":true}
				return
	var changes:Array=[];var hits:=0;var misses:=0;var unique_rays:=0
	for item in legends:
		var control:Node3D=item.control;var patch:Node3D=item.patch;var cache:Dictionary={}
		for mesh in patch.find_children("*","MeshInstance3D",true,false):
			var replacement:=ArrayMesh.new()
			for surface in range(mesh.mesh.get_surface_count()):
				var arrays:Array=mesh.mesh.surface_get_arrays(surface)
				var vertices:PackedVector3Array=arrays[Mesh.ARRAY_VERTEX];var normals:PackedVector3Array=arrays[Mesh.ARRAY_NORMAL]
				for i in range(vertices.size()):
					var local:Vector3=control.to_local(mesh.to_global(vertices[i]))
					var key:=Vector2i(roundi(local.x*100000.),roundi(local.y*100000.))
					if not cache.has(key):
						unique_rays+=1
						var query:=PhysicsRayQueryParameters3D.create(control.to_global(Vector3(local.x,local.y,.15)),control.to_global(Vector3(local.x,local.y,-.15)),3)
						cache[key]=service.host.get_world_3d().direct_space_state.intersect_ray(query)
					var hit:Dictionary=cache[key]
					if hit.is_empty():misses+=1;continue
					hits+=1
					vertices[i]=mesh.to_local(hit.position+hit.normal*(.00035+maxf(0.,local.z)))
					if i<normals.size():normals[i]=(mesh.global_basis.inverse()*hit.normal).normalized()
				arrays[Mesh.ARRAY_VERTEX]=vertices;arrays[Mesh.ARRAY_NORMAL]=normals
				replacement.add_surface_from_arrays(Mesh.PRIMITIVE_TRIANGLES,arrays)
				replacement.surface_set_material(surface,mesh.mesh.surface_get_material(surface))
			changes.append({"mesh":mesh,"replacement":replacement})
	projection_report={"unique_rays":unique_rays,"vertices":hits,"misses":misses,"offset":.00035,"cache_used":false}
	if misses==0:_apply_meshes(changes)
	projection_report.elapsed_ms=(Time.get_ticks_usec()-started)/1000.

func export_projection()->Dictionary:
	var result:Dictionary=projection_report.duplicate(true);result.meshes={};result.descriptor=descriptor
	for item in legends:
		for mesh in item.patch.find_children("*","MeshInstance3D",true,false):
			var surfaces:Array=[]
			for i in range(mesh.mesh.get_surface_count()):
				var arrays:Array=mesh.mesh.surface_get_arrays(i)
				surfaces.append({"vertices":Array(arrays[Mesh.ARRAY_VERTEX]).map(func(v):return [v.x,v.y,v.z]),"normals":Array(arrays[Mesh.ARRAY_NORMAL]).map(func(v):return [v.x,v.y,v.z]),"indices":Array(arrays[Mesh.ARRAY_INDEX])})
			result.meshes[str(mesh.name)]=surfaces
	return result
