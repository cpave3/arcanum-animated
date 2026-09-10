// Run on a fresh viewer page, including at a short viewport such as 1280×540.
async () => {
  const assert = (value, message) => { if (!value) throw new Error(message); };
  const wait = ms => new Promise(resolve => setTimeout(resolve, ms));
  const until = async (condition, message) => {
    const deadline = Date.now()+12000;
    while (!condition()) {
      if (Date.now()>deadline) throw new Error(message);
      await wait(25);
    }
  };
  const root = document.querySelector('#sequence-demo');
  const set = (id, value) => {
    const element = document.getElementById(id);
    element.value = value;
    element.dispatchEvent(new Event('change'));
  };
  function visiblePixels(video) {
    const rectangle = video.getBoundingClientRect();
    assert(rectangle.top >= 0 && rectangle.bottom <= innerHeight && rectangle.left >= 0 && rectangle.right <= innerWidth,
      'Sequence video is outside the viewport; transitions cannot be seen');
    assert(!video.hidden && getComputedStyle(video).display !== 'none' && getComputedStyle(video).visibility === 'visible' && Number(getComputedStyle(video).opacity) === 1,
      'Active transition is hidden');
    const canvas = document.createElement('canvas');
    canvas.width = video.videoWidth; canvas.height = video.videoHeight;
    const context = canvas.getContext('2d');
    context.drawImage(video, 0, 0);
    const pixels = context.getImageData(0, 0, canvas.width, canvas.height).data;
    let alpha = 0;
    let signature = 0;
    for (let i=3; i<pixels.length; i+=4) {
      alpha += pixels[i];
      signature = (signature + pixels[i]*(i%7919)) % 2147483647;
    }
    assert(alpha > 1000, 'Transition decoded to a blank frame');
    return signature;
  }
  async function checkMotion(stage) {
    const video = root.querySelector(`[data-sequence-clip="${stage}"]`);
    await until(() => root.dataset.phase === stage && video.currentTime > .45, `${stage} did not start`);
    await wait(50);
    const first = visiblePixels(video);
    await until(() => video.currentTime > 1.15, `${stage} stopped advancing`);
    await wait(50);
    assert(root.dataset.phase === stage, `${stage} ended prematurely`);
    assert(first !== visiblePixels(video), `${stage} is displaying a frozen frame`);
  }
  set('speed', '1');
  for (const family of ['rift', 'vortex']) {
    window.scrollTo(0, 0);
    set('sequence-style', family);
    document.querySelector('#sequence-start').click();
    await checkMotion('opening');
    await until(() => root.dataset.phase === 'looping', 'Steady loop did not start');
    document.querySelector('#sequence-stop').click();
    await checkMotion('closing');
    await until(() => root.dataset.phase === 'idle', 'Closing did not finish');
  }
  return {riftOpeningVisibleAndMoving: true, riftClosingVisibleAndMoving: true,
    vortexOpeningVisibleAndMoving: true, vortexClosingVisibleAndMoving: true};
}
