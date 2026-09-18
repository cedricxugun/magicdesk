extends RefCounted
## Guided-release geometry study; not main-App or final actuator hardware.
var asset:Node3D
var rig:Array=[]
var leaves:Array=[]
func setup(root:Node3D,rig_path:String="res://assets/collection/i_opening_rig_r15.json")->void:
    asset=root;var data:Dictionary=JSON.parse_string(FileAccess.get_file_as_string(rig_path))
    for row in data.rig:
        var node:Node3D=asset.find_child(row.name,true,false);assert(node!=null)
        var item:Dictionary=row.duplicate(true);item.node=node;item.home_transform=node.transform
        for key in ["offset","anchor","end","home_direction","release_offset"]:
            if item.has(key):item[key]=Vector3(item[key][0],item[key][1],item[key][2])
        rig.append(item)
    for row in data.leaves:
        var node:Node3D=asset.find_child(row.name,true,false);assert(node!=null);leaves.append({"node":node,"home":node.transform,"travel":float(row.travel)})
func ease_unit(value:float)->float:
    var x:=clampf(value,0.,1.);return x*x*(3.-2.*x)
func apply_time(seconds:float)->void:
    var amount:float=ease_unit((seconds-.5)/3.) if seconds<6. else 1.-ease_unit((seconds-7.)/3.)
    var release:=ease_unit(amount/.30)
    for row in rig:
        if row.kind=="release":
            row.node.transform=row.home_transform;row.node.position=row.home_transform.origin+row.offset*(ease_unit(amount/float(row.phase_end)) if row.has("phase_end") else release)
        elif row.kind=="support_envelope":
            var end:Vector3=row.end+row.release_offset*release;var vector:Vector3=end-row.anchor;var axis:=vector.normalized()
            var delta:=Quaternion(row.home_direction,axis)
            var basis:Basis=Basis(delta)*row.home_transform.basis.orthonormalized()
            row.node.position=(row.anchor+end)*.5;row.node.basis=Basis(basis.x,basis.y*(vector.length()/float(row.length)),basis.z)
        else:
            var open:float=ease_unit((amount-.30-maxi(0,int(row.order))*.05)/.45) if row.kind=="shell" else ease_unit((amount-.30)/.50)
            var axis:Vector3=Vector3.UP if row.kind=="shell" else Vector3.RIGHT
            row.node.transform=row.home_transform;row.node.basis=row.home_transform.basis*Basis(axis,float(row.angle)*open)
    var iris:float=ease_unit(seconds/.5) if seconds<7. else 1.-ease_unit((seconds-10.)/.5)
    for row in leaves:row.node.transform=row.home;row.node.basis=row.home.basis*Basis(Vector3.UP,-row.travel*iris)
