extends Node3D
## Isolated score-placement candidate. Final emitter hardware and effect assets remain.
var sheet:MeshInstance3D
var material:ShaderMaterial
var catalog:Dictionary
var cache:Dictionary={}
var movement:=0
var current_tiles:Array=[]
var status:Dictionary={}
func setup(asset:Node3D)->void:
    catalog=JSON.parse_string(FileAccess.get_file_as_string("res://assets/collection/art/I/moonlight_candidate/score/manifest.json"))
    var mouth:Node3D=asset.find_child("IH1_Mouth",true,false);assert(mouth!=null)
    sheet=MeshInstance3D.new();mouth.add_child(sheet);sheet.name="I_MoonlightStaffCandidate"
    var vertices:=PackedVector3Array();var uv:=PackedVector2Array();var indices:=PackedInt32Array();var segments:=32
    for y in range(2):
        for x in range(segments+1):
            var u:=float(x)/segments
            vertices.append(Vector3((.5-u)*1.62,-.24-.10*sin(PI*u),(float(y)-.5)*.77));uv.append(Vector2(u,float(y)))
    for x in range(segments):indices.append_array([x,x+1,x+segments+2,x,x+segments+2,x+segments+1])
    var arrays:Array=[];arrays.resize(Mesh.ARRAY_MAX);arrays[Mesh.ARRAY_VERTEX]=vertices;arrays[Mesh.ARRAY_TEX_UV]=uv;arrays[Mesh.ARRAY_INDEX]=indices
    var mesh:=ArrayMesh.new();mesh.add_surface_from_arrays(Mesh.PRIMITIVE_TRIANGLES,arrays);sheet.mesh=mesh
    material=ShaderMaterial.new();material.shader=load("res://collection/i_staff_projection.gdshader");sheet.material_override=material;sheet.cast_shadow=GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
func _texture(path:String)->Texture2D:
    if not cache.has(path):cache[path]=load(path)
    return cache[path]
func set_score_position(movement_number:int,quarter:float,visibility:float=1.)->void:
    var row:Dictionary=catalog.movements[movement_number-1];var anchors:Array=row.anchors
    var lo:=0;var hi:=anchors.size()-1
    while lo+1<hi:
        var mid:=(lo+hi)/2
        if float(anchors[mid].quarter)<=quarter:lo=mid
        else:hi=mid
    var a:Dictionary=anchors[lo];var b:Dictionary=anchors[hi]
    var mix_amount:=clampf((quarter-float(a.quarter))/maxf(.000001,float(b.quarter)-float(a.quarter)),0.,1.)
    var note_x:=lerpf(float(a.x),float(b.x),mix_amount)
    var width:float=float(row.height)*2.10;var offset:=clampf(note_x-width*.35,0.,maxf(0.,float(row.width)-width));var start_tile:=int(floor(offset/float(row.tile_width)))
    var wanted:Array=[]
    for n in range(3):
        var index:=mini(start_tile+n,row.tiles.size()-1);var path:String=row.tiles[index];wanted.append(path)
        material.set_shader_parameter("page_"+str(n),_texture(path))
    for path in cache.keys():
        if not wanted.has(path):cache.erase(path)
    current_tiles=wanted;movement=movement_number
    material.set_shader_parameter("offset_in_tile",offset-start_tile*float(row.tile_width));material.set_shader_parameter("window_width",width);material.set_shader_parameter("tile_width",row.tile_width)
    material.set_shader_parameter("opacity",clampf(visibility,0.,1.)*.85);material.set_shader_parameter("playhead",clampf((note_x-offset)/width,0.,1.));sheet.visible=visibility>.001
    status={"movement":movement_number,"score_quarter":quarter,"window_x":offset,"window_width":width,"first_tile":start_tile,"texture_cache":cache.size(),"scope":"Real score placement candidate; synchronous tile loads and estimated audio alignment are not final performance/sync acceptance."}
func _exit_tree()->void:
    if is_instance_valid(sheet):sheet.queue_free()
