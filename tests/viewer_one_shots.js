async () => {
  const {viewerDriver} = await import('/tests/viewer_driver.js');
  const d = await viewerDriver();
  const holds = new Set(d.catalog.sequences.map(s=>s.steps[0].effect));
  d.set('speed','2');
  let checked = 0;
  for (const effect of d.catalog.effects.filter(e=>e.kind==='one-shot' && Object.keys(e.variants).length)) {
    d.select(effect.id);
    d.assert(!d.$('poster').hidden && !d.active(), 'Single clips must start with a poster, not autoplay');
    d.click('primary');
    await d.until(()=>d.phase()==='playing' && d.active()?.currentTime>0, `${effect.id} did not play`);
    await d.until(()=>d.phase()==='ended' && !d.active().seeking, `${effect.id} did not finish`);
    await d.wait(100);
    d.assert(d.pixels().maximum === (holds.has(effect.id)?255:0), `${effect.id} has wrong final alpha`);
    d.set('background','light');
    d.assert(d.phase()==='ended', 'Stage settings restarted a finished clip');
    checked++;
  }
  d.select('teleport-arrival'); d.set('speed','1'); d.click('primary');
  await d.until(()=>d.phase()==='playing' && d.active().currentTime>.2, 'Arrival failed to start');
  d.click('pause'); const time=d.active().currentTime;
  await d.wait(150);
  d.assert(d.active().paused && Math.abs(d.active().currentTime-time)<.03, 'Pause did not hold the frame');
  d.click('pause');
  await d.until(()=>d.phase()==='ended', 'Resume failed');
  d.click('primary');
  await d.until(()=>d.phase()==='playing' && d.active().currentTime>.1, 'Replay failed');
  d.set('palette','psychic');
  d.assert(d.phase()==='idle' && !d.$('poster').hidden && !d.active(), 'Palette change must reset to the poster');
  d.assert(new URL(d.$('poster').src).pathname.endsWith('/psychic.png'), 'Poster color mismatch');
  return {oneShotsChecked:checked,endpoints:true,pauseResume:true,replay:true,paletteReset:true};
}
