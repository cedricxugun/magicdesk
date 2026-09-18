extends SceneTree
func _initialize()->void:run.call_deferred()
func run()->void:
    var directory:="res://../review/I_refinement/part_a_mouth/shutter_r2/diaphragm/"
    var spec:Dictionary=JSON.parse_string(FileAccess.get_file_as_string(directory+"build.json"))
    var profile:Dictionary=JSON.parse_string(FileAccess.get_file_as_string("res://assets/collection/art/I/diaphragm/aperture_profile.json"))
    var engine=load("res://collection/i_acoustics.gd").new()
    var historical:float=engine.effective_aperture_area(0.)
    engine.bind_measured_aperture(profile,spec.component_sha256)
    assert(engine.effective_aperture_area(0.)>.6 and engine.effective_aperture_area(0.)<.7)
    assert(engine.effective_aperture_area(1.)>.999)
    # The authored early steering slightly reduces the opening first. Preserve
    # that measurement instead of forcing a false monotonic actuator curve.
    assert(engine.effective_aperture_area(.09375)<engine.effective_aperture_area(0.))
    var events:Array=[]
    engine.set_controls(.8,.75);engine.start();engine.set_pressed(true)
    for frame in range(60):engine.tick(1./60.)
    engine.set_pressed(false)
    for frame in range(180):
        engine.tick(1./60.);events.append_array(engine.drain_events())
    assert(engine.outgoing_count==1 and engine.echo_count==1)
    engine.quiet()
    for frame in range(300):engine.tick(1./60.)
    assert(engine.ready_to_close())
    FileAccess.open(directory+"measured_acoustics_qa.json",FileAccess.WRITE).store_string(JSON.stringify({"source_sha256":spec.source_sha256,"component_sha256":spec.component_sha256,"passed":true,"historical_closed_area":historical,"measured_closed_area":engine.effective_aperture_area(0.),"events":events,"ready_to_close":engine.ready_to_close(),"scope":"Independent reservoir/sonification event engine using measured projected three-tongue aperture. Historical formula retained only for unbound legacy modules. No audio or full native interaction acceptance."},"  "))
    print("I_MEASURED_APERTURE_QA true");quit()
