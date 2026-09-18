shader_type spatial;
render_mode unshaded,cull_disabled,depth_draw_never;
uniform sampler2D strands:filter_linear_mipmap,repeat_enable;
uniform float strength=0.;
uniform float clock=0.;
uniform vec3 color=vec3(1.,.57,.20);
uniform float length_fraction=1.;
void vertex(){
 float down=.5-VERTEX.y;
 float full_radius=mix(.036,.185,down);
 float clipped_radius=mix(.036,mix(.036,.185,length_fraction),down);
 VERTEX.xz*=clipped_radius/full_radius;
}
void fragment(){
 float art=texture(strands,vec2(UV.x,fract(UV.y*.8-clock*.08))).r;
 float edge=smoothstep(0.,.10,UV.y)*smoothstep(0.,.16,1.-UV.y);
 float facing=1.-pow(abs(dot(normalize(NORMAL),normalize(VIEW))),1.4);
 float intensity=(.045+art*.30)*(0.25+facing*.75)*strength*edge;
 ALBEDO=color;EMISSION=color*intensity*2.5;ALPHA=clamp(intensity,0.,.18);
}
