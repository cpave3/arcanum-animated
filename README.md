# Animation collection

Transparent WebM effects for Foundry/Sequencer: 33 effects: eleven loops and twenty-two one-shots, each available in 11 damage palettes (the three physical types share `melee`), four original colorways, and two thematic palettes, `divine` and `eldritch`:

- `fireball-projectile`: centered right-facing orb with a tail to the left; move and rotate the square sprite externally, without stretching (384×384 VTT, 30 fps, 2-second loop).
- `fireball-embers`: scorched fissures, pulsing hot coals, and drifting sparks (384×384 VTT, 30 fps, 4-second loop).
- `miasma-pool`: irregular dark floor pools with slow billowing smoke from multiple vents (384×384 VTT, 24 fps, 4-second loop).
- `rift`: neon tear with a dark shimmering interior (384×384 VTT, 24 fps).
- `vortex`: tear with layered outward spirals (384×384 VTT, 30 fps).
- `vortex-open`: the same outward spirals without a central object; transparent opening (384×384 VTT, 30 fps).
- `vortex-black-hole`: outward spirals around a perfectly circular dark core with subtle shimmer, a bright photon ring, and orbiting arcs (384×384 VTT, 30 fps).
- `rift-edge-anchor-left`: native left-hand force brace with `spire`, `eye`, and `branch` runes, three stationary power orbs and three small moving rim contacts (256×256 VTT, 30 fps; Radiant default).
- `rift-edge-anchor-right`: native right-hand force brace with `gate`, `hourglass`, and `fork` runes, fitted to the opposite bank (256×256 VTT, 30 fps; Radiant default).
- `orb-anchor`: glowing orb, lightning, and sparks (256×256 VTT, 30 fps).
- `rune-anchor`: vertical runes, side brackets, and sparks (256×256 VTT, 30 fps).

Loops last 3 seconds, except the 2-second fireball projectile and 4-second miasma pool and fireball embers. One-shots use 384×384 VTT at 30 fps and last 2 seconds except Celestial Revelation (5 seconds), Turn Undead (4 seconds) and the fireball and paired-ray clips below.

| One-shot ID | Motion | Cue time at 1× |
| --- | --- | --- |
| `ray-cast-1` | Caster-only charge and one release pulse (36 frames, 1.2 s) | Frame 12: release |
| `ray-cast-2` | Caster-only charge and two release pulses (46 frames, ≈1.5333 s) | Frames 12, 22: releases |
| `ray-cast-3` | Caster-only charge and three release pulses (56 frames, ≈1.8667 s) | Frames 12, 22, 32: releases |
| `ray-beam` | Standalone full-width left-to-right beam (9 frames, 0.3 s) | Frame 4: arrival |
| `ray-hit` | Centered impact only; blank frame 0 (40 frames, ≈1.3333 s) | Frame 1: impact |
| `celestial-revelation` | Caster-centered light fades into a pool, spirals inward to a bright core, then bursts outward and dissolves (150 frames, 5 s) | 2.70 s: revelation burst |
| `turn-undead` | Glyphs assemble one by one, spin to charge, then fly outward intact with searing radiant echoes (120 frames, 4 s) | 1.80 s: release |
| `fireball` | Left-to-center bolt, top-down blast, then scorched ground cools to empty (209 frames, ≈6.97 s) | 0.47 s: impact |
| `fireball-stylized` | Graphic flame variant: rounded lobes, bold hot-color bands, and cinders; same flight, impact timing, and fading ground (≈6.97 s) | 0.47 s: impact |
| `fireball-opening` | Same impact settles into burning ground (120 frames, 4 s) | 0.47 s: impact; handoff at 4 s |
| `fireball-detonation` | Centered explosion only; blank frame 0, then the original impact settles into embers (107 frames, ≈3.57 s) | Frame 1: impact; frame 106 matches embers frame 0 |
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

One-shots do not wrap frames. All finish fully transparent **except sequence openings: `portal-open`, `vortex-opening`, `fireball-opening`, and `fireball-detonation`**. Their final source frames exactly match their respective loops’ frame 0 (`rift`, `vortex`, or `fireball-embers`) in every palette. The corresponding closing clips start on those same frames; switch from the loop at its cycle boundary. Lossy WebM compression can introduce small pixel differences between clips. Arrival and departure are independently animated, not reversed copies. Cue times refer to the effect starting, and scale with playback speed. These assets do not move tokens automatically.

Original colors: `purple`, `gold`, `red`, `orange`.

Thematic palettes: `divine` combines blue shadows, warm gold, and icy white highlights; it is the default for Turn Undead and Celestial Revelation. `eldritch` runs from dark violet through purple and magenta to saturated red highlights. Both preserve source brightness and alpha. Neither is a damage type.

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

