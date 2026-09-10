"""Render a golden rune-column anchor with brackets and sparks. Requires Pillow, NumPy, and ffmpeg."""
import math

from PIL import Image, ImageDraw

from animation_fx.layers import bloom
from animation_fx.primitives import particles, runes

SIZE = 320
SCALE = 2
FPS = 30
FRAMES = 90


def render(frame):
    time = (frame % FRAMES) / FRAMES
    phase = math.tau * time
    sparks = Image.new('RGBA', (SIZE * SCALE, SIZE * SCALE))
    draw = ImageDraw.Draw(sparks)

    for index, glyph in enumerate(runes.ANCHOR_GLYPHS):
        pulse = .72 + .28 * math.sin(phase - index * .8) ** 2
        runes.draw_rune(draw, glyph, center=(160, 88+index*36), opacity=pulse, scale=SCALE,
                        color=(255, 174, 30), highlight=(255, 239, 159), outer_alpha=245)
    runes.draw_brackets(draw, scale=SCALE)
    particles.draw_anchor_sparks(sparks, time, SCALE)
    image = bloom(sparks, [6 * SCALE, 2 * SCALE])
    return image.resize((SIZE, SIZE), Image.Resampling.LANCZOS)
