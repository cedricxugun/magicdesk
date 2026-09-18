extends RefCounted
## Isolated normal-operation restoration. No maintenance or main-App binding.
var asset:Node3D
var rows:Array=[]
var leaves:Array=[]
var cam:Node3D
var cam_home:Transform3D
func setup(root:Node3D)->void:
    asset=root
    var rig:Dictionary=JSON.parse_string(FileAccess.get_file_as_string("res://assets/collection/i_restore_rig_r9.json"))
    for row in rig.panels:
        var node:Node3D=asset.find_child(row.name,true,false)
        assert(node!=null)
        var links:Array=[]
        for name in row.links:
            var link:Node3D=asset.find_child(name,true,false);assert(link!=null)
            links.append({"node":link,"home":link.transform})
        rows.append({"node":node,"home":node.transform,"axis":Vector3(row.axis[0],row.axis[1],row.axis[2]),"drive":Vector3(row.drive[0],row.drive[1],row.drive[2]),"angle":float(row.angle),"links":links})
    for i in range(6):
        var leaf:Node3D=asset.find_child("IH1_IrisLeaf"+str(i),true,false);assert(leaf!=null)
        leaves.append({"node":leaf,"home":leaf.transform})
    cam=asset.find_child("IH1_IrisCamDrive",true,false);cam_home=cam.transform
func smooth_unit(value:float)->float:
    var t:=clampf(value,0.,1.);return t*t*(3.-2.*t)
func apply(progress:float,iris:float)->void:
    for i in range(rows.size()):
        var row:Dictionary=rows[i];var amount:=smooth_unit((progress-i*.09)/.55)
        var q:=Quaternion(row.axis,row.angle*amount)
        row.node.transform=row.home;row.node.position=row.home.origin+q*row.drive-row.drive
        for link in row.links:link.node.transform=link.home;link.node.basis=link.home.basis*Basis(q)
    for leaf in leaves:leaf.node.transform=leaf.home;leaf.node.basis=leaf.home.basis*Basis(Vector3.UP,-1.05*iris)
    cam.transform=cam_home;cam.basis=cam_home.basis*Basis(Vector3.UP,-.30*iris)
func apply_reference_time(seconds:float)->void:
    var progress:float=smooth_unit((seconds-.5)/2.) if seconds<5. else 1.-smooth_unit((seconds-5.5)/2.)
    var iris:float=smooth_unit(seconds/.5) if seconds<5.5 else 1.-smooth_unit((seconds-7.5)/.5)
    apply(progress,iris)