These are artistic assignments, not official D&D color definitions. Damage palettes apply to every registered effect, including future effects. A full export produces 561 WebM/PNG pairs (33 effects × 17 palettes/colorways). Three compositions, four sequences, and one journey reference these clips; they add no exported effects or pairs.

## Preview

```sh
python3 serve.py
```

Open http://localhost:8000. Use `--port 8001` if needed. `serve.py` supports byte-range requests for reliable WebM seeking; the plain `python -m http.server` server does not provide this behavior. The server serves this directory regardless of your current working directory. Refresh the page after HTML or catalog changes; no server restart is needed for those changes.

The viewer reads `assets/catalog.json` into a searchable library with **Loops**, **One-shots**, **Composed**, **Sequences**, and **Journeys** filters. Library thumbnails are static PNGs, not playing videos. Select an entry to inspect it on one focused stage, initially over a battle grid. Background, effect size, and playback speed are configurable.

- Nothing plays automatically when you select an entry or change its palette. Press **Play** for a single clip or composition, or **Start** for a sequence or journey.
- Loops repeat; one-shots play once and hold their final frame. **Replay** plays a finished one-shot again, and **Restart** starts the selected entry from the beginning.
- **Pause/Resume** controls the active preview. **Stop** resets a single clip or composition to its poster. Seek is available for single clips and compositions and pauses on the chosen frame; sequences and journeys cannot be scrubbed.
- Palette choices are remembered independently per library entry during the current page session. Changing palette resets the preview without starting playback. Color is baked into the WebM, not applied with a browser filter.
- Optional left and right overlays have independent enable toggles, asset selectors, palettes, and mirror toggles; the old shared asset/palette selectors are removed. Native handed anchors need no automatic mirroring. Each side’s WebM and PNG downloads match its selected asset and palette. They accompany the focused preview rather than running separate gallery previews.
- Every WebM and PNG download matches its selected palette. A sequence exposes downloads for all three clips—opening, loop, and closing—plus their PNGs, and lets you copy all three asset paths.

### GitHub Pages

The workflow in `.github/workflows/pages.yml` publishes the static preview on pushes to `main`, or manually from **Actions → Deploy preview to GitHub Pages → Run workflow**.

1. Push this repository to GitHub, including `assets/` and its `catalog.json`.
2. In **Settings → Pages → Build and deployment**, select **GitHub Actions** as the source.
3. Run the workflow (or push another commit to `main`). The deployment URL appears in the workflow's `github-pages` environment, normally `https://<owner>.github.io/<repository>/`.

Only `index.html`, `viewer.css`, `viewer/`, and `assets/` are published. No Python server, build, or animation rendering runs on GitHub. After adding or changing exports, run `python3 render.py --catalog-only` locally and commit the updated catalog and assets before deploying. The viewer's relative URLs support repository subpaths without configuration. The preview and downloadable media are public on a public Pages site. If your default branch is not `main`, update the workflow's branch trigger.

### Celestial Revelation controls in Foundry

Use [examples/sequencer-celestial-revelation.js](examples/sequencer-celestial-revelation.js) as a **Script** macro with Sequencer enabled.

1. Copy `assets/celestial-revelation/` into your Foundry Data directory (only `divine.webm`, `radiant.webm`, and `necrotic.webm` are required).
2. Set `BASE` in the macro to the folder **containing** `celestial-revelation`, relative to Data, with no leading slash or `Data/` prefix. For example, `worlds/your-world/animations`.
3. Select exactly one token and run the macro. The dialog stays bound to that token even if selection changes. Choose **Divine**, **Radiant**, or **Necrotic**, then **Activate**.
4. **Clear** cancels an unfinished reveal and restores the complete lighting configuration saved before activation. Closing the dialog only dismisses the controls; select the same token and rerun the macro to manage it again.

The five-second animation follows the token and draws above it. `SIZE = 6` is the full sprite width in grid squares, not the light radius. At media time **2.70 seconds**, the macro applies a 360° color-matched light with bright radius **10**, dim radius **0**, and alpha **0.25**. Radii use Foundry scene distance units; this is 10 ft on a feet-based scene. Existing light animation and darkness restrictions are temporarily disabled so the revelation light is visible. Divine uses pale warm gold, Radiant golden yellow, and Necrotic spectral mint; edit `COLORS` to adjust the light tint.

Timing uses Sequencer's `mediaIsPlaying` and `mediaCurrentTime`, not a timeout measured from clicking Activate. Slow loading does not switch the light on early. Network/document propagation and client rendering can still add delay: alignment is **best-effort, not frame-perfect across clients**. If playback fails, ends before its cue, or supplies no usable clock within 20 seconds, the macro reports the problem and attempts to restore the original lighting rather than silently enabling it at an arbitrary time.

