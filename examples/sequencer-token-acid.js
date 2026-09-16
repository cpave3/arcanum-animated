// Standalone Foundry Script macro; select tokens, then choose a color and Apply or Clear.
// Attach/scale API: https://fantasycomputer.works/FoundryVTT-Sequencer/api/effect.html
// Mock-tested; the new dialog/recolor flow has not been tested in live Foundry.
const BASE = "assets/animations";
const EFFECT = "token-acid";
const DEFAULT_COLOR = "acid";
const TITLE = "Acid burn";
const SCALE = 1.35; // Compensates for transparent padding around the token-sized artwork.
const PALETTES = ["purple", "gold", "red", "orange", "acid", "cold", "fire", "force", "lightning", "melee", "necrotic", "poison", "psychic", "radiant", "thunder", "eldritch", "divine"];
const NS = `my-animations.${EFFECT}.v1`;
if (typeof Sequencer === "undefined" || typeof Sequence === "undefined" || !canvas.scene) {
  ui.notifications.error(`${TITLE} requires Sequencer and an active scene.`);
  return;
}
const tokens = [...canvas.tokens.controlled];
if (!tokens.length) { ui.notifications.warn("Select one or more tokens first."); return; }
if (!PALETTES.includes(DEFAULT_COLOR) || !Number.isFinite(SCALE) || SCALE <= 0) {
  ui.notifications.error(`${TITLE}: use a registered DEFAULT_COLOR and a positive SCALE.`); return;
}
const scene = canvas.scene;
const sceneId = scene.id;
const current = () => canvas.scene?.id === sceneId &&
  tokens.every(t => scene.tokens.get(t.document.id) === t.document);
const locks = globalThis[Symbol.for(`${NS}.busy`)] ??= new Set();
const manager = Sequencer.EffectManager;
const nameFor = token => `${NS}.${sceneId}.${token.document.id}.`;
const named = prefix => manager.getEffects({ name: `${prefix}*`, sceneId })
  .filter(e => e.data.sceneId === sceneId && e.data.name.startsWith(prefix));
