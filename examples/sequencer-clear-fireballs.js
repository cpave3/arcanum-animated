// Standalone Foundry Script macro; paired with sequencer-fireball.js v1.
// CLEAR ALL means this canvas scene only. GM needed for all users by default;
// Sequencer's effect-delete permission may also allow deleting others' effects.
// API source verification: see CAST header. Not integration-tested in Foundry.
const NS = "my-animations.fireball.v1";
const CLAIM = Symbol.for(`${NS}.clearing`);
const manager = Sequencer.EffectManager;
const sceneId = canvas.scene.id;
const effects = manager.getEffects({ name: `${NS}.*`, sceneId })
  .filter(e => e.data.sceneId === sceneId);
const active = effects.filter(e => e.data.name.includes(".active.") && !e[CLAIM]);
const jobs = [];
for (const marker of active) {
  const separator = marker.data.name.indexOf(".active.");
  const prefix = marker.data.name.slice(0, separator);
  const meta = JSON.parse(decodeURIComponent(marker.data.name.slice(separator + 8)));
  if (meta.sceneId !== sceneId) continue;
  const children = effects.filter(e => e.data.name.startsWith(`${prefix}.`) && e !== marker);
  if (!marker.userCanDelete || children.some(e => !e.userCanDelete)) {
    ui.notifications.warn("Cannot clear another user's fireball. Ask a GM or check Sequencer effect-delete permissions.");
    continue;
  }
  // Synchronous same-client claim prevents overlapping CLEAR/auto-expiry invocations. The
  // persistent marker, not this transient property, is the lifecycle authority.
  marker[CLAIM] = true;
  const landed = children.some(e => ["opening", "embers"].some(stage => e.data.name === `${prefix}.${stage}`));
  jobs.push((async () => {
    try {
      await manager.endEffects({ effects: [marker.id, ...children.map(e => e.id)], sceneId });
      // Catch a child registered while the first end request was in progress.
      const late = manager.getEffects({ name: `${prefix}.*`, sceneId })
        .filter(e => e.data.sceneId === sceneId);
      if (late.length) await manager.endEffects({ effects: late.map(e => e.id), sceneId });
      if (!landed || canvas.scene.id !== sceneId) return;
      const closingName = `${prefix}.closing`;
      // Sequence initialization is asynchronous; recheck at serialization time.
      const guard = Hooks.on("preCreateSequencerEffect", data => {
        if (data.name === closingName && (canvas.scene.id !== sceneId || data.sceneId !== sceneId)) return false;
      });
      try {
        await new Sequence().effect()
          .file(`${meta.base}/fireball-closing/${meta.color}.webm`)
          .name(closingName).atLocation(meta.point)
          .size(meta.size, { gridUnits: true }).belowTokens().duration(90 * 1000 / 30).play();
      } finally {
        Hooks.off("preCreateSequencerEffect", guard);
      }
    } catch (error) {
      delete marker[CLAIM];
      throw error;
    }
  })());
}
await Promise.all(jobs);
// Flight-only clears have no ground fire to close. Opening/embers close at the
// stored destination with their original base path, palette and grid-unit size.
// Plain WebM endEffects stops immediately: closing begins at loop frame 0, so a
// mid-loop/opening clear can jump. loopOptions({loops, endOnLastLoop:true}) ends
// a finite persisted clip automatically; it does NOT make manual endEffects
// wait for a loop boundary. No unsupported updateEffects/customData API used.
// Socket operations are not atomic across clients: simultaneous CLEARs on two
// clients can duplicate a closing, and an in-flight socket create can arrive
// after clear. CAST guards local delayed stages, but cannot promise distributed
// transactions. Use one GM to clear; repeat CLEAR for any reappearing marker.
// A socket-created orphan without its marker needs manual Effect Manager removal.
// Scene changes suppress closing to avoid a wrong-scene ghost. No other scenes
// or namespaces are ended. Reload does not resume an interrupted CAST.
// CLEAR also cancels an active CAST burnSeconds wait when its marker ends;
// no later auto-closing is played. After reload, persistent manual CLEAR still works.
