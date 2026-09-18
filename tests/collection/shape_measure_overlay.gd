extends Node2D
var heading:=""
var details:=""
var markers:Array=[]
var font:=SystemFont.new()
func _ready()->void:
    font.font_names=["PingFang SC","Arial"]
func _draw()->void:
    draw_string(font,Vector2(24,34),heading,HORIZONTAL_ALIGNMENT_LEFT,-1,22,Color(.85,.90,.92))
    draw_string(font,Vector2(24,62),details,HORIZONTAL_ALIGNMENT_LEFT,-1,15,Color(.57,.73,.79))
    for row in markers:
        var p:Vector2=row.point
        var label:=Vector2(clampf(p.x+26.,20.,690.),clampf(p.y-24.,95.,950.))
        draw_circle(p,4.,Color(.95,.45,.25));draw_line(p,label,Color(.95,.45,.25),1.2)
        draw_string(font,label+Vector2(5,-5),row.text,HORIZONTAL_ALIGNMENT_LEFT,-1,14,Color(.95,.71,.47))
