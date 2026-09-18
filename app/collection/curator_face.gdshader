shader_type spatial;
render_mode diffuse_burley,specular_schlick_ggx;
uniform sampler2D expressions:source_color,filter_linear_mipmap;
uniform float expression=0.;
uniform float previous_expression=0.;
uniform float transition=1.;
uniform float brightness=1.;
uniform vec2 gaze=vec2(0.);
uniform float face_specular=.5;
uniform float face_coat=.4;
uniform float face_roughness=.23;
uniform float scan_amount=0.;
uniform float scan_min=.62;
uniform float scan_max=3.8;
varying float world_y;
void vertex(){world_y=(MODEL_MATRIX*vec4(VERTEX,1.)).y;}
float face(float tile,vec2 uv){
 vec2 offset=vec2(mod(tile,4.),floor(tile/4.));
 vec4 sample=texture(expressions,(offset+clamp(uv,vec2(.006),vec2(.994)))/vec2(4.,2.));
 return max(sample.r,max(sample.g,sample.b))*sample.a;
}
void fragment(){
 float height=clamp((world_y-scan_min)/max(.01,scan_max-scan_min),0.,1.);
 if(scan_amount>0. && height>1.-scan_amount)discard;
 vec2 uv=(UV-.5)*1.25+.5-gaze;
 float pixels=mix(face(previous_expression,uv),face(expression,uv),transition);
 ALBEDO=vec3(.004,.005,.006);METALLIC=.08;ROUGHNESS=face_roughness;SPECULAR=face_specular;CLEARCOAT=face_coat;CLEARCOAT_ROUGHNESS=.1;
 EMISSION=vec3(1.,.46,.08)*pixels*brightness*2.8;
}
