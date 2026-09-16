// Standalone Foundry Script macro (top-level await); Sequencer required.
// Select one caster; place the crosshair. Visuals only, no damage/rolls.
// API verified by curl against fantasycalendar/FoundryVTT-Sequencer commit
// a2e041c4760cab25eac346d1a025b4ce0ffa3a0d: docs/{crosshair,effect-manager}.md,
// docs/api/effect.md, src/{sections/effect,sections/section,canvas-effects/canvas-effect}.js,
// src/modules/{sequencer,sequencer-effect-manager}.js. Not Foundry-tested.
const BASE = "assets/animations";
const color = "fire";
const size = 6; // Full square clip width in grid units, independent of token size.
const projectileSize = 2;
const burnSeconds = 0; // 0 = indefinite; positive = seconds of EMBERS after opening.
const speed = 10; // Grid squares/second; movement is external to the 60f/30fps clip.
const frameMs = 1000 / 30;
const NS = "my-animations.fireball.v1"; // Shared protocol with CLEAR; do not reuse.
const CLAIM = Symbol.for(`${NS}.clearing`);
const manager = Sequencer.EffectManager;
if (canvas.tokens.controlled.length !== 1) throw new Error("Select exactly one caster token.");
if (!/^[a-z0-9-]+$/i.test(color) || ![size, projectileSize, speed].every(n => Number.isFinite(n) && n > 0)) {
  throw new Error("Use a palette name and positive size, projectileSize, and speed.");
}
if (!Number.isFinite(burnSeconds) || burnSeconds < 0) {
  throw new Error("burnSeconds must be a finite nonnegative number (0 = indefinite).");
}
const sceneId = canvas.scene.id;
const source = { ...canvas.tokens.controlled[0].center };
const destination = await Sequencer.Crosshair.show({ label: { text: "Fireball destination" } });
if (!destination) return;
if (canvas.scene.id !== sceneId) return;
const point = { x: destination.x, y: destination.y };
const id = foundry.utils.randomID();
const prefix = `${NS}.${id}`;
// Metadata lives in the serialized name, not customData (no verified setter).
const metadata = encodeURIComponent(JSON.stringify({ base: BASE, color, size, point, sceneId }));
const markerName = `${prefix}.active.${metadata}`;
const file = kind => `${BASE}/fireball-${kind}/${color}.webm`;
await Sequencer.Preloader.preload([file("projectile"), file("detonation"), file("embers"), file("closing")]);
if (canvas.scene.id !== sceneId) return;
let cancelled = false;
let cancelBurn;
const markers = () => manager.getEffects({ name: markerName, sceneId })
  .filter(e => e.data.sceneId === sceneId && !e[CLAIM]);
const alive = () => !cancelled && canvas.scene.id === sceneId && markers().length > 0;

