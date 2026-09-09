import bpy,sys,json
from pathlib import Path
args=sys.argv[sys.argv.index('--')+1:]
ident=args[0];root=Path(__file__).resolve().parents[2]
scene=bpy.context.scene;scene.render.engine='BLENDER_EEVEE'
scene.render.resolution_percentage=70
output=root/'review/collection';output.mkdir(parents=True,exist_ok=True)
for label,frame in [('closed',1),('open',145),('exploded',277)]:
    scene.frame_set(frame)
    scene.render.filepath=str(output/(ident+'_'+label+'.png'))
    bpy.ops.render.render(write_still=True)
    print('COLLECTION_RENDER',ident,label,flush=True)
