shader_type spatial;
render_mode cull_disabled,depth_draw_opaque;
uniform float opening=0.0;
uniform sampler2D atlas:source_color,filter_linear_mipmap;
uniform float power=1.0;
uniform float scan_amount=0.0;
uniform float scan_min=.62;
uniform float scan_max=3.8;
varying float world_y;
void vertex(){world_y=(MODEL_MATRIX*vec4(VERTEX,1.0)).y;}
void fragment(){
 float height=clamp((world_y-scan_min)/max(.01,scan_max-scan_min),0.0,1.0);
 if(scan_amount>0.0 && height>1.0-scan_amount)discard;
 float interior=sin(UV.x*3.14159)*sin(UV.y*3.14159);
 float edge=1.0-smoothstep(.02,.25,interior);
 vec3 art=texture(atlas,(vec2(3,1)+UV)/vec2(4,2)).rgb;
 ALBEDO=vec3(.016,.019,.018);METALLIC=.35;ROUGHNESS=.24;
 EMISSION=art*opening*power*.3;
 ALPHA=mix(1.0,edge,opening);
}
