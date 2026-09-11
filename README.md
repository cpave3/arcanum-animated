# Animation collection

Transparent WebM effects for Foundry/Sequencer: eight loops and nineteen one-shots, each available in 11 damage palettes (the three physical types share `melee`), four original colorways, and two thematic palettes, `divine` and `eldritch`:

- `fireball-embers`: scorched fissures, pulsing hot coals, and drifting sparks (384×384 VTT, 30 fps, 4-second loop).
- `miasma-pool`: irregular dark floor pools with slow billowing smoke from multiple vents (384×384 VTT, 24 fps, 4-second loop).
- `rift`: neon tear with a dark shimmering interior (384×384 VTT, 24 fps).
- `vortex`: tear with layered outward spirals (384×384 VTT, 30 fps).
- `vortex-open`: the same outward spirals without a central object; transparent opening (384×384 VTT, 30 fps).
- `vortex-black-hole`: outward spirals around a perfectly circular dark core with subtle shimmer, a bright photon ring, and orbiting arcs (384×384 VTT, 30 fps).
- `orb-anchor`: glowing orb, lightning, and sparks (256×256 VTT, 30 fps).
- `rune-anchor`: vertical runes, side brackets, and sparks (256×256 VTT, 30 fps).

Loops last 3 seconds, except the 4-second miasma pool and fireball embers. One-shots use 384×384 VTT at 30 fps and last 2 seconds except Turn Undead (4 seconds) and the fireball and paired-ray clips below.

| One-shot ID | Motion | Cue time at 1× |
| --- | --- | --- |
| `ray-cast-1` | Caster charge, then one rightward beam (36 frames, 1.2 s) | 0.4 s: release |
| `ray-cast-2` | Same charge, then two rightward bursts (46 frames, ≈1.5333 s) | 0.4, ≈0.733333 s: releases |
| `ray-cast-3` | Same charge, then three rightward bursts (56 frames, ≈1.8667 s) | 0.4, ≈0.733333, ≈1.066667 s: releases |
| `ray-hit` | Matching left-entry beam and centered impact (42 frames, 1.4 s) | 4/30 s (≈0.133333 s): impact |
| `turn-undead` | Glyphs assemble one by one, spin to charge, then fly outward intact with searing radiant echoes (120 frames, 4 s) | 1.80 s: release |
| `fireball` | Left-to-center bolt, top-down blast, then scorched ground cools to empty (209 frames, ≈6.97 s) | 0.47 s: impact |
| `fireball-stylized` | Graphic flame variant: rounded lobes, bold hot-color bands, and cinders; same flight, impact timing, and fading ground (≈6.97 s) | 0.47 s: impact |
| `fireball-opening` | Same impact settles into burning ground (120 frames, 4 s) | 0.47 s: impact; handoff at 4 s |
| `fireball-closing` | Burning ground cools and scorch fades (90 frames, 3 s) | 0.00 s: replace `fireball-embers` loop |
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

One-shots do not wrap frames. All finish fully transparent **except sequence openings: `portal-open`, `vortex-opening`, and `fireball-opening`**. Their final source frames exactly match `rift`, `vortex`, and `fireball-embers` frame 0, respectively, in every palette. The corresponding closing clips start on those same frames; switch from the loop at its cycle boundary. Lossy WebM compression can introduce small pixel differences between clips. Arrival and departure are independently animated, not reversed copies. Cue times refer to the effect starting, and scale with playback speed. These assets do not move tokens automatically.

Original colors: `purple`, `gold`, `red`, `orange`.

Thematic palettes: `divine` combines blue shadows, warm gold, and icy white highlights; it is the default for Turn Undead. `eldritch` runs from dark violet through purple and magenta to saturated red highlights. Both preserve source brightness and alpha. Neither is a damage type.

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

These are artistic assignments, not official D&D color definitions. Damage palettes apply to every registered effect, including future effects. A full export produces 459 WebM/PNG pairs (27 effects × 17 palettes/colorways).

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

### Paired rays in Foundry/Sequencer

Use `ray-cast-1`, `ray-cast-2`, or `ray-cast-3` on the caster and `ray-hit` on each desired target. `fire` is their default for a Scorching Ray look; choose `eldritch` for an Eldritch Blast look. All four start and finish fully transparent in all 17 palettes.

