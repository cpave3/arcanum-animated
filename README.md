# Animation collection

Transparent WebM effects for Foundry/Sequencer: seven loops and ten one-shots, each available in 11 damage palettes (the three physical types share `melee`) plus the four original colorways:

- `miasma-pool`: irregular dark floor pools with slow billowing smoke from multiple vents (384×384 VTT, 24 fps, 4-second loop).
- `rift`: neon tear with a dark shimmering interior (384×384 VTT, 24 fps).
- `vortex`: tear with layered outward spirals (384×384 VTT, 30 fps).
- `vortex-open`: the same outward spirals without a central object; transparent opening (384×384 VTT, 30 fps).
- `vortex-black-hole`: outward spirals around a perfectly circular dark core with subtle shimmer, a bright photon ring, and orbiting arcs (384×384 VTT, 30 fps).
- `orb-anchor`: glowing orb, lightning, and sparks (256×256 VTT, 30 fps).
- `rune-anchor`: vertical runes, side brackets, and sparks (256×256 VTT, 30 fps).

Loops last 3 seconds, except the slower 4-second miasma pool. One-shots last 2 seconds (384×384 VTT, 30 fps).

| One-shot ID | Motion | Cue time at 1× |
| --- | --- | --- |
| `teleport-departure` | Spirals gather inward, swell, collapse into a flash, then scatter | 1.00 s: move/hide token |
| `teleport-arrival` | Flash expands into rings and curling wisps | 0.40 s: show token |
| `impact-burst` | Central flash, short traveling sparks, and an expanding shock ring | 0.23 s |
| `ground-eruption` | Top-down branching fissures grow, glow, and vent small energy bursts | 0.83 s |
| `casting-release` | Varied library runes assemble, power gathers, then discharges | 1.10 s |
| `dispel` | Varied rune ward breaks into outward-moving glyph fragments | 0.67 s |
| `portal-open` | A point grows into the existing neon rift | 2.00 s: hand off to `rift` loop |
| `portal-close` | The existing rift contracts into a flash and disappears | 0.00 s: replace `rift` loop |
| `vortex-opening` | Rift opens, then swirl emerges outward from it | 2.00 s: hand off to `vortex` loop |
| `vortex-closing` | Swirl is sucked inward, rift seals, shared closing sparks scatter | 0.00 s: replace `vortex` loop |

One-shots do not wrap frames. All finish fully transparent **except `portal-open` and `vortex-opening`**. Their final source frames match `rift` and `vortex` frame 0, respectively, for geometrically aligned handoffs. `portal-close` and `vortex-closing` start on those matching source frames; switch from the loop at its cycle boundary. Lossy WebM compression can introduce small pixel differences between clips. Arrival and departure are independently animated, not reversed copies. Cue times refer to the effect starting, and scale with playback speed. These assets do not move tokens automatically.

Original colors: `purple`, `gold`, `red`, `orange`.

| Damage palette | Look |
| --- | --- |
| `acid` | Vivid lime with yellow highlights |
| `cold` | Ice blue / cyan |
| `fire` | Orange with hot yellow highlights |
| `force` | Red (same palette as `red`) |
| `lightning` | Pale electric blue |
| `melee` | Muted cool steel for bludgeoning, piercing, and slashing |
| `necrotic` | Spectral green shadows, cyan/mint highlights |
| `poison` | Saturated venom green |
| `psychic` | Pink / rose |
| `radiant` | Gold (same palette as `gold`) |
| `thunder` | Indigo / violet |

These are artistic assignments, not official D&D color definitions. Damage palettes apply to every registered effect, including future effects. There are currently 255 WebMs and matching PNGs.

## Preview

```sh
python3 serve.py
```

Open http://localhost:8000. Use `--port 8001` if needed. `serve.py` supports byte-range requests for reliable WebM seeking; the plain `python -m http.server` server does not provide this behavior. The server serves this directory regardless of your current working directory. Refresh the page after HTML or catalog changes; no server restart is needed for those changes.

The viewer reads `assets/catalog.json` into a searchable library with **Loops**, **One-shots**, and **Sequences** filters. Library thumbnails are static PNGs, not playing videos. Select an entry to inspect it on one focused stage, initially over a battle grid. Background, effect size, and playback speed are configurable.

