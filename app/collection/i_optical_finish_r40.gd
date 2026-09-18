extends RefCounted
static func apply(environment:Environment)->void:
    # Restrained optical spread around HDR emitters; no full-screen bloom floor.
    environment.glow_enabled=true
    environment.glow_intensity=.35
    environment.glow_strength=.80
    environment.glow_bloom=0.
    environment.glow_hdr_threshold=2.
    environment.glow_hdr_scale=1.
    environment.glow_blend_mode=Environment.GLOW_BLEND_MODE_ADDITIVE
    environment.glow_normalized=true
    for i in range(7):environment.set_glow_level(i,.65 if i==1 else .35 if i==2 else 0.)
