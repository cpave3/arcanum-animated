import { PreviewPlayer } from './player.js';

// Flight owns geometry and elapsed time; PreviewPlayer owns all ground transitions.
export class JourneyPlayer {
  constructor(container, { onChange = () => {}, onTime = () => {} } = {}) {
    Object.assign(this, { container, onChange, onTime });
    this.rate = 1;
    this.burnDuration = 0;
    this.travelDuration = 1;
    this.positions = { from: { x: 22, y: 50 }, to: { x: 78, y: 50 } };
    this.videos = [];
    this.phase = 'idle';
    this.revision = 0;
    this.observer = new ResizeObserver(() => this.layout());
    this.observer.observe(container);
  }

  snapshot() {
    const ground = this.ground?.snapshot();
    return { kind: this.spec?.kind, phase: this.phase, paused: !!this.paused,
      wanted: this.wanted, active: ['idle', 'loading', 'error'].includes(this.phase) ? -1 : 0,
      time: this.phase === 'flying' ? this.flightTime : ground?.time || 0,
      duration: this.phase === 'flying' ? this.travelDuration : ground?.duration || 0,
      error: this.error };
  }
  emit() { this.onChange(this.snapshot()); this.onTime(this.snapshot()); }

  cancel() {
    this.revision++;
    cancelAnimationFrame(this.frame);
    this.silent = true;
    this.projectile?.cancel();
    this.ground?.cancel();
    this.silent = false;
    this.paused = false;
    this.wanted = false;
    this.error = null;
  }

  load(spec) {
    this.cancel();
    this.silent = true;
    this.projectile?.load(null);
    this.ground?.load(null);
    this.silent = false;
    this.videos.forEach(video => video.remove());
    this.videos = [];
    this.spec = spec;
    this.phase = 'idle';
    this.flightTime = this.loopTime = 0;
    this.projectile = this.ground = null;
    if (spec) {
      for (const phase of ['flying', 'opening', 'looping', 'closing']) {
        const video = document.createElement('video');
        video.muted = true;
        video.playsInline = true;
        video.dataset.journeyPhase = phase;
        video.dataset.active = 'false';
        this.container.append(video);
        this.videos.push(video);
      }
      this.projectile = new PreviewPlayer([this.videos[0]], { onChange: state => {
        if (!this.silent && state.error) this.fail(state.error);
      } });
      this.ground = new PreviewPlayer(this.videos.slice(1), { onChange: state => {
        if (this.silent) return;
        if (state.error) return this.fail(state.error);
        if (!this.onGround) return;
        this.advance();
        this.phase = state.phase;
        this.wanted = state.wanted;
        this.ground.paused = this.paused;
        this.anchorWall = performance.now();
        if (state.phase === 'idle') { cancelAnimationFrame(this.frame); this.paused = false; }
        this.emit();
      }, onTime: () => { if (this.onGround && !this.silent) this.onTime(this.snapshot()); } });
      this.silent = true;
      this.projectile.load({ kind: 'loop', steps: [spec.projectile] });
      this.ground.load({ kind: 'sequence', steps: spec.steps });
      this.silent = false;
      this.setRate(this.rate);
    }
    this.onGround = false;
    this.layout();
    this.emit();
  }

  layout() {
    if (!this.spec) return;
    const { width, height } = this.container.getBoundingClientRect();
    const point = side => ({ x: width * this.positions[side].x / 100, y: height * this.positions[side].y / 100 });
    const from = point('from'), to = point('to');
    const progress = Math.min(1, this.flightTime / this.travelDuration);
    const size = Math.min(width, height) * .48;
    this.videos.forEach((video, index) => {
      Object.assign(video.style, {
        left: `${index ? to.x : from.x + (to.x - from.x) * progress}px`,
        top: `${index ? to.y : from.y + (to.y - from.y) * progress}px`,
        width: `${size}px`, height: `${size}px`,
        transform: `translate(-50%, -50%) rotate(${index ? 0 : Math.atan2(to.y - from.y, to.x - from.x)}rad)`,
      });
    });
    for (const side of ['from', 'to']) {
      const token = this.container.querySelector(`[data-token="${side}"]`);
      Object.assign(token.style, { left: `${this.positions[side].x}%`, top: `${this.positions[side].y}%` });
    }
  }
  setPosition(side, axis, value) { this.positions[side][axis] = value; this.layout(); }
  setTravelDuration(value) { this.travelDuration = value; this.layout(); }
  setBurnDuration(value) { this.advance(); this.burnDuration = value; }

  async start() {
    if (!this.spec) return;
    this.cancel();
    const revision = this.revision;
    this.onGround = false;
    this.flightTime = this.loopTime = 0;
    this.wanted = true;
    this.phase = 'loading';
    this.emit();
    try {
      this.videos.forEach(video => { video.preload = 'auto'; if (video.error || video.readyState < 2) video.load(); });
      await Promise.all(this.videos.map(video => this.projectile.ready(video)));
      if (revision !== this.revision) return;
      await this.projectile.start();
      if (revision !== this.revision) return;
      this.projectile.setPaused(this.paused);
      this.phase = 'flying';
      this.anchorWall = performance.now();
      this.layout(); this.emit(); this.schedule();
    } catch (error) { if (revision === this.revision) this.fail(error.message); }
  }

  advance() {
    const now = performance.now();
    const delta = (now - this.anchorWall) * this.rate / 1000;
    if (!this.paused) {
      if (this.phase === 'flying') this.flightTime = Math.min(this.travelDuration, this.flightTime + delta);
      if (this.phase === 'looping') this.loopTime += delta;
    }
    this.anchorWall = now;
  }
  schedule() {
    cancelAnimationFrame(this.frame);
    if (this.paused || ['idle', 'error'].includes(this.phase)) return;
    this.frame = requestAnimationFrame(() => {
      this.advance();
      this.layout();
      if (this.phase === 'flying' && this.flightTime >= this.travelDuration) {
        this.projectile.stop();
        this.onGround = true;
        // Start frame zero at arrival: the first visible flash follows one frame later.
        this.ground.start();
      }
      if (this.phase === 'looping' && this.wanted && this.burnDuration > 0 && this.loopTime >= this.burnDuration) this.stop();
      this.onTime(this.snapshot());
      this.schedule();
    });
  }
  setPaused(value) {
    this.advance(); this.paused = value;
    this.projectile?.setPaused(value);
    this.ground?.setPaused(value);
    this.schedule(); this.emit();
  }
  setRate(value) {
    this.advance(); this.rate = value;
    this.projectile?.setRate(value); this.ground?.setRate(value);
  }
  stop() {
    if (this.onGround && ['opening', 'looping', 'closing'].includes(this.phase)) this.ground.stop();
    else { this.cancel(); this.phase = 'idle'; this.emit(); }
  }
  fail(message) { this.cancel(); this.phase = 'error'; this.error = message; this.emit(); }
  destroy() { this.load(null); this.observer.disconnect(); }
}
