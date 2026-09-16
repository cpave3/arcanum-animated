async () => {
  const {viewerDriver} = await import('/tests/viewer_driver.js');
  const d = await viewerDriver();
  const tokenIds = d.catalog.effects.filter(e => e.tags.includes('token')).map(e => e.id).sort();
  document.querySelector('[data-kind="token-effect"]').click();
  const visible = () => [...document.querySelectorAll('.library-item')].map(b => b.dataset.entry).sort();
  d.assert(JSON.stringify(visible()) === JSON.stringify(tokenIds), 'Token category must contain exactly the token overlays');
  d.assert(Number(document.querySelector('[data-count="token-effect"]').textContent) === tokenIds.length, 'Wrong token count');
  document.querySelector('[data-kind="loop"]').click();
  d.assert(!visible().some(id => tokenIds.includes(id)), 'Token effects still appear under general Loops');
  d.select('token-burning');
  d.assert(d.$('selection-kind').textContent === 'Token effect', 'Wrong category heading');
  d.assert(!d.$('token-preview-controls').hidden && !d.$('token-preview').hidden, 'Preview token must be visible by default');
  const image = d.$('token-preview').querySelector('img');
  await d.until(() => image.complete && image.naturalWidth > 0, 'Preview portrait did not load');
  for (const size of ['40', '90']) {
    d.set('size', size, 'input');
    const scene = d.$('scene').getBoundingClientRect(), token = d.$('token-preview').getBoundingClientRect();
    d.assert(Math.abs(scene.width/token.width-1.35/.95) < .02, 'Preview token must be 5% smaller than the macro scale reference');
    d.assert(Math.abs(scene.left+scene.width/2-token.left-token.width/2) < 1, 'Token not centered');
  }
  d.click('primary');
  await d.until(() => d.phase() === 'looping' && d.active().currentTime > .2, 'Token effect no longer loops');
  const video = d.active(), before = video.currentTime;
  d.assert(Number(getComputedStyle(video).zIndex) > Number(getComputedStyle(d.$('token-preview')).zIndex), 'Effect is not above token');
  d.click('hide-preview-token');
  d.assert(d.$('token-preview').hidden, 'Checkbox did not hide the token');
  await d.wait(120);
  d.assert(d.active() === video && !video.paused && video.currentTime > before, 'Hiding the token disrupted playback');
  d.set('palette', 'necrotic');
  d.assert(d.$('token-preview').hidden, 'Palette change forgot hide preference');
  d.select('token-electric');d.assert(d.$('token-preview').hidden, 'Switching token effects forgot hide preference');
  d.click('hide-preview-token');d.assert(!d.$('token-preview').hidden, 'Checkbox did not restore token');
  d.select('rift');
  d.assert(d.$('token-preview').hidden && d.$('token-preview-controls').hidden, 'Token leaked into ordinary effect preview');
  d.select('ray-composition-1');
  d.assert(d.$('token-preview').hidden && !d.$('composition-controls').hidden, 'Token preview interferes with composition tokens');
  d.select('token-burning');
  d.assert(!d.$('token-preview').hidden, 'Token did not return');
  return {category:true, count:tokenIds.length, portrait:true, scaleRatio:true, layerOrder:true, hideWithoutPlaybackReset:true};
}