The original lighting and active palette are saved in the token's `flags.world.celestialRevelation`. Clear works after reload; an interrupted charge is shown as interrupted and must be cleared before another activation. The light lasts until Clear, with no automatic expiry. Clear restores the saved lighting, including replacing any manual light edits made while the revelation was active. Failed restoration retains the backup for a retry. Scene changes before the cue cancel activation; deleting the token leaves no separate ambient light behind.

Use one controlling GM/client per token: the local dialog lock and serialized writes prevent repeated local clicks and Clear/write races, but separate clients are not a distributed lock. The user needs token-update and Sequencer effect permissions. This is token lighting, not an Active Effect, and does not consume an Aasimar feature use or modify rules data. APIs were checked against Sequencer source; **the macro has not been run in a live Foundry session**.

```sh
node --test tests/test_celestial_macros.js
```

### Rift-edge anchor review

Choose either **Rift edge · Left force brace** (`rift-edge-anchor-left`) or **Rift edge · Right force brace** (`rift-edge-anchor-right`), then **Preview with Vortex**. This selects the original Vortex without autoplay and loads the two corresponding files: the left asset on the left and the right asset on the right. Both entries share the same mount preset: **32% size**, **8.75% spacing**, and both partner IDs. Press **Play** to review the assembly. Each side has its own asset selector, palette, mirror toggle, and enable toggle. Anchor palettes default to **Radiant** and are independent of the Vortex palette.

These are two native orientations, not one asset reused with automatic mirroring. Each brace follows its own asymmetric bank of the actual compact-rift contour. The left uses the new rune set (`spire`, `eye`, `branch`); the right retains the original set (`gate`, `hourglass`, `fork`). Each has three runes, one brace, and three tethers connecting consistent powered joints: each has a **large stationary orb on the brace and a small contact light following that bank’s rim**. There is no dual middle fork or floating duplicate contact. Both sources are 320×320, 30 fps, 90 frames (3-second loops), with 256×256 VTT delivery, gold source artwork, and all 17 palettes. Existing Orb and Rune anchors and the original Vortex artwork remain unchanged.

The singleton `rift-edge-anchor` is removed from the registry. Generate both handed IDs below; old singleton files are not a substitute for either native asset. No automatic mirror is needed for this pair; manual mirror toggles remain available for independent experimentation.

### Rift controls in Foundry/Sequencer

The approved assembly has a standalone **Script** macro: [examples/sequencer-rift-controls.js](examples/sequencer-rift-controls.js).

1. Enable Sequencer. Copy the five complete folders `vortex-opening`, `vortex`, `vortex-closing`, `rift-edge-anchor-left`, and `rift-edge-anchor-right` from `assets/` into your Foundry Data directory. The macro needs the WebMs; PNGs and JSON are optional.
2. Paste the file into a Foundry macro of type **Script**. Set `BASE` to the folder containing those five folders, relative to Data, e.g. `worlds/your-world/animations`. Do not include `Data/` or a leading slash.
3. Set `SIZE` if desired (the full rift canvas width, initially 6 grid squares) and `ANCHOR_PALETTE` (initially `radiant`). Both anchor sizes and offsets scale with the rift.
4. Run the macro. No token selection is required. Its dialog stays open for repeated table controls; closing the dialog does not close the rift or disable its ambient effects.

| Control | Action |
| --- | --- |
| Create rift | Choose one of the 17 rift palettes, then place a free-position crosshair (no grid snapping, so intersections and between-square positions work). Plays the full 2-second swirling opening and starts the persistent 3-second vortex loop. Anchors start OFF. |
| Toggle both | Turns both anchors ON unless both are already ON, in which case it turns both OFF. A mixed state becomes both ON. |
| Toggle left | Changes only the left anchor, without restarting the rift or right anchor. |
| Toggle right | Changes only the right anchor, without restarting the rift or left anchor. |
| Close | Cancels pending creation, removes both anchors and the loop, and plays the 2-second vortex closing at the saved position and size. |

The dialog reports the active palette and left/right state. Palette selection applies to **creation**, not recoloring an existing rift. Close the existing rift before creating another. Close remains available while opening; other conflicting operations are disabled. Assets are preloaded before creation, and the closing asset is loaded before removing a live rift. Finite transition clips explicitly use `.waitUntilFinished()`; the steady loop is not launched while the opening is still playing.

Tag Ambient Lights and Ambient Sounds with the exact Tagger tag **`rift`** (configurable as `AMBIENT_TAG` in the macro). The macro sets `hidden: false` when opening starts and `hidden: true` when closing starts, after any loop-boundary wait. It changes only tagged documents in the scene where the controller was opened; anchor toggles and unrelated tags are unaffected. Normal sound range/volume and light darkness settings still apply. You need permission to update these documents—normally a GM.

