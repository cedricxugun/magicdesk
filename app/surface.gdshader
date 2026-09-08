shader_type spatial;
render_mode diffuse_burley, specular_schlick_ggx;

uniform vec4 base_color : source_color = vec4(1.0);
uniform sampler2D color_map : source_color, filter_linear_mipmap_anisotropic, repeat_enable;
uniform sampler2D rough_map : hint_default_white, filter_linear_mipmap_anisotropic, repeat_enable;
uniform sampler2D normal_map : hint_normal, filter_linear_mipmap_anisotropic, repeat_enable;
uniform bool use_color_map = false;
uniform bool use_rough_map = false;
uniform bool use_normal_map = false;
uniform float metalness = 0.0;
uniform float surface_roughness = 0.3;
uniform float normal_depth = 0.15;
uniform float coat = 0.0;
uniform float coat_roughness = 0.2;
uniform float brushed = 0.0;
uniform float patina = 0.0;
uniform float base_surface = 0.0;
uniform float enamel_balance = 0.0;
uniform float metal_tone = 1.0;
uniform vec4 enamel_tone : source_color = vec4(0.855,0.815,0.730,1.0);

varying vec3 surface_position;
varying vec3 surface_normal;

float hash31(vec3 p) {
    p = fract(p * 0.1031);
    p += dot(p, p.yzx + 33.33);
    return fract((p.x + p.y) * p.z);
}

float grain_noise(vec3 p) {
    vec3 i = floor(p);
    vec3 f = fract(p);
    f = f*f*(3.0-2.0*f);
    return mix(mix(mix(hash31(i),hash31(i+vec3(1,0,0)),f.x),
                   mix(hash31(i+vec3(0,1,0)),hash31(i+vec3(1,1,0)),f.x),f.y),
               mix(mix(hash31(i+vec3(0,0,1)),hash31(i+vec3(1,0,1)),f.x),
                   mix(hash31(i+vec3(0,1,1)),hash31(i+vec3(1,1,1)),f.x),f.y),f.z);
}

void vertex() {
    surface_position = VERTEX;
    surface_normal = NORMAL;
}

void fragment() {
    ALBEDO = base_color.rgb * (use_color_map ? texture(color_map, UV).rgb : vec3(1.0));
    if (metalness>0.5) { ALBEDO=min(ALBEDO*metal_tone,vec3(.88)); }
    METALLIC = metalness;
    ROUGHNESS = clamp(surface_roughness * (use_rough_map ? texture(rough_map, UV).g : 1.0), 0.16, 0.92);
    if (enamel_balance > 0.0) {
        // Keep the edge chips and faint staining, but quiet broad mottling so the
        // finish reads as fired glossy enamel rather than coarse stone or paper.
        float edge = min(min(UV.x,1.0-UV.x),min(UV.y,1.0-UV.y));
        float face = smoothstep(0.008,0.055,edge);
        ALBEDO = mix(ALBEDO,enamel_tone.rgb,enamel_balance*face);
        ROUGHNESS = mix(ROUGHNESS,0.29,enamel_balance*0.65);
    }
    float geometry_edge = smoothstep(0.035,0.22,length(dFdx(NORMAL))+length(dFdy(NORMAL)));
    if (use_normal_map && length(TANGENT)>0.1 && length(BINORMAL)>0.1) {
        vec3 sampled = texture(normal_map, UV).rgb * 2.0 - 1.0;
        sampled.xy *= normal_depth;
        sampled.z = sqrt(max(0.01, 1.0-dot(sampled.xy,sampled.xy)));
        NORMAL = normalize(normalize(TANGENT)*sampled.x + normalize(BINORMAL)*sampled.y + NORMAL*sampled.z);
    }
    // Baked self-occlusion belongs in ambient illumination, not in metal's albedo.
    float cavity = COLOR.r;
    if (!(cavity>=0.0 && cavity<=1.0)) { cavity=1.0; }

    if (patina > 0.0 || brushed > 0.0 || base_surface > 0.0) {
        // Object coordinates remain attached to each physical moving component.
        // The fixed pedestal is a lathed part: its grain follows the circumference.
        vec3 p = surface_position;
        float radius = length(p.xz);
        float angle = radius > 0.0001 ? atan(p.z,p.x) : 0.0;
        float patch = grain_noise(p*8.0);
        float detail = grain_noise(p*105.0);
        float cavity_oil = pow(1.0-cavity,1.5)*(0.55+0.45*patch);
        float rim_distance = min(min(abs(p.y-0.135),abs(p.y-0.485)),abs(p.y-0.567));
        float seam_oil = exp(-rim_distance*115.0)*base_surface*(0.30+0.70*patch);
        float oil = clamp((cavity_oil*.78 + seam_oil*0.10)*patina,0.0,0.35);
        float worn_edge = geometry_edge*smoothstep(0.32,0.75,detail)*patina;

        // Restrained oxidation in protected cavities; polished contact edges.
        ALBEDO *= mix(vec3(1.0),vec3(0.78,0.73,0.64),oil);
        ROUGHNESS += oil*0.10 + (patch-0.5)*0.04*patina;
        if (metalness > 0.5) {
            ALBEDO = mix(ALBEDO,ALBEDO*1.23,worn_edge*0.75);
            ROUGHNESS -= worn_edge*0.13;
            float axial_coordinate = mix(p.y + p.z*0.18,p.y,base_surface);
            float grain_frequency = 780.0;
            float grain_aa = 1.0-smoothstep(1.4,4.5,fwidth(axial_coordinate)*grain_frequency);
            float line = sin(axial_coordinate*grain_frequency+grain_noise(p*4.0)*2.3);
            ROUGHNESS += line*0.027*brushed*grain_aa;
            // Sparse, interrupted tool scuffs on the pedestal rings, not all-over dirt.
            float scuff_wave = abs(sin(p.y*295.0 + patch*0.22));
            float scuff_aa = max(fwidth(scuff_wave),0.015);
            float scuff = (1.0-smoothstep(0.04,0.04+scuff_aa,scuff_wave));
            scuff *= smoothstep(0.66,0.86,grain_noise(vec3(angle*18.0,p.y*35.0,radius*4.0)));
            scuff *= base_surface*patina;
            ALBEDO *= 1.0+scuff*0.12;
            ROUGHNESS += scuff*0.09;
        } else if (base_surface > 0.0 && coat > 0.1) {
            // The broad ivory panel stays clean. Chips are confined to its two edges.
            float paint_edge = min(abs(p.y-0.155),abs(p.y-0.46));
            float chip = (1.0-smoothstep(0.003,0.016,paint_edge))*smoothstep(0.48,0.80,detail);
            chip *= base_surface;
            ALBEDO = mix(ALBEDO,vec3(0.075,0.060,0.042),chip*0.86);
            METALLIC = mix(METALLIC,0.73,chip);
            ROUGHNESS += chip*0.16;
        }
        ROUGHNESS = clamp(ROUGHNESS,0.17,0.86);
    }
    AO = mix(1.0, cavity, 0.65);
    AO_LIGHT_AFFECT = 0.015;
    CLEARCOAT = coat;
    CLEARCOAT_ROUGHNESS = coat_roughness;
}
