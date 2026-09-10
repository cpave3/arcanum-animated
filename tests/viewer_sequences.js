// Playwright CLI eval function; run on a fresh viewer page served by serve.py.
async () => {
  const assert = (value, message) => { if (!value) throw new Error(message); };
  const wait = ms => new Promise(resolve => setTimeout(resolve, ms));
  const until = async (condition, message) => {
    const deadline = Date.now() + 12000;
    while (!condition()) {
      if (Date.now() > deadline) throw new Error(message);
      await wait(25);
    }
  };
  const set = (id, value) => {
    const element = document.getElementById(id);
    element.value = value;
    element.dispatchEvent(new Event('change'));
  };
  const root = document.querySelector('#sequence-demo');
  const phase = () => root.dataset.phase;
  const clip = stage => root.querySelector(`[data-sequence-clip="${stage}"]`);
  const start = () => document.querySelector('#sequence-start').click();
  const stop = () => document.querySelector('#sequence-stop').click();
  assert(phase() === 'idle', 'Sequence should initially be idle');
  assert([...root.querySelectorAll('video')].every(v => v.paused && v.hidden && Number(getComputedStyle(v).opacity) === 0), 'Idle sequence should be visually empty');
  set('speed', '2');

  for (const [chain, color, opening, loop, closing] of [
    ['rift', 'necrotic', 'portal-open', 'rift', 'portal-close'],
    ['vortex', 'psychic', 'vortex-opening', 'vortex', 'vortex-closing'],
  ]) {
    set('sequence-style', chain);
    set('sequence-color', color);
    start();
    await until(() => phase() === 'opening', `${chain} did not open`);
    assert(document.querySelector('#sequence-style').disabled, 'Configuration should be locked while running');
    assert(new URL(clip('opening').src).pathname.endsWith(`/${opening}/${color}.webm`), 'Wrong opening asset');
    await until(() => phase() === 'looping', `${chain} did not enter its loop`);
    const steady = clip('looping');
    assert(steady.loop && !steady.hidden, 'Steady phase must loop visibly');
    assert(new URL(steady.src).pathname.endsWith(`/${loop}/${color}.webm`), 'Wrong loop asset');
    let last = steady.currentTime;
    let wrapped = false;
    const onTime = () => { if (steady.currentTime < last) wrapped = true; last = steady.currentTime; };
    steady.addEventListener('timeupdate', onTime);
    await until(() => wrapped, `${chain} did not sustain across a loop boundary`);
    steady.removeEventListener('timeupdate', onTime);
    stop();
    assert(!steady.loop, 'Stop must finish this iteration rather than loop again');
    await until(() => phase() === 'closing', `${chain} did not close`);
    assert(!clip('closing').hidden && steady.hidden, 'Closing must replace the loop');
    assert(new URL(clip('closing').src).pathname.endsWith(`/${closing}/${color}.webm`), 'Wrong closing asset');
    await until(() => phase() === 'idle', `${chain} did not finish`);
    assert([...root.querySelectorAll('video')].every(v => v.hidden && v.paused), 'Closing must leave an empty stage');
    assert(!document.querySelector('#sequence-start').disabled, 'Start must be reusable');
  }

  const phases = [];
  const observer = new MutationObserver(() => phases.push(phase()));
  observer.observe(root, { attributes: true, attributeFilter: ['data-phase'] });
  start();
  await until(() => phase() === 'opening' && !clip('opening').paused, 'Early-stop test did not open');
  document.querySelector('#play').click();
  const held = clip('opening').currentTime;
  await wait(150);
  assert(clip('opening').paused && Math.abs(held-clip('opening').currentTime) < .03, 'Global Pause must pause the sequence');
  stop();
  assert(root.querySelector('[data-sequence-status]').textContent.includes('close queued'), 'Early Stop should queue closing');
  document.querySelector('#play').click();
  await until(() => phase() === 'closing', 'Queued close did not run after opening');
  await until(() => phase() === 'idle', 'Queued close did not finish');
  observer.disconnect();
  assert(!phases.includes('looping'), 'Early Stop should skip the steady loop');

  start();
  stop();
  await wait(150);
  assert(phase() === 'idle', 'Stop during loading must cancel stale work');
  start();
  await until(() => phase() === 'opening', 'Restart after cancellation failed');
  stop();
  await until(() => phase() === 'idle', 'Restarted sequence failed to close');
  assert(document.querySelector('#status').hidden, 'Other preview playback regressed');
  return { riftChain: true, vortexChain: true, sustainedLoop: true, boundaryStop: true,
    earlyStop: true, pauseResume: true, cancellation: true, restart: true };
}