Canceled placement and failed preloading do not touch ambient effects. A failed opening restores the ambient values it changed; partial update failures attempt to restore prior values and show an error. If disabling a light/sound fails, the live rift stays available for another Close attempt. Close can also disable leftover tagged effects when no visual rift exists. Close the old control dialog before running a newly pasted macro version, so the old controller is not reused.

The native left/right anchor files are **not mirrored**. Their canvases are 32% of the rift canvas width, with centers offset left/right by 8.75%. Anchors render above the rift, and all three render above tokens. `syncGroup` ties newly enabled anchors to the existing vortex’s 3-second loop clock, without cropping their loops or restarting the rift.

One controlled rift is supported per scene. Persistent effects carry their own palette, paths, point, and pixel geometry; reopening the macro after a reload discovers them. Saved pixel dimensions keep existing anchors aligned if the grid or macro configuration changes. The invisible control marker is intentional—remove the rift through this macro rather than deleting only its visible loop.

Run as a GM, or use a user with Sequencer permission to delete all effects belonging to that rift. Other effect namespaces and scenes are untouched. Use **one GM controller**: cross-client socket operations are not transactional. Reload does not resume an interrupted opening; Close can clean up its saved marker. Scene changes suppress late creation/closing to avoid rendering on the wrong map.

For a playing loop, Close waits up to the remainder of its 3-second cycle before closing. Opening/interrupted effects or unavailable clocks close immediately. This is **best-effort alignment**, not frame-perfect synchronization across clients. Sequencer APIs were checked against source and the macro is covered by mocked execution tests; it has **not been run in a live Foundry session**.

```sh
node --test tests/test_rift_macros.js
```


### Ray components in Foundry/Sequencer

Use one `ray-cast-1`, `ray-cast-2`, or `ray-cast-3` on the caster, a separate `ray-beam` for each release, and `ray-hit` on each target that should show an impact. `fire` is the default for a Scorching Ray look; choose `eldritch` for an Eldritch Blast look. All five components have 640×640 source frames, 384×384 VTT exports, and 30 fps. They start and finish fully transparent in all 17 palettes.

- **Caster:** an accelerating inward vortex charges for 12 frames (0.4 s), followed by centered release pulses only—no baked outgoing beams. The 1/2/3-release clips last 36/46/56 frames, with releases at frames 12, 22, and 32 as applicable.
- **Beam:** a standalone 9-frame clip travels across the full canvas width, from logical `(0, 256)` to `(512, 256)`. Stretch its X axis between caster and target centers while keeping its Y scale fixed. Its arrival cue is local frame 4 (≈0.133333 s). Travel always takes four frames, independent of distance: long distances stretch the pixels, not the travel time.
- **Impact:** a 40-frame centered burst with no incoming beam. Frame 0 is blank; the impact cue is local frame 1 (≈0.033333 s).

At native speed, let `frameMs = 1000 / 30`. Start each beam at `releaseFrame * frameMs` and each hit at `(releaseFrame + 4 - 1) * frameMs`. The hit's frame-1 cue then coincides with the beam's frame-4 arrival. These are absolute delays from the same sequence start, not waits between effects; impact tails must overlap independently. Adjust all timing consistently if changing playback speed.

Pairing is defined in the source registry, `animation_fx/catalog.py`: caster partners are `ray-beam` and `ray-hit` (`Release`, direction `center`); beam partners are all three casters and `ray-hit` (`Arrival`, direction `right`); hit partners are `ray-beam` and all three casters (`Impact`, direction `center`). Exported `effect.json` files include this `pairing` metadata, and `assets/catalog.json` carries it to the viewer. `times` are precise frame/FPS seconds on each component's **local clock**. Use numeric metadata rather than rounded labels for scheduling.

#### Breaking migration from baked rays

Old caster/target exports are incompatible with this component timing and geometry. Re-render **all five effects in all palettes**, then update existing Foundry macros to schedule the separate beam and impact. Reindexing alone does not replace old media.

```sh
python3 render.py --effect ray-cast-1 --color all
python3 render.py --effect ray-cast-2 --color all
python3 render.py --effect ray-cast-3 --color all
python3 render.py --effect ray-beam --color all
python3 render.py --effect ray-hit --color all
```

These are migration instructions, not a claim that exports have been regenerated here. Compositions are preview recipes, not additional exports.

#### Foundry script macro

Copy [examples/sequencer-rays.js](examples/sequencer-rays.js) into a Foundry **Script** macro with Sequencer enabled. Set `BASE` to your uploaded assets directory **relative to Foundry's Data directory**, without a leading slash (for example, `modules/my-animations/assets`). Choose `color` and `beamCount` (1, 2, or 3), select one caster token, and target one or more tokens. The macro uses the target list round-robin. Its per-beam `impactMask` defaults to all hits; set entries to `false` to suppress individual impacts, not their beams.

