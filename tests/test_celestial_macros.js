// Entry point: execute the actual Script macro, then operate its dialog buttons.
// Mocked Foundry/Sequencer integration, with independent wall and media clocks.
const {test} = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const path = require('node:path');
const source = fs.readFileSync(path.join(__dirname, '../examples/sequencer-celestial-revelation.js'), 'utf8');
const asset = JSON.parse(fs.readFileSync(path.join(__dirname, '../assets/celestial-revelation/effect.json'), 'utf8'));
const flush = async () => { for (let i=0; i<60; i++) await Promise.resolve(); };
function setup(saved) {
  let now = 0, id = 0;
  const timers = new Map(), hooks = new Map(), effects = [], errors = [], history = [], dialogs = [];
  const env = {preloadFail:false, skip:false, fail:false, hold:false, permission:true};
  const pending = [];
  const later = (fn, ms) => { const key = ++id; timers.set(key, {at:now+ms, fn}); return key; };
  const clock = async ms => {
    const end = now+ms;
    for (;;) {
      const next = [...timers].sort((a,b) => a[1].at-b[1].at)[0];
      if (!next || next[1].at > end) break;
      now = next[1].at; timers.delete(next[0]); next[1].fn(); await flush();
    }
    now = end; await flush();
  };
  const Hooks = {
    on(event, fn) { const key = ++id; if (!hooks.has(event)) hooks.set(event,new Map()); hooks.get(event).set(key,fn); return key; },
    off(event,key) { hooks.get(event)?.delete(key); },
    call(event,data) { let ok=true; for (const fn of [...(hooks.get(event)?.values() || [])]) if(fn(data) === false) ok=false; return ok; },
  };
  const original = {bright:3,dim:22,color:'#123456',alpha:.8,angle:90,luminosity:-.2,
    animation:{type:'torch',speed:7,intensity:8},darkness:{min:.4,max:.9}};
  const doc = {id:'t1',uuid:'Scene.a.Token.t1',name:'Aasimar <test>',isOwner:true,
    flags:structuredClone(saved?.flags || {}), lightData:structuredClone(saved?.lightData || original),
    getFlag(scope,key) { return this.flags[scope]?.[key]; },
    get light() { return {toObject:() => structuredClone(this.lightData)}; },
    async update(data) {
      if (env.writeHold && 'light.bright' in data) await new Promise(r => pending.push(r));
      if (env.restoreFail && 'light' in data) throw new Error('Restore denied');
      if (env.lightFail && 'light.bright' in data) throw new Error('Light update denied');
      history.push({at:now,data:structuredClone(data)});
      for (const [key,value] of Object.entries(data)) {
        if (key === 'light') { this.lightData=structuredClone(value); continue; }
        const parts=key.split('.'); let target=this;
        if(parts[0] === 'light') { target=this.lightData; parts.shift(); }
        for(const part of parts.slice(0,-1)) target=target[part] ??= {};
        const last=parts.at(-1);
        if(last.startsWith('-=')) delete target[last.slice(2)]; else target[last]=structuredClone(value);
      }
    },
  };
  const token = {document:doc};
  const scene = {id:'a',tokens:new Map([[doc.id,doc]])};
  const canvas = {scene,grid:{size:100},tokens:{controlled:[token]}};
  const manager = {
    getEffects:() => effects,
    async endEffects({effects:ids}) {
      for (const e of [...effects]) if(ids.includes(e.id)) { effects.splice(effects.indexOf(e),1); e.resolve(); }
    },
  };
  class Sequence {
    constructor() { this.data={}; }
    effect() {return this;}
    file(v) {this.data.file=v;return this;}
    name(v) {this.data.name=v;return this;}
    attachTo(v) {this.attached=v;return this;}
    size(v) {this.data.size=v;return this;}
    belowTokens(v) {this.data.belowTokens=v;return this;}
    duration(v) {this.data.duration=v;return this;}
    waitUntilFinished() {this.wait=true;return this;}
    async play() {
      if(env.hold) await new Promise(r => pending.push(r));
      if(env.fail) throw new Error('Asset missing');
      if(env.skip) return;
      this.data.sceneId=canvas.scene.id;
      if(!Hooks.call('preCreateSequencerEffect',this.data)) return;
      const e={id:`e${++id}`,data:this.data,attached:this.attached,userCanDelete:env.permission,mediaIsPlaying:false,mediaCurrentTime:0};
      const done=new Promise(r => e.resolve=r);
      Hooks.call('createSequencerEffect',e); effects.push(e);
      if(this.wait) await done;
    }
  }
  class Dialog {
    constructor(config) {this.config=config;dialogs.push(this);}
    render() {
      const nodes=new Map();
      for(const name of ['activate','clear']) nodes.set(`[data-action="${name}"]`,{dataset:{action:name},addEventListener:(_,fn)=>this[name]=fn});
      nodes.set('[name="palette"]',{value:'divine'});
      nodes.set('[data-token]',{});nodes.set('[data-status]',{});this.nodes=nodes;
      this.config.render([{querySelector:key=>nodes.get(key),querySelectorAll:()=>[...nodes.values()].filter(n=>n.dataset)}]);
    }
    dismiss() {this.config.close();}
  }
  const context=vm.createContext({canvas,Sequence,Dialog,Hooks,Date:{now:()=>now},
    Sequencer:{EffectManager:manager,Preloader:{preload:async()=>{if(env.preloadFail) throw new Error('Preload failed');}}},
    foundry:{utils:{randomID:()=>`r${++id}`}},ui:{notifications:{error:t=>errors.push(t),warn:t=>errors.push(t)}},
    setTimeout:later,queueMicrotask,
  });
  const run=()=>vm.runInContext(`(async()=>{${source}\n})()`,context);
  const click=async name=>{dialogs.at(-1)[name]();await flush();};
  const cue=async(seconds=asset.cue_time)=>{effects[0].mediaIsPlaying=true;effects[0].mediaCurrentTime=seconds;await clock(16);};
  const release=async()=>{pending.splice(0).forEach(r=>r());await flush();};
  const finish=async()=>{await manager.endEffects({effects:effects.map(e=>e.id)});await flush();};
  return {run,click,cue,clock,release,finish,env,doc,token,canvas,scene,effects,errors,history,dialogs,original,
    saved:()=>doc.getFlag('world','celestialRevelation'),hooks:()=>[...hooks.values()].reduce((n,v)=>n+v.size,0)};
}

