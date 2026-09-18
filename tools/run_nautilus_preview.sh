#!/bin/sh
set -eu
magicdesk_root="$(cd "$(dirname "$0")/.." && pwd)"
magicdesk_godot="${MAGICDESK_GODOT_BIN:-/Applications/Godot.app/Contents/MacOS/Godot}"
exec "$magicdesk_godot" --path "$magicdesk_root/app" res://review/i_mouth_viewer.tscn -- --review-config=res://../review/I_refinement/nautilus_r1/interactive_r58/viewer_config.json --review-diagnostics=res://../review/I_refinement/nautilus_r1/interactive_r58/user_live.json
