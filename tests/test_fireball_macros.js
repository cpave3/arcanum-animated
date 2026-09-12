// Public entry points: execute the standalone Foundry Script macro bodies.
// Observable outcomes: effect creation/movement, persistent discovery, scoped clear.
// These mocks model the verified Sequencer subset, not a Foundry integration.
const { test } = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const castSource = fs.readFileSync(path.join(__dirname, '../examples/sequencer-fireball.js'), 'utf8');
const clearSource = fs.readFileSync(path.join(__dirname, '../examples/sequencer-clear-fireballs.js'), 'utf8');
const flush = async () => { for (let i = 0; i < 30; i++) await Promise.resolve(); };

function setup() {
  let counter = 0;
  let now = 0;
  const timers = new Map();
  const clock = {
    setTimeout(fn, delay) { const id = ++counter; timers.set(id, { at: now + delay, fn }); return id; },
    clearTimeout(id) { timers.delete(id); },
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
  const hooks = new Map();
  const effects = [];
  const history = [];
  const warnings = [];
  const pending = [];
  const env = { destination: { x: 850, y: 450 }, hold: null, beforeCreate: null };
  const Hooks = {
    on(name, fn) { if (!hooks.has(name)) hooks.set(name, new Map()); const id = ++counter; hooks.get(name).set(id, fn); return id; },
    off(name, id) { hooks.get(name)?.delete(id); },
    call(name, data) { let allowed = true; for (const fn of [...(hooks.get(name)?.values() || [])]) if (fn(data) === false) allowed = false; return allowed; },
    callAll(name, data) { this.call(name, data); },
  };
  const canvas = { scene: { id: 'scene-a' }, grid: { size: 100 }, tokens: { controlled: [{ center: { x: 50, y: 50 }, w: 300 }] } };
  const manager = {
    // Actual getEffects works on visible effects; explicit scene checks in macros
    // are necessary because source _filterEffects does not test sceneId.
    getEffects({ name, effects: ids } = {}) {
      const regex = name && new RegExp('^' + name.split('*').map(s => s.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')).join('.*') + '$');
      return effects.filter(e => (!regex || regex.test(e.data.name)) && (!ids || ids.includes(e.id)));
    },
    async endEffects(filter) {
      for (const effect of this.getEffects(filter).filter(e => e.userCanDelete)) {
        effects.splice(effects.indexOf(effect), 1);
        Hooks.callAll('endedSequencerEffect', effect);
        effect.resolve?.();
      }
      await Promise.resolve();
    },
  };
  class Sequence {
    constructor() { this.data = {}; }
    effect() { return this; }
    file(value) { this.data.file = value; return this; }
    name(value) { this.data.name = value; return this; }
    atLocation(value) { this.data.source = value; return this; }
    anchor(value) { this.data.anchor = value; return this; }
    size(value, options) { this.data.size = { value, options }; return this; }
    belowTokens(value = true) { this.data.belowTokens = value; return this; }
    opacity(value) { this.data.opacity = value; return this; }
    persist() { this.data.persist = true; return this; }
    duration(value) { this.data.duration = value; return this; }
    waitUntilFinished(value) { this.data.waitOffset = value; return this; }
    moveTowards(point, options) { this.data.moves = { point, options }; return this; }
    async play() {
      await Promise.resolve(); // Initialization/sanitization precedes preCreate.
      if (env.hold && this.data.name.endsWith(env.hold)) await new Promise(resolve => pending.push(resolve));
      this.data.sceneId = canvas.scene.id;
      this.data.creatorUserId = 'caster';
      if (!Hooks.call('preCreateSequencerEffect', this.data)) return;
      await env.beforeCreate?.(this.data);
      const effect = { id: `effect-${++counter}`, data: this.data, userCanDelete: true };
      const promise = new Promise(resolve => { effect.resolve = resolve; });
      Hooks.callAll('createSequencerEffect', effect); // Before manager registration.
      effects.push(effect);
      history.push(effect);
      if (this.data.persist) return promise;
      // Finite Sequence.play waits its scheduled duration even if ended early.
      return new Promise(resolve => { effect.finish = () => {
        const index = effects.indexOf(effect);
        if (index >= 0) effects.splice(index, 1);
        Hooks.callAll('endedSequencerEffect', effect);
        resolve();
      }; });
    }
  }
  const context = vm.createContext({ canvas, Sequence, Hooks,
    Sequencer: { EffectManager: manager, Crosshair: { show: async () => env.destination }, Preloader: { preload: async () => {} } },
    foundry: { utils: { randomID: () => `cast${++counter}` } },
    ui: { notifications: { warn: text => warnings.push(text) } },
    setTimeout: clock.setTimeout, clearTimeout: clock.clearTimeout, queueMicrotask, console,
  });
  function run(source) { return vm.runInContext(`(async () => {${source}\n})()`, context); }
  const cast = (color = 'fire', size = 6, burnSeconds = 0) => run(castSource.replace('const color = "fire";', `const color = "${color}";`).replace('const size = 6;', `const size = ${size};`).replace('const burnSeconds = 0;', `const burnSeconds = ${burnSeconds};`));
  const clear = () => run(clearSource);
  const stage = suffix => effects.filter(e => e.data.name.endsWith(`.${suffix}`));
  const finish = async suffix => { for (const effect of stage(suffix)) effect.finish(); await flush(); };
  async function land(color, size) { const task = cast(color, size); await flush(); await finish('projectile'); await finish('opening'); await task; }
  return { env, effects, history, warnings, pending, canvas, cast, clear, stage, finish, land, hooks, clock, timers, manager };
}

test('cancelled crosshair creates no effects; caster selection is required', async () => {
  const e = setup(); e.env.destination = false;
  await e.cast(); assert.equal(e.history.length, 0);
  e.canvas.tokens.controlled = [];
  await assert.rejects(e.cast(), /Select exactly one/);
});

test('cast moves a centered rotating projectile then opens into persistent embers', async () => {
  const e = setup(); const task = e.cast(); await flush();
  const projectile = e.stage('projectile')[0].data;
  assert.equal(projectile.anchor, 0.5);
  assert.equal(projectile.belowTokens, false);
  assert.equal(projectile.moves.options.rotate, true);
  assert.equal(projectile.moves.point.x, 850);
  assert.equal(projectile.size.options.gridUnits, true);
  assert.equal(projectile.duration, Math.hypot(800, 400));
  assert.equal(projectile.waitOffset, -1000 / 30); // Blank opening frame leads arrival.
  assert.equal(e.stage('opening').length, 0);
  await e.finish('projectile');
  assert.equal(e.stage('opening')[0].data.duration, 107 * 1000 / 30);
  assert.equal(e.stage('opening')[0].data.belowTokens, false);
  assert.equal(e.stage('embers').length, 0);
  await e.finish('opening'); await task;
  assert.equal(e.stage('embers')[0].data.persist, true);
  assert.equal(e.stage('embers')[0].data.belowTokens, true);
  assert.equal(e.effects.filter(x => x.data.name.includes('.active.')).length, 1);
  assert.equal([...e.hooks.values()].reduce((n, m) => n + m.size, 0), 0);
});

test('clear discovers two casts after hooks disappear, preserves palette/size/position and unrelated effects', async () => {
  const e = setup(); await e.land('fire', 6);
  e.env.destination = { x: 1200, y: 900 }; await e.land('cold', 8);
  const names = e.effects.filter(x => x.data.name.includes('.active.')).map(x => x.data.name);
  assert.notEqual(names[0], names[1]);
  // Simulate a foreign caster/reloaded persistent data (no runtime map involved).
  e.effects.forEach(x => { x.data.creatorUserId = 'other-user'; });
  const unrelated = { id: 'other', data: { name: 'other-module.fireball', sceneId: 'scene-a' } };
  e.effects.push(unrelated);
  const task = e.clear(); await flush();
  const closing = e.stage('closing').map(x => x.data);
  assert.ok(closing.length > 0 && closing.every(effect => effect.belowTokens === true));
  assert.equal(closing.length, 2);
  assert.ok(closing.some(x => x.file.endsWith('/cold.webm') && x.source.x === 1200 && x.size.value === 8));
  assert.ok(closing.some(x => x.file.endsWith('/fire.webm') && x.source.x === 850 && x.size.value === 6));
  assert.ok(closing.every(x => x.duration === 3000 && x.size.options.gridUnits));
  assert.ok(e.effects.includes(unrelated));
  assert.equal(e.stage('embers').length, 0);
  await e.finish('closing'); await task;
});

for (const phase of ['projectile', 'opening']) test(`clear during ${phase} prevents delayed embers; double clear creates no duplicate closing`, async () => {
  const e = setup(); const cast = e.cast(); await flush();
  if (phase === 'opening') await e.finish('projectile');
  const running = e.stage(phase)[0];
  const clears = [e.clear(), e.clear()]; await flush();
  assert.equal(e.stage('closing').length, phase === 'opening' ? 1 : 0);
  running.finish(); await cast; await flush();
  assert.equal(e.stage('embers').length, 0);
  await e.finish('closing'); await Promise.all(clears);
  await e.clear(); assert.equal(e.effects.length, 0);
});

test('preCreate guard cancels embers queued before clear', async () => {
  const e = setup(); const task = e.cast(); await flush(); await e.finish('projectile');
  e.env.hold = '.embers'; await e.finish('opening');
  assert.equal(e.pending.length, 1);
  await e.clear();
  e.pending.shift()(); await task;
  assert.equal(e.stage('embers').length, 0);
  assert.equal(e.effects.length, 0);
});

test('clear respects permissions and scene isolation', async () => {
  const e = setup(); await e.land();
  e.effects.forEach(x => { x.userCanDelete = false; });
  await e.clear(); assert.equal(e.warnings.length, 1); assert.equal(e.stage('embers').length, 1);
  e.effects.forEach(x => { x.userCanDelete = true; });
  e.canvas.scene.id = 'scene-b'; await e.clear(); assert.equal(e.stage('embers').length, 1);
  e.canvas.scene.id = 'scene-a'; const task = e.clear(); e.canvas.scene.id = 'scene-b';
  await task; assert.equal(e.stage('closing').length, 0);
});

test('post-create guard removes a stage created after clear passed its preCreate check', async () => {
  const e = setup(); const task = e.cast(); await flush(); await e.finish('projectile');
  e.env.beforeCreate = async data => {
    if (data.name.endsWith('.embers')) await e.clear();
  };
  await e.finish('opening'); await task; await flush();
  assert.equal(e.effects.length, 0);
  assert.equal(e.history.filter(x => x.data.name.endsWith('.embers')).length, 1);
});

test('scene switch during closing initialization cannot create a wrong-scene effect', async () => {
  const e = setup(); await e.land(); e.env.hold = '.closing';
  const task = e.clear(); await flush(); assert.equal(e.pending.length, 1);
  e.canvas.scene.id = 'scene-b'; e.pending.shift()(); await task;
  assert.equal(e.stage('closing').length, 0);
});

test('long travel retains the native looping projectile and finite movement duration', async () => {
  const e = setup(); e.env.destination = { x: 5050, y: 50 };
  const task = e.cast(); await flush();
  const projectile = e.stage('projectile')[0].data;
  assert.equal(projectile.duration, 5000);
  assert.equal(projectile.persist, undefined);
  assert.ok(projectile.file.endsWith('/fireball-projectile/fire.webm'));
  await e.finish('projectile'); await e.finish('opening'); await task;
  assert.equal(e.stage('embers').length, 1);
});

test('overlapping casts keep independent IDs and lifecycle hooks', async () => {
  const e = setup(); const first = e.cast('fire'); const second = e.cast('cold');
  await flush(); assert.equal(e.stage('projectile').length, 2);
  assert.notEqual(e.stage('projectile')[0].data.name, e.stage('projectile')[1].data.name);
  await e.finish('projectile'); await e.finish('opening'); await Promise.all([first, second]);
  assert.equal(e.stage('embers').length, 2);
});


test('burnSeconds rejects negative and nonfinite durations before creating effects', async () => {
  const e = setup();
  for (const duration of [-1, NaN, Infinity]) await assert.rejects(e.cast('fire', 6, duration), /burnSeconds/);
  assert.equal(e.history.length, 0);
});

test('zero burnSeconds leaves embers indefinitely without timers or hooks', async () => {
  const e = setup(); await e.land();
  await e.clock.advance(86400000);
  assert.equal(e.stage('embers').length, 1);
  assert.equal(e.timers.size, 0);
  assert.equal(e.stage('closing').length, 0);
  assert.equal([...e.hooks.values()].reduce((n, m) => n + m.size, 0), 0);
});

test('auto-expiry starts after opening and closes only its own cast with original visual data', async () => {
  const e = setup(); await e.land('fire', 6);
  const other = [...e.effects];
  e.env.destination = { x: 1200, y: 900 };
  const task = e.cast('cold', 8, 2); await flush();
  await e.clock.advance(10000);
  assert.equal(e.stage('projectile').length, 1);
  assert.equal(e.stage('closing').length, 0);
  await e.finish('projectile'); await e.clock.advance(10000);
  assert.equal(e.stage('opening').length, 1);
  assert.equal(e.stage('closing').length, 0);
  await e.finish('opening');
  await e.clock.advance(1999);
  assert.equal(e.stage('embers').length, 2);
  await e.clock.advance(1);
  assert.equal(e.stage('embers').length, 1);
  assert.ok(other.every(effect => e.effects.includes(effect)));
  assert.equal(e.effects.filter(x => x.data.name.includes('.active.')).length, 1);
  const closing = e.stage('closing')[0].data;
  assert.ok(closing.file.endsWith('/fireball-closing/cold.webm'));
  assert.equal(closing.source.x, 1200); assert.equal(closing.source.y, 900);
  assert.equal(closing.size.value, 8); assert.equal(closing.size.options.gridUnits, true);
  assert.equal(closing.duration, 3000);
  assert.equal(closing.belowTokens, true);
  await e.finish('closing'); await task;
  assert.equal(e.timers.size, 0);
  assert.equal([...e.hooks.values()].reduce((n, m) => n + m.size, 0), 0);
});

test('manual early CLEAR cancels two independent burn waits promptly with no later double closing', async () => {
  const e = setup();
  const first = e.cast('fire', 6, 2); const second = e.cast('cold', 8, 5);
  await flush(); await e.finish('projectile'); await e.finish('opening');
  assert.equal(e.timers.size, 2);
  await e.clock.advance(1000);
  const clear = e.clear(); await flush();
  let released = false;
  Promise.all([first, second]).then(() => { released = true; }); await flush();
  assert.equal(released, true); // No need to advance to either deadline.
  assert.equal(e.timers.size, 0);
  assert.equal(e.hooks.get('endedSequencerEffect').size, 0);
  assert.equal(e.stage('embers').length, 0);
  assert.equal(e.stage('closing').length, 2);
  await e.finish('closing'); await clear;
  await e.clock.advance(10000);
  assert.equal(e.history.filter(x => x.data.name.endsWith('.closing')).length, 2);
  assert.equal(e.effects.length, 0);
  assert.equal([...e.hooks.values()].reduce((n, m) => n + m.size, 0), 0);
});

test('removing one marker cancels only its timer while another cast auto-expires', async () => {
  const e = setup(); const first = e.cast('fire', 6, 2); const second = e.cast('cold', 8, 5);
  await flush(); await e.finish('projectile'); await e.finish('opening');
  const marker = e.effects.find(x => x.data.name.includes('.active.'));
  await e.manager.endEffects({ effects: [marker.id] }); await flush();
  let released = false; first.then(() => { released = true; }); await flush();
  assert.equal(released, true);
  assert.equal(e.timers.size, 1);
  await e.clock.advance(5000);
  assert.equal(e.stage('closing').length, 1);
  assert.ok(e.stage('closing')[0].data.file.endsWith('/cold.webm'));
  await e.finish('closing'); await second;
  assert.equal(e.timers.size, 0);
  assert.equal([...e.hooks.values()].reduce((n, m) => n + m.size, 0), 0);
});

test('CLEAR during auto-closing does not duplicate closing or end it', async () => {
  const e = setup(); const task = e.cast('fire', 6, 1);
  await flush(); await e.finish('projectile'); await e.finish('opening');
  await e.clock.advance(1000);
  const closing = e.stage('closing')[0];
  await e.clear();
  assert.deepEqual(e.stage('closing'), [closing]);
  assert.equal(e.history.filter(x => x.data.name.endsWith('.closing')).length, 1);
  await e.finish('closing'); await task;
  assert.equal(e.effects.length, 0);
});
