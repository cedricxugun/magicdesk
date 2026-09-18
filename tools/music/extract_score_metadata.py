"""Extract exact engraved pitch/time/position data; make a bounded real-score preview."""
from pathlib import Path
from fractions import Fraction
import xml.etree.ElementTree as ET
import re,json,hashlib,copy,argparse
ROOT=Path(__file__).resolve().parents[2];BASE=ROOT/'production/I_refinement/moonlight/engraving';OUT=ROOT/'review/I_refinement/moonlight';OUT.mkdir(parents=True,exist_ok=True)
NS='http://www.w3.org/2000/svg';ET.register_namespace('',NS);ET.register_namespace('xlink','http://www.w3.org/1999/xlink')
parser=argparse.ArgumentParser();parser.add_argument('--variant',choices=['staff','compact'],default='staff');args=parser.parse_args();variant=args.variant
reports=[]
for movement in range(1,4):
 p=BASE/f'moonlight{movement}-{variant}.svg';root=ET.fromstring(p.read_text());notes=[]
 for node in root.iter():
  if not node.get('id','').startswith('md-note-'):continue
  positions=[]
  for part in node.iter():
   transform=part.get('transform','');m=re.fullmatch(r'translate\(([-.\d]+),\s*([-.\d]+)\)',transform)
   if m:positions.append((float(m[1]),float(m[2])))
  assert len(positions)<=1,(node.attrib,positions)
  notes.append({'id':node.get('id'),'pitch':int(node.get('data-pitch')),'quarter':str(Fraction(node.get('data-moment'))*4),'duration_quarters':str(Fraction(node.get('data-duration'))*4),'bar':int(node.get('data-bar')),'voice':node.get('data-voice'),'visible':bool(positions),'x':positions[0][0] if positions else None,'y':positions[0][1] if positions else None})
 assert len({n['id'] for n in notes})==len(notes)
 assert all(0<=n['pitch']<=127 and Fraction(n['duration_quarters'])>0 for n in notes)
 notes.sort(key=lambda n:(Fraction(n['quarter']),n['pitch'],n['voice']))
 measures=[]
 for bar in sorted({n['bar'] for n in notes}):
  group=[n for n in notes if n['bar']==bar and n['visible']]
  if not group:continue
  measures.append({'bar':bar,'first_quarter':str(min(Fraction(n['quarter']) for n in group)),'first_x':min(n['x'] for n in group),'last_x':max(n['x'] for n in group),'notes':len(group)})
 data={'movement':movement,'svg_sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'viewbox':root.get('viewBox'),'notes':notes,'measures':measures,'scope':'Engraved score coordinates/time, not mapped to recorded performance. Tied notes remain visual events; MIDI note attacks can differ.'}
 (BASE/(f'moonlight{movement}-'+('compact-' if variant=='compact' else '')+'notation.json')).write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')
 # Cairo outlines all textual musical marks; Godot's SVG reader drops raw <text>.
 native=BASE/(f'moonlight{movement}-'+('compact-' if variant=='compact' else '')+'cairo.svg');assert native.exists(),'Compile the Cairo SVG before producing runtime previews'
 original_vb=[float(x) for x in data['viewbox'].split()]
 root=ET.fromstring(native.read_text());vb=[float(x) for x in root.get('viewBox').split()];scale=vb[2]/original_vb[2]
 limit=(measures[min(2,len(measures)-1)]['first_x']-1)*scale
 root.set('viewBox',f'0 {vb[1]} {limit} {vb[3]}');root.set('width','1400');root.set('height',str(round(1400*vb[3]/limit)))
 for node in root.iter():
  for key in ['fill','stroke']:
   if node.get(key) and node.get(key)!='none':node.set(key,'#e5b879')
  if node.get('style'):node.set('style',node.get('style').replace('rgb(0%,0%,0%)','#e5b879'))
 (OUT/f'movement{movement}_{variant}_first_bars.svg').write_bytes(ET.tostring(root,encoding='utf-8',xml_declaration=True))
 reports.append({'movement':movement,'noteheads':len(notes),'measure_numbers':[measures[0]['bar'],measures[-1]['bar']],'last_note_quarter':notes[-1]['quarter'],'first_pitch':notes[0]['pitch'],'output':str(BASE/(f'moonlight{movement}-'+('compact-' if variant=='compact' else '')+'notation.json'))})
(OUT/f'notation_inventory_{variant}.json').write_text(json.dumps(reports,indent=2)+'\n');print(json.dumps(reports,indent=2))
