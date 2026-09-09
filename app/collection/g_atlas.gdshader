shader_type spatial;
render_mode unshaded,cull_disabled,depth_draw_never,fog_disabled;
uniform sampler2D atlas:source_color,filter_linear_mipmap_anisotropic;
uniform float tile=0.0;
uniform float gain=0.0;
uniform bool instanced=false;
varying float energy;
void vertex(){energy=instanced?INSTANCE_CUSTOM.x:1.0;}
void fragment(){
 vec2 offset=vec2(mod(tile,2.0),floor(tile/2.0));
 vec3 art=texture(atlas,(offset+clamp(UV,vec2(.008),vec2(.992)))*.5).rgb;
 float v=max(art.r,max(art.g,art.b));
 float amount=gain*energy;
 ALBEDO=art;EMISSION=art*amount*5.0;
 ALPHA=smoothstep(.014,.085,v)*clamp(v*amount*1.8,0.0,.88);
}
