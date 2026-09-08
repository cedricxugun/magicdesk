shader_type spatial;
render_mode unshaded,cull_front,depth_draw_never,depth_test_disabled,fog_disabled;

uniform sampler3D curl_field:repeat_enable,filter_linear;
uniform sampler2D scene_depth:hint_depth_texture,repeat_disable,filter_nearest;
uniform float activity=0.0;
uniform float flow_time=0.0;
uniform int ring_count=0;
uniform vec4 ring_data[3];
uniform vec4 stream_points[24];
uniform vec4 stream_lower[6];
uniform vec4 stream_upper[6];
uniform vec3 core_position=vec3(0.0,2.2,0.0);
uniform vec3 bounds_lower=vec3(-2.5,.55,-2.5);
uniform vec3 bounds_upper=vec3(2.5,3.0,2.5);
uniform bool physical_enabled=false;
uniform sampler3D density_frame_a:repeat_disable,filter_linear;
uniform sampler3D density_frame_b:repeat_disable,filter_linear;
uniform vec3 physical_bounds_min=vec3(-3.1,.5,-3.1);
uniform vec3 physical_bounds_max=vec3(3.1,4.8,3.1);
uniform float physical_mix=0.0;
uniform float physical_density_scale=1.0;
uniform float physical_gain=0.0;
uniform float physical_step=.025;
uniform mat4 world_to_physical=mat4(1.0);
uniform bool physical_occupancy_enabled=false;
uniform sampler3D physical_occupancy:repeat_disable,filter_nearest;
uniform vec3 physical_occupancy_size=vec3(32.0,20.0,32.0);
uniform int max_march_steps=128;
uniform vec3 core_light_position=vec3(0.0,2.2,0.0);
uniform vec4 core_light_color:source_color=vec4(1.0);
uniform float core_light_energy=0.0;
uniform float core_light_range=1.0;
uniform int core_shadow_steps=3;
varying vec3 ray_surface;
varying vec3 ray_origin;
varying mat4 object_to_world;

void vertex(){
    ray_surface=VERTEX;
    ray_origin=(inverse(MODEL_MATRIX)*vec4(CAMERA_POSITION_WORLD,1.0)).xyz;
    object_to_world=MODEL_MATRIX;
}

vec3 curl_velocity(vec3 p){return (texture(curl_field,p*.175).rgb*2.0-1.0);}

float ring_density(vec3 p,vec4 event){
    float age=event.x;
    if(age<0.0 || age>3.25 || event.y<.001){return 0.0;}
    bool reverse=event.z>.5;
    float age_growth=1.0-exp(-age*3.4);
    float angle=atan(p.z,p.x);
    float sector=.50+.31*sin(angle*3.0+.71)+.18*sin(angle*5.0-1.17);
    float radius=reverse ? .96-age_growth*.33 : .52+1.30*age_growth;
    radius+=sin(angle*4.0+.4)*.11*age_growth;
    float height=1.12+max(age-.18,0.0)*(.14+.43*sector);
    float thickness=.105+.275*(1.0-exp(-age*7.0));
    float radial=length(p.xz);
    vec2 section=vec2(radial-radius,(p.y-height)*.93);
    if(length(section)>thickness+.33){return 0.0;}
    vec3 curl=curl_velocity(p+vec3(event.w,flow_time*.16,-flow_time*.09));
    vec3 wp=p+curl*(.12+.07*age_growth);
    radial=length(wp.xz);
    section=vec2(radial-radius,(wp.y-height)*.93);
    float sdf=length(section);
    // Material moves around the torus cross-section: a genuine rolling density field.
    float theta=atan(wp.z,wp.x);
    float rotation=age*(reverse ? -4.8 : 5.2)+sin(theta*3.0)*.22;
    vec2 advected=mat2(vec2(cos(rotation),sin(rotation)),vec2(-sin(rotation),cos(rotation)))*section;
    vec3 q=vec3(cos(theta)*(radius+advected.x),advected.y+height,sin(theta)*(radius+advected.x));
    q-=curl_velocity(q+vec3(.71,age*.12,.23))*.20;
    float large=texture(curl_field,q*.19+vec3(event.w*.07,.31,.17)).a;
    float medium=texture(curl_field,q*.47+vec3(.27,age*.027,.53)).a;
    float fine=texture(curl_field,q*1.12+vec3(.73,.21,-age*.04)).a;
    float turbulent=(large-.5)*.19+(medium-.5)*.115+(fine-.5)*.048;
    float shape=1.0-smoothstep(thickness*.34,thickness+.05,sdf-turbulent);
    float raw=large*.58+medium*.28+fine*.14;
    float threshold=.425+.18*(1.0-shape);
    float core=smoothstep(threshold,threshold+.175,raw)*shape;
    float onset=smoothstep(0.0,.07,age);
    float dissipation=1.0-smoothstep(reverse ?.24: .54+sector*.45,reverse ?.9:1.30+sector*.65,age);
    return core*event.y*onset*dissipation;
}

