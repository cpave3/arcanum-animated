// Run in Firefox and Chromium, including short/narrow viewports.
async () => {
  const {viewerDriver} = await import('/tests/viewer_driver.js');
  const d = await viewerDriver();
  d.set('speed','1');
  function visibleSignature() {
    const v=d.active(),rect=v.getBoundingClientRect(),style=getComputedStyle(v);
    d.assert(rect.width>0 && rect.top>=0 && rect.bottom<=innerHeight && rect.left>=0 && rect.right<=innerWidth,'Transition is outside the viewport');
    d.assert(style.display!=='none' && style.visibility==='visible' && Number(style.opacity)===1,'Transition is visually hidden');
    const pixels=d.pixels();d.assert(pixels.sum>1000,'Transition has a blank decoded frame');return pixels.signature;
  }
  async function motion(phase) {
    await d.until(()=>d.phase()===phase && d.active().currentTime>.45,`${phase} did not start`);
    await d.wait(50);const first=visibleSignature();
    await d.until(()=>d.active().currentTime>1.15,`${phase} stopped advancing`);
    await d.wait(50);d.assert(d.phase()===phase && visibleSignature()!==first,`${phase} did not visibly animate`);
  }
  for(const sequence of d.catalog.sequences.filter(s=>s.colors.length)) {
    d.select(sequence.id);d.click('primary');await motion('opening');
    await d.until(()=>d.phase()==='looping','Steady loop missing');d.click('stop');await motion('closing');
    await d.until(()=>d.phase()==='idle','Closing did not finish');
  }
  return {openingFramesVisible:true,closingFramesVisible:true};
}
