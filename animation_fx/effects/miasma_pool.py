"""Top-down dark pools with slow, expanding smoke curls from several ground vents."""
import math

import numpy as np
from PIL import Image

SIZE = 512
FPS = 24
FRAMES = 96
Y, X = np.mgrid[:SIZE, :SIZE].astype(np.float32)
X = (X - SIZE / 2) / 218
Y = (Y - SIZE / 2) / 218
R = np.hypot(X, Y)
VENTS = [(-.30, -.20, .48, .38), (.28, -.03, .42, .51), (-.13, .35, .42, .32)]


def render(frame):
    phase = math.tau * (frame % FRAMES) / FRAMES
    # Domain warping gives the pools ragged banks without a hard circular outline.
    wx = X + .07 * np.sin(7*Y + .6*np.sin(5*X + phase))
    wy = Y + .07 * np.sin(8*X + .6*np.cos(5*Y - phase))
    turbulence = (np.sin(12*wx + 4*wy + 1.5*np.sin(7*wy + phase))
                  + np.sin(14*wy - 5*wx + 1.2*np.sin(8*wx - phase))
                  + .4*np.sin(27*wx + 19*wy + phase)) / 2.4
    density = np.zeros_like(X)
    smoke = np.zeros_like(X)
    curls = np.zeros_like(X)
    for index, (cx, cy, width, height) in enumerate(VENTS):
        dx, dy = wx-cx, wy-cy
        local_radius = np.hypot(dx, dy)
        angle = np.arctan2(dy, dx)
        breath = 1 + .06*np.sin(phase + index*2)
        patch = np.exp(-((dx/(width*breath))**2 + (dy/(height*breath))**2)*1.8)
        density += patch
        wave = 2*angle - 18*local_radius + 2*phase + index*2 + .9*turbulence
        ribbon = np.exp(-(np.sin(wave/2)/.32)**2)
        billow = (.5 + .5*np.sin(13*local_radius - phase + 2*turbulence))**2
        vapor = np.sqrt(patch)
        smoke += vapor * (.23 + .50*billow) * (.65 + .35*turbulence)
        curls += vapor * ribbon * (.45 + .55*billow)
    edge = np.clip((1.06-R)/.24, 0, 1)**2
    banks = np.clip((density - .045 + .025*turbulence)*1.35, 0, 1)*edge
    base = np.zeros((SIZE, SIZE, 4), dtype=np.uint8)
    base[:, :, :3] = (4, 2, 9)
    base[:, :, 3] = np.rint(banks*.87*255).astype(np.uint8)
    detail = np.clip(.7*smoke + .5*curls, 0, 1)
    haze = np.zeros_like(base)
    haze[:, :, 0] = np.rint(58 + 65*detail).astype(np.uint8)
    haze[:, :, 1] = np.rint(22 + 35*detail).astype(np.uint8)
    haze[:, :, 2] = np.rint(96 + 85*detail).astype(np.uint8)
    haze[:, :, 3] = np.rint(np.clip((.35*smoke + .52*curls)*edge, 0, .65)*255).astype(np.uint8)
    return Image.alpha_composite(Image.fromarray(base), Image.fromarray(haze))
