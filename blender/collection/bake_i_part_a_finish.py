"""Derive physical roughness/normal maps from the authored brushing, using Blender baking."""
import bpy,json,hashlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'production/I_refinement/part_a_mouth/material_r2'
bpy.ops.wm.read_factory_settings(use_empty=True)
scene=bpy.context.scene;scene.render.engine='CYCLES';scene.cycles.samples=1;scene.render.bake.margin=0
bpy.ops.mesh.primitive_plane_add(size=1)
o=bpy.context.object
mat=bpy.data.materials.new('Nickel microfinish bake');mat.use_nodes=True;o.data.materials.append(mat)
n=mat.node_tree.nodes;links=mat.node_tree.links;n.clear()
out=n.new('ShaderNodeOutputMaterial');source=n.new('ShaderNodeTexImage');source.image=bpy.data.images.load(str(OUT/'nickel_brushing.png'));source.image.colorspace_settings.name='Non-Color'
target=n.new('ShaderNodeTexImage')
value=n.new('ShaderNodeMapRange');value.inputs['From Min'].default_value=.2;value.inputs['From Max'].default_value=.8;value.inputs['To Min'].default_value=.24;value.inputs['To Max'].default_value=.33
links.new(source.outputs['Color'],value.inputs['Value'])
em=n.new('ShaderNodeEmission');links.new(value.outputs['Result'],em.inputs['Color']);links.new(em.outputs[0],out.inputs['Surface'])
im=bpy.data.images.new('A nickel roughness',1024,1024);im.colorspace_settings.name='Non-Color';target.image=im;n.active=target
bpy.ops.object.bake(type='EMIT');im.filepath_raw=str(OUT/'nickel_roughness.png');im.file_format='PNG';im.save()
bsdf=n.new('ShaderNodeBsdfPrincipled');links.new(bsdf.outputs[0],out.inputs['Surface'])
bump=n.new('ShaderNodeBump');bump.inputs['Strength'].default_value=.12;bump.inputs['Distance'].default_value=.00035;links.new(source.outputs['Color'],bump.inputs['Height']);links.new(bump.outputs['Normal'],bsdf.inputs['Normal'])
im=bpy.data.images.new('A nickel normal',1024,1024);im.colorspace_settings.name='Non-Color';target.image=im;n.active=target
bpy.ops.object.bake(type='NORMAL',normal_space='TANGENT');im.filepath_raw=str(OUT/'nickel_normal.png');im.file_format='PNG';im.save()
(OUT/'bake.json').write_text(json.dumps({'source_sha256':hashlib.sha256((OUT/'nickel_brushing.png').read_bytes()).hexdigest(),'maps':['nickel_roughness.png','nickel_normal.png'],'pipeline':'Blender Cycles tangent normal and emission roughness baking from authored input; base color remains measured material choice, not the scan color.','samples':1,'resolution':1024},indent=2)+'\n')
print('I_PART_A_FINISH_BAKED')
