// Runs the public copy-paste macro; effects model Sequencer attachment/persistence.
const {test} = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const path = require('node:path');
const source = fs.readFileSync(path.join(__dirname,'../examples/sequencer-token-burning.js'),'utf8');
const flush = async () => { for(let i=0;i<50;i++) await Promise.resolve(); };
function setup(script = source) {
  let id=0;
  const tokens=[1,2,3].map(n=>({x:n*100,y:100,w:n===3?300:100,h:n===3?300:100,
    document:{id:`t${n}`,name:`Token ${n}`,isOwner:true}}));
  const scene={id:'a',tokens:new Map(tokens.map(t=>[t.document.id,t.document]))};
  const canvas={scene,tokens:{controlled:tokens}};
  const effects=[],errors=[],hooks=new Map(),pending=[],history=[],dialogs=[];
  const env={fail:null,skip:false,hold:false,preloadFail:false};
  const Hooks={
    on(event,fn) {const key=++id;if(!hooks.has(event))hooks.set(event,new Map());hooks.get(event).set(key,fn);return key;},
    off(event,key) {hooks.get(event)?.delete(key);},
    call(event,data) {let ok=true;for(const fn of [...(hooks.get(event)?.values()||[])])if(fn(data)===false)ok=false;return ok;},
  };
  const manager={
    getEffects:()=>effects,
    async endEffects({effects:ids}) {
      if (env.endFail) throw new Error('End effects failed');
      for(const e of [...effects])if(ids.includes(e.id)) {effects.splice(effects.indexOf(e),1);e.resolve?.();}
    },
  };
  class Sequence {
    constructor(){this.data={};}
    effect(){return this;}
    file(v){this.data.file=v;return this;}
    name(v){this.data.name=v;return this;}
    attachTo(token,options){this.token=token;this.options=options;return this;}
    scaleToObject(scale,options){this.scale=scale;this.scaling=options;return this;}
    belowTokens(v){this.data.belowTokens=v;return this;}
    persist(){this.data.persist=true;return this;}
    async play(){
      if(env.hold)await new Promise(r=>pending.push(r));
      if(this.token.document.id===env.fail)throw new Error('Missing asset / create denied');
      if(env.skip)return;
      this.data.sceneId=canvas.scene.id;
      if(!Hooks.call('preCreateSequencerEffect',this.data))return;
      const e={id:`e${++id}`,data:this.data,token:this.token,options:this.options,scale:this.scale,scaling:this.scaling,userCanDelete:true};
      const done=new Promise(r=>e.resolve=r);
      Hooks.call('createSequencerEffect',e);effects.push(e);history.push(e);
      await done;
    }
  }
  class Dialog {
    constructor(config) {this.config=config;dialogs.push(this);}
    render() {
      const nodes=new Map();
      for(const action of ['apply','clear']) nodes.set(`[data-action="${action}"]`,{
        dataset:{action},addEventListener:(_,fn)=>this[action]=fn,
      });
      nodes.set('[name="palette"]',{value:''});nodes.set('[data-tokens]',{});nodes.set('[data-status]',{});
      this.nodes=nodes;
      this.config.render([{querySelector:key=>nodes.get(key),querySelectorAll:()=>[...nodes.values()].filter(n=>n.dataset)}]);
    }
    close() {this.config.close();}
  }
  const context=vm.createContext({canvas,Sequence,Dialog,Hooks,Sequencer:{EffectManager:manager,
    Preloader:{preload:async()=>{if(env.preloadHold)await new Promise(r=>pending.push(r));if(env.preloadFail)throw new Error('Preload failed');}}},
    foundry:{utils:{randomID:()=>`r${++id}`}},setTimeout,clearTimeout,queueMicrotask,
    ui:{notifications:{error:t=>errors.push(t),warn:t=>errors.push(t)}},
  });
  const run=(text = script)=>vm.runInContext(`(async()=>{${text}\n})()`,context);
  const release=async()=>{pending.splice(0).forEach(r=>r());await flush();};
  const click=async(action,dialog=dialogs.at(-1))=>{dialog[action]();await flush();};
  const color=(value,dialog=dialogs.at(-1))=>{dialog.nodes.get('[name="palette"]').value=value;};
  return {run,click,color,dialogs,release,env,tokens,canvas,scene,effects,errors,history,
    hookCount:()=>[...hooks.values()].reduce((n,v)=>n+v.size,0)};
}

