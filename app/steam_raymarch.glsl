#[compute]
#version 450
// Half-resolution integration of the real Mantaflow scalar density cache.
layout(local_size_x=8,local_size_y=8,local_size_z=1) in;
layout(set=0,binding=0) uniform sampler2D scene_depth;
layout(set=0,binding=1) uniform sampler3D density_a;
layout(set=0,binding=2) uniform sampler3D density_b;
layout(set=0,binding=3) uniform sampler3D occupancy;
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

vec3 view_at(vec2 uv,float depth){vec4 v=p.inv_projection*vec4(uv*2.0-1.0,depth,1.0);return v.xyz/v.w;}
float density(vec3 wp){
    vec3 cp=(p.world_to_cache*vec4(wp,1.0)).xyz;
    if(cp.y<0.0)return 0.0;
    vec3 uv=(cp-p.cache_min_step.xyz)/(p.cache_max_mix.xyz-p.cache_min_step.xyz);
    if(any(lessThan(uv,vec3(0)))||any(greaterThan(uv,vec3(1))))return 0.0;
    float d=mix(textureLod(density_a,uv,0.0).r,textureLod(density_b,uv,0.0).r,p.cache_max_mix.w);
    return max(0.0,d*p.world_min_gain.w*p.world_max_density.w);
}
float empty_step(vec3 wp,vec3 dir){
    if(p.settings.z<.5)return 0.0;
    vec3 cp=(p.world_to_cache*vec4(wp,1.0)).xyz;
    vec3 cd=(p.world_to_cache*vec4(dir,0.0)).xyz;
    vec3 cell_size=(p.cache_max_mix.xyz-p.cache_min_step.xyz)/p.occupancy_size.xyz;
    vec3 uv=clamp((cp-p.cache_min_step.xyz)/(p.cache_max_mix.xyz-p.cache_min_step.xyz),vec3(0),vec3(.99999));
    if(textureLod(occupancy,uv,0.0).r>.1)return 0.0;
    vec3 lo=p.cache_min_step.xyz+floor(uv*p.occupancy_size.xyz)*cell_size;
    vec3 target=mix(lo,lo+cell_size,step(vec3(0.0),cd));
    vec3 safe_cd=mix(vec3(1e-8),cd,greaterThan(abs(cd),vec3(1e-8)));
    vec3 t=(target-cp)/safe_cd;
    return max(.001,min(t.x,min(t.y,t.z))+.001);
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
    if(p.settings.z<.5)ds=max(ds,(end-begin)/float(limit-1));
    float cosine=max(.001,-dot(direction,p.camera_world[2].xyz));
    vec3 light_direction=normalize(vec3(-.55,.48,-.68));
    float scatter=.12+.24*pow(max(dot(direction,light_direction),0.0),5.0);
    float remaining=1.0,t=begin+ds*.5;
    vec3 result=vec3(0);
    for(int i=0;i<512;i++){
        if(i>=limit||t>end)break;
        vec3 wp=origin+direction*t;
        float skip=empty_step(wp,direction);
        if(skip>0.0){t+=skip;continue;}
        float d=density(wp)*clamp((opaque_t-t)*cosine/max(.001,p.settings.w),0.0,1.0);
        if(d>.007){
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
