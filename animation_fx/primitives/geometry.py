"""Placement operators for native-size transparent layers."""
import numpy as np
from PIL import Image


def scale_layer(image, width, height):
    """Scale around the layer's center without changing its output canvas."""
    size = image.width
    result = Image.new('RGBA', image.size)
    if width <= 0 or height <= 0:
        return result
    dimensions = (max(1, round(size*width)), max(1, round(size*height)))
    resized = image.resize(dimensions, Image.Resampling.LANCZOS)
    result.alpha_composite(resized, ((size-dimensions[0])//2, (size-dimensions[1])//2))
    return result


def compose(*layers):
    result = layers[0].copy()
    for layer in layers[1:]:
        result = Image.alpha_composite(result, layer)
    return result


def centered_grid(size, unit):
    y, x = np.mgrid[:size, :size].astype(np.float32)
    return (x-size/2)/unit, (y-size/2)/unit


def fade_horizontal_edges(image, fraction=.10):
    """Feather cropped beams after bloom so even their glow reaches zero at the border."""
    x = np.arange(image.width, dtype=float)
    distance = np.minimum(x, image.width-1-x)
    fade = np.clip(distance/(image.width*fraction), 0, 1)
    fade = fade*fade*(3-2*fade)
    result = image.copy()
    alpha = np.asarray(image.getchannel('A'), dtype=float)*fade[None, :]
    result.putalpha(Image.fromarray(np.rint(alpha).astype(np.uint8)))
    return result
