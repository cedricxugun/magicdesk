extends RefCounted
## Service motion waits for actual pressure/optics recovery and reverses in place.
var amount:=0.
var requested:="rest"
var phase:="rest"
var rig:Dictionary={}
var groups:Array=[]
func setup(asset:Node3D,rig_path:String="res://assets/collection/i_service_rig.json")->void:
    rig=JSON.parse_string(FileAccess.get_file_as_string(rig_path))
    for item in rig.groups:
        var node:Node3D=asset.find_child(item.name,true,false)
        assert(node!=null,"Missing I service group "+str(item.name))
        groups.append({"node":node,"home":node.transform,"route":item.route})
func request_service(sim:RefCounted)->void:
    requested="service";sim.quiet()
func request_stow(sim:RefCounted)->void:
    requested="rest";sim.quiet()
func request_operation(sim:RefCounted)->void:
    requested="operate"
    if amount>.0001:sim.quiet()
    else:sim.start()
func tick(delta:float,sim:RefCounted,opening:float)->void:
    if requested=="service":
        if not sim.ready_to_close():phase="depressurize";return
        if opening>.0001:phase="fold";return
        amount=move_toward(amount,1.,delta*.22);phase="service" if amount>=1. else "extract"
    elif amount>0.:
        amount=move_toward(amount,0.,delta*.25);phase="reassemble"
        if amount==0. and requested=="operate":sim.start()
    else:phase="operate" if requested=="operate" else "depressurize" if not sim.ready_to_close() else "fold" if opening>.0001 else "rest"
func apply()->void:
    for item in groups:
        var offset:=Vector3.ZERO
        var rotation:=Quaternion.IDENTITY
        for i in range(item.route.size()-1):
            var a:Dictionary=item.route[i];var b:Dictionary=item.route[i+1]
            if amount<=float(b.at):
                var t:=smoothstep(float(a.at),float(b.at),amount)
                offset=Vector3(a.offset[0],a.offset[1],a.offset[2]).lerp(Vector3(b.offset[0],b.offset[1],b.offset[2]),t);break
        for i in range(item.route.size()-1):
            var a:Dictionary=item.route[i];var b:Dictionary=item.route[i+1]
            if amount<=float(b.at):
                var qa:Array=a.get("rotation",[0.,0.,0.,1.]);var qb:Array=b.get("rotation",[0.,0.,0.,1.])
                rotation=Quaternion(qa[0],qa[1],qa[2],qa[3]).slerp(Quaternion(qb[0],qb[1],qb[2],qb[3]),smoothstep(float(a.at),float(b.at),amount));break
        item.node.transform=item.home;item.node.position+=offset;item.node.basis=item.home.basis*Basis(rotation)
func state()->Dictionary:return {"amount":amount,"requested":requested,"phase":phase}
