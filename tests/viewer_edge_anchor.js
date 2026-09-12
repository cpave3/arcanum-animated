async () => {
  // Entry points: library selection, mount preview, overlay controls, and transport.
  // Outcome: original vortex with two independent, correctly placed anchor layers.
  const {viewerDriver} = await import('/tests/viewer_driver.js');
  const d = await viewerDriver();
  const anchor = d.catalog.effects.find(effect => effect.id === 'rift-edge-anchor-left');
  d.assert(anchor?.mount?.effect === 'vortex', 'Missing original-vortex mount');
  const base = d.catalog.effects.find(effect => effect.id === anchor.mount.effect);
  const layers = ['left', 'right'].map(side => document.querySelector(`[data-overlay-side="${side}"]`));
  const nodeCount = 5;
  const partners = ['left', 'right'].map(side => d.catalog.effects.find(effect => effect.id === anchor.mount[side]));
  d.assert(partners[0].id !== partners[1].id, 'Mount must use distinct assets');
  d.assert(document.querySelectorAll('video').length === nodeCount, 'Expected five fixed video nodes');
  const active = video => video.dataset.active === 'true';
  const enabled = side => d.$(`overlay-${side}`).checked;
  const checkDownloads = (id, effect, color) => {
    const links = [...d.$(id).querySelectorAll('a[download]')];
    d.assert(links.length === 2, `${id} download count mismatch`);
    for (const extension of ['webm', 'png']) {
      const link = links.find(link => link.download === `${effect.id}-${color}.${extension}`);
      const path = effect.variants[color][extension === 'png' ? 'poster' : 'webm'];
      d.assert(link && new URL(link.href).pathname === new URL(path, new URL('/assets/catalog.json', location.href)).pathname,
        `${id} ${color} ${extension} mismatch`);
    }
  };
  const checkPlacement = () => {
    d.assert(d.$('overlay-size').value === '32' && d.$('overlay-spacing').value === '8.75', 'Mount preset snapped or missing');
    const scene = d.$('scene').getBoundingClientRect();
    for (const [index, video] of layers.entries()) {
      const rect = video.getBoundingClientRect();
      const center = scene.x + scene.width * (index === 0 ? .4125 : .5875);
      d.assert(Math.abs(rect.width - scene.width * .32) < 1, 'Anchor size mismatch');
      d.assert(Math.abs(rect.x + rect.width / 2 - center) < 1, 'Anchor spacing mismatch');
      d.assert(Math.abs(rect.y + rect.height / 2 - scene.y - scene.height / 2) < 1, 'Anchor vertical position mismatch');
      const transform = new DOMMatrix(getComputedStyle(video).transform);
      d.assert(transform.a === 1 && video.dataset.mirrored === 'false', 'Native mount assets must not be mirrored');
    }
  };
  const mount = async (color, source = anchor) => {
    d.select(source.id);
    d.set('palette', color);
    checkDownloads('downloads', source, color);
    d.assert(!d.$('preview-mount').hidden && !d.$('preview-mount').disabled, 'Missing usable mount button');
    d.assert(d.$('preview-mount').closest('.export-section'), 'Mount button is outside export section');
    d.assert(d.$('preview-mount').textContent === `Preview with ${base.title}`, 'Mount title mismatch');
    d.click('preview-mount');
    d.assert(d.$('workspace').dataset.entry === base.id && d.phase() === 'idle' && !d.active(), 'Mount selected wrong base or autoplayed');
    d.assert(d.$('overlay-controls').open, 'Independent controls remain collapsed');
    for (const [index, side] of ['left', 'right'].entries()) {
      const partner = partners[index];
      d.assert(d.$(`overlay-${side}-style`).value === partner.id && enabled(side), 'Mount did not enable paired style');
      d.assert(d.$(`overlay-${side}-palette`).value === color, 'Mount lost selected anchor color');
      d.assert(!d.$(`overlay-${side}-mirror`).checked, 'Mount double-mirrored native artwork');
      const options = [...d.$(`overlay-${side}-palette`).options].map(option => option.value).sort();
      d.assert(JSON.stringify(options) === JSON.stringify(Object.keys(partner.variants).sort()), 'Overlay palette options mismatch');
      checkDownloads(`overlay-${side}-downloads`, partner, color);
      const label = d.$(`overlay-${side}-downloads`).textContent;
      d.assert(label.includes(side) && label.includes(partner.id) && label.includes(color), 'Downloads must label chosen side, file and color');
    }
    checkPlacement();
    await d.until(() => layers.every(video => active(video) && video.paused && video.readyState >= 2), 'Idle anchors did not load paused');
    for (const [index, video] of layers.entries()) {
      d.assert(new URL(video.src).pathname === new URL(partners[index].variants[color].webm, new URL('/assets/catalog.json', location.href)).pathname, 'Anchor media palette mismatch');
    }
    d.assert(layers[0].src !== layers[1].src, 'Mount reused one file for both sides');
    d.assert(document.querySelectorAll('video').length === nodeCount, 'Mount leaked video nodes');
  };

  for (const side of ['left', 'right']) {
    d.assert(d.$(`overlay-${side}-style`).value === 'orb-anchor', 'Default style must remain orb');
    d.assert(d.$(`overlay-${side}-mirror`).checked === (side === 'right'), 'Canonical-left default orientation mismatch');
  }
  d.set('speed', '1');
  d.select(base.id);
  const baseDefault = d.$('palette').value;
  d.assert(d.$('preview-mount').hidden, 'Non-mount effect has mount button');
  d.select(anchor.id);
  d.assert(d.$('palette').value === anchor.default_color, 'Anchor default palette mismatch');
  const colors = Object.keys(anchor.variants);
  d.assert(colors.length >= 2, 'Render multiple anchor palettes before running this test');
  for (const color of colors) {
    await mount(color);
    d.assert(d.$('palette').value === baseDefault, 'Anchor palette overwrote base default');
    checkDownloads('downloads', base, baseDefault);
  }

  await mount(colors[0], partners[1]);

  const baseColor = Object.keys(base.variants).find(color => color !== baseDefault);
  d.assert(baseColor, 'Render multiple base palettes before running this test');
  d.set('palette', baseColor);
  await mount(colors.find(color => color !== baseColor));
  d.assert(d.$('palette').value === baseColor, 'Mount lost base palette preference');
  checkDownloads('downloads', base, baseColor);

  d.click('primary');
  await d.until(() => d.phase() === 'looping' && d.active()?.currentTime > 0 && layers.every(video => !video.paused && video.currentTime > 0), 'Composed preview did not play');
  const signature = video => {
    const canvas = document.createElement('canvas');
    canvas.width = video.videoWidth; canvas.height = video.videoHeight;
    const context = canvas.getContext('2d'); context.drawImage(video, 0, 0);
    const pixels = context.getImageData(0, 0, canvas.width, canvas.height).data;
    let sum = 0, mark = 0;
    for (let i = 3; i < pixels.length; i += 4) {
      sum += pixels[i]; mark = (mark + pixels[i]*(i % 7919)) % 2147483647;
    }
    d.assert(sum > 1000, 'Anchor decoded blank');
    return mark;
  };
  const marks = layers.map(signature);
  await d.wait(250);
  d.assert(layers.every((video, index) => signature(video) !== marks[index]), 'Anchor contact effects did not visibly animate');
  for (const [index, side] of ['left', 'right'].entries()) {
    const other = layers[1 - index];
    const time = other.currentTime;
    d.click(`overlay-${side}`);
    d.assert(!enabled(side) && !active(layers[index]) && !layers[index].hasAttribute('src'), `${side} did not disable`);
    d.assert(active(other) && !other.paused, `${side} toggle disabled other layer`);
    await d.until(() => other.currentTime !== time, 'Other layer stopped advancing');
    d.click(`overlay-${side}`);
    await d.until(() => layers.every(video => active(video) && !video.paused), `${side} did not re-enable independently`);
  }
  d.click('pause');
  await d.until(() => d.active()?.paused && layers.every(video => video.paused), 'Pause did not pause all layers');
  const times = layers.map(video => video.currentTime);
  await d.wait(150);
  d.assert(layers.every((video, index) => Math.abs(video.currentTime - times[index]) < .05), 'Paused anchors advanced');
  d.click('pause');
  await d.until(() => !d.active()?.paused && layers.every((video, index) => !video.paused && video.currentTime !== times[index]), 'Resume did not resume anchors');
  d.click('restart');
  await d.until(() => d.phase() === 'looping' && layers.every(video => !video.paused), 'Restart failed');
  d.click('stop');
  await d.until(() => d.phase() === 'idle' && !d.active() && layers.every(video => video.paused), 'Stop did not leave idle paused anchors');

  const otherAnchor = d.catalog.effects.find(effect => effect.id === 'orb-anchor');
  d.assert(otherAnchor, 'Missing existing anchor style regression fixture');
  // Public controls must change only the chosen side, even while the base is paused.
  d.click('primary');
  await d.until(() => d.active()?.currentTime > .1 && layers.every(video => !video.paused), 'Independent control setup did not play');
  d.click('pause');
  for (const [index, side] of ['left', 'right'].entries()) {
    const otherSide = side === 'left' ? 'right' : 'left';
    const other = layers[1 - index];
    const snapshot = () => JSON.stringify({
      src: other.src, time: other.currentTime, mirror: other.dataset.mirrored,
      style: d.$(`overlay-${otherSide}-style`).value, palette: d.$(`overlay-${otherSide}-palette`).value,
      base: d.active()?.src, baseTime: d.active()?.currentTime, color: d.$('palette').value,
    });
    const before = snapshot();
    const checkMirror = expected => {
      d.assert(d.$(`overlay-${side}-mirror`).checked === expected, 'Mirror checkbox mismatch');
      d.assert(layers[index].dataset.mirrored === String(expected), 'Mirror attribute mismatch');
      d.assert(new DOMMatrix(getComputedStyle(layers[index]).transform).a === (expected ? -1 : 1), 'Mirror transform mismatch');
    };
    d.set(`overlay-${side}-style`, partners[1 - index].id);
    checkMirror(true);
    d.click(`overlay-${side}-mirror`);
    checkMirror(false);
    const color = Object.keys(partners[1 - index].variants).find(color => color !== d.$(`overlay-${side}-palette`).value);
    d.set(`overlay-${side}-palette`, color);
    checkMirror(false);
    checkDownloads(`overlay-${side}-downloads`, partners[1 - index], color);
    await d.until(() => active(layers[index]) && layers[index].paused && layers[index].currentSrc.includes(`/${color}.webm`), 'Independent palette media did not load paused');
    d.set(`overlay-${side}-style`, otherAnchor.id);
    checkMirror(side === 'right');
    await d.until(() => active(layers[index]) && layers[index].paused && layers[index].currentSrc.includes('/orb-anchor/'), 'Old style did not load independently');
    d.assert(snapshot() === before, 'Side controls changed other overlay or reset main preview');
  }
  d.click('stop');
  d.set('overlay-size', '45', 'input');
  d.set('overlay-spacing', '12', 'input');
  d.set('overlay-left-style', partners[0].id);
  d.set('overlay-right-style', partners[1].id);
  checkPlacement();
  for (const side of ['left', 'right']) if (enabled(side)) d.click(`overlay-${side}`);
  await d.wait(150);
  d.assert(layers.every(video => !active(video) && !video.hasAttribute('src')), 'Disabled loading overlays returned');
  d.assert(document.querySelectorAll('video').length === nodeCount, 'Overlay controls leaked video nodes');
  d.assert(d.$('catalog-state').hidden, 'Viewer reported an overlay error');
  return {palettes: colors.length, base: base.id, size: 32, spacing: 8.75, independent: true, nativeOrientation: true, nodeCount};
}
