async () => {
  const {viewerDriver} = await import('/tests/viewer_driver.js');
  const d = await viewerDriver();
  d.set('speed','2');
  for (const sequence of d.catalog.sequences.filter(s=>s.colors.length)) {
    d.select(sequence.id); d.set('palette','necrotic');
    d.assert(d.phase()==='idle' && !d.active() && d.$('poster').hidden, 'Sequence must start empty');
    d.assert(d.$('phase-strip').children.length===3, 'Sequence phases are missing');
    d.click('primary');
    await d.until(()=>d.phase()==='opening' && d.active().currentTime>0, 'Opening failed');
    d.assert(new URL(d.active().src).pathname.endsWith(`/${sequence.steps[0].effect}/necrotic.webm`), 'Wrong opening clip');
    await d.until(()=>d.phase()==='looping', 'Sequence failed to enter loop');
    const loop=d.active(); let last=loop.currentTime,wrapped=false;
    const observe=()=>{if(loop.currentTime<last)wrapped=true;last=loop.currentTime;};
    loop.addEventListener('timeupdate',observe);
    await d.until(()=>wrapped,'Steady clip did not repeat');
    loop.removeEventListener('timeupdate',observe);
    d.click('stop');
    d.assert(!loop.loop,'Close must exit at the next loop boundary');
    await d.until(()=>d.phase()==='closing','Closing failed');
    d.assert(new URL(d.active().src).pathname.endsWith(`/${sequence.steps[2].effect}/necrotic.webm`),'Wrong closing clip');
    await d.until(()=>d.phase()==='idle','Closing did not finish');
    d.assert(!d.active(),'Completed sequence must leave the stage empty');
  }
  d.select('vortex-sequence');
  const seen=[]; const observer=new MutationObserver(()=>seen.push(d.phase()));
  observer.observe(d.$('stage'),{attributes:true,attributeFilter:['data-phase']});
  d.click('primary');
  await d.until(()=>d.phase()==='opening' && !d.active().paused,'Early-stop opening failed');
  d.click('pause'); const held=d.active().currentTime;
  d.click('stop');
  await d.wait(100);
  d.assert(d.active().paused && Math.abs(d.active().currentTime-held)<.03,'Queued close ignored pause');
  d.click('pause');
  await d.until(()=>d.phase()==='closing','Queued close failed');
  await d.until(()=>d.phase()==='idle','Queued close did not finish');
  observer.disconnect(); d.assert(!seen.includes('looping'),'Early close should skip looping');
  d.click('primary');d.click('stop'); await d.wait(100);
  d.assert(d.phase()==='idle','Loading cancellation leaked a stale transition');
  d.click('primary'); await d.until(()=>d.phase()==='opening','Restart failed');
  d.select('rift'); await d.wait(100);
  d.assert(d.phase()==='idle' && !d.active(),'Selection change did not cancel the old sequence');
  return {sequences:true,sustainedLoops:true,boundaryClose:true,earlyClose:true,pauseResume:true,cancellation:true};
}
