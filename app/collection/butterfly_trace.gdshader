shader_type spatial;
render_mode unshaded,cull_disabled,depth_draw_never;
uniform sampler2D pattern:filter_linear_mipmap,repeat_enable;
uniform float progress=0.;
uniform float gain=0.;
uniform float clock=0.;
uniform vec3 ink_color=vec3(1.,.33,.025);
uniform bool pulse_only=false;
uniform float rear_progress=-1.;
varying float coordinate;
void vertex(){coordinate=mix(INSTANCE_CUSTOM.r,INSTANCE_CUSTOM.g,VERTEX.y+.5);}
void fragment(){
 float front=1.-smoothstep(progress+.055,progress+.115,coordinate);
 float tip=1.-smoothstep(.0,.065,abs(coordinate-progress));
 if(pulse_only)front=tip;
 float art=texture(pattern,vec2(.5,fract(coordinate*.7-clock*.17))).r;
 float strength=gain*front*(.30+tip*1.5)*(.55+art*.45);
 if(rear_progress>=0.)strength*=smoothstep(rear_progress-.025,rear_progress+.015,coordinate);
 ALBEDO=ink_color;EMISSION=ALBEDO*strength*2.0;ALPHA=clamp(strength,0.,.95);
}
