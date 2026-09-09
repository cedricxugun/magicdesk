"""Collect G's actual EXE evidence, retaining frame-time limits and art provenance."""
import pathlib,json,csv,datetime,statistics,subprocess,hashlib,argparse
ROOT=pathlib.Path(__file__).resolve().parents[1];folder=ROOT/'review/G_complete/native'
p=argparse.ArgumentParser();p.add_argument('--ffmpeg',required=True);args=p.parse_args()
log=(folder/'native.log').read_text(encoding='utf-8-sig')
def timestamp(line):
    t=datetime.datetime.strptime(line[:12],'%H:%M:%S.%f');return t.hour*3600+t.minute*60+t.second+t.microsecond/1e6
first=next(timestamp(x) for x in log.splitlines() if ' first frame ' in x)
click=next(timestamp(x) for x in log.splitlines() if 'qa pointer down' in x)
loaded=next(timestamp(x) for x in log.splitlines() if 'COLLECTION_LOAD' in x and '"id":"G"' in x)
start=max(0,click-first-.4)
subprocess.run([args.ffmpeg,'-hide_banner','-loglevel','error','-y','-ss',str(start),'-i',str(folder/'G_native_full.mp4'),'-c:v','libx264','-preset','fast','-crf','17','-pix_fmt','yuv420p','-movflags','+faststart',str(folder/'G_showcase.mp4')],check=True)
rows=list(csv.DictReader((folder/'frame_trace.csv').open(encoding='utf-8-sig')))
def stats(rs):
    vals=sorted(float(x['present_gap_ms']) for x in rs)
    return {'frames':len(rs),'fps':round(1000/statistics.mean(vals),2),'median_ms':round(statistics.median(vals),3),'p95_ms':round(vals[int((len(vals)-1)*.95)],3),'maximum_ms':round(max(vals),3)}
post=[r for r in rows if float(r['elapsed_seconds'])>loaded-first+.5]
checks={k:json.loads((ROOT/'review/G_complete'/v).read_text(encoding='utf-8')) for k,v in [('mechanism','mechanism_qa.json'),('endpoint','endpoint_qa.json'),('clearance','clearance.json'),('native','native/report.json')]}
errors=[x for x in log.splitlines() if 'renderer error:' in x or 'UpdateLayeredWindow error=' in x]
report={'version':'0.3.1 G','all_checks_passed':all(x['all_passed'] for x in checks.values()),'checks':{k:v['all_passed'] for k,v in checks.items()},'native_errors':errors,'shutdown_exit_zero':'renderer exit code=0' in log,'all_frames':stats(rows),'after_G_ready':stats(post),'performance_scope':'Native desktop compositor, RTX 3060, including original-speed 30 fps recording; startup separated from operation.','blender':{'frames':1441,'fps':30,'optical_quads':24,'chips_glints':64,'relief_layers':28,'baked_from':'review/G_complete/mechanical_take.json'},'video':{'path':'review/G_complete/native/G_showcase.mp4','trimmed_start_seconds':round(start,3),'speed':1.0,'source':'native compositor RGBA, app-owned native input replay'},'executable_sha256':hashlib.sha256((ROOT/'dist/staging/MagicDesk-G.exe').read_bytes()).hexdigest()}
(folder/'delivery_report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
art=ROOT/'production/G_complete';files=[art/'images/G_motion_vfx.png',ROOT/'app/assets/collection/art/G/optical_atlas.png']
manifest={'channel':'subscription built-in image_gen','model_id':'not exposed; unverified','files':[{'path':str(x.relative_to(ROOT)).replace('\\','/'),'sha256':hashlib.sha256(x.read_bytes()).hexdigest()} for x in files],'prompts':['production/G_complete/prompts/motion.txt','production/G_complete/prompts/atlas.txt'],'audio_source':'tools/make_g_inscription.py; original PCM comb-tone synthesis','volumetric_geometry':'blender/collection/complete_g.py, 28 authored contour layers; not a flat image projection'}
(art/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(report,ensure_ascii=False,indent=2))
