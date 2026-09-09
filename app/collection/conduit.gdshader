shader_type spatial;
render_mode unshaded,cull_disabled,depth_draw_never;
uniform sampler2D fabric:source_color,filter_linear_mipmap_anisotropic,repeat_enable;
uniform float strength=0.0;
uniform float flow=0.0;
void fragment(){
 vec2 uv=vec2(UV.x,UV.y*.85+flow);
 vec3 art=texture(fabric,uv).rgb;
 float luminance=max(art.r,max(art.g,art.b));
 float edge=smoothstep(0.0,.018,UV.y)*smoothstep(0.0,.018,1.0-UV.y);
 ALBEDO=art;
 EMISSION=art*strength*3.5;
 ALPHA=clamp(sqrt(luminance)*strength*.68,0.0,.72)*edge;
}
