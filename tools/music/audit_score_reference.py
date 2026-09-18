"""Build score-time reference from engraved events; MIDI performance ticks are separate."""
from pathlib import Path
from fractions import Fraction
import json,hashlib,collections
import numpy as np
ROOT=Path(__file__).resolve().parents[2];OUT=ROOT/'review/I_refinement/moonlight/onset_refinement'
reports=[]
for movement in [1,2,3]:
 path=ROOT/'production/I_refinement/moonlight/engraving'/f'moonlight{movement}-notation.json';notation=json.loads(path.read_text());groups=collections.defaultdict(list)
 for note in notation['notes']:
  quarter=float(Fraction(note['quarter']));duration=float(Fraction(note['duration_quarters']))
  groups[quarter].append({'pitch':note['pitch'],'duration_quarters':duration,'id':note['id'],'visible':note.get('visible',True),'bar':note['bar']})
 events=[{'quarter':q,'pitches':sorted({n['pitch'] for n in groups[q]}),'heads':groups[q]} for q in sorted(groups)]
 old=json.loads((OUT/f'movement_{movement}.json').read_text());tail=[]
 # Distinctive tail chords are explicit checkable landmarks, not an automatic
 # whole-piece pitch-sequence correspondence or tie/ornament classification.
 for event in events[-10:]:
  for pitch in event['pitches']:
   candidates=[e for e in old['events'] if pitch in e['pitches'] and abs(e['quarter']-event['quarter'])<1.0]
   if candidates:
    nearest=min(candidates,key=lambda e:abs(e['quarter']-event['quarter']));tail.append({'pitch':pitch,'engraved_quarter':event['quarter'],'nearest_midi_quarter':nearest['quarter'],'quarter_difference':nearest['quarter']-event['quarter']})
 report={'movement':movement,'notation_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'events':events,'tail_comparison':tail,'scope':'Engraved notehead main score times are authoritative for staff position. Heads may include ties/grace groups; this is a pitch-occupancy reference, not a claim that every head is a rearticulated onset.'}
 (OUT/f'score_reference_{movement}.json').write_text(json.dumps(report,indent=2)+'\n');reports.append({'movement':movement,'event_groups':len(events),'tail_max_difference_quarters':max(abs(x['quarter_difference']) for x in tail)})
(OUT/'reference_audit.json').write_text(json.dumps({'movements':reports,'specific_issue':'Third-movement final simultaneous engraved chords at quarters1050/1052 have upper MIDI notes delayed by0.7135417 quarter relative to lower notes. Current runtime display is in engraving quarters, so performance-MIDI time cannot be assumed identical.'},indent=2)+'\n');print(reports)
