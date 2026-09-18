"""Author a deterministic, recording-clock music response, without changing audio.

20 ms centered stereo power windows, sampled at 100 Hz. A common scale across
the complete work preserves the relative dynamics between its three movements.
This is a bounded visual envelope, not a loudspeaker/acoustic simulation.
"""
import hashlib
import json
import subprocess
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
ASSETS = ROOT / 'app/assets/collection/art/I/moonlight_candidate'
MANIFEST = ASSETS / 'manifest.json'
OUT = ROOT / 'review/I_refinement/moonlight/current_mouth/response'
RATE, HOP, HALF_WINDOW = 24000, 240, 240


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    manifest = json.loads(MANIFEST.read_text())
    tracks = []
    for row in manifest['movements']:
        audio = ROOT / 'app' / row['audio'].removeprefix('res://')
        assert sha(audio) == row['audio_sha256']
        decoded = subprocess.check_output([
            '/opt/homebrew/bin/ffmpeg', '-v', 'error', '-i', str(audio),
            '-f', 'f32le', '-acodec', 'pcm_f32le', '-ac', '2', '-ar', str(RATE), '-'])
        pcm = np.frombuffer(decoded, dtype='<f4').reshape(-1, 2)
        assert np.isfinite(pcm).all()
        # Sum channel powers; mono downmix could cancel an out-of-phase signal.
        power = np.mean(pcm.astype(np.float64) ** 2, axis=1)
        cumulative = np.r_[0., np.cumsum(power)]
        centers = np.arange(0, len(pcm) + HOP, HOP)
        left = np.clip(centers - HALF_WINDOW, 0, len(pcm))
        right = np.clip(centers + HALF_WINDOW, 0, len(pcm))
        rms = np.sqrt((cumulative[right] - cumulative[left]) / (2 * HALF_WINDOW))
        tracks.append({'row': row, 'rms': rms, 'decoded_seconds': len(pcm) / RATE})
    reference = float(np.percentile(np.concatenate([t['rms'] for t in tracks]), 99))
    floor = 10 ** (-58 / 20)
    assert reference > floor
    result = {'schema': 1, 'interval_seconds': HOP / RATE, 'window_seconds': 2 * HALF_WINDOW / RATE,
              'floor_rms': floor, 'reference_rms': reference,
              'mapping': 'clamp((RMS-floor)/(global_p99-floor),0,1)^0.70',
              'scope': 'Visual music dynamics derived from exact source recordings; not score alignment or physical acoustic motion.',
              'movements': []}
    audit = []
    for t in tracks:
        level = np.clip((t['rms'] - floor) / (reference - floor), 0, 1) ** .70
        values = np.round(level, 6).tolist()
        row = t['row']
        result['movements'].append({'movement': row['movement'], 'audio_sha256': row['audio_sha256'],
                                   'decoded_seconds': t['decoded_seconds'], 'values': values})
        audible = np.flatnonzero(level > .01)
        audit.append({'movement': row['movement'], 'samples': len(values),
                      'decoded_seconds': t['decoded_seconds'], 'audio_sha256': row['audio_sha256'],
                      'first_level_above_0_01_seconds': float(audible[0] * HOP / RATE),
                      'median_level': float(np.median(level)), 'maximum': float(level.max()),
                      'silent_prefix_level_max': float(level[:300].max())})
    target = ASSETS / 'response_envelopes_r1.json'
    target.write_text(json.dumps(result, separators=(',', ':')) + '\n')
    manifest['response_envelope'] = 'res://' + str(target.relative_to(ROOT / 'app'))
    manifest['response_envelope_sha256'] = sha(target)
    # Do not erase the distinction between source PCM durations and runtime metadata.
    manifest['warnings'] = ['Alignment remains estimated except for four locally reviewed tail anchors.',
                            'Current mouth preview only; full conch and art acceptance remain unfinished.']
    MANIFEST.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + '\n')
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / 'envelopes.json').write_text(json.dumps({'script_sha256': sha(Path(__file__)),
        'envelope_sha256': sha(target), 'reference_rms': reference, 'floor_rms': floor,
        'tracks': audit, 'scope': result['scope']}, indent=2) + '\n')
    print(json.dumps(audit))


if __name__ == '__main__':
    main()
