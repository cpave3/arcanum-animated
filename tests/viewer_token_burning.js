async () => {
  const {viewerDriver} = await import('/tests/viewer_driver.js');
  const d = await viewerDriver();
  d.select('token-burning');
  d.assert(d.$('palette').value === 'fire', 'Burning must default to Fire');
  d.set('speed', '1'); d.click('primary');
  await d.until(() => d.phase() === 'looping' && d.active().currentTime > .2, 'Burning did not play');
  d.assert(d.active().videoWidth === 640 && d.active().videoHeight === 640, 'Huge-token resolution was lost');
  const first = d.pixels();
  d.assert(first.sum > 1000, 'Burning decoded blank');
  await d.wait(700);
  d.assert(d.pixels().signature !== first.signature, 'Flames are not moving');
  const video = d.active(), canvas = document.createElement('canvas');
  canvas.width = canvas.height = 640;
  const ctx = canvas.getContext('2d'); ctx.drawImage(video, 0, 0);
  const rgba = ctx.getImageData(0, 0, 640, 640).data;
  let covered = 0, center = 0;
  for (let y = 0; y < 640; y++) for (let x = 0; x < 640; x++) {
    const alpha = rgba[(y*640+x)*4+3];
    if (alpha > 30) covered++;
    if (x >= 260 && x < 380 && y >= 260 && y < 380) center += alpha;
  }
  d.assert(covered/(640*640) > .15 && covered/(640*640) < .30, 'Flames should cover the token without filling the canvas');
  d.assert(center/(120*120) > 40 && center/(120*120) < 140, 'Flames must cross the token face without becoming opaque');
  await d.until(() => d.active().currentTime > 1.6, 'Loop did not reach its end');
  await d.until(() => d.active().currentTime < .5, 'Loop did not restart');
  d.assert(d.phase() === 'looping' && d.pixels().sum > 1000, 'Loop stopped or became blank');
  d.click('primary');
  for (const palette of d.catalog.palettes) {
    d.set('palette', palette.id);
    const link = d.$('downloads').querySelector('[data-download="webm"]');
    d.assert(link.href.includes(`/token-burning/${palette.id}.webm`), 'Wrong burning download');
    d.assert((await fetch(link.href, {method:'HEAD'})).ok, 'Missing burning color');
  }
  d.set('palette', 'fire');
  return {native640:true, animated:true, frontFlames:true, loops:true, allPalettes:true};
}
