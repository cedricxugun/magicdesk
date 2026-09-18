shader_type spatial;
render_mode unshaded, cull_disabled, depth_draw_never, blend_mix;
uniform sampler2D page_0 : source_color, filter_linear_mipmap_anisotropic, repeat_disable;
uniform sampler2D page_1 : source_color, filter_linear_mipmap_anisotropic, repeat_disable;
uniform sampler2D page_2 : source_color, filter_linear_mipmap_anisotropic, repeat_disable;
uniform float offset_in_tile=0.;
uniform float window_width=600.;
uniform float tile_width=512.;
uniform float reveal=0.;
uniform float playhead=.5;
uniform float center_z=-.30;
uniform vec3 valid_tiles=vec3(1.);
uniform float score_offset=0.;
uniform float score_length=100000.;
uniform float music_level=0.;
uniform float playing=0.;
uniform float reading_started=0.;
uniform float score_gain=1.;
uniform float optical_backing=0.;
uniform bool correct_alpha=true;
uniform float cursor_width=.010;
uniform float edge_fade=.025;
uniform bool tile_gradients=true;
uniform float ink_coverage_gain=1.;
void vertex(){
    float spread=smoothstep(.05,.72,reveal);
    VERTEX.z=center_z+(VERTEX.z-center_z)*max(.005,spread);
}
void fragment(){
    float x=offset_in_tile+UV.x*window_width;
    float tile=floor(x/tile_width);
    vec2 continuous_uv=vec2(x/tile_width,1.-UV.y);
    vec2 dx=dFdx(continuous_uv),dy=dFdy(continuous_uv);
    vec2 uv=vec2(fract(continuous_uv.x),continuous_uv.y);
    // Derivatives of fract() jump at tile seams and select an overly blurry mip.
    vec4 ink=tile_gradients ? (tile<1.?textureGrad(page_0,uv,dx,dy):tile<2.?textureGrad(page_1,uv,dx,dy):textureGrad(page_2,uv,dx,dy)) : (tile<1.?texture(page_0,uv):tile<2.?texture(page_1,uv):texture(page_2,uv));
    ink.a=1.-pow(1.-ink.a,ink_coverage_gain);
    float valid=tile<1.?valid_tiles.x:tile<2.?valid_tiles.y:valid_tiles.z;
    float score_x=score_offset+UV.x*window_width;
    ink.a*=valid*step(0.,score_x)*step(score_x,score_length);
    float edges=smoothstep(0.,edge_fade,UV.x)*smoothstep(0.,edge_fade,1.-UV.x);
    float glyph=ink.a*smoothstep(.68,1.,reveal);
    float cursor=exp(-pow((UV.x-playhead)/cursor_width,2.))*reading_started;
    float passed=(1.-smoothstep(playhead-.003,playhead+.003,UV.x))*reading_started;
    vec3 paper_light=mix(vec3(.94,.96,1.),vec3(.70,.40,.11),passed);
    paper_light=mix(paper_light,vec3(1.,.71,.26),cursor);
    float backing=optical_backing*smoothstep(.1,.8,reveal);
    ALBEDO=mix(vec3(.013,.019,.021),paper_light,glyph);
    EMISSION=paper_light*glyph*(.26+cursor*(.20+playing*(.45+music_level*.75)))*score_gain;
    ALPHA=edges*max(backing,glyph*.95)*smoothstep(0.,.15,reveal);
    if(correct_alpha){
        float opacity=glyph+backing*(1.-glyph);
        // Straight-alpha output: avoid attenuating antialiased ink twice.
        ALBEDO=(paper_light*glyph+vec3(.009,.014,.017)*backing*(1.-glyph))/max(opacity,.0001);
        EMISSION=paper_light*glyph*(.40+cursor*(.20+playing*(.45+music_level*.75)))*score_gain/max(opacity,.0001);
        float vertical=smoothstep(0.,.035,UV.y)*smoothstep(0.,.035,1.-UV.y);
        ALPHA=edges*vertical*opacity*smoothstep(0.,.15,reveal);
    }
}
