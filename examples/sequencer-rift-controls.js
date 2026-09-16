// Standalone Foundry Script macro (top-level await). Scene effects only; one GM controller recommended.
// Source verified at fantasycalendar/FoundryVTT-Sequencer commit
// a2e041c4760cab25eac346d1a025b4ce0ffa3a0d (not integration-tested in Foundry):
// https://github.com/fantasycalendar/FoundryVTT-Sequencer/blob/a2e041c4760cab25eac346d1a025b4ce0ffa3a0d/docs/api/effect.md
// Same revision: src/canvas-effects/canvas-effect.js, src/sections/{effect,section}.js,
// src/modules/{sequencer,sequencer-effect-manager}.js; docs/{crosshair,effect-manager}.md.
// syncGroup shares creationTimestamp; _startEffect/_startLoop seek late persistent joins
// modulo media duration. All three loops are 90f/30fps. No startTime cropping or mirroring.
// mediaCurrentTime is seconds. Close waits the remaining 3s cycle when playing, then
// starts native closing frame 0. This is best-effort, NOT frame-accurate across clients:
// socket/decode delay can jump. Opening/interrupted/unavailable clocks close immediately.
// Marker names carry durable metadata; reload discovers state but cannot resume opening.
// Socket creates/deletes are not transactional across clients: use ONE GM controller.
// Scene changes suppress late stages/closing; orphan socket effects need Effect Manager cleanup.
const BASE = "assets/animations";
const SIZE = 6; // Full canvas width in current grid units, converted once to stored pixels.
const ANCHOR_PALETTE = "radiant";
const PALETTES = ["purple", "gold", "red", "orange", "acid", "cold", "fire", "force", "lightning", "melee", "necrotic", "poison", "psychic", "radiant", "thunder", "eldritch", "divine"];
const NS = "my-animations.rift.v1";
const AMBIENT_TAG = "rift"; // Exact Tagger tag on Ambient Lights and Ambient Sounds.
if (typeof Sequencer === "undefined" || typeof Sequence === "undefined" || !canvas.scene) {
  ui.notifications.error("Rift controls require Sequencer and an active canvas scene.");
  return;
}
if (!Number.isFinite(SIZE) || SIZE <= 0 || !PALETTES.includes(ANCHOR_PALETTE)) {
  ui.notifications.error("Rift controls: configure a positive SIZE and a registered anchor palette.");
  return;
}
const scene = canvas.scene;
const sceneId = scene.id;
const key = Symbol.for(`${NS}.controllers`);
const controllers = globalThis[key] ??= new Map(); // UI lock only; effects remain the authority.
if (controllers.has(sceneId)) {
  controllers.get(sceneId).dialog.render(true);
  return;
}
const manager = Sequencer.EffectManager;
const state = { busy: false, closing: false, epoch: 0, root: null, dismissed: false };
const current = () => canvas.scene?.id === sceneId;
// Serialize document writes so Close cannot be overtaken by an in-flight enable.
let ambientQueue = Promise.resolve();
function ambient(work) {
  const operation = ambientQueue.then(work);
  ambientQueue = operation.then(() => undefined, () => undefined);
  return operation; // The caller still receives and reports any rejection.
}
function taggedAmbient() {
  const tagged = doc => (doc.flags?.tagger?.tags ?? []).includes(AMBIENT_TAG);
  return [...scene.lights.filter(tagged), ...scene.sounds.filter(tagged)];
}
async function restoreAmbient(records) {
  const results = await Promise.allSettled(records.map(({ doc, hidden }) => doc.update({ hidden })));
  const failures = results.filter(result => result.status === "rejected");
  if (failures.length) throw new Error(`Could not restore tagged ambient effects: ${failures.map(r => r.reason?.message || r.reason).join("; ")}`);
}
async function setAmbient(enabled) {
  const changed = [];
  try {
    for (const doc of taggedAmbient()) {
      if (doc.hidden === !enabled) continue;
      const record = { doc, hidden: doc.hidden };
      await doc.update({ hidden: !enabled });
      changed.push(record);
    }
    return changed;
  } catch (error) {
    try { await restoreAmbient(changed); }
    catch (restoreError) { throw new Error(`${error.message || error}; ${restoreError.message}`); }
    throw error;
  }
}
const effects = (prefix = NS) => manager.getEffects({ name: `${prefix}.*`, sceneId })
  .filter(e => e.data.sceneId === sceneId && e.data.name.startsWith(`${prefix}.`));
