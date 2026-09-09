shader_type spatial;
render_mode diffuse_burley,specular_schlick_ggx,cull_disabled;
varying float field_gain;
varying float variant;
void vertex(){field_gain=INSTANCE_CUSTOM.x;variant=INSTANCE_CUSTOM.y;}
void fragment(){
 ALBEDO=mix(vec3(.46,.30,.10),vec3(.82,.69,.37),variant);
 METALLIC=.94;ROUGHNESS=.20;CLEARCOAT=.22;CLEARCOAT_ROUGHNESS=.14;
 EMISSION=vec3(1.0,.68,.27)*field_gain*(.8+variant*1.4);
}
