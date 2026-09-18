"""Verify container frames, action clocks, pause silence and recording alignment."""
import argparse,json,subprocess,re,hashlib
from pathlib import Path
import numpy as np
from PIL import Image
parser=argparse.ArgumentParser();parser.add_argument('--video',required=True);parser.add_argument('--take',required=True);parser.add_argument('--out',required=True);args=parser.parse_args();video=Path(args.video);take_path=Path(args.take);take=json.loads(take_path.read_text());ROOT=Path(__file__).resolve().parents[2]
def execute(argv):return subprocess.run(argv,capture_output=True,check=True)
probe=json.loads(execute(['/opt/homebrew/bin/ffprobe','-v','error','-show_streams','-show_format','-of','json',str(video)]).stdout);stream=next(r for r in probe['streams']if r['codec_type']=='video');fps=take['fps'];frames=int(stream['nb_frames']);frame_match=take['frames']<=frames<=take['frames']+3
samples=take['samples'];counter='forced_draw_calls'if take.get('force_capture')else 'engine_rendered_frame';has_counter=all(counter in r for r in samples);engine_steps=has_counter and all(b[counter]-a[counter]==b['frame']-a['frame']for a,b in zip(samples,samples[1:]));groups=[]
for sample in samples:
    state=sample.get('music',{}).get('state','unknown')
    if not groups or groups[-1]['state']!=state:groups.append({'state':state,'samples':[]})
    groups[-1]['samples'].append(sample)
audio=[];clock=[]
for group in groups:
    rows=group['samples'];start=rows[0]['frame']/fps;end=rows[-1]['frame']/fps
    if end-start<.6:continue
    point=(start+end)/2;window=min(.6,(end-start)/2)
    result=subprocess.run(['/opt/homebrew/bin/ffmpeg','-nostdin','-hide_banner','-ss',str(point),'-t',str(window),'-i',str(video),'-af','volumedetect','-f','null','-'],capture_output=True,text=True,check=True);match=re.search(r'max_volume: ([^ ]+) dB',result.stderr);assert match
    peak=float(match.group(1));passed=peak>-65 if group['state']=='playing'else peak<-80
    audio.append({'state':group['state'],'start':point,'duration':window,'max_dbfs':peak,'passed':passed})
    origin=float(rows[0].get('music',{}).get('local_seconds',0))
    errors=[abs(float(r['music']['local_seconds'])-origin-((r['frame']-rows[0]['frame'])/fps if group['state']=='playing'else 0))for r in rows]
    clock.append({'state':group['state'],'start_frame':rows[0]['frame'],'maximum_clock_drift':max(errors),'passed':max(errors)<.10})
def decode(path,start,length,rate=8000):
    result=execute(['/opt/homebrew/bin/ffmpeg','-nostdin','-v','error','-ss',str(start),'-t',str(length),'-i',str(path),'-ac','1','-ar',str(rate),'-f','f32le','-']);return np.frombuffer(result.stdout,dtype='<f4').astype(np.float64)
first=next(g for g in groups if g['state']=='playing');capture_start=first['samples'][0]['frame']/fps;rate=8000
manifest=json.loads((ROOT/'app/assets/collection/art/I/moonlight_candidate/manifest.json').read_text());source=ROOT/'app'/manifest['movements'][0]['audio'].removeprefix('res://');assert hashlib.sha256(source.read_bytes()).hexdigest()==manifest['movements'][0]['audio_sha256']
source_start=float(take.get('source_start_seconds',4.15));skipped=[];alignment=None
for elapsed in [2.,4.,6.,8.]:
    if capture_start+elapsed+1.>first['samples'][-1]['frame']/fps:continue
    reference=decode(source,source_start+elapsed-.25,1.5)
    if np.max(np.abs(reference),initial=0.)<1e-6:
        skipped.append({'source_seconds':source_start+elapsed,'reason':'Selected recording is silent here; a zero waveform cannot establish correlation.'});continue
    captured=decode(video,capture_start+elapsed,1.)
    cross=np.correlate(reference,captured,'valid');power=np.convolve(reference*reference,np.ones(len(captured)),mode='valid');correlation=cross/np.sqrt(np.maximum(power*np.sum(captured*captured),1e-30));best=int(np.argmax(correlation));offset=best/rate-.25
    alignment={'correlation':float(correlation[best]),'offset_seconds':offset,'capture_seconds':capture_start+elapsed,'source_seconds':source_start+elapsed,'skipped_silent_windows':skipped,'passed':float(correlation[best])>.95 and abs(offset)<.10,'scope':'One audible exported first-movement window compared with the selected source recording; silent source intro is not used for correlation. Not score-note alignment.'};break
