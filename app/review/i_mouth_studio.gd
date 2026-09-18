extends RefCounted
## Local inspection studio. Does not change the shared main App lighting profile.
static func apply(viewport:Viewport,environment:Environment,lights:Array)->Dictionary:
    # TAA settles a static shot but smears the current field-driven foil motion.
    # HIGH spatial filtering was measured with the actual mouth on this Mac.
    viewport.use_taa=false
    viewport.msaa_3d=Viewport.MSAA_4X
    viewport.scaling_3d_scale=1.
    RenderingServer.positional_soft_shadow_filter_set_quality(RenderingServer.SHADOW_QUALITY_SOFT_HIGH)
    environment.ambient_light_energy=.40
    var energies:=[8.,4.,5.]
    var colors:=[Color(1.,.95,.86),Color(.85,.92,1.),Color(1.,.98,.93)]
    assert(lights.size()==energies.size())
    for index in range(lights.size()):
        var light:AreaLight3D=lights[index]
        light.light_energy=energies[index]
        light.light_color=colors[index]
        light.shadow_enabled=true
        light.light_size=.25
        light.shadow_normal_bias=.012
    return {"profile":"mouth_studio_r1","shadow_filter":"high","msaa":4,"taa":false,"render_scale":1.,"ambient_energy":.40,"light_energies":energies,"scope":"Independent mouth viewer only; main collection lighting unchanged. Bounded local frame cadence is not whole App performance acceptance."}