test('selected token is locked to dialog; one dialog per token; only requested palettes',async()=>{
  const h=setup();await h.run();await h.run();assert.equal(h.dialogs.length,1);
  assert.match(h.dialogs[0].config.content,/>Divine<.*>Radiant<.*>Necrotic</s);
  h.canvas.tokens.controlled=[{document:{id:'other'}}];await h.click('activate');
  assert.equal(h.effects[0].attached,h.token);assert.equal(h.effects[0].data.size,600);
  assert.equal(h.effects[0].data.belowTokens,false);
});
for (const [palette,color] of [['divine','#fff0c2'],['radiant','#ffd45c'],['necrotic','#66ffd0']]) {
  test(`${palette}: slow decode does not light early; burst applies light; Clear restores original`,async()=>{
    const h=setup();await h.run();h.dialogs[0].nodes.get('[name="palette"]').value=palette;
    await h.click('activate');assert.match(h.effects[0].data.file,new RegExp(`/${palette}\\.webm$`));
    await h.clock(4000);assert.deepEqual(h.doc.lightData,h.original);
    await h.cue(asset.cue_time-.01);assert.deepEqual(h.doc.lightData,h.original);
    await h.cue();assert.equal(h.doc.lightData.bright,10);assert.equal(h.doc.lightData.dim,0);
    assert.equal(h.doc.lightData.color,color);assert.equal(h.saved().status,'active');
    await h.finish();assert.equal(h.hooks(),0);assert.equal(h.saved().status,'active');
    await h.click('activate');assert.equal(h.effects.length,0);
    await h.click('clear');assert.deepEqual(h.doc.lightData,h.original);assert.equal(h.saved(),undefined);
  });
}
test('Clear during charge cancels delayed light application',async()=>{
  const h=setup();await h.run();await h.click('activate');await h.click('clear');await h.clock(5000);
  assert.deepEqual(h.doc.lightData,h.original);assert.equal(h.saved(),undefined);assert.equal(h.effects.length,0);assert.equal(h.hooks(),0);
});
test('Clear serializes behind an in-flight burst light write',async()=>{
  const h=setup();await h.run();await h.click('activate');h.env.writeHold=true;await h.cue();
  await h.click('clear');await h.release();await h.clock(16);
  assert.deepEqual(h.doc.lightData,h.original);assert.equal(h.saved(),undefined);
});
test('dismiss does not clear; saved light can be restored after a fresh context/reload',async()=>{
  const h=setup();await h.run();await h.click('activate');await h.cue();await h.finish();h.dialogs[0].dismiss();
  assert.equal(h.doc.lightData.bright,10);
  const next=setup({flags:h.doc.flags,lightData:h.doc.lightData});await next.run();await next.click('clear');
  assert.deepEqual(next.doc.lightData,h.original);assert.equal(next.saved(),undefined);
});
test('delayed creation after Clear is vetoed',async()=>{
  const h=setup();h.env.hold=true;await h.run();await h.click('activate');await h.click('clear');
  await h.clock(16);await h.release();assert.equal(h.effects.length,0);assert.equal(h.saved(),undefined);assert.equal(h.hooks(),0);
});
for (const problem of ['preloadFail','skip','fail','lightFail']) {
  test(`${problem} reports failure and leaves original lighting`,async()=>{
    const h=setup();h.env[problem]=true;await h.run();await h.click('activate');
    if(h.effects.length) await h.cue();else await h.clock(16);
    assert.ok(h.errors.length);assert.deepEqual(h.doc.lightData,h.original);assert.equal(h.saved(),undefined);
  });
}
test('failed restore retains backup for retry and surfaces error',async()=>{
  const h=setup();await h.run();await h.click('activate');await h.cue();await h.finish();h.env.restoreFail=true;
  await h.click('clear');assert.ok(h.saved());assert.match(h.errors.at(-1),/Restore denied/);
  h.env.restoreFail=false;await h.click('clear');assert.deepEqual(h.doc.lightData,h.original);assert.equal(h.saved(),undefined);
});
test('scene change before cue cancels activation and restores backup',async()=>{
  const h=setup();await h.run();await h.click('activate');h.canvas.scene={id:'b'};await h.clock(16);
  assert.equal(h.saved(),undefined);assert.deepEqual(h.doc.lightData,h.original);assert.equal(h.effects.length,0);
});
test('missing media clock times out visibly without enabling light',async()=>{
  const h=setup();await h.run();await h.click('activate');await h.clock(20016);
  assert.match(h.errors[0],/playback cue/);assert.deepEqual(h.doc.lightData,h.original);assert.equal(h.saved(),undefined);
});
test('requires selection and token update permission',async()=>{
  const h=setup();h.canvas.tokens.controlled=[];await h.run();assert.equal(h.dialogs.length,0);assert.match(h.errors[0],/exactly one/);
  h.canvas.tokens.controlled=[h.token];await h.run();h.doc.isOwner=false;await h.click('activate');
  assert.equal(h.effects.length,0);assert.equal(h.saved(),undefined);assert.match(h.errors.at(-1),/permission/);
});

test('animation interrupted before burst does not leave light or backup',async()=>{
  const h=setup();await h.run();await h.click('activate');await h.finish();await h.clock(16);
  assert.match(h.errors[0],/ended before its burst/);assert.deepEqual(h.doc.lightData,h.original);assert.equal(h.saved(),undefined);
});
test('deleted token cancels pending cue without further document writes',async()=>{
  const h=setup();await h.run();await h.click('activate');const count=h.history.length;
  h.scene.tokens.delete(h.doc.id);await h.clock(16);
  assert.equal(h.history.length,count);assert.equal(h.effects.length,0);assert.equal(h.hooks(),0);
});
