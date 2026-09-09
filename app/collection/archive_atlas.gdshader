shader_type spatial;
render_mode unshaded,cull_disabled,depth_draw_never;
uniform sampler2D atlas:source_color,filter_linear_mipmap;
uniform float tile=0.;
uniform float gain=1.;
uniform vec2 crop=vec2(1.);
uniform vec2 center=vec2(.5);
uniform bool swap_uv=false;
uniform float travel=0.;
uniform vec3 hue=vec3(1.);
void fragment(){
 vec2 uv=swap_uv?UV.yx:UV;
 uv=(uv-.5)*crop+center;
 uv.x=fract(uv.x+travel);
 vec2 offset=vec2(mod(tile,2.),floor(tile/2.));
 vec3 art=texture(atlas,(offset+clamp(uv,vec2(.006),vec2(.994)))*.5).rgb;
 float light=max(art.r,max(art.g,art.b));
 ALBEDO=art*hue;EMISSION=art*hue*gain*2.4;
 ALPHA=clamp(light*gain,0.,.94);
}
