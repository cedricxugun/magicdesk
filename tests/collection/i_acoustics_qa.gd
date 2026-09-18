extends SceneTree
const Acoustics=preload("res://collection/i_acoustics.gd")
var checks:Array=[]
func _initialize()->void:run.call_deferred()
func check(label:String,ok:bool,detail:Variant=null)->void:checks.append({"label":label,"passed":ok,"detail":detail})
func advance(a:RefCounted,seconds:float)->Array:
	var events:Array=[]
	for i in range(roundi(seconds*120.)):
		a.tick(1./120.);events.append_array(a.drain_events())
	return events
func run()->void:
	var a:RefCounted=Acoustics.new();a.set_controls(.72,.8);a.set_pressed(true)
	var charge:Array=advance(a,1.5)
	check("charge_without_premature_wave",a.pressure>1.3 and a.compression>.9 and charge.is_empty(),a.state())
	a.set_pressed(false);var released:Array=advance(a,2.)
	var outgoing:Array=released.filter(func(e):return e.kind=="outgoing");var returns:Array=released.filter(func(e):return e.kind=="return")
	check("one_release_one_delayed_return",outgoing.size()==1 and returns.size()==1,released)
	if outgoing.size()==1 and returns.size()==1:check("return_later_and_weaker",returns[0].time-outgoing[0].time>.45 and returns[0].gain<outgoing[0].gain)
	a.set_pressed(true);advance(a,1.);a.set_pressed(false);advance(a,.25);a.quiet();var after_cancel:Array=advance(a,3.)
	check("quiet_cancels_future_echo_and_settles",after_cancel.is_empty() and a.ready_to_close(),a.state())
	a.set_controls(.2,0.);a.set_pressed(true);advance(a,1.);a.set_pressed(false)
	check("closed_throat_does_not_emit",advance(a,2.).is_empty())
	var gains:Array=[]
	for tuning in [.05,.72]:
		var b:RefCounted=Acoustics.new();b.set_controls(tuning,.8);b.set_pressed(true);advance(b,1.5);b.set_pressed(false)
		var echoes:Array=advance(b,2.).filter(func(e):return e.kind=="return");gains.append(echoes[0].gain if not echoes.is_empty() else 0.)
	check("tuning_changes_return_strength",gains[1]>gains[0]*2.,gains)
	var report:={"passed":checks.all(func(c):return c.passed),"checks":checks,"scope":"Normalized pneumatic state and sonification scheduler only. Not yet connected to model/sound/VFX; not full acoustics."}
	DirAccess.make_dir_recursive_absolute("res://../review/I_refinement/r2")
	FileAccess.open("res://../review/I_refinement/r2/acoustics_qa.json",FileAccess.WRITE).store_string(JSON.stringify(report,"  "));print("I_ACOUSTICS_QA ",JSON.stringify(report));quit(0 if report.passed else 1)
