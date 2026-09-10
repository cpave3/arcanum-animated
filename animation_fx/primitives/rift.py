"""Tall and compact rifts with shared dark-shimmer material."""
import math

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

from animation_fx.layers import dark_shimmer
from animation_fx.primitives.geometry import centered_grid

COMPACT_SIZE = 640
COMPACT_FRAMES = 90
X, Y = centered_grid(COMPACT_SIZE, 275)

SIZE = 512
SCALE = 2
FPS = 24
FRAMES = 72


def _render_tall(frame):
    phase = 2 * math.pi * frame / FRAMES
    left, right = [], []
    for i in range(49):
        t = i / 48
        y = 57 + 398 * t
        taper = math.sin(math.pi * t)
        center = 256 + 12 * math.sin(t * 8) + 6 * math.sin(t * 27)
        center += 3 * taper * math.sin(t * 19 + phase)
        width = taper ** 0.85 * (24 + 7 * math.sin(t * 17) ** 2)
        width *= 1 + 0.065 * math.sin(phase + t * 5)
        jag = taper * (4 * math.sin(i * 2.7) + 3 * math.cos(i * 1.8))
        left.append(((center - width + jag) * SCALE, y * SCALE))
        right.append(((center + width + 3 * taper * math.sin(i * 2.3)) * SCALE, y * SCALE))
    polygon = left + right[::-1]
    dimensions = (SIZE * SCALE,) * 2
    edge = Image.new('L', dimensions)
    ImageDraw.Draw(edge).line(polygon + [polygon[0]], fill=255, width=3 * SCALE, joint='curve')
    result = Image.new('RGBA', dimensions)
    pulse = 0.85 + 0.15 * math.sin(phase)
    for radius, color, opacity in [(15, (104, 0, 255), .40), (6, (143, 15, 255), .65), (2, (177, 40, 255), .85)]:
        mask = edge.filter(ImageFilter.GaussianBlur(radius * SCALE))
        mask = mask.point(lambda p: round(p * opacity * pulse))
        layer = Image.new('RGBA', dimensions, color + (0,))
        layer.putalpha(mask)
        result = Image.alpha_composite(result, layer)
    mask = Image.new('L', dimensions)
    ImageDraw.Draw(mask).polygon(polygon, fill=255)
    yy, xx = np.mgrid[:SIZE*SCALE, :SIZE*SCALE].astype(np.float32)
    x, y = (xx / SCALE - 256) / 100, (yy / SCALE - 256) / 100
    result = Image.alpha_composite(result, dark_shimmer(mask, x, y, phase))
    draw = ImageDraw.Draw(result)
    draw.line(polygon + [polygon[0]], fill=(159, 35, 255, 255), width=3 * SCALE, joint='curve')
    draw.line(polygon + [polygon[0]], fill=(225, 149, 255, 255), width=SCALE, joint='curve')
    return result.resize((SIZE, SIZE), Image.Resampling.LANCZOS)


def _rift_contour(phase):
    # Sparse contour points give the tear broad fractures instead of a serrated rim.
    left, right = [], []
    for i in range(25):
        t = i / 24
        taper = math.sin(math.pi * t)
        y = 211 + 218 * t
        center = 320 + 7 * math.sin(9 * t) + 3 * taper * math.sin(phase + 17 * t)
        width = 25 * taper ** .8 * (1 + .13 * math.sin(13 * t + phase))
        jagged = 3.2 * taper * math.sin(i * 2.4)
        left.append((center - width + jagged, y))
        right.append((center + width + jagged, y))
    return left + right[::-1]


def _add_dark_core(image, contour, phase, darkness):
    rim = Image.new('RGBA', (COMPACT_SIZE, COMPACT_SIZE))
    d = ImageDraw.Draw(rim)
    d.line(contour + [contour[0]], fill=(186, 32, 255, 230), width=5)
    image = Image.alpha_composite(image, rim.filter(ImageFilter.GaussianBlur(10)))
    image = Image.alpha_composite(image, rim.filter(ImageFilter.GaussianBlur(3)))
    mask = Image.new('L', (COMPACT_SIZE, COMPACT_SIZE))
    ImageDraw.Draw(mask).polygon(contour, fill=255)
    interior = dark_shimmer(mask, X, Y, phase, frequencies=(36, 8, 13, 19, 17),
                            darkness=darkness)
    image = Image.alpha_composite(image, interior)
    d = ImageDraw.Draw(image)
    d.line(contour + [contour[0]], fill=(191, 58, 249, 255), width=2)
    return image


def render_rift(frame, variant='tall', background=None):
    """Render a native RGBA rift, optionally onto a same-size RGBA background.

    Tall is 512px with a 72-frame loop at 24 fps; compact is 640px with a
    90-frame loop at 30 fps. Compact draws each layer onto the background
    in order to preserve the original vortex's alpha rounding and rim pixels.
    Tall is supersampled before compositing onto the native-size background.
    The supplied background is not modified.
    """
    if variant == 'tall':
        image = _render_tall(frame % FRAMES)
        return image if background is None else Image.alpha_composite(background, image)
    if variant == 'compact':
        phase = math.tau * (frame % COMPACT_FRAMES) / COMPACT_FRAMES
        image = Image.new('RGBA', (COMPACT_SIZE, COMPACT_SIZE)) if background is None else background
        return _add_dark_core(image, _rift_contour(phase), phase,
                              np.exp(-((X / .10) ** 2)))
    raise ValueError(f'Unknown rift variant: {variant!r}')
