"""Expanding, cooling cloud volumes with advected cellular detail, not waving sheets."""
import math

import numpy as np
from PIL import Image

from animation_fx.layers import bloom
from animation_fx.primitives.combustion import energy_field, value_noise
from animation_fx.primitives.timing import smooth


def billow(size, center, radius, age, seed=0):
    """Render a local gas pocket; callers supply expansion and outward transport."""
    result = Image.new('RGBA', (size, size))
    opacity = smooth(age/.055)*(1-smooth((age-.85)/1.1))
    if opacity <= 0:
        return result
    unit = size/2
    cx, cy = (size/2+center[0]*unit, size/2+center[1]*unit)
    extent = radius*unit*1.3
    left, top = max(0, int(cx-extent)), max(0, int(cy-extent))
    right, bottom = min(size, math.ceil(cx+extent)), min(size, math.ceil(cy+extent))
    yy, xx = np.mgrid[top:bottom, left:right].astype(float)
    x, y = (xx-cx)/(radius*unit), (yy-cy)/(radius*unit)
    # Noise moves with each expanding pocket rather than sliding across a global disk.
    coarse = value_noise(x*2.6+seed*13-age*.35, y*2.6+seed*7-age*.22)
    fine = value_noise(x*7+seed*3-age*.5, y*7+seed*11)
    grain = value_noise(x*19+seed, y*19-age*.7)
    texture = .60*coarse+.28*fine+.12*grain
    distance = np.hypot(x, y) + .28*(coarse-.5)
    density = np.clip((1.02-distance)/.24, 0, 1)
    folds = np.clip((texture-.20)/.6, 0, 1)
    depth = np.sqrt(np.clip(1-distance*distance, 0, 1))
    hot = math.exp(-age*2.1)
    heat = .035 + hot*(.24+.65*folds+.25*depth)
    light = energy_field(density, heat, opacity)
    result.alpha_composite(bloom(light, [2]), (left, top))
    return result
