// Shared browser-test driver: exercises public controls, never player internals.
export async function viewerDriver() {
  const $ = id => document.getElementById(id);
  const assert = (value, message) => { if (!value) throw new Error(message); };
  const wait = ms => new Promise(resolve => setTimeout(resolve, ms));
  const until = async (condition, message) => {
    const deadline = Date.now()+15000;
    while (!condition()) { if (Date.now()>deadline) throw new Error(message); await wait(25); }
  };
  await until(() => document.body.dataset.ready === 'true', 'Viewer did not load its catalog');
  const catalog = await (await fetch('/assets/catalog.json', { cache: 'no-store' })).json();
  const set = (id, value, event = 'change') => {
    const control = $(id); control.value = value; control.dispatchEvent(new Event(event));
  };
  const click = id => $(id).click();
  const phase = () => $('stage').dataset.phase;
  const active = () => document.querySelector('[data-main-slot][data-active="true"]');
  const select = id => {
    set('search', '', 'input');
    document.querySelector('[data-kind="all"]').click();
    const button = document.querySelector(`[data-entry="${CSS.escape(id)}"]`);
    assert(button, `Missing library entry ${id}`); button.click();
    assert($('workspace').dataset.entry === id, `Entry ${id} was not selected`);
  };
  const pixels = () => {
    const video = active(); assert(video?.videoWidth, 'No decoded active video');
    const canvas = document.createElement('canvas'); canvas.width = video.videoWidth; canvas.height = video.videoHeight;
    const context = canvas.getContext('2d'); context.drawImage(video, 0, 0);
    const rgba = context.getImageData(0, 0, canvas.width, canvas.height).data;
    let maximum = 0, sum = 0, signature = 0;
    for (let i=3; i<rgba.length; i+=4) {
      maximum = Math.max(maximum, rgba[i]); sum += rgba[i];
      signature = (signature + rgba[i]*(i%7919)) % 2147483647;
    }
    return {maximum, sum, signature};
  };
  return {$, assert, wait, until, catalog, set, click, phase, active, select, pixels};
}
