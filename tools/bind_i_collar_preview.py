"""Bind freshly checked collar geometry to its own aperture and optical layout.

The old diaphragm preview assets remain valid. Do not relabel old pass receipts.
"""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REVIEW = ROOT / 'review/I_refinement/part_a_mouth/shutter_r2/collar_clamps'
ASSETS = ROOT / 'app/assets/collection/art/I/collar_clamps'


def read(path):
    return json.loads(path.read_text())


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n')


def main():
    spec_path = REVIEW / 'build.json'
    spec = read(spec_path)
    assert sha(ROOT / spec['source']) == spec['source_sha256']
    assert sha(ROOT / spec['component']) == spec['component_sha256']
    for name, key in [('collar_hardware_check.json', 'passed'), ('geometry_check.json', 'scoped_passed'),
                      ('combination_check.json', 'passed'), ('glb_geometry_check.json', 'passed'),
                      ('attributes_qa.json', 'passed')]:
        check = read(REVIEW / name)
        assert check[key] and check['source_sha256'] == spec['source_sha256'], name
        if 'component_sha256' in check:
            assert check['component_sha256'] == spec['component_sha256'], name

    measured = read(REVIEW / 'aperture_measurement.json')
    assert measured['source_sha256'] == spec['source_sha256']
    assert measured['component_sha256'] == spec['component_sha256']
    assert [v['opening'] for v in measured['samples']] == [i / 32 for i in range(33)]
    profile = {k: measured[k] for k in ['source_sha256', 'component_sha256', 'scope']}
    profile['samples'] = [{k: row[k] for k in ['opening', 'clear_fraction']} for row in measured['samples']]
    profile['max_grid_fraction_difference'] = max(abs(r['fine']['clear_fraction'] - r['coarse']['clear_fraction']) for r in measured['convergence'])
    profile['measurement_sha256'] = sha(REVIEW / 'aperture_measurement.json')
    profile_path = ASSETS / 'aperture_profile.json'
    write(profile_path, profile)

    old_layout_path = ROOT / 'app/assets/collection/art/I/moonlight_candidate/current_mouth/layout.json'
    layout = read(old_layout_path)
    mount = read(REVIEW / 'optics_mount_check.json')
    assert mount['passed'] and mount['mouth_source_sha256'] == spec['source_sha256']
    assert mount['mouth_component_sha256'] == spec['component_sha256']
    assert mount['source_sha256'] == layout['source_sha256']
    assert mount['optics_component_sha256'] == sha(ROOT / layout['component']) == layout['component_sha256']
    layout.update(mouth_source_sha256=spec['source_sha256'], mouth_component_sha256=spec['component_sha256'],
                  prior_layout_sha256=sha(old_layout_path), mount_check_sha256=sha(REVIEW / 'optics_mount_check.json'))
    layout['scope'] = 'Same authored optical geometry and placement, freshly checked against collar source in nine mouth poses. No full-conch or art acceptance.'
    layout_path = ASSETS / 'music_layout.json'
    write(layout_path, layout)

    spec['aperture_profile'] = 'res://' + str(profile_path.relative_to(ROOT / 'app'))
    spec['music_optics_layout'] = 'res://' + str(layout_path.relative_to(ROOT / 'app'))
    spec['preview_checks'] = {key: str((REVIEW / name).relative_to(ROOT)) for key, name in [
        ('foil_frames', 'attributes_qa.json'), ('music_controller', 'controller_qa.json'),
        ('music_response', 'response_qa.json'), ('optics_mount', 'optics_mount_check.json')]}
    write(spec_path, spec)
    old_profile = read(ROOT / 'app/assets/collection/art/I/diaphragm/aperture_profile.json')
    comparison = max(abs(a['clear_fraction'] - b['clear_fraction']) for a, b in zip(profile['samples'], old_profile['samples']))
    write(REVIEW / 'preview_binding.json', {
        'source_sha256': spec['source_sha256'], 'component_sha256': spec['component_sha256'],
        'profile_sha256': sha(profile_path), 'layout_sha256': sha(layout_path),
        'fresh_aperture_difference_from_prior': comparison,
        'scope': 'Bindings generated after current source/GLB/aperture/optical-mount checks. Runtime/music/native checks must still run.'})
    print('I_COLLAR_PREVIEW_BOUND', comparison)


if __name__ == '__main__':
    main()
