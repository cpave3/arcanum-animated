async () => {
  const {viewerDriver} = await import('/tests/viewer_driver.js');
  const d = await viewerDriver();
  d.select('turn-undead');
  d.assert(d.$('palette').value === 'divine', 'Turn Undead must default to Divine');
  d.assert(d.$('palette').options.length === d.catalog.palettes.length, 'Missing exported palettes');
  const divine = [...d.$('palette').options].find(option => option.value === 'divine');
  d.assert(divine.parentElement.label === 'Themed colors', 'Divine is not grouped as a themed color');
  const radius = () => {
    const video = d.active(), canvas = document.createElement('canvas');
    canvas.width = video.videoWidth; canvas.height = video.videoHeight;
    const context = canvas.getContext('2d'); context.drawImage(video, 0, 0);
    const pixels = context.getImageData(0, 0, canvas.width, canvas.height).data;
    let mass = 0, weighted = 0;
    for (let y = 0; y < canvas.height; y++) for (let x = 0; x < canvas.width; x++) {
      const alpha = pixels[(y*canvas.width+x)*4+3];
      mass += alpha; weighted += alpha*Math.hypot(x-canvas.width/2, y-canvas.height/2);
    }
    d.assert(mass > 1000, 'Radiant blast decoded blank');
    return weighted/mass;
  };
  d.set('speed', '1'); d.click('primary');
  await d.until(() => d.phase() === 'playing' && d.active().currentTime > .23, 'Runes did not form');
  const orbitRadius = radius(), orbitSignature = d.pixels().signature;
  await d.until(() => d.active().currentTime > .6, 'Rune orbit did not advance');
  d.assert(d.pixels().signature !== orbitSignature, 'Runes did not visibly orbit');
  d.assert(Math.abs(radius()-orbitRadius) < 8, 'Runes expanded before the release');
  await d.until(() => d.active().currentTime > 1.0, 'Release did not start');
  const first = radius();
  await d.until(() => d.active().currentTime > 1.7, 'Echoes did not advance');
  d.assert(radius() > first+20, 'Light did not echo outward from the caster');
  await d.until(() => d.phase() === 'ended' && !d.active().seeking, 'Turn Undead did not finish');
  await d.wait(100);
  d.assert(d.pixels().maximum === 0, 'Turn Undead left an afterimage');
  for (const palette of d.catalog.palettes) {
    d.set('palette', palette.id);
    const link = d.$('downloads').querySelector('[data-download="webm"]');
    d.assert(link.href.includes(`/turn-undead/${palette.id}.webm`), 'Wrong palette download');
    d.assert((await fetch(link.href, {method:'HEAD'})).ok, 'Missing palette asset');
  }
  d.set('palette', 'divine');
  return {divineDefault:true, expandingRadiantEchoes:true, transparentEnding:true, allPaletteDownloads:true};
}
