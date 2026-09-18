extends SceneTree
func _initialize()->void:
    print("CAPTURE_FEATURE movie=",OS.has_feature("movie")," args=",OS.get_cmdline_args())
    for row in Engine.get_method_list():
        if "movie" in str(row.name):print("CAPTURE_ENGINE_METHOD ",row.name)
    quit()
