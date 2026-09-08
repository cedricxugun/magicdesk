#[compute]
#version 450
layout(local_size_x=8,local_size_y=8,local_size_z=1) in;
layout(rgba16f,set=0,binding=0) uniform restrict image2D scene_color;
layout(set=0,binding=1) uniform sampler2D scene_depth;
layout(set=0,binding=2) uniform sampler2D steam_image;
layout(set=0,binding=3) uniform sampler2D steam_depth;
layout(std430,set=0,binding=4) readonly buffer Parameters {
    mat4 inv_projection;mat4 camera_world;mat4 world_to_cache;
    vec4 cache_min_step;vec4 cache_max_mix;vec4 world_min_gain;vec4 world_max_density;
    vec4 core_position_range;vec4 core_color_energy;vec4 sizes;vec4 settings;vec4 occupancy_size;
} p;
float view_depth(vec2 uv,float z){vec4 v=p.inv_projection*vec4(uv*2.0-1.0,max(z,1e-7),1);return -v.z/v.w;}
void main(){
    ivec2 pixel=ivec2(gl_GlobalInvocationID.xy),full_size=ivec2(p.sizes.xy),low_size=ivec2(p.sizes.zw);
    if(any(greaterThanEqual(pixel,full_size)))return;
    vec2 uv=(vec2(pixel)+.5)/p.sizes.xy;
    float target_depth=view_depth(uv,texelFetch(scene_depth,pixel,0).r);
    vec2 low_pos=uv*p.sizes.zw-.5,fract_pos=fract(low_pos);
    ivec2 low_base=ivec2(floor(low_pos));
    vec4 accumulated=vec4(0),nearest=vec4(0);float weights=0.0,best=1e20;
    // Bilateral upsample keeps full-resolution opaque silhouettes and alpha.
    for(int y=0;y<2;y++)for(int x=0;x<2;x++){
        ivec2 q=clamp(low_base+ivec2(x,y),ivec2(0),low_size-1);
        float z=texelFetch(steam_depth,q,0).r;
        float difference=abs(z-target_depth);
        vec4 v=texelFetch(steam_image,q,0);
        if(difference<best){best=difference;nearest=v;}
        float spatial=(x==0?1.0-fract_pos.x:fract_pos.x)*(y==0?1.0-fract_pos.y:fract_pos.y);
        float tolerance=.015+.002*min(z,target_depth);
        float weight=spatial*exp(-difference/max(.001,tolerance));
        accumulated+=v*weight;weights+=weight;
    }
    vec4 steam=weights>.00001?accumulated/weights:nearest;
    // No history, stochastic jitter, screen-sized alpha fill, or separate overlay.
    if(steam.a<.0001)return;
    vec4 original=imageLoad(scene_color,pixel);
    float transmittance=1.0-clamp(steam.a,0.0,1.0);
    imageStore(scene_color,pixel,vec4(steam.rgb+original.rgb*transmittance,steam.a+original.a*transmittance));
}
