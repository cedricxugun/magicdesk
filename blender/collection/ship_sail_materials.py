"""Bake authored sail cloth and compass into portable PBR maps, not runtime placeholders."""
import bpy, hashlib, json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
ART=ROOT/'app/assets/collection/art/G_AI/ship'

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()

def finish_sails(cloths):
    for label,obj in cloths:
        decorated=label=='Main'
        key={'version':3,'crest':sha(ART/'sun_compass_mask.png'),'weave':sha(ART/'ivory_sail_weave.png'),
             'vertices':[[round(v.co.x,6),round(v.co.y,6),round(v.co.z,6)] for v in obj.data.vertices],
             'decorated':decorated}
        fingerprint=hashlib.sha256(json.dumps(key,sort_keys=True).encode()).hexdigest()
        manifest=ART/(label.lower()+'_bake.json')
        paths={k:ART/(label.lower()+'_'+k+'.png') for k in ['albedo','roughness','metallic','normal']}
        valid=manifest.exists() and all(p.exists() for p in paths.values())
        if valid:
            old=json.loads(manifest.read_text());valid=old['fingerprint']==fingerprint and all(sha(paths[k])==old['maps'][k] for k in paths)
        if not valid:
            mat=bpy.data.materials.new('Ship_'+label+'_BakeAuthoring');mat.use_nodes=True
            obj.data.materials.clear();obj.data.materials.append(mat)
            nodes=mat.node_tree.nodes;links=mat.node_tree.links
            principled=next(n for n in nodes if n.type=='BSDF_PRINCIPLED')
            output=next(n for n in nodes if n.type=='OUTPUT_MATERIAL')
            uv=nodes.new('ShaderNodeUVMap');uv.uv_map=obj.data.uv_layers[0].name
            weave=nodes.new('ShaderNodeTexImage');weave.image=bpy.data.images.load(str(ART/'ivory_sail_weave.png'),check_existing=True)
            links.new(uv.outputs['UV'],weave.inputs['Vector'])
            base=nodes.new('ShaderNodeMixRGB');base.blend_type='MULTIPLY';base.inputs[0].default_value=.14;base.inputs[1].default_value=(.78,.745,.67,1)
            links.new(weave.outputs['Color'],base.inputs[2]);links.new(base.outputs[0],principled.inputs['Base Color'])
            coordinates=nodes.new('ShaderNodeSeparateXYZ');links.new(uv.outputs['UV'],coordinates.inputs[0])
            lower=nodes.new('ShaderNodeMath');lower.operation='GREATER_THAN';lower.inputs[1].default_value=.085;links.new(coordinates.outputs['Y'],lower.inputs[0])
            upper=nodes.new('ShaderNodeMath');upper.operation='LESS_THAN';upper.inputs[1].default_value=.125;links.new(coordinates.outputs['Y'],upper.inputs[0])
            band=nodes.new('ShaderNodeMath');band.operation='MULTIPLY';links.new(lower.outputs[0],band.inputs[0]);links.new(upper.outputs[0],band.inputs[1])
            stripe=nodes.new('ShaderNodeMixRGB');stripe.inputs[2].default_value=(.16,.007,.012,1)
            links.new(band.outputs[0],stripe.inputs[0]);links.new(base.outputs[0],stripe.inputs[1]);links.new(stripe.outputs[0],principled.inputs['Base Color'])
            height=nodes.new('ShaderNodeRGBToBW');links.new(weave.outputs['Color'],height.inputs[0])
            bump=nodes.new('ShaderNodeBump');bump.inputs['Strength'].default_value=.22;bump.inputs['Distance'].default_value=.00010
            links.new(height.outputs[0],bump.inputs['Height']);links.new(bump.outputs['Normal'],principled.inputs['Normal'])
            principled.inputs['Roughness'].default_value=.61
            if decorated:
                heraldry=obj.data.uv_layers.new(name='Heraldry')
                for loop in obj.data.loops:
                    v=obj.data.vertices[loop.vertex_index].co
                    heraldry.data[loop.index].uv=((v.x-.10)/.14+.5,(v.z-.255)/.14+.5)
                crest_uv=nodes.new('ShaderNodeUVMap');crest_uv.uv_map='Heraldry'
                crest=nodes.new('ShaderNodeTexImage');crest.image=bpy.data.images.load(str(ART/'sun_compass_mask.png'),check_existing=True);crest.image.colorspace_settings.name='Non-Color';crest.extension='CLIP'
                links.new(crest_uv.outputs[0],crest.inputs['Vector'])
                mask=nodes.new('ShaderNodeValToRGB');mask.color_ramp.elements[0].position=.09;mask.color_ramp.elements[1].position=.8
                links.new(crest.outputs['Color'],mask.inputs[0])
                color=nodes.new('ShaderNodeMixRGB');color.inputs[2].default_value=(.42,.245,.072,1)
                links.new(mask.outputs[0],color.inputs[0]);links.new(stripe.outputs[0],color.inputs[1]);links.new(color.outputs[0],principled.inputs['Base Color'])
                metal=nodes.new('ShaderNodeMath');metal.operation='MULTIPLY';metal.inputs[1].default_value=.74
                links.new(mask.outputs[0],metal.inputs[0]);links.new(metal.outputs[0],principled.inputs['Metallic'])
                rough=nodes.new('ShaderNodeMapRange');rough.inputs['To Min'].default_value=.61;rough.inputs['To Max'].default_value=.35
                links.new(mask.outputs[0],rough.inputs[0]);links.new(rough.outputs[0],principled.inputs['Roughness'])
                thread=nodes.new('ShaderNodeBump');thread.inputs['Strength'].default_value=.35;thread.inputs['Distance'].default_value=.00012
                links.new(mask.outputs[0],thread.inputs['Height']);links.new(bump.outputs['Normal'],thread.inputs['Normal']);links.new(thread.outputs['Normal'],principled.inputs['Normal'])
            scene=bpy.context.scene;scene.render.engine='CYCLES';scene.cycles.samples=8
            bpy.ops.object.select_all(action='DESELECT');obj.select_set(True);bpy.context.view_layer.objects.active=obj
            obj.data.uv_layers.active_index=0
            for layer in obj.data.uv_layers:layer.active_render=layer==obj.data.uv_layers[0]
            disabled=[]
            for modifier in obj.modifiers:
                if modifier.show_render:disabled.append(modifier);modifier.show_render=False;modifier.show_viewport=False
            target=nodes.new('ShaderNodeTexImage');nodes.active=target
            emission=nodes.new('ShaderNodeEmission')
            scene.render.bake.margin=16;scene.render.bake.use_selected_to_active=False
            for channel in paths:
                image=bpy.data.images.new('Ship_'+label+'_'+channel,1024,1024,alpha=False)
                image.colorspace_settings.name='sRGB' if channel=='albedo' else 'Non-Color'
                target.image=image;nodes.active=target
                for link in list(output.inputs['Surface'].links):links.remove(link)
                if channel=='normal':
                    links.new(principled.outputs['BSDF'],output.inputs['Surface']);bpy.ops.object.bake(type='NORMAL')
                else:
                    socket=principled.inputs[{'albedo':'Base Color','roughness':'Roughness','metallic':'Metallic'}[channel]]
                    for link in list(emission.inputs['Color'].links):links.remove(link)
                    if socket.is_linked:links.new(socket.links[0].from_socket,emission.inputs['Color'])
                    else:
                        v=socket.default_value;emission.inputs['Color'].default_value=tuple(v) if channel=='albedo' else (v,v,v,1)
                    links.new(emission.outputs[0],output.inputs['Surface']);bpy.ops.object.bake(type='EMIT')
                image.filepath_raw=str(paths[channel]);image.file_format='PNG';image.save()
            for modifier in disabled:modifier.show_render=True;modifier.show_viewport=True
            manifest.write_text(json.dumps({'fingerprint':fingerprint,'maps':{k:sha(p) for k,p in paths.items()},
                'source_art':{k:sha(ART/k) for k in ['sun_compass_mask.png','ivory_sail_weave.png']},
                'scope':'Cycles source PBR bake from authored raster assets, not physically measured cloth data'},indent=2)+'\n')
        # Portable glTF-compatible material used by source renders and exported geometry.
        mat=bpy.data.materials.new('Collection_Ship'+label+'Sail');mat.use_nodes=True
        p=next(n for n in mat.node_tree.nodes if n.type=='BSDF_PRINCIPLED');links=mat.node_tree.links
        for channel,path in paths.items():
            tex=mat.node_tree.nodes.new('ShaderNodeTexImage');tex.image=bpy.data.images.load(str(path),check_existing=True)
            tex.image.colorspace_settings.name='sRGB' if channel=='albedo' else 'Non-Color'
            if channel=='normal':
                normal=mat.node_tree.nodes.new('ShaderNodeNormalMap');normal.inputs['Strength'].default_value=1
                links.new(tex.outputs['Color'],normal.inputs['Color']);links.new(normal.outputs['Normal'],p.inputs['Normal'])
            else:links.new(tex.outputs['Color'],p.inputs[{'albedo':'Base Color','roughness':'Roughness','metallic':'Metallic'}[channel]])
        obj.data.materials.clear();obj.data.materials.append(mat)
