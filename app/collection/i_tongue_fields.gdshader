shader_type spatial;
render_mode cull_back;
uniform sampler2D center_field : filter_linear, repeat_disable;
uniform sampler2D width_field : filter_linear, repeat_disable;
uniform sampler2D normal_field : filter_linear, repeat_disable;
uniform float feed : hint_range(0.0,1.0)=0.0;
uniform float row_count=361.0;
uniform float frame_count=257.0;
uniform bool field_v_flipped=false;
uniform bool data_v_flipped=true;
uniform float skin_offset=0.0;
uniform vec4 base_color : source_color = vec4(0.65,0.63,0.61,1.0);
uniform float metalness=0.96;
uniform float roughness_factor=0.28;
uniform sampler2D roughness_map : hint_default_white, filter_linear_mipmap, repeat_enable;
uniform vec4 roughness_channel=vec4(1.,0.,0.,0.);
uniform sampler2D finish_normal : hint_normal, filter_linear_mipmap, repeat_enable;
uniform float finish_normal_strength=0.8;
uniform bool preserve_authored_frame=false;
vec4 row_center(float x,float t){return textureLod(center_field,vec2(x,t),0.);}
vec3 point_at(float x,float t,float w,float offset){
    vec4 c=row_center(x,t);vec3 width=textureLod(width_field,vec2(x,t),0.).xyz;vec3 n=textureLod(normal_field,vec2(x,t),0.).xyz;
    return c.xyz+width*(.5-w)+n*((c.w-1.)*sin(3.14159265359*w)+offset);
}
void vertex(){
    float t=(clamp(feed,0.,1.)*(frame_count-1.)+.5)/frame_count;if(field_v_flipped){t=1.-t;}
    float code=data_v_flipped ? 1.-UV2.y : UV2.y;float back=step(1.5,code);float w=clamp(code-back*2.,0.,1.);
    float offset=skin_offset+(back-.5)*.0015;float x=UV2.x;
    vec4 c=row_center(x,t);vec3 width=textureLod(width_field,vec2(x,t),0.).xyz;vec3 n=textureLod(normal_field,vec2(x,t),0.).xyz;
    VERTEX=c.xyz+width*(.5-w)+n*((c.w-1.)*sin(3.14159265359*w)+offset);
    float lo=max(.5/row_count,x-1./row_count);float hi=min(1.-.5/row_count,x+1./row_count);
    vec3 ds=point_at(hi,t,w,offset)-point_at(lo,t,w,offset);
    vec3 dw=-width+n*(c.w-1.)*3.14159265359*cos(3.14159265359*w);
    vec3 frame_n=normalize(cross(ds,dw))*(1.-2.*back);
    if(preserve_authored_frame){
    vec3 frame_t=normalize(ds-frame_n*dot(frame_n,ds));
    vec3 frame_b=normalize(cross(frame_n,frame_t))*CUSTOM0.w;
    vec3 rest_t=CUSTOM0.xyz;vec3 rest_n=CUSTOM1.xyz;
    vec3 rest_b=normalize(cross(rest_n,rest_t))*CUSTOM0.w;
    mat3 transport_frame=mat3(frame_t,frame_b,frame_n)*transpose(mat3(rest_t,rest_b,rest_n));
    NORMAL=normalize(transport_frame*NORMAL);
    TANGENT=normalize(transport_frame*TANGENT);
    BINORMAL=normalize(transport_frame*BINORMAL);
    }else{
        // Retained imported-LOD diagnostic mode has no custom rest-frame data.
        NORMAL=frame_n;TANGENT=normalize(ds);BINORMAL=normalize(dw);
    }
}
void fragment(){
    ALBEDO=base_color.rgb;METALLIC=metalness;
    ROUGHNESS=clamp(roughness_factor*dot(texture(roughness_map,UV),roughness_channel),.02,1.);
    NORMAL_MAP=texture(finish_normal,UV).rgb;NORMAL_MAP_DEPTH=finish_normal_strength;
}
