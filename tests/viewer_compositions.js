async () => {
  // Public entry points: library selection, transport and position controls.
  // Outcomes: decoded independent bursts, native timing, geometry and clean cancellation.
  const {viewerDriver} = await import('/tests/viewer_driver.js');
  const d = await viewerDriver();
  const videos = () => [...document.querySelectorAll('[data-composition-track]')];
  const visible = role => videos().filter(v => v.dataset.role === role && v.dataset.active === 'true');
  const settled = () => videos().every(v => v.readyState >= 2 && !v.seeking);
  const time = () => Number(d.$('seek').value);
  const canvas = document.createElement('canvas');
  const context = canvas.getContext('2d', {willReadFrequently: true});
  function peak(video, x = 0, y = 0, width = 1, height = 1) {
    d.assert(video?.videoWidth, 'Track has no decoded frame');
    canvas.width = video.videoWidth; canvas.height = video.videoHeight;
    context.drawImage(video, 0, 0);
    const data = context.getImageData(Math.floor(x * canvas.width), Math.floor(y * canvas.height),
      Math.max(1, Math.floor(width * canvas.width)), Math.max(1, Math.floor(height * canvas.height))).data;
    let maximum = 0;
    for (let i = 3; i < data.length; i += 4) maximum = Math.max(maximum, data[i]);
    return maximum;
  }
  async function seek(value) {
    d.set('seek', String(value), 'input');
    await d.until(() => ['playing', 'ended'].includes(d.phase()) && settled() && Math.abs(time() - value) < .002,
      `Composition seek to ${value} did not settle`);
    await d.wait(80);
  }
  function geometry() {
    const beam = videos().find(v => v.dataset.role === 'beam');
    const caster = videos().find(v => v.dataset.role === 'caster');
    const target = videos().find(v => v.dataset.role === 'target');
    const from = d.$('composition-scene').querySelector('[data-token="from"]').getBoundingClientRect();
    const to = d.$('composition-scene').querySelector('[data-token="to"]').getBoundingClientRect();
    const dx = to.x + to.width / 2 - from.x - from.width / 2;
    const dy = to.y + to.height / 2 - from.y - from.height / 2;
    const matrix = new DOMMatrix(getComputedStyle(beam).transform);
    d.assert(Math.abs(parseFloat(beam.style.width) - Math.hypot(dx, dy)) < 1, 'Beam does not bridge token centers');
    d.assert(Math.abs(Math.atan2(matrix.b, matrix.a) - Math.atan2(dy, dx)) < .001, 'Beam angle does not follow endpoints');
    for (const endpoint of [caster, target]) {
      const rect = endpoint.getBoundingClientRect();
      d.assert(Math.abs(rect.width - rect.height) < .1, 'Endpoint layer was stretched');
      d.assert(Math.abs(rect.height - parseFloat(beam.style.height)) < .1, 'Beam native height differs from endpoint size');
    }
    d.assert(Math.abs(caster.getBoundingClientRect().x + caster.getBoundingClientRect().width / 2 - from.x - from.width / 2) < 1, 'Caster not centered on From');
    d.assert(Math.abs(target.getBoundingClientRect().y + target.getBoundingClientRect().height / 2 - to.y - to.height / 2) < 1, 'Impact not centered on To');
    return {width: parseFloat(beam.style.width), height: parseFloat(beam.style.height)};
  }

  d.assert(d.catalog.compositions?.length === 3, 'Export the three compositions before running this test');
  document.querySelector('[data-kind="composition"]').click();
  d.assert(document.querySelectorAll('.library-item').length === 3, 'Composition filter is incomplete');
  for (const count of [1, 2, 3]) {
    const item = d.catalog.compositions.find(item => item.id === `ray-composition-${count}`);
    d.select(item.id);
    d.assert(d.phase() === 'idle' && videos().every(v => v.paused), 'Selection autoplayed');
    d.assert(videos().length === item.tracks.length && visible('target').length === 0, 'Wrong independent track allocation');
    d.assert(!d.$('composition-poster').hidden && d.$('composition-poster').src.includes(`/ray-cast-${count}/`), 'Poster is not the caster');
    const color = item.colors.includes('eldritch') ? 'eldritch' : item.colors[0];
    d.set('palette', color);
    d.assert(videos().every(v => new URL(v.src).pathname.endsWith(`/${color}.webm`)), 'Tracks use mixed palettes');
    const downloads = [...d.$('downloads').querySelectorAll('[data-download="webm"]')];
    d.assert(downloads.length === 3 && d.$('downloads').querySelectorAll('[data-download="poster"]').length === 3, 'Missing component downloads');
    const paths = d.$('path-field').value.split(' → ');
    d.assert(paths.length === 3 && new Set(paths).size === 3 && paths.every(path => path.endsWith(`/${color}.webm`) && !path.includes('?')), 'Copy paths must contain three unique palette-matched components');
    for (const link of downloads) d.assert((await fetch(link.href)).ok, `Download unavailable: ${link.href}`);

    const beamTracks = item.tracks.filter(track => track.role === 'beam');
    const targetTracks = item.tracks.filter(track => track.role === 'target');
    for (const [index, track] of beamTracks.entries()) {
      await seek(track.start - .005);
      d.assert(!visible('beam').length, 'Beam started before release');
      await seek(track.start + .15);
      const beam = visible('beam')[0];
      d.assert(beam && Math.abs(beam.currentTime - .15) < .025, 'Beam lost native clip timing');
      for (const x of [.2, .5, .8]) d.assert(peak(beam, x, .45, .04, .1) > 15, 'Decoded beam does not bridge the centerline');
      const targetTrack = targetTracks[index];
      const target = videos()[item.tracks.indexOf(targetTrack)];
      await seek(targetTrack.start + .005);
      d.assert(peak(target) < 5, 'Target frame zero should be transparent');
      await seek(targetTrack.start + .05);
      d.assert(peak(target, .35, .35, .3, .3) > 30, 'Decoded impact missed its cue');
    }
    if (count > 1) {
      await seek(targetTracks.at(-1).start + .08);
      d.assert(visible('target').length === count, 'Impact tails did not overlap independently');
      d.assert(new Set(visible('target').map(v => v.currentTime.toFixed(2))).size === count, 'Overlapping impacts reused one timeline');
      d.assert(visible('target').every(v => peak(v) > 0), 'An overlapping impact has no decoded pixels');
    }
  }

  const item = d.catalog.compositions.find(item => item.id === 'ray-composition-3');
  d.set('speed', '0.5'); d.click('restart');
  const playedBeams = new Set();
  await d.until(() => {
    for (const video of visible('beam')) {
      if (video.readyState >= 2 && !video.seeking && peak(video, .45, .45, .1, .1) > 15) {
        playedBeams.add(video.dataset.compositionTrack);
      }
    }
    return d.phase() === 'ended';
  }, 'Natural composition playback did not finish');
  d.assert(playedBeams.size === 3, 'Not all three beams visibly played on the shared clock');
  await seek(.55);
  const original = geometry();
  d.set('to-x', '60', 'input');
  const shorter = geometry();
  d.assert(shorter.width < original.width && shorter.height === original.height, 'Distance changed beam thickness');
  d.set('to-y', '75', 'input'); d.set('from-y', '30', 'input');
  geometry();
  d.assert(Math.abs(visible('beam')[0].currentTime - .15) < .025, 'Geometry changed travel time');
  d.assert(peak(visible('beam')[0], .5, .45, .1, .1) > 15, 'Angled beam lost its decoded frame');
  d.click('reset-positions');
  d.assert(Math.abs(geometry().width - original.width) < 1, 'Position reset failed');

  d.set('speed', '0.5'); d.click('restart');
  await d.until(() => d.phase() === 'playing' && time() > .12, 'Composition failed to start');
  d.assert(settled(), 'Clock started before tracks were decoded');
  d.click('pause');
  const pausedTime = time();
  await d.wait(180);
  d.assert(time() === pausedTime && videos().every(v => v.paused), 'Pause did not freeze the shared clock');
  d.assert(videos().every(v => getComputedStyle(v).display !== 'none'), 'Paused transparent media left layout');
  d.set('speed', '2'); d.click('pause');
  const resumedTime = time();
  await d.wait(180);
  d.assert(time() - resumedTime > .22 && videos().every(v => v.playbackRate === 2), 'Resume/speed did not advance the shared timeline');
  d.click('restart');
  await d.until(() => d.phase() === 'playing' && time() < .15, 'Restart did not reset the clock');
  await seek(.9);
  d.assert(d.$('pause').textContent === 'Resume' && videos().every(v => v.paused), 'Seeking must pause every track');
  d.click('pause');
  const duration = Math.max(item.duration, ...item.tracks.map(track => track.start + d.catalog.effects.find(effect => effect.id === track.effect).duration));
  await d.until(() => d.phase() === 'ended', 'Composition did not finish after impact tails');
  d.assert(Math.abs(time() - duration) < .002 && !videos().some(v => v.dataset.active === 'true'), 'End time clipped the last tail or left an afterimage');
  d.click('stop');
  d.assert(d.phase() === 'idle' && time() === 0, 'Stop did not return to ready');

  d.click('primary');
  d.set('palette', item.colors.find(color => color !== d.$('palette').value));
  await d.wait(150);
  d.assert(d.phase() === 'idle' && videos().every(v => v.paused), 'Palette change left a stale start job');
  d.click('primary'); d.set('seek', '.8', 'input'); d.select('ray-hit');
  await d.wait(150);
  d.assert(d.phase() === 'idle' && videos().length === 0 && document.querySelectorAll('video').length === 5, 'Selection did not cancel jobs and clean up tracks');
  document.querySelector('[data-composed-effect="ray-composition-3"]').click();
  d.assert(d.$('workspace').dataset.entry === item.id && d.phase() === 'idle', 'Component-to-composition navigation failed');
  d.select('ray-hit');
  return {compositions: 3, decodedBeamAndImpact: true, overlap: true, geometry: true, transport: true, cancellation: true, componentDownloads: true};
}
