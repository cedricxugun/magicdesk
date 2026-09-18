extends RefCounted
## A bounded visual mass/spring response, not a physical acoustic simulation.
var moving:Node3D
var rest_position:Vector3
var morphs:Array=[]
var max_stroke:=.006
var displacement:=0.
var velocity:=0.
var load_amount:=0.
var accepting:=true
func bind(asset:Node3D,spec:Dictionary)->void:
    moving=asset.find_child(str(spec.moving),true,false);assert(moving!=null)
    rest_position=moving.position;max_stroke=float(spec.max_stroke);morphs.clear()
    for name in spec.morphs:
        var mesh:=asset.find_child(str(name),true,false) as MeshInstance3D
        assert(mesh!=null)
        var positive:=mesh.find_blend_shape_by_name(str(spec.pressure_key))
        var negative:=mesh.find_blend_shape_by_name(str(spec.rebound_key))
        assert(positive>=0 and negative>=0,"Missing authored suspension morphs")
        morphs.append([mesh,positive,negative])
    set_displacement(0.)
func set_load(amount:float)->void:
    if accepting:load_amount=clampf(amount,0.,1.)
func impulse(strength:float)->void:
    if accepting:velocity-=clampf(strength,0.,1.)*.035
func quiet()->void:
    accepting=false;load_amount=0.
func resume()->void:accepting=true
func tick(delta:float)->void:
    var remaining:=maxf(0.,delta)
    while remaining>.0000001:
        var step:=minf(remaining,1./240.);remaining-=step
        velocity+=(110.*(load_amount*max_stroke*.80-displacement)-11.*velocity)*step
        var position:=displacement+velocity*step
        if position>max_stroke:position=max_stroke;velocity=minf(velocity,0.)
        elif position<-max_stroke:position=-max_stroke;velocity=maxf(velocity,0.)
        displacement=position
    set_displacement(displacement)
func set_displacement(value:float)->void:
    displacement=clampf(value,-max_stroke,max_stroke)
    moving.position=rest_position+Vector3.UP*displacement
    for row in morphs:
        row[0].set_blend_shape_value(row[1],maxf(0.,displacement/max_stroke))
        row[0].set_blend_shape_value(row[2],maxf(0.,-displacement/max_stroke))
func settled()->bool:
    return load_amount<.0001 and absf(displacement)<.00001 and absf(velocity)<.0001
