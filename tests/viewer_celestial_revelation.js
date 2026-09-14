async () => {
  const {viewerDriver} = await import('/tests/viewer_driver.js');
  const d = await viewerDriver();
  d.select('celestial-revelation');
  d.assert(d.$('palette').value === 'divine', 'Revelation must default to Divine');
  d.assert(d.$('palette').options.length === d.catalog.palettes.length, 'Missing palettes');
  const radius = () => {
    const video = d.active(), canvas = document.createElement('canvas');
    canvas.width = video.videoWidth; canvas.height = video.videoHeight;
    const ctx = canvas.getContext('2d'); ctx.drawImage(video, 0, 0);
    const pixels = ctx.getImageData(0, 0, canvas.width, canvas.height).data;
    let mass = 0, weighted = 0;
    for (let y = 0; y < canvas.height; y++) for (let x = 0; x < canvas.width; x++) {
      const alpha = pixels[(y*canvas.width+x)*4+3];
      mass += alpha; weighted += alpha*Math.hypot(x-canvas.width/2, y-canvas.height/2);
    }
    d.assert(mass > 1000, 'Revelation decoded blank');
    return weighted/mass;
  };
  for (const color of ['divine', 'radiant', 'necrotic']) {
    d.set('palette', color); d.set('speed', '1'); d.click('primary');
    await d.until(() => d.phase() === 'playing' && d.active().currentTime > .2, 'Pool did not start');
    const early = d.pixels().sum;
    await d.until(() => d.active().currentTime > 1.3, 'Pool did not gather');
    d.assert(d.pixels().sum > early*3, 'Pool did not fade in');
    const pool = radius();
    await d.until(() => d.active().currentTime > 2.45, 'Core did not form');
    d.assert(radius() < pool*.3, 'Energy did not contract into the caster');
    await d.until(() => d.active().currentTime > 3.1, 'Burst did not start');
    const burst = radius();
    await d.until(() => d.active().currentTime > 3.65, 'Burst did not expand');
    d.assert(radius() > burst+30, 'Burst did not expand outwards');
    await d.until(() => d.phase() === 'ended' && !d.active().seeking, 'Revelation did not finish');
    await d.wait(100);
    d.assert(d.pixels().maximum === 0, 'Revelation left a residual image');
  }
  for (const palette of d.catalog.palettes) {
    d.set('palette', palette.id);
    const link = d.$('downloads').querySelector('[data-download="webm"]');
    d.assert(link.href.includes(`/celestial-revelation/${palette.id}.webm`), 'Wrong palette download');
    d.assert((await fetch(link.href, {method:'HEAD'})).ok, 'Missing palette asset');
  }
  d.set('palette', 'divine');
  return {pooling:true, inwardCollapse:true, outwardBurst:true, clearEnding:true, allPalettes:true};
}
