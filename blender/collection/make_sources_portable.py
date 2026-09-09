"""Keep collection Blender images relative to the checkout for device handoff."""
import bpy,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
report=[]
for path in sorted((ROOT/'blender/collection').glob('*.blend')):
    bpy.ops.wm.open_mainfile(filepath=str(path))
    bpy.ops.file.make_paths_relative()
    bpy.ops.wm.save_as_mainfile(filepath=str(path),check_existing=False)
    missing=[]
    for image in bpy.data.images:
        if image.source=='FILE' and image.filepath and not image.packed_file:
            target=Path(bpy.path.abspath(image.filepath))
            if not target.exists():missing.append(image.filepath)
    report.append({'source':str(path.relative_to(ROOT)),'missing_external_images':missing})
    print('PORTABLE_SOURCE',path.name,'missing',len(missing),flush=True)
(ROOT/'production/selector_rework/source_portability.json').write_text(json.dumps(report,indent=2))