- The caster draws an accelerating, twisting inward vortex into a bright core over 0.4 s, then releases at local frames 12, 22, and 32 as applicable: 0.4 s, ≈0.733333 s, and ≈1.066667 s. Clip durations are 1.2 s, ≈1.5333 s, and ≈1.8667 s respectively. Each pulse fades out before the next burst. The outgoing and incoming beam edges feather to full transparency at the frame border, including their glow. Caster beams also feather in beneath the orb rather than starting with a flat cut.
- The target clip lasts 1.4 s. A matching beam enters from the **left**, reaching a centered impact at local frame 4: 4/30 s (≈0.133333 s).
- Center each canvas on its token. Rotate both halves by the **same** caster-to-target heading: the caster emits rightward and the target receives from the left. Do not mirror the target half. All bursts in a multi-ray caster clip have the same baked heading; for independently aimed rays, repeat `ray-cast-1` with separate rotations.
- Schedule `ray-hit` externally only for each desired roll result (a hit or failed save, according to your workflow). These assets do not roll attacks, select targets, resolve misses, or automatically trigger hits. Starting a target clip at a caster release places its impact 4/30 s later; to schedule an impact at a chosen time, start the target clip 4/30 s before it. Adjust timing for playback speed.

Each paired export's `effect.json` includes `pairing`: `effects` lists partner IDs, `event` is `Release` or `Impact`, `times` contains precise frame/FPS seconds on that clip's **local clock**, and `direction` is `right` or `from-left`. Caster partners are `['ray-hit']`; the target partners are `['ray-cast-1', 'ray-cast-2', 'ray-cast-3']`. Use the numeric metadata, not rounded labels, for scheduling. `catalog.json` carries the exported pairing metadata through to the viewer.

The viewer offers matching-palette partner links when that palette is available on the partner. Each half retains independent playback: following a link does not start or automatically synchronize the clips. Foundry/Sequencer scheduling remains external and has not been tested here.

Paired-ray browser regression check (fresh page):

```sh
playwright-cli goto http://localhost:8000
playwright-cli eval "$(cat tests/viewer_paired_rays.js)"
```

This checks decoded 1/2/3-burst playback, feathered edges, left-entry impact, and matching-palette partner navigation without autoplay.

### Chained sequences

The library includes `portal-open → rift → portal-close`, `vortex-opening → vortex → vortex-closing`, and `fireball-opening → fireball-embers → fireball-closing`. Available palettes are those exported for all three clips.

- Press **Start** to preload all three clips and begin opening. The steady clip repeats until you request **Close**.
- **Close** during the loop waits for the next loop boundary (up to one loop at 1×: 3 seconds for portals, 4 seconds for fireball), keeping source frames aligned. An early Close during opening queues closing immediately after opening, without entering the loop. Close during initial loading cancels the start.
- **Pause/Resume** and playback speed apply to the sequence. A queued close waits while paused. **Restart** begins again from opening.
- Selecting another entry or palette resets the preview. After closing, the stage is empty and ready for another Start. Media failures show an error and allow retry.

`index.html`, `viewer.css`, `viewer/app.js`, and `viewer/player.js` provide the catalog-driven library and shared playback workspace. Inactive sequence videos stay in layout at zero opacity rather than `display: none`: Firefox can otherwise skip a rewound WebM straight to its end. They remain paused, non-interactive, and hidden from accessibility until active.

## Generate

Python 3.10+, Pillow, NumPy, and an FFmpeg build with `libvpx-vp9` are required.

```sh
python3 -m pip install -r requirements.txt
python3 render.py                                  # entire collection, VTT profile
python3 render.py --profile high                    # native-resolution exports in assets-high/
python3 render.py --effect one-shots               # all nineteen one-shots, all palettes
python3 render.py --effect teleport-arrival --color necrotic
python3 render.py --effect rune-anchor --color red # one asset
python3 render.py --effect miasma-pool --color necrotic
python3 render.py --effect turn-undead --color divine # sacred caster-centered release
python3 render.py --effect ray-cast-3 --color fire   # three caster bursts
python3 render.py --effect ray-hit --color eldritch # independent target impact
python3 render.py --effect fireball --color fire    # finite impact and cooling
python3 render.py --effect fireball-opening --color all
python3 render.py --effect fireball-embers --color all
python3 render.py --effect fireball-closing --color all
python3 render.py --effect vortex-opening --color all
python3 render.py --effect vortex --color all      # one effect, all colors
python3 render.py --effect vortex-black-hole       # circular core + photon ring, all colors
python3 render.py --color necrotic                 # all effects, ghostly green
python3 render.py --output /tmp/my-collection      # alternate output folder
python3 render.py --catalog-only                  # reindex existing exports; no rendering or encoding
```

