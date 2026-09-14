// Foundry Script macro (top-level await). Select exactly one token; Sequencer required.
// Playback getters / attachTo / hooks checked against Sequencer source, not live Foundry.
// https://github.com/fantasycalendar/FoundryVTT-Sequencer/blob/master/src/canvas-effects/canvas-effect.js
// https://fantasycomputer.works/FoundryVTT-Sequencer/api/effect.html
// Burst cue: celestial-revelation frame 81 / 30 fps. Network lighting is best-effort sync.
const BASE = "assets/animations";
const SIZE = 6; // Full clip width in grid squares, independent of token size.
const BURST_SECONDS = 2.7;
const COLORS = { radiant: "#ffd45c", divine: "#fff0c2", necrotic: "#66ffd0" };
const FLAG = "celestialRevelation";
const NS = "my-animations.celestial-revelation.v1";
if (
  typeof Sequencer === "undefined" ||
  typeof Sequence === "undefined" ||
  !canvas.scene
) {
  ui.notifications.error(
    "Celestial Revelation requires Sequencer and an active scene.",
  );
  return;
}
if (canvas.tokens.controlled.length !== 1) {
  ui.notifications.warn("Select exactly one token for Celestial Revelation.");
  return;
}
if (!Number.isFinite(SIZE) || SIZE <= 0) {
  ui.notifications.error("Celestial Revelation: SIZE must be positive.");
  return;
}
const token = canvas.tokens.controlled[0];
const doc = token.document;
const scene = canvas.scene;
const sceneId = scene.id;
const prefix = `${NS}.${doc.id}.`;
const controllers = (globalThis[Symbol.for(`${NS}.controllers`)] ??= new Map());
if (controllers.has(doc.uuid)) {
  controllers.get(doc.uuid).dialog.render(true);
  return;
}
const state = {
  epoch: 0,
  busy: false,
  clearing: false,
  root: null,
  dismissed: false,
};
const stored = () => doc.getFlag("world", FLAG);
const exists = () => scene.tokens.get(doc.id) === doc;
const current = () => canvas.scene?.id === sceneId && exists();
const report = (error) =>
  ui.notifications.error(`Celestial Revelation: ${error.message || error}`);
const effects = () =>
  Sequencer.EffectManager.getEffects({ name: `${prefix}*`, sceneId }).filter(
    (e) => e.data.sceneId === sceneId && e.data.name.startsWith(prefix),
  );
