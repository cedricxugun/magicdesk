"""Author source shader formation matching runtime G0/legacy and G1 fields."""
import bpy,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
def prepare(roots,print_root,take,skip_indices=()):
    seal=json.loads((ROOT/'app/assets/collection/butterfly_seal.json').read_text())
    data=json.loads((ROOT/'app/assets/collection/models/G_optical_curator_butterfly_candidate.json').read_text())
    spec=data['g_archive']['contents'][1]['butterfly'];progress_values=[];gain_values=[]
    for index,root in enumerate(roots):
        if index in skip_indices:
            progress_values.append([]);gain_values.append([]);continue
        materials={};progress=[];gains=[]
        for obj in [root]+list(root.children_recursive):
            obj.hide_set(False)
            if obj.type not in ['MESH','CURVE','FONT']:continue
            wing=obj
            while wing!=root and wing.name not in spec['wing_spans']:wing=wing.parent
            if wing==root:wing=None
            for slot in obj.material_slots:
                source=slot.material
                if not source or not source.use_nodes:continue
                key=(source.name,wing.name if index==1 and wing else '')
                if key in materials:slot.link='OBJECT';slot.material=materials[key];continue
                mat=source.copy();mat.name='CandidateFormation_'+str(index)+'_'+source.name;materials[key]=mat;slot.link='OBJECT';slot.material=mat
                nt=mat.node_tree;nt.animation_data_clear();nodes=nt.nodes;links=nt.links
                p=next(n for n in nodes if n.type=='BSDF_PRINCIPLED')
                # Disconnect legacy formation gates, retaining finish textures,
                # coat, roughness mapping and normal channels.
                for socket in ['Alpha','Emission Strength','Emission Color']:
                    for link in list(p.inputs[socket].links):links.remove(link)
                p.inputs['Alpha'].default_value=1.;p.inputs['Emission Strength'].default_value=0.
                output=next(n for n in nodes if n.type=='OUTPUT_MATERIAL')
                for link in list(output.inputs['Surface'].links):links.remove(link)
                def calc(op,*args):
                    n=nodes.new('ShaderNodeMath');n.operation=op
                    for i,a in enumerate(args):
                        if isinstance(a,(int,float)):n.inputs[i].default_value=a
                        else:links.new(a,n.inputs[i])
                    return n.outputs[0]
                def smooth(value,a,b,low=0.,high=1.):
                    n=nodes.new('ShaderNodeMapRange');n.interpolation_type='SMOOTHSTEP';n.clamp=True
                    links.new(value,n.inputs[0]);n.inputs[1].default_value=a;n.inputs[2].default_value=b;n.inputs[3].default_value=low;n.inputs[4].default_value=high
                    return n.outputs[0]
                value=nodes.new('ShaderNodeValue');value.name='RecordedFormation';progress.append(value.outputs[0]);raw=value.outputs[0]
                gain=nodes.new('ShaderNodeValue');gain.name='RecordedFormationGain';gains.append(gain.outputs[0])
                coords=nodes.new('ShaderNodeTexCoord');coords.object=wing if index==1 and wing else print_root
                sep=nodes.new('ShaderNodeSeparateXYZ');links.new(coords.outputs['Object'],sep.inputs[0]);level=calc('DIVIDE',sep.outputs['Z'],take['heights'][index])
                metallic=p.inputs['Metallic'].default_value;front=calc('ADD',raw,.035 if metallic>.8 else 0.);gate=calc('GREATER_THAN',raw,.0001);edge_width=.018;edge_gain=6.
                if index==1:
                    p.inputs['Emission Color'].default_value=(1.,.33,.025,1.);edge_gain=1.8
                    if wing:
                        kind='upper' if 'Upper' in wing.name else 'lower';cfg=seal['wings'][kind];side=-1 if wing.name.endswith('-1') else 1
                        x=calc('MULTIPLY',sep.outputs['X'],side)
                        level=calc('DIVIDE',calc('MAXIMUM',0.,x),spec['wing_spans'][wing.name]);front=calc('ADD',smooth(raw,*cfg['metal_phase']),.025 if metallic>.8 else 0.)
                        material_key=source.get('butterfly_material_key','')
                        if material_key in ['Porcelain','Red']:
                            bounds=cfg['bounds'];uv=nodes.new('ShaderNodeCombineXYZ')
                            links.new(calc('DIVIDE',calc('SUBTRACT',x,bounds[0]),bounds[2]),uv.inputs['X'])
                            links.new(calc('DIVIDE',calc('SUBTRACT',sep.outputs['Z'],bounds[1]),bounds[3]),uv.inputs['Y'])
                            texture=nodes.new('ShaderNodeTexImage');texture.image=bpy.data.images.load(str(ROOT/'app'/cfg['texture'].removeprefix('res://')),check_existing=True);texture.image.colorspace_settings.name='Non-Color';texture.extension='EXTEND';links.new(uv.outputs[0],texture.inputs['Vector'])
                            channels=nodes.new('ShaderNodeSeparateColor');links.new(texture.outputs['Color'],channels.inputs[0]);level=channels.outputs['Red']
                            phase=cfg['red_phase'] if material_key=='Red' else cfg['seal_phase'];front=smooth(raw,*phase);gate=calc('GREATER_THAN',raw,phase[0]);edge_gain=.85
                    else:front=smooth(raw,.03,.44)
                    distance=calc('ABSOLUTE',calc('SUBTRACT',level,front))
                else:
                    p.inputs['Emission Color'].default_value=(1.,.69,.33,1.)
                    distance=calc('ABSOLUTE',calc('SUBTRACT',sep.outputs['Z'],calc('MULTIPLY',raw,take['heights'][index])))
                visible=calc('MULTIPLY',gate,calc('LESS_THAN',level,calc('ADD',front,.000001)))
                transparent=nodes.new('ShaderNodeBsdfTransparent');mix=nodes.new('ShaderNodeMixShader');links.new(visible,mix.inputs[0]);links.new(transparent.outputs[0],mix.inputs[1]);links.new(p.outputs['BSDF'],mix.inputs[2]);links.new(mix.outputs[0],output.inputs['Surface'])
                edge=smooth(distance,0.,edge_width,1.,0.)
                links.new(calc('MULTIPLY',calc('MULTIPLY',edge,edge_gain),gain.outputs[0]),p.inputs['Emission Strength'])
        progress_values.append(progress);gain_values.append(gains)
    return progress_values,gain_values
