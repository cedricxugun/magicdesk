shader_type spatial;
render_mode unshaded, cull_disabled, depth_draw_never, shadows_disabled;
uniform sampler2D atlas : source_color, filter_linear, repeat_disable;
uniform vec2 tile = vec2(0.0);
uniform vec3 tint : source_color = vec3(1.0, 0.38, 0.065);
uniform float gain = 0.0;
uniform bool flow = false;
uniform float head = 1.0;
void fragment() {
    vec2 uv = UV;
    float window = 1.0;
    if (flow) {
        float distance = uv.x - head;
        uv.x = distance * 4.0 + 0.5;
        window = 1.0 - smoothstep(0.115, 0.125, abs(distance));
    }
    // Clamp inside this authored tile; no sampling adjacent atlas artwork.
    vec2 sample_uv = (clamp(uv, vec2(0.0016), vec2(0.9984)) + tile) * 0.5;
    vec4 texel = texture(atlas, sample_uv);
    float mask = dot(texel.rgb, vec3(0.2126, 0.7152, 0.0722)) * texel.a;
    ALBEDO = tint * 1.5;
    ALPHA = clamp(mask * gain * window, 0.0, 1.0);
}
