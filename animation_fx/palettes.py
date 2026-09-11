"""Hue shifts and brightness-indexed gradients preserve HSV value and alpha."""
from dataclasses import dataclass

import numpy as np
from PIL import Image


@dataclass(frozen=True)
class Palette:
    hue: float  # Degrees on the HSV color wheel.
    highlight_hue: float | None = None
    saturation_scale: float = 1.0
    # Ordered (HSV value, RGB tint) stops in [0, 1], with nonzero tints.
    # Overrides hue/saturation mapping; hue still supplies the viewer swatch.
    gradient: tuple[tuple[float, tuple[float, float, float]], ...] | None = None


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
    'eldritch': Palette(285, gradient=(
        (0.0, (.32, .01, 1.0)),
        (.20, (.32, .01, 1.0)),
        (.45, (.70, .02, 1.0)),
        (.65, (1.0, .02, .65)),
        (.85, (1.0, .01, .12)),
        (1.0, (1.0, .02, .03)),
    )),
    'divine': Palette(42, gradient=(
        (0.0, (.12, .30, 1.0)),
        (.22, (.12, .30, 1.0)),
        (.50, (1.0, .72, .18)),
        (.72, (1.0, .82, .35)),
        (.93, (.82, .92, 1.0)),
        (1.0, (.95, .98, 1.0)),
    )),
}


def colorize(image: Image.Image, source: Palette, target: Palette) -> Image.Image:
    """Recolor a master without lifting dark cores or changing alpha.

    Gradients interpolate RGB tints by input HSV value, then normalize the tint
    to that same value. Source hue and saturation do not affect gradient output.
    Equal palettes return an independent, byte-identical copy.
    """
    if source == target:
        return image.copy()
    pixels = np.asarray(image).copy()
    rgb = pixels[:, :, :3].astype(np.float32) / 255
    high, low = rgb.max(axis=2), rgb.min(axis=2)
    if target.gradient is not None:
        positions, tints = zip(*target.gradient)
        tint = np.stack([np.interp(high, positions, channel)
                         for channel in zip(*tints)], axis=-1)
        tint *= (high / tint.max(axis=2))[:, :, None]
        pixels[:, :, :3] = np.rint(tint * 255).astype(np.uint8)
        return Image.fromarray(pixels)
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
