shader_type spatial;
render_mode diffuse_burley, specular_schlick_ggx;
uniform sampler2D conductor_mask : filter_linear_mipmap_anisotropic,repeat_enable;
uniform float response=0.;
uniform float base_response=0.;
uniform float travel=0.;
uniform float emission_gain=5.;
uniform vec3 diffuser_color=vec3(1.,.42,.09);
uniform bool wavefront_enabled=false;
uniform float phase_offset=0.;
uniform bool guided_network=false;
void fragment(){
    // The actual rounded outward glass surface defines the light's width.
    // Existing generated filament only adds small longitudinal variation.
    float filament=texture(conductor_mask,vec2(fract(UV.x-travel*.035),.5)).r;
    ALBEDO=vec3(.54,.47,.31);
    ROUGHNESS=.26;
    METALLIC=0.;
    SPECULAR=.35;
    EMISSION=diffuser_color*(base_response+response*(.85+.15*filament))*emission_gain;
    if(wavefront_enabled){
        float packet=pow(max(0.,cos(6.283185*(UV.x-travel*.23+phase_offset))),16.);
        float detail=texture(conductor_mask,vec2(fract(UV.x-travel*.18+phase_offset),.5)).r;
        EMISSION=diffuser_color*(base_response*(.70+.45*packet)+response*(.45+.55*detail))*emission_gain;
        if(guided_network){
            EMISSION=diffuser_color*(base_response*(.10+1.55*packet)+response*(.25+1.10*packet)*detail)*emission_gain;
        }
    }
}
