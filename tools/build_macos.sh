#!/bin/bash
set -euo pipefail

helios_root="$(cd "$(dirname "$0")/.." && pwd)"
helios_godot="${GODOT_BIN:-/Applications/Godot.app/Contents/MacOS/Godot}"
helios_app="${MAGICDESK_APP_PATH:-$helios_root/dist/macos/MagicDesk.app}"
helios_zip="${MAGICDESK_ZIP_PATH:-$helios_root/dist/MagicDesk-macOS-arm64.zip}"

[[ "$(uname -s)" == Darwin ]] || { echo 'Build this bundle on macOS.' >&2; exit 1; }
[[ -x "$helios_godot" ]] || { echo 'Set GODOT_BIN to the Godot 4.7.1 executable.' >&2; exit 1; }
[[ "$("$helios_godot" --version)" == 4.7.1.stable.* ]] || { echo 'Godot 4.7.1 stable is required.' >&2; exit 1; }

# Fail early when Git LFS source files have not been downloaded.
python3 - "$helios_root" <<'PY'
import pathlib, subprocess, sys
root = pathlib.Path(sys.argv[1])
files = subprocess.check_output(['git', '-C', str(root), 'ls-files', '-z', 'app']).decode().split('\0')
for name in filter(None, files):
    path = root / name
    if path.is_file() and path.stat().st_size < 1024:
        if path.read_bytes().startswith(b'version https://git-lfs.github.com/spec/v1'):
            raise SystemExit(f'Run git lfs pull first: {name}')
PY

mkdir -p "$(dirname "$helios_app")" "$(dirname "$helios_zip")"
"$helios_godot" --headless --editor --path "$helios_root/app" --import
"$helios_godot" --headless --path "$helios_root/app" --export-release macOS "$helios_app"
cp "$helios_root/dist/THIRD_PARTY_NOTICES.txt" "$helios_app/Contents/Resources/THIRD_PARTY_NOTICES.txt"
cp "$helios_root/使用说明-macOS.md" "$helios_app/Contents/Resources/使用说明-macOS.md"
# Godot's installed official template is Universal 2. Thin every Mach-O before
# signing so the delivered app contains only this computer's native arm64 code.
python3 - "$helios_app" <<'PY'
import pathlib, subprocess, sys
app = pathlib.Path(sys.argv[1])
for path in app.rglob('*'):
    if not path.is_file() or path.is_symlink():
        continue
    with path.open('rb') as stream:
        magic = stream.read(4)
    if magic not in (b'\xca\xfe\xba\xbe', b'\xbe\xba\xfe\xca', b'\xca\xfe\xba\xbf'):
        continue
    archs = subprocess.check_output(['lipo', str(path), '-archs'], text=True).split()
    if 'arm64' not in archs:
        raise SystemExit(f'Missing arm64: {path}')
    if len(archs) > 1:
        temp = path.with_name(path.name + '.arm64')
        subprocess.run(['lipo', str(path), '-thin', 'arm64', '-output', str(temp)], check=True)
        temp.chmod(path.stat().st_mode)
        temp.replace(path)
PY
# Local ad-hoc signature; this does not claim Developer ID or notarization.
codesign --force --deep --sign - "$helios_app"
codesign --verify --deep --strict --verbose=2 "$helios_app"
helios_executable=$(/usr/libexec/PlistBuddy -c 'Print :CFBundleExecutable' "$helios_app/Contents/Info.plist")
lipo "$helios_app/Contents/MacOS/$helios_executable" -verify_arch arm64
ditto -c -k --sequesterRsrc --keepParent "$helios_app" "$helios_zip"
(cd "$(dirname "$helios_zip")" && shasum -a 256 "$(basename "$helios_zip")" > "$(basename "${helios_zip%.zip}").sha256")
echo "App: $helios_app"
echo "ZIP: $helios_zip"
