"""Reusable drawing layers. Geometry is independent of export and colorway selection."""
import numpy as np
from PIL import Image, ImageFilter

def bloom(image, radii):
    result = Image.new('RGBA', image.size)
    for radius in radii:
        result = Image.alpha_composite(result, image.filter(ImageFilter.GaussianBlur(radius)))
    return Image.alpha_composite(result, image)


def dark_shimmer(mask, x, y, phase, *, frequencies=(12, 3, 4, 7, 5), darkness=1):
    a, b, c, d, e = frequencies
    shimmer = (.5 + .5 * np.sin(a*x + b*y + phase + 2*np.sin(c*y - 2*phase))) ** 3
    folds = (.5 + .5 * np.sin(d*x - e*y - phase)) ** 2
    pixels = np.zeros((*x.shape, 4), dtype=np.uint8)
    pixels[:, :, 0] = (3 + 40 * shimmer * folds * darkness).astype(np.uint8)
    pixels[:, :, 1] = (1 + 8 * shimmer * darkness).astype(np.uint8)
    pixels[:, :, 2] = (7 + 68 * shimmer * folds * darkness).astype(np.uint8)
    pixels[:, :, 3] = np.asarray(mask)
    return Image.fromarray(pixels)
