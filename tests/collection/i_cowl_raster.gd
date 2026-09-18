extends RefCounted
## Diagnostic only: preserve actual imported arrays/materials, vary LOD/proxy use.
static func apply(asset:Node3D,mode:String)->Array:
    var records:Array=[]
    for node in asset.find_children("*","MeshInstance3D",true,false):
        var name:String=str(node.name)
        if not (name.begins_with("IN1_PorcelainPanel_") or name.begins_with("IN1_FixedRearShell_") or name=="IN1_FixedMouthCheek05"):continue
        var original:=node.mesh as ArrayMesh
        if original==null:continue
        var replacement:ArrayMesh
        if mode=="no-shadow":
            replacement=original.duplicate() as ArrayMesh
            replacement.shadow_mesh=null
        else:
            replacement=ArrayMesh.new()
            assert(original.get_blend_shape_count()==0)
            for surface in range(original.get_surface_count()):
                var arrays:Array=original.surface_get_arrays(surface)
                replacement.add_surface_from_arrays(original.surface_get_primitive_type(surface),arrays)
                replacement.surface_set_material(surface,original.surface_get_material(surface))
                assert(replacement.surface_get_array_len(surface)==original.surface_get_array_len(surface))
                assert(replacement.surface_get_array_index_len(surface)==original.surface_get_array_index_len(surface))
            if mode=="no-lod":replacement.shadow_mesh=original.shadow_mesh
        node.mesh=replacement
        var formats:Array=[]
        var compressed:Array=[]
        for surface in range(original.get_surface_count()):
            formats.append(original.surface_get_format(surface))
            compressed.append(bool(original.surface_get_format(surface)&Mesh.ARRAY_FLAG_COMPRESS_ATTRIBUTES))
        records.append({"mesh":name,"surfaces":original.get_surface_count(),"surface_formats":formats,"compressed_attributes":compressed,"mode":mode,"original_shadow_proxy":original.shadow_mesh!=null,"new_shadow_proxy":replacement.shadow_mesh!=null})
    return records
