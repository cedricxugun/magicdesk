extends RefCounted
static func apply(asset:Node3D,path:String)->Dictionary:
    var profile:Dictionary=JSON.parse_string(FileAccess.get_file_as_string(path));var counts:Dictionary={}
    for node in asset.find_children("*","MeshInstance3D",true,false):
        for surface in range(node.mesh.get_surface_count()):
            var original:=node.get_active_material(surface)as BaseMaterial3D
            if original==null:continue
            var name:String=original.resource_name.get_slice(".",0)
            if not profile.materials.has(name):continue
            var row:Dictionary=profile.materials[name];var material:=original.duplicate()as BaseMaterial3D;var c:Array=row.color_linear
            material.albedo_color=Color(c[0],c[1],c[2],original.albedo_color.a).linear_to_srgb();material.metallic=float(row.metallic);material.roughness=float(row.roughness)
            if row.has("coat"):
                material.clearcoat_enabled=true;material.clearcoat=float(row.coat);material.clearcoat_roughness=float(row.coat_roughness)
            if bool(row.get("brushing",false)):
                material.set_meta("chamber_brushing_texture",str(profile.brushing_texture));material.set_meta("chamber_brushing_center",float(profile.brushing_center));material.set_meta("chamber_brushing_strength",float(profile.brushing_strength))
            node.set_surface_override_material(surface,material);counts[name]=int(counts.get(name,0))+1
    assert(counts.has("IN1_Porcelain")and counts.has("IN1_FoldedDiaphragm")and counts.has("IN1_AcousticBronze"))
    return {"profile":path,"profile_sha256":FileAccess.get_sha256(path),"material_surface_counts":counts,"scope":"Body instance material copies only; source/base/mouth resources not edited."}
