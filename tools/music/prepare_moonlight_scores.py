"""Compile preserved Mutopia sources into tagged continuous staff artwork.

Requires LilyPond 2.26.0. This is engraving data, not audio alignment.
"""
from pathlib import Path
import argparse,subprocess,re,json,hashlib
ROOT=Path(__file__).resolve().parents[2]
a=argparse.ArgumentParser();a.add_argument('--lilypond',default='/tmp/magicdesk-lilypond/lilypond-2.26.0/bin/lilypond');a.add_argument('--movement',type=int,nargs='+',default=[1,2,3]);a.add_argument('--compact',action='store_true');args=a.parse_args()
base=ROOT/'production/I_refinement/moonlight';out=base/'engraving';out.mkdir(exist_ok=True)
converter=str(Path(args.lilypond).with_name('convert-ly'))
hook=r'''
% Stable metadata for real engraved noteheads; timing is score time, not recording time.
#(define md-note-serial 0)
#(define (md-note-tags context)
  (make-engraver
    (acknowledgers
      ((note-head-interface engraver grob source-engraver)
        (let* ((event (ly:grob-property grob 'cause))
               (pitch (ly:event-property event 'pitch))
               (moment (ly:context-current-moment context))
               (duration (ly:event-property event 'duration))
               (dur (ly:duration->number duration)))
          (set! md-note-serial (+ md-note-serial 1))
          (ly:grob-set-property! grob 'output-attributes
            `((id . ,(format #f "md-note-~a" md-note-serial))
              (data-pitch . ,(+ 60 (ly:pitch-semitones pitch)))
              (data-moment . ,(format #f "~a" (ly:moment-main moment)))
              (data-duration . ,(format #f "~a" dur))
              (data-bar . ,(ly:context-property context 'currentBarNumber))
              (data-voice . ,(ly:context-id context)))))))))
\paper {
  page-breaking = #ly:one-line-auto-height-breaking
  indent = 0\mm
  top-margin = 3\mm
  bottom-margin = 3\mm
  left-margin = 3\mm
  right-margin = 3\mm
  print-page-number = ##f
  tagline = ##f
}
'''
score_music={
1:r'''\new PianoStaff <<
 \new Staff = "up" << \new Voice = "upper" { \voiceOne \topmain } \new Voice = "middle" { \voiceTwo \topsecondary } >>
 \new Staff = "down" { \bottom }
>>''',
2:r'''\new PianoStaff << \new Staff = "up" \new Voice = "main" { \top \topDC } \new Staff = "down" { \bottom \bottomDC } >>''',
3:r'''\new PianoStaff <<
 \new Staff = "up" << \topmain \topsecondary >>
 \new Staff = "down" << \bottom \bottomsecondary \sustain >>
>>'''}
report_path=out/('build-compact.json' if args.compact else 'build.json')
report=json.loads(report_path.read_text()) if report_path.exists() else []
report=[row for row in report if row['movement'] not in args.movement]
for movement in args.movement:
    source=base/'mutopia'/f'moonlight{movement}-a4.ly'
    converted=subprocess.run([converter,str(source)],capture_output=True,text=True,check=True)
    (out/f'conversion{movement}.log').write_text(converted.stderr)
    text=converted.stdout.split('\\book',1)[0]
    # convert-ly cannot migrate this old Scheme helper. Preserve quarter-note triplet grouping.
    text=re.sub(r"(?m)^.*#\(override-auto-beam-setting.*$",'',text)
    if movement==1:
        text=text.replace('\\tupletSpan 4',"\\set Timing.beamExceptions = #'()\n\\set Timing.beatBase = #1/4\n\\set Timing.beatStructure = #'(1 1 1 1)\n\\tupletSpan 4")
    text=re.sub(r'\\(?:noPageBreak|pageBreak|noBreak|break)\b','',text)
    if movement==2:
        # Written Allegretto D.C.: append the opening section without its internal repeat.
        # The second volta in each voice begins the Trio; retain the source's relative pitch scope.
        dc=[]
        for name in ['top','bottom']:
            start=re.search(r'(?m)^'+name+r'\s*=\s*',text).end()
            part=text[start:]
            starts=list(re.finditer(r'\\repeat volta 2',part))
            assert len(starts)>=3
            prefix=part[:starts[1].start()].replace('\\repeat volta 2','\\repeat volta 1')
            dc.append(name+'DC = '+prefix+'}\n')
        text+='\n'+'\n'.join(dc)
    text+=hook+'\n\\score {\n \\unfoldRepeats '+score_music[movement]+r'''
 \layout {
  \context { \Voice \consists #md-note-tags }
  \context { \Score \omit Fingering \omit StringNumber }
 }
 \midi { \tempo 4 = 60 }
}
'''
    if args.compact:
        text=text.replace('\\context { \\Voice \\consists #md-note-tags }','\\context { \\Voice \\consists #md-note-tags \\override TextScript.stencil = ##f \\override Fingering.stencil = ##f }')
    suffix='compact' if args.compact else 'staff'
    path=out/f'moonlight{movement}-{suffix}.ly';path.write_text(text)
    command=[args.lilypond,'--svg','-o',str(out/f'moonlight{movement}-{suffix}'),str(path)]
    result=subprocess.run(command,capture_output=True,text=True)
    (out/f'engraving{movement}-{suffix}.log').write_text(result.stdout+result.stderr)
    report.append({'movement':movement,'exit_code':result.returncode,'input_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'output_source':str(path.relative_to(ROOT)),'scope':'Volta repeats unfolded; movement II Allegretto Da Capo appended without repeats. Requires event/route review and recording alignment; no final App binding.'})
    print('MOONLIGHT_ENGRAVING',movement,result.returncode,flush=True)
report_path.write_text(json.dumps(report,indent=2)+'\n')
raise SystemExit(1 if any(x['exit_code'] for x in report) else 0)