`render.py` reports the current effect, frame count, percentage, elapsed time, and estimated remaining frame time on stderr. It uses an updating line in terminals and throttled newline updates in logs. Encoding and file publication are separate phases; **complete** means the files have been published, not merely that the last frame was submitted.

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
| Spark head/trail/glint | `animation_fx/primitives/particles.py:draw_spark` | Teleports, impacts, casting, dispel, portal/vortex transitions, both anchors, all vortex loops, fireball, Turn Undead |
| Burst particle motion | `particles.py:draw_burst` | All one-shot spark releases; no copied per-effect trails |
| Variable rune | `runes.py:GLYPHS` / `draw_rune` | Rune anchor, Casting Release, Dispel, Turn Undead |
| Binding brackets | `runes.py:draw_brackets` | Rune anchor |
| Ground fractures | `cracks.py:fracture_network` / `draw_cracks` | Ground Eruption and fireball ground; seeded trunks, forks and cross-fractures with progressive reveal |
| Rift styles | `rift.py:render_rift` (`tall` or `compact`) | Rift loop, vortex loop, both portal transition pairs |
| Smoke spiral | `swirl.py:render_swirl` | Vortex, open vortex, black hole, vortex transitions |
| Closing/opening accents | `transitions.py:transition_accents` | Both plain and swirling portals share the flash and finishing sparks |
| Turbulent combustion | `combustion.py:turbulence` / `energy_field` / `flame_cloud` | Fireball projectile, explosion, and hot coals; Turn Undead radiant shells |
| Expanding gas pocket | `gas.py:billow` | Realistic fireball central ignition and staggered secondary explosions |
| Finite beam pulse | `beams.py:draw_beam` | All three count-parameterized caster recipes and the target incoming beam; `paired_rays.impact` supplies the separate target impact |
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

### Turn Undead composition

`animation_fx/effects/turn_undead.py` renders a 640×640, 30 fps, 4-second one-shot centered on the caster. Each glyph begins fading in and spiraling into the rotating ring four frames after the previous one, taking eight frames to settle. All eight are assembled at frame 36 (1.20 s); the completed ring accelerates for another 0.60 s before releasing a central flash at frame 54 (1.80 s). The intact glyphs launch radially along their release directions and fade in flight, without fragmentation. Three independently timed radiant echoes start at frames 54, 61, and 69 through one parameterized `radiant_echo` renderer. Thin luminous shells and fluted coronas use shared turbulence and energy fields, not flame clouds. Canvas flashes, rings, rays, intact flying runes, and traveling sparks dissolve to full transparency, with no projectile or scorch. The poster is frame 78 (2.60 s), when all three echoes are visible. The purple master supports all 17 palettes; `divine` is the catalog default. Place the canvas center on the caster.

### Stylized fireball comparison

Select **Fireball · Stylized** (`fireball-stylized`) to compare a more abstract, animated flame treatment with the original **Fireball**. Both use the same 209-frame timeline and ground/cooling layers. The variant replaces only the independent bolt and explosion components with `stylized_flames.flame_mass`: merged rounded lobes, broad color bands, rolling hot patches, and ejected cinders instead of shaded expanding gas pockets and cooling smoke. It is a separate one-shot in all 17 palettes; its separate flame components do not alter the realistic clips or sequence.

```sh
python3 render.py --effect fireball-stylized --color all
```

### Fireball components and orientation

`animation_fx/effects/fireball.py` composes three independent transparent layers: `projectile(frame)` for the fast, round bolt with an incandescent core, `explosion(frame)` for the volumetric blast with a central ignition and six staggered secondary gas pockets (frame relative to detonation), and `ground(phase, growth, energy)` for scorch, fractures, coals, and sparks. The shared `gas.billow` primitive expands locally shaded cloud volumes, transports them outward, and cools them into smoke; texture travels with each pocket rather than waving over a disk. The same revised explosion is used by the finite shot and sequence opening. Shared combustion primitives supply the bolt material; ground reuses the fracture and spark painters. The projectile travels horizontally **from the left edge toward the canvas center**, not upward. At frame 14 (≈0.47 s) it becomes a broad, centered, top-down explosion. Place the canvas center at the intended impact point; `fire` is the default palette for all four clips and the sequence.

