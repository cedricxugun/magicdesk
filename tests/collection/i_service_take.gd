extends SceneTree
func _initialize()->void:
    var sim:RefCounted=load("res://collection/i_acoustics.gd").new()
    var service:RefCounted=load("res://collection/i_service.gd").new()
    var rows:Array=[];var opening:=0.
    for frame in range(1000):
        if frame==8:service.request_operation(sim);sim.set_controls(.72,.8)
        if frame==45:sim.set_pressed(true)
        if frame==90:sim.set_pressed(false)
        if frame==95:service.request_service(sim)
        if frame==355:service.request_operation(sim)
        if frame==505:sim.set_pressed(true)
        if frame==525:service.request_service(sim)
        if frame==595:service.request_operation(sim)
        if frame==645:service.request_service(sim)
        if frame==815:service.request_stow(sim)
        sim.tick(1./30.);service.tick(1./30.,sim,opening)
        var target:float=1. if sim.listening and service.amount==0. else 0. if sim.ready_to_close() else opening
        opening=move_toward(opening,target,2./30.)
        rows.append({"frame":frame+1,"time":sim.clock,"opening":opening,"state":sim.state(),"service":service.state(),"events":sim.drain_events()})
    var out:="res://../review/I_refinement/service_r4/";DirAccess.make_dir_recursive_absolute(out)
    FileAccess.open(out+"take.json",FileAccess.WRITE).store_string(JSON.stringify({"fps":30,"samples":rows,"scope":"Pressure/optics recovery followed by reversible service state. Source motion and geometry review pending."},""))
    print("I_SERVICE_TAKE ",rows.size());quit()
