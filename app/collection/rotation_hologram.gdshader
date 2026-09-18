shader_type spatial;
render_mode unshaded, cull_disabled, depth_draw_never, shadows_disabled;
uniform sampler2D artwork : source_color, filter_linear_mipmap;
uniform vec3 ink : source_color = vec3(0.10,0.58,0.76);
uniform float gain = 0.0;
uniform float reveal = 1.0;
uniform float clock = 0.0;
uniform bool artwork_color=false;
void fragment(){
 vec4 stamp=texture(artwork,UV);
 float scan=smoothstep(1.0-reveal-.08,1.0-reveal+.03,UV.y);
 float fine=.98+.02*sin(UV.y*180.+clock*5.);
 vec3 color=artwork_color?stamp.rgb:ink;
 ALBEDO=color;EMISSION=color*.65*gain;
 ALPHA=clamp(stamp.a*gain*scan*fine,0.,.88);
}
