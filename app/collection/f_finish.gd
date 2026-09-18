extends RefCounted
## Opt-in F finish specification. Geometry and authored texture UVs stay intact.
var profile:Dictionary={}
func setup(path:String)->void:
	profile=JSON.parse_string(FileAccess.get_file_as_string(path))
func key_for(node:Node,source:String)->String:
	var ancestry:="";var parent:Node=node
	while parent!=null:
		ancestry+="/"+str(parent.name);parent=parent.get_parent()
	for rule in profile.get("rules",[]):
		if rule.source!=source:continue
		for token in rule.ancestors:
			if ancestry.contains(str(token)):return rule.finish
	return str(profile.get("defaults",{}).get(source,""))
func apply(material:ShaderMaterial,key:String)->void:
	for parameter in profile.get("finishes",{}).get(key,{}):
		material.set_shader_parameter(parameter,profile.finishes[key][parameter])
	material.set_meta("f_finish",key)
