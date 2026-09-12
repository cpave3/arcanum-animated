// Independent decoders share one clock; geometry never changes native clip time.
export class CompositionPlayer {
  constructor(container, { poster = null, onChange = () => {}, onTime = () => {} } = {}) {
    Object.assign(this, { container, poster, onChange, onTime });
    this.videos = [];
    this.spec = null;
    this.rate = 1;
    this.revision = 0;
    this.controller = new AbortController();
    this.phase = 'idle';
    this.active = -1;
    this.time = 0;
    this.paused = false;
    this.positions = { from: { x: 22, y: 50 }, to: { x: 78, y: 50 } };
    this.observer = new ResizeObserver(() => this.layout());
    this.observer.observe(container);
  }

  snapshot() {
    return { kind: this.spec?.kind, phase: this.phase, active: this.active,
      paused: this.paused, wanted: this.wanted, time: this.time,
      duration: this.spec?.duration || 0, error: this.error };
  }

  emit() { this.onChange(this.snapshot()); this.onTime(this.snapshot()); }

  pauseVideo(video) { video.playTicket = (video.playTicket || 0) + 1; video.pause(); }

  cancel() {
    this.revision++;
    this.controller.abort();
    this.controller = new AbortController();
    cancelAnimationFrame(this.frame);
    this.videos.forEach(video => { this.pauseVideo(video); video.dataset.active = 'false'; });
    this.active = -1;
    this.paused = false;
    this.wanted = false;
    this.error = null;
  }

  load(spec) {
    this.cancel();
    this.videos.forEach(video => { video.removeAttribute('src'); video.load(); video.remove(); });
    this.videos = [];
    this.spec = spec;
    this.time = 0;
    this.phase = 'idle';
    if (spec) for (const [index, track] of spec.tracks.entries()) {
      const video = document.createElement('video');
      video.muted = true;
      video.playsInline = true;
      video.preload = 'auto';
      video.dataset.compositionTrack = index;
      video.dataset.role = track.role;
      video.dataset.active = 'false';
      video.setAttribute('aria-hidden', 'true');
      video.addEventListener('error', () => {
        if (this.videos.includes(video) && video.error) this.fail(`Could not load ${track.url}: ${video.error.message}`);
      });
      video.src = track.url;
      this.videos.push(video);
      this.container.append(video);
    }
    if (this.poster) {
      this.poster.hidden = !spec;
      if (spec) this.poster.src = spec.poster;
    }
    this.layout();
    this.emit();
  }

  layout() {
    if (!this.spec) return;
    const { width, height } = this.container.getBoundingClientRect();
    const from = { x: width * this.positions.from.x / 100, y: height * this.positions.from.y / 100 };
    const to = { x: width * this.positions.to.x / 100, y: height * this.positions.to.y / 100 };
    const dx = to.x - from.x, dy = to.y - from.y;
    const size = Math.min(width, height) * .48;
    for (const video of this.videos) {
      const beam = video.dataset.role === 'beam';
      const point = video.dataset.role === 'target' ? to : from;
      Object.assign(video.style, {
        left: `${point.x}px`, top: `${point.y}px`,
        width: `${beam ? Math.hypot(dx, dy) : size}px`, height: `${size}px`,
        transform: beam ? `translateY(-50%) rotate(${Math.atan2(dy, dx)}rad)` : 'translate(-50%, -50%)',
      });
    }
    for (const side of ['from', 'to']) {
      const token = this.container.querySelector(`[data-token="${side}"]`);
      if (token) Object.assign(token.style, { left: `${this.positions[side].x}%`, top: `${this.positions[side].y}%` });
    }
    if (this.poster && this.spec) Object.assign(this.poster.style, {
      left: `${from.x}px`, top: `${from.y}px`, width: `${size}px`, height: `${size}px`,
    });
  }

  setPosition(side, axis, value) { this.positions[side][axis] = value; this.layout(); }

