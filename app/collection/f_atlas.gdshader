shader_type spatial;
render_mode unshaded,cull_disabled,depth_draw_never,fog_disabled;
uniform sampler2D atlas:source_color,filter_linear_mipmap_anisotropic;
uniform float tile=0.0;
uniform float gain=1.0;
uniform vec4 tint:source_color=vec4(1.0,.96,.86,1.0);
uniform bool instanced=false;
uniform bool segment_uv=false;
varying vec2 art_uv;
varying float instance_gain;
void vertex(){
 art_uv=UV;
 instance_gain=instanced?INSTANCE_CUSTOM.x:1.0;
 if(segment_uv)art_uv.x=mix(INSTANCE_CUSTOM.y,INSTANCE_CUSTOM.z,UV.x);
}
void fragment(){
 vec2 offset=vec2(mod(tile,2.0),floor(tile/2.0));
 vec2 local=art_uv;
 if(tile<.5)local+=vec2(-.0052,-.0007);
 else if(tile>1.5 && tile<2.5)local+=vec2(-.0091,-.0491);
 else if(tile>2.5)local.y-=.0443;
 vec3 art=texture(atlas,(offset+clamp(local,vec2(.005),vec2(.995)))/2.0).rgb;
 float value=max(art.r,max(art.g,art.b));
 float mask=smoothstep(.018,.095,value);
 float amount=gain*instance_gain;
 ALBEDO=art*tint.rgb;
 EMISSION=art*tint.rgb*amount*6.0;
 ALPHA=clamp(value*amount*1.8,0.0,.90)*mask;
}
