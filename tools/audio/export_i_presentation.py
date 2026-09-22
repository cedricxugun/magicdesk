"""Export only declared presentation frames, excluding recorder cleanup tail."""
import argparse,json,subprocess,hashlib,shutil
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('--raw',required=True);p.add_argument('--take',required=True);p.add_argument('--out',required=True);a=p.parse_args();raw=Path(a.raw);take=Path(a.take);out=Path(a.out);s=json.loads(take.read_text());frames=int(s['frames']);fps=float(s['fps']);assert frames>0 and fps>0
ffprobe=shutil.which('ffprobe') or '/opt/homebrew/bin/ffprobe';ffmpeg=shutil.which('ffmpeg') or '/opt/homebrew/bin/ffmpeg'
probe=json.loads(subprocess.check_output([ffprobe,'-v','error','-select_streams','v:0','-show_entries','stream=nb_frames','-of','json',str(raw)]));raw_frames=int(probe['streams'][0]['nb_frames']);assert raw_frames>=frames
assert raw_frames<=frames+(12 if s.get('recorder_cleanup_tail')else 3),'Unexpected excess frames: investigate capture rather than hiding a stall with trimming'
subprocess.run([ffmpeg,'-y','-hide_banner','-loglevel','error','-i',str(raw),'-map','0:v:0','-map','0:a:0?','-t',str(frames/fps),'-frames:v',str(frames),'-c:v','libx264','-crf','18','-pix_fmt','yuv420p','-c:a','aac','-b:a','192k','-movflags','+faststart',str(out)],check=True)
sha=lambda x:hashlib.sha256(x.read_bytes()).hexdigest();out.with_suffix('.export.json').write_text(json.dumps({'raw':str(raw),'raw_frames':raw_frames,'presentation_frames':frames,'excluded_cleanup_frames':raw_frames-frames,'duration':frames/fps,'take_sha256':sha(take),'video_sha256':sha(out),'scope':'Retains the first declared frames from time zero. Recorder shutdown tail is excluded; no interior audio/video edits.'},indent=2)+'\n');print('PRESENTATION_EXPORT',frames,'tail excluded',raw_frames-frames)