float stream_density(vec3 p,int index){
    vec4 lo=stream_lower[index];vec3 hi=stream_upper[index].xyz;
    if(lo.w<.004 || any(lessThan(p,lo.xyz)) || any(greaterThan(p,hi))){return 0.0;}
    vec3 warped=p+curl_velocity(p+vec3(0.0,flow_time*.11,.41))*.21;
    float shape=0.0;
    for(int k=0;k<3;k++){
        vec4 aa=stream_points[index*4+k];vec4 bb=stream_points[index*4+k+1];
        vec3 d=bb.xyz-aa.xyz;
        float t=clamp(dot(warped-aa.xyz,d)/max(dot(d,d),.0001),0.0,1.0);
        float r=mix(aa.w,bb.w,t);
        float distance_to_axis=length(warped-mix(aa.xyz,bb.xyz,t));
        shape=max(shape,1.0-smoothstep(r*.30,r,distance_to_axis));
    }
    if(shape<.001){return 0.0;}
    vec3 q=p-curl_velocity(p+vec3(.21,flow_time*.15,.61))*.18;
    float broad=texture(curl_field,q*.29+vec3(.4,-flow_time*.07,0)).a;
    float middle=texture(curl_field,q*.58+vec3(.17,.6,.37)).a;
    float fine=texture(curl_field,q*1.29+vec3(.2,.3,.7)).a;
    float raw=broad*.58+middle*.28+fine*.14;
    float threshold=.405+.20*(1.0-shape);
    return smoothstep(threshold,threshold+.18,raw)*shape*lo.w*.72;
}

float density_at(vec3 p){
    if(physical_enabled){
        vec3 cache_p=(world_to_physical*vec4(p,1.0)).xyz;
        // Static y=0 ground collider: wavelet interpolation must not emit steam
        // under the same physical floor used by the Mantaflow simulation.
        if(cache_p.y<0.0){return 0.0;}
        vec3 uv=(cache_p-physical_bounds_min)/(physical_bounds_max-physical_bounds_min);
        if(any(lessThan(uv,vec3(0.0))) || any(greaterThan(uv,vec3(1.0)))){return 0.0;}
        float a=texture(density_frame_a,uv).r;float b=texture(density_frame_b,uv).r;
        return max(0.0,mix(a,b,physical_mix)*physical_density_scale*physical_gain);
    }
    if(p.y<.57 || p.y>3.65){return 0.0;}
    float density=0.0;
    for(int j=0;j<3;j++){if(j<ring_count){density+=ring_density(p,ring_data[j]);}}
    for(int j=0;j<6;j++){density+=stream_density(p,j);}
    return min(density,1.8)*smoothstep(.57,.82,p.y);
}

float empty_distance(vec3 p){
    if(physical_enabled){return 0.0;}
    float distance_to_field=10.0;
    for(int j=0;j<3;j++){
        if(j>=ring_count || ring_data[j].x<0.0){continue;}
        vec4 event=ring_data[j];float age=event.x;
        float angle=atan(p.z,p.x);
        float sector=.50+.31*sin(angle*3.0+.71)+.18*sin(angle*5.0-1.17);
        float growth=1.0-exp(-age*3.4);
        float radius=event.z>.5 ?.96-growth*.33 : .52+1.30*growth;
        radius+=sin(angle*4.0+.4)*.11*growth;
        float height=1.12+max(age-.18,0.0)*(.14+.43*sector);
        float thickness=.105+.275*(1.0-exp(-age*7.0));
        float d=length(vec2(length(p.xz)-radius,(p.y-height)*.93))-thickness-.31;
        distance_to_field=min(distance_to_field,max(d,0.0));
    }
    for(int j=0;j<6;j++){
        if(stream_lower[j].w<.004){continue;}
        vec3 d=max(max(stream_lower[j].xyz-p,p-stream_upper[j].xyz),vec3(0.0));
        distance_to_field=min(distance_to_field,length(d));
    }
    return distance_to_field;
}