- Nothing plays automatically when you select an entry or change its palette. Press **Play** for a single clip or **Start** for a sequence.
- Loops repeat; one-shots play once and hold their final frame. **Replay** plays a finished one-shot again, and **Restart** starts the selected entry from the beginning.
- **Pause/Resume** controls the active preview. **Stop** resets a single clip to its poster. Seek is available for single clips only and pauses on the chosen frame; sequences cannot be scrubbed.
- Palette choices are remembered independently per library entry during the current page session. Changing palette resets the preview without starting playback. Color is baked into the WebM, not applied with a browser filter.
- Optional left and right overlays can be toggled independently and share an overlay style and palette; the right overlay is mirrored. Their WebM and PNG downloads are available inside the overlay section. They accompany the focused preview rather than running separate gallery previews.
- Every WebM and PNG download matches its selected palette. A sequence exposes downloads for all three clips—opening, loop, and closing—plus their PNGs, and lets you copy all three asset paths.

### Chained sequences

The library includes `portal-open → rift → portal-close` and `vortex-opening → vortex → vortex-closing`. Available palettes are those exported for all three clips.

- Press **Start** to preload all three clips and begin opening. The steady clip repeats until you request **Close**.
- **Close** during the loop waits for the next loop boundary (up to one 3-second loop at 1×), keeping source frames aligned. An early Close during opening queues closing immediately after opening, without entering the loop. Close during initial loading cancels the start.
- **Pause/Resume** and playback speed apply to the sequence. A queued close waits while paused. **Restart** begins again from opening.
- Selecting another entry or palette resets the preview. After closing, the stage is empty and ready for another Start. Media failures show an error and allow retry.

`index.html`, `viewer.css`, `viewer/app.js`, and `viewer/player.js` provide the catalog-driven library and shared playback workspace. Inactive sequence videos stay in layout at zero opacity rather than `display: none`: Firefox can otherwise skip a rewound WebM straight to its end. They remain paused, non-interactive, and hidden from accessibility until active.

## Generate

Python 3.10+, Pillow, NumPy, and an FFmpeg build with `libvpx-vp9` are required.

```sh
python3 -m pip install -r requirements.txt
python3 render.py                                  # entire collection, VTT profile
python3 render.py --profile high                    # native-resolution exports in assets-high/
python3 render.py --effect one-shots               # all ten one-shots, all palettes
python3 render.py --effect teleport-arrival --color necrotic
python3 render.py --effect rune-anchor --color red # one asset
python3 render.py --effect miasma-pool --color necrotic
python3 render.py --effect vortex-opening --color all
python3 render.py --effect vortex --color all      # one effect, all colors
python3 render.py --effect vortex-black-hole       # circular core + photon ring, all colors
python3 render.py --color necrotic                 # all effects, ghostly green
python3 render.py --output /tmp/my-collection      # alternate output folder
python3 render.py --catalog-only                  # reindex existing exports; no rendering or encoding
```

### Export profiles

`--profile vtt` is the default: VP9 CRF 36, higher compression effort, and antialiased downscaling to at most 384×384 (256×256 for anchors). It writes to `assets/`, which the viewer uses. All original frames, frame rates, durations, cue timings, and alpha are retained. Lower resolution reduces texture memory and decoded pixel work as well as download size; small sparks and wisps are softer when enlarged.

`--profile high` keeps the original 320–640 pixel dimensions at CRF 22 and writes to `assets-high/` by default. Use this for oversized effects or close-up displays. Both profiles render directly from the procedural source, not from a previously compressed WebM. `--output` overrides either destination. A partial-color export cannot mix profiles or timing in the same effect directory: use a separate output folder or regenerate `--color all`. Neither profile changes the source artwork or root-level snapshots.

Measured on the original 210-file collection before adding miasma and vortex transitions: **211.6 MiB → 60.1 MiB (71.6% smaller)**. The largest VTT file is about 733 KiB. Example purple exports:

| Effect | Previous | VTT |
| --- | ---: | ---: |
| Vortex | 2,494 KiB | 582 KiB |
| Rune anchor | 711 KiB | 234 KiB |
| Teleport arrival | 821 KiB | 219 KiB |

In Foundry, specify the effect's intended world/grid size rather than relying on its native pixel dimensions, so switching resolution does not change its footprint.

Outputs: `assets/{effect}/{color}.webm` and matching transparent `.png` stills (representative posters for one-shots). Each export also writes `assets/{effect}/effect.json` with profile, loop status, exported size, source size, FPS, frame count, duration, cue time, and poster time. Metadata cue time is frame-based; portal opening’s final frame is at 59/30 seconds, with loop handoff after the full 2-second clip. Each effect's geometry is rendered once per frame, then mapped into the requested palettes. Encoders write to unique temporary directories; files are published only after all requested colors for that effect encode successfully. After each successful effect export, the CLI atomically rebuilds `catalog.json` in the output folder via `animation_fx/viewer_catalog.py`. It lists registered effects, palettes, sequences, delivery metadata, and available variants with relative WebM/PNG filenames, byte sizes, and per-variant versions. Refresh the viewer after rendering; each variant’s manifest version is used in media URLs to pick up replaced files.

