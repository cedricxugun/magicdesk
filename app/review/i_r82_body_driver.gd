extends RefCounted
## R82 authored slide-then-turn mechanism. No replacement of the legacy driver.
var bindings:Array=[]
var opening:=0.
var motion_profile:="r82"
var duration:=114./30.
func vec(v:Array)->Vector3:return Vector3(float(v[0]),float(v[2]),-float(v[1]))
func _source_curve(v:float)->float:
    v=clampf(v,0.,1.)
    return v*v*v*(v*(v*6.-15.)+10.)
func bind(asset:Node3D,spec:Dictionary)->bool:
    bindings.clear()
    motion_profile=str(spec.get("motion_profile","r82"))
    duration=107./30. if motion_profile=="outer_edge_r85" else 114./30.
    for i in range(spec.panels.size()):
        var p:Dictionary=spec.panels[i]
        var j:Dictionary=spec.joints[i]
        var node:=asset.find_child(str(p.node),true,false) as Node3D
        var car:=asset.find_child(str(j.carriage),true,false) as Node3D
        var latch:=asset.find_child(str(j.latch),true,false) as Node3D
        if node==null or car==null or latch==null:
            push_error("Incomplete R82 mechanism export: "+str(p.node)+" / "+str(j.carriage)+" / "+str(j.latch))
            return false
        var row:Dictionary={"id":int(p.id),"node":node,"carriage":car,"latch":latch,"rest":node.transform,"carriage_rest":car.transform,"latch_rest":latch.transform,"axis":vec(p.axis).normalized(),"translation":vec(p.translation),"angle":float(p.angle),"extensions":[]}
        row.latch_axis=vec(p.get("latch_axis",p.axis)).normalized()
        for part in j.get("extension_nodes",[]):
            var extension:=asset.find_child(str(part.node),true,false) as Node3D
            if extension==null:
                push_error("Missing telescopic stage: "+str(part.node));return false
            row.extensions.append({"node":extension,"rest":extension.transform,"fraction":float(part.fraction)})
        bindings.append(row)
    set_opening(0.)
    return bindings.size()==6
func set_opening(value:float)->void:
    opening=clampf(value,0.,1.)
    var frame:=1.+opening*114.
    var unlock:=_source_curve((frame-8.)/16.)
    if motion_profile=="outer_edge_r85":
        frame=68.+opening*107.
        unlock=_source_curve((frame-68.)/16.)
    for p in bindings:
        var t:=clampf((frame-25.-float(p.id-1)*1.5)/82.,0.,1.)
        var split:=.30
        if motion_profile=="outer_edge_r85":
            t=clampf((frame-85.)/90.,0.,1.);split=.25
        var clear:=_source_curve(t/split)
        var turn:=_source_curve((t-split)/(1.-split))
        var transform:Transform3D=p.rest
        transform.origin+=p.translation*clear
        transform.basis=Basis(Quaternion(p.axis,p.angle*turn))*transform.basis
        p.node.transform=transform
        var carriage:Transform3D=p.carriage_rest
        carriage.origin+=p.translation*clear
        p.carriage.transform=carriage
        for extension in p.extensions:
            var stage:Transform3D=extension.rest
            stage.origin+=p.translation*clear*extension.fraction
            extension.node.transform=stage
        var latch:Transform3D=p.latch_rest
        latch.basis=Basis(Quaternion(p.latch_axis,.70*unlock))*latch.basis
        p.latch.transform=latch
func snapshot()->Dictionary:
    var rows:Array=[]
    for p in bindings:
        rows.append({"id":p.id,"position":p.node.position,"carriage_position":p.carriage.position,"basis":p.node.basis})
    return {"opening":opening,"panels":rows}
