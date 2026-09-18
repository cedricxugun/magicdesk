extends SceneTree
func _initialize()->void:
	var profile:Dictionary=JSON.parse_string(FileAccess.get_file_as_string("res://assets/collection/butterfly_seal.json"))
	var data:Dictionary=JSON.parse_string(FileAccess.get_file_as_string("res://assets/collection/models/G_optical_curator_butterfly_candidate.json"))
	var checked:=0;var maximum:=0.0
	var images:Dictionary={}
	for key in ["upper","lower"]:
		var tex:Texture2D=load(profile.wings[key].texture);var img:Image=tex.get_image()
		if img.is_compressed():img.decompress()
		images[key]=img
	for guide in data.g_archive.contents[1].butterfly.guides:
		if not guide.wing:continue
		var key:="upper" if str(guide.node).contains("Upper") else "lower";var b:Array=profile.wings[key].bounds;var img:Image=images[key]
		for p in guide.points:
			var u:float=(absf(p[0])-b[0])/b[2];var v:float=1.0-(p[1]-b[1])/b[3]
			if u<0 or v<0 or u>1 or v>1:continue
			var value:=img.get_pixel(clampi(roundi(u*(img.get_width()-1)),0,img.get_width()-1),clampi(roundi(v*(img.get_height()-1)),0,img.get_height()-1)).r
			maximum=maxf(maximum,value);checked+=1
	var report:={"passed":maximum<.05 and checked>500,"sampled_vein_points":checked,"maximum_field_at_vein":maximum,"scope":"Imported data textures aligned to actual guide points, including V orientation and grayscale sampling; not visual acceptance"}
	FileAccess.open("res://../review/G_optical_curator/butterfly_r2/runtime/seal_field_qa.json",FileAccess.WRITE).store_string(JSON.stringify(report,"  "));print("SEAL_FIELDS ",JSON.stringify(report));quit(0 if report.passed else 2)
