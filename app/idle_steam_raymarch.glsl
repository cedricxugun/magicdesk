#[compute]
#version 450
// Real looping idle Mantaflow density; height/radius estimate age, recorded yaw
// supplies each parcel's birth orientation. Existing tails survive pause/reverse.
layout(local_size_x=8,local_size_y=8,local_size_z=1) in;
layout(set=0,binding=0) uniform sampler2D scene_depth;
layout(set=0,binding=1) uniform sampler3D density_a;
layout(set=0,binding=2) uniform sampler3D density_b;
layout(rgba16f,set=0,binding=4) uniform restrict writeonly image2D steam_image;
layout(r32f,set=0,binding=5) uniform restrict writeonly image2D steam_depth;
layout(std430,set=0,binding=6) readonly buffer Parameters {
    mat4 inv_projection;mat4 camera_world;mat4 world_to_cache;
    vec4 cache_min_step;vec4 cache_max_mix;
    vec4 world_min_gain;vec4 world_max_density;
    vec4 core_position_range;vec4 core_color_energy;
    vec4 sizes; // full xy, low zw
    vec4 settings; // march limit, core shadow count, occupancy enabled, depth softness
    vec4 occupancy_size;
} p;
layout(std430,set=0,binding=7) readonly buffer BirthHistory {
    vec4 info; // count, sample interval, current yaw, history span
    vec4 lower_source; // six emitters: radius, height, initial up velocity, buoyancy
    vec4 valve_source; // single valve local xyz, plume selector width
    vec4 valve_flow; // initial up velocity, buoyancy, attached nozzle length, radial flow speed
    vec4 valve_displacement; // new fixed mount minus the original cache mount, in turntable space
    float angles[64]; // continuous yaw, newest first; no modulo discontinuity
} h;

float birth_yaw(float age){
    float f=clamp(age/max(h.info.y,.001),0.0,h.info.x-1.0);
    int index=int(f),next_index=min(index+1,int(h.info.x)-1);
    return mix(h.angles[index],h.angles[next_index],fract(f));
}
vec3 undo_yaw(vec3 point,float yaw){
    float c=cos(yaw),s=sin(yaw);
    // Inverse Godot Basis(UP, yaw), preserving physical height.
    return vec3(c*point.x-s*point.z,point.y,s*point.x+c*point.z);
}
float rise_age(float height,float velocity,float buoyancy){
    float rise=max(0.0,height-h.valve_flow.z);
    float acceleration=max(.001,buoyancy);
    float age=(sqrt(velocity*velocity+2.0*acceleration*rise)-velocity)/acceleration;
    // A short attached nozzle region follows the live valve; beyond it the
    // continuous history field supplies the historical birth orientation.
    return age*smoothstep(.015,.09,height);
}
vec4 historical_cache_point(vec3 wp){
    vec3 point=(p.world_to_cache*vec4(wp,1.0)).xyz;
    float lower_age=rise_age(point.y-h.lower_source.y,h.lower_source.z,h.lower_source.w);
    float outward=max(0.0,length(point.xz)-h.lower_source.x-.08);
    lower_age=max(lower_age,outward/max(.05,h.valve_flow.w)*.35);
    float valve_age=rise_age(point.y-h.valve_source.y,h.valve_flow.x,h.valve_flow.y);
    vec3 valve_point=undo_yaw(point,birth_yaw(valve_age));
    float from_valve=length(valve_point.xz-h.valve_source.xz);
    float valve_weight=smoothstep(h.valve_source.y-.16,h.valve_source.y-.015,point.y);
    valve_weight*=1.0-smoothstep(.20,h.valve_source.w+.08*valve_age,from_valve);
    float age=mix(lower_age,valve_age,valve_weight);
    return vec4(undo_yaw(point,birth_yaw(age)),age);
}

