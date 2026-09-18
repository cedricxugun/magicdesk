extends RefCounted
## Geometry/space study only; not bound to main I or music.
var asset:Node3D
var rig:Array=[]
var leaves:Array=[]
func setup(root:Node3D)->void:
    asset=root;var data:Dictionary=JSON.parse_string(FileAccess.get_file_as_string("res://assets/collection/i_opening_rig_r14.json"))
    for row in data.rig:
        var node:Node3D=asset.find_child(row.name,true,false);assert(node!=null)
        rig.append({"node":node,"home":node.transform,"angle":float(row.angle),"order":int(row.order),"kind":row.kind})
    for row in data.leaves:
        var node:Node3D=asset.find_child(row.name,true,false);assert(node!=null)
        leaves.append({"node":node,"home":node.transform,"travel":float(row.travel)})
func ease_unit(value:float)->float:
    var x:=clampf(value,0.,1.);return x*x*(3.-2.*x)
func apply_time(seconds:float)->void:
    var amount:float=ease_unit((seconds-.5)/3.) if seconds<6. else 1.-ease_unit((seconds-7.)/3.)
    for row in rig:
        var open:float=ease_unit((amount-maxi(0,row.order)*.065)/.675) if row.kind=="shell" else ease_unit(amount/.40)
        var axis:Vector3=Vector3.UP if row.kind=="shell" else Vector3.RIGHT
        row.node.transform=row.home;row.node.basis=row.home.basis*Basis(axis,row.angle*open)
    var iris:float=ease_unit(seconds/.5) if seconds<7. else 1.-ease_unit((seconds-10.)/.5)
    for row in leaves:row.node.transform=row.home;row.node.basis=row.home.basis*Basis(Vector3.UP,-row.travel*iris)
