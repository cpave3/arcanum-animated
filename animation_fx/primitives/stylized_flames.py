"""Smooth, graphic flame volumes with broad color bands instead of fine noise."""
import math

import numpy as np
from PIL import Image

from animation_fx.layers import bloom
from animation_fx.primitives.geometry import centered_grid
from animation_fx.primitives.combustion import value_noise


COLORS = ((37, 4, 199), (95, 17, 250), (181, 77, 255), (243, 219, 255))


def flame_mass(size, radius, phase, *, center=(0, 0), opacity=1, heat=1, stretch=(1, 1)):
    """Merged rolling lobes give both the bolt and blast the same animated ink style."""
    if opacity <= 0 or radius <= 0:
        return Image.new('RGBA', (size, size))
    x, y = centered_grid(size, size/2)
    x, y = (x-center[0])/(radius*stretch[0]), (y-center[1])/(radius*stretch[1])
    field = 1.35*np.exp(-3*(x*x+y*y))
    for index in range(9):
        angle = index*math.tau/9 + .13*math.sin(phase+index*2.1)
        reach = .68+.13*math.sin(index*7+phase*.8)
        width = .25+.045*math.sin(index*3+phase)
        dx, dy = x-reach*math.cos(angle), y-reach*math.sin(angle)
        field += .85*np.exp(-(dx*dx+dy*dy)/(width*width))
    rolling = value_noise(x*2+.7*math.sin(phase), y*2+.7*math.cos(phase))
    hot_field = field*(.45+.95*rolling)
    pixels = np.zeros((size, size, 4), dtype=np.uint8)
    for threshold, color in zip((.28, .48, .86, 1.30), COLORS):
        source = field if threshold == .28 else np.minimum(field, hot_field)
        coverage = np.clip((source*heat-threshold)/.08, 0, 1)
        selected = coverage > 0
        # Opaque bands retain a clean silhouette; only the contour is antialiased.
        previous = pixels[..., :3].astype(float)
        pixels[..., :3] = np.rint(previous*(1-coverage[..., None])
                                  + np.asarray(color)*coverage[..., None]).astype(np.uint8)
        pixels[..., 3][selected] = np.maximum(pixels[..., 3][selected],
                                               np.rint(255*coverage[selected]).astype(np.uint8))
    image = bloom(Image.fromarray(pixels), [size/160])
    image.putalpha(image.getchannel('A').point(lambda a: round(a*opacity)))
    return image