vec3 view_at(vec2 uv,float depth){vec4 v=p.inv_projection*vec4(uv*2.0-1.0,depth,1.0);return v.xyz/v.w;}
float reference_density(vec3 cp){
    if(cp.y<0.0)return 0.0;
    vec3 uv=(cp-p.cache_min_step.xyz)/(p.cache_max_mix.xyz-p.cache_min_step.xyz);
    if(any(lessThan(uv,vec3(0)))||any(greaterThan(uv,vec3(1))))return 0.0;
    float d=mix(textureLod(density_a,uv,0.0).r,textureLod(density_b,uv,0.0).r,p.cache_max_mix.w);
    return max(0.0,d*p.world_min_gain.w*p.world_max_density.w);
}
float source_gate(float age){
    return p.occupancy_size.x<0.0?1.0:smoothstep(p.occupancy_size.x,p.occupancy_size.x+.08,age);
}
float valve_region(vec3 cp){
    float age=rise_age(cp.y-h.valve_source.y,h.valve_flow.x,h.valve_flow.y);
    float vertical=smoothstep(h.valve_source.y-.16,h.valve_source.y-.015,cp.y);
    return vertical*(1.0-smoothstep(.20,h.valve_source.w+.08*age,length(cp.xz-h.valve_source.xz)));
}
float density(vec3 wp){
    vec4 parcel=historical_cache_point(wp);
    float base=reference_density(parcel.xyz)*source_gate(parcel.w);
    if(dot(h.valve_displacement.xyz,h.valve_displacement.xyz)<.000001)return base;
    // The lower six source mouths retain the original cache and birth history.
    // Only the upper plume is retargeted; blended cache regions are partitioned
    // smoothly because the saved density volume has no per-source labels.
    base*=1.0-valve_region(parcel.xyz);
    vec3 point=(p.world_to_cache*vec4(wp,1.0)).xyz;
    float age=rise_age(point.y-h.valve_source.y-h.valve_displacement.y,h.valve_flow.x,h.valve_flow.y);
    vec3 upper=undo_yaw(point,birth_yaw(age))-h.valve_displacement.xyz;
    float weight=valve_region(upper);
    if(weight>.0001)base+=reference_density(upper)*weight*source_gate(age);
    return base;
}
void main(){
    ivec2 pixel=ivec2(gl_GlobalInvocationID.xy),sz=ivec2(p.sizes.zw);
    if(any(greaterThanEqual(pixel,sz)))return;
    vec2 uv=(vec2(pixel)+.5)/p.sizes.zw;
    ivec2 full_pixel=clamp(ivec2(uv*p.sizes.xy),ivec2(0),ivec2(p.sizes.xy)-1);
    // Integrate through the selected full-resolution sample: depth and ray agree.
    uv=(vec2(full_pixel)+.5)/p.sizes.xy;
    float z=texelFetch(scene_depth,full_pixel,0).r;
    vec3 opaque_view=view_at(uv,max(z,1e-7));
    float linear_depth=-opaque_view.z;
    imageStore(steam_depth,pixel,vec4(linear_depth));
    imageStore(steam_image,pixel,vec4(0));
    vec3 near_view=view_at(uv,1.0),far_view=view_at(uv,.00001);
    vec3 origin=(p.camera_world*vec4(near_view,1.0)).xyz;
    vec3 direction=normalize(mat3(p.camera_world)*(far_view-near_view));
    vec3 opaque_world=(p.camera_world*vec4(opaque_view,1.0)).xyz;
    float opaque_t=dot(opaque_world-origin,direction);
    vec3 inv_dir=1.0/direction;
    vec3 a=(p.world_min_gain.xyz-origin)*inv_dir,b=(p.world_max_density.xyz-origin)*inv_dir;
    vec3 lo=min(a,b),hi=max(a,b);
    float begin=max(0.0,max(lo.x,max(lo.y,lo.z)));
    float end=min(opaque_t,min(hi.x,min(hi.y,hi.z)));
    if(end<=begin||p.world_min_gain.w<.001)return;
    float ds=max(.003,p.cache_min_step.w);
    int limit=clamp(int(p.settings.x),32,512);
    // No occupancy jumps: the age-dependent warp is not a rigid DDA grid.
    ds=max(ds,(end-begin)/float(limit-1));
    float cosine=max(.001,-dot(direction,p.camera_world[2].xyz));
    vec3 light_direction=normalize(vec3(-.55,.48,-.68));
    float scatter=.12+.24*pow(max(dot(direction,light_direction),0.0),5.0);
    float remaining=1.0,t=begin+ds*.5;
    vec3 result=vec3(0);
    for(int i=0;i<512;i++){
        if(i>=limit||t>end)break;
        vec3 wp=origin+direction*t;
        float d=density(wp)*clamp((opaque_t-t)*cosine/max(.001,p.settings.w),0.0,1.0);
        if(d>.0007){
            float shadow_tau=0.0;
            for(int k=1;k<=6;k++)shadow_tau+=density(wp+light_direction*(float(k)*.105))*.105;
            vec3 illumination=vec3(.18)+vec3(1.15)*exp(-shadow_tau*7.4)*(.78+scatter);
            vec3 to_core=p.core_position_range.xyz-wp;float dc=length(to_core);
            if(p.core_color_energy.w>.001&&dc<p.core_position_range.w){
                int shadow_steps=clamp(int(p.settings.y),1,4);
                float cds=dc/float(shadow_steps),tau=0.0;
                vec3 cd=to_core/max(dc,.001);
                for(int k=0;k<4;k++){if(k>=shadow_steps)break;tau+=density(wp+cd*((float(k)+.5)*cds))*cds;}
                float edge=clamp(1.0-dc/p.core_position_range.w,0.0,1.0);
                illumination+=p.core_color_energy.rgb*p.core_color_energy.w*2.0*edge*edge/(.40+dc*dc)*exp(-tau*6.0);
            }
            float alpha=1.0-exp(-d*ds*4.6);
            result+=remaining*alpha*illumination;remaining*=1.0-alpha;
            if(remaining<.015)break;
        }
        t+=ds;
    }
    imageStore(steam_image,pixel,vec4(result,1.0-remaining));
}