This is a visual preview: make your own rolls and supply the hit results. There is no attack, save, or roll integration, and no automatic token movement.

The caster and hits use `.scaleToObject(3)`. Beams use `.atLocation(caster).stretchTo(target, { onlyX: true }).scale({ x: 1, y: canvas.grid.size * 3 / 384 })`: fixed three-grid-square height for these VTT files, independent of distance. Do not add `.anchor()`, `.size()`, or `.scaleToObject()` to the beam. Sequencer handles the custom sprite's left-center anchor and rotation for `stretchTo`; there is no need to rotate or mirror the centered endpoint effects. If using 640-pixel high-profile files instead, change the beam scale denominator to 640.

The API behavior was checked against Sequencer's source ([effect section](https://github.com/fantasycalendar/FoundryVTT-Sequencer/blob/master/src/sections/effect.js), [canvas effect](https://github.com/fantasycalendar/FoundryVTT-Sequencer/blob/master/src/canvas-effects/canvas-effect.js)); the macro has **not been run in Foundry**.

#### Composed ray previews

The **Composed** filter contains three non-exported entries: `ray-composition-1`, `ray-composition-2`, and `ray-composition-3`. Each combines a caster track with one independent beam and impact track per release. Impact tails overlap without restarting earlier hits. All tracks share a palette and composition clock while retaining their local clip timing.

Use the **From / To** horizontal and vertical position sliders and **Reset positions** to change the endpoints; the dummy tokens are **not draggable**. The connecting beam rotates and stretches only in length; endpoint effects stay centered and square. Distance changes do not change the four-frame travel time.

Compositions support **Play**, **Pause/Resume**, **Stop**, **Replay**, **Restart**, seek, and playback speed. Selection and palette changes reset without autoplay. Downloads and copied paths refer to the three unique components (caster, beam, impact), not a flattened composition export. Matching-palette partner and composition links let you navigate without starting playback.

Composition browser regression check (fresh page, after migration exports):

```sh
playwright-cli goto http://localhost:8000
playwright-cli eval "$(cat tests/viewer_compositions.js)"
```

This exercises decoded beams and impacts, overlapping tracks, endpoint sliders and Reset, full transport, cancellation, and component downloads. `tests/viewer_paired_rays.js` checks all five components, timing labels, palette downloads, transparent endings, and partner/composition navigation without autoplay:

```sh
playwright-cli goto http://localhost:8000
playwright-cli eval "$(cat tests/viewer_paired_rays.js)"
```

### Fireball journey in the viewer

Select **Journeys → Fireball · Projectile + burning ground** (`fireball-journey`). Set the **From / To** position sliders, **Travel duration** (default 1 second), and **Burn duration** (default 0: manual Close). Start moves a fixed-size square projectile toward To, rotating its right-facing head along the path without stretching. On arrival, detonation plays at To, then embers loop until Close or the optional positive burn duration expires. Burn duration counts only time in the ember phase, not flight or opening.

Close during flight cancels the journey. During the loop, Close waits for the next 4-second boundary; a positive burn duration likewise rounds up to that boundary. Closing lasts 3 seconds at 1×. From/To controls, Pause/Resume, Restart, and playback speed apply to the journey; selecting another entry or palette cancels playback without autoplay. Downloads and copied paths cover all four component clips in the selected palette. A palette is available only when all four have both WebM and PNG files.

The viewer starts detonation’s blank frame 0 at arrival, so the first flash follows 1/30 second later at 1×. The Foundry macro starts opening one frame before arrival to align its frame-1 flash. This is nominal scheduling, **not frame-perfect synchronization**: client scheduling and media decoding can add jitter.

### Fireball script macros in Foundry/Sequencer

1. Enable Sequencer and upload the four folders `fireball-projectile`, `fireball-detonation`, `fireball-embers`, and `fireball-closing` from `assets/` into your Foundry assets directory. Keep the palette filenames and folder structure.
2. Copy [examples/sequencer-fireball.js](examples/sequencer-fireball.js) into a **Script** macro. Set `BASE` to that directory relative to Foundry’s Data directory, without a leading slash (for example, `modules/my-animations/assets`). Set `color`, ground `size`, `projectileSize`, and `speed` as needed.
3. Copy [examples/sequencer-clear-fireballs.js](examples/sequencer-clear-fireballs.js) into a second **Script** macro for Clear. It reads each cast’s stored path, palette, destination, and size; keep the shared namespace unchanged in both macros.
4. Select exactly one caster token, run the cast macro, and choose the destination with the crosshair. Canceling the crosshair creates nothing. These are visual effects only: no rolls, damage, or token movement.

The projectile uses `.moveTowards(point, { rotate: true }).duration(travelMs)`, not `stretchTo`: the sprite moves at fixed size, looping its 60-frame artwork when travel exceeds 2 seconds. Travel time depends on distance and the configured grid-squares-per-second speed. The original `fireball`, `fireball-opening`, and `fireball-stylized` assets remain available and unchanged; this journey is an additional way to use the shared artwork, not a replacement.

