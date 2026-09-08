shader_type spatial;
render_mode unshaded,cull_back,depth_draw_never;
uniform vec4 arc_start[6];
uniform vec4 arc_end[6];
uniform vec4 arc_bow[6];
uniform float live=0.0;
uniform float pulse_time=0.0;
varying float opacity;
varying float glow_layer;

vec3 arc_point(float t,int channel){
    vec3 a=arc_start[channel].xyz,b=arc_end[channel].xyz;
    vec3 d=normalize(b-a+vec3(.00001));
    vec3 side=normalize(cross(d,vec3(0,0,1))+vec3(.00001,0,0));
    vec3 up=normalize(cross(d,side));
    float seed=arc_bow[channel].w;
    float jag=(sin(t*57.0+seed)*.025+sin(t*117.0+seed*1.31)*.018);
    return mix(a,b,t)+sin(t*3.14159265)*(arc_bow[channel].xyz+side*jag+up*sin(t*73.0+seed*.7)*.024);
}
void vertex(){
    int channel=int(COLOR.r*10.0+.5);
    glow_layer=COLOR.g*2.0;
    float t=UV.x;
    vec3 p=arc_point(t,channel);
    vec3 tangent=normalize(arc_point(min(.9999,t+.003),channel)-arc_point(max(.0001,t-.003),channel));
    vec3 side=normalize(cross(tangent,vec3(0,1,0))+vec3(.00001,0,0));
    vec3 up=normalize(cross(tangent,side));
    vec3 normal=side*cos(UV.y*6.2831853)+up*sin(UV.y*6.2831853);
    float radius=glow_layer<.5?.0055:glow_layer<1.5?.014:.029;
    radius*=channel>3?.68:1.0;
    float flutter=.89+.11*sin(pulse_time*27.0+float(channel)*1.37+t*8.0);
    VERTEX=p+normal*radius*flutter;
    NORMAL=normal;
    opacity=arc_start[channel].w*live;
}
void fragment(){
    float pulse=.70+.30*pow(sin(pulse_time*12.0+glow_layer*.6),2.0);
    if(glow_layer<.5){ALBEDO=vec3(1.0,.84,.70);EMISSION=vec3(7.0,3.2,2.2);ALPHA=opacity*pulse;}
    else {ALBEDO=vec3(1.0,.045,.012);EMISSION=vec3(2.6,.022,.006);ALPHA=opacity*(glow_layer<1.5?.28:.095)*pulse;}
}
