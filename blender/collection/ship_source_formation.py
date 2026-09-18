"""Editable G2 hull/cloth materialization fields; preserves authored PBR maps."""
import bpy,json
from pathlib import Path
from mathutils import Vector
ROOT=Path(__file__).resolve().parents[2]

def prepare(root,spec):
    profile=json.loads((ROOT/'app/assets/collection/ship_fabrication.json').read_text())
    objects=[o for o in root.children_recursive if o.type in ['MESH','CURVE','FONT']]
    for obj in objects:obj.hide_set(False);obj.hide_render=False;obj.hide_viewport=False
    bpy.context.view_layer.update();deps=bpy.context.evaluated_depsgraph_get();bounds={}
    for obj in objects:
        key=obj.name if 'WorkingSheet' in obj.name else obj.parent.name
        ev=obj.evaluated_get(deps);mesh=ev.to_mesh();matrix=obj.parent.matrix_world.inverted()@obj.matrix_world
        points=[matrix@v.co for v in mesh.vertices];ev.to_mesh_clear()
        if key not in bounds:bounds[key]=points
        else:bounds[key].extend(points)
    limits={k:([min(p[i] for p in points) for i in range(3)],[max(p[i] for p in points) for i in range(3)]) for k,points in bounds.items()}
    progress=[];gains=[];cache={}
    for obj in objects:
        branch=obj.parent;name=branch.name;key_name=obj.name if 'WorkingSheet' in obj.name else name
        low,high=limits[key_name];wave=name in spec['rig']['waves'];hull=name==spec['rig']['roll']
        mast=name in spec['rig']['sails'] or name=='GS2_Mast';fittings=name==spec['fittings_node']
        phase=(.10,.32) if wave else (.32,.52) if mast else (.52,.68) if fittings else (.22,.48) if hull or name=='GS2_Deck' else (.02,.28)
        for slot in obj.material_slots:
            source=slot.material
            if not source or not source.use_nodes:continue
            key=(source.name,key_name)
            if key in cache:slot.link='OBJECT';slot.material=cache[key];continue
            mat=source.copy();mat.name='ShipFormation_'+source.name;slot.link='OBJECT';slot.material=mat;cache[key]=mat
            nodes=mat.node_tree.nodes;links=mat.node_tree.links;mat.node_tree.animation_data_clear()
            p=next(n for n in nodes if n.type=='BSDF_PRINCIPLED');output=next(n for n in nodes if n.type=='OUTPUT_MATERIAL')
            for link in list(output.inputs['Surface'].links):links.remove(link)
            for socket in ['Alpha','Emission Color','Emission Strength']:
                for link in list(p.inputs[socket].links):links.remove(link)
            p.inputs['Alpha'].default_value=1.;p.inputs['Emission Color'].default_value=(1.,.55,.20,1.)
            def calc(op,*args):
                n=nodes.new('ShaderNodeMath');n.operation=op
                for i,value in enumerate(args):
                    if isinstance(value,(float,int)):n.inputs[i].default_value=value
                    else:links.new(value,n.inputs[i])
                return n.outputs[0]
            def smooth(value,a,b,low=0.,high=1.):
                n=nodes.new('ShaderNodeMapRange');n.interpolation_type='SMOOTHSTEP';n.clamp=True;links.new(value,n.inputs[0])
                for i,v in enumerate([a,b,low,high],1):n.inputs[i].default_value=v
                return n.outputs[0]
            def texture(path):
                n=nodes.new('ShaderNodeTexImage');n.image=bpy.data.images.load(str(ROOT/'app'/path.removeprefix('res://')),check_existing=True);n.extension='EXTEND';return n
            raw_node=nodes.new('ShaderNodeValue');raw_node.name='RecordedFormation';raw=raw_node.outputs[0];progress.append(raw)
            gain_node=nodes.new('ShaderNodeValue');gain_node.name='RecordedFormationGain';gain=gain_node.outputs[0];gains.append(gain)
            coords=nodes.new('ShaderNodeTexCoord');coords.object=branch;sep=nodes.new('ShaderNodeSeparateXYZ');links.new(coords.outputs['Object'],sep.inputs[0])
            level=calc('DIVIDE',calc('ABSOLUTE',sep.outputs['X']),max(abs(low[0]),abs(high[0]),.001)) if wave else calc('DIVIDE',calc('SUBTRACT',sep.outputs['Z'],low[2]),max(.001,high[2]-low[2]))
            level=calc('MINIMUM',1.,calc('MAXIMUM',0.,level));front=smooth(raw,*phase);gate=calc('GREATER_THAN',raw,phase[0]);warp=None
            cloth='ShipMainSail' in source.name or 'ShipJibSail' in source.name
            porcelain=hull and 'Porcelain' in source.name
            if porcelain:
                cfg=profile['hull'];image=texture(cfg['texture']);image.image.colorspace_settings.name='Non-Color';links.new(coords.outputs['UV'],image.inputs['Vector'])
                rgb=nodes.new('ShaderNodeSeparateColor');links.new(image.outputs['Color'],rgb.inputs[0]);level=rgb.outputs['Red'];front=smooth(raw,*cfg['phase']);gate=calc('GREATER_THAN',raw,cfg['phase'][0]);mat['ship_material_kind']='hull'
            elif cloth:
                cfg=profile['sails']['main' if 'Main' in source.name else 'jib'];image=texture(cfg['texture']);image.image.colorspace_settings.name='Non-Color';links.new(coords.outputs['UV'],image.inputs['Vector'])
                rgb=nodes.new('ShaderNodeSeparateColor');links.new(image.outputs['Color'],rgb.inputs[0]);level=rgb.outputs['Green']
                front=smooth(raw,*cfg['cloth_phase']);warp_front=smooth(raw,*cfg['warp_phase']);gate=calc('GREATER_THAN',raw,cfg['warp_phase'][0])
                warp=calc('MULTIPLY',calc('MULTIPLY',calc('GREATER_THAN',level,front),calc('LESS_THAN',level,calc('ADD',warp_front,.000001))),calc('GREATER_THAN',rgb.outputs['Red'],.35))
                old_color=p.inputs['Base Color'].links[0].from_socket;old_metal=p.inputs['Metallic'].links[0].from_socket
                plain=texture('res://assets/collection/art/G_AI/ship/jib_albedo.png');links.new(coords.outputs['UV'],plain.inputs['Vector'])
                embroidery=smooth(raw,*cfg['crest_phase']);blend=nodes.new('ShaderNodeMixRGB')
                links.new(calc('MULTIPLY',calc('GREATER_THAN',old_metal,.15),calc('SUBTRACT',1.,embroidery)),blend.inputs[0]);links.new(old_color,blend.inputs[1]);links.new(plain.outputs['Color'],blend.inputs[2]);links.new(blend.outputs[0],p.inputs['Base Color'])
                links.new(calc('MULTIPLY',old_metal,embroidery),p.inputs['Metallic']);mat['ship_material_kind']='sail'
            else:mat['ship_material_kind']='metal'
            visible=calc('LESS_THAN',level,calc('ADD',front,.000001))
            if warp is not None:visible=calc('MAXIMUM',visible,warp)
            visible=calc('MULTIPLY',visible,gate)
            distance=calc('ABSOLUTE',calc('SUBTRACT',level,front));edge=smooth(distance,0.,.035,1.,0.)
            climax=calc('EXPONENT',calc('MULTIPLY',-1.,calc('POWER',calc('DIVIDE',calc('SUBTRACT',raw,.77),.16),2.)))
            links.new(calc('MULTIPLY',calc('MULTIPLY',edge,calc('ADD',1.32,calc('MULTIPLY',.48,climax))),gain),p.inputs['Emission Strength'])
            surface=p.outputs['BSDF']
            if warp is not None:
                thread=nodes.new('ShaderNodeEmission');thread.inputs['Color'].default_value=(1.,.52,.14,1.);links.new(calc('MULTIPLY',gain,.8),thread.inputs['Strength'])
                switch=nodes.new('ShaderNodeMixShader');links.new(warp,switch.inputs[0]);links.new(surface,switch.inputs[1]);links.new(thread.outputs[0],switch.inputs[2]);surface=switch.outputs[0]
            transparent=nodes.new('ShaderNodeBsdfTransparent');mix=nodes.new('ShaderNodeMixShader');links.new(visible,mix.inputs[0]);links.new(transparent.outputs[0],mix.inputs[1]);links.new(surface,mix.inputs[2]);links.new(mix.outputs[0],output.inputs['Surface'])
    return progress,gains
