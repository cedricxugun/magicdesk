shader_type spatial;
render_mode diffuse_burley,specular_schlick_ggx;
uniform sampler2D atlas:source_color,filter_linear_mipmap;
uniform float pulse=0.0;
uniform float strength=0.0;
uniform float scan_amount=0.0;
uniform float scan_min=.62;
uniform float scan_max=3.8;
varying float world_y;
void vertex(){world_y=(MODEL_MATRIX*vec4(VERTEX,1.0)).y;}
void fragment(){
 float height=clamp((world_y-scan_min)/max(.01,scan_max-scan_min),0.0,1.0);
 if(scan_amount>0.0 && height>1.0-scan_amount)discard;
 vec2 local=vec2(fract(UV.x-pulse),.47+UV.y*.06);
 vec3 art=texture(atlas,(vec2(3,0)+local)/vec2(4,2)).rgb;
 ALBEDO=vec3(.19,.013,.006);METALLIC=.22;ROUGHNESS=.23;
 CLEARCOAT=.5;CLEARCOAT_ROUGHNESS=.12;
 EMISSION=art*strength*5.0;
}
