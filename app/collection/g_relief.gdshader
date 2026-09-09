shader_type spatial;
render_mode cull_disabled;
uniform sampler2D atlas:source_color,filter_linear_mipmap;
uniform float gain=0.0;
uniform float reveal=0.0;
uniform float travel=0.0;
varying float layer_height;
void vertex(){layer_height=VERTEX.y/.44;}
void fragment(){
 float visible_amount=clamp(reveal*30.0-layer_height*27.0,0.0,1.0);
 if(visible_amount<.002)discard;
 vec3 art=texture(atlas,vec2(.5+fract(UV.x+travel*.018)*.49,.50+UV.y*.49)).rgb;
 ALBEDO=vec3(.72,.56,.34);METALLIC=.78;ROUGHNESS=.24;
 EMISSION=mix(vec3(1.0,.36,.10),vec3(1.0,.76,.40),clamp(layer_height,0.0,1.0))*gain*(1.2+art*2.0);
 ALPHA=visible_amount*.88;
}
