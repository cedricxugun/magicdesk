shader_type spatial;
render_mode unshaded,cull_back,depth_draw_always;
uniform float front=100.;
varying float height;
void vertex(){height=(MODEL_MATRIX*vec4(VERTEX,1.)).y;}
void fragment(){if(height<front)discard;ALBEDO=vec3(0.);ALPHA=0.;}
