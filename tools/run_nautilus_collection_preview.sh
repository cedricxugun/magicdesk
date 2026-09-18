#!/bin/sh
set -eu
magicdesk_root="$(cd "$(dirname "$0")/.." && pwd)"
magicdesk_godot="${MAGICDESK_GODOT_BIN:-/Applications/Godot.app/Contents/MacOS/Godot}"
exec "$magicdesk_godot" --path "$magicdesk_root/app" --script res://review/i_collection_preview.gd
