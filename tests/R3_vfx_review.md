# R3 effect review

## Orbit scale and motion

The uploaded R3 reference was used explicitly for the final orbit scale. The effect now uses 10–12 particles on offset ellipses above the core: major radius 2.20–2.48 m, minor radius 0.94–1.20 m, vertical offset 0.28–0.43 m, and 18–28 degree tilt. Particle bodies retain a 0.042–0.056 m diameter, with a 0.17 m red halo. Trails keep 1.12 seconds of actual world-space history. Each particle lasts 8–11.5 seconds and is replenished; closing and disassembly fade them over 0.65 seconds.

`review/core_R3/steady_open.png` and `R3_orbit.mp4` verify the larger span and the visible long arcs. Those captures preceded the final white/red soft-head refinement and the three extra long lightning channels; the final native application captures are the acceptance source for those changes.

## Lightning and physical anchors

The final lightning uses `assets/lightning_beam.png` on depth-tested 3D curved ribbons. Nine channels cover four short primary contacts, two interior branches and three longer discharge paths to the physical high-voltage anodes. The strong reveal/overload state enables the network; settled operation uses intermittent single-channel discharge. The mesh topology is built during setup and remains resident with zero alpha between discharges.

All three anode anchors were found exactly once in the final GLB. Their local target `(0, 0.59, 0)` is the end of the actual `Valve_Anode` metal beam, which is authored at Blender local Z 0.48–0.59. See `core_terminal_endpoints.json` for the closed-pose global coordinates and the source geometry reference.

## Core and transparency

The core uses the authored `assets/core_plasma.png`, sampled in three projections with two slow opposing flows. Dark-red cells remain between the incandescent features. Glow, lightning and trails use ordinary alpha compositing rather than RGB-only additive output. A previous isolated orbit sample on transparent background contained alpha values from 1 to 255, confirming that the Windows RGBA compositor receives nonzero effect coverage.

The independent visual probes are not a native performance benchmark. The final 1920×1400 native application should be checked for frame timing, effect bounds and UI interaction after export.

## Final native acceptance

Reviewed `tests/R3_release_native/native_open.png` and `native_overload.png`, captured by the actual exported EXE. The wide upper elliptical trails span both petal sides; white/red heads remain round and readable. The overload frame shows the long authored branching channels crossing the chamber to the real valve anodes and lower metal contacts. The core retains its faceted geometry and red structure.

All four image borders have maximum alpha 0 in both captures. The overload image has at least a two-pixel strong-alpha margin, and the open image has a five-pixel top margin; no effect is cut by the output bounds. See `tests/R3_release_native/visual_bounds_review.json`.

The main-thread native benchmark reports 2,146 presented frames, average 50.58 FPS, median frame interval 19.24 ms, and 95th percentile 23.45 ms. Production effect files were frozen after this visual review.
