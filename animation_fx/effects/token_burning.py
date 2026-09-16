"""Fast, seamless token fire: tall overlapping flames and racing embers."""
import math

import numpy as np
from PIL import Image

from animation_fx.layers import bloom
from animation_fx.primitives import combustion, geometry, particles
from animation_fx.primitives.canvas import Canvas, LIGHT

SIZE = 640
FPS = 30
FRAMES = 60
X, Y = geometry.centered_grid(SIZE, SIZE/512)
BASES = ((-115, 132), (-55, 151), (22, 153), (103, 134),
         (-144, 65), (145, 62), (-141, -15), (140, -22),
         (-57, 78), (42, 100), (-22, 5), (65, 8))
SEEDS = np.random.default_rng(714).random((24, 4))


def render(frame):
    t = (frame % FRAMES)/FRAMES
    phase = math.tau*t
    density = np.zeros_like(X)
    hot = np.zeros_like(X)
    for index, (cx, cy) in enumerate(BASES):
        wave = 2*phase+index*2.4
        height = 112+24*math.sin(wave)+18*math.sin(2*wave)
        rise = (cy-Y)/height
        bent = cx+17*np.sin(rise*5-wave)*np.clip(rise, 0, 1)
        width = (21+6*math.sin(wave)) * np.clip(1-rise, .05, 1)**.7
        body = np.exp(-((X-bent)/width)**2)
        envelope = np.clip(rise/.12, 0, 1)*np.clip((1-rise)/.35, 0, 1)
        flicker = .8+.2*np.sin(rise*12-4*phase+index)
        tongue = body*envelope*flicker
        density += tongue*.65
        hot = np.maximum(hot, body*np.clip(1-rise, 0, 1)*envelope)
    field = bloom(combustion.energy_field(density, .20+.74*hot**.7), [4, 1])
    ink = Canvas(size=SIZE)
    for index, (offset, side, speed, drift) in enumerate(SEEDS):
        # Integer cycles and a zero-alpha birth/death keep wrapping particles seamless.
        age = (t*(2+int(speed*2))+offset) % 1
        base_x, base_y = BASES[index % len(BASES)]
        x = base_x+(drift-.5)*22*age+5*math.sin(age*5+side*math.tau)
        y = base_y-24-(125+40*speed)*age
        alpha = round(180*math.sin(math.pi*age)**2)
        particles.draw_spark(ink.draw, (256+x, 256+y), (255+x, 259+y), color=LIGHT,
                             alpha=alpha, scale=2, radius=.5, trail_alpha=alpha//3)
    image = geometry.compose(field, ink.finish())
    # Keep the fire token-sized, without a broad aura or opaque smoke sheet.
    alpha = np.asarray(image.getchannel('A'), dtype=float)
    edge = np.clip((244-np.maximum(np.abs(X), np.abs(Y)))/20, 0, 1)
    image.putalpha(Image.fromarray(np.rint(alpha*edge).astype(np.uint8)))
    return image
