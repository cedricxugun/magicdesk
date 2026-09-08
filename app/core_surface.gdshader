shader_type spatial;
render_mode diffuse_burley, specular_schlick_ggx;

uniform float heat = 0.0;
uniform float surge = 0.0;
uniform float flow_time = 0.0;
uniform float filament = 0.0;
uniform sampler2D plasma_art:source_color,filter_linear_mipmap_anisotropic,repeat_enable;
varying vec3 local_point;

float hash31(vec3 p) {
    p=fract(p*0.1031);p+=dot(p,p.yzx+33.33);
    return fract((p.x+p.y)*p.z);
}
float noise3(vec3 p) {
    vec3 i=floor(p),f=fract(p);f=f*f*(3.0-2.0*f);
    return mix(mix(mix(hash31(i),hash31(i+vec3(1,0,0)),f.x),mix(hash31(i+vec3(0,1,0)),hash31(i+vec3(1,1,0)),f.x),f.y),
               mix(mix(hash31(i+vec3(0,0,1)),hash31(i+vec3(1,0,1)),f.x),mix(hash31(i+vec3(0,1,1)),hash31(i+vec3(1,1,1)),f.x),f.y),f.z);
}
void vertex(){local_point=VERTEX;}
void fragment(){
    vec3 p=local_point*19.0;
    vec3 drift=vec3(flow_time*0.34,-flow_time*0.48,flow_time*0.19);
    vec3 convected=p+vec3(sin(p.y*.7+flow_time*.48),cos(p.z*.65-flow_time*.43),sin(p.x*.6+flow_time*.36))*.44;
    float slow=noise3(convected*0.48+drift);
    float medium=noise3(convected*1.7-drift*1.30);
    float fine=noise3(convected*5.8+vec3(0,flow_time*0.38,0));
    float flowing=slow*0.61+medium*0.28+fine*0.11;
    float facing=clamp(dot(normalize(NORMAL),normalize(VIEW)),0.0,1.0);
    float front_heat=pow(facing,1.7);
    float incandescent=smoothstep(0.38,0.76,flowing)*front_heat;
    incandescent=mix(incandescent,0.32+0.53*pow(facing,2.0),filament);
    incandescent=clamp(incandescent*(1.0+surge*.65)+surge*0.11*front_heat,0.0,1.0);
    float cellular=pow(1.0-abs(medium*2.0-1.0),9.0)*0.32;
    vec3 crimson=vec3(0.34,0.0018,0.006);
    vec3 hot_red=vec3(3.4,0.033,0.018);
    vec3 white_hot=vec3(12.0,6.0,4.6);
    vec3 radiance=mix(crimson,hot_red,0.24+flowing*0.65);
    radiance=mix(radiance,white_hot,pow(incandescent,1.55));
    radiance+=vec3(1.2,0.014,0.022)*cellular;
    if(filament<0.5){
        // Three projections avoid stretching and seams on the faceted crystal.
        vec3 weights=pow(abs(normalize(local_point)),vec3(9.0));
        weights/=max(weights.x+weights.y+weights.z,.001);
        vec3 p0=local_point*1.05+vec3(.17,.39,.61);
        vec2 flow_a=vec2(flow_time*.024,-flow_time*.017);
        vec2 flow_b=vec2(-flow_time*.013,flow_time*.029);
        vec3 layer_a=texture(plasma_art,p0.yz+flow_a).rgb*weights.x+texture(plasma_art,p0.xz+flow_a.yx).rgb*weights.y+texture(plasma_art,p0.xy+flow_a).rgb*weights.z;
        vec3 layer_b=texture(plasma_art,p0.yz*.78+flow_b).rgb*weights.x+texture(plasma_art,p0.xz*.78+flow_b.yx).rgb*weights.y+texture(plasma_art,p0.xy*.78+flow_b).rgb*weights.z;
        vec3 plasma=mix(layer_a,layer_b,.10+.05*sin(flow_time*.63));
        plasma=pow(max(plasma,vec3(0.0)),vec3(1.38));
        float incandescent_edge=smoothstep(.10,.64,min(plasma.g,plasma.b));
        radiance=plasma*(2.0+surge*1.5)+vec3(.035,.0002,.001);
        radiance+=vec3(2.4,1.8,1.3)*incandescent_edge*(.40+surge*.65);
    }
    ALBEDO=mix(vec3(0.032,0.004,0.008),vec3(0.11,0.005,0.011),heat);
    METALLIC=0.33;
    ROUGHNESS=0.25+(fine-0.5)*0.10;
    CLEARCOAT=0.20;CLEARCOAT_ROUGHNESS=0.18;
    EMISSION=radiance*heat*(0.80+surge*0.80);
}
