extends RefCounted
## Recording-derived bands, actual authored frame UVs and local shadowed spill.
var bindings:Array=[]
var status:Dictionary={}
var levels:=Vector3.ZERO
var illumination:Dictionary={}
var light_floor:=0.
func bind(asset:Node3D,spec:Dictionary)->void:
    var layout:Dictionary=JSON.parse_string(FileAccess.get_file_as_string(str(spec.chamber_response_layout)))
    assert(layout.source_sha256==spec.source_sha256 and layout.component_sha256==spec.component_sha256)
    assert(FileAccess.get_sha256(str(layout.mask))==layout.mask_sha256)
    illumination=layout.get("illumination",{})
    var texture:Texture2D=load(str(layout.mask))
    for row in layout.cells:
        var mesh:=asset.find_child(str(row.frame),true,false)as MeshInstance3D;assert(mesh!=null)
        var materials:Array=[]
        for i in range(mesh.mesh.get_surface_count()):
            var old:=mesh.get_active_material(i)as BaseMaterial3D;assert(old!=null)
            var arrays:Array=mesh.mesh.surface_get_arrays(i);assert(not (arrays[Mesh.ARRAY_TEX_UV2]as PackedVector2Array).is_empty())
            var mat:=ShaderMaterial.new();mat.shader=load("res://collection/i_chamber_conductor.gdshader")
            mat.set_shader_parameter("base_color",old.albedo_color);mat.set_shader_parameter("metallic_value",old.metallic);mat.set_shader_parameter("roughness_value",old.roughness)
            mat.set_shader_parameter("conductor_mask",texture);mat.set_shader_parameter("cell_phase",float(row.phase_offset))
            if not illumination.is_empty():
                mat.set_shader_parameter("continuous_conductor",true)
                mat.set_shader_parameter("emission_gain",float(illumination.emission_gain))
                mat.set_shader_parameter("mask_cross_scale",float(illumination.mask_cross_scale))
                mat.set_shader_parameter("conductor_offset",float(illumination.get("conductor_offset",0.)))
                mat.set_shader_parameter("conductor_half_width",float(illumination.get("conductor_half_width",.18)))
                mat.set_shader_parameter("packet_floor",float(illumination.packet_floor))
                var color:Array=illumination.get("light_color",[1.,.54,.16])
                mat.set_shader_parameter("conductor_color",Vector3(color[0],color[1],color[2]))
            if old.has_meta("chamber_brushing_texture"):
                mat.set_shader_parameter("has_brushing",true);mat.set_shader_parameter("brushing_texture",load(str(old.get_meta("chamber_brushing_texture"))));mat.set_shader_parameter("brushing_center",float(old.get_meta("chamber_brushing_center")));mat.set_shader_parameter("brushing_strength",float(old.get_meta("chamber_brushing_strength")))
            mesh.set_surface_override_material(i,mat);materials.append({"index":i,"original":old,"material":mat,"mesh":mesh,"emits":not bool(illumination.get("physical_conductors",false))})
        for diffuser in row.get("diffusers",[]):
            var conduit:=asset.find_child(str(diffuser.get("runtime_mesh",diffuser.mesh)),true,false)as MeshInstance3D;assert(conduit!=null)
            var matched:=0
            for i in range(conduit.mesh.get_surface_count()):
                var original:=conduit.get_active_material(i)as BaseMaterial3D
                if not original.resource_name.begins_with(str(diffuser.material)):continue
                var finish:=ShaderMaterial.new();finish.shader=load("res://collection/i_opal_conductor.gdshader")
                finish.set_shader_parameter("conductor_mask",texture)
                finish.set_shader_parameter("emission_gain",float(illumination.emission_gain))
                var tint:Array=illumination.get("light_color",[1.,.42,.09])
                finish.set_shader_parameter("diffuser_color",Vector3(tint[0],tint[1],tint[2]))
                conduit.set_surface_override_material(i,finish)
                materials.append({"index":i,"original":original,"material":finish,"mesh":conduit,"emits":true});matched+=1
            assert(matched>0,"Missing authored opal conductor surface")
        var light:OmniLight3D=null
        if bool(row.light_enabled):
            light=OmniLight3D.new();asset.add_child(light);var p:Array=row.light_position_godot;light.position=Vector3(p[0],p[1],p[2]);light.light_color=Color(1.,.56,.19);light.omni_range=.48;light.light_energy=0.;light.shadow_enabled=true
        var binding:Dictionary={"mesh":mesh,"materials":materials,"band":int(row.band),"light":light}
        if row.has("membrane_motion"):
            var m:Dictionary=row.membrane_motion;var membrane:=asset.find_child(str(m.mesh),true,false)as MeshInstance3D;assert(membrane!=null)
            var pressure:int=membrane.find_blend_shape_by_name(str(m.pressure_key));var rebound:int=membrane.find_blend_shape_by_name(str(m.rebound_key));assert(pressure>=0 and rebound>=0)
            binding["motion"]={"mesh":membrane,"pressure":pressure,"rebound":rebound,"position":0.,"velocity":0.,"frequency":float(m.natural_frequency_hz),"damping":float(m.damping_ratio),"max_world_stroke":float(m.max_world_stroke)}
        bindings.append(binding)
    status={"source_sha256":layout.source_sha256,"frames":bindings.size(),"motion":"authored_membrane_shapes"if bindings.any(func(r):return r.has("motion"))else "emission_only","authored_mask_sha256":layout.mask_sha256}
    update(Vector3.ZERO,0.,false,0.,0.)