function discover() {
  const markers = effects().filter(e => e.data.name.includes(".active."));
  if (markers.length > 1) throw new Error("Multiple controlled rifts found; ask a GM to remove duplicates in Effect Manager.");
  if (!markers.length) return null;
  const marker = markers[0];
  const split = marker.data.name.indexOf(".active.");
  const meta = JSON.parse(decodeURIComponent(marker.data.name.slice(split + 8)));
  if (meta.sceneId !== sceneId || !Number.isFinite(meta.width) || meta.width <= 0 ||
      !Number.isFinite(meta.point?.x) || !Number.isFinite(meta.point?.y) ||
      !PALETTES.includes(meta.palette) || !PALETTES.includes(meta.anchorPalette) || typeof meta.base !== "string") {
    throw new Error("Invalid stored rift metadata; ask a GM to remove its marker in Effect Manager.");
  }
  return { marker, meta, prefix: marker.data.name.slice(0, split) };
}
const has = (rift, stage) => effects(rift.prefix).some(e => e.data.name === `${rift.prefix}.${stage}`);
function permitted(list) {
  if (list.some(e => !e.userCanDelete)) throw new Error("Cannot control this rift. Ask a GM or check Sequencer effect-delete permissions.");
}
async function end(list) {
  permitted(list);
  if (list.length) await manager.endEffects({ effects: list.map(e => e.id), sceneId });
}
const report = error => ui.notifications.error(`Rift controls: ${error.message || error}`);
function refresh() {
  if (!state.root) return;
  try {
    const r = discover();
    const left = !!r && has(r, "left"), right = !!r && has(r, "right");
    state.root.querySelector('[data-status]').textContent = !current() ? "Scene changed — reopen the macro." :
      `${state.busy || state.closing ? "Busy · " : ""}${r ? `Rift ${has(r, "loop") ? "open" : "opening/interrupted"} (${r.meta.palette}) · Left ${left ? "ON" : "OFF"} · Right ${right ? "ON" : "OFF"}` : "No rift"}`;
    state.root.querySelector('[data-action="both"]').textContent = `Toggle both — ${left && right ? "turn OFF" : "turn ON"}`;
    const palette = state.root.querySelector('[name="palette"]');
    if (r) palette.value = r.meta.palette;
    palette.disabled = !!r || state.busy || state.closing || !current();
    for (const button of state.root.querySelectorAll('[data-action]')) {
      const name = button.dataset.action;
      button.disabled = !current() || state.closing || (state.busy && name !== "close") ||
        (name === "create" && !!r) || (["both", "left", "right"].includes(name) && (!r || !has(r, "loop"))) ||
        (name === "close" && !r && !state.busy && !taggedAmbient().some(doc => !doc.hidden));
    }
  } catch (error) { report(error); }
}
function visual(r, stage, file, point = r.meta.point, width = r.meta.width, z = 0) {
  return new Sequence().effect().file(`${r.meta.base}/${file}.webm`)
    .name(`${r.prefix}.${stage}`).atLocation(point).size(width).belowTokens(false).zIndex(z);
}
async function finite(sequence, name) {
  let created = false;
  const hook = Hooks.on("createSequencerEffect", effect => { if (effect.data.name === name) created = true; });
  try {
    await sequence.duration(2000).waitUntilFinished().play();
    if (!created) throw new Error("Clip creation failed; check module assets and Sequencer permissions.");
  } finally { Hooks.off("createSequencerEffect", hook); }
}
async function startPersistent(sequence, name) {
  await new Promise((resolve, reject) => {
    const hook = Hooks.on("createSequencerEffect", effect => {
      if (effect.data.name !== name) return;
      cleanup();
      queueMicrotask(resolve); // Hook precedes manager registration.
    });
    const timer = setTimeout(() => { cleanup(); reject(new Error("Effect creation timed out; check assets and Sequencer permissions.")); }, 15000);
    function cleanup() { clearTimeout(timer); Hooks.off("createSequencerEffect", hook); }
    sequence.play().then(() => {
      cleanup(); reject(new Error("Effect was not created; check module asset paths and Sequencer permissions."));
    }, error => { cleanup(); reject(error); });
  });
}
// Guard both serialization and the later registration race, without private APIs.
async function guarded(r, epoch, needsMarker, work, closing = false) {
  const valid = () => current() && epoch === state.epoch &&
    (!needsMarker || effects(r.prefix).some(e => e.data.name === r.marker.data.name));
  const owns = name => name.startsWith(`${r.prefix}.`) && (name === `${r.prefix}.closing`) === closing;
  const pre = Hooks.on("preCreateSequencerEffect", data => {
    if (owns(data.name) && (!valid() || data.sceneId !== sceneId)) return false;
  });
  const create = Hooks.on("createSequencerEffect", effect => {
    if (owns(effect.data.name)) queueMicrotask(() => {
      if (!valid()) void end([effect]).catch(report);
    });
  });
  try { await work(valid); }
  finally { Hooks.off("preCreateSequencerEffect", pre); Hooks.off("createSequencerEffect", create); }
}
async function create(palette, epoch) {
  if (discover()) throw new Error("This scene already has a controlled rift. Close it first.");
  if (!PALETTES.includes(palette)) throw new Error("Choose a registered palette.");
  const point = await Sequencer.Crosshair.show({
    label: { text: "Place rift" },
    snap: { position: 0 }, // No snapping flags: allow any point, including grid intersections.
  });
  if (!point || !current() || epoch !== state.epoch) return;
  if (discover()) throw new Error("A rift was created while placing the crosshair.");
  const prefix = `${NS}.${foundry.utils.randomID()}`;
  const meta = { base: BASE, size: SIZE, gridSize: canvas.grid.size, width: SIZE * canvas.grid.size,
    palette, anchorPalette: ANCHOR_PALETTE, point: { x: point.x, y: point.y }, sceneId };
  const name = `${prefix}.active.${encodeURIComponent(JSON.stringify(meta))}`;
  const r = { prefix, meta, marker: { data: { name } } };
  let ambientBefore = [];
  const restoreFailedOpen = () => epoch === state.epoch && ambientBefore.length
    ? ambient(() => restoreAmbient(ambientBefore)) : Promise.resolve();
  try {
    await Sequencer.Preloader.preload([
      "icons/svg/circle.svg",
      ...["vortex-opening", "vortex", "vortex-closing"].map(kind => `${BASE}/${kind}/${palette}.webm`),
      ...["left", "right"].map(side => `${BASE}/rift-edge-anchor-${side}/${ANCHOR_PALETTE}.webm`),
    ]);
    if (!current() || epoch !== state.epoch) return;
    if (discover()) throw new Error("A rift was created while loading its assets.");
    await guarded(r, epoch, false, async valid => {
      await startPersistent(new Sequence().effect().file("icons/svg/circle.svg").name(name)
        .atLocation(meta.point).size(1).opacity(0).belowTokens(false).persist(), name);
      if (!valid()) return;
      await guarded(r, epoch, true, async alive => {
        ambientBefore = await ambient(() => setAmbient(true));
        if (!alive()) return;
        // Full 60 frames, not a shortened overlap with the loop.
        await finite(visual(r, "opening", `vortex-opening/${palette}`), `${prefix}.opening`);
        if (!alive()) return;
        await startPersistent(visual(r, "loop", `vortex/${palette}`).syncGroup(prefix).persist(), `${prefix}.loop`);
      });
    });
    if (!current() || epoch !== state.epoch || !has(r, "loop")) {
      await end(effects(prefix).filter(e => e.data.name !== `${prefix}.closing`));
      await restoreFailedOpen();
    }
  } catch (error) {
    await end(effects(prefix).filter(e => e.data.name !== `${prefix}.closing`));
    try { await restoreFailedOpen(); }
    catch (restoreError) { throw new Error(`${error.message || error}; ${restoreError.message}`); }
    if (current() && epoch === state.epoch) throw error;
  }
}
async function toggle(action, epoch) {
  const r = discover();
  if (!r || !has(r, "loop")) throw new Error("Create a rift and wait for its opening before toggling anchors.");
  permitted(effects(r.prefix));
  const sides = action === "both" ? ["left", "right"] : [action];
  const enable = !sides.every(side => has(r, side));
  const added = [];
  try {
    await guarded(r, epoch, true, async alive => {
      if (enable) await Sequencer.Preloader.preload(sides.filter(side => !has(r, side))
        .map(side => `${r.meta.base}/rift-edge-anchor-${side}/${r.meta.anchorPalette}.webm`));
      for (const side of sides) {
        if (!alive()) return;
        const name = `${r.prefix}.${side}`;
        if (!enable) { await end(effects(r.prefix).filter(e => e.data.name === name)); continue; }
        if (has(r, side)) continue;
        added.push(name);
        const point = { x: r.meta.point.x + (side === "left" ? -1 : 1) * r.meta.width * 0.0875, y: r.meta.point.y };
        await startPersistent(visual(r, side, `rift-edge-anchor-${side}/${r.meta.anchorPalette}`,
          point, r.meta.width * 0.32, 1).syncGroup(r.prefix).persist(), name);
      }
    });
  } catch (error) {
    await end(effects(r.prefix).filter(e => added.includes(e.data.name)));
    if (current() && epoch === state.epoch) throw error;
  }
}
async function closeRift() {
  const r = discover();
  if (r) {
    permitted(effects(r.prefix));
    await Sequencer.Preloader.preload([`${r.meta.base}/vortex-closing/${r.meta.palette}.webm`]);
  }
  ++state.epoch; // Cancels pending crosshair, opening, and anchor continuations.
  if (!r) {
    await ambient(() => setAmbient(false));
    return;
  }
  const hadVisibleRift = has(r, "opening") || has(r, "loop");
  const loop = effects(r.prefix).find(e => e.data.name === `${r.prefix}.loop`);
  const epoch = state.epoch;
  // Reading a verified getter, not seeking/cropping the loop. No clock => immediate jump.
  if (loop?.mediaIsPlaying && Number.isFinite(loop.mediaCurrentTime)) {
    const phase = ((loop.mediaCurrentTime % 3) + 3) % 3;
    if (phase > 0) await new Promise(resolve => setTimeout(resolve, (3 - phase) * 1000));
  }
  const stillMarked = effects(r.prefix).some(e => e.data.name === r.marker.data.name);
  await ambient(() => setAmbient(false));
  await end(effects(r.prefix));
  await end(effects(r.prefix));
  if (!current() || !stillMarked || !hadVisibleRift) return;
  await guarded(r, epoch, false, async () => {
    await finite(visual(r, "closing", `vortex-closing/${r.meta.palette}`), `${r.prefix}.closing`);
  }, true);
}
async function action(name) {
  if (!current()) { ui.notifications.warn("Scene changed; reopen Rift controls in the current scene."); return; }
  if (state.closing || (state.busy && name !== "close")) return;
  if (name === "close") state.closing = true;
  else state.busy = true;
  refresh();
  try {
    if (name === "close") await closeRift();
    else if (name === "create") await create(state.root.querySelector('[name="palette"]').value, state.epoch);
    else await toggle(name, state.epoch);
  } catch (error) { report(error); }
  finally {
    if (name === "close") state.closing = false;
    else state.busy = false;
    refresh();
    if (state.dismissed && !state.busy && !state.closing) controllers.delete(sceneId);
  }
}
state.dialog = new Dialog({
  title: "Rift controls",
  content: `<p>One GM controller recommended. Anchors start OFF.</p>
    <label>Rift palette <select name="palette">${PALETTES.map(p => `<option value="${p}">${p}</option>`).join("")}</select></label>
    <p data-status></p><div>${[["create", "Create rift"], ["both", "Toggle both"], ["left", "Toggle left"], ["right", "Toggle right"], ["close", "Close"]]
      .map(([a, label]) => `<button type="button" data-action="${a}">${label}</button>`).join("")}</div>`,
  buttons: {},
  render: html => {
    state.dismissed = false;
    state.root = html[0];
    for (const button of state.root.querySelectorAll('[data-action]')) button.addEventListener("click", () => { void action(button.dataset.action); });
    refresh();
  },
  close: () => {
    state.root = null;
    state.dismissed = true;
    if (!state.busy && !state.closing) controllers.delete(sceneId);
  },
}, { width: 420 });
controllers.set(sceneId, state);
state.dialog.render(true);
// X dismisses only the controls; it never creates/closes a rift. Reopen to discover it.
