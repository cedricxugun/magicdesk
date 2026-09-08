shader_type spatial;
render_mode diffuse_burley, specular_schlick_ggx;

uniform vec4 enamel_color:source_color=vec4(.28,.009,.004,1.0);
uniform float metalness=.25;
uniform float roughness_value=.25;
uniform vec2 height_limits=vec2(0.0,1.0);
uniform float energy=0.0;
uniform float fill=1.0;
uniform float scan=-2.0;
uniform float scan_energy=0.0;
uniform float heat=0.0;
uniform float flow_clock=0.0;
uniform float phase_offset=0.0;
varying float marking_height;

void vertex(){
    marking_height=clamp((VERTEX.y-height_limits.x)/max(.0001,height_limits.y-height_limits.x),0.0,1.0);
}
void fragment(){
    // The original bevelled enamel remains an opaque, lit physical surface.
    // Emission is confined to that small existing inlay, never the shell edge.
    ALBEDO=enamel_color.rgb;
    METALLIC=metalness;
    ROUGHNESS=roughness_value;
    CLEARCOAT=.48;CLEARCOAT_ROUGHNESS=.22;
    float filled=1.0-smoothstep(fill-.035,fill+.035,marking_height);
    if(fill<=.0)filled=0.0;
    if(fill>=1.0)filled=1.0;
    float front=exp(-pow((marking_height-scan)/.13,2.0))*scan_energy;
    float slow_flow=.88+.12*sin(marking_height*4.6-flow_clock*.82+phase_offset);
    float strength=max(0.0,energy*slow_flow*filled+front);
    float hot=clamp(heat+front*.13,0.0,1.0);
    vec3 warm=mix(vec3(1.0,.036,.008),vec3(1.0,.36,.055),smoothstep(.0,.72,hot));
    warm=mix(warm,vec3(1.0,.80,.49),smoothstep(.72,1.0,hot));
    EMISSION=warm*strength;
}
