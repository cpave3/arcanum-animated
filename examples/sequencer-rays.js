// Foundry Script macro; requires Sequencer and regenerated 384px VTT ray assets.
// API checked against Sequencer source; not run in Foundry.
const BASE = "assets/animations"; // Relative to Foundry Data; no leading slash.
const color = "fire"; // Any exported palette, e.g. "eldritch".
const beamCount = 3; // 1, 2, or 3.
const impactMask = Array(beamCount).fill(true); // Per beam, e.g. [true, false, true].
const caster = canvas.tokens.controlled[0];
const targets = Array.from(game.user.targets); // Or supply an ordered Token list.

if (!Number.isInteger(beamCount) || beamCount < 1 || beamCount > 3) {
  throw new Error("Set beamCount to 1, 2, or 3.");
}
if (impactMask.length !== beamCount || impactMask.some(hit => typeof hit !== "boolean")) {
  throw new Error("Supply one boolean impactMask entry per beam.");
}
if (canvas.tokens.controlled.length !== 1) {
  throw new Error("Select exactly one caster token.");
}
if (!targets.length) {
  throw new Error("Target at least one token.");
}

// Visual preview only: make your own rolls and set impactMask from their results.
const frameMs = 1000 / 30;
const releaseFrames = [12, 22, 32].slice(0, beamCount);
const casterFile = `${BASE}/ray-cast-${beamCount}/${color}.webm`;
const beamFile = `${BASE}/ray-beam/${color}.webm`;
const hitFile = `${BASE}/ray-hit/${color}.webm`;
const seq = new Sequence();

seq.effect().file(casterFile).atLocation(caster).scaleToObject(3);

for (let i = 0; i < beamCount; i++) {
  const target = targets[i % targets.length];
  const hit = impactMask[i];

  // Sequencer supplies the left-center anchor; only the length follows distance.
  seq.effect()
    .file(beamFile)
    .atLocation(caster)
    .stretchTo(target, { onlyX: true })
    .scale({ x: 1, y: canvas.grid.size * 3 / 384 })
    .delay(releaseFrames[i] * 1000 / 30);

  // Blank hit frame 0 precedes its frame-1 impact, aligned with beam frame 4.
  seq.effect()
    .file(hitFile)
    .atLocation(target)
    .scaleToObject(3)
    .delay((releaseFrames[i] + 4 - 1) * frameMs)
    .playIf(hit);
}

// No waits: all delays share the sequence start and impact tails can overlap.
await seq.play({ preload: true });
