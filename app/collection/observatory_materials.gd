extends RefCounted
static func apply(materials:Array)->int:
	return load("res://collection/finish_profile.gd").apply(materials,"res://assets/collection/observatory_materials.json","observatory_finish")