Projectile and detonation use `.belowTokens(false)`, so tokens are engulfed by the flight/explosion. Embers and both manual/timed closing use `.belowTokens()`, so tokens stand above the cracked ground. The viewer uses the same ordering around its dummy tokens.

`burnSeconds = 0` leaves embers persistent until manual Clear. A positive value is an optional duration in **seconds of EMBERS only**, after detonation finishes. Clear cancels an active timer, so it cannot play a second closing later. The timeout is local to the casting client: it does not survive reload or resume on another client. Persistent markers and embers do survive reload, so manual Clear still works. Reload during flight/opening does not resume the interrupted cast.

Clear ends **all casts in this namespace in the current scene** that the caller has permission to delete, including other users’ casts when permitted. Use one GM to clear all users’ fireballs, or configure Sequencer’s effect-delete permission; denied casts produce a warning. Other namespaces and scenes are not touched. Clearing during flight cancels later stages without adding ground; clearing opening or embers plays the 3-second closing at the stored destination. Unlike the viewer, manual Clear and timed expiry stop the current phase immediately: mid-loop/opening removal can visibly jump to closing frame 0.

One GM clearing is recommended because cross-client socket operations are not atomic: simultaneous clears can duplicate closing, and a delayed creation can reappear. Repeat Clear for a remaining marker; an orphan without a marker needs manual Effect Manager removal. The APIs were checked against Sequencer source and the mocked Node regression suite; these macros have **not been tested in an actual Foundry session**.

### Chained sequences

The library includes `portal-open → rift → portal-close`, `vortex-opening → vortex → vortex-closing`, `fireball-opening → fireball-embers → fireball-closing`, and `fireball-detonation → fireball-embers → fireball-closing` (`fireball-impact-sequence`). Available palettes are those exported for all three clips.

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
python3 render.py --effect one-shots               # all twenty-one one-shots, all palettes
python3 render.py --effect teleport-arrival --color necrotic
python3 render.py --effect rune-anchor --color red # one asset
python3 render.py --effect rift-edge-anchor-left --color all # native left brace
python3 render.py --effect rift-edge-anchor-right --color all # native right brace
python3 render.py --effect miasma-pool --color necrotic
python3 render.py --effect turn-undead --color divine # sacred caster-centered release
python3 render.py --effect ray-cast-3 --color fire   # three caster bursts
python3 render.py --effect ray-beam --color fire    # independently stretched connecting beam
python3 render.py --effect ray-hit --color eldritch # independent target impact
python3 render.py --effect fireball --color fire    # finite impact and cooling
python3 render.py --effect fireball-projectile --color all
python3 render.py --effect fireball-detonation --color all
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

Outputs: `assets/{effect}/{color}.webm` and matching transparent `.png` stills (representative posters for one-shots). Each export also writes `assets/{effect}/effect.json` with profile, loop status, exported size, source size, FPS, frame count, duration, cue time, and poster time. Metadata cue time is frame-based; portal opening’s final frame is at 59/30 seconds, with loop handoff after the full 2-second clip. Each effect's geometry is rendered once per frame, then mapped into the requested palettes. Encoders write to unique temporary directories; files are published only after all requested colors for that effect encode successfully. After each successful effect export, the CLI atomically rebuilds `catalog.json` in the output folder via `animation_fx/viewer_catalog.py`. It lists registered effects, palettes, sequences, compositions, journeys, delivery metadata, and available variants with relative WebM/PNG filenames, byte sizes, and per-variant versions. Refresh the viewer after rendering; each variant’s manifest version is used in media URLs to pick up replaced files.

In Sequencer, use a path such as `.file("your-upload-folder/rune-anchor/red.webm")`. Place two independent anchor effects over the rift so they can be toggled separately. Use the native left/right files for the handed rift-edge pair without automatic mirroring; the viewer offers separate manual mirror controls. Foundry integration itself has not been tested here.

The root-level WebMs/PNGs are preserved artwork snapshots, not regenerated outputs. The earlier individual `render_*.py` commands have been replaced by `render.py`.

## Composable animation framework

Effects are recipes. Geometry, particle appearance, glyph definitions, and transition accents live in reusable primitives, independent of palette mapping and video export.

