async () => {
  const {viewerDriver} = await import('/tests/viewer_driver.js');
  const d = await viewerDriver();
  const statuses = {electric:'lightning', poison:'poison', frost:'cold', necrotic:'necrotic', charmed:'psychic', acid:'acid'};
  for (const [slug, color] of Object.entries(statuses)) {
    d.select(`token-${slug}`);
    d.assert(d.$('palette').value === color, `${slug}: incorrect default palette`);
    d.set('speed', '1'); d.click('primary');
    await d.until(() => d.phase() === 'looping' && d.active().currentTime > .2, `${slug}: did not play`);
    d.assert(d.active().videoWidth === 640 && d.active().videoHeight === 640, `${slug}: lost native resolution`);
    const first = d.pixels();
    d.assert(first.sum > 1000, `${slug}: blank video`);
    if (slug === 'necrotic') d.assert(first.sum > 3000000, 'Necrotic drain is missing its ghostly volume');
    await d.wait(550);
    d.assert(d.pixels().signature !== first.signature, `${slug}: not animated`);
    if (slug === 'frost') {
      const canvas = document.createElement('canvas'); canvas.width = canvas.height = 640;
      const context = canvas.getContext('2d'); context.drawImage(d.active(), 0, 0);
      const rgba = context.getImageData(0, 0, 640, 640).data;
      let rim = 0, rimCount = 0, core = 0, coreCount = 0;
      for (let y = 0; y < 640; y++) for (let x = 0; x < 640; x++) {
        const radius = Math.hypot(x-320, y-320)/1.25;
        const alpha = rgba[(y*640+x)*4+3];
        if (radius > 145 && radius < 175) { rim += alpha; rimCount++; }
        if (radius < 75) { core += alpha; coreCount++; }
      }
      d.assert(rim/rimCount > 55 && rim/rimCount < 170, 'Frost edge coating missing or opaque');
      d.assert(core/coreCount < 5, 'Frost coating obscures the token face');
    }
    await d.until(() => d.active().currentTime > 2.6, `${slug}: did not reach end`);
    await d.until(() => d.active().currentTime < .5, `${slug}: did not loop`);
    d.assert(d.phase() === 'looping' && d.pixels().sum > 1000, `${slug}: blank loop seam`);
    d.click('primary');
    for (const palette of d.catalog.palettes) {
      d.set('palette', palette.id);
      const link = d.$('downloads').querySelector('[data-download="webm"]');
      d.assert(link.href.includes(`/token-${slug}/${palette.id}.webm`), `${slug}: incorrect download`);
      d.assert((await fetch(link.href, {method:'HEAD'})).ok, `${slug}: missing color`);
    }
  }
  d.select('token-electric');
  return {electric:true, poison:true, frost:true, necrotic:true, charmed:true, acid:true, native640:true, allPaletteDownloads:true};
}
