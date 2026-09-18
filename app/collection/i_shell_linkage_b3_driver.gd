extends RefCounted
## Authored B3 mechanism. Exact planar four-bar solve; no scaling of shell parts.
var rows:Array=[]
var bindings:Array=[]
var opening:=0.0
var conversion:=Transform3D(Basis(Vector3(1,0,0),Vector3(0,0,-1),Vector3(0,1,0)),Vector3.ZERO)

func vector(a:Array)->Vector3:
    return Vector3(float(a[0]),float(a[1]),float(a[2]))

func bind(asset:Node3D,spec:Dictionary)->void:
    rows=spec.rig;bindings.clear()
    for row in rows:
        var panel:Node3D=asset.find_child(row.panel_pivot,true,false)
        var ab:Node3D=asset.find_child(row.link_pivots[0],true,false)
        var dc:Node3D=asset.find_child(row.link_pivots[1],true,false)
        assert(panel!=null and ab!=null and dc!=null,"Incomplete B3 hinge hierarchy")
        bindings.append({"panel":panel,"ab":ab,"dc":dc})
    set_opening(0.)

func arm_frame(start:Vector3,end:Vector3,axis:Vector3)->Transform3D:
    var direction:Vector3=(end-start).normalized()
    return Transform3D(Basis(direction,axis.cross(direction).normalized(),axis),start)

func solve(row:Dictionary,amount:float)->Dictionary:
    var axis:=vector(row.axis);var radial:=Vector3(cos(float(row.azimuth)),sin(float(row.azimuth)),0.)
    var up:=Vector3(0,0,1);var a:=vector(row.a);var d:=vector(row.d)
    var b0:=vector(row.b0);var c0:=vector(row.c0)
    var theta:float=float(row.theta0)+float(row.travel)*amount
    var b:=a+radial*(float(row.length_ab)*cos(theta))+up*(float(row.length_ab)*sin(theta))
    var delta:=d-b;var distance:=delta.length();var direction:=delta/distance
    var coupler:float=row.length_bc;var second:float=row.length_dc
    var along:float=(coupler*coupler-second*second+distance*distance)/(2.*distance)
    var height_squared:float=coupler*coupler-along*along
    assert(height_squared>0.,"Four-bar branch left its valid travel")
    var side:=axis.cross(direction)
    var c:=b+direction*along+side*sqrt(height_squared)*(1. if int(row.branch)==0 else -1.)
    var initial:=c0-b0;var actual:=c-b
    var angle:=atan2(axis.dot(initial.cross(actual)),initial.dot(actual))
    var rotation:=Basis(axis,angle)
    # Virtual pivots share a plane. A fixed axial offset locates an actual link
    # in a parallel plane without changing the carried shell's rigid transform.
    var ab_offset:=axis*float(row.get("ab_axis_offset",0.))
    return {"panel":Transform3D(rotation,b-rotation*b0),"ab":arm_frame(a+ab_offset,b+ab_offset,axis),"dc":arm_frame(d,c,axis),"b":b+ab_offset,"c":c}

func set_opening(amount:float)->void:
    opening=clampf(amount,0.,1.)
    for i in range(rows.size()):
        var phase:=clampf(opening*6.-i,0.,1.)
        phase=phase*phase*(3.-2.*phase)
        var pose:=solve(rows[i],phase)
        for key in ["panel","ab","dc"]:
            var node:Node3D=bindings[i][key]
            node.transform=conversion*pose[key]*conversion.inverse()
