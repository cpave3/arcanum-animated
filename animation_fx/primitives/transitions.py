"""Shared portal lifecycle: aperture + optional swirl + reusable flash/spark accents."""
from functools import lru_cache
import math

from PIL import Image

from animation_fx.primitives.canvas import Canvas
from animation_fx.primitives.geometry import compose, scale_layer
from animation_fx.primitives.rift import render_rift
from animation_fx.primitives.swirl import render_swirl
from animation_fx.primitives.timing import smooth


@lru_cache(maxsize=4)
def _rest_state(variant, with_swirl):
    return render_rift(0, variant, background=render_swirl(0) if with_swirl else None)


def transition_accents(t, *, opening, size):
    """One accent recipe for both plain and swirling portals; uses the shared emitter."""
    canvas = Canvas(size)
    if opening:
        canvas.flash(26, math.exp(-((t-.13)/.05)**2)*smooth(t/.05))
        canvas.sparks(t, 170)
    else:
        canvas.flash(30, math.exp(-((t-.78)/.05)**2))
        canvas.sparks(max(0, (t-.75)/.25), 130)
    return canvas.finish(smooth(t/.04)*(1-smooth((t-.85)/.15)))


def render_transition(t, *, opening, variant='tall', with_swirl=False):
    """Compose an opening/closing effect from the same pieces as its steady loop."""
    if with_swirl and variant != 'compact':
        raise ValueError('The swirl uses the compact rift canvas')
    rest = _rest_state(variant, with_swirl)
    if (opening and t == 1) or (not opening and t == 0):
        return rest.copy()
    if (opening and t == 0) or (not opening and t == 1):
        return Image.new('RGBA', rest.size)
    if opening:
        aperture = smooth(t/(.42 if with_swirl else .88))
        spread = smooth((t-.14)/.86)
        material_frame = round(t*59)-59
    else:
        aperture = 1-smooth((t-(.50 if with_swirl else 0))/(.30 if with_swirl else .80))
        spread = 1-smooth(t/.60)
        material_frame = -round(t*59)
    core = render_rift(material_frame, variant) if with_swirl else _rest_state(variant, False)
    core = scale_layer(core, aperture**1.7, aperture**.5)
    layers = []
    if with_swirl:
        layers.append(scale_layer(render_swirl(material_frame), spread, spread))
    layers.append(core)
    layers.append(transition_accents(t, opening=opening, size=rest.width))
    return compose(*layers)
