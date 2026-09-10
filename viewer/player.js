// One transport for single clips and event-driven opening → loop → closing sequences.
// Its video elements must remain in layout at opacity:0 when inactive (Firefox).
export class PreviewPlayer {
  constructor(videos, { poster = null, onChange = () => {}, onTime = () => {} } = {}) {
    this.videos = videos;
    this.poster = poster;
    this.onChange = onChange;
    this.onTime = onTime;
    this.spec = null;
    this.phase = 'idle';
    this.paused = false;
    this.rate = 1;
    this.active = -1;
    this.revision = 0;
    this.playRevision = 0;
    this.seekRevision = 0;
    this.controller = new AbortController();
    for (const [index, video] of videos.entries()) {
      video.addEventListener('ended', () => this.ended(index));
      video.addEventListener('timeupdate', () => { if (index === this.active) this.onTime(this.snapshot()); });
      video.addEventListener('error', () => {
        if (this.spec?.steps[index] && video.error) this.fail(`Could not load ${video.getAttribute('src')}: ${video.error.message}`);
      });
    }
  }

  snapshot() {
    const video = this.videos[this.active];
    const step = this.spec?.steps[this.active];
    return { phase: this.phase, paused: this.paused, wanted: this.wanted,
      active: this.active, time: video?.currentTime || 0,
      duration: step?.effect.duration || this.spec?.steps[0]?.effect.duration || 0,
      error: this.error, kind: this.spec?.kind };
  }

  emit() { this.onChange(this.snapshot()); this.onTime(this.snapshot()); }

  show(index) {
    this.videos.forEach((video, i) => {
      video.dataset.active = String(i === index);
      video.setAttribute('aria-hidden', String(i !== index));
    });
  }

  cancel() {
    this.revision++;
    this.controller.abort();
    this.controller = new AbortController();
    this.videos.forEach(video => { video.pause(); video.loop = false; });
    this.active = -1;
    this.wanted = false;
    this.paused = false;
    this.error = null;
    this.show(-1);
  }

  load(spec) {
    this.cancel();
    this.spec = spec;
    this.phase = 'idle';
    if (this.poster) {
      this.poster.hidden = !spec || spec.kind === 'sequence';
      if (spec) this.poster.src = spec.poster;
      else this.poster.removeAttribute('src');
    }
    this.videos.forEach((video, i) => {
      const step = spec?.steps[i];
      if (step) {
        video.preload = spec.kind === 'sequence' ? 'auto' : 'metadata';
        video.src = step.url;
      } else video.removeAttribute('src');
      video.load();
    });
    this.emit();
  }

  ready(video) {
    const signal = this.controller.signal;
    return new Promise((resolve, reject) => {
      const events = ['loadeddata', 'canplay', 'seeked', 'error'];
      const cleanup = () => { events.forEach(e => video.removeEventListener(e, check)); signal.removeEventListener('abort', abort); };
      const abort = () => { cleanup(); reject(signal.reason); };
      const check = () => {
        if (video.error) { cleanup(); reject(new Error(`Could not load ${video.getAttribute('src')}: ${video.error.message}`)); }
        else if (video.readyState >= 2 && !video.seeking) { cleanup(); resolve(); }
      };
      events.forEach(e => video.addEventListener(e, check));
      signal.addEventListener('abort', abort, { once: true });
      if (signal.aborted) abort(); else check();
    });
  }

  async start() {
    if (!this.spec) return;
    this.cancel();
    this.wanted = true;
    this.phase = 'loading';
    const revision = this.revision;
    this.emit();
    try {
      const clips = this.spec.steps.map((_, i) => this.videos[i]);
      clips.forEach(video => {
        video.preload = 'auto';
        if (video.error || video.readyState < 2) video.load();
      });
      await Promise.all(clips.map(video => this.ready(video)));
      if (revision === this.revision) await this.present(0);
    } catch (error) { if (revision === this.revision) this.fail(error.message); }
  }

