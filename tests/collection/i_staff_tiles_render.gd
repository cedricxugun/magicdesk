extends SceneTree
func _initialize()->void:
    var manifest:Dictionary=JSON.parse_string(FileAccess.get_file_as_string("res://../production/I_refinement/moonlight/tiles/manifest.json"))
    var rows:Array=[];var failures:Array=[]
    for movement in manifest.movements:
        var output:="res://assets/collection/art/I/moonlight_candidate/score/m"+str(movement.movement)+"/"
        DirAccess.make_dir_recursive_absolute(output);var paths:Array=[]
        for source in movement.tiles:
            var image:=Image.new();var error:=image.load_svg_from_string(FileAccess.get_file_as_string("res://../"+str(source)))
            var dest:String=output+str(source).get_file().get_basename()+".png"
            if error!=OK:failures.append(source)
            else:
                var result:=image.save_png(dest)
                if result!=OK:failures.append(dest)
                paths.append(dest)
        var row:Dictionary=movement.duplicate(true);row.tiles=paths;rows.append(row)
        print("I_STAFF_TILES_RENDER ",movement.movement," ",paths.size())
    FileAccess.open("res://assets/collection/art/I/moonlight_candidate/score/manifest.json",FileAccess.WRITE).store_string(JSON.stringify({"movements":rows,"failures":failures},"  "))
    quit(0 if failures.is_empty() else 1)
