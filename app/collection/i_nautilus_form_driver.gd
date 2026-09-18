extends RefCounted
## Unlocked primary-shape study; detailed linkage solver follows shape review.
var panels:Array=[]
func bind(asset:Node3D,spec:Dictionary)->void:
    for row in spec.form_panels:
        var node:=asset.find_child(str(row.node),true,false) as Node3D;assert(node!=null)
        var axis:Vector3=Vector3(row.axis_blender[0],row.axis_blender[2],-row.axis_blender[1]).normalized()
        var lift_values:Array=row.get("lift_blender",[0.,0.,0.])
        var lift:=Vector3(lift_values[0],lift_values[2],-lift_values[1])
        var panel:Dictionary={"node":node,"rest":node.transform,"axis":axis,"angle":float(row.angle),"lift":lift,"lift_fraction":float(row.get("lift_fraction",0.))}
        if row.has("mechanism"):
            var m:Dictionary=row.mechanism
            var carriage:=asset.find_child(str(m.carriage),true,false) as Node3D
            var rotor:=asset.find_child(str(m.rotor),true,false) as Node3D
            assert(carriage!=null and rotor!=null)
            var h:Array=m.axis_local_blender
            panel["mechanism"]={"carriage":carriage,"rotor":rotor,"carriage_rest":carriage.transform,"rotor_rest":rotor.transform,"axis":Vector3(h[0],h[2],-h[1]).normalized(),"stroke":float(m.stroke)}
        panels.append(panel)
    set_opening(0.)
func set_opening(value:float)->void:
    for panel in panels:
        var pose:Transform3D=panel.rest
        var t:=clampf(value,0.,1.);var fraction:float=panel.lift_fraction
        var clear:=clampf(t/maxf(fraction,.000001),0.,1.)
        var turn:=clampf((t-fraction)/maxf(1.-fraction,.000001),0.,1.)
        pose.origin+=panel.lift*clear
        pose.basis=Basis(Quaternion(panel.axis,panel.angle*turn))*pose.basis
        panel.node.transform=pose
        if panel.has("mechanism"):
            var m:Dictionary=panel.mechanism
            var carriage_pose:Transform3D=m.carriage_rest;carriage_pose.origin+=Vector3(0,m.stroke*clear,0)
            m.carriage.transform=carriage_pose
            var rotor_pose:Transform3D=m.rotor_rest;rotor_pose.basis=Basis(Quaternion(m.axis,panel.angle*turn))*rotor_pose.basis
            m.rotor.transform=rotor_pose