The finite `fireball` and `fireball-opening` use the same impact timeline. Opening frame 119, embers frame 0, and closing frame 0 are pixel-identical before encoding in every palette. Embers repeat over 120 frames. The finite shot continues with closing frame 1 after opening frame 119, avoiding a duplicated handoff frame: 120 + 90 − 1 = 209 frames. Its first and last frames are fully transparent, as are the opening’s first frame and closing’s last frame. Ground can remain visible without reaching fully opaque alpha.

Other infrastructure:
- `animation_fx/layers.py`: glow compositing and dark-shimmer material.
- `animation_fx/palettes.py`: named colorways, shared HSV mapping, and optional brightness-indexed gradients (used by Divine and Eldritch), preserving alpha and brightness.
- `animation_fx/catalog.py`: effect registration, centralized `SEQUENCES`, and public `Effect.render(frame, color)` API.
- `animation_fx/viewer_catalog.py`: generated viewer manifest from registries and completed exports.
- `animation_fx/recipe.py`: callable frame recipes with size/timing metadata.
- `animation_fx/export.py` / `profiles.py`: transparent export and VTT/high delivery settings.
- `render.py`: collection CLI.

After refining a primitive, rebuild its consumers (or run `python3 render.py` for everything). For registry or presentation changes that do not require new artwork, run `python3 render.py --catalog-only` to reindex existing exports without rendering or encoding, then refresh the page. Use `--output` or `--profile high` to reindex another output folder. The generator remains offline: changing Python code alone does not change already exported WebMs.

### Add a color

Add a `Palette(hue_in_degrees)` entry to `PALETTES` in `animation_fx/palettes.py`, then generate with `--color your-name`. The generated catalog supplies palette options to the viewer; no HTML edit is needed. Source-to-target hue offsets preserve color variation within the master artwork. Optional `highlight_hue` introduces a brightness-dependent second color; `saturation_scale` mutes the palette without brightening dark cores. For multi-tone palettes such as Divine and Eldritch, `gradient` supplies brightness-indexed RGB tint stops while preserving source brightness and alpha. The viewer’s themed grouping is declared in `THEMED_COLORS` alongside the original-color grouping in the catalog. All registered effects automatically support every palette through the CLI.

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

Tests exercise actual frame rendering for all effect/color pairs, preserve the original artwork snapshots, check animated dark cores and alpha, and invoke the CLI to encode/decode real transparent WebMs, including a one-shot’s transparent endpoints, visible poster, and metadata, plus a VTT-versus-high export size regression. They also verify exact sequence handoffs in every palette, fireball’s left-to-center travel, centered top-down blast, finite endpoints, smooth ember seam, and shared impact/cooling timeline. Fireball component mocks wrap or remove the actual layer functions through `Effect.render`, verifying both calls and visible contributions. Turn Undead tests exercise `Effect.render` for transparent clamped endpoints, centered outward motion, independently timed visible echoes, cue/poster strength, all-palette alpha preservation, and shared-painter contributions. Tests prove primitive reuse by changing one glyph/spark implementation and observing all consuming effects change. Paired-ray tests count rendered right-edge pulses, check pre-release charge and beam-free gaps, verify left-entry travel and the separate centered impact, and remove the shared beam painter to prove its visible contribution to all four clips. Small real caster/target exports are decoded to check alpha and visible beams; their JSON pairing cues are checked through catalog generation. Catalog tests reject invalid pairing times and missing partner IDs and verify Divine/Eldritch thematic grouping. FFmpeg and ffprobe must be on PATH.


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

This exercises the catalog’s real chains through multiple loop iterations, boundary-aligned Close, early Close, pause/resume, loading cancellation, and reuse after completion.


Fireball browser check (visible bolt, expanding blast, transparent finish, and the sustained ember sequence):

```sh
playwright-cli goto http://localhost:8000
playwright-cli eval "$(cat tests/viewer_fireball.js)"
playwright-cli goto http://localhost:8000
playwright-cli eval "$(cat tests/viewer_fireball_stylized.js)"
```

Turn Undead browser check (Divine default, outward-moving decoded light, clean ending, all palette downloads):

```sh
playwright-cli goto http://localhost:8000
playwright-cli eval "$(cat tests/viewer_turn_undead.js)"
```

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
