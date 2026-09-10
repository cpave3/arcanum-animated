"""Render one reusable golden spark anchor. Requires Pillow, NumPy, and ffmpeg."""
import math

import numpy as np
from PIL import Image, ImageDraw

from animation_fx.layers import bloom
from animation_fx.primitives import particles

SIZE = 320
SCALE = 2
FPS = 30
FRAMES = 90


def render(frame):
    time = (frame % FRAMES) / FRAMES
    phase = math.tau * time
    sparks = Image.new('RGBA', (SIZE * SCALE, SIZE * SCALE))
    draw = ImageDraw.Draw(sparks)

    def line(points, color, width=1):
        draw.line([(x * SCALE, y * SCALE) for x, y in points], fill=color, width=width * SCALE)

    # Periodic displacement keeps the branching lightning alive across the loop seam.
    for bolt in range(9):
        theta = math.tau * bolt / 9 + .10 * math.sin(phase + bolt)
        length = 72 + 20 * math.sin(2 * phase + bolt * 3)
        flicker = .55 + .45 * (.5 + .5 * math.sin(11 * phase + bolt * 5))
        points = []
        for i in range(12):
            t = i / 11
            radius = 19 + length * t
            jitter = 9 * math.sin(i * 8 + 7 * phase + bolt) * math.sin(math.pi * t)
            points.append((160 + radius * math.cos(theta) - jitter * math.sin(theta),
                           160 + radius * math.sin(theta) + jitter * math.cos(theta)))
        line(points, (255, 158, 15, int(230 * flicker)), 3)
        line(points, (255, 245, 168, int(255 * flicker)))
        start = points[6]
        branch_theta = theta + (.65 if bolt % 2 else -.65)
        branch = [start]
        for i in range(1, 5):
            branch.append((start[0] + i * 8 * math.cos(branch_theta) + 3 * math.sin(i * 9 + phase * 8),
                           start[1] + i * 8 * math.sin(branch_theta) + 3 * math.cos(i * 7 + phase * 8)))
        line(branch, (255, 205, 73, int(210 * flicker)))
    particles.draw_anchor_sparks(sparks, time, SCALE)
    image = bloom(sparks, [6 * SCALE, 2 * SCALE])
    yy, xx = np.mgrid[:SIZE*SCALE, :SIZE*SCALE].astype(np.float32)
    radius = np.sqrt((xx / SCALE - 160) ** 2 + (yy / SCALE - 160) ** 2)
    orb_radius = 23 + 2 * math.sin(2 * phase)
    core = np.clip(1 - (radius / orb_radius) ** 2, 0, 1)
    halo = np.exp(-(radius / (orb_radius * 1.8)) ** 2)
    orb = np.zeros((SIZE*SCALE, SIZE*SCALE, 4), dtype=np.uint8)
    orb[:, :, 0] = 255
    orb[:, :, 1] = (165 + 90 * np.sqrt(core)).astype(np.uint8)
    orb[:, :, 2] = (20 + 210 * core).astype(np.uint8)
    orb[:, :, 3] = (255 * np.clip(core * 2 + halo * .65, 0, 1)).astype(np.uint8)
    image = Image.alpha_composite(image, Image.fromarray(orb))
    return image.resize((SIZE, SIZE), Image.Resampling.LANCZOS)
