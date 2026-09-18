shader_type spatial;
render_mode unshaded,cull_disabled,depth_draw_never;
uniform sampler2D pattern:filter_linear_mipmap,repeat_enable;
uniform vec3 color=vec3(1.,.55,.18);
uniform float gain=0.;
uniform float time=0.;
uniform bool instanced=false;
uniform bool print_wire=false;
uniform float progress=0.;
uniform float reveal=1.;
uniform float height=1.;
uniform vec3 origin=vec3(0.);
uniform vec3 up=vec3(0.,1.,0.);
uniform float row=.5;
uniform float path_start=0.;
uniform float path_span=1.;
varying vec3 world;
varying vec4 custom;
varying float along;
void vertex(){world=(MODEL_MATRIX*vec4(VERTEX,1.)).xyz;custom=INSTANCE_CUSTOM;along=VERTEX.y+.5;}
void fragment(){
 float coordinate=print_wire?UV.y:path_start+along*path_span;
 float light=texture(pattern,vec2(.50+(UV.x-.5)*.015,fract(coordinate*.75-time*.17))).r;
 float strength=gain*(.55+light*.45)*(instanced?custom.r:1.);
 if(print_wire){
  float level=dot(world-origin,up)/height;
  strength*=smoothstep(progress-.005,progress+.025,level)*(1.-smoothstep(reveal-.015,reveal+.02,level));
 }
 ALBEDO=color;EMISSION=color*strength*4.;ALPHA=clamp(strength,0.,.96);
}
