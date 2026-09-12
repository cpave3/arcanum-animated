async () => {
  // Public entry points: library, From/To controls, palettes and transport.
  // Outcomes: square moving orb, ground at arrival, persistent loop and clean close/cancel.
  const { viewerDriver } = await import('/tests/viewer_driver.js');
  const d = await viewerDriver();
  const item = d.catalog.journeys?.find(item => item.id === 'fireball-journey');
  d.assert(item?.colors.length, 'Render/export fireball-journey before running this test');
  const videos = () => [...document.querySelectorAll('[data-journey-phase]')];
  const video = phase => videos().find(v => v.dataset.journeyPhase === phase);
  const visible = phase => video(phase)?.dataset.active === 'true';
  const position = v => ({ x: parseFloat(v.style.left), y: parseFloat(v.style.top) });
  const peak = v => {
    d.assert(v?.videoWidth, 'Missing decoded journey frame');
    const canvas = document.createElement('canvas');
    canvas.width = v.videoWidth; canvas.height = v.videoHeight;
    const ctx = canvas.getContext('2d'); ctx.drawImage(v, 0, 0);
    const data = ctx.getImageData(0, 0, canvas.width, canvas.height).data;
    let max = 0; for (let i = 3; i < data.length; i += 4) max = Math.max(max, data[i]);
    return max;
  };
  document.querySelector('[data-kind="journey"]').click();
  d.assert([...document.querySelectorAll('.library-item')].some(v => v.dataset.entry === item.id), 'Journey filter missing entry');
  d.select(item.id);
  d.assert(d.$('seek').disabled && d.phase() === 'idle' && videos().length === 4, 'Journey allocation or transport incorrect');
  const tokenLayer = Number(getComputedStyle(d.$('composition-scene').querySelector('[data-token="to"]')).zIndex);
  for (const phase of ['flying', 'opening']) {
    d.assert(Number(getComputedStyle(video(phase)).zIndex) > tokenLayer, `${phase} must engulf tokens`);
  }
  for (const phase of ['looping', 'closing']) {
    d.assert(Number(getComputedStyle(video(phase)).zIndex) < tokenLayer, `${phase} must be ground beneath tokens`);
  }
  d.assert(Number(d.$('travel-duration').value) === item.travel_duration && Number(d.$('burn-duration').value) === 0, 'Wrong default timing');
  for (const color of item.colors) {
    d.set('palette', color);
    const paths = d.$('path-field').value.split(' → ');
    d.assert(paths.length === 4 && new Set(paths).size === 4 && paths.every(path => path.endsWith(`/${color}.webm`)), 'Copy paths missing unique components');
    for (const type of ['webm', 'poster']) {
      const links = [...d.$('downloads').querySelectorAll(`[data-download="${type}"]`)];
      d.assert(links.length === 4, `Missing ${type} downloads`);
      for (const link of links) d.assert((await fetch(link.href)).ok, `Unavailable download ${link.href}`);
    }
  }
  d.set('from-y', '25', 'input'); d.set('to-y', '75', 'input');
  d.set('travel-duration', '1.5'); d.set('speed', '1'); d.click('primary');
  await d.until(() => d.phase() === 'flying' && visible('flying'), 'Flight never started');
  const orb = video('flying');
  const first = position(orb);
  const scene = d.$('composition-scene').getBoundingClientRect();
  const dx = scene.width * .56, dy = scene.height * .5;
  const matrix = new DOMMatrix(getComputedStyle(orb).transform);
  d.assert(Math.abs(Math.atan2(matrix.b, matrix.a) - Math.atan2(dy, dx)) < .001, 'Orb angle does not follow From → To');
  d.assert(orb.style.width === orb.style.height && getComputedStyle(orb).objectFit === 'contain', 'Orb was stretched');
  await d.wait(180);
  d.assert(position(orb).x > first.x && position(orb).y > first.y && peak(orb) > 0, 'Projectile did not visibly advance');
  d.click('pause'); const paused = position(orb);
  await d.wait(160);
  d.assert(position(orb).x === paused.x && videos().every(v => v.paused), 'Pause did not freeze flight');
  d.assert(videos().every(v => getComputedStyle(v).display !== 'none'), 'Firefox decoders left layout');
  d.set('speed', '2'); d.click('pause');
  await d.wait(120);
  d.assert(position(orb).x - paused.x > dx * .1 && videos().every(v => v.playbackRate === 2), 'Flight speed/resume failed');
  await d.until(() => d.phase() === 'opening' && visible('opening') && video('opening').currentTime > .05, 'No arrival detonation');
  d.assert(!visible('flying') && peak(video('opening')) > 0, 'Detonation missing or orb remains');
  for (const phase of ['opening', 'looping', 'closing']) {
    const v = video(phase), p = position(v);
    d.assert(Math.abs(p.x - scene.width * .78) < 1 && Math.abs(p.y - scene.height * .75) < 1 && v.style.width === v.style.height, 'Ground not square and centered at To');
  }
  await d.until(() => d.phase() === 'looping', 'Ground did not reach embers');
  await d.wait(2300);
  d.assert(d.phase() === 'looping' && visible('looping') && peak(video('looping')) > 0, 'Manual embers did not persist beyond a loop');
  d.click('pause'); const loopTime = video('looping').currentTime;
  await d.wait(160);
  d.assert(video('looping').currentTime === loopTime, 'Ground pause failed');
  d.click('stop');
  d.assert(d.phase() === 'looping' && !video('looping').loop, 'Close skipped loop boundary');
  d.click('pause');
  await d.until(() => d.phase() === 'closing', 'Manual Close never reached closing');
  await d.until(() => d.phase() === 'idle', 'Closing never cleared');
  d.assert(videos().every(v => v.paused && v.dataset.active === 'false'), 'Clear left visible media');

  d.set('travel-duration', '.25'); d.set('burn-duration', '.3'); d.click('restart');
  await d.until(() => d.phase() === 'looping', 'Auto-expiry run did not reach loop');
  d.click('pause'); await d.wait(400);
  d.assert(video('looping').loop, 'Auto-expiry counted paused wall time');
  d.click('pause');
  await d.until(() => !video('looping').loop, 'Burn timer did not request Close');
  await d.until(() => d.phase() === 'closing', 'Auto-expiry did not exit at boundary');
  await d.until(() => d.phase() === 'idle', 'Auto-expiry did not clear');

  d.set('burn-duration', '0'); d.click('restart');
  await d.until(() => d.phase() === 'opening', 'Queued-close run did not open');
  d.click('stop');
  d.assert(d.$('playback-status').textContent.includes('queued'), 'Opening Close was not queued');
  await d.until(() => d.phase() === 'closing', 'Opening Close did not skip embers');
  d.set('travel-duration', '3'); d.click('restart');
  await d.until(() => d.phase() === 'flying', 'Cancel run did not fly');
  d.click('stop'); await d.wait(1800);
  d.assert(d.phase() === 'idle' && videos().every(v => v.dataset.active === 'false'), 'Flight cancel detonated later');
  d.click('restart'); d.set('palette', item.colors.find(c => c !== d.$('palette').value));
  await d.wait(100);
  d.assert(d.phase() === 'idle' && videos().every(v => v.paused), 'Palette change left a stale start');
  d.click('restart');
  const retired = videos();
  d.select(item.projectile); await d.wait(100);
  d.assert(!videos().length && retired.every(v => !v.isConnected && v.paused && !v.getAttribute('src')), 'Selection did not release all journey decoders');
  for (const id of [item.projectile, ...item.steps.map(step => step.effect)]) {
    d.select(id); document.querySelector('[data-journey-effect="fireball-journey"]').click();
    d.assert(d.$('workspace').dataset.entry === item.id, 'Component journey link failed');
  }
  d.select(item.projectile);
  return { journey: true, geometry: true, persistence: true, autoExpiry: true, transport: true, cleanup: true, downloads: 4 };
}
