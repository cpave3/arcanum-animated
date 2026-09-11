// Evaluate on a fresh viewer page after exporting the fireball collection.
async () => {
  const {viewerDriver} = await import('/tests/viewer_driver.js');
  const d = await viewerDriver();
  d.select('fireball');
  d.assert(d.$('palette').value === 'fire', 'Fireball should default to its fire palette');
  d.set('speed', '1'); d.click('primary');
  await d.until(() => d.phase() === 'playing' && d.active().currentTime > .18, 'Bolt did not start');
  const bolt = d.pixels();
  d.assert(bolt.sum > 1000, 'Incoming bolt decoded blank');
  await d.until(() => d.active().currentTime > 1.4, 'Explosion did not start');
  d.assert(d.pixels().sum > bolt.sum*3, 'Explosion did not expand beyond the bolt');
  await d.until(() => d.phase() === 'ended' && !d.active().seeking, 'One-shot did not finish');
  await d.wait(100);
  d.assert(d.pixels().maximum === 0, 'One-shot did not fade to transparent');
  d.select('fireball-sequence'); d.set('palette', 'necrotic');
  const links = [...d.$('downloads').querySelectorAll('[data-download="webm"]')];
  d.assert(links.length === 3 && links.every(a => a.href.includes('/necrotic.webm')), 'Sequence downloads mismatch');
  d.set('speed', '2'); d.click('primary');
  await d.until(() => d.phase() === 'looping' && d.active().currentTime > .2, 'Impact did not settle into embers');
  const embers = d.pixels();
  d.assert(embers.sum > 1000, 'Persistent ground decoded blank');
  await d.wait(300);
  d.assert(d.pixels().signature !== embers.signature, 'Embers are not animated');
  const video = d.active(); let last = video.currentTime, wrapped = false;
  const observe = () => { if (video.currentTime < last) wrapped = true; last = video.currentTime; };
  video.addEventListener('timeupdate', observe);
  await d.until(() => wrapped, 'Embers did not loop');
  video.removeEventListener('timeupdate', observe);
  d.click('stop');
  await d.until(() => d.phase() === 'closing', 'Embers did not begin cooling');
  await d.until(() => d.phase() === 'idle', 'Cooling did not finish');
  d.assert(!d.active(), 'Finished sequence did not clear the stage');
  return {visibleBolt:true, expandingBlast:true, transparentEnding:true, animatedEmbers:true, sustainedLoop:true, closing:true};
}
