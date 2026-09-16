"""Outward-flowing swirl: 640px RGBA, 30 fps, 90-frame loop."""
import math

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

from animation_fx.primitives import particles
from animation_fx.primitives.geometry import centered_grid

SIZE = 640
FPS = 30
FRAMES = 90
X, Y = centered_grid(SIZE, 275)
R = np.sqrt(X * X + Y * Y)
ANGLE = np.arctan2(Y, X)
RNG = np.random.default_rng(73)
PARTICLES = RNG.random((220, 5))


def render_swirl(frame, *, inward=False, particle_count=None):
    """Render smoke ribbons and sparks; inward flow also reverses particle trails."""
    time = (frame % FRAMES) / FRAMES
    phase = math.tau * time * (-1 if inward else 1)
    # Integer temporal harmonics make every field periodic over one loop.
    noise = (np.sin(19 * X + 11 * Y + 2 * np.sin(9 * Y + phase))
             + np.sin(31 * Y - 13 * X + np.sin(15 * X - phase))
             + .5 * np.sin(57 * X + 39 * Y + 2 * np.sin(21 * Y + phase))) / 2.5
    spiral = 3 * ANGLE - 17 * R + 2 * phase + .65 * noise
    ribbons = np.exp(-((np.sin(spiral / 2) / .105) ** 2))
    wisps = np.exp(-((np.sin((spiral + .65 + .25 * noise) / 2) / .30) ** 2))
    envelope = np.clip((1.03 - R) / .30, 0, 1) ** 2
    envelope *= np.clip((R - .12) / .18, 0, 1)
    clouds = (0.5 + 0.5 * noise) ** 2
    broken = .45 + .55 * (.5 + .5 * np.sin(13 * R + 4 * ANGLE - phase))
    slow_spiral = 2 * ANGLE - 12 * R + phase + .35 * noise
    fast_spiral = 4 * ANGLE - 21 * R + 3 * phase + .45 * noise
    slow = np.exp(-(np.sin(slow_spiral / 2) / .24) ** 2)
    fast = np.exp(-(np.sin(fast_spiral / 2) / .075) ** 2)
    strength = envelope * (.12 * clouds + .36 * ribbons * broken
                           + .12 * wisps + .18 * slow + .20 * fast * broken)
    alpha = np.clip(envelope * (.13 + .40 * clouds) + strength, 0, .90)
    pixels = np.zeros((SIZE, SIZE, 4), dtype=np.uint8)
    pixels[:, :, 0] = np.clip(65 + 190 * strength, 0, 255)
    pixels[:, :, 1] = np.clip(12 + 115 * strength, 0, 255)
    pixels[:, :, 2] = np.clip(106 + 170 * strength, 0, 255)
    pixels[:, :, 3] = (alpha * 255).astype(np.uint8)
    image = Image.fromarray(pixels)

    sparks = Image.new('RGBA', (SIZE, SIZE))
    draw = ImageDraw.Draw(sparks)
    for offset, direction, speed, size, brightness in PARTICLES[:particle_count]:
        age = (time + offset) % 1
        travel = 1-age if inward else age
        radius = .16 + .84 * travel
        theta = direction * math.tau + 3.5 * travel
        x = SIZE / 2 + 275 * radius * math.cos(theta)
        y = SIZE / 2 + 275 * radius * math.sin(theta)
        opacity = int(230 * math.sin(math.pi * age) ** 1.4 * (.4 + .6 * brightness))
        length = .012 + .022 * speed
        trail_direction = 1 if inward else -1
        tail_r = radius + trail_direction * length
        tail_theta = theta + trail_direction * length * 3.5 / .84
        tail = (SIZE / 2 + 275 * tail_r * math.cos(tail_theta),
                SIZE / 2 + 275 * tail_r * math.sin(tail_theta))
        particles.draw_spark(draw, (x, y), tail, color=(239, 184, 255), alpha=opacity,
                             radius=.55+.75*size, trail_color=(187, 80, 255), trail_alpha=opacity//2)
    image = Image.alpha_composite(image, sparks.filter(ImageFilter.GaussianBlur(2)))
    image = Image.alpha_composite(image, sparks)

    return image
