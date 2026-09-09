extends SceneTree
## The native variable delta found a missed 99.996% completion endpoint.
## Reproduce with both adversarial residuals and realistic frame-time jitter.
func _initialize()->void:run.call_deferred()
func run()->void:
	var controller=load("res://collection/g_instrument.gd")
	var checks:Array=[]
	for residue in [.9989,.99901,.99996,.9999999]:
		var m:=Node3D.new();var play:=RefCounted.new()
		# Use the real module to preserve its typed property contract.
		m.free();m=load("res://collection/module.gd").new()
		m.play=load("res://collection/play_state.gd").new();m.play.values={"imprint":1.0}
		m.openness=1;m.open_target=1;m.power=1
		var instrument:RefCounted=controller.new();instrument.setup(m);instrument.records[0]=residue;instrument.alignment=1;instrument.pins=1
		for i in range(40):instrument.tick([.0141,.0232,.0178,.0127][i%4])
		checks.append({"start":residue,"finished":instrument.records[0],"peaks":instrument.peak_count,"passed":instrument.records[0]==1.0 and instrument.peak_count==1})
		m.free()
	var ok:bool=checks.all(func(c):return c.passed)
	FileAccess.open("res://../review/G_complete/endpoint_qa.json",FileAccess.WRITE).store_string(JSON.stringify({"all_passed":ok,"checks":checks},"  "))
	print("G_ENDPOINT ",ok);quit(0 if ok else 2)
