async () => {
  const {viewerDriver} = await import('/tests/viewer_driver.js');
  const d = await viewerDriver();
  const ids = ['ray-cast-1', 'ray-cast-2', 'ray-cast-3', 'ray-beam', 'ray-hit'];
  d.set('speed', '0.5');
  let partnerLinks = 0, compositionLinks = 0;
  for (const id of ids) {
    const effect = d.catalog.effects.find(entry => entry.id === id);
    d.select(id); d.set('palette', 'eldritch');
    d.assert(d.phase() === 'idle' && !d.active(), `${id} autoplayed`);
    d.assert(!d.$('pairing').hidden, `${id} lacks timing controls`);
    const cues = d.$('pairing-cues').textContent;
    d.assert(cues.includes(effect.pairing.event) && cues.includes(effect.pairing.direction), `${id} timing label mismatch`);
    d.assert(effect.pairing.direction === (id === 'ray-beam' ? 'right' : 'center'), `${id} uses baked-half direction`);
    d.assert(d.$('palette').options.length === 17, `${id} missing palettes`);
    for (const color of ['fire', 'eldritch']) {
      d.set('palette', color);
      d.assert(new URL(d.$('poster').src).pathname.endsWith(`/${id}/${color}.png`), `${id} poster mismatch`);
      for (const extension of ['webm', 'png']) {
        d.assert([...document.querySelectorAll('a[download]')].some(link =>
          new URL(link.href).pathname.endsWith(`/${id}/${color}.${extension}`)), `${id} missing ${color} ${extension} download`);
      }
    }
    d.click('primary');
    await d.until(() => d.phase() === 'playing' && d.active()?.currentTime > 0, `${id} did not play`);
    await d.until(() => d.phase() === 'ended' && !d.active().seeking, `${id} did not finish`);
    await d.wait(100);
    d.assert(d.pixels().maximum === 0, `${id} left an afterimage`);
    d.click('stop');
    d.assert(d.phase() === 'idle' && !d.$('poster').hidden, `${id} stop did not reset`);
    d.assert(d.$('paired-effects').children.length === effect.pairing.effects.length, `${id} partner list mismatch`);
    for (const partner of effect.pairing.effects) {
      d.select(id); d.set('palette', 'eldritch');
      document.querySelector(`[data-paired-effect="${partner}"]`).click();
      d.assert(d.$('workspace').dataset.entry === partner, `Link did not select ${partner}`);
      d.assert(d.$('palette').value === 'eldritch' && d.phase() === 'idle' && !d.active(), 'Partner link changed palette or autoplayed');
      partnerLinks++;
    }
    const compositions = d.catalog.compositions.filter(entry => entry.tracks.some(track => track.effect === id));
    d.assert(compositions.length === (id.startsWith('ray-cast-') ? 1 : 3), `${id} missing compositions`);
    for (const composition of compositions) {
      d.select(id); d.set('palette', 'eldritch');
      document.querySelector(`[data-composed-effect="${composition.id}"]`).click();
      d.assert(d.$('workspace').dataset.entry === composition.id, 'Composition link failed');
      d.assert(d.$('palette').value === 'eldritch' && d.phase() === 'idle', 'Composition link changed palette or autoplayed');
      d.assert(!d.$('composition-controls').hidden, 'Composition position controls missing');
      compositionLinks++;
    }
  }
  return {components: ids.length, partnerLinks, compositionLinks, transparentEndpoints: true, noAutoplay: true};
}
