"""One impact recipe, with either finite cooling or a seamless scorched-ground lifecycle."""
import math
from functools import lru_cache

import numpy as np
from PIL import Image

from animation_fx.primitives import combustion, cracks, particles
from animation_fx.primitives.canvas import Canvas, LIGHT
from animation_fx.primitives.geometry import centered_grid, compose
from animation_fx.primitives.timing import smooth

SIZE = 640
FPS = 30
IMPACT_FRAME = 14
OPEN_FRAMES = 120
LOOP_FRAMES = 120
CLOSE_FRAMES = 90
SHOT_FRAMES = OPEN_FRAMES + CLOSE_FRAMES - 1
X, Y = centered_grid(SIZE, SIZE/2)
R = np.hypot(X, Y)
ANGLE = np.arctan2(Y, X)
NETWORK = cracks.fracture_network(seed=183, radius=150)
SEEDS = np.random.default_rng(815).random((100, 4))
GROUND_NOISE = combustion.turbulence(X*3, Y*3, 0)
BANK = np.clip((.64 + .065*np.sin(7*ANGLE) + .06*GROUND_NOISE - R)/.22, 0, 1)


def attenuate(image, opacity):
    image = image.copy()
    image.putalpha(image.getchannel('A').point(lambda a: round(a*opacity)))
    return image


@lru_cache(maxsize=1)
def scorch():
    pixels = np.zeros((SIZE, SIZE, 4), dtype=np.uint8)
    pixels[..., :3] = (9, 5, 12)
    pixels[..., 3] = np.rint(BANK*(.7+.18*GROUND_NOISE)*255).astype(np.uint8)
    return Image.fromarray(pixels)


def ground(phase=0, growth=1, energy=1):
    surface = Canvas(size=SIZE)
    cracks.draw_cracks(surface.draw, NETWORK, growth, energy=energy*.65, phase=phase)
    grain = (.5+.5*GROUND_NOISE)**5
    pulse = (.5+.5*np.sin(phase + X*17-Y*21))**3
    hot = BANK*grain*(.25+.75*pulse)*energy
    coals = combustion.energy_field(hot*2, .4+.5*pulse)
    sparks = Canvas(size=SIZE)
    for offset, direction, distance, size in SEEDS[:55]:
        age = (phase/math.tau+offset) % 1
        angle = direction*math.tau
        radius = 22+112*distance+12*age
        head = (256+radius*math.cos(angle), 256+radius*math.sin(angle))
        tail = (head[0]-2*math.cos(angle), head[1]-2*math.sin(angle))
        particles.draw_spark(sparks.draw, head, tail, color=LIGHT, scale=2,
                             radius=.3+.6*size, alpha=round(210*math.sin(math.pi*age)**2*energy))
    return compose(attenuate(scorch(), growth), surface.finish(), attenuate(coals, growth),
                   sparks.finish(growth))


def projectile(frame):
    t = frame/IMPACT_FRAME
    head = -.94+.94*t**1.35
    dx = X-head
    wake = np.clip(-dx/.62, 0, 1)
    width = .018+.085*(1-wake)
    curl = .026*np.sin(dx*32-frame*.65)*wake
    noise = combustion.turbulence(dx*5, Y*8, frame*.25)
    density = np.exp(-((Y-curl)/width)**2*2)*np.clip(1-wake, 0, 1)
    density *= (dx < 0)*(.6+.4*noise)*np.clip((X+.98)/.10, 0, 1)
    tail = combustion.energy_field(density, .4+.5*(1-wake)+.15*noise)
    ball = combustion.flame_cloud(dx, Y, .125, frame*.4,
                                  roughness=.12, core_heat=.65, detail=4)
    core = Canvas(size=SIZE)
    core.flash(22, .95, (256+head*256, 256))
    return attenuate(compose(tail, ball, core.finish()), smooth(t/.15))


def explosion(frame):
    """Standalone transparent blast layer, timed from detonation, without ground or bolt."""
    age = frame/FPS
    opacity = 1-smooth((age-.65)/1.35)
    smoke_opacity = smooth(age/.3)*(1-smooth((age-1)/1.8))
    if opacity <= 0 and smoke_opacity <= 0:
        return Image.new('RGBA', (SIZE, SIZE))
    radius = .10+.59*(1-math.exp(-age*5))
    blast = combustion.flame_cloud(X, Y, radius, age*4, opacity)
    # Slower, offset inner billows overtake the first shell rather than scaling as one disk.
    inner_age = max(0, age-.10)
    inner_opacity = smooth(inner_age/.12)*(1-smooth((inner_age-.35)/.95))
    inner_radius = .07+.43*(1-math.exp(-inner_age*4))
    inner = combustion.flame_cloud(X+.05, Y-.035, inner_radius, -age*5+2,
                                   inner_opacity, roughness=.8, core_heat=.22, detail=1.5)
    core_opacity = smooth(age/.035)*(1-smooth((age-.12)/.48))
    core = combustion.flame_cloud(X, Y, .06+.23*(1-math.exp(-age*9)), age*7+4,
                                  core_opacity, roughness=.4, core_heat=.6, detail=2)
    detail = Canvas(size=SIZE)
    shock_age = age/.85
    if 0 < shock_age < 1:
        radius_units = 15+215*shock_age**.65
        for i in range(3):
            detail.ring(radius_units-i*3, (1-shock_age)**2*(.7-i*.16), 2)
    detail.flash(67, math.exp(-((age-.08)/.10)**2))
    detail.sparks(age/1.8, radius=218, count=96)
    smoke = combustion.smoke_cloud(X, Y, .12+.56*(1-math.exp(-age*2)), age*1.6, smoke_opacity)
    return compose(smoke, blast, inner, core, detail.finish())


def impact(frame):
    """Compose independent bolt, explosion and ground components on one timeline."""
    if frame < IMPACT_FRAME:
        return projectile(frame)
    age = (frame-IMPACT_FRAME)/FPS
    settle = (OPEN_FRAMES-1-IMPACT_FRAME)/FPS
    phase = math.tau*(age-settle)/4
    return compose(ground(phase, smooth(age/.5)), explosion(frame-IMPACT_FRAME))


def opening(frame):
    return impact(frame)


def embers(frame):
    return ground(math.tau*(frame % LOOP_FRAMES)/LOOP_FRAMES)


def closing(frame):
    t = frame/(CLOSE_FRAMES-1)
    cooling = 1-smooth(t)
    return attenuate(ground(math.tau*frame/LOOP_FRAMES, energy=cooling),
                     1-smooth((t-.2)/.8))


def one_shot(frame):
    if frame < OPEN_FRAMES:
        return impact(frame)
    return closing(frame-(OPEN_FRAMES-1))
