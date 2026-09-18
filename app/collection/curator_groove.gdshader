shader_type spatial;
render_mode unshaded,cull_disabled,depth_draw_never;
uniform sampler2D traces:filter_linear_mipmap;
uniform vec3 color=vec3(1.,.58,.2);
uniform float gain=0.;
uniform float progress=0.;
uniform float rotation=0.;
void fragment(){
 vec2 p=UV-.5;
 float radius=length(p)*2.;float angle=atan(p.y,p.x)+rotation;
 float sector=pow(.5+.5*cos(angle-progress*18.),18.);
 float front=1.-smoothstep(.025,.15,abs(radius-mix(.82,.22,progress)));
 float art=texture(traces,UV).r;
 float strength=art*(front*.8+sector*.7)*gain;
 ALBEDO=color;EMISSION=color*strength*4.;ALPHA=clamp(strength,0.,.9);
}