  async present(index) {
    const revision = this.revision;
    const video = this.videos[index];
    try {
      video.currentTime = 0;
      await this.ready(video);
      if (revision !== this.revision) return;
      if (this.spec.kind === 'sequence' && index === 1 && !this.wanted) return this.present(2);
      if (this.active >= 0) this.videos[this.active].pause();
      this.active = index;
      this.phase = this.spec.kind === 'sequence' ? this.spec.steps[index].phase
        : this.spec.kind === 'loop' ? 'looping' : 'playing';
      video.loop = this.spec.kind === 'loop' || (this.phase === 'looping' && this.wanted);
      if (this.poster) this.poster.hidden = true;
      this.show(index);
      this.emit();
      this.applyPlayback();
    } catch (error) { if (revision === this.revision) this.fail(error.message); }
  }

  applyPlayback() {
    if (this.active < 0) return;
    const video = this.videos[this.active];
    const revision = this.revision;
    const ticket = ++this.playRevision;
    video.playbackRate = this.rate;
    if (this.paused || this.phase === 'ended') video.pause();
    else video.play().catch(error => {
      if (revision === this.revision && ticket === this.playRevision && !this.paused) this.fail(error.message);
    });
  }

  setPaused(value) { this.paused = value; this.applyPlayback(); this.emit(); }
  setRate(value) { this.rate = value; this.videos.forEach(v => { v.playbackRate = value; }); }

  stop() {
    if (!this.spec) return;
    if (this.spec.kind !== 'sequence' || ['idle', 'loading', 'error', 'ended'].includes(this.phase)) {
      this.cancel(); this.phase = 'idle';
      if (this.poster) this.poster.hidden = this.spec.kind === 'sequence';
      this.emit(); return;
    }
    this.wanted = false;
    if (this.phase === 'looping') {
      this.videos[this.active].loop = false;
      if (this.videos[this.active].ended) this.ended(this.active);
    }
    this.emit();
  }

  ended(index) {
    const video = this.videos[index];
    if (index !== this.active || !video.ended) return;
    if (this.spec.kind === 'sequence') {
      if (index === 0) this.present(this.wanted ? 1 : 2);
      else if (index === 1) this.present(2);
      else { this.cancel(); this.phase = 'idle'; this.emit(); }
    } else if (this.spec.kind === 'one-shot') {
      this.phase = 'ended';
      video.pause();
      // Hold the real final frame even when playback dropped a presentation frame.
      video.currentTime = Math.max(0, this.spec.steps[0].effect.duration - .5/this.spec.steps[0].effect.fps);
      this.emit();
    }
  }

  async seek(time) {
    if (!this.spec || this.spec.kind === 'sequence') return;
    const revision = this.revision;
    const ticket = ++this.seekRevision;
    const video = this.videos[0];
    const effect = this.spec.steps[0].effect;
    this.active = 0;
    this.paused = true;
    this.phase = this.spec.kind === 'loop' ? 'looping' : 'playing';
    video.pause();
    video.loop = this.spec.kind === 'loop';
    this.playRevision++;
    video.preload = 'auto';
    if (this.poster) this.poster.hidden = true;
    this.show(0);
    this.emit();
    try {
      if (video.readyState < 2) video.load();
      await this.ready(video);
      if (revision !== this.revision || ticket !== this.seekRevision) return;
      const lastFrame = effect.duration - .5/effect.fps;
      video.currentTime = Math.min(Math.max(0, time), lastFrame);
      if (time >= lastFrame && this.spec.kind === 'one-shot') this.phase = 'ended';
      await this.ready(video);
      if (revision === this.revision && ticket === this.seekRevision) this.emit();
    } catch (error) { if (revision === this.revision && ticket === this.seekRevision) this.fail(error.message); }
  }

  fail(message) {
    this.cancel(); this.phase = 'error'; this.error = message;
    this.emit();
  }
}
