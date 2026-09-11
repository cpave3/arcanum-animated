async () => {
  const {viewerDriver} = await import('/tests/viewer_driver.js');
  const d = await viewerDriver();
  d.select('fireball');
  const original = d.$('poster').src;
  d.select('fireball-stylized');
  d.assert(d.$('poster').src !== original, 'Variant replaced the original entry');
  d.assert(d.$('palette').value === 'fire', 'Variant should default to fire');
  d.assert(d.$('palette').options.length === d.catalog.palettes.length, 'Missing variant palettes');
  d.set('speed', '1'); d.click('primary');
  await d.until(() => d.phase() === 'playing' && d.active().currentTime > .18, 'Stylized bolt did not start');
  const bolt = d.pixels().sum;
  d.assert(bolt > 1000, 'Bolt decoded blank');
  await d.until(() => d.active().currentTime > 1.1, 'Stylized blast did not start');
  d.assert(d.pixels().sum > bolt*3, 'Blast did not expand');
  await d.until(() => d.phase() === 'ended' && !d.active().seeking, 'Variant did not finish');
  await d.wait(100);
  d.assert(d.pixels().maximum === 0, 'Variant did not fade to transparent');
  for (const palette of d.catalog.palettes) {
    d.set('palette', palette.id);
    const link = d.$('downloads').querySelector('[data-download="webm"]');
    d.assert(link.href.includes(`/fireball-stylized/${palette.id}.webm`), 'Wrong variant download');
    d.assert((await fetch(link.href, {method:'HEAD'})).ok, 'Missing variant asset');
  }
  d.set('palette', 'fire');
  return {separateVariant:true, visibleBolt:true, expandingBlast:true, transparentEnding:true, allPalettes:true};
}