const selectedEffects = () => tokens.flatMap(token => named(nameFor(token)));
const report = error => ui.notifications.error(`${TITLE}: ${error.message || error}`);
function permitted(list) {
  if (list.some(e => !e.userCanDelete)) throw new Error("Cannot remove an existing effect; check Sequencer delete permissions or ask a GM.");
}
async function remove(list) {
  permitted(list);
  if (list.length) await manager.endEffects({ effects: list.map(e => e.id), sceneId });
}
async function start(token, file, name, valid) {
  await new Promise((resolve, reject) => {
    let expired = false;
    const pre = Hooks.on("preCreateSequencerEffect", data => {
      if (data.name === name && (!valid() || expired || data.sceneId !== sceneId)) return false;
    });
    const created = Hooks.on("createSequencerEffect", effect => {
      if (effect.data.name !== name || effect.data.sceneId !== sceneId) return;
      queueMicrotask(async () => {
        try {
          if (!valid() || expired) {
            await remove([effect]);
            throw new Error("Apply canceled before the effect was ready.");
          }
          resolve();
        } catch (error) { reject(error); if (expired) report(error); }
        finally { cleanup(); }
      });
    });
    const timer = setTimeout(() => {
      expired = true;
      // Keep guards until delayed playback settles, preventing a timed-out effect reappearing.
      reject(new Error("Effect creation timed out; check assets and Sequencer permissions."));
    }, 15000);
    function cleanup() {
      clearTimeout(timer);
      Hooks.off("preCreateSequencerEffect", pre);
      Hooks.off("createSequencerEffect", created);
    }
    (async () => {
      try {
        await new Sequence().effect().file(file).name(name)
          .attachTo(token, { bindRotation: false, bindScale: true })
          .scaleToObject(SCALE, { uniform: false, considerTokenScale: false })
          .belowTokens(false).persist().play();
        reject(new Error("Effect was not created; check assets and Sequencer permissions."));
      } catch (error) { reject(error); }
      finally { cleanup(); }
    })();
  });
}
const state = { root: null, busy: false, color: DEFAULT_COLOR };
function refresh() {
  if (!state.root) return;
  state.root.querySelector('[data-tokens]').textContent = tokens.map(t => t.document.name).join(", ");
  const count = tokens.filter(t => named(nameFor(t)).length).length;
  state.root.querySelector('[data-status]').textContent = !current() ? "Scene changed or token removed — reopen this macro." :
    state.busy ? "Working…" : `${count}/${tokens.length} tokens affected`;
  state.root.querySelector('[name="palette"]').disabled = state.busy || !current();
  for (const button of state.root.querySelectorAll('[data-action]')) button.disabled = state.busy || !current();
}
async function action(which) {
  if (!current()) { report(new Error("Scene changed or token removed; reopen the macro.")); return; }
  if (tokens.some(t => !t.document.isOwner)) { report(new Error("You need ownership of every selected token, or a GM must run this macro.")); return; }
  if (state.busy || locks.has(sceneId)) { ui.notifications.warn(`${TITLE}: another operation is still running. Please wait.`); return; }
  const color = state.root.querySelector('[name="palette"]').value;
  if (which === "apply" && !PALETTES.includes(color)) { report(new Error("Choose a registered colorway.")); return; }
  state.color = color;
  state.busy = true;
  locks.add(sceneId);
  refresh();
  let cancelled = false, committing = false;
  const valid = () => !cancelled && current();
  const added = new Set();
  try {
    if (which === "clear") {
      await remove(selectedEffects());
    } else {
      const file = `${BASE}/${EFFECT}/${color}.webm`;
      const plan = tokens.map(token => {
        const existing = named(nameFor(token));
        return { token, existing, keep: existing.find(e => e.data.file === file) };
      });
      const obsolete = plan.flatMap(item => item.existing.filter(e => e !== item.keep));
      permitted(obsolete);
      if (plan.some(item => !item.keep)) await Sequencer.Preloader.preload([file]);
      if (!valid()) throw new Error("Scene or selected tokens changed while loading; apply canceled.");
      for (const item of plan) {
        if (!valid()) throw new Error("Scene or selected tokens changed; apply canceled.");
        if (item.keep) continue;
        const name = `${nameFor(item.token)}${foundry.utils.randomID()}`;
        added.add(name);
        await start(item.token, file, name, valid);
      }
      if (!valid()) throw new Error("Scene or selected tokens changed; apply canceled.");
      // Preserve old colors until every replacement has registered successfully.
      committing = true;
      await remove(obsolete);
    }
  } catch (error) {
    cancelled = true;
    if (!committing) {
      try { await remove(selectedEffects().filter(e => added.has(e.data.name))); }
      catch (cleanup) { error = new Error(`${error.message || error}; rollback failed: ${cleanup.message || cleanup}`); }
    } else {
      error = new Error(`${error.message || error}. New colors were created but old effects may remain; retry Apply or Clear.`);
    }
    report(error);
  } finally {
    locks.delete(sceneId);
    state.busy = false;
    refresh();
  }
}
new Dialog({
  title: `${TITLE} · Token effects`,
  content: `<p>Tokens: <span data-tokens></span></p>
    <label>Colorway <select name="palette">${PALETTES.map(color => `<option value="${color}"${color === DEFAULT_COLOR ? " selected" : ""}>${color[0].toUpperCase()+color.slice(1)}</option>`).join("")}</select></label>
    <p data-status></p>
    <button type="button" data-action="apply">Apply</button>
    <button type="button" data-action="clear">Clear</button>`,
  buttons: {},
  render: html => {
    state.root = html[0];
    state.root.querySelector('[name="palette"]').value = state.color;
    for (const button of state.root.querySelectorAll('[data-action]')) button.addEventListener("click", () => { void action(button.dataset.action); });
    refresh();
  },
  close: () => { state.root = null; }, // Dismissal never removes effects or cancels an in-flight Apply.
}, { width: 420 }).render(true);
