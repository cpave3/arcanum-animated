// Entry point: the copy-paste Script macro and its rendered button listeners.
// Outcomes: scoped persistent effects, native placements, lifecycle and table controls.
// This models the verified API subset; it is not a live Foundry integration.
const { test } = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const path = require('node:path');
const source = fs.readFileSync(path.join(__dirname, '../examples/sequencer-rift-controls.js'), 'utf8');
const flush = async () => { for (let i = 0; i < 80; i++) await Promise.resolve(); };
function setup(saved = []) {
  let id = 0, now = 0;
  const effects = saved.map(e => ({ ...e, data: structuredClone(e.data) }));
  const history = [], errors = [], preloads = [], crosshairs = [], timers = new Map(), hooks = new Map(), dialogs = [], pending = [];
  const env = { point: { x: 500, y: 400 }, fail: null, hold: null, crosshairHold: false, permission: true, beforeCreate: null };
  const clock = {
    setTimeout(fn, delay) { const key = ++id; timers.set(key, { at: now + delay, fn }); return key; },
    clearTimeout(key) { timers.delete(key); },
    async advance(ms) {
      const target = now + ms;
      for (;;) {
        const next = [...timers].sort((a, b) => a[1].at - b[1].at)[0];
        if (!next || next[1].at > target) break;
        now = next[1].at; timers.delete(next[0]); next[1].fn(); await flush();
      }
      now = target; await flush();
    },
  };
  const Hooks = {
    on(event, fn) { const key = ++id; if (!hooks.has(event)) hooks.set(event, new Map()); hooks.get(event).set(key, fn); return key; },
    off(event, key) { hooks.get(event)?.delete(key); },
    call(event, data) { let ok = true; for (const fn of [...(hooks.get(event)?.values() || [])]) if (fn(data) === false) ok = false; return ok; },
  };
  const canvas = { scene: { id: 'a', lights: [], sounds: [] }, grid: { size: 100 } };
  const manager = {
    // Deliberately ignores sceneId, matching the source filtering caveat.
    getEffects({ name } = {}) {
      return effects.filter(e => !name || (name.endsWith('*') ? e.data.name.startsWith(name.slice(0, -1)) : e.data.name === name));
    },
    async endEffects({ effects: ids }) {
      for (const e of [...effects]) if (ids.includes(e.id) && e.userCanDelete) {
        effects.splice(effects.indexOf(e), 1); Hooks.call('endedSequencerEffect', e); e.resolve?.();
      }
      await Promise.resolve();
    },
  };
  class Sequence {
    constructor() { this.data = {}; }
    effect() { return this; }
    file(v) { this.data.file = v; return this; }
    name(v) { this.data.name = v; return this; }
    atLocation(v) { this.data.point = v; return this; }
    size(v, options) { this.data.size = v; this.data.sizeOptions = options; return this; }
    belowTokens(v = true) { this.data.belowTokens = v; return this; }
    zIndex(v) { this.data.zIndex = v; return this; }
    opacity(v) { this.data.opacity = v; return this; }
    persist() { this.data.persist = true; return this; }
    syncGroup(v) { this.data.syncGroup = v; return this; }
    duration(v) { this.data.duration = v; return this; }
    waitUntilFinished() { this.data.waitUntilFinished = true; return this; }
    // No mirror/startTime/private methods: accidental use fails the real macro.
    async play() {
      await Promise.resolve();
      if (env.hold && this.data.name.includes(env.hold)) await new Promise(resolve => pending.push(resolve));
      this.data.sceneId = canvas.scene.id;
      if (!Hooks.call('preCreateSequencerEffect', this.data)) return;
      if (env.skip && this.data.file.includes(env.skip)) return;
      if (env.fail && this.data.file.includes(env.fail)) throw new Error('Missing module/assets or effect-create permission');
      await env.beforeCreate?.(this.data);
      const e = { id: `e${++id}`, data: this.data, userCanDelete: env.permission, mediaIsPlaying: true, mediaCurrentTime: 0 };
      const promise = new Promise(resolve => { e.resolve = resolve; });
      Hooks.call('createSequencerEffect', e);
      effects.push(e); history.push({ ...e, at: now });
      if (this.data.persist) return promise;
      const finished = new Promise(resolve => clock.setTimeout(() => {
        const index = effects.indexOf(e); if (index >= 0) effects.splice(index, 1);
        Hooks.call('endedSequencerEffect', e); resolve();
      }, this.data.duration));
      // Model the reported early-return path: launching does not imply playback completed.
      return this.data.waitUntilFinished ? finished : undefined;
    }
  }
  class Dialog {
    constructor(config) { this.config = config; dialogs.push(this); }
    render() {
      const nodes = new Map();
      for (const name of ['create', 'both', 'left', 'right', 'close']) nodes.set(`[data-action="${name}"]`, {
        dataset: { action: name }, textContent: '', addEventListener: (_event, fn) => { this[name] = fn; },
      });
      nodes.set('[name="palette"]', { value: this.config.content.match(/<option value="([^"]+)"/)[1] }); nodes.set('[data-status]', { textContent: '' });
      this.nodes = nodes;
      this.config.render([{ querySelector: key => nodes.get(key), querySelectorAll: () => [...nodes.values()].filter(n => n.dataset) }]);
      return this;
    }
    dismiss() { this.config.close(); }
  }
  const context = vm.createContext({ canvas, Sequence, Dialog, Hooks,
    Sequencer: { EffectManager: manager, Preloader: { preload: async files => {
      preloads.push([...files]);
      if (env.preloadHold) await new Promise(resolve => pending.push(resolve));
      if (env.preloadFail) throw new Error('Preload failed: missing asset');
    } }, Crosshair: { show: async config => {
      crosshairs.push(config);
      if (env.crosshairHold) await new Promise(resolve => pending.push(resolve));
      return env.point;
    } } },
    foundry: { utils: { randomID: () => `r${++id}` } },
    ui: { notifications: { error: text => errors.push(text), warn: text => errors.push(text) } },
    setTimeout: clock.setTimeout, clearTimeout: clock.clearTimeout, queueMicrotask,
  });
  const run = () => vm.runInContext(`(async () => {${source}\n})()`, context);
  const click = async name => { dialogs.at(-1)[name](); await flush(); };
  const stage = name => effects.find(e => e.data.name.startsWith('my-animations.rift.v1.') && e.data.name.endsWith(`.${name}`));
  const created = name => history.filter(e => e.data.name.endsWith(`.${name}`));
  const open = async () => { await run(); await click('create'); await clock.advance(2000); };
  const release = async () => { pending.splice(0).forEach(fn => fn()); await flush(); };
  const hookCount = () => [...hooks.values()].reduce((sum, map) => sum + map.size, 0);
  return { run, click, stage, created, open, release, hookCount, env, effects, history, errors, dialogs, canvas, clock, manager, timers, preloads, crosshairs };
}

test('dialog has exactly five actions, registry palettes, default purple; X does not create', async () => {
  const h = setup(); await h.run();
  const content = h.dialogs[0].config.content;
  const registry = fs.readFileSync(path.join(__dirname, '../animation_fx/palettes.py'), 'utf8');
  const palettes = [...registry.matchAll(/^    '([^']+)': Palette/gm)].map(m => m[1]);
  assert.deepEqual([...content.matchAll(/<option value="([^"]+)"/g)].map(m => m[1]), palettes);
  assert.equal((content.match(/data-action=/g) || []).length, 5);
  assert.equal(h.dialogs[0].nodes.get('[name="palette"]').value, 'purple');
  h.dialogs[0].dismiss(); assert.equal(h.history.length, 0);
  await h.run(); assert.equal(h.dialogs.length, 2);
});

test('full finite opening then persistent vortex, anchors OFF and explicit stored pixel geometry', async () => {
  const h = setup(); await h.run(); await h.click('create');
  assert.equal(h.stage('opening').data.duration, 2000);
  assert.equal(h.stage('loop'), undefined);
  await h.clock.advance(1999); assert.equal(h.stage('loop'), undefined);
  await h.clock.advance(1);
  assert.match(h.stage('loop').data.file, /\/vortex\/purple.webm$/);
  assert.equal(h.stage('opening'), undefined);
  assert.equal(h.created('loop')[0].at - h.created('opening')[0].at, 2000);
  assert.equal(h.stage('loop').data.persist, true);
  assert.equal(h.stage('loop').data.size, 600);
  assert.equal(h.stage('left'), undefined); assert.equal(h.stage('right'), undefined);
  const marker = h.effects.find(e => e.data.name.includes('.active.'));
  assert.equal(marker.data.opacity, 0); assert.equal(marker.data.file, 'icons/svg/circle.svg');
  const meta = JSON.parse(decodeURIComponent(marker.data.name.split('.active.')[1]));
  assert.deepEqual(meta, { base: 'assets/animations', size: 6, gridSize: 100, width: 600,
    palette: 'purple', anchorPalette: 'radiant', point: { x: 500, y: 400 }, sceneId: 'a' });
  assert.equal(h.hookCount(), 0); assert.equal(h.timers.size, 0);
});

test('native independent anchors and mixed both rules use matching syncGroup without restarting loop', async () => {
  const h = setup(); await h.open(); const loop = h.stage('loop');
  await h.click('left'); assert(h.stage('left')); assert.equal(h.stage('right'), undefined);
  assert.match(h.dialogs[0].nodes.get('[data-status]').textContent, /Left ON · Right OFF/);
  await h.click('both'); assert(h.stage('right')); assert.equal(h.created('left').length, 1);
  for (const [side, x] of [['left', 447.5], ['right', 552.5]]) {
    const d = h.stage(side).data;
    assert.match(d.file, new RegExp(`/rift-edge-anchor-${side}/radiant.webm$`));
    assert.deepEqual({ ...d.point }, { x, y: 400 }); assert.equal(d.size, 192);
    assert.equal(d.belowTokens, false); assert(d.zIndex > loop.data.zIndex);
    assert.equal(d.syncGroup, loop.data.syncGroup); assert.equal(d.persist, true);
  }
  assert.equal(loop.data.belowTokens, false);
  assert.match(h.dialogs[0].nodes.get('[data-action="both"]').textContent, /OFF/);
  await h.click('both'); assert.equal(h.stage('left'), undefined); assert.equal(h.stage('right'), undefined);
  await h.click('right'); assert(h.stage('right')); assert.equal(h.stage('left'), undefined);
  await h.click('both'); assert(h.stage('left')); assert(h.stage('right'));
  await h.click('left'); assert.equal(h.stage('left'), undefined); assert(h.stage('right'));
  await h.click('right'); assert.equal(h.stage('right'), undefined);
  assert.equal(h.stage('loop'), loop); assert.equal(h.errors.length, 0);
});

test('reconnect discovers metadata, chosen palette and physical size survive config/grid change; scoped boundary close', async () => {
  const a = setup(); await a.run(); a.dialogs[0].nodes.get('[name="palette"]').value = 'eldritch';
  await a.click('create'); await a.clock.advance(2000); await a.click('both');
  const saved = a.effects.map(e => ({ id: e.id, data: structuredClone(e.data), userCanDelete: true }));
  const h = setup(saved); h.canvas.grid.size = 200; await h.run();
  const unrelated = { id: 'other', data: { name: 'other.loop', sceneId: 'a' }, userCanDelete: true };
  const otherScene = { id: 'scene-b', data: { ...saved[0].data, sceneId: 'b' }, userCanDelete: true };
  h.effects.push(unrelated, otherScene);
  h.stage('loop').mediaIsPlaying = true; h.stage('loop').mediaCurrentTime = 1.25;
  await h.click('create'); assert.match(h.errors.pop(), /already/);
  await h.click('close'); await h.clock.advance(1749); assert(h.stage('loop'));
  await h.clock.advance(1); assert.equal(h.stage('loop'), undefined);
  const closing = h.stage('closing'); assert(closing);
  assert.equal(closing.data.size, 600); assert.match(closing.data.file, /vortex-closing\/eldritch.webm$/);
  assert.deepEqual({ ...closing.data.point }, { x: 500, y: 400 });
  assert.equal(closing.data.duration, 2000); assert.equal(closing.data.belowTokens, false);
  await h.clock.advance(1999); assert(h.stage('closing')); await h.clock.advance(1);
  assert.deepEqual(h.effects, [unrelated, otherScene]); assert.equal(h.hookCount(), 0);
});

test('crosshair cancel, no-loop toggles, missing Sequencer, and deletion permission errors', async () => {
  const h = setup(); await h.run(); h.env.point = null; await h.click('create');
  assert.equal(h.history.length, 0); await h.click('left'); assert.match(h.errors.pop(), /wait for its opening/);
  h.env.point = { x: 0, y: 0 }; await h.click('create'); await h.clock.advance(2000);
  h.stage('loop').userCanDelete = false;
  await h.click('both'); await h.click('close');
  assert.equal(h.errors.length, 2); assert(h.errors.every(e => /permissions/.test(e))); assert(h.stage('loop'));
  const errors = [];
  await vm.runInNewContext(`(async()=>{${source}})()`, { ui: { notifications: { error: e => errors.push(e) } } });
  assert.match(errors[0], /Sequencer/);
});

test('same-client duplicate invocation, rapid create/toggles and concurrent operations are guarded', async () => {
  const h = setup(); await h.run(); await h.run(); assert.equal(h.dialogs.length, 1);
  await h.click('create'); await h.click('create'); await h.click('left');
  assert.equal(h.created('opening').length, 1); await h.clock.advance(2000);
  h.env.hold = '.left'; await h.click('both'); await h.click('both'); await h.click('right');
  h.env.hold = null; await h.release();
  assert.equal(h.created('left').length, 1); assert.equal(h.created('right').length, 1);
});

test('Close cancels pending crosshair and opening, with no late loop or duplicate closing', async () => {
  const h = setup(); await h.run(); h.env.crosshairHold = true;
  await h.click('create'); await h.click('close'); await h.release(); assert.equal(h.history.length, 0);
  h.env.crosshairHold = false; await h.click('create'); await h.click('close'); await h.click('close');
  assert.equal(h.created('closing').length, 1);
  await h.clock.advance(2000); assert.equal(h.created('loop').length, 0); assert.equal(h.effects.length, 0);
  assert.equal(h.hookCount(), 0); assert.equal(h.errors.length, 0);
});

test('Close blocks a delayed loop/anchor create after serialization awaits', async () => {
  for (const stage of ['loop', 'left']) {
    const h = setup(); await h.run();
    if (stage === 'loop') { h.env.hold = '.loop'; await h.click('create'); await h.clock.advance(2000); }
    else { await h.click('create'); await h.clock.advance(2000); h.env.hold = '.left'; await h.click('both'); }
    await h.click('close'); h.env.hold = null; await h.release(); await h.clock.advance(2000);
    assert.equal(h.effects.length, 0); assert.equal(h.created(stage).length, 0);
    assert.equal(h.hookCount(), 0); assert.equal(h.errors.length, 0);
  }
});

test('external marker removal suppresses opening continuation and late anchor registration', async () => {
  const h = setup(); await h.run(); await h.click('create');
  await h.manager.endEffects({ effects: h.effects.filter(e => e.data.name.includes('.active.')).map(e => e.id) });
  await h.clock.advance(2000); assert.equal(h.created('loop').length, 0); assert.equal(h.effects.length, 0);
  await h.click('create'); await h.clock.advance(2000);
  h.env.beforeCreate = async data => {
    if (data.name.endsWith('.left')) await h.manager.endEffects({ effects: h.effects.filter(e => e.data.name.includes('.active.')).map(e => e.id) });
  };
  await h.click('both'); assert.equal(h.stage('left'), undefined); assert.equal(h.stage('right'), undefined);
  assert.equal(h.hookCount(), 0);
});

test('scene changes suppress creation/closing and old dialog cannot affect the new scene', async () => {
  const h = setup(); await h.run(); await h.click('create'); h.canvas.scene.id = 'b';
  await h.clock.advance(2000); assert.equal(h.created('loop').length, 0); assert.equal(h.effects.length, 0);
  await h.click('create'); assert.match(h.errors.pop(), /Scene changed/);
  h.canvas.scene.id = 'a'; await h.click('create'); await h.clock.advance(2000);
  h.stage('loop').mediaCurrentTime = 2; await h.click('close'); h.canvas.scene.id = 'b';
  await h.clock.advance(1000); assert.equal(h.created('closing').length, 0); assert.equal(h.effects.length, 0);
  assert.equal(h.hookCount(), 0);
});

test('asset/create failures clean marker and partial layers, report error and release UI/hooks', async () => {
  for (const failure of ['circle.svg', 'vortex-opening', '/vortex/']) {
    const h = setup(); await h.run(); h.env.fail = failure; await h.click('create'); await h.clock.advance(2000);
    assert.equal(h.effects.length, 0, failure); assert.match(h.errors[0], /assets/);
    assert.equal(h.hookCount(), 0); h.env.fail = null;
    await h.click('create'); await h.clock.advance(2000); assert(h.stage('loop'));
  }
  const h = setup(); await h.open(); h.env.fail = 'rift-edge-anchor-right'; await h.click('both');
  assert.equal(h.stage('left'), undefined); assert.equal(h.stage('right'), undefined); assert(h.stage('loop'));
  assert.match(h.errors[0], /assets/); assert.equal(h.hookCount(), 0);
  h.env.fail = 'vortex-closing'; await h.click('close'); assert.equal(h.effects.length, 0);
  assert.equal(h.errors.length, 2); assert.equal(h.hookCount(), 0);
});

test('silent creation veto is an error, never an invisible successful rift', async () => {
  for (const skip of ['circle.svg', 'vortex-opening', '/vortex/']) {
    const h = setup(); await h.run(); h.env.skip = skip;
    await h.click('create'); await h.clock.advance(2000);
    assert.equal(h.effects.length, 0); assert.equal(h.errors.length, 1);
    assert.match(h.errors[0], /assets|asset paths/); assert.equal(h.hookCount(), 0);
  }
});

test('reopened controls do not autoplay and anchor toggles use stored pixels after grid resize', async () => {
  const h = setup(); await h.open(); h.dialogs[0].dismiss();
  const count = h.history.length; h.canvas.grid.size = 250;
  await h.run(); assert.equal(h.history.length, count);
  await h.click('both'); assert.equal(h.stage('left').data.size, 192);
  assert.equal(h.stage('right').data.point.x, 552.5);
  assert.equal(h.created('opening').length, 1);
});

test('scene change while crosshair or closing serialization is pending leaves no wrong-scene ghost', async () => {
  const h = setup(); await h.run(); h.env.crosshairHold = true; await h.click('create');
  h.canvas.scene.id = 'b'; await h.release(); assert.equal(h.history.length, 0);
  h.canvas.scene.id = 'a'; h.env.crosshairHold = false; await h.click('create'); await h.clock.advance(2000);
  h.env.hold = '.closing'; await h.click('close'); h.canvas.scene.id = 'b'; await h.release();
  assert.equal(h.created('closing').length, 0); assert.equal(h.effects.length, 0); assert.equal(h.hookCount(), 0);
});


test('preloads the chosen rift and native anchors; dialog reports active palette and allowed actions', async () => {
  const h = setup(); await h.run();
  assert.equal(h.dialogs[0].nodes.get('[data-action="left"]').disabled, true);
  h.dialogs[0].nodes.get('[name="palette"]').value = 'necrotic';
  await h.click('create');
  assert.equal(h.preloads[0].length, 6);
  for (const kind of ['vortex-opening', 'vortex', 'vortex-closing']) {
    assert(h.preloads[0].some(file => file.endsWith(`/${kind}/necrotic.webm`)));
  }
  for (const side of ['left', 'right']) assert(h.preloads[0].some(file => file.endsWith(`/rift-edge-anchor-${side}/radiant.webm`)));
  assert.equal(h.dialogs[0].nodes.get('[data-action="create"]').disabled, true);
  assert.equal(h.dialogs[0].nodes.get('[data-action="close"]').disabled, false);
  await h.clock.advance(2000);
  assert.equal(h.dialogs[0].nodes.get('[data-action="left"]').disabled, false);
  assert.equal(h.dialogs[0].nodes.get('[name="palette"]').value, 'necrotic');
  assert.equal(h.dialogs[0].nodes.get('[name="palette"]').disabled, true);
  assert.match(h.dialogs[0].nodes.get('[data-status]').textContent, /necrotic/);
});

test('Close cancels creation during preloading, and preload failures leave no invisible marker', async () => {
  const h = setup(); await h.run(); h.env.preloadHold = true;
  await h.click('create'); await h.click('close'); h.env.preloadHold = false; await h.release();
  assert.equal(h.history.length, 0);
  h.env.preloadFail = true; await h.click('create');
  assert.equal(h.effects.length, 0); assert.match(h.errors[0], /Preload failed/);
  h.env.preloadFail = false; await h.click('create'); await h.clock.advance(2000);
  h.env.preloadFail = true; await h.click('close');
  assert(h.stage('loop')); // Keep the live rift if its closing file cannot be loaded.
  h.env.preloadFail = false; await h.click('close'); await h.clock.advance(2000);
  assert.equal(h.effects.length, 0);
});


test('crosshair disables position snapping and preserves fractional coordinates in every layer', async () => {
  const h = setup(); h.env.point = { x: 500.25, y: 400.75 };
  await h.open();
  assert.equal(h.crosshairs[0].snap.position, 0);
  assert.deepEqual({ ...h.stage('loop').data.point }, h.env.point);
  await h.click('both');
  assert.equal(h.stage('left').data.point.x, 447.75);
  assert.equal(h.stage('right').data.point.x, 552.75);
  assert.equal(h.stage('left').data.point.y, 400.75);
  await h.click('close');
  assert.deepEqual({ ...h.stage('closing').data.point }, h.env.point);
  await h.clock.advance(2000);
});


function ambientDocument(tags, hidden = true) {
  return {
    flags: tags === undefined ? {} : { tagger: { tags } }, hidden, updates: [],
    async update(change) {
      this.updates.push({ ...change });
      await this.beforeUpdate?.(change);
      this.hidden = change.hidden;
      return this;
    },
  };
}

test('opening enables exactly rift-tagged lights and sounds; anchors never change them', async () => {
  const h = setup();
  const light = ambientDocument(['rift']), sound = ambientDocument(['music', 'rift']);
  const alreadyOn = ambientDocument(['rift'], false);
  const unrelated = [ambientDocument(['drift']), ambientDocument(['rifft']), ambientDocument(undefined), ambientDocument(['rift-other'], false)];
  h.canvas.scene.lights.push(light, alreadyOn, ...unrelated.slice(0, 2));
  h.canvas.scene.sounds.push(sound, ...unrelated.slice(2));
  await h.run();
  assert(light.hidden && sound.hidden);
  await h.click('create');
  assert(h.stage('opening'));
  assert.equal(light.hidden, false); assert.equal(sound.hidden, false);
  assert.equal(alreadyOn.updates.length, 0);
  await h.clock.advance(2000);
  await h.click('both'); await h.click('left'); await h.click('right');
  assert.deepEqual(light.updates, [{ hidden: false }]);
  assert.deepEqual(sound.updates, [{ hidden: false }]);
  h.stage('loop').mediaCurrentTime = 1;
  await h.click('close'); await h.clock.advance(1999);
  assert.equal(light.hidden, false); assert.equal(sound.hidden, false);
  await h.clock.advance(1);
  assert(h.stage('closing'));
  assert.equal(light.hidden, true); assert.equal(sound.hidden, true); assert.equal(alreadyOn.hidden, true);
  assert(unrelated.every(doc => doc.updates.length === 0));
  await h.clock.advance(2000);
});

test('cancelled placement and preload failure leave tagged ambient state untouched', async () => {
  const h = setup(), light = ambientDocument(['rift']); h.canvas.scene.lights.push(light);
  await h.run(); h.env.point = null; await h.click('create');
  assert.equal(light.updates.length, 0);
  h.env.point = { x: 1, y: 2 }; h.env.preloadFail = true; await h.click('create');
  assert.equal(light.updates.length, 0);
});

test('failed light/sound enable and failed opening restore the prior ambient state', async () => {
  for (const failOpening of [false, true]) {
    const h = setup(), light = ambientDocument(['rift']), sound = ambientDocument(['rift']);
    h.canvas.scene.lights.push(light); h.canvas.scene.sounds.push(sound);
    if (failOpening) h.env.fail = 'vortex-opening';
    else sound.beforeUpdate = () => { throw new Error('Sound update denied'); };
    await h.run(); await h.click('create');
    assert.equal(light.hidden, true); assert.equal(sound.hidden, true);
    assert.deepEqual(light.updates, [{ hidden: false }, { hidden: true }]);
    assert.equal(h.effects.length, 0); assert.equal(h.hookCount(), 0);
    assert.match(h.errors[0], failOpening ? /assets/ : /Sound update denied/);
  }
});

test('ambient close failure is reported and keeps the live rift available for retry', async () => {
  const h = setup(), light = ambientDocument(['rift']), sound = ambientDocument(['rift']);
  h.canvas.scene.lights.push(light); h.canvas.scene.sounds.push(sound);
  await h.open();
  sound.beforeUpdate = change => { if (change.hidden) throw new Error('Cannot disable sound'); };
  await h.click('close');
  assert(h.stage('loop')); assert.equal(light.hidden, false); assert.equal(sound.hidden, false);
  assert.match(h.errors[0], /Cannot disable sound/);
  sound.beforeUpdate = undefined;
  await h.click('close'); await h.clock.advance(2000);
  assert.equal(light.hidden, true); assert.equal(sound.hidden, true); assert.equal(h.effects.length, 0);
});

test('Close during an in-flight ambient enable leaves all tagged documents disabled', async () => {
  const h = setup(), light = ambientDocument(['rift']), sound = ambientDocument(['rift']);
  h.canvas.scene.lights.push(light); h.canvas.scene.sounds.push(sound);
  let release;
  light.beforeUpdate = change => { if (!change.hidden) return new Promise(resolve => { release = resolve; }); };
  await h.run(); await h.click('create');
  assert.equal(h.created('opening').length, 0);
  await h.click('close'); release(); await flush();
  assert.equal(light.hidden, true); assert.equal(sound.hidden, true);
  assert.equal(h.created('opening').length, 0); assert.equal(h.created('loop').length, 0);
  assert.equal(h.created('closing').length, 0); assert.equal(h.effects.length, 0);
});

test('scene switches clean up the bound scene without touching the new scene documents', async () => {
  const h = setup(), original = h.canvas.scene;
  const light = ambientDocument(['rift']), newLight = ambientDocument(['rift']);
  original.lights.push(light); await h.run(); await h.click('create');
  assert.equal(light.hidden, false);
  h.canvas.scene = { id: 'b', lights: [newLight], sounds: [] };
  await h.clock.advance(2000);
  assert.equal(light.hidden, true); assert.equal(newLight.hidden, true); assert.equal(newLight.updates.length, 0);
  assert.equal(h.effects.length, 0);
});

test('Close can disable leftover tagged effects even when no visual rift exists', async () => {
  const h = setup(), sound = ambientDocument(['rift'], false);
  h.canvas.scene.sounds.push(sound); await h.run();
  assert.equal(h.dialogs[0].nodes.get('[data-action="close"]').disabled, false);
  await h.click('close');
  assert.equal(sound.hidden, true); assert.equal(h.history.length, 0);
});


test('a failed rollback is reported alongside the original ambient update error', async () => {
  const h = setup(), light = ambientDocument(['rift']), sound = ambientDocument(['rift']);
  h.canvas.scene.lights.push(light); h.canvas.scene.sounds.push(sound);
  await h.open();
  light.beforeUpdate = change => { if (!change.hidden) throw new Error('Light restore denied'); };
  sound.beforeUpdate = change => { if (change.hidden) throw new Error('Sound disable denied'); };
  await h.click('close');
  assert(h.stage('loop'));
  assert.match(h.errors[0], /Sound disable denied/);
  assert.match(h.errors[0], /Light restore denied/);
  light.beforeUpdate = sound.beforeUpdate = undefined;
  await h.click('close'); await h.clock.advance(2000);
  assert(light.hidden && sound.hidden); assert.equal(h.effects.length, 0);
});
