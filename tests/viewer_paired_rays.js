async () => {
  const {viewerDriver} = await import('/tests/viewer_driver.js');
  const d = await viewerDriver();
  const canvas = document.createElement('canvas');
  const context = canvas.getContext('2d', {willReadFrequently:true});
  function regionPeak(left, right) {
    const video = d.active();
    canvas.width = video.videoWidth; canvas.height = video.videoHeight;
    context.drawImage(video, 0, 0);
    const x = Math.floor(left*canvas.width), width = Math.max(1, Math.floor((right-left)*canvas.width));
    const data = context.getImageData(x, Math.floor(canvas.height*.47), width, Math.floor(canvas.height*.06)).data;
    let peak = 0; for (let i=3; i<data.length; i+=4) peak = Math.max(peak, data[i]);
    return peak;
  }
  d.set('speed', '0.25');
  for (const count of [1, 2, 3]) {
    d.select(`ray-cast-${count}`); d.set('palette', 'eldritch');
    d.assert(!d.$('pairing').hidden && d.$('pairing-cues').textContent.includes('Release'), 'Missing paired release timing');
    d.assert(d.$('palette').options.length === d.catalog.palettes.length, 'Missing ray palettes');
    d.click('primary');
    await d.until(() => d.phase() === 'playing' && d.active().currentTime > 0, 'Caster did not start');
    let bursts = 0, lit = false;
    while (d.phase() === 'playing') {
      const next = regionPeak(.91, .96) > 30;
      if (next && !lit) bursts++;
      lit = next;
      if (next) d.assert(regionPeak(1-1/canvas.width, 1) < 8, 'Outgoing beam has a hard edge');
      await d.wait(15);
    }
    d.assert(bursts === count, `Expected ${count} decoded bursts, got ${bursts}`);
    await d.until(() => !d.active().seeking, 'Final caster seek did not finish');
    await d.wait(80);
    d.assert(d.pixels().maximum === 0, 'Caster left an afterimage');
  }
  document.querySelector('[data-paired-effect="ray-hit"]').click();
  d.assert(d.$('workspace').dataset.entry === 'ray-hit', 'Pair link did not select target');
  d.assert(d.$('palette').value === 'eldritch' && d.phase() === 'idle', 'Pair link must preserve palette without autoplay');
  d.assert(d.$('paired-effects').children.length === 3, 'Target must link to all caster variants');
  d.click('primary');
  await d.until(() => d.phase() === 'playing' && d.active().currentTime > .06, 'Target beam did not arrive');
  d.assert(regionPeak(.04, .2) > 30, 'Incoming beam is not visible on the left');
  d.assert(regionPeak(0, 1/canvas.width) < 8, 'Incoming beam has a hard edge');
  await d.until(() => d.active().currentTime > .2, 'Impact did not start');
  d.assert(regionPeak(.47, .53) > 100, 'Target was not struck at its center');
  await d.until(() => d.phase() === 'ended' && !d.active().seeking, 'Target did not finish');
  await d.wait(80); d.assert(d.pixels().maximum === 0, 'Target left an afterimage');
  return {oneTwoThreeBursts:true, softenedEdges:true, pairedNavigation:true, palettePreserved:true, incomingImpact:true};
}
