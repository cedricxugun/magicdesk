shader_type spatial;
render_mode unshaded,cull_disabled,depth_draw_never;
uniform sampler2D beam_art:source_color,filter_linear_mipmap_anisotropic,repeat_disable;
uniform vec4 arc_start[9];
uniform vec4 arc_end[9];
uniform vec4 arc_bow[9];
uniform float live=0.0;
uniform float pulse_time=0.0;
varying vec2 art_uv;
varying float opacity;

vec3 centerline(float t,int i){
    return mix(arc_start[i].xyz,arc_end[i].xyz,t)+sin(t*3.14159265)*arc_bow[i].xyz;
}
void vertex(){
    int i=int(COLOR.r*10.0+.5);
    float t=UV.x;
    vec3 p=centerline(t,i);
    vec3 tangent=normalize(arc_end[i].xyz-arc_start[i].xyz+cos(t*3.14159265)*3.14159265*arc_bow[i].xyz);
    vec3 eye=(inverse(MODEL_MATRIX)*vec4(CAMERA_POSITION_WORLD,1)).xyz;
    vec3 side=normalize(cross(tangent,eye-p)+vec3(.00001,0,0));
    float length_beam=length(arc_end[i].xyz-arc_start[i].xyz);
    float width=clamp(length_beam*.32,.13,.29)*((i==4||i==5)?.75:1.0);
    VERTEX=p+side*(UV.y-.5)*width*2.0;
    NORMAL=normalize(eye-p);
    // The end margins of the authored beam taper to the actual contacts.
    art_uv=vec2(mix(.022,.978,t),UV.y);
    opacity=arc_start[i].w*live;
}
void fragment(){
    vec4 art=texture(beam_art,art_uv);
    vec3 plus=texture(beam_art,art_uv+vec2(0,.006)).rgb;
    vec3 minus=texture(beam_art,art_uv-vec2(0,.006)).rgb;
    float filament=max(min(art.g,art.b),max(min(plus.g,plus.b),min(minus.g,minus.b))*.70);
    float white_core=smoothstep(.008,.17,filament);
    float red_halo=clamp(art.r-max(art.g,art.b),0.0,1.0);
    float alpha=max(art.a*(.22+white_core*.78)*(1.0-red_halo*.40),white_core*.95);
    float pulse=.78+.22*sin(pulse_time*15.0+art_uv.x*3.0);
    ALBEDO=art.rgb;
    EMISSION=art.rgb*2.0+vec3(8.0,5.0,3.8)*white_core;
    ALPHA=alpha*opacity*pulse;
}