In Sequencer, use a path such as `.file("your-upload-folder/rune-anchor/red.webm")`. Place two independent anchor effects over the rift so they can be toggled separately. The viewer mirrors the right anchor. Foundry integration itself has not been tested here.

The root-level WebMs/PNGs are preserved artwork snapshots, not regenerated outputs. The earlier individual `render_*.py` commands have been replaced by `render.py`.

## Composable animation framework

Effects are recipes. Geometry, particle appearance, glyph definitions, and transition accents live in reusable primitives, independent of palette mapping and video export.

| Primitive | Where to refine it | Existing consumers |
| --- | --- | --- |
| Spark head/trail/glint | `animation_fx/primitives/particles.py:draw_spark` | Teleports, impacts, casting, dispel, portal/vortex transitions, both anchors, all vortex loops |
| Burst particle motion | `particles.py:draw_burst` | All one-shot spark releases; no copied per-effect trails |
| Variable rune | `runes.py:GLYPHS` / `draw_rune` | Rune anchor, Casting Release, Dispel |
| Binding brackets | `runes.py:draw_brackets` | Rune anchor |
| Ground fractures | `cracks.py:fracture_network` / `draw_cracks` | Ground Eruption; seeded trunks, forks and cross-fractures with progressive reveal |
| Rift styles | `rift.py:render_rift` (`tall` or `compact`) | Rift loop, vortex loop, both portal transition pairs |
| Smoke spiral | `swirl.py:render_swirl` | Vortex, open vortex, black hole, vortex transitions |
| Closing/opening accents | `transitions.py:transition_accents` | Both plain and swirling portals share the flash and finishing sparks |
| Placement/compositing | `geometry.py:scale_layer` / `compose` | Transition recipes; usable by new effects |
| Timeline utilities | `timing.py:progress` / `smooth` | Finite effect recipes |

`Canvas` in `primitives/canvas.py` supplies rings, soft flashes, spirals, rune placement, and shared burst emitters. Its coordinates use a 512-unit square; `Canvas(size=640)` changes output resolution without changing the recipe's relative layout. Lower-level glyph and spark painters also accept a Pillow drawing context plus scale, so existing supersampled artwork can reuse them unchanged.

The rune library currently includes `spire`, `fork`, `eye`, `chalice`, `gate`, `hourglass`, `branch`, and `hook`. Choose a glyph by name, then vary its position, size, rotation, opacity, or fragmentation. Casting and dispel cycle through this same library; dispel separates the glyph strokes rather than replacing them with unrelated triangles. The anchor deliberately selects five named glyphs via `ANCHOR_GLYPHS`.

```python
from animation_fx.primitives.canvas import Canvas
from animation_fx.primitives.timing import progress, smooth


def render_seal(frame):
    t = progress(frame, frames=60)
    ink = Canvas(size=512)
    ink.ring(100, opacity=1-t)
    ink.rune('eye', (256, 256), size=3, rotation=t, opacity=1-t)
    ink.sparks(t, radius=180)
    return ink.finish(smooth(t/.08) * (1-smooth((t-.8)/.2)))
```

Register a callable recipe in `animation_fx/catalog.py`:

```python
from animation_fx.recipe import FrameRecipe

# Inside EFFECTS, with render_seal imported from its effect module:
'seal': Effect(FrameRecipe(render_seal, SIZE=512, FPS=30, FRAMES=60),
               'purple', loop=False, cue_frame=20, poster_frame=20),
```

The existing rift-centered vortex is simply a shared swirl passed as the background to `render_rift(frame, 'compact', background=render_swirl(frame))`. Both portal pairs use `render_transition(...)`; enabling `with_swirl=True` adds the swirl stages without duplicating closing accents.

Other infrastructure:
- `animation_fx/layers.py`: glow compositing and dark-shimmer material.
- `animation_fx/palettes.py`: named colorways and shared HSV mapping.
- `animation_fx/catalog.py`: effect registration, centralized `SEQUENCES`, and public `Effect.render(frame, color)` API.
- `animation_fx/viewer_catalog.py`: generated viewer manifest from registries and completed exports.
- `animation_fx/recipe.py`: callable frame recipes with size/timing metadata.
- `animation_fx/export.py` / `profiles.py`: transparent export and VTT/high delivery settings.
- `render.py`: collection CLI.

