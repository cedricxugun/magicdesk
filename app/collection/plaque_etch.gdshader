shader_type spatial;
render_mode unshaded,cull_disabled,depth_draw_never;
uniform sampler2D portrait:source_color,filter_linear_mipmap;
uniform float gain=1.;
float shade(vec4 p){return dot(p.rgb,vec3(.3,.59,.11))*p.a;}
void fragment(){
 vec2 d=vec2(.009);
 vec4 center=texture(portrait,UV);
 vec4 left=texture(portrait,UV-vec2(d.x,0));vec4 right=texture(portrait,UV+vec2(d.x,0));
 vec4 top=texture(portrait,UV-vec2(0,d.y));vec4 bottom=texture(portrait,UV+vec2(0,d.y));
 float silhouette=abs(left.a-right.a)+abs(top.a-bottom.a);
 float detail=abs(shade(left)-shade(right))+abs(shade(top)-shade(bottom));
 float stroke=clamp(silhouette*2.2+detail*2.,0.,1.);
 vec3 gold=vec3(1.,.52,.15);
 ALBEDO=gold;EMISSION=gold*gain*1.5;
 ALPHA=clamp(stroke*.9+center.a*.035,0.,.95);
}
