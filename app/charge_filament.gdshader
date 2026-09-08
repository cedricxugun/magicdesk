shader_type spatial;
render_mode diffuse_burley, specular_schlick_ggx;
uniform float power=0.0;
uniform float sweep=-2.0;
uniform float running=0.0;
uniform float release=0.0;
void fragment(){
    float pulse=exp(-pow((UV.y-sweep)*8.5,2.0));
    float leading=exp(-pow((UV.y-sweep)*21.0,2.0));
    float intensity=power*(pulse*3.6+running*.15+release*.45);
    ALBEDO=vec3(.16,.008,.005);
    METALLIC=.62;
    ROUGHNESS=.28;
    EMISSION=mix(vec3(1.0,.008,.004),vec3(1.0,.30,.17),leading*.70)*intensity;
}
