shader_type spatial;
render_mode unshaded, cull_disabled, depth_draw_never, blend_add;
uniform sampler2D filament : filter_linear_mipmap_anisotropic, repeat_disable;
uniform float strength=0.;
uniform vec3 tip_delta=vec3(0.);
uniform bool follows_tip=false;
uniform float filament_u_span=1.;
uniform float minimum_pixel_width=0.;
uniform float mask_power=1.;
void vertex(){
    // glTF flips source Blender V: imported UV.y=1 is the measured tip.
    if(follows_tip) VERTEX+=tip_delta*UV.y;
}
void fragment(){
    float span=filament_u_span;
    if(minimum_pixel_width>0.){
        float pixel_uv=length(vec2(dFdx(UV.x),dFdy(UV.x)));
        span=min(span,.006/max(pixel_uv*minimum_pixel_width,.000001));
    }
    vec2 filament_uv=vec2(.5+(UV.x-.5)*span,UV.y);
    float mask=pow(texture(filament,filament_uv).r,mask_power);
    ALBEDO=vec3(1.,.53,.12);
    EMISSION=vec3(1.,.48,.08)*strength;
    ALPHA=mask*clamp(strength,0.,1.);
}
