shader_type spatial;
render_mode unshaded, cull_disabled, depth_draw_never, blend_mix;
uniform sampler2D page_0 : source_color, filter_linear_mipmap, repeat_disable;
uniform sampler2D page_1 : source_color, filter_linear_mipmap, repeat_disable;
uniform sampler2D page_2 : source_color, filter_linear_mipmap, repeat_disable;
uniform float offset_in_tile = 0.;
uniform float window_width = 550.;
uniform float tile_width = 512.;
uniform float opacity = .9;
uniform float playhead = .35;
uniform vec3 amber : source_color = vec3(.96,.59,.22);
void fragment(){
    float x=offset_in_tile+UV.x*window_width;
    float tile=floor(x/tile_width);
    vec2 uv=vec2(fract(x/tile_width),UV.y);
    vec4 ink=tile<1. ? texture(page_0,uv) : tile<2. ? texture(page_1,uv) : texture(page_2,uv);
    float border=smoothstep(0.,.025,UV.x)*smoothstep(0.,.025,1.-UV.x);
    float cursor=exp(-pow((UV.x-playhead)/.018,2.));
    vec3 color=mix(amber,vec3(1.,.92,.71),cursor*.65);
    ALBEDO=color;EMISSION=color*.7;
    ALPHA=ink.a*opacity*border;
}
