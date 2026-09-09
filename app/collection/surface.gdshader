shader_type spatial;
render_mode diffuse_burley,specular_schlick_ggx;
uniform vec4 tint:source_color=vec4(1.0);
uniform sampler2D color_map:source_color,filter_linear_mipmap_anisotropic,repeat_enable;
uniform sampler2D roughness_map:hint_default_white,filter_linear_mipmap_anisotropic,repeat_enable;
uniform sampler2D normal_map:hint_normal,filter_linear_mipmap_anisotropic,repeat_enable;
uniform bool has_color=false;
uniform bool has_roughness=false;
uniform bool has_normal=false;
uniform float metallic=0.0;
uniform float roughness=.3;
uniform float coat=.25;
uniform vec4 emission_color:source_color=vec4(0.0);
uniform float emission_energy=0.0;
uniform float power=1.0;
uniform float scan_amount=0.0;
uniform float scan_min=.62;
uniform float scan_max=3.8;
uniform sampler2D scan_fabric:source_color,filter_linear_mipmap_anisotropic,repeat_enable;
uniform float formation=1.0;
uniform bool clip_enabled=false;
uniform vec3 clip_normal=vec3(0,0,1);
uniform float clip_d=0.0;
varying float world_y;
varying vec3 world_position;
void vertex(){world_position=(MODEL_MATRIX*vec4(VERTEX,1.0)).xyz;world_y=world_position.y;}
void fragment(){
 if(clip_enabled && dot(world_position,clip_normal)+clip_d<0.0)discard;
 vec3 forming=vec3(0.0);float formation_mask=0.0;
 if(formation<.9999){
  forming=texture(scan_fabric,UV*vec2(2.0,1.0)).rgb;
  formation_mask=1.0-clamp(max(forming.r,max(forming.g,forming.b))*4.0,0.0,1.0);
  if(formation<formation_mask)discard;
 }
 float height=clamp((world_y-scan_min)/max(.01,scan_max-scan_min),0.0,1.0);
 float boundary=1.0-scan_amount;
 vec3 archive=vec3(0.0);
 if(scan_amount>0.0)archive=texture(scan_fabric,world_position.xy*.8+vec2(scan_amount*.15,0)).rgb;
 bool scaffold=scan_amount>0.0 && height>boundary;
 if(scaffold && (height>boundary+.055 || max(archive.r,max(archive.g,archive.b))<.18))discard;
 ALBEDO=tint.rgb*(has_color?texture(color_map,UV).rgb:vec3(1.0));
 METALLIC=metallic;
 ROUGHNESS=clamp(has_roughness?texture(roughness_map,UV).g:roughness,.18,.8);
 if(has_normal){NORMAL_MAP=texture(normal_map,UV).rgb;NORMAL_MAP_DEPTH=.14;}
 CLEARCOAT=coat;CLEARCOAT_ROUGHNESS=.13;
 EMISSION=emission_color.rgb*emission_energy*power;
 if(scan_amount>0.0){float edge=1.0-smoothstep(.0,.010,abs(height-boundary));EMISSION+=vec3(5.0,.22,.04)*edge;}
 if(scaffold){ALBEDO=vec3(.08,.02,.008);METALLIC=0.;EMISSION=archive*vec3(6.,1.3,.4);}
 if(formation<.9999){float edge=1.0-smoothstep(.0,.12,abs(formation_mask-formation));EMISSION+=(vec3(1.0,.48,.16)*edge+forming*2.0)*(1.0-formation)*3.0;}
}