  ready(video, minimum = 2) {
    const signal = this.controller.signal;
    return new Promise((resolve, reject) => {
      const events = ['loadeddata', 'canplay', 'canplaythrough', 'progress', 'seeked', 'error'];
      const cleanup = () => {
        clearTimeout(timer);
        events.forEach(event => video.removeEventListener(event, check));
        signal.removeEventListener('abort', abort);
      };
      const abort = () => { cleanup(); reject(signal.reason); };
      const check = () => {
        if (video.error) { cleanup(); reject(new Error(`Could not load ${video.src}: ${video.error.message}`)); }
        else {
          // Firefox reports HAVE_CURRENT_DATA at the end of a fully buffered clip.
          const buffered = video.buffered;
          const complete = video.readyState >= 2 && buffered.length === 1 &&
            buffered.start(0) <= .001 && buffered.end(0) >= video.duration - .001;
          if (!video.seeking && (video.readyState >= minimum || (minimum === 4 && complete))) {
            cleanup(); resolve();
          }
        }
      };
      const timer = setTimeout(() => { cleanup(); reject(new Error(`Timed out loading ${video.src}`)); }, 20000);
      events.forEach(event => video.addEventListener(event, check));
      signal.addEventListener('abort', abort, { once: true });
      if (signal.aborted) abort(); else check();
    });
  }

  async present(time, paused) {
    if (!this.spec) return;
    this.cancel();
    const revision = this.revision;
    this.time = Math.min(Math.max(0, time), this.spec.duration);
    this.paused = paused;
    this.wanted = true;
    this.phase = 'loading';
    this.emit();
    try {
      this.videos.forEach(video => { if (video.error) video.load(); });
      await Promise.all(this.videos.map(video => this.ready(video, 4)));
      if (revision !== this.revision) return;
      this.videos.forEach((video, index) => {
        const track = this.spec.tracks[index];
        video.currentTime = Math.min(Math.max(0, this.time - track.start), track.effect.duration - .5 / track.effect.fps);
        video.playbackRate = this.rate;
      });
      await Promise.all(this.videos.map(video => this.ready(video)));
      if (revision !== this.revision) return;
      this.active = 0;
      this.phase = this.time >= this.spec.duration ? 'ended' : 'playing';
      if (this.poster) this.poster.hidden = true;
      this.anchor();
      this.sync();
      this.emit();
      this.schedule();
    } catch (error) { if (revision === this.revision) this.fail(error.message); }
  }

  start() { return this.present(0, false); }
  seek(time) { return this.present(time, true); }
  anchor() { this.anchorTime = this.time; this.anchorWall = performance.now(); }
  advance() {
    if (this.phase === 'playing' && !this.paused) {
      this.time = Math.min(this.spec.duration, this.anchorTime + (performance.now() - this.anchorWall) * this.rate / 1000);
    }
  }

  sync() {
    this.videos.forEach((video, index) => {
      const track = this.spec.tracks[index];
      const local = this.time - track.start;
      const visible = local >= 0 && local < track.effect.duration && this.phase !== 'ended';
      const entering = visible && video.dataset.active !== 'true';
      video.dataset.active = String(visible);
      if (!visible) { this.pauseVideo(video); return; }
      const desired = Math.min(local, track.effect.duration - .5 / track.effect.fps);
      // Correct boundary entry and meaningful drift, not every animation frame.
      if (!video.seeking && ((entering && Math.abs(video.currentTime - desired) > .001) || Math.abs(video.currentTime - desired) > .08)) video.currentTime = desired;
      if (this.paused) this.pauseVideo(video);
      else if (video.paused && !video.ended) {
        const revision = this.revision;
        const ticket = video.playTicket = (video.playTicket || 0) + 1;
        video.play().catch(error => {
          if (revision === this.revision && ticket === video.playTicket && !this.paused && video.dataset.active === 'true') this.fail(error.message);
        });
      }
    });
  }

  schedule() {
    cancelAnimationFrame(this.frame);
    if (this.phase !== 'playing' || this.paused) return;
    this.frame = requestAnimationFrame(() => {
      this.advance();
      if (this.time >= this.spec.duration) {
        this.phase = 'ended'; this.wanted = false;
        this.sync(); this.emit();
      } else { this.sync(); this.onTime(this.snapshot()); this.schedule(); }
    });
  }

  setPaused(value) {
    this.advance();
    this.paused = value;
    this.anchor();
    if (this.active >= 0) this.sync();
    this.schedule();
    this.emit();
  }

  setRate(value) {
    this.advance();
    this.rate = value;
    this.anchor();
    this.videos.forEach(video => { video.playbackRate = value; });
  }

  stop() {
    this.cancel(); this.time = 0; this.phase = 'idle';
    if (this.poster) this.poster.hidden = !this.spec;
    this.emit();
  }

  fail(message) { this.cancel(); this.phase = 'error'; this.error = message; this.emit(); }
  destroy() { this.load(null); this.observer.disconnect(); }
}
