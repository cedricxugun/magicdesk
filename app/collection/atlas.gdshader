shader_type spatial;
render_mode unshaded,cull_disabled,depth_draw_never;
uniform sampler2D atlas:source_color,filter_linear_mipmap;
uniform float tile=0.0;
uniform float strength=0.0;
uniform vec4 tint:source_color=vec4(1.0);
uniform vec2 image_scale=vec2(1.0);
uniform float flow=0.0;
uniform float spin=0.0;
void fragment(){
 vec2 local=(UV-.5)*image_scale+.5;
 vec2 centered=local-.5;
 local=mat2(vec2(cos(spin),sin(spin)),vec2(-sin(spin),cos(spin)))*centered+.5;
 local.x=fract(local.x+flow);
 vec2 offset=vec2(mod(tile,4.0),floor(tile/4.0));
 vec3 art=texture(atlas,(offset+clamp(local,vec2(.012),vec2(.988)))/vec2(4.0,2.0)).rgb;
 float fade=smoothstep(0.0,.045,UV.x)*smoothstep(0.0,.045,1.0-UV.x)*smoothstep(0.0,.045,UV.y)*smoothstep(0.0,.045,1.0-UV.y);
 float luminance=max(art.r,max(art.g,art.b));
 ALBEDO=art*tint.rgb;EMISSION=art*tint.rgb*strength*1.8;
 ALPHA=clamp(luminance*strength,0.0,1.0)*fade;
}
