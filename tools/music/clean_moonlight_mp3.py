"""Remove an identified non-audio HTML footer; retain original and verify PCM identity."""
from pathlib import Path
import re,json,hashlib,subprocess
ROOT=Path(__file__).resolve().parents[2];BASE=ROOT/'app/assets/collection/art/I/moonlight_candidate';source=BASE/'pitman_movement_3_original.mp3';data=source.read_bytes();original_sha=hashlib.sha256(data).hexdigest();assert original_sha=='a4c16b5e2c5ee548be14e74136b687f8586e619fd1c06abc566ebeeae511066f'
match=re.search(rb'\n<!-- Ejected in [0-9.]+ seconds\. -->$',data);assert match is not None
clean=data[:match.start()];assert clean[-128:-125]==b'TAG','Expected intact ID3v1 tag before HTML footer'
dest=BASE/'pitman_movement_3_clean.mp3'
if dest.exists():assert dest.read_bytes()==clean
else:dest.write_bytes(clean)

def pcm(path):
 p=subprocess.Popen(['/opt/homebrew/bin/ffmpeg','-v','error','-i',str(path),'-map','0:a:0','-f','f32le','-acodec','pcm_f32le','-'],stdout=subprocess.PIPE,stderr=subprocess.PIPE);h=hashlib.sha256();count=0
 while True:
  block=p.stdout.read(1024*1024)
  if not block:break
  count+=len(block);h.update(block)
 error=p.stderr.read().decode(errors='replace');code=p.wait();assert code==0,error
 return {'sha256':h.hexdigest(),'bytes':count,'stderr':error}
a=pcm(source);b=pcm(dest);assert a['sha256']==b['sha256'] and a['bytes']==b['bytes']
report={'original':str(source.relative_to(ROOT)),'original_sha256':original_sha,'clean':str(dest.relative_to(ROOT)),'clean_sha256':hashlib.sha256(clean).hexdigest(),'removed_bytes':len(data)-len(clean),'removed_text':match.group().decode(),'original_id3v1_preserved':True,'pcm_original':a,'pcm_clean':b,'pcm_identical':True,'scope':'Exact suffix removal after intact ID3v1 tag, no MP3 frame editing/re-encoding; full ffmpeg decoded PCM byte-identical. Does not validate musical alignment or subjective recording quality.'}
out=ROOT/'review/I_refinement/moonlight/mp3_clean';out.mkdir(parents=True,exist_ok=True);(out/'report.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
