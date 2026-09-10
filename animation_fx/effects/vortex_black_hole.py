"""Circular black-hole silhouette with a luminous photon ring and orbiting arcs."""
import math

import numpy as np
from PIL import Image

from animation_fx.primitives.swirl import ANGLE, FPS, FRAMES, R, SIZE, X, Y, render_swirl
from animation_fx.layers import dark_shimmer


def render(frame):
    phase = math.tau * (frame % FRAMES) / FRAMES
    radius = R * 275
    # Radial coverage gives a fixed, antialiased circle rather than a polygonal contour.
    mask = Image.fromarray(np.rint(np.clip(63.5 - radius, 0, 1) * 255).astype(np.uint8))
    core = dark_shimmer(mask, X, Y, phase, frequencies=(36, 8, 13, 19, 17),
                        darkness=.20 * np.exp(-((R / .22) ** 2)))

    orbit = (.5 + .5 * np.cos(2 * ANGLE - 2 * phase)) ** 6
    photon_ring = np.exp(-((radius - 66) / 1.4) ** 2)
    outer_ring = np.exp(-((radius - 75) / 2.2) ** 2) * (.18 + .82 * orbit)
    halo = np.exp(-((radius - 68) / 10) ** 2)
    brightness = np.clip(photon_ring * (.80 + .20 * orbit) + .65 * outer_ring, 0, 1)
    ring = np.zeros((SIZE, SIZE, 4), dtype=np.uint8)
    ring[:, :, 0] = (156 + 99 * brightness).astype(np.uint8)
    ring[:, :, 1] = (40 + 197 * brightness).astype(np.uint8)
    ring[:, :, 2] = 255
    ring[:, :, 3] = np.rint(np.clip(photon_ring + .85 * outer_ring + .25 * halo, 0, 1) * 255).astype(np.uint8)
    image = Image.alpha_composite(render_swirl(frame), Image.fromarray(ring))
    return Image.alpha_composite(image, core)