After refining a primitive, rebuild its consumers (or run `python3 render.py` for everything). For registry or presentation changes that do not require new artwork, run `python3 render.py --catalog-only` to reindex existing exports without rendering or encoding, then refresh the page. Use `--output` or `--profile high` to reindex another output folder. The generator remains offline: changing Python code alone does not change already exported WebMs.

### Add a color

Add a `Palette(hue_in_degrees)` entry to `PALETTES` in `animation_fx/palettes.py`, then generate with `--color your-name`. The generated catalog supplies palette options to the viewer; no HTML edit is needed. Source-to-target hue offsets preserve color variation within the master artwork. Optional `highlight_hue` introduces a brightness-dependent second color; `saturation_scale` mutes the palette without brightening dark cores. All registered effects automatically support every palette through the CLI.

### Add an effect

1. Add a module under `animation_fx/effects/` with `SIZE`, `FPS`, `FRAMES`, and `render(frame)` returning a square Pillow `RGBA` image.
2. Use deterministic particles and integer temporal harmonics for smooth loops. Keep the exterior alpha zero and glow partially transparent; do not bake a background into frames.
3. Register it in `EFFECTS` with its master palette name. For one-shots set `loop=False`, `cue_frame`, and a visible `poster_frame`. `Effect.render` wraps loop frames but clamps one-shot frames, then maps colors; the exporter handles video, metadata, and still generation.
4. Generate with `python3 render.py --effect your-effect --color all`.
5. Refresh the viewer: the generated catalog adds the library entry without per-effect HTML or JavaScript. Optional `Effect` fields `title`, `description`, `role`, `tags`, and `default_color` control presentation; omitted titles are derived from the effect ID. Use `role='anchor'` for an overlay effect.

### Add a sequence

Register a `Sequence` in `SEQUENCES` in `animation_fx/catalog.py`, referencing an opening one-shot, a looping effect, and a closing one-shot. Render any missing clips/palettes, or run `python3 render.py --catalog-only` if they are already exported. Refresh the viewer to see the new sequence; no per-sequence HTML or JavaScript is required.

## Tests

```sh
python3 -m unittest discover -s tests -v
```

Tests exercise actual frame rendering for all effect/color pairs, preserve the original artwork snapshots, check animated dark cores and alpha, and invoke the CLI to encode/decode real transparent WebMs, including a one-shot’s transparent endpoints, visible poster, and metadata, plus a VTT-versus-high export size regression. They also verify loop handoffs and prove primitive reuse by changing one glyph/spark implementation and observing all consuming effects change. FFmpeg and ffprobe must be on PATH.


Optional browser regression checks (require Playwright CLI and a running viewer; use a fresh page for each):

```sh
playwright-cli goto http://localhost:8000
playwright-cli eval "$(cat tests/viewer_library.js)"
```

The library check covers catalog-driven browsing, search/filtering, selection, and palette/download behavior.

One-shot regression check:

```sh
playwright-cli goto http://localhost:8000
playwright-cli eval "$(cat tests/viewer_one_shots.js)"
```

This checks focused one-shot playback, idle posters, Replay, decoded final-frame alpha, pause/resume, palette/download consistency, and overlays. The viewer explicitly seeks to the final presentation frame after playback ends so dropped frames under load cannot leave an earlier afterimage on screen.


Sequence browser regression check (fresh page):

```sh
playwright-cli goto http://localhost:8000
playwright-cli eval "$(cat tests/viewer_sequences.js)"
```

This exercises both real chains through multiple loop iterations, boundary-aligned Close, early Close, pause/resume, loading cancellation, and reuse after completion.


Visible-frame regression check (also run with a short or narrow viewport):

```sh
playwright-cli goto http://localhost:8000
playwright-cli eval "$(cat tests/viewer_sequence_frames.js)"
```

This checks decoded, changing pixels during both opening and closing, plus actual on-screen video bounds—not just playback phase labels.


Run the same sequence checks in Firefox as well as Chromium:

```sh
playwright-cli --session=firefox-sequence open --browser=firefox
playwright-cli --session=firefox-sequence goto http://localhost:8000
playwright-cli --session=firefox-sequence eval "$(cat tests/viewer_sequence_frames.js)"
playwright-cli --session=firefox-sequence goto http://localhost:8000
playwright-cli --session=firefox-sequence eval "$(cat tests/viewer_sequences.js)"
```
