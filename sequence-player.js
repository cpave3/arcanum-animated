/* Reusable opening → steady loop → closing playback, driven by media events. */
class SequencedPlayer {
  constructor(root, { chains, assetUrl }) {
    this.root = root;
    this.chains = chains;
    this.assetUrl = assetUrl;
    this.style = root.querySelector('[data-sequence-style]');
    this.color = root.querySelector('[data-sequence-color]');
    this.startButton = root.querySelector('[data-sequence-start]');
    this.stopButton = root.querySelector('[data-sequence-stop]');
    this.status = root.querySelector('[data-sequence-status]');
    this.clips = Object.fromEntries([...root.querySelectorAll('[data-sequence-clip]')]
      .map(video => [video.dataset.sequenceClip, video]));
    this.revision = 0;
    this.playRevision = 0;
    this.paused = false;
    this.rate = 1;
    this.active = null;
    this.phase = 'idle';
    this.running = false;
    this.controller = new AbortController();
    for (const [stage, video] of Object.entries(this.clips)) {
      video.addEventListener('ended', () => this.ended(stage, video));
      video.addEventListener('error', () => {
        if (video.error) this.fail(`Could not load ${video.getAttribute('src')}: ${video.error.message}`);
      });
    }
    this.startButton.addEventListener('click', () => this.start());
    this.stopButton.addEventListener('click', () => this.stop());
    this.style.addEventListener('change', () => this.configure());
    this.color.addEventListener('change', () => this.configure());
    this.configure();
  }

  configure() {
    this.reset();
    const chain = this.chains[this.style.value];
    for (const [stage, video] of Object.entries(this.clips)) {
      video.src = this.assetUrl(chain[stage], this.color.value);
      video.preload = 'auto';
      video.load();
    }
  }

  reset() {
    this.revision++;
    this.controller.abort();
    this.controller = new AbortController();
    this.active = null;
    this.running = false;
    this.errorMessage = null;
    for (const video of Object.values(this.clips)) {
      video.pause();
      video.loop = false;
      video.hidden = true;
    }
    this.setPhase('idle');
  }

  setPhase(phase) {
    this.phase = phase;
    this.root.dataset.phase = phase;
    const editable = phase === 'idle' || phase === 'error';
    this.style.disabled = this.color.disabled = !editable;
    this.startButton.disabled = !editable;
    this.stopButton.disabled = !this.running || phase === 'closing';
    let label = { idle: 'Idle', loading: 'Loading clips…', opening: 'Opening',
      looping: 'Looping', closing: 'Closing', error: this.errorMessage || 'Playback error' }[phase];
    if (!this.running && phase === 'opening') label = 'Opening · close queued';
    if (!this.running && phase === 'looping') label = 'Finishing loop · close queued';
    if (this.paused && ['opening', 'looping', 'closing'].includes(phase)) label = `Paused · ${label}`;
    this.status.textContent = label;
  }

  ready(video) {
    const signal = this.controller.signal;
    return new Promise((resolve, reject) => {
      const cleanup = () => {
        video.removeEventListener('loadeddata', check);
        video.removeEventListener('seeked', check);
        video.removeEventListener('error', check);
        signal.removeEventListener('abort', abort);
      };
      const abort = () => { cleanup(); reject(signal.reason); };
      const check = () => {
        if (video.error) {
          cleanup(); reject(new Error(`Could not load ${video.getAttribute('src')}: ${video.error.message}`));
        } else if (video.readyState >= 2 && !video.seeking) {
          cleanup(); resolve();
        }
      };
      video.addEventListener('loadeddata', check);
      video.addEventListener('seeked', check);
      video.addEventListener('error', check);
      signal.addEventListener('abort', abort, { once: true });
      if (signal.aborted) abort(); else check();
    });
  }

  async start() {
    if (!['idle', 'error'].includes(this.phase)) return;
    this.root.scrollIntoView({ block: 'start', behavior: 'auto' });
    this.reset();
    this.running = true;
    this.setPhase('loading');
    const revision = this.revision;
    try {
      for (const video of Object.values(this.clips)) {
        if (video.error) video.load();
      }
      await Promise.all(Object.values(this.clips).map(video => this.ready(video)));
      if (revision !== this.revision) return;
      await this.present('opening');
    } catch (error) {
      if (revision === this.revision) this.fail(error.message);
    }
  }

  async present(stage) {
    const revision = this.revision;
    const video = this.clips[stage];
    try {
      video.currentTime = 0;
      await this.ready(video);
      if (revision !== this.revision) return;
      if (stage === 'looping' && !this.running) return this.present('closing');
      if (this.active) this.active.pause();
      this.active = video;
      video.loop = stage === 'looping' && this.running;
      for (const clip of Object.values(this.clips)) clip.hidden = clip !== video;
      this.setPhase(stage);
      this.applyPlayback();
    } catch (error) {
      if (revision === this.revision) this.fail(error.message);
    }
  }

  ended(stage, video) {
    if (video !== this.active || !video.ended) return;
    if (stage === 'opening') this.present(this.running ? 'looping' : 'closing');
    else if (stage === 'looping') this.present('closing');
    else this.reset();
  }

  stop() {
    if (!this.running) return;
    this.running = false;
    if (this.phase === 'loading') {
      this.reset();
      return;
    }
    if (this.phase === 'looping') {
      this.active.loop = false;
      if (this.active.ended) this.ended('looping', this.active);
    }
    this.setPhase(this.phase);
  }

  setPaused(paused) {
    this.paused = paused;
    this.setPhase(this.phase);
    this.applyPlayback();
  }

  setRate(rate) {
    this.rate = rate;
    for (const video of Object.values(this.clips)) video.playbackRate = rate;
  }

  applyPlayback() {
    if (!this.active) return;
    const video = this.active;
    const revision = this.revision;
    const playRevision = ++this.playRevision;
    video.playbackRate = this.rate;
    if (this.paused) video.pause();
    else video.play().catch(error => {
      if (revision === this.revision && playRevision === this.playRevision && video === this.active && !this.paused) {
        this.fail(error.message);
      }
    });
  }

  restart() {
    this.reset();
    this.start();
  }

  fail(message) {
    this.reset();
    this.errorMessage = message;
    this.setPhase('error');
  }
}
