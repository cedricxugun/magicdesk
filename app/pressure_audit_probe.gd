extends SceneTree
func _initialize()->void:
	var texture=load("res://assets/pressure_noise.tres")
	print("PRESSURE_NOISE fractal_type=",texture.noise.fractal_type," octaves=",texture.noise.fractal_octaves," frequency=",texture.noise.frequency," gain=",texture.noise.fractal_gain," lacunarity=",texture.noise.fractal_lacunarity)
	quit()