const defaults={burning:'fire',electric:'lightning',poison:'poison',frost:'cold',necrotic:'necrotic',charmed:'psychic',acid:'acid'};
const macro=slug=>fs.readFileSync(path.join(__dirname,`../examples/sequencer-token-${slug}.js`),'utf8');
const palettes=[...fs.readFileSync(path.join(__dirname,'../animation_fx/palettes.py'),'utf8').matchAll(/^    '([^']+)': Palette/gm)].map(m=>m[1]);
for(const [slug,defaultColor] of Object.entries(defaults)) {
  test(`${slug}: opens without effects, correct default, Apply and Clear work`,async()=>{
    const h=setup(macro(slug));await h.run();const dialog=h.dialogs[0];
    assert.equal(h.effects.length,0);assert.equal(dialog.nodes.get('[name="palette"]').value,defaultColor);
    assert.deepEqual([...dialog.config.content.matchAll(/<option value="([^"]+)"/g)].map(m=>m[1]),palettes);
    await h.click('apply');assert.equal(h.effects.length,3);assert.equal(h.hookCount(),0);
    for(const e of h.effects){
      assert.equal(e.data.file,`assets/animations/token-${slug}/${defaultColor}.webm`);
      assert.equal(e.data.persist,true);assert.equal(e.data.belowTokens,false);assert.equal(e.scale,1.35);
      assert.equal(e.options.bindRotation,false);assert.equal(e.options.bindScale,true);
      assert.equal(e.token,h.tokens.find(t=>t===e.token));
    }
    const original=[...h.effects];await h.click('apply');assert.deepEqual(h.effects,original);
    await h.click('clear');assert.equal(h.effects.length,0);assert.deepEqual(h.errors,[]);
  });
  test(`${slug}: every color can be applied and replaces existing colors without duplication`,async()=>{
    const h=setup(macro(slug));await h.run();
    for(const color of palettes){
      h.color(color);await h.click('apply');assert.equal(h.effects.length,3);
      assert.ok(h.effects.every(e=>e.data.file===`assets/animations/token-${slug}/${color}.webm`));
      assert.ok(fs.existsSync(path.join(__dirname,`../assets/token-${slug}/${color}.webm`)));
    }
    h.color(defaultColor);await h.click('clear');assert.equal(h.effects.length,0);assert.deepEqual(h.errors,[]);
  });
  test(`${slug}: failed recolor preserves all original loops and removes attempted replacements`,async()=>{
    const h=setup(macro(slug));await h.run();await h.click('apply');const before=[...h.effects];
    h.color('purple');h.env.fail='t2';await h.click('apply');
    assert.deepEqual(h.effects,before);assert.match(h.errors[0],/Missing asset/);assert.equal(h.hookCount(),0);
  });
}
test('dialog selection is fixed; mixed selection fills missing tokens and keeps matching loops',async()=>{
  const h=setup();h.canvas.tokens.controlled=[h.tokens[0]];await h.run();await h.click('apply');const first=h.effects[0];
  h.canvas.tokens.controlled=h.tokens;await h.run();h.canvas.tokens.controlled=[];await h.click('apply');
  assert.equal(h.effects.length,3);assert.equal(h.effects[0],first);assert.equal(h.history.length,3);
  await h.click('clear',h.dialogs[0]);assert.equal(h.effects.length,2);
});
test('closing controls never applies or clears effects',async()=>{
  const h=setup();await h.run();h.dialogs[0].close();assert.equal(h.effects.length,0);
  await h.run();await h.click('apply');h.dialogs.at(-1).close();assert.equal(h.effects.length,3);
});
test('selection lock and rendering token labels avoid HTML interpolation',async()=>{
  const h=setup();h.tokens[0].document.name='<img src=x>';await h.run();
  assert.ok(!h.dialogs[0].config.content.includes('<img src=x>'));
  assert.match(h.dialogs[0].nodes.get('[data-tokens]').textContent,/<img src=x>/);
});
test('all token types coexist and Clear removes only this type in every color',async()=>{
  const h=setup();for(const slug of Object.keys(defaults)){await h.run(macro(slug));await h.click('apply');}
  assert.equal(h.effects.length,Object.keys(defaults).length*3);
  await h.run(macro('poison'));h.color('divine');await h.click('apply');assert.equal(h.effects.length,Object.keys(defaults).length*3);
  const others=h.effects.filter(e=>!e.data.name.includes('token-poison.'));
  h.color('red');await h.click('clear');assert.deepEqual(h.effects,others);
});
test('foreign scenes and unrelated effects are untouched',async()=>{
  const h=setup();await h.run();await h.click('apply');
  const foreign={id:'foreign',data:{...h.effects[0].data,sceneId:'other'},userCanDelete:true};
  const other={id:'other',data:{name:'unrelated',sceneId:'a'},userCanDelete:true};
  h.effects.push(foreign,other);await h.click('clear');assert.deepEqual(h.effects,[foreign,other]);
});
test('preload failure and skipped creation surface errors without removing originals',async()=>{
  for(const reason of ['preloadFail','skip']){
    const h=setup();await h.run();await h.click('apply');const before=[...h.effects];
    h.color('necrotic');h.env[reason]=true;await h.click('apply');
    assert.deepEqual(h.effects,before);assert.ok(h.errors.length);assert.equal(h.hookCount(),0);
  }
});
test('scene change during delayed creation cancels Apply and does not leave a late effect',async()=>{
  const h=setup();h.canvas.tokens.controlled=[h.tokens[0]];await h.run();h.env.hold=true;await h.click('apply');
  h.canvas.scene={id:'other'};await h.release();assert.equal(h.effects.length,0);assert.equal(h.hookCount(),0);assert.ok(h.errors.length);
  h.canvas.scene=h.scene;h.env.hold=false;await h.click('apply');assert.equal(h.effects.length,1);
});
test('no ownership, invalid color, and no selection are reported without starting effects',async()=>{
  const h=setup();h.canvas.tokens.controlled=[];await h.run();assert.equal(h.dialogs.length,0);assert.match(h.errors.at(-1),/Select/);
  h.canvas.tokens.controlled=h.tokens;await h.run();h.tokens[0].document.isOwner=false;await h.click('apply');assert.match(h.errors.at(-1),/ownership/);
  h.tokens[0].document.isOwner=true;h.color('../other');await h.click('apply');assert.match(h.errors.at(-1),/colorway/);assert.equal(h.effects.length,0);
});
test('recolor and Clear preflight deletion permissions across all selected tokens',async()=>{
  const h=setup();await h.run();await h.click('apply');const before=[...h.effects];h.effects[1].userCanDelete=false;
  h.color('necrotic');await h.click('apply');assert.deepEqual(h.effects,before);assert.equal(h.history.length,3);
  await h.click('clear');assert.deepEqual(h.effects,before);assert.equal(h.errors.length,2);
});
test('double clicks and overlapping dialogs cannot race while applying',async()=>{
  const h=setup();h.canvas.tokens.controlled=[h.tokens[0]];await h.run();h.env.hold=true;await h.click('apply');
  assert.equal(h.dialogs[0].nodes.get('[data-action="clear"]').disabled,true);
  await h.click('apply');await h.run();await h.click('clear');assert.equal(h.errors.length,2);
  await h.release();assert.equal(h.effects.length,1);assert.equal(h.history.length,1);
});
test('closing during preload allows an already-started Apply to finish',async()=>{
  const h=setup();await h.run();h.env.preloadHold=true;await h.click('apply');h.dialogs[0].close();
  await h.release();assert.equal(h.effects.length,3);assert.deepEqual(h.errors,[]);
});
test('failed old-color removal retains new colors and can be cleaned by retrying Apply',async()=>{
  const h=setup();await h.run();await h.click('apply');h.color('necrotic');h.env.endFail=true;await h.click('apply');
  assert.equal(h.effects.length,6);assert.match(h.errors.at(-1),/retry Apply or Clear/);
  h.env.endFail=false;await h.click('apply');assert.equal(h.effects.length,3);assert.ok(h.effects.every(e=>e.data.file.endsWith('/necrotic.webm')));
});