let writes = Promise.resolve();
function write(work) {
  const operation = writes.then(work);
  writes = operation.catch(() => undefined);
  return operation;
}
async function endEffects(name) {
  const list = effects().filter((e) => !name || e.data.name === name);
  if (list.some((e) => !e.userCanDelete))
    throw new Error(
      "Cannot remove this animation. Ask a GM or check Sequencer delete permissions.",
    );
  if (list.length)
    await Sequencer.EffectManager.endEffects({
      effects: list.map((e) => e.id),
      sceneId,
    });
}
async function restore(castId) {
  return write(async () => {
    if (!exists()) return;
    const saved = stored();
    if (!saved || (castId && saved.castId !== castId)) return;
    if (saved.version !== 1 || !saved.original)
      throw new Error(
        "Unrecognized saved lighting. Ask a GM to inspect the token's world.celestialRevelation flag.",
      );
    // Restore and remove the backup in one document update; failure keeps recovery available.
    await doc.update({
      light: saved.original,
      [`flags.world.-=${FLAG}`]: null,
    });
  });
}
function refresh() {
  if (!state.root) return;
  const saved = stored();
  state.root.querySelector("[data-token]").textContent = doc.name;
  state.root.querySelector("[data-status]").textContent = !current()
    ? "Scene changed or token removed — reopen controls."
    : state.clearing
      ? "Clearing…"
      : state.busy
        ? "Revealing…"
        : saved
          ? `${saved.status === "active" ? "Active" : "Interrupted — Clear to reset"} (${saved.palette})`
          : "Inactive";
  const palette = state.root.querySelector('[name="palette"]');
  if (saved && Object.hasOwn(COLORS, saved.palette))
    palette.value = saved.palette;
  palette.disabled = !!saved || state.busy || state.clearing;
  state.root.querySelector('[data-action="activate"]').disabled =
    !current() || !!saved || state.busy || state.clearing;
  state.root.querySelector('[data-action="clear"]').disabled =
    !current() ||
    state.clearing ||
    (!saved && !state.busy && !effects().length);
}
async function activate(palette) {
  if (stored())
    throw new Error("Clear the existing revelation before activating again.");
  if (!Object.hasOwn(COLORS, palette))
    throw new Error("Choose Divine, Radiant, or Necrotic.");
  const epoch = state.epoch;
  const castId = foundry.utils.randomID();
  const name = `${prefix}${castId}`;
  const valid = () => current() && epoch === state.epoch;
  const file = `${BASE}/celestial-revelation/${palette}.webm`;
  await Sequencer.Preloader.preload([file]);
  if (!valid()) return;
  await write(async () => {
    if (!valid()) return;
    if (stored())
      throw new Error("A revelation is already stored on this token.");
    await doc.update({
      [`flags.world.${FLAG}`]: {
        version: 1,
        castId,
        palette,
        status: "charging",
        original: doc.light.toObject(),
      },
    });
  });
  if (!valid()) {
    await restore(castId);
    return;
  }
  let cancelled = false;
  const alive = () => !cancelled && valid() && stored()?.castId === castId;
  let playbackError,
    playbackDone = false,
    seen = false,
    lit = false;
  const pre = Hooks.on("preCreateSequencerEffect", (data) => {
    if (data.name === name && (!alive() || data.sceneId !== sceneId))
      return false;
  });
  const created = Hooks.on("createSequencerEffect", (effect) => {
    if (effect.data.name === name)
      queueMicrotask(() => {
        if (!alive()) void endEffects(name).catch(report);
      });
  });
  // Keep guards until the play operation settles, including delayed creation after Clear.
  const play = (async () => {
    try {
      await new Sequence()
        .effect()
        .file(file)
        .name(name)
        .attachTo(token)
        .size(SIZE * canvas.grid.size)
        .belowTokens(false)
        .duration(5000)
        .waitUntilFinished()
        .play();
    } catch (error) {
      playbackError = error;
    } finally {
      playbackDone = true;
      Hooks.off("preCreateSequencerEffect", pre);
      Hooks.off("createSequencerEffect", created);
    }
  })();
  try {
    const deadline = Date.now() + 20000;
    while (alive()) {
      if (playbackError) throw playbackError;
      const effect = effects().find((e) => e.data.name === name);
      seen ||= !!effect;
      if (
        effect?.mediaIsPlaying &&
        Number.isFinite(effect.mediaCurrentTime) &&
        effect.mediaCurrentTime >= BURST_SECONDS
      ) {
        await write(async () => {
          if (!alive()) return;
          await doc.update({
            "light.bright": 10,
            "light.dim": 20,
            "light.color": COLORS[palette],
            "light.alpha": 0.25,
            "light.angle": 360,
            "light.luminosity": 0.5,
            "light.animation.type": "pulse",
            "light.darkness.min": 0,
            "light.darkness.max": 1,
            [`flags.world.${FLAG}.status`]: "active",
          });
          lit = true;
        });
        break;
      }
      if (playbackDone || (seen && !effect))
        throw new Error(
          "Animation ended before its burst; lighting was not applied. Check the asset and Sequencer permissions.",
        );
      if (Date.now() >= deadline)
        throw new Error(
          "Could not read the burst playback cue. Check the asset and Sequencer version; lighting was not applied.",
        );
      await new Promise((resolve) => setTimeout(resolve, 16));
    }
    if (!alive()) {
      await endEffects(name);
      await restore(castId);
      return;
    }
    await play;
    if (playbackError) throw playbackError;
    if (!lit) await restore(castId);
  } catch (error) {
    cancelled = true;
    const failures = [error.message || error];
    try {
      await endEffects(name);
    } catch (cleanup) {
      failures.push(cleanup.message || cleanup);
    }
    try {
      await restore(castId);
    } catch (cleanup) {
      failures.push(cleanup.message || cleanup);
    }
    throw new Error(failures.join("; "));
  }
}
async function action(name) {
  if (!current()) {
    ui.notifications.warn(
      "Scene changed or token removed; reopen Celestial Revelation controls.",
    );
    return;
  }
  if (!doc.isOwner) {
    ui.notifications.error(
      "You need permission to update this token's lighting.",
    );
    return;
  }
  if (state.clearing || (state.busy && name !== "clear")) return;
  if (name === "clear") {
    state.clearing = true;
    ++state.epoch;
  } else state.busy = true;
  refresh();
  try {
    if (name === "clear") {
      const results = await Promise.allSettled([endEffects(), restore()]);
      const failures = results.filter((r) => r.status === "rejected");
      if (failures.length)
        throw new Error(
          failures.map((r) => r.reason.message || r.reason).join("; "),
        );
    } else await activate(state.root.querySelector('[name="palette"]').value);
  } catch (error) {
    report(error);
  } finally {
    if (name === "clear") state.clearing = false;
    else state.busy = false;
    refresh();
    if (state.dismissed && !state.busy && !state.clearing)
      controllers.delete(doc.uuid);
  }
}
state.dialog = new Dialog(
  {
    title: "Celestial Revelation",
    content: `<p>Token: <strong data-token></strong></p>
    <label>Color <select name="palette">${Object.keys(COLORS)
      .map(
        (p) =>
          `<option value="${p}">${p[0].toUpperCase() + p.slice(1)}</option>`,
      )
      .join("")}</select></label>
    <p data-status></p><p>10 ft bright + 10ft dim light at the burst. Clear restores the previous lighting.</p>
    <button type="button" data-action="activate">Activate</button>
    <button type="button" data-action="clear">Clear</button>`,
    buttons: {},
    render: (html) => {
      state.dismissed = false;
      state.root = html[0];
      for (const button of state.root.querySelectorAll("[data-action]"))
        button.addEventListener("click", () => {
          void action(button.dataset.action);
        });
      refresh();
    },
    close: () => {
      state.root = null;
      state.dismissed = true;
      if (!state.busy && !state.clearing) controllers.delete(doc.uuid);
    },
  },
  { width: 390 },
);
controllers.set(doc.uuid, state);
state.dialog.render(true);
