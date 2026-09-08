# Native presentation review — 2026-09-08

Baseline: `cinematic_asset_native/frame_trace.csv` and `performance.json`.

The baseline presented 2028 frames at 47.79 FPS, with a 20.29 ms median interval and a 26.26 ms P95. During opening, DIB allocations grew from 2 to 11; expansion at elapsed 10.704 s coincided with a 37.439 ms presentation interval. This is a correlation, not a complete attribution of rendering cost.

The native host now reserves the canonical canvas backing on the first frame. `UpdateLayeredWindow` still receives the current alpha crop width and height, so this allocation change does not enlarge the visible window or its input region. The following packaged validation must confirm a constant allocation count through opening and explosion.

Godot reads a complete 1920×1400 RGBA frame asynchronously, then scans alpha, copies the crop and sends it over loopback TCP. Native keeps only the most recent pending frame, converts it to premultiplied BGRA and presents it. This avoids a growing native playback queue, but it does not eliminate readback or transport latency. No claim of zero input latency or locked 60 FPS is made.

The new VFX remain real scene geometry, materials and 3D density rendering. The native host receives rendered RGBA; it does not substitute a pre-rendered movie for the interactive model.