| Primitive | Where to refine it | Existing consumers |
| --- | --- | --- |
| Spark head/trail/glint | `animation_fx/primitives/particles.py:draw_spark` | Teleports, impacts, casting, dispel, portal/vortex transitions, all four anchors, all vortex loops, fireball, Turn Undead |
| Burst particle motion | `particles.py:draw_burst` | All one-shot spark releases; no copied per-effect trails |
| Variable rune | `runes.py:GLYPHS` / `draw_rune` | Rune anchor, rift-edge anchor, Casting Release, Dispel, Turn Undead |
| Binding brackets | `runes.py:draw_brackets` | Rune anchor; rift-edge anchor uses one side |
| Charged orb | `orbs.py:orb_layer` | Orb anchor and rift-edge anchor |
| Lightning tether | `lightning.py:draw_tether` | Rift-edge anchor |
| Compact rim geometry | `rift.py:compact_contour` | Compact rift rendering and rift-edge anchor contact placement |
| Ground fractures | `cracks.py:fracture_network` / `draw_cracks` | Ground Eruption and fireball ground; seeded trunks, forks and cross-fractures with progressive reveal |
| Rift styles | `rift.py:render_rift` (`tall` or `compact`) | Rift loop, vortex loop, both portal transition pairs |
| Smoke spiral | `swirl.py:render_swirl` | Vortex, open vortex, black hole, vortex transitions |
| Closing/opening accents | `transitions.py:transition_accents` | Both plain and swirling portals share the flash and finishing sparks |
| Turbulent combustion | `combustion.py:turbulence` / `energy_field` / `flame_cloud` | Fireball projectile, explosion, and hot coals; Turn Undead radiant shells |
| Expanding gas pocket | `gas.py:billow` | Realistic fireball central ignition and staggered secondary explosions |
| Finite beam pulse | `beams.py:draw_beam` | Standalone `ray-beam`; `paired_rays.caster` supplies charge/releases and `paired_rays.impact` supplies the separate target impact |
| Placement/compositing | `geometry.py:scale_layer` / `compose` | Transition recipes; usable by new effects |
| Timeline utilities | `timing.py:progress` / `smooth` | Finite effect recipes |

`Canvas` in `primitives/canvas.py` supplies rings, soft flashes, spirals, rune placement, and shared burst emitters. Its coordinates use a 512-unit square; `Canvas(size=640)` changes output resolution without changing the recipe's relative layout. Lower-level glyph and spark painters also accept a Pillow drawing context plus scale, so existing supersampled artwork can reuse them unchanged.

The rune library currently includes `spire`, `fork`, `eye`, `chalice`, `gate`, `hourglass`, `branch`, and `hook`. Choose a glyph by name, then vary its position, size, rotation, opacity, or fragmentation. Casting and dispel cycle through this same library; dispel separates the glyph strokes rather than replacing them with unrelated triangles. The original rune anchor deliberately selects five named glyphs via `ANCHOR_GLYPHS`; each handed rift-edge anchor selects its own three from the same library.

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

`animation_fx/effects/fireball.py` composes three independent transparent layers: `projectile(frame)` for the fast, round bolt with an incandescent core, `explosion(frame)` for the volumetric blast with a central ignition and six staggered secondary gas pockets (frame relative to detonation), and `ground(phase, growth, energy)` for scorch, fractures, coals, and sparks. The shared `gas.billow` primitive expands locally shaded cloud volumes, transports them outward, and cools them into smoke; texture travels with each pocket rather than waving over a disk. The same revised explosion is used by the finite shot and sequence opening. Shared combustion primitives supply the bolt material; ground reuses the fracture and spark painters. The projectile travels horizontally **from the left edge toward the canvas center**, not upward. At frame 14 (≈0.47 s) it becomes a broad, centered, top-down explosion. Place the canvas center at the intended impact point; `fire` is the default palette for the original four clips and sequence, as well as the new projectile, detonation, impact sequence, and journey.

`projectile_material` supplies both the original moving bolt and the new centered looping orb. `fireball-detonation` never draws a projectile: frame 0 is blank, frames 1–106 match original opening frames 14–119, and its last frame exactly matches embers/closing frame 0 in every palette. The projectile loop keeps its head centered and points right with its tail to the left; external movement and rotation determine its world trajectory.

The finite `fireball` and `fireball-opening` use the same impact timeline. Opening frame 119, embers frame 0, and closing frame 0 are pixel-identical before encoding in every palette. Embers repeat over 120 frames. The finite shot continues with closing frame 1 after opening frame 119, avoiding a duplicated handoff frame: 120 + 90 − 1 = 209 frames. Its first and last frames are fully transparent, as are the opening’s first frame and closing’s last frame. Ground can remain visible without reaching fully opaque alpha.

