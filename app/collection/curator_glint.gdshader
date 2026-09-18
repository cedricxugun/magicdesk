shader_type spatial;
render_mode unshaded,cull_disabled,depth_draw_never;
uniform sampler2D atlas:source_color,filter_linear_mipmap;
uniform vec3 color=vec3(1.,.78,.42);
uniform float gain=0.;
uniform bool instanced=false;
varying float instance_gain;
void vertex(){instance_gain=INSTANCE_CUSTOM.r;}
void fragment(){
 // The authored star occupies a small region inside the fourth atlas tile.
 vec3 art=texture(atlas,vec2(.732,.718)+(UV-.5)*.10).rgb;
 float intensity=max(art.r,max(art.g,art.b))*gain*(instanced?instance_gain:1.);
 ALBEDO=color;EMISSION=color*intensity*3.5;ALPHA=clamp(intensity,0.,.94);
}
