import { PreviewPlayer } from './player.js';
import { CompositionPlayer } from './composition-player.js';
import { JourneyPlayer } from './journey-player.js';

const $ = id => document.getElementById(id);
const kindLabel = { 'token-effect': 'Token effect', loop: 'Loop', 'one-shot': 'One-shot', sequence: 'Sequence', composition: 'Composition', journey: 'Journey' };
const categoryFor = item => item.tags.includes('token') ? 'token-effect' : item.kind;
const phaseLabel = { flying: 'Flight', opening: 'Open', looping: 'Loop', closing: 'Close', playing: 'Clip' };
const bytes = value => `${Math.round(value / 1024)} KiB`;
const seconds = value => `${Number(value).toFixed(1)}s`;
const catalogURL = new URL('../assets/catalog.json', import.meta.url);

function element(tag, className, text) {
  const node = document.createElement(tag);
  if (className) node.className = className;
  if (text !== undefined) node.textContent = text;
  return node;
}

async function initialize() {
  const response = await fetch(catalogURL, { cache: 'no-store' });
  if (!response.ok) throw new Error(`Catalog unavailable (${response.status}). Run python3 render.py --catalog-only, then refresh.`);
  const catalog = await response.json();
  if (catalog.schema !== 1 || !Array.isArray(catalog.effects) || !Array.isArray(catalog.sequences) || !Array.isArray(catalog.palettes)) {
    throw new Error('Invalid viewer catalog. Rebuild it with python3 render.py --catalog-only.');
  }
  const effects = new Map(catalog.effects.map(effect => [effect.id, effect]));
  const compositions = catalog.compositions || [];
  const journeys = catalog.journeys || [];
  const entries = [...catalog.effects, ...catalog.sequences, ...compositions, ...journeys];
  const colors = item => ['sequence', 'composition', 'journey'].includes(item.kind) ? item.colors : Object.keys(item.variants);
  const preferences = new Map();
  let selected = null;
  let selectedColor = null;
  let filter = 'all';
  let paths = [];
  let overlays = [];

  function assetURL(variant, type) {
    const url = new URL(variant[type], catalogURL);
    if (url.origin !== location.origin || !url.pathname.startsWith(new URL('.', catalogURL).pathname)) {
      throw new Error('Catalog contains an asset outside its collection folder.');
    }
    url.searchParams.set('v', variant.version);
    return url.href;
  }

  function colorFor(item) {
    const available = colors(item);
    const preferred = preferences.get(item.id) || item.default_color;
    return available.includes(preferred) ? preferred : available[0];
  }

  function stepsFor(item) {
    if (item.kind === 'journey') return [{ phase: 'flying', effect: effects.get(item.projectile) },
      ...item.steps.map(step => ({ ...step, effect: effects.get(step.effect) }))];
    if (item.kind === 'composition') return [...new Map(item.tracks.map(track =>
      [track.effect, { ...track, effect: effects.get(track.effect) }])).values()];
    return item.kind === 'sequence' ? item.steps.map(step => ({ ...step, effect: effects.get(step.effect) }))
      : [{ phase: item.kind === 'loop' ? 'looping' : 'playing', effect: item }];
  }

  function specFor(item, color) {
    if (item.kind === 'journey') {
      const [projectile, ...steps] = stepsFor(item).map(step => ({ ...step, url: assetURL(step.effect.variants[color], 'webm') }));
      return { kind: 'journey', projectile, steps, poster: assetURL(projectile.effect.variants[color], 'poster') };
    }
    if (item.kind === 'composition') {
      const tracks = item.tracks.map(track => {
        const effect = effects.get(track.effect);
        return { ...track, effect, url: assetURL(effect.variants[color], 'webm') };
      });
      return { kind: item.kind, tracks,
        duration: Math.max(item.duration, ...tracks.map(track => track.start + track.effect.duration)),
        poster: assetURL(tracks.find(track => track.role === 'caster').effect.variants[color], 'poster') };
    }
    const steps = stepsFor(item).map(step => ({ ...step,
      url: assetURL(step.effect.variants[color], 'webm') }));
    const posterEffect = item.kind === 'sequence' ? steps[1].effect : item;
    return { kind: item.kind, steps, poster: assetURL(posterEffect.variants[color], 'poster') };
  }

  function fillPalettes(select, available, value) {
    select.replaceChildren();
    const groups = new Map();
    for (const palette of catalog.palettes) {
      if (!available.includes(palette.id)) continue;
      if (!groups.has(palette.group)) {
        const group = document.createElement('optgroup'); group.label = palette.group;
        groups.set(palette.group, group); select.append(group);
      }
      const option = new Option(palette.label, palette.id);
      groups.get(palette.group).append(option);
    }
    select.disabled = available.length === 0;
    if (value) select.value = value;
  }

  function notice(message) {
    $('catalog-state').hidden = false;
    $('catalog-state').dataset.state = 'error';
    $('catalog-state').setAttribute('role', 'alert');
    $('catalog-state').textContent = message;
  }

  function updateTime(state) {
    $('time').value = `${seconds(state.time)} / ${seconds(state.duration)}`;
    $('seek').max = state.duration || 1;
    $('seek').step = selected?.fps ? 1 / selected.fps : .001;
    if (document.activeElement !== $('seek')) $('seek').value = state.time;
  }

  function updateTransport(state) {
    const available = selected && colors(selected).length > 0;
    const active = ['loading', 'flying', 'opening', 'looping', 'closing', 'playing'].includes(state.phase);
    $('stage').dataset.phase = state.phase;
    $('primary').textContent = state.phase === 'error' ? 'Retry' : ['sequence', 'journey'].includes(selected?.kind) ? 'Start' : state.phase === 'ended' ? 'Replay' : 'Play';
    $('primary').disabled = !available || active;
    $('pause').disabled = !available || state.active < 0 || state.phase === 'ended';
    $('pause').textContent = state.paused ? 'Resume' : 'Pause';
    $('stop').disabled = !available || (!active && state.phase !== 'ended') || state.phase === 'closing' || (['sequence', 'journey'].includes(selected?.kind) && !state.wanted && active);
    $('stop').textContent = ['sequence', 'journey'].includes(selected?.kind) ? 'Close' : 'Stop';
    $('restart').disabled = !available;
    $('seek').disabled = !available || ['sequence', 'journey'].includes(selected?.kind) || state.phase === 'loading' || state.phase === 'error';
    let label = { idle: 'Ready', loading: 'Loading…', flying: 'Flying', opening: 'Opening', looping: 'Looping',
      closing: 'Closing', playing: 'Playing', ended: 'Finished · replay to watch again', error: state.error }[state.phase];
    if (['sequence', 'journey'].includes(selected?.kind) && !state.wanted && state.phase === 'opening') label = 'Opening · close queued';
    if (['sequence', 'journey'].includes(selected?.kind) && !state.wanted && state.phase === 'looping') label = 'Finishing loop · close queued';
    if (state.paused && active) label = `Paused · ${label}`;
    if (!selected) label = 'Select an effect';
    else if (!available) label = `Not rendered. Run python3 render.py --effect ${['sequence', 'composition', 'journey'].includes(selected.kind) ? 'all' : selected.id}`;
    $('playback-status').textContent = label;
    $('playback-status').dataset.state = state.phase;
    for (const step of $('phase-strip').children) step.dataset.active = String(step.dataset.phase === state.phase);
    syncOverlays(state);
  }

  const clipPlayer = new PreviewPlayer([...document.querySelectorAll('[data-main-slot]')], {
    poster: $('poster'), onChange: updateTransport, onTime: updateTime,
  });

  const compositionPlayer = new CompositionPlayer($('composition-scene'), {
    poster: $('composition-poster'), onChange: updateTransport, onTime: updateTime,
  });
  const journeyPlayer = new JourneyPlayer($('composition-scene'), {
    onChange: updateTransport, onTime: updateTime,
  });
  let player = clipPlayer;

  function overlaysPaused(state = player.snapshot()) {
    return state.paused || !['flying', 'opening', 'looping', 'closing', 'playing'].includes(state.phase);
  }

  function syncOverlays(state) {
    for (const layer of overlays) {
      if (layer.enabled && layer.player.active >= 0 && layer.player.paused !== overlaysPaused(state)) {
        layer.player.setPaused(overlaysPaused(state));
      }
    }
  }

  overlays = [...document.querySelectorAll('[data-overlay-side]')].map(video => {
    const layer = { side: video.dataset.overlaySide, video, enabled: false, player: null };
    layer.player = new PreviewPlayer([video], { onChange: state => {
      if (state.error) notice(`${layer.side} overlay: ${state.error}`);
      if (layer.enabled && state.active >= 0 && state.paused !== overlaysPaused()) layer.player.setPaused(overlaysPaused());
    }});
    return layer;
  });

  function configureOverlay(layer) {
    const { side, video } = layer;
    const effect = effects.get($(`overlay-${side}-style`).value);
    const color = $(`overlay-${side}-palette`).value;
    video.dataset.mirrored = String($(`overlay-${side}-mirror`).checked);
    const downloads = $(`overlay-${side}-downloads`);
    downloads.replaceChildren();
    if (effect?.variants[color]) downloads.append(downloadRow(effect, color, `${side} · ${effect.id} · ${color}`));
    const enabled = $(`overlay-${side}`).checked && !!effect?.variants[color];
    const url = enabled ? assetURL(effect.variants[color], 'webm') : null;
    if (url === layer.url && enabled === layer.enabled) return;
    layer.enabled = enabled;
    layer.url = url;
    layer.player.load(enabled ? specFor(effect, color) : null);
    layer.player.setRate(Number($('speed').value));
    if (enabled) layer.player.start();
  }

  const anchors = catalog.effects.filter(effect => effect.role === 'anchor' && effect.kind === 'loop');
  function applyOverlayMount(effect) {
    if (!effect?.mount) return;
    for (const name of ['size', 'spacing']) {
      $(`overlay-${name}`).value = effect.mount[name];
      $('scene').style.setProperty(`--overlay-${name}`, `${$(`overlay-${name}`).value}%`);
    }
  }

  function updateOverlayStyle(layer, color = null) {
    const { side } = layer;
    const effect = effects.get($(`overlay-${side}-style`).value);
    const available = effect ? colors(effect) : [];
    const palette = $(`overlay-${side}-palette`);
    const preferred = color || palette.value;
    fillPalettes(palette, available, available.includes(preferred) ? preferred : effect && colorFor(effect));
    $(`overlay-${side}-mirror`).checked = (effect?.anchor_side || 'left') !== side;
    configureOverlay(layer);
  }
  for (const layer of overlays) {
    const { side } = layer;
    const style = $(`overlay-${side}-style`);
    for (const effect of anchors) style.append(new Option(effect.title, effect.id));
    style.disabled = $(`overlay-${side}`).disabled = anchors.length === 0;
    style.addEventListener('change', () => {
      applyOverlayMount(effects.get(style.value));
      updateOverlayStyle(layer);
    });
    for (const id of [`overlay-${side}-palette`, `overlay-${side}-mirror`, `overlay-${side}`]) {
      $(id).addEventListener('change', () => configureOverlay(layer));
    }
    updateOverlayStyle(layer);
  }

  function updateCurrentMark() {
    for (const button of $('library-list').querySelectorAll('button')) {
      button.setAttribute('aria-current', String(button.dataset.entry === selected?.id));
    }
  }

  function renderLibrary() {
    const query = $('search').value.trim().toLowerCase();
    const visible = entries.filter(item => (filter === 'all' || categoryFor(item) === filter) &&
      `${item.title} ${item.id} ${item.description} ${item.tags.join(' ')}`.toLowerCase().includes(query));
    $('library-list').replaceChildren();
    for (const item of visible) {
      const row = element('li');
      const button = element('button', 'library-item'); button.type = 'button'; button.dataset.entry = item.id;
      const color = colorFor(item);
      if (color) {
        const preview = item.kind === 'composition' ? effects.get(item.tracks.find(track => track.role === 'caster').effect)
          : item.kind === 'journey' ? effects.get(item.projectile) : item.kind === 'sequence' ? effects.get(item.steps[1].effect) : item;
        const image = element('img', 'library-thumb'); image.alt = ''; image.loading = 'lazy';
        image.src = assetURL(preview.variants[color], 'poster'); button.append(image);
      } else button.append(element('span', 'library-thumb', '—'));
      const copy = element('span', 'item-copy');
      copy.append(element('span', 'item-title', item.title),
        element('span', 'item-meta', `${kindLabel[categoryFor(item)]} · ${color ? (['sequence', 'journey'].includes(item.kind) ? `${item.steps.length + (item.kind === 'journey' ? 1 : 0)} stages` : seconds(item.duration)) : 'Not rendered'}`));
      button.append(copy); row.append(button); $('library-list').append(row);
      button.addEventListener('click', () => selectEntry(item, true));
    }
    $('library-count').textContent = `${visible.length} / ${entries.length}`;
    $('empty-library').hidden = visible.length > 0;
    updateCurrentMark();
  }

  function downloadRow(effect, color, label = null) {
    const variant = effect.variants[color];
    const row = element('div', 'download-row');
    if (label) row.append(element('span', 'download-label', label));
    const webm = element('a', '', `WebM · ${bytes(variant.bytes)}`);
    webm.href = assetURL(variant, 'webm'); webm.download = `${effect.id}-${color}.webm`;
    webm.dataset.download = 'webm';
    const png = element('a', '', 'PNG'); png.href = assetURL(variant, 'poster');
    png.download = `${effect.id}-${color}.png`; png.dataset.download = 'poster';
    row.append(webm, png);
    return row;
  }

  function updateDownloads() {
    $('downloads').replaceChildren(); paths = [];
    if (selectedColor) for (const step of stepsFor(selected)) {
      const label = selected.kind === 'composition' ? `${step.role} · ${step.effect.title}` : ['sequence', 'journey'].includes(selected.kind) ? `${phaseLabel[step.phase]} · ${step.effect.title}` : null;
      $('downloads').append(downloadRow(step.effect, selectedColor, label));
      paths.push(new URL(step.effect.variants[selectedColor].webm, catalogURL).pathname.replace(/^\//, ''));
    }
    $('path-field').value = paths.join(' → ');
    $('copy-path').disabled = paths.length === 0;
    $('copy-path').textContent = paths.length > 1 ? 'Copy paths' : 'Copy path';
  }

  function updateTokenPreview() {
    const tokenEffect = selected && categoryFor(selected) === 'token-effect';
    $('token-preview-controls').hidden = !tokenEffect;
    $('token-preview').hidden = !tokenEffect || $('hide-preview-token').checked;
  }

  function updateSelection() {
    $('workspace').dataset.entry = selected.id;
    $('workspace').dataset.kind = selected.kind;
    $('workspace').dataset.category = categoryFor(selected);
    $('selection-kind').textContent = kindLabel[categoryFor(selected)];
    updateTokenPreview();
    $('selection-title').textContent = selected.title;
    $('selection-description').textContent = selected.description || (selected.kind === 'loop' ? 'A seamless loop. Press Play to preview.' : 'Plays once, then holds its final frame.');
    $('stage').setAttribute('aria-label', `${selected.title} preview`);
    $('asset-stats').replaceChildren();
    const steps = stepsFor(selected);
    const info = selected.kind === 'journey'
      ? ['Moving projectile → persistent ground', 'Close at loop boundary', 'Arrival → blank frame → flash (1/30s)']
      : selected.kind === 'composition'
      ? [seconds(selected.duration), `${selected.tracks.length} independent tracks`, 'From → To · native clip timing']
      : selected.kind === 'sequence'
      ? [steps.map(step => `${phaseLabel[step.phase]} ${seconds(step.effect.duration)}`).join(' → '), 'Close at loop boundary']
      : [`${selected.size} × ${selected.size}`, `${selected.fps} fps`, seconds(selected.duration), ...(selected.cue_time === null ? [] : [`Cue ${seconds(selected.cue_time)}`])];
    if (selectedColor) info.push(bytes(steps.reduce((sum, step) => sum + step.effect.variants[selectedColor].bytes, 0)));
    for (const text of info) $('asset-stats').append(element('span', '', text));
    $('phase-strip').replaceChildren();
    if (['sequence', 'journey'].includes(selected.kind)) for (const step of steps) {
      const node = element('li', '', `${phaseLabel[step.phase]} · ${seconds(step.effect.duration)}`);
      node.dataset.phase = step.phase; $('phase-strip').append(node);
    }
    $('palette-swatches').replaceChildren();
    for (const palette of catalog.palettes.filter(p => colors(selected).includes(p.id))) {
      const button = element('button', 'swatch'); button.type = 'button';
      button.style.setProperty('--swatch', palette.swatch); button.title = palette.label;
      button.setAttribute('aria-label', palette.label); button.setAttribute('aria-pressed', String(palette.id === selectedColor));
      button.addEventListener('click', () => setColor(palette.id)); $('palette-swatches').append(button);
    }
    $('pairing').hidden = !selected.pairing;
    $('paired-effects').replaceChildren();
    if (selected.pairing) {
      const pair = selected.pairing;
      $('pairing-cues').textContent = `${pair.event}: ${pair.times.map(seconds).join(', ')} · Direction: ${pair.direction.replace('-', ' ')}`;
      for (const id of pair.effects) {
        const partner = effects.get(id);
        const button = element('button', '', `Pair with ${partner.title}`); button.type = 'button';
        button.dataset.pairedEffect = id;
        button.addEventListener('click', () => {
          if (colors(partner).includes(selectedColor)) preferences.set(partner.id, selectedColor);
          selectEntry(partner, true);
        });
        $('paired-effects').append(button);
      }
    }
    $('composed-effects').replaceChildren();
    for (const item of [...compositions, ...journeys].filter(item => item.kind === 'journey'
      ? item.projectile === selected.id || item.steps.some(step => step.effect === selected.id)
      : item.tracks.some(track => track.effect === selected.id))) {
      const button = element('button', '', `Preview ${item.title}`); button.type = 'button';
      if (item.kind === 'journey') button.dataset.journeyEffect = item.id;
      else button.dataset.composedEffect = item.id;
      button.addEventListener('click', () => {
        if (colors(item).includes(selectedColor)) preferences.set(item.id, selectedColor);
        selectEntry(item, true);
      });
      $('composed-effects').append(button);
    }
    const mountTarget = selected.mount && entries.find(item => item.id === selected.mount.effect);
    $('preview-mount').hidden = !mountTarget;
    const mountReady = selectedColor && mountTarget && colors(mountTarget).length > 0 &&
      ['left', 'right'].every(side => colors(effects.get(selected.mount[side])).includes(selectedColor));
    $('preview-mount').disabled = !mountReady;
    $('preview-mount').title = mountReady ? '' : 'Requires both anchor files in the selected palette.';
    $('preview-mount').textContent = mountTarget ? `Preview with ${mountTarget.title}` : '';
    updateDownloads();
    const nextPlayer = selected.kind === 'journey' ? journeyPlayer : selected.kind === 'composition' ? compositionPlayer : clipPlayer;
    if (player !== nextPlayer) player.load(null);
    player = nextPlayer;
    $('composition-scene').dataset.enabled = String(['composition', 'journey'].includes(selected.kind));
    $('composition-controls').hidden = !['composition', 'journey'].includes(selected.kind);
    $('journey-controls').hidden = selected.kind !== 'journey';
    $('positions-note').textContent = selected.kind === 'journey'
      ? 'Move From and To. The projectile moves and rotates without stretching; ground stays centered on To.'
      : 'Move the tokens with these controls. Arrow keys adjust position. Distance changes beam length, not thickness or timing.';
    if (selected.kind === 'journey') {
      if ($('travel-duration').checkValidity()) journeyPlayer.setTravelDuration(Number($('travel-duration').value));
      if ($('burn-duration').checkValidity()) journeyPlayer.setBurnDuration(Number($('burn-duration').value));
    }
    player.setRate(Number($('speed').value));
    player.load(selectedColor ? specFor(selected, selectedColor) : null);
    if (['composition', 'journey'].includes(selected.kind)) {
      for (const side of ['from', 'to']) for (const axis of ['x', 'y']) player.setPosition(side, axis, Number($(`${side}-${axis}`).value));
    }
    updateCurrentMark();
  }

  function selectEntry(item, focusPreview = false) {
    if (item.kind === 'journey' && selected?.id !== item.id) $('travel-duration').value = item.travel_duration;
    selected = item; selectedColor = colorFor(item);
    fillPalettes($('palette'), colors(item), selectedColor);
    updateSelection();
    if (focusPreview && matchMedia('(max-width: 980px)').matches) {
      $('workspace').scrollIntoView({ block: 'start', behavior: 'auto' });
      $('workspace').focus({ preventScroll: true });
    }
  }

  function setColor(color) {
    selectedColor = color; preferences.set(selected.id, color); $('palette').value = color;
    updateSelection();
    const thumbnail = $('library-list').querySelector(`[data-entry="${CSS.escape(selected.id)}"] img`);
    if (thumbnail) thumbnail.src = specFor(selected, color).poster;
  }

  for (const side of ['from', 'to']) for (const axis of ['x', 'y']) {
    $(`${side}-${axis}`).addEventListener('input', event => {
      if (['composition', 'journey'].includes(selected?.kind)) player.setPosition(side, axis, Number(event.target.value));
    });
  }
  $('reset-positions').addEventListener('click', () => {
    for (const side of ['from', 'to']) for (const axis of ['x', 'y']) {
      const value = axis === 'y' ? 50 : side === 'from' ? 22 : 78;
      $(`${side}-${axis}`).value = value;
      if (['composition', 'journey'].includes(selected?.kind)) player.setPosition(side, axis, value);
    }
  });

  for (const [id, apply] of [['travel-duration', value => journeyPlayer.setTravelDuration(value)],
    ['burn-duration', value => journeyPlayer.setBurnDuration(value)]]) {
    $(id).addEventListener('change', () => {
      if (!$(id).checkValidity() || !Number.isFinite(Number($(id).value))) {
        $(id).reportValidity(); return;
      }
      apply(Number($(id).value));
    });
  }

  $('preview-mount').addEventListener('click', () => {
    const anchor = selected;
    const color = selectedColor;
    selectEntry(entries.find(item => item.id === anchor.mount.effect), true);
    applyOverlayMount(anchor);
    for (const layer of overlays) {
      $(`overlay-${layer.side}-style`).value = anchor.mount[layer.side];
      $(`overlay-${layer.side}`).checked = true;
      updateOverlayStyle(layer, color);
    }
    $('overlay-controls').open = true;
  });

  $('hide-preview-token').addEventListener('change', updateTokenPreview);
  $('palette').addEventListener('change', () => setColor($('palette').value));
  $('search').addEventListener('input', renderLibrary);
  for (const button of document.querySelectorAll('[data-kind]')) {
    const kind = button.dataset.kind;
    button.querySelector('[data-count]').textContent = kind === 'all' ? entries.length : entries.filter(item => categoryFor(item) === kind).length;
    button.addEventListener('click', () => {
      filter = kind;
      for (const tab of document.querySelectorAll('[data-kind]')) tab.setAttribute('aria-pressed', String(tab === button));
      renderLibrary();
    });
  }
  $('primary').addEventListener('click', () => player.start());
  $('restart').addEventListener('click', () => player.start());
  $('pause').addEventListener('click', () => player.setPaused(!player.paused));
  $('stop').addEventListener('click', () => player.stop());
  $('seek').addEventListener('input', () => { if (!['sequence', 'journey'].includes(selected?.kind)) player.seek(Number($('seek').value)); });
  $('seek').addEventListener('change', () => $('seek').blur());
  $('speed').addEventListener('change', () => {
    const rate = Number($('speed').value); player.setRate(rate); overlays.forEach(layer => layer.player.setRate(rate));
  });
  $('background').addEventListener('change', () => {
    $('stage').dataset.background = $('background').value;
    $('background-color').disabled = $('background').value !== 'custom';
  });
  $('background-color').disabled = true;
  $('background-color').addEventListener('input', () => $('stage').style.setProperty('--background-color', $('background-color').value));
  $('size').addEventListener('input', () => $('scene').style.setProperty('--size', `${$('size').value}%`));
  for (const name of ['spacing', 'size']) $(`overlay-${name}`).addEventListener('input', () => {
    $('scene').style.setProperty(`--overlay-${name}`, `${$(`overlay-${name}`).value}%`);
  });
  $('copy-path').addEventListener('click', async () => {
    const value = paths.join('\n');
    try {
      await navigator.clipboard.writeText(value);
      if (value === paths.join('\n')) $('copy-path').textContent = 'Copied';
    }
    catch { $('path-field').focus(); $('path-field').select(); notice('Clipboard access unavailable. Copy the selected path text manually.'); }
  });
  $('catalog-state').hidden = true;
  renderLibrary();
  if (entries.length) selectEntry(entries.find(item => colors(item).length > 0) || entries[0]);
  else { $('catalog-state').hidden = false; $('catalog-state').textContent = 'No effects registered yet.'; }
  document.body.dataset.ready = 'true';
}

initialize().catch(error => {
  $('catalog-state').hidden = false;
  $('catalog-state').dataset.state = 'error';
  $('catalog-state').setAttribute('role', 'alert');
  $('catalog-state').textContent = error.message;
});
