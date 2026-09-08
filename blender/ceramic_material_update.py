"""Apply new ceramic maps to loaded Blender data. NO saving or exporting side effects.

Caller controls persistence. Only Ivory_Enamel is modified.
"""
import bpy,pathlib
ROOT=pathlib.Path(__file__).resolve().parents[1];ASSET=ROOT/'app'/'assets'

def apply_ceramic_material():
    m=bpy.data.materials.get('Ivory_Enamel')
    if not m:raise RuntimeError('Ivory_Enamel not found')
    m.use_nodes=True;nt=m.node_tree;nt.nodes.clear()
    out=nt.nodes.new('ShaderNodeOutputMaterial');out.location=(610,40)
    p=nt.nodes.new('ShaderNodeBsdfPrincipled');p.name='Ceramic_Glaze_Principled';p.location=(220,40)
    p.inputs['Metallic'].default_value=0.;p.inputs['IOR'].default_value=1.46
    p.inputs['Roughness'].default_value=.215;p.inputs['Specular IOR Level'].default_value=.5
    p.inputs['Coat Weight'].default_value=.42;p.inputs['Coat Roughness'].default_value=.105;p.inputs['Coat IOR'].default_value=1.46
    p.inputs['Anisotropic'].default_value=0.;p.inputs['Subsurface Weight'].default_value=0.
    nt.links.new(p.outputs['BSDF'],out.inputs['Surface'])
    def tex(name,file,space,loc):
        t=nt.nodes.new('ShaderNodeTexImage');t.name=name;t.label=name;t.location=loc;t.image=bpy.data.images.load(str(ASSET/file),check_existing=True);t.image.colorspace_settings.name=space;t.interpolation='Linear';t.extension='EXTEND';return t
    albedo=tex('Ceramic Ivory / clean pigment','ceramic_ivory_albedo.png','sRGB',(-620,400));nt.links.new(albedo.outputs['Color'],p.inputs['Base Color'])
    rough=tex('Ceramic Glaze / perceptual roughness','ceramic_glaze_roughness.png','Non-Color',(-620,90));nt.links.new(rough.outputs['Color'],p.inputs['Roughness'])
    normal=tex('Ceramic Glaze / isotropic micro-normal','ceramic_glaze_normal.png','Non-Color',(-620,-220))
    n=nt.nodes.new('ShaderNodeNormalMap');n.name='Ceramic Micro-Normal (subvisible)';n.inputs['Strength'].default_value=.20;n.location=(-170,-180);nt.links.new(normal.outputs['Color'],n.inputs['Color']);nt.links.new(n.outputs['Normal'],p.inputs['Normal'])
    # Clearcoat uses the smooth geometric normal, so its narrow highlight stays continuous.
    m.diffuse_color=(.7605,.7157,.6308,1);m['ceramic_revision']='clean-glaze-v1';m['ceramic_metallic']=0.;m['ceramic_roughness_mean']=.215
    return m

if __name__=='__main__':
    apply_ceramic_material();print('CERAMIC_MATERIAL_APPLIED_IN_MEMORY_NO_SAVE',flush=True)
