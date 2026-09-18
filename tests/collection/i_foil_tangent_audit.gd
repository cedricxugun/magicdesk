extends SceneTree
func _initialize()->void:run.call_deferred()
func run()->void:
    var folder:="res://../review/I_refinement/part_a_mouth/shutter_r2/foil_frame/"
    DirAccess.make_dir_recursive_absolute(folder)
    var spec:Dictionary=JSON.parse_string(FileAccess.get_file_as_string("res://../review/I_refinement/part_a_mouth/shutter_r2/diaphragm/build.json"))
    var asset:Node3D=load("res://"+str(spec.component).trim_prefix("app/")).instantiate();root.add_child(asset)
    var reports:Array=[]
    for group in spec.tongues:
        for name in group.mesh_names:
            var node:=asset.find_child(name,true,false) as MeshInstance3D
            var a:=node.mesh.surface_get_arrays(0)
            var p:PackedVector3Array=a[Mesh.ARRAY_VERTEX];var n:PackedVector3Array=a[Mesh.ARRAY_NORMAL]
            var uv:PackedVector2Array=a[Mesh.ARRAY_TEX_UV];var code:PackedVector2Array=a[Mesh.ARRAY_TEX_UV2]
            var tangent:PackedFloat32Array=a[Mesh.ARRAY_TANGENT]
            var grid:Dictionary={}
            for i in range(p.size()):
                var row:=roundi(code[i].x*int(group.rows)-.5)
                var v:=1.-code[i].y;var back:=1 if v>1.5 else 0
                var column:=roundi((v-back*2.)*16)
                grid[Vector3i(row,column,back)]=i
            var current_dots:Array=[];var imported_dots:Array=[];var tangent_dots:Array=[];var normal_dots:Array=[];var corrected_dots:Array=[];var legacy_imported_dots:Array=[];var shear:=0.
            var positive_v:=0;var negative_v:=0
            for key in grid:
                if key.x<2 or key.x>int(group.rows)-3 or key.y<1 or key.y>15:continue
                var i:int=grid[key];var left:int=grid[key-Vector3i(1,0,0)];var right:int=grid[key+Vector3i(1,0,0)]
                var below:int=grid[key-Vector3i(0,1,0)];var above:int=grid[key+Vector3i(0,1,0)]
                var ds:=p[right]-p[left];var dw:=p[above]-p[below]
                var us:=uv[right]-uv[left];var uw:=uv[above]-uv[below];var det:=us.x*uw.y-us.y*uw.x
                if absf(det)<.00000001 or ds.length()<.0000001 or dw.length()<.0000001:continue
                if uw.y>0.:positive_v+=1
                else:negative_v+=1
                var tu:Vector3=((ds*uw.y-dw*us.y)/det).normalized()
                var bv:Vector3=((dw*us.x-ds*uw.x)/det).normalized()
                var authored_t:=Vector3(tangent[i*4],tangent[i*4+1],tangent[i*4+2])
                var authored_b:=n[i].cross(authored_t)*tangent[i*4+3]
                var current_n:=ds.cross(dw).normalized()*(1. if key.z==0 else -1.)
                var corrected_t:Vector3=(ds-current_n*current_n.dot(ds)).normalized()
                var corrected_b:Vector3=current_n.cross(corrected_t).normalized()*tangent[i*4+3]
                corrected_dots.append(corrected_b.dot(authored_b.normalized()))
                legacy_imported_dots.append(dw.normalized().dot(authored_b.normalized()))
                current_dots.append(dw.normalized().dot(bv));imported_dots.append(authored_b.normalized().dot(bv))
                tangent_dots.append(authored_t.normalized().dot(tu));normal_dots.append(n[i].dot(current_n))
                shear=maxf(shear,absf(ds.normalized().dot(dw.normalized())))
            current_dots.sort();imported_dots.sort();tangent_dots.sort();normal_dots.sort();corrected_dots.sort();legacy_imported_dots.sort()
            reports.append({"mesh":name,"samples":current_dots.size(),"increasing_material_v":positive_v,"decreasing_material_v":negative_v,"legacy_bitangent_uv_dot_median":current_dots[current_dots.size()/2],"imported_cross_n_t_sign_uv_dot_median":imported_dots[imported_dots.size()/2],"imported_tangent_uv_dot_median":tangent_dots[tangent_dots.size()/2],"imported_vs_analytic_normal_dot_median":normal_dots[normal_dots.size()/2],"max_normalized_ds_dot_dw":shear})
            reports[-1]["orthogonal_bitangent_imported_dot_min"]=corrected_dots[0]
            reports[-1]["orthogonal_bitangent_imported_dot_median"]=corrected_dots[corrected_dots.size()/2]
            reports[-1]["legacy_bitangent_imported_dot_min"]=legacy_imported_dots[0]
    var result={"component_sha256":spec.component_sha256,"source_sha256":spec.source_sha256,"meshes":reports,"scope":"Read-only REST audit of actual Godot-imported positions/UV/normals/tangents versus material-coordinate derivatives; no art or moving-pose acceptance."}
    FileAccess.open(folder+"orthogonal_candidate.json",FileAccess.WRITE).store_string(JSON.stringify(result,"  "))
    print("I_FOIL_TANGENT_AUDIT ",JSON.stringify(reports));asset.queue_free();await process_frame;quit()
