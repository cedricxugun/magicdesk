shader_type spatial;
render_mode unshaded, cull_disabled, depth_draw_never, shadows_disabled;
uniform sampler2D crest : source_color, filter_linear_mipmap, repeat_disable;
uniform vec3 tint : source_color = vec3(1.0,.79,.51);
uniform float gain = 0.0;
void fragment() {
    // Mirrored sampling closes the authored strip around the circumference;
    // the waveform itself is the generated image, not a procedural sine ring.
    vec2 uv=vec2(abs(UV.x*2.0-1.0),UV.y);
    vec4 texel=texture(crest,uv);
    float mask=dot(texel.rgb,vec3(.2126,.7152,.0722))*texel.a;
    ALBEDO=tint;
    EMISSION=tint*.7;
    ALPHA=clamp(mask*gain,0.0,.85);
}
