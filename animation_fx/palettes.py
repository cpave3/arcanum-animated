"""Hue-based colorways preserve brightness and alpha, with optional saturation scaling."""
from dataclasses import dataclass

import numpy as np
from PIL import Image


@dataclass(frozen=True)
class Palette:
    hue: float  # Degrees on the HSV color wheel.
    highlight_hue: float | None = None
    saturation_scale: float = 1.0


PALETTES = {
    'purple': Palette(275),
    'gold': Palette(42),
    'red': Palette(0),
    'orange': Palette(25),
    'acid': Palette(85, highlight_hue=65),
    'cold': Palette(200, highlight_hue=185, saturation_scale=.70),
    'fire': Palette(25, highlight_hue=50),
    'force': Palette(0),
    'lightning': Palette(215, highlight_hue=195, saturation_scale=.55),
    'melee': Palette(210, saturation_scale=.16),
    'necrotic': Palette(145, highlight_hue=180),
    'poison': Palette(120, highlight_hue=140),
    'psychic': Palette(320, highlight_hue=335),
    'radiant': Palette(42),
    'thunder': Palette(245, highlight_hue=265),
}


def colorize(image: Image.Image, source: Palette, target: Palette) -> Image.Image:
    """Shift a master palette without turning dark cores into bright color fills."""
    if source == target:
        return image.copy()
    pixels = np.asarray(image).copy()
    rgb = pixels[:, :, :3].astype(np.float32) / 255
    high, low = rgb.max(axis=2), rgb.min(axis=2)
    chroma = high - low
    denominator = np.where(chroma == 0, 1, chroma)
    r, g, b = np.moveaxis(rgb, -1, 0)
    hue = np.where(high == r, (g-b) / denominator,
                   np.where(high == g, (b-r) / denominator + 2, (r-g) / denominator + 4))
    hue_shift = (target.hue-source.hue) / 60
    if target.highlight_hue is not None:
        # Brighter regions drift toward the secondary hue; dark cores stay dark.
        highlight_shift = (target.highlight_hue-target.hue + 180) % 360 - 180
        hue_shift += highlight_shift / 60 * high ** 1.5
    hue = (hue + hue_shift) % 6
    chroma *= target.saturation_scale
    low = high - chroma
    intermediate = chroma * (1 - np.abs(hue % 2 - 1))
    zero = np.zeros_like(chroma)
    sectors = [(chroma, intermediate, zero), (intermediate, chroma, zero),
               (zero, chroma, intermediate), (zero, intermediate, chroma),
               (intermediate, zero, chroma), (chroma, zero, intermediate)]
    for sector, channels in enumerate(sectors):
        selected = np.floor(hue) == sector
        for channel, values in enumerate(channels):
            pixels[:, :, channel][selected] = np.rint((values[selected] + low[selected]) * 255).astype(np.uint8)
    return Image.fromarray(pixels)
