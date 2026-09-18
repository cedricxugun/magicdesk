shader_type spatial;
render_mode diffuse_burley,specular_schlick_ggx;
uniform vec4 tint:source_color=vec4(1.0);
uniform sampler2D color_map:source_color,filter_linear_mipmap_anisotropic,repeat_enable;
uniform sampler2D roughness_map:hint_default_white,filter_linear_mipmap_anisotropic,repeat_enable;
uniform sampler2D normal_map:hint_normal,filter_linear_mipmap_anisotropic,repeat_enable;
uniform bool has_color=false;
uniform bool has_roughness=false;
uniform bool has_normal=false;
uniform bool has_metallic=false;
uniform sampler2D metallic_map:hint_default_white,filter_linear_mipmap_anisotropic,repeat_enable;
uniform vec4 metallic_channel=vec4(0.,0.,1.,0.);
uniform float metallic=0.0;
uniform float roughness=.3;
uniform float coat=.25;
uniform float coat_roughness=.13;
uniform float specular_strength=.5;
uniform float roughness_offset=0.0;
uniform float roughness_scale=1.0;
uniform float roughness_floor=.18;
uniform float normal_depth=.14;
uniform float anisotropy_strength=0.0;
uniform float instrument_gain=-1.0;
uniform float instrument_time=0.0;
uniform sampler2D instrument_profile:source_color,filter_linear_mipmap;
uniform vec4 emission_color:source_color=vec4(0.0);
uniform float emission_energy=0.0;
uniform float power=1.0;
uniform float scan_amount=0.0;
uniform float scan_min=.62;
uniform float scan_max=3.8;
uniform sampler2D scan_fabric:source_color,filter_linear_mipmap_anisotropic,repeat_enable;
uniform float formation=1.0;
uniform bool record_print=false;
uniform bool butterfly_body=false;
uniform bool butterfly_wing=false;
uniform vec3 wing_origin=vec3(0.);
uniform vec3 wing_outward=vec3(1.,0.,0.);
uniform float wing_span=.4;
uniform float wing_start=.3;
uniform float wing_end=.88;
uniform int wing_seal_kind=0;
uniform sampler2D wing_seal_map:filter_linear_mipmap,repeat_disable;
uniform vec4 wing_seal_bounds=vec4(0.,0.,1.,1.);
uniform vec3 wing_vertical=vec3(0.,1.,0.);
uniform float wing_seal_start=.54;
uniform float wing_seal_end=.90;
uniform bool ship_part=false;
uniform bool ship_hull=false;
uniform bool ship_sail=false;
uniform bool ship_center_out=false;
uniform vec2 ship_phase=vec2(.02,.30);
uniform vec2 ship_warp_phase=vec2(.54,.82);
uniform vec2 ship_crest_phase=vec2(.90,.995);
uniform vec3 ship_form_origin=vec3(0.);
uniform vec3 ship_form_axis=vec3(0.,1.,0.);
uniform vec2 ship_form_bounds=vec2(0.,1.);
uniform sampler2D ship_seal_map:filter_linear_mipmap,repeat_disable;
uniform sampler2D ship_weft_map:filter_linear_mipmap,repeat_disable;
uniform sampler2D ship_plain_cloth:source_color,filter_linear_mipmap_anisotropic,repeat_disable;
uniform vec3 build_color=vec3(1.,.69,.33);
uniform float build_gain=1.;
uniform float print_progress=1.0;
uniform float print_height=1.0;
uniform vec3 print_origin=vec3(0.0);
uniform vec3 print_x=vec3(1,0,0);
uniform vec3 print_y=vec3(0,1,0);
uniform vec3 print_z=vec3(0,0,1);
uniform float print_power=1.0;
uniform sampler2D interaction_pattern:filter_linear_mipmap;
uniform vec2 interaction_mask_center=vec2(.5);
uniform float interaction_mask_radius=.39;
uniform vec3 interaction_center=vec3(0.);
uniform vec3 interaction_axis=vec3(0.,1.,0.);
uniform vec3 interaction_x=vec3(1.,0.,0.);
uniform vec3 interaction_z=vec3(0.,0.,1.);
uniform float interaction_gain=0.;
uniform vec3 interaction_crown=vec3(0.);
uniform float interaction_crown_gain=0.;
uniform bool record_vinyl=false;
uniform bool clip_enabled=false;
uniform vec3 clip_normal=vec3(0,0,1);
uniform float clip_d=0.0;
varying float world_y;
varying vec3 world_position;
void vertex(){world_position=(MODEL_MATRIX*vec4(VERTEX,1.0)).xyz;world_y=world_position.y;}
void fragment(){
 vec3 record_local=vec3(dot(world_position-print_origin,print_x),dot(world_position-print_origin,print_y),dot(world_position-print_origin,print_z));
 float build_height=clamp(record_local.y/max(.01,print_height),0.0,1.0);
 bool record_ghost=false;
 bool ship_thread_only=false;
 float ship_thread_tip=0.;
 float physical_front=print_progress+(metallic>.8?.035:0.);
 if(butterfly_body)physical_front=smoothstep(.03,.44,print_progress);
 if(butterfly_wing){
  vec3 delta=world_position-wing_origin;
  build_height=max(0.,dot(delta,wing_outward))/wing_span;
  physical_front=smoothstep(wing_start,wing_end,print_progress)+(metallic>.8?.025:0.);
  if(wing_seal_kind>0){
   vec2 uv=(vec2(dot(delta,wing_outward),dot(delta,wing_vertical))-wing_seal_bounds.xy)/wing_seal_bounds.zw;uv.y=1.-uv.y;
   build_height=texture(wing_seal_map,uv).r;
   physical_front=smoothstep(wing_seal_start,wing_seal_end,print_progress);
   if(record_print && print_progress<=wing_seal_start)discard;
  }
 }
 if(ship_part){
  float position=dot(world_position-ship_form_origin,ship_form_axis);
  build_height=ship_center_out?abs(position)/max(.001,ship_form_bounds.y):clamp((position-ship_form_bounds.x)/max(.001,ship_form_bounds.y),0.,1.);
  physical_front=smoothstep(ship_phase.x,ship_phase.y,print_progress);
  if(record_print && print_progress<=ship_phase.x)discard;
 }
 if(ship_hull){
  build_height=texture(ship_seal_map,UV).r;
  physical_front=smoothstep(ship_phase.x,ship_phase.y,print_progress);
  if(record_print && print_progress<=ship_phase.x)discard;
 }
 if(ship_sail){
  // glTF imported V is one minus the authored mast-height coordinate.
  build_height=texture(ship_weft_map,UV).g;
  physical_front=smoothstep(ship_phase.x,ship_phase.y,print_progress);
  float warp_front=smoothstep(ship_warp_phase.x,ship_warp_phase.y,print_progress);
  if(record_print && build_height>physical_front && build_height<=warp_front && print_progress>ship_warp_phase.x){
   ship_thread_only=texture(ship_weft_map,UV).r>.35;
   ship_thread_tip=1.-smoothstep(0.,.065,abs(build_height-warp_front));
  }
  if(record_print && print_progress<=ship_warp_phase.x)discard;
 }
 if(record_print && (print_progress<.001 || (build_height>physical_front && !ship_thread_only)))discard;
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
 METALLIC=metallic*(has_metallic?dot(texture(metallic_map,UV),metallic_channel):1.);
 if(ship_sail && METALLIC>.15){
  float embroidery=smoothstep(ship_crest_phase.x,ship_crest_phase.y,print_progress);
  ALBEDO=mix(texture(ship_plain_cloth,UV).rgb,ALBEDO,embroidery);METALLIC*=embroidery;
 }
 ROUGHNESS=clamp((has_roughness?texture(roughness_map,UV).g:roughness)*roughness_scale+roughness_offset,roughness_floor,.8);
 if(has_normal){NORMAL_MAP=texture(normal_map,UV).rgb;NORMAL_MAP_DEPTH=normal_depth;}
 ANISOTROPY=anisotropy_strength;ANISOTROPY_FLOW=vec2(1,0);
 if(record_vinyl){
  vec2 disc_uv=(UV-vec2(.5))*2.0;float radius=length(disc_uv);
  float detail=1.0-smoothstep(.006,.025,fwidth(radius));float groove=sin(radius*402.1239)*detail;
  ALBEDO*=.82+groove*.06;ROUGHNESS=.30+groove*.025;
  ANISOTROPY=.48;ANISOTROPY_FLOW=length(disc_uv)>.001?normalize(vec2(-disc_uv.y,disc_uv.x)):vec2(1,0);
 }
 SPECULAR=specular_strength;CLEARCOAT=coat;CLEARCOAT_ROUGHNESS=coat_roughness;
 EMISSION=emission_color.rgb*emission_energy*power;
 if(interaction_gain>0. && metallic>.8){
  vec3 p=world_position-interaction_center;
  float region=1.-smoothstep(.050,.055,length(p));
  float angle=atan(dot(p,interaction_z),dot(p,interaction_x));
  vec2 direction=vec2(cos(angle),sin(angle));
  float art=texture(interaction_pattern,interaction_mask_center+interaction_mask_radius*direction).r;
  art=max(art,texture(interaction_pattern,interaction_mask_center+(interaction_mask_radius-.003)*direction).r);
  art=max(art,texture(interaction_pattern,interaction_mask_center+(interaction_mask_radius+.003)*direction).r);
  float band=1.-smoothstep(.0015,.004,abs(dot(p,interaction_axis)));
  EMISSION+=vec3(1.,.56,.17)*interaction_gain*region*(.10+band*art*5.0);
 }
 if(interaction_crown_gain>0. && metallic<.5){
  float region=1.-smoothstep(.034,.038,length(world_position-interaction_crown));
  EMISSION+=vec3(1.,.025,.006)*interaction_crown_gain*region*.30;
 }
 if(instrument_gain>=0.0){
  vec3 filament=texture(instrument_profile,vec2(.75,.08+fract(UV.y*.75-instrument_time*.13)*.34)).rgb;
  float chase=pow(.5+.5*sin(world_y*8.0+world_position.x*3.0-instrument_time*5.0),5.0);
  EMISSION+=vec3(1.0,.62,.23)*instrument_gain*power*(.60+chase*.8)*(vec3(.50)+filament);
 }
 if(scan_amount>0.0){float edge=1.0-smoothstep(.0,.010,abs(height-boundary));EMISSION+=vec3(5.0,.22,.04)*edge;}
 if(scaffold){ALBEDO=vec3(.08,.02,.008);METALLIC=0.;EMISSION=archive*vec3(6.,1.3,.4);}
 if(formation<.9999){float edge=1.0-smoothstep(.0,.12,abs(formation_mask-formation));EMISSION+=(vec3(1.0,.48,.16)*edge+forming*2.0)*(1.0-formation)*3.0;}
 if(record_print && print_progress<.9999){
  bool ship=ship_part||ship_hull||ship_sail;
  float edge_width=ship?max(.018,min(.08,fwidth(build_height)*1.5)):.018;
  float edge=1.0-smoothstep(.0,edge_width,((butterfly_body||butterfly_wing||ship)?abs(build_height-physical_front):abs(record_local.y-print_progress*print_height)));
  if(ship)ALBEDO=mix(ALBEDO,vec3(.70,.30,.055),edge*.45);
  EMISSION+=((butterfly_body||butterfly_wing)?vec3(1.,.33,.025)*(wing_seal_kind>0?.85:1.8):build_color*6.0)*edge*print_power*build_gain;
  if(record_ghost){ALBEDO=vec3(.006,.016,.022);METALLIC=0.0;ROUGHNESS=.7;EMISSION=vec3(.14,.48,.80)*print_power*2.4;}
 }
 if(ship_thread_only){ALBEDO=vec3(.65,.35,.08);METALLIC=.35;ROUGHNESS=.5;EMISSION=vec3(1.,.52,.14)*(.5+ship_thread_tip*.8)*print_power;}
}
