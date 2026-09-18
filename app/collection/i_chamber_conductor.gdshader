shader_type spatial;
render_mode diffuse_burley, specular_schlick_ggx;
uniform vec4 base_color : source_color=vec4(.24,.125,.042,1.);
uniform float metallic_value=.83;
uniform float roughness_value=.31;
uniform sampler2D conductor_mask : filter_linear_mipmap_anisotropic,repeat_enable;
uniform float response=0.;
uniform float travel=0.;
uniform float cell_phase=0.;
uniform bool continuous_conductor=false;
uniform float base_response=0.;
uniform float emission_gain=8.;
uniform float mask_cross_scale=.42;
uniform float packet_floor=.48;
uniform vec3 conductor_color=vec3(1.,.54,.16);
uniform float conductor_offset=0.;
uniform float conductor_half_width=.18;
uniform bool has_brushing=false;
uniform sampler2D brushing_texture : filter_linear_mipmap_anisotropic,repeat_enable;
uniform float brushing_center=.32;
uniform float brushing_strength=0.;
void fragment(){
    float q=1.-UV2.y;
    float edge_distance=min(abs(q),abs(1.-q));
    float across=edge_distance-conductor_offset;
    vec2 light_uv=vec2(fract(UV2.x-travel*.17+cell_phase),.5+across*mask_cross_scale);
    float texture_mask=texture(conductor_mask,light_uv).r;
    float edge_window=1.-smoothstep(.08,.18,edge_distance);
    if(continuous_conductor){edge_window=1.-smoothstep(conductor_half_width*.60,conductor_half_width,abs(across));}
    float packet=packet_floor+(1.-packet_floor)*pow(.5+.5*cos(6.283185*(UV2.x-travel*.27+cell_phase)),2.);
    ALBEDO=base_color.rgb;
    METALLIC=metallic_value;
    float micro=has_brushing?(texture(brushing_texture,vec2(UV2.x*6.,q)).r-brushing_center)*brushing_strength:0.;
    ROUGHNESS=clamp(roughness_value+micro,.08,1.);
    vec3 light_color=continuous_conductor?conductor_color:vec3(1.,.47,.09);
    EMISSION=light_color*texture_mask*edge_window*(base_response+response*packet)*emission_gain;
}
