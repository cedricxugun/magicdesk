"""Collect verifiable F delivery evidence and trim waiting from the real video."""
import pathlib,json,csv,datetime,statistics,subprocess,hashlib,argparse,re
ROOT=pathlib.Path(__file__).resolve().parents[1];folder=ROOT/'review/F_complete/final'
p=argparse.ArgumentParser();p.add_argument('--ffmpeg',required=True);args=p.parse_args()
log=(folder/'native.log').read_text(encoding='utf-8-sig')
def timestamp(line):
    t=datetime.datetime.strptime(line[:12],'%H:%M:%S.%f');return t.hour*3600+t.minute*60+t.second+t.microsecond/1e6
first=next(timestamp(x) for x in log.splitlines() if ' first frame ' in x)
click=next(timestamp(x) for x in log.splitlines() if 'qa pointer down' in x)
loaded=next(timestamp(x) for x in log.splitlines() if 'COLLECTION_LOAD' in x and '"id":"F"' in x)
start=max(0,click-first-.4)
subprocess.run([args.ffmpeg,'-hide_banner','-loglevel','error','-y','-ss',str(start),'-i',str(folder/'F_native_full.mp4'),'-c:v','libx264','-preset','fast','-crf','17','-pix_fmt','yuv420p','-movflags','+faststart',str(folder/'F_showcase.mp4')],check=True)
rows=list(csv.DictReader((folder/'frame_trace.csv').open(encoding='utf-8-sig')))
def stats(rs):
    values=sorted(float(x['present_gap_ms']) for x in rs)
    return dict(frames=len(rs),fps=round(1000/statistics.mean(values),2),median_ms=round(statistics.median(values),3),p95_ms=round(values[int((len(values)-1)*.95)],3),maximum_ms=round(max(values),3))
post=[r for r in rows if float(r['elapsed_seconds'])>loaded-first+.5]
checks={name:json.loads((ROOT/'review/F_complete'/filename).read_text(encoding='utf-8')) for name,filename in [('physics','physics.json'),('instrument','instrument_qa.json'),('lagrange','lagrange_equivalence.json'),('clearance','clearance.json'),('native','final/report.json'),('blender','blender_bake.json')]}
native_errors=[line for line in log.splitlines() if 'renderer error:' in line or 'UpdateLayeredWindow error=' in line]
report=dict(version='0.3.0 F delivery',test_passed={k:v['all_passed'] for k,v in checks.items() if 'all_passed' in v},native_window_errors=native_errors,renderer_shutdown_exit_zero='renderer exit code=0' in log,frame_time_all=stats(rows),frame_time_after_F_ready=stats(post),performance_scope='Native desktop presentation while recording at 30 fps; initial load reported separately.',video=dict(path='review/F_complete/final/F_showcase.mp4',trimmed_start_seconds=round(start,3),speed=1.0,source='native compositor RGBA stream; application-owned input replay'),blender=checks['blender'],lagrange=checks['lagrange'])
(folder/'delivery_report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
art=ROOT/'production/F_complete'
files=[art/'images/F_motion_vfx.png',art/'images/F_calibration_signature.png',ROOT/'app/assets/collection/art/F/field_atlas.png']
manifest=dict(channel='subscription built-in image_gen',model_id='not exposed; unverified',files=[dict(path=str(x.relative_to(ROOT)).replace('\\','/'),sha256=hashlib.sha256(x.read_bytes()).hexdigest()) for x in files],prompts=['production/F_complete/prompts/F_motion_vfx.txt','production/F_complete/prompts/F_calibration_signature.txt','production/F_complete/prompts/F_field_atlas.txt'],atlas_centers=[[.4948,.4993],[.5003,.5000],[.4909,.4509],[.3764,.4557]],audio_source='tools/make_f_resonance.py; original PCM modal synthesis')
(art/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(report,ensure_ascii=False,indent=2))
