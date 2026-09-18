extends Node3D
## Opt-in I cassette; driven by the actual pneumatic state, no repeated click pulses.
var service:Node3D
var rig:Dictionary
var controls:Dictionary={}
var caption_projection:Dictionary={}
var outgoing:=0.
var returning:=0.
var outgoing_energy:=0.
var return_energy:=0.
var pressure_press:=0.
var service_pose:=0.

func named(root:Node3D,label:String)->Node3D:
    var result:Node3D=root.find_child(label,true,false) as Node3D
    if result==null:result=root.find_child(label.replace(".","_"),true,false) as Node3D
    return result

func setup(owner:Node3D)->void:
    service=owner
    rig=JSON.parse_string(FileAccess.get_file_as_string("res://assets/collection/i_console_rig.json")).rig
    var library:Node3D=load("res://assets/collection/components/I_controls_r1.glb").instantiate()
    var plate:Node3D=service.selector.find_child("S_PANEL",true,false).duplicate();add_child(plate);plate.show()
    service._add_control_colliders(plate,-1,2)
    var kinds:Array=["frequency","pressure","throat","gauge","service"];var indices:Array=[1,2,5,3,4]
    for slot in range(5):
        var kind:String=kinds[slot];var spec:Dictionary=rig[kind]
        var widget:Node3D=named(library,spec.root).duplicate();add_child(widget);widget.show()
        var mount:Node3D=service.host.buttons[slot+1].mount
        var home:Transform3D=service.legacy_mount_homes[slot]
        var point:Vector3=mount.get_parent().to_global(home.origin)
        widget.global_position=point;widget.look_at(point+Vector3(point.x,0,point.z).normalized(),Vector3.UP,true)
        var moving:Node3D=named(widget,spec.moving)
        controls[kind]={"node":widget,"moving":moving,"home":moving.transform,"index":indices[slot]}
        named(widget,spec.label).position.z=0.
        service._add_control_colliders(widget,indices[slot],16)
    library.free()

func seat_captions()->void:
    var rays:=0;var misses:=0;var changes:Array=[]
    for kind in controls:
        var widget:Node3D=controls[kind].node;var patch:Node3D=named(widget,rig[kind].label);var cache:Dictionary={}
        for mesh in patch.find_children("*","MeshInstance3D",true,false):
            var result:=ArrayMesh.new()
            for surface in range(mesh.mesh.get_surface_count()):
                var arrays:Array=mesh.mesh.surface_get_arrays(surface);var vertices:PackedVector3Array=arrays[Mesh.ARRAY_VERTEX];var normals:PackedVector3Array=arrays[Mesh.ARRAY_NORMAL]
                for i in range(vertices.size()):
                    var local:Vector3=widget.to_local(mesh.to_global(vertices[i]));var key:=Vector2i(roundi(local.x*100000.),roundi(local.y*100000.))
                    if not cache.has(key):
                        rays+=1
                        var query:=PhysicsRayQueryParameters3D.create(widget.to_global(Vector3(local.x,local.y,.15)),widget.to_global(Vector3(local.x,local.y,-.15)),3)
                        cache[key]=service.host.get_world_3d().direct_space_state.intersect_ray(query)
                    var hit:Dictionary=cache[key]
                    if hit.is_empty():misses+=1;continue
                    vertices[i]=mesh.to_local(hit.position+hit.normal*(.00035+maxf(0.,local.z)))
                    if i<normals.size():normals[i]=(mesh.global_basis.inverse()*hit.normal).normalized()
                arrays[Mesh.ARRAY_VERTEX]=vertices;arrays[Mesh.ARRAY_NORMAL]=normals
                result.add_surface_from_arrays(Mesh.PRIMITIVE_TRIANGLES,arrays);result.surface_set_material(surface,mesh.mesh.surface_get_material(surface))
            changes.append({"mesh":mesh,"result":result})
    if misses==0:
        for change in changes:change.mesh.mesh=change.result
    caption_projection={"rays":rays,"misses":misses,"applied":misses==0}

func update(delta:float,sim:RefCounted,events:Array,service_value:float=0.)->void:
    for event in events:
        if event.kind=="outgoing":outgoing_energy=maxf(outgoing_energy,float(event.gain))
        elif event.kind=="return":return_energy=maxf(return_energy,float(event.gain))
    # Equal decay time keeps a weaker return readable; the physical floats ease in.
    var decay:float=exp(-delta*(1.6 if sim.listening else 7.))
    outgoing_energy*=decay;return_energy*=decay
    outgoing=lerpf(outgoing,outgoing_energy,1.-exp(-delta*18.));returning=lerpf(returning,return_energy,1.-exp(-delta*18.))
    pressure_press=move_toward(pressure_press,1. if sim.pressed else 0.,delta*8.)
    service_pose=move_toward(service_pose,service_value,delta*5.)
    var control:Dictionary=controls.frequency
    control.moving.transform=Transform3D(Basis(Vector3.FORWARD,lerpf(-PI*.8,PI*.8,sim.frequency)),Vector3.ZERO)*control.home
    control=controls.pressure;control.moving.transform=Transform3D(Basis.IDENTITY,Vector3(0,0,-.015*pressure_press))*control.home
    named(control.node,rig.pressure.indicator).position.y=.058*clampf((sim.pressure-1.)/.43,0.,1.)
    control=controls.throat
    var pivot:=Vector3(0,0,.039);var motion:=Transform3D(Basis.IDENTITY,pivot)*Transform3D(Basis(Vector3.UP,lerpf(-.52,.52,sim.throat)),Vector3.ZERO)*Transform3D(Basis.IDENTITY,-pivot)
    control.moving.transform=motion*control.home
    control=controls.gauge
    named(control.node,rig.gauge.outgoing).position.y=.052*outgoing
    named(control.node,rig.gauge["return"]).position.y=.052*returning
    control=controls.service;pivot=Vector3(0,0,.040)
    motion=Transform3D(Basis.IDENTITY,pivot)*Transform3D(Basis(Vector3.UP,service_pose*.26),Vector3.ZERO)*Transform3D(Basis.IDENTITY,-pivot)
    control.moving.transform=motion*control.home
