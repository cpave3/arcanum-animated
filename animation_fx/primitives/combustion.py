"""Palette-neutral turbulent energy fields for projectiles, blasts and hot ground."""
import numpy as np
from PIL import Image

from animation_fx.layers import bloom


def value_noise(x, y):
    ix, iy = np.floor(x), np.floor(y)
    fx, fy = x-ix, y-iy
    fx, fy = fx*fx*(3-2*fx), fy*fy*(3-2*fy)

    def lattice(a, b):
        value = np.sin(a*127.1+b*311.7)*43758.5453
        return value-np.floor(value)

    return ((1-fy)*((1-fx)*lattice(ix, iy)+fx*lattice(ix+1, iy))
            + fy*((1-fx)*lattice(ix, iy+1)+fx*lattice(ix+1, iy+1)))


def turbulence(x, y, phase):
    wx = x + .16*np.sin(4*y + phase)
    wy = y + .16*np.sin(5*x - phase)
    result = np.zeros_like(x)
    for frequency, weight in ((3, 1), (7, .5), (17, .25)):
        result += weight*value_noise(wx*frequency+1.7*np.sin(phase),
                                     wy*frequency+1.7*np.cos(phase))
    return result/1.75*2-1


def energy_field(density, heat, opacity=1):
    """Purple master with dark folds, saturated flame bodies and white-hot ridges."""
    heat = np.clip(heat, 0, 1)
    stops = np.array([[12, 3, 23], [72, 14, 120], [165, 42, 248],
                      [222, 137, 255], [255, 244, 255]], dtype=float)
    pixels = np.zeros((*density.shape, 4), dtype=np.uint8)
    for channel in range(3):
        pixels[..., channel] = np.interp(heat, np.linspace(0, 1, len(stops)), stops[:, channel])
    pixels[..., 3] = np.rint(np.clip(density*opacity, 0, 1)*255).astype(np.uint8)
    return Image.fromarray(pixels)


def flame_cloud(x, y, radius, phase, opacity=1, *, roughness=1, core_heat=0, detail=1):
    """A textured flame volume, from a dense round bolt to ragged blast billows."""
    if opacity <= 0:
        return Image.new('RGBA', (x.shape[1], x.shape[0]))
    angle = np.arctan2(y, x)
    noise = turbulence(x*2*detail, y*2*detail, phase)
    edge = radius*(1 + roughness*(.12*np.sin(7*angle+.6*np.sin(3*angle))
                   + .07*np.sin(13*angle-phase*.4)))
    distance = np.hypot(x, y) + radius*.22*roughness*noise
    body = np.clip((edge-distance)/(radius*.26), 0, 1)
    folds = .5+.5*turbulence(x*3*detail, y*3*detail, phase)
    rim = np.exp(-((distance-edge*.79)/(radius*.12))**2)
    heat = np.clip(.06 + .62*folds**1.7 + .18*rim + .2*(1-distance/radius)
                   + core_heat*np.exp(-3*(distance/radius)**2), 0, 1)
    return bloom(energy_field(body, heat, opacity), [7, 2])


def smoke_cloud(x, y, radius, phase, opacity=1):
    """Translucent rolling soot, kept separate from the luminous flame field."""
    noise = turbulence(x*2, y*2, phase)
    distance = np.hypot(x, y) + .09*noise
    shell = np.exp(-((distance-radius)/.13)**2)
    curls = (.5+.5*turbulence(x*4, y*4, phase))**2
    pixels = np.zeros((*x.shape, 4), dtype=np.uint8)
    for channel, base in enumerate((37, 31, 43)):
        pixels[..., channel] = base + 38*curls
    pixels[..., 3] = np.rint(np.clip(shell*(.18+.55*curls)*opacity, 0, 1)*255).astype(np.uint8)
    return Image.fromarray(pixels)
