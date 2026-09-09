shader_type spatial;
render_mode unshaded,cull_back,depth_draw_never;
uniform sampler2D atlas:source_color,filter_linear_mipmap;
uniform float front=100.;
uniform float gain=0.;
uniform float phase=0.;
varying vec3 point;
void vertex(){point=(MODEL_MATRIX*vec4(VERTEX,1.)).xyz;}
void fragment(){
 float zone=smoothstep(front-.01,front+.055,point.y);
 vec2 uv=vec2(fract((point.x+point.z*.3)*.85),fract(point.y*.45+phase*.075));
 vec3 fibres=texture(atlas,(vec2(1,0)+uv)*.5).rgb;
 float line=max(fibres.r,max(fibres.g,fibres.b));
 float silhouette=pow(1.-abs(dot(normalize(NORMAL),normalize(VIEW))),3.5);
 float mask=clamp(smoothstep(.06,.6,line)*.55+silhouette*.5,0.,.8);
 ALBEDO=vec3(1.,.28,.04);EMISSION=(fibres*3.+vec3(1.,.18,.015)*silhouette)*gain*2.;
 ALPHA=mask*zone*gain;
}