Other infrastructure:
- `animation_fx/layers.py`: glow compositing and dark-shimmer material.
- `animation_fx/palettes.py`: named colorways, shared HSV mapping, and optional brightness-indexed gradients (used by Divine and Eldritch), preserving alpha and brightness.
- `animation_fx/catalog.py`: effect registration, centralized `SEQUENCES`, `COMPOSITIONS`, and `JOURNEYS`, and public `Effect.render(frame, color)` API.
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
5. Refresh the viewer: the generated catalog adds the library entry without per-effect HTML or JavaScript. Optional `Effect` fields `title`, `description`, `role`, `tags`, and `default_color` control presentation; omitted titles are derived from the effect ID. Use `role='anchor'` for an overlay effect. Use `anchor_side='left'` or `'right'` for a native handed anchor; this field is restricted to anchors. Optional `mount=AnchorMount('vortex', size=32, spacing=8.75, left='rift-edge-anchor-left', right='rift-edge-anchor-right')` adds a catalog-driven preview target, placement preset, and two registered looping anchor partners. Both handed entries share this preset; it does not create another exported asset.

### Add a sequence

Register a `Sequence` in `SEQUENCES` in `animation_fx/catalog.py`, referencing an opening one-shot, a looping effect, and a closing one-shot. Render any missing clips/palettes, or run `python3 render.py --catalog-only` if they are already exported. Refresh the viewer to see the new sequence; no per-sequence HTML or JavaScript is required.

## Tests

```sh
python3 -m unittest discover -s tests -v
```

Tests exercise actual frame rendering for all effect/color pairs, preserve the original artwork snapshots, check animated dark cores and alpha, and invoke the CLI to encode/decode real transparent WebMs, including a one-shot’s transparent endpoints, visible poster, and metadata, plus a VTT-versus-high export size regression. They also verify exact sequence handoffs in every palette, fireball’s left-to-center travel, centered top-down blast, finite endpoints, smooth ember seam, and shared impact/cooling timeline. Fireball component mocks wrap or remove the actual layer functions through `Effect.render`, verifying both calls and visible contributions. Turn Undead tests exercise `Effect.render` for transparent clamped endpoints, centered outward motion, independently timed visible echoes, cue/poster strength, all-palette alpha preservation, and shared-painter contributions. Tests prove primitive reuse by changing one glyph/spark implementation and observing all consuming effects change. Paired-ray tests exercise `Effect.render` for beam-free caster/impact edges, full-width left-to-right beam travel, shared charge/impact painters, beam-only primitive use, and transparent endpoints in all 17 palettes. Real caster, beam, and impact exports are decoded to check alpha and local cues. Catalog tests check composition tracks against exported timing, maximum track-end duration, three-component palette intersection, invalid references, and Divine/Eldritch thematic grouping. FFmpeg and ffprobe must be on PATH.


Targeted rift-edge anchor and catalog checks (without the expensive full collection):

```sh
python3 -m unittest discover -s tests -p test_rift_edge_anchor.py -v
python3 -m unittest discover -s tests -p test_viewer_catalog.py -v
```

Anchor tests exercise both native assets through public rendering in all 17 palettes, preserved alpha, bounded artwork, animation and loop wrapping, three distinct side-specific glyphs, one brace, three tethers, and visible shared rune/orb/lightning/particle contributions. Across all 90 frames, they check a stationary middle power orb and one small moving contact per native bank, exact native-pixel alpha and mirror sampling within one pixel, and contact forward mapping against the actual rim using parent centers 264/376 and scale 0.64. They also verify that the opposite render is not merely a mirrored copy, contour changes move rendered contacts, and original Orb, Rune, and Vortex snapshots remain unchanged. Catalog tests check both delivered partner paths and mount metadata, removal of the old ID, restricted `anchor_side`, and atomic rejection of invalid targets, partner roles/nonloops, and placement ranges.

After rendering both anchors’ palettes, browser review uses the running viewer. The browser checks cover per-side files, palettes, mirror controls, and paired mounting from either anchor:

```sh
playwright-cli goto http://localhost:8000
playwright-cli eval "$(cat tests/viewer_edge_anchor.js)"
```

Targeted fireball journey, catalog, and macro checks (without the expensive full collection):

```sh
python3 -m unittest discover -s tests -p test_fireball_journey.py -v
python3 -m unittest discover -s tests -p test_viewer_catalog.py -v
node --test tests/test_fireball_macros.js
```

Journey tests exercise `Effect.render` for a stationary centered head, left tail, animated periodic seam/wrapping, all-palette alpha, projectile-free detonation, original-impact offsets, exact ground handoffs, visible shared-material contributions, and the unchanged original frame-8 bolt hash. Catalog tests cover four-component palette intersection and atomic rejection of invalid journey references. The 17 Node macro tests use mocked Foundry/Sequencer APIs, not a live Foundry integration.

Fireball journey browser regression (running viewer with all four component exports):

```sh
playwright-cli goto http://localhost:8000
playwright-cli eval "$(cat tests/viewer_fireball_journey.js)"
```

This checks moving decoded pixels, fixed-size rotation, From/To controls, timing, pause/resume, flight cancellation, persistent and timed burns, boundary closing, and all four downloads.

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
