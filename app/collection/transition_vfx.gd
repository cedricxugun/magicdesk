extends Node3D
## Full-geometry wire pass and authored optical textures for archive/recast.
var owner_service:Node3D
var atlas:Texture2D
var ghosts:Array=[]
var ghost_material:ShaderMaterial
var ghost_depth:ShaderMaterial
var ring:MeshInstance3D
var ring_material:ShaderMaterial
var beams:Array=[]
var flares:Array=[]
var radius:=1.0
var bottom:=.59
var top:=3.9
var front:=.59
var running:=false
var clock:=0.0

func setup(service:Node3D)->void:
	owner_service=service;atlas=load("res://assets/collection/art/archive_atlas.png")
	ghost_material=ShaderMaterial.new();ghost_material.shader=load("res://collection/archive_ghost.gdshader");ghost_material.set_shader_parameter("atlas",atlas)
	ghost_depth=ShaderMaterial.new();ghost_depth.shader=load("res://collection/archive_depth.gdshader");ghost_depth.render_priority=-10;ghost_depth.next_pass=ghost_material
	ring=MeshInstance3D.new();ring_material=material(0,Vector2(1,.055));ring.material_override=ring_material;ring.cast_shadow=GeometryInstance3D.SHADOW_CASTING_SETTING_OFF;add_child(ring);ring.hide()
	for i in range(3):
		var beam:=MeshInstance3D.new();var cylinder:=CylinderMesh.new();cylinder.top_radius=.006;cylinder.bottom_radius=.006;cylinder.height=1;cylinder.radial_segments=8;beam.mesh=cylinder
		beam.material_override=material(0,Vector2(1,.04));beam.material_override.set_shader_parameter("swap_uv",true);beam.cast_shadow=GeometryInstance3D.SHADOW_CASTING_SETTING_OFF;add_child(beam);beam.hide();beams.append(beam)
		var flare:=MeshInstance3D.new();var quad:=QuadMesh.new();quad.size=Vector2(.16,.16);flare.mesh=quad;flare.material_override=material(3);flare.cast_shadow=GeometryInstance3D.SHADOW_CASTING_SETTING_OFF;add_child(flare);flare.hide();flares.append(flare)

func material(tile:int,crop:Vector2=Vector2.ONE)->ShaderMaterial:
	var m:=ShaderMaterial.new();m.shader=load("res://collection/archive_atlas.gdshader");m.set_shader_parameter("atlas",atlas);m.set_shader_parameter("tile",float(tile));m.set_shader_parameter("crop",crop)
	if tile==0:m.set_shader_parameter("center",Vector2(.5,.450))
	if tile==3:m.set_shader_parameter("center",Vector2(.5,.432));m.set_shader_parameter("crop",Vector2(.7,.7))
	return m

func begin(subject:Node3D)->void:
	finish();running=true;clock=0
	ghost_material.set_shader_parameter("front",100.0);ghost_material.set_shader_parameter("gain",0.)
	ghost_depth.set_shader_parameter("front",100.0)
	var meshes:Array[MeshInstance3D]=[];collect(subject,meshes)
	var bounds:=AABB();var first:=true
	for source in meshes:
		var box: AABB=source.global_transform*source.get_aabb();bounds=box if first else bounds.merge(box);first=false
		var ghost:=MeshInstance3D.new();ghost.mesh=source.mesh;ghost.material_override=ghost_depth;ghost.cast_shadow=GeometryInstance3D.SHADOW_CASTING_SETTING_OFF;add_child(ghost);ghost.global_transform=source.global_transform
		for i in range(source.get_blend_shape_count()):ghost.set_blend_shape_value(i,source.get_blend_shape_value(i))
		ghosts.append({"node":ghost,"source":source})
	bottom=maxf(.58,bounds.position.y);top=maxf(bottom+.15,bounds.end.y)
	front=top
	radius=clampf(maxf(absf(bounds.position.x),absf(bounds.end.x))+.07,.68,1.35)
	ring.mesh=annulus(radius)

func collect(node:Node,meshes:Array[MeshInstance3D])->void:
	if node is MeshInstance3D and node.is_visible_in_tree():meshes.append(node)
	for child in node.get_children():
		if not child is StaticBody3D:collect(child,meshes)

func annulus(r:float)->ArrayMesh:
	var vertices:=PackedVector3Array();var uv:=PackedVector2Array();var indices:=PackedInt32Array()
	for i in range(129):
		var a:=i/128.0*TAU
		for side in [-1,1]:vertices.append(Vector3(cos(a)*(r+side*.027),0,sin(a)*(r+side*.027)));uv.append(Vector2(i/128.0,(side+1)*.5))
	for i in range(128):var k:=i*2;indices.append_array(PackedInt32Array([k,k+1,k+3,k,k+3,k+2]))
	var arrays:Array=[];arrays.resize(Mesh.ARRAY_MAX);arrays[Mesh.ARRAY_VERTEX]=vertices;arrays[Mesh.ARRAY_TEX_UV]=uv;arrays[Mesh.ARRAY_INDEX]=indices
	var mesh:=ArrayMesh.new();mesh.add_surface_from_arrays(Mesh.PRIMITIVE_TRIANGLES,arrays);return mesh

func update(amount:float,recast:bool,delta:float)->void:
	if not running:return
	clock+=delta;front=lerpf(bottom,top,1.0-amount)
	var gain:=1.0 if recast else smoothstep(0.0,.10,amount)*(1.0-smoothstep(.78,1.0,amount))
	ghost_material.set_shader_parameter("front",front);ghost_material.set_shader_parameter("gain",gain*.80);ghost_material.set_shader_parameter("phase",clock)
	ghost_depth.set_shader_parameter("front",front)
	for item in ghosts:item.node.global_transform=item.source.global_transform
	ring.show();ring.global_position=Vector3(0,front+.009,0);ring_material.set_shader_parameter("gain",2.6);ring_material.set_shader_parameter("travel",clock*.12)
	for i in range(beams.size()):
		var emitter:Node3D=owner_service.scanner_emitters[i]
		var radial:Vector3=Vector3(emitter.global_position.x,0,emitter.global_position.z).normalized()
		var destination:=radial*radius+Vector3(0,front+.009,0)
		var direction:Vector3=destination-emitter.global_position
		beams[i].show();beams[i].global_position=(destination+emitter.global_position)*.5
		beams[i].global_basis=Basis(Quaternion(Vector3.UP,direction.normalized()))*Basis.from_scale(Vector3(1,direction.length(),1));beams[i].material_override.set_shader_parameter("gain",2.4)
		flares[i].show();flares[i].global_position=emitter.global_position;flares[i].global_basis=owner_service.host.camera.global_basis;flares[i].material_override.set_shader_parameter("gain",2.2)

func finish()->void:
	running=false
	for item in ghosts:item.node.hide();item.node.queue_free()
	ghosts.clear()
	if ring:ring.hide()
	for beam in beams:beam.hide()
	for flare in flares:flare.hide()
