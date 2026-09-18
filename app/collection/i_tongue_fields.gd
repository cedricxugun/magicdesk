extends RefCounted
var materials:Array[ShaderMaterial]=[]
var carriage:Node3D
var spool:Node3D
var guide_rotor:Node3D
var spec:Dictionary
var receipts:Dictionary={}
func _reference_point(row:int,w:float,offset:float,centers:PackedVector4Array,widths:PackedVector3Array,normals:PackedVector3Array)->Vector3:
    var c:=centers[row]
    return Vector3(c.x,c.y,c.z)+widths[row]*(.5-w)+normals[row]*((c.w-1.)*sin(PI*w)+offset)
func bind(asset:Node3D,data:Dictionary,keep_imported_mesh_for_audit:bool=false)->void:
    spec=data;carriage=asset.find_child(spec.carriage,true,false);spool=asset.find_child(spec.spool,true,false)
    guide_rotor=null
    if spec.has("guide_roll"):
        guide_rotor=asset.find_child(str(spec.guide_roll.rotor),true,false)
        assert(guide_rotor!=null,"Missing authored guide roller")
    var textures:Dictionary={}
    for key in ["center","width","normal"]:textures[key]=load("res://"+str(spec.motion_textures[key]).trim_prefix("app/"))
    var hashes:Dictionary={}
    for key in textures:
        var numeric:Image=textures[key].get_image();numeric.convert(Image.FORMAT_RGBAF)
        var hash:=HashingContext.new();hash.start(HashingContext.HASH_SHA256);hash.update(numeric.get_data());hashes[key]=hash.finish().hex_encode()
        assert(hashes[key]==spec.field_pixel_sha256[key],"Imported motion field bytes differ: "+str(key))
    var im:Image=textures.center.get_image();assert(im.get_width()==int(spec.rows) and im.get_height()==int(spec.pose_steps)+1)
    var first:Color=im.get_pixel(180,0);var last:Color=im.get_pixel(180,im.get_height()-1)
    var expected:Array=spec.field_sample_front_center
    var first_error:=Vector4(first.r,first.g,first.b,first.a).distance_to(Vector4(expected[0],expected[1],expected[2],expected[3]))
    var last_error:=Vector4(last.r,last.g,last.b,last.a).distance_to(Vector4(expected[0],expected[1],expected[2],expected[3]))
    var flip:bool=last_error<first_error;assert(minf(first_error,last_error)<0.00001,"Motion field import changed numeric data")
    var reference_centers:=PackedVector4Array();var reference_widths:=PackedVector3Array();var reference_normals:=PackedVector3Array()
    var width_image:Image=textures.width.get_image();var normal_image:Image=textures.normal.get_image()
    var reference_row:int=im.get_height()-1 if flip else 0
    for row in range(int(spec.rows)):
        var c:=im.get_pixel(row,reference_row);var w:=width_image.get_pixel(row,reference_row);var n:=normal_image.get_pixel(row,reference_row)
        reference_centers.append(Vector4(c.r,c.g,c.b,c.a));reference_widths.append(Vector3(w.r,w.g,w.b));reference_normals.append(Vector3(n.r,n.g,n.b))
    var uv_flip:=true;var counts:Array=[];var rendered:Array=[];var rest_errors:Array=[]
    for i in range(spec.mesh_names.size()):
        var mesh_node:=asset.find_child(spec.mesh_names[i],true,false) as MeshInstance3D;assert(mesh_node!=null)
        assert(mesh_node.mesh.get_blend_shape_count()==0,"Runtime should use compact motion fields")
        var arrays:Array=mesh_node.mesh.surface_get_arrays(0);var uv:PackedVector2Array=arrays[Mesh.ARRAY_TEX_UV2];assert(not uv.is_empty(),"Missing authored row coordinates")
        var min_v:=10.
        for value in uv:min_v=minf(min_v,value.y)
        uv_flip=min_v<-.5
        var centers:Image=textures.center.get_image();var widths:Image=textures.width.get_image();var normals:Image=textures.normal.get_image();var positions:PackedVector3Array=arrays[Mesh.ARRAY_VERTEX];var rest_error:=0.
        var rest_tangents:=PackedFloat32Array();var rest_normals:=PackedFloat32Array()
        var imported_tangents:PackedFloat32Array=arrays[Mesh.ARRAY_TANGENT]
        assert(imported_tangents.size()==positions.size()*4,"Authored finish requires imported tangent handedness")
        var row_y:int=centers.get_height()-1 if flip else 0
        for j in range(positions.size()):
            var row_x:int=clampi(roundi(uv[j].x*float(spec.rows)-.5),0,int(spec.rows)-1)
            var code:float=1.-uv[j].y if uv_flip else uv[j].y;var back:float=1. if code>1.5 else 0.;var across:float=clampf(code-2.*back,0.,1.)
            var c:Color=centers.get_pixel(row_x,row_y);var wd:Color=widths.get_pixel(row_x,row_y);var no:Color=normals.get_pixel(row_x,row_y)
            var expected_position:=Vector3(c.r,c.g,c.b)+Vector3(wd.r,wd.g,wd.b)*(.5-across)+Vector3(no.r,no.g,no.b)*((c.a-1.)*sin(PI*across)+float(i)*.0036+(back-.5)*.0015)
            rest_error=maxf(rest_error,expected_position.distance_to(positions[j]))
            var offset:=float(i)*.0036+(back-.5)*.0015
            var ds:=_reference_point(mini(row_x+1,int(spec.rows)-1),across,offset,reference_centers,reference_widths,reference_normals)-_reference_point(maxi(row_x-1,0),across,offset,reference_centers,reference_widths,reference_normals)
            var dw:Vector3=-reference_widths[row_x]+reference_normals[row_x]*(reference_centers[row_x].w-1.)*PI*cos(PI*across)
            var rn:Vector3=ds.cross(dw).normalized()*(1.-2.*back)
            var rt:Vector3=(ds-rn*rn.dot(ds)).normalized()
            rest_tangents.append_array(PackedFloat32Array([rt.x,rt.y,rt.z,imported_tangents[j*4+3]]))
            rest_normals.append_array(PackedFloat32Array([rn.x,rn.y,rn.z]))
        assert(rest_error<.00001,"Row data does not reconstruct the authored REST mesh")
        rest_errors.append(rest_error)
        var original:=mesh_node.mesh.surface_get_material(0) as StandardMaterial3D;assert(original!=null)
        # Rest-pose decimation is not valid for a foil that later bends around small rollers.
        # Keep the authored indices and numeric row attributes, with no generated LOD/shadow mesh.
        if not keep_imported_mesh_for_audit:
            # Carry the imported edge normals/tangent frame along the deformation;
            # replacing them with the sheet normal erases the authored edge finish.
            arrays[Mesh.ARRAY_CUSTOM0]=rest_tangents;arrays[Mesh.ARRAY_CUSTOM1]=rest_normals
            var flags: int=(Mesh.ARRAY_CUSTOM_RGBA_FLOAT<<Mesh.ARRAY_FORMAT_CUSTOM0_SHIFT)|(Mesh.ARRAY_CUSTOM_RGB_FLOAT<<Mesh.ARRAY_FORMAT_CUSTOM1_SHIFT)
            var full_mesh:=ArrayMesh.new();full_mesh.add_surface_from_arrays(Mesh.PRIMITIVE_TRIANGLES,arrays,[],{},flags)
            assert(full_mesh.get_surface_count()==1,"Rest-frame custom arrays must preserve a valid foil surface")
            assert(full_mesh.surface_get_array_len(0)==positions.size() and full_mesh.surface_get_array_index_len(0)==arrays[Mesh.ARRAY_INDEX].size(),"Adding rest frames must not change foil topology")
            full_mesh.surface_set_material(0,original);mesh_node.mesh=full_mesh
        rendered.append({"indices":mesh_node.mesh.surface_get_array_index_len(0),"vertices":mesh_node.mesh.surface_get_array_len(0),"shadow_mesh":mesh_node.mesh.shadow_mesh!=null,"full_authored_topology":not keep_imported_mesh_for_audit})
        var material:=ShaderMaterial.new();material.shader=load("res://collection/i_tongue_fields.gdshader")
        material.set_shader_parameter("preserve_authored_frame",not keep_imported_mesh_for_audit)
        material.set_shader_parameter("center_field",textures.center);material.set_shader_parameter("width_field",textures.width);material.set_shader_parameter("normal_field",textures.normal)
        material.set_shader_parameter("row_count",float(spec.rows));material.set_shader_parameter("frame_count",float(spec.pose_steps)+1.)
        material.set_shader_parameter("field_v_flipped",flip);material.set_shader_parameter("data_v_flipped",uv_flip);material.set_shader_parameter("skin_offset",float(i)*.0036)
        material.set_shader_parameter("base_color",original.albedo_color);material.set_shader_parameter("metalness",original.metallic);material.set_shader_parameter("roughness_factor",original.roughness)
        if original.roughness_texture:
            material.set_shader_parameter("roughness_map",original.roughness_texture)
            var channel:=Vector4.ZERO
            if int(original.roughness_texture_channel)<4:channel[int(original.roughness_texture_channel)]=1.
            else:channel=Vector4(.333333,.333333,.333333,0.)
            material.set_shader_parameter("roughness_channel",channel)
        if original.normal_enabled and original.normal_texture:
            material.set_shader_parameter("finish_normal",original.normal_texture);material.set_shader_parameter("finish_normal_strength",original.normal_scale)
        else:material.set_shader_parameter("finish_normal_strength",0.)
        mesh_node.material_override=material;mesh_node.extra_cull_margin=.15;materials.append(material);counts.append(arrays[Mesh.ARRAY_VERTEX].size())
    receipts={"field_format":im.get_format(),"field_size":[im.get_width(),im.get_height()],"field_v_flipped":flip,"data_v_flipped":uv_flip,"field_sample_error":minf(first_error,last_error),"field_pixel_sha256":hashes,"vertices":counts,"rest_vertex_errors":rest_errors,"rendered_meshes":rendered}
    set_feed(0.)
func set_feed(amount:float)->void:
    amount=clampf(amount,0.,1.)
    for material in materials:material.set_shader_parameter("feed",amount)
    var k:=amount*float(spec.pose_steps);var a:Dictionary=spec.states[int(floorf(k))];var b:Dictionary=spec.states[int(ceilf(k))];var f:=k-floorf(k);var p:Array=a.axis;var q:Array=b.axis
    carriage.position=Vector3(p[0],p[2],-p[1]).lerp(Vector3(q[0],q[2],-q[1]),f);spool.basis=Basis(Vector3.UP,float(spec.spin_sign)*lerpf(float(a.angle),float(b.angle),f))
    if guide_rotor:
        var guide:Dictionary=spec.guide_roll
        guide_rotor.basis=Basis(Vector3.UP,float(guide.spin_sign)*float(guide.travel)*amount/float(guide.radius))
