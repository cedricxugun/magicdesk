extends SceneTree
func _initialize()->void:
    var errors:Array=[]
    for i in range(1,4):
        var base:="res://../review/I_refinement/moonlight/movement"+str(i)+"_first_bars"
        var image:=Image.new();var result:=image.load_svg_from_string(FileAccess.get_file_as_string(base+".svg"))
        if result!=OK:errors.append({"movement":i,"error":result})
        else:image.save_png(base+".png")
    print("I_NOTATION_RENDER ",errors);quit(0 if errors.is_empty() else 1)
