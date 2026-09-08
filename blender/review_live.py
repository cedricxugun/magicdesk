import bpy, pathlib,json,time
ROOT=pathlib.Path(__file__).resolve().parents[1];REVIEW=ROOT/'review'
bpy.context.preferences.view.show_splash=False
class HELIOS_OT_review_pose(bpy.types.Operator):
    bl_idname='helios.review_pose';bl_label='Review pose'
    state:bpy.props.StringProperty(default='closed')
    def execute(self,ctx):
        if ctx.screen.is_animation_playing:bpy.ops.screen.animation_cancel(restore_frame=False)
        frame,scale={'closed':(1,4.55),'open':(180,7.25),'exploded':(340,8.5)}[self.state]
        ctx.scene.frame_set(frame)
        return {'FINISHED'}
class HELIOS_OT_review_render(bpy.types.Operator):
    bl_idname='helios.review_render';bl_label='Render current pose'
    def execute(self,ctx):
        ctx.scene.render.filepath=str(REVIEW/'current_view.png');bpy.ops.render.render('INVOKE_DEFAULT',write_still=True)
        return {'FINISHED'}
class HELIOS_PT_review(bpy.types.Panel):
    bl_label='HELIOS / B - Reference refinement';bl_space_type='VIEW_3D';bl_region_type='UI';bl_category='HELIOS'
    def draw(self,ctx):
        l=self.layout;l.label(text='B - Enamel / machined nickel')
        for key,title in [('closed','01  Closed / reference view'),('open','02  Bloom / inner mechanism'),('exploded','03  Exploded components')]:
            op=l.operator('helios.review_pose',text=title);op.state=key
        l.operator('screen.animation_play',text='Play / pause complete sequence',icon='PLAY')
        l.operator('helios.review_render',text='Cycles render this view',icon='RENDER_STILL')
        l.label(text='Frames 1-600 / 24 fps')
        l.label(text='Physical assembly + editable materials')
for cls in [HELIOS_OT_review_pose,HELIOS_OT_review_render,HELIOS_PT_review]:
    try:bpy.utils.register_class(cls)
    except Exception:pass
bpy.context.scene.frame_set(30)
for area in bpy.context.screen.areas:
    if area.type=='VIEW_3D':
        sp=area.spaces.active;sp.region_3d.view_perspective='CAMERA';sp.region_3d.view_camera_zoom=0;sp.overlay.show_overlays=False;sp.shading.type='MATERIAL';sp.shading.use_scene_world=True;sp.shading.use_scene_lights=True;sp.show_region_ui=True
        for reg in area.regions:
            if reg.type=='UI':
                try:reg.active_panel_category='HELIOS'
                except Exception:pass
last_mtime=0
def command_tick():
    global last_mtime
    file=REVIEW/'blender_command.json'
    if file.exists() and file.stat().st_mtime>last_mtime:
        last_mtime=file.stat().st_mtime
        try:
            cmd=json.loads(file.read_text(encoding='utf-8'))
            if cmd.get('pose'):bpy.ops.helios.review_pose(state=cmd['pose'])
            if cmd.get('screenshot'):bpy.ops.screen.screenshot(filepath=str(REVIEW/'blender_screen.png'))
            if cmd.get('reload'):
                file.write_text('{}',encoding='utf-8');last_mtime=file.stat().st_mtime
                bpy.ops.wm.open_mainfile(filepath=str(ROOT/'blender'/'Helios_Incubator.blend'))
                bpy.context.scene.frame_set(30)
                for area in bpy.context.screen.areas:
                    if area.type=='VIEW_3D':
                        sp=area.spaces.active;sp.shading.type='MATERIAL';sp.shading.use_scene_world=True;sp.shading.use_scene_lights=True;sp.region_3d.view_perspective='CAMERA';sp.overlay.show_overlays=False
        except Exception as e:print('HELIOS_REVIEW_COMMAND',e)
    return 1.0
bpy.app.timers.register(command_tick,first_interval=2,persistent=True)
print('HELIOS_LIVE_REVIEW_READY',flush=True)
