shader_type spatial;
render_mode unshaded, cull_disabled, depth_draw_never, blend_mix;

uniform float opacity=0.0;
uniform float flow_time=0.0;
uniform float surge=0.0;
void vertex(){
    MODELVIEW_MATRIX=VIEW_MATRIX*mat4(INV_VIEW_MATRIX[0],INV_VIEW_MATRIX[1],INV_VIEW_MATRIX[2],MODEL_MATRIX[3]);
}
void fragment(){
    vec2 p=UV*2.0-1.0;
    float r=length(p);
    float a=r>0.0001?atan(p.y,p.x):0.0;
    float curl=sin(a*5.0+r*14.0-flow_time*1.1)*0.056+sin(a*9.0-r*8.0+flow_time*0.73)*0.033;
    float edge=r+curl;
    float soft=exp(-edge*edge*3.3)*(1.0-smoothstep(0.57,0.97,edge));
    ALBEDO=vec3(0.96,0.025,0.018);
    EMISSION=vec3(0.72,0.012,0.006)*(1.0+surge*0.6);
    ALPHA=soft*opacity;
}