assert alignment is not None,'No audible first-group window available for waveform verification'

decoded_probe=json.loads(execute(['/opt/homebrew/bin/ffprobe','-v','error','-select_streams','v:0','-count_frames','-show_entries','stream=nb_read_frames','-of','json',str(video)]).stdout);decoded_count=int(decoded_probe['streams'][0]['nb_read_frames']);assert decoded_count==frames
last_png=take_path.parent/('frame_%03d.png'%(take['frames']-1));expected_image=np.asarray(Image.open(last_png).convert('RGB'),dtype=np.float64);raw=execute(['/opt/homebrew/bin/ffmpeg','-nostdin','-v','error','-i',str(video),'-vf','select=eq(n\\,%d)'%(frames-1),'-frames:v','1','-f','rawvideo','-pix_fmt','rgb24','-']).stdout
actual_image=np.frombuffer(raw,dtype=np.uint8).reshape((int(stream['height']),int(stream['width']),3));same_size=actual_image.shape==expected_image.shape;pixel_error=float(np.mean((actual_image.astype(float)-expected_image)**2)/255**2)if same_size else 1.;final_image={'same_dimensions':same_size,'normalized_mean_square_error':pixel_error,'passed':same_size and pixel_error<.01,'scope':'Decoded final frame matches the declared end-state screenshot within lossy-video tolerance.'}
continuity=None
if take.get('capture_mode')=='continuous_music':
    states=[g['state']for g in groups]
    windows=[]
    for elapsed in [12.,14.,17.,30.,50.]:
        if capture_start+elapsed+1.>take['frames']/fps:continue
        capture=decode(video,capture_start+elapsed,1.)
        ref=decode(source,float(take.get('source_start_seconds',0.))+elapsed-.25,1.5)
        cross=np.correlate(ref,capture,'valid');power=np.convolve(ref*ref,np.ones(len(capture)),mode='valid');corr=cross/np.sqrt(np.maximum(power*np.sum(capture*capture),1e-30));best=int(np.argmax(corr));offset=best/rate-.25
        windows.append({'capture_seconds':capture_start+elapsed,'source_seconds':float(take.get('source_start_seconds',0.))+elapsed,'correlation':float(corr[best]),'offset_seconds':offset,'passed':float(corr[best])>.95 and abs(offset)<.10})
    continuity={'state_groups':states,'ends_playing':samples[-1]['music']['state']=='playing','audio_windows':windows,'passed':states==['stopped','playing']and samples[-1]['music']['state']=='playing'and all(w['passed']for w in windows),'scope':'No sampled pause/stop after start, source-audio matching across the former 15/17/20-second test interruptions and later windows when those windows lie within the declared presentation. Does not certify every sample or full-work playback.'}
passed=frame_match and engine_steps and all(r['passed']for r in audio+clock)and alignment['passed']and final_image['passed']and (continuity is None or continuity['passed']);d={'passed':passed,'video':str(video),'video_sha256':hashlib.sha256(video.read_bytes()).hexdigest(),'take':str(take_path),'container_frames':frames,'decoded_frames':decoded_count,'declared_action_frames':take['frames'],'duration':float(probe['format']['duration']),'frame_count_passed':frame_match,'draw_step_counter':counter,'action_draw_step_correspondence_passed':engine_steps,'samples_with_window_not_drawable':sum(not r.get('window_can_draw',True)for r in samples),'audio_segments':audio,'clock_groups':clock,'source_audio_alignment':alignment,'final_frame':final_image,'continuous_playback':continuity,'scope':'Decoded/container frame count, sampled draw-call/action correspondence, pause/stop silence, playback clock drift, excerpt waveform alignment, continuous-mode interruption windows when requested and final declared-state image. Forced calls tracked explicitly; Engine frames_drawn does not count them consistently. Not full-work musical synchronization or visual/native acceptance.'};Path(args.out).write_text(json.dumps(d,indent=2)+'\n');print(json.dumps(d,indent=2))
