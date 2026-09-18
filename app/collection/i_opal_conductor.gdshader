shader_type spatial;
render_mode diffuse_burley, specular_schlick_ggx;
uniform sampler2D conductor_mask : filter_linear_mipmap_anisotropic,repeat_enable;
uniform float response=0.;
uniform float base_response=0.;
uniform float travel=0.;
uniform float emission_gain=5.;
uniform vec3 diffuser_color=vec3(1.,.42,.09);
void fragment(){
    // The actual rounded outward glass surface defines the light's width.
    // Existing generated filament only adds small longitudinal variation.
    float filament=texture(conductor_mask,vec2(fract(UV.x-travel*.035),.5)).r;
    ALBEDO=vec3(.54,.47,.31);
    ROUGHNESS=.26;
    METALLIC=0.;
    SPECULAR=.35;
    EMISSION=diffuser_color*(base_response+response*(.85+.15*filament))*emission_gain;
}