float physical_empty_step(vec3 p,vec3 direction){
    vec3 cp=(world_to_physical*vec4(p,1.0)).xyz;
    vec3 cd=(world_to_physical*vec4(direction,0.0)).xyz;
    vec3 uv=(cp-physical_bounds_min)/(physical_bounds_max-physical_bounds_min);
    if(texture(physical_occupancy,clamp(uv,vec3(0.0),vec3(.99999))).r>.1){return 0.0;}
    vec3 cell=floor(clamp(uv,vec3(0.0),vec3(.99999))*physical_occupancy_size);
    vec3 cell_size=(physical_bounds_max-physical_bounds_min)/physical_occupancy_size;
    vec3 low=physical_bounds_min+cell*cell_size;
    vec3 high=low+cell_size;
    vec3 target=mix(low,high,step(vec3(0.0),cd));
    vec3 t=(target-cp)/cd;
    return max(.001,min(t.x,min(t.y,t.z))+.001);
}

void fragment(){
    if(activity<.001){discard;}
    vec3 direction=normalize(ray_surface-ray_origin);
    vec3 world_direction=normalize((object_to_world*vec4(direction,0.0)).xyz);
    vec3 world_origin=(object_to_world*vec4(ray_origin,1.0)).xyz;
    vec3 inv=1.0/world_direction;
    vec3 a=(bounds_lower-world_origin)*inv;
    vec3 b=(bounds_upper-world_origin)*inv;
    vec3 lo=min(a,b);vec3 hi=max(a,b);
    float begin=max(0.0,max(lo.x,max(lo.y,lo.z)));
    float end=min(hi.x,min(hi.y,hi.z));
    if(end<=begin){discard;}
    vec4 depth_point=INV_PROJECTION_MATRIX*vec4(SCREEN_UV*2.0-1.0,texture(scene_depth,SCREEN_UV).r,1.0);
    float opaque_depth=-depth_point.z/depth_point.w;
    float camera_depth_cosine=-(VIEW_MATRIX*vec4(world_direction,0.0)).z;
    end=min(end,opaque_depth/max(camera_depth_cosine,.001));
    if(end<=begin){discard;}
    float step_world=physical_enabled ? physical_step : .025;
    if(physical_enabled && !physical_occupancy_enabled){step_world=max(step_world,(end-begin)/float(max_march_steps-1));}
    vec3 light_dir=normalize(vec3(-.55,.48,-.68));
    vec3 transmission=vec3(0.0);float remaining=1.0;
    float distance=begin+step_world*.5;
    for(int i=0;i<256;i++){
        if(i>=max_march_steps){break;}
        if(distance>end){break;}
        vec3 wp=world_origin+world_direction*distance;
        if(physical_enabled && physical_occupancy_enabled){
            float jump=physical_empty_step(wp,world_direction);
            if(jump>.0){distance+=jump;continue;}
        }
        float empty=empty_distance(wp);
        if(empty>.045){distance+=max(.04,empty*.78);continue;}
        float sample_depth=-(VIEW_MATRIX*vec4(wp,1.0)).z;
        if(sample_depth>opaque_depth){break;}
        float density=density_at(wp)*clamp((opaque_depth-sample_depth)/.09,0.0,1.0);
        if(density>.007){
            float optical_to_light=0.0;
            for(int s=1;s<=6;s++){
                float distance_to_light=float(s)*.105;
                optical_to_light+=density_at(wp+light_dir*distance_to_light)*.105;
            }
            float shadow=exp(-optical_to_light*7.4);
            float forward_scatter=.12+.24*pow(max(dot(world_direction,light_dir),0.0),5.0);
            vec3 illumination=vec3(.18)+vec3(1.15)*shadow*(.78+forward_scatter);
            // White steam scatters the actual core light. Its scalar physical
            // density and base color never change when the core changes color.
            vec3 to_core=core_light_position-wp;
            float core_distance=length(to_core);
            if(core_light_energy>.001 && core_distance<core_light_range){
                vec3 core_direction=to_core/max(core_distance,.001);
                float core_tau=0.0;
                float core_ds=core_distance/float(core_shadow_steps);
                for(int s=0;s<4;s++){
                    if(s>=core_shadow_steps){break;}
                    core_tau+=density_at(wp+core_direction*(float(s)+.5)*core_ds)*core_ds;
                }
                float edge=clamp(1.0-core_distance/core_light_range,0.0,1.0);
                float falloff=edge*edge/(.40+core_distance*core_distance);
                illumination+=core_light_color.rgb*core_light_energy*2.0*falloff*exp(-core_tau*6.0);
            }
            float step_opacity=1.0-exp(-density*step_world*4.6);
            transmission+=remaining*step_opacity*illumination;
            remaining*=1.0-step_opacity;
            if(remaining<.015){break;}
        }
        distance+=step_world;
    }
    float opacity=1.0-remaining;
    if(opacity<.004){discard;}
    ALBEDO=transmission/max(opacity,.001);ALPHA=opacity;
}
