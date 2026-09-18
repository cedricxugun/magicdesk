shader_type spatial;
render_mode unshaded,cull_disabled,depth_draw_never;
uniform sampler2D pattern:filter_linear_mipmap,repeat_disable;
uniform vec2 mask_center=vec2(.5);
uniform float gain=0.;
uniform float pointer_angle=0.;
uniform float charge=0.;
void fragment(){
 vec2 p=UV-.5;float angle=atan(p.y,p.x);
 float distance=abs(atan(sin(angle-pointer_angle),cos(angle-pointer_angle)));
 float sector=1.-smoothstep(.08,.55,distance);
 vec2 sample_uv=UV+mask_center-.5;
 float art=texture(pattern,sample_uv).r;
 // Subpixel authored filaments need coverage at normal desktop size.
 // Dilate by less than one screen pixel, preserving the actual mask shape.
 vec2 footprint=fwidth(UV)*.70;
 art=max(art,texture(pattern,sample_uv+vec2(footprint.x,0.)).r);
 art=max(art,texture(pattern,sample_uv-vec2(footprint.x,0.)).r);
 art=max(art,texture(pattern,sample_uv+vec2(0.,footprint.y)).r);
 art=max(art,texture(pattern,sample_uv-vec2(0.,footprint.y)).r);
 float strength=art*gain*(.08*charge+sector)*3.0;
 ALBEDO=vec3(1.,.66,.26);EMISSION=vec3(1.,.66,.26)*strength*3.5;ALPHA=clamp(strength,0.,.90);
}