// play() awaits a persistent effect's eventual end. Wait for its creation instead.
async function startPersistent(sequence, name) {
  await new Promise((resolve, reject) => {
    const hook = Hooks.on("createSequencerEffect", effect => {
      if (effect.data.name !== name) return;
      cleanup();
      // create hook fires just before EffectManager registers the effect.
      queueMicrotask(resolve);
    });
    const timeout = setTimeout(() => {
      cleanup();
      reject(new Error(`Sequencer did not create ${name}; check asset paths and effect permissions.`));
    }, 15000);
    function cleanup() { clearTimeout(timeout); Hooks.off("createSequencerEffect", hook); }
    sequence.play().then(() => {
      cleanup();
      if (name !== markerName && !alive()) resolve();
      else reject(new Error(`Sequencer did not create ${name}; check asset paths and effect permissions.`));
    }, error => { cleanup(); reject(error); });
  });
}
const isStage = name => ["projectile", "opening", "embers"].some(stage => name === `${prefix}.${stage}`);
async function cleanupCast() {
  const effects = manager.getEffects({ name: `${prefix}.*`, sceneId })
    .filter(e => e.data.sceneId === sceneId && (e.data.name === markerName || isStage(e.data.name)));
  if (effects.length) await manager.endEffects({ effects: effects.map(e => e.id), sceneId });
}
const preHook = Hooks.on("preCreateSequencerEffect", data => {
  if (isStage(data.name) && !alive()) return false;
});
const endHook = Hooks.on("endedSequencerEffect", effect => {
  if (effect.data.name === markerName) {
    cancelled = true;
    cancelBurn?.();
  }
});
// Also catch clear during asynchronous effect sanitization/creation.
const createdStages = new Set();
const createHook = Hooks.on("createSequencerEffect", effect => {
  if (isStage(effect.data.name)) {
    createdStages.add(effect.data.name);
    queueMicrotask(() => {
      if (!alive()) void manager.endEffects({ effects: [effect.id], sceneId });
    });
  }
});
try {
  await startPersistent(new Sequence().effect().file("icons/svg/circle.svg")
    .atLocation(point).name(markerName).opacity(0).size(1).persist(), markerName);
  if (!alive()) return;
  const travelMs = Math.max(frameMs, Math.hypot(point.x - source.x, point.y - source.y) / (speed * canvas.grid.size) * 1000);
  // duration supplies movement time; no moveSpeed override and no stretchTo.
  // Nonpersistent video loops automatically when duration exceeds media length.
  await new Sequence().effect().file(file("projectile"))
    .name(`${prefix}.projectile`).atLocation(source).anchor(0.5).belowTokens(false)
    .size(projectileSize, { gridUnits: true }).moveTowards(point, { rotate: true })
    .duration(travelMs).waitUntilFinished(-frameMs).play();
  if (alive() && !createdStages.has(`${prefix}.projectile`)) throw new Error("Projectile creation failed; check Sequencer errors and asset paths.");
  if (!alive()) return;
  // Start blank frame 0 one frame before arrival: frame-1 impact meets the orb.
  // Separate guarded stages can add client scheduling/decoding jitter.
  await new Sequence().effect().file(file("detonation"))
    .name(`${prefix}.opening`).atLocation(point).size(size, { gridUnits: true }).belowTokens(false)
    .duration(107 * 1000 / 30).play();
  if (alive() && !createdStages.has(`${prefix}.opening`)) throw new Error("Detonation creation failed; check Sequencer errors and asset paths.");
  if (!alive()) return;
  await startPersistent(new Sequence().effect().file(file("embers"))
    .name(`${prefix}.embers`).atLocation(point).size(size, { gridUnits: true }).belowTokens().persist(), `${prefix}.embers`);
  if (!alive()) await cleanupCast();
  else if (burnSeconds > 0) {
    await new Promise(resolve => {
      // Chunk long durations to stay below the JS timer's signed 32-bit limit.
      let remaining = burnSeconds;
      let timer;
      cancelBurn = () => { clearTimeout(timer); resolve(); };
      function tick() {
        if (remaining <= 0) return resolve();
        const delay = Math.min(remaining, 2147483647 / 1000);
        remaining -= delay;
        timer = setTimeout(tick, delay * 1000);
      }
      tick();
    });
    cancelBurn = undefined;
    const marker = alive() && markers()[0];
    if (!marker) return;
    const children = manager.getEffects({ name: `${prefix}.*`, sceneId })
      .filter(e => e.data.sceneId === sceneId && isStage(e.data.name));
    if (!marker.userCanDelete || children.some(e => !e.userCanDelete)) {
      throw new Error("Cannot auto-clear fireball; check Sequencer effect-delete permissions.");
    }
    // Same claim as CLEAR: whichever starts first owns this cast's closing.
    marker[CLAIM] = true;
    try {
      await cleanupCast();
      await cleanupCast(); // Catch a child registered during the first end request.
      if (canvas.scene.id !== sceneId) return;
      const closingName = `${prefix}.closing`;
      const guard = Hooks.on("preCreateSequencerEffect", data => {
        if (data.name === closingName && (canvas.scene.id !== sceneId || data.sceneId !== sceneId)) return false;
      });
      try {
        await new Sequence().effect().file(file("closing"))
          .name(closingName).atLocation(point).size(size, { gridUnits: true }).belowTokens()
          .duration(90 * 1000 / 30).play();
      } finally {
        Hooks.off("preCreateSequencerEffect", guard);
      }
    } catch (error) {
      delete marker[CLAIM];
      throw error;
    }
  }
} catch (error) {
  cancelled = true;
  await cleanupCast();
  throw error;
} finally {
  Hooks.off("preCreateSequencerEffect", preHook);
  Hooks.off("endedSequencerEffect", endHook);
  Hooks.off("createSequencerEffect", createHook);
}
// Marker + embers survive reload and remain discoverable by any permitted user.
// Reload during travel/opening cancels the JS continuation; CLEAR removes its marker.
// burnSeconds uses local JS timers: reload cancels auto-expiry, not persistent
// embers/markers. Run CLEAR after reload; timers are not resumed or synchronized.
