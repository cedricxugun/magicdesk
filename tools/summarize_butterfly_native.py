"""Keep bounded native evidence; do not count unattended overnight profiling as QA."""
import csv
import json
import statistics
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'review/G_optical_curator/butterfly_r2/native'

def read_json(path):
    return json.loads(path.read_text())

def summarize(path, start, end):
    groups = defaultdict(list)
    events = []
    previous = None
    peak_energy = 0.0
    with path.open() as stream:
        for row in csv.DictReader(stream):
            if None in row or None in row.values():
                continue
            t = float(row['wall_s'])
            if not start <= t <= end:
                continue
            key = (row['model'], row['curiosity'], row['stage'])
            if key != previous:
                events.append(row)
                previous = key
            groups['/'.join(key)].append(float(row['interval_ms']))
            if row['curiosity'] == '1':
                peak_energy = max(peak_energy, float(row['energy']))
    stats = {}
    for key, values in groups.items():
        values.sort()
        stats[key] = {'frames': len(values), 'median_ms': statistics.median(values),
                      'p95_ms': values[int((len(values)-1)*.95)], 'max_ms': max(values)}
    return {'window_wall_s': [start, end], 'frame_intervals': stats,
            'events': events, 'G1_peak_energy': peak_energy,
            'gpu_timing': 'Unavailable: Metal viewport reported zero; not zero GPU cost.'}

start = read_json(OUT / 'resume_review.json')['start_wall_s']
resume = summarize(OUT / 'frames.csv', start, start + 1800)
fresh = summarize(OUT / 'fresh/frames.csv', 1450, 1500)
captures = {}
for p in sorted(OUT.glob('resume_0*.json')):
    state = read_json(p)['collection']['play']['g_instrument']
    captures[p.name] = {k: state[k] for k in ['selected', 'loaded_index', 'owners',
        'stage', 'parameters', 'action_count', 'action_energy', 'butterfly']}
assert captures['resume_02_fold.json']['parameters'][1] < .8
assert abs(captures['resume_03_wheel.json']['parameters'][1] - .568076923076923) < 1e-6
assert captures['resume_04_release.json']['action_energy'] == 0
assert captures['resume_05_change.json']['owners'][1] == 'slot'
fresh_stages = [e['stage'] for e in fresh['events'] if e['curiosity'] == '1']
assert 'printing' in fresh_stages and 'folding_butterfly' in fresh_stages
report = {'scope': 'Independent arm64 native app, real CUA controls; development checkpoint only.',
    'build': read_json(OUT / 'build.json'), 'captures': captures,
    'resume': resume, 'fresh': fresh,
    'verified': ['Physical slider drag and wheel alter aperture',
        'Action gesture registers and releases to zero energy',
        'Dial change folds butterfly, erases it, returns original disc and loads curiosity 2',
        'Fresh physical dial loads G1 through reading and printing',
        'Native Tab after completed formation returns original disc and exposes mechanical plaques'],
    'limitations': ['Initial G1 selection before resumed session was not performed by this review',
        'Attempted partial-print native cancel arrived after printing completed; partial native cancellation unverified',
        'Exact exported PCK headless control replay passes partial cancel; distinct from native input',
        'Native gesture recorded no nonzero charge sample; sustained hold peak is only covered by scripted replay',
        'Not stable 60 FPS; frame intervals include CUA capture and OS scheduling',
        'Small physical lettering and whole-G choreography remain to refine',
        'No final visual/AAA acceptance; curiosities 2-5 remain old']}
(OUT / 'native_input_report.json').write_text(json.dumps(report, indent=2) + '\n')
print(json.dumps({'report': str(OUT / 'native_input_report.json'),
    'G1_frame_intervals': resume['frame_intervals'].get('G/1/playing'),
    'G1_peak_energy': resume['G1_peak_energy']}, indent=2))
