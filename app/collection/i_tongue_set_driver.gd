extends RefCounted
var controllers:Array=[]
var groups:Array=[]
var receipts:Array=[]
func bind(asset:Node3D,spec:Dictionary)->void:
    groups=spec.tongues
    for group in groups:
        var controller=load("res://collection/i_tongue_fields.gd").new();controller.bind(asset,group);controllers.append(controller);receipts.append(controller.receipts)
    set_opening(0.)
func set_opening(amount:float)->void:
    amount=clampf(amount,0.,1.)
    for i in range(controllers.size()):
        var limits:Array=groups[i].window;var t:=clampf((amount-float(limits[0]))/(float(limits[1])-float(limits[0])),0.,1.)
        controllers[i].set_feed(t*t*(3.-2.*t))