func update(bands:Vector3,clock:float,playing:bool,opening:float,delta:float)->void:
    var gate:=smoothstep(.35,.90,opening)
    var target:=bands.clamp(Vector3.ZERO,Vector3.ONE)*gate if playing else Vector3.ZERO
    var factor:=1.-exp(-maxf(delta,0.)/ (.05 if target.length()>levels.length()else .18))
    levels=levels.lerp(target,factor)
    # Illumination remains readable during quiet passages; membrane force below
    # continues to use only the recording, never this open-state light floor.
    if not illumination.is_empty():
        var floor_target:float=gate*float(illumination.playing_floor if playing else illumination.open_floor)
        light_floor=lerpf(light_floor,floor_target,1.-exp(-maxf(delta,0.)/.20))
        if gate==0.:light_floor=0.
    var strokes:Array=[]
    for row in bindings:
        var value:float=levels[row.band]
        for material in row.materials:
            material.material.set_shader_parameter("response",(value if illumination.is_empty() else value*gate) if material.emits else 0.)
            material.material.set_shader_parameter("base_response",light_floor if material.emits else 0.)
            material.material.set_shader_parameter("travel",clock)
        if row.light!=null:row.light.light_energy=value*.16 if illumination.is_empty() else gate*(light_floor+value)*float(illumination.spill_gain)
        if row.has("motion"):
            var m:Dictionary=row.motion;var omega:float=TAU*m.frequency;var remaining:=maxf(delta,0.)
            while remaining>.0000001:
                var step:=minf(remaining,1./240.);remaining-=step
                var drive:float=target[row.band]*.75
                m.velocity+=(omega*omega*(drive-m.position)-2.*m.damping*omega*m.velocity)*step
                var next:float=m.position+m.velocity*step
                if next>1.:next=1.;m.velocity=minf(0.,m.velocity)
                elif next< -1.:next=-1.;m.velocity=maxf(0.,m.velocity)
                m.position=next
            var pressure_value:=maxf(0.,m.position);var rebound_value:=maxf(0.,-m.position)
            if m.mesh.get_blend_shape_value(m.pressure)!=pressure_value:m.mesh.set_blend_shape_value(m.pressure,pressure_value)
            if m.mesh.get_blend_shape_value(m.rebound)!=rebound_value:m.mesh.set_blend_shape_value(m.rebound,rebound_value)
            strokes.append({"mesh":str(m.mesh.name),"weight":m.position,"velocity":m.velocity,"maximum_world_stroke":absf(m.position)*m.max_world_stroke})
    status["bands"]=[bands.x,bands.y,bands.z];status["levels"]=[levels.x,levels.y,levels.z];status["clock"]=clock;status["playing"]=playing;status["opening"]=opening
    status["membranes"]=strokes
    status["light_floor"]=light_floor
func release()->void:
    for row in bindings:
        if is_instance_valid(row.mesh):
            for material in row.materials:
                if is_instance_valid(material.mesh):material.mesh.set_surface_override_material(material.index,material.original)
        if is_instance_valid(row.light):row.light.queue_free()
        if row.has("motion")and is_instance_valid(row.motion.mesh):
            row.motion.mesh.set_blend_shape_value(row.motion.pressure,0.);row.motion.mesh.set_blend_shape_value(row.motion.rebound,0.)
    bindings.clear()
    levels=Vector3.ZERO;light_floor=0.;illumination.clear()
