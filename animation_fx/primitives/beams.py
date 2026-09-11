"""Shared finite beam pulse with a traveling head, luminous core and trailing filaments."""
import math

import numpy as np
from PIL import Image, ImageDraw

from animation_fx.primitives.canvas import Canvas, LIGHT
from animation_fx.primitives.timing import smooth

TRAVEL_FRAMES = 4
PULSE_FRAMES = 8


def draw_beam(canvas, frame, start, end, *, width=7, origin_fade=0):
    """Use identical pulse timing for outgoing and incoming halves of a paired ray."""
    if not 0 < frame < PULSE_FRAMES:
        return
    layer = Canvas(size=canvas.size)
    _paint_beam(layer, frame, start, end, width=width)
    if origin_fade:
        dx, dy = end[0]-start[0], end[1]-start[1]
        length = math.hypot(dx, dy)
        x = np.arange(layer.image.width)[None, :]/2-start[0]
        y = np.arange(layer.image.height)[:, None]/2-start[1]
        fade = np.clip((x*dx+y*dy)/(length*origin_fade), 0, 1)
        fade = fade*fade*(3-2*fade)
        alpha = np.asarray(layer.image.getchannel('A'))*fade
        layer.image.putalpha(Image.fromarray(np.rint(alpha).astype(np.uint8)))
    canvas.image = Image.alpha_composite(canvas.image, layer.image)
    canvas.draw = ImageDraw.Draw(canvas.image)


def _paint_beam(canvas, frame, start, end, *, width):
    if not 0 < frame < PULSE_FRAMES:
        return
    travel = min(1, frame/TRAVEL_FRAMES)
    fade = 1-smooth((frame-TRAVEL_FRAMES)/(PULSE_FRAMES-TRAVEL_FRAMES))
    dx, dy = end[0]-start[0], end[1]-start[1]
    length = math.hypot(dx, dy)
    nx, ny = -dy/length, dx/length
    head = (start[0]+dx*travel, start[1]+dy*travel)
    for thickness, color, opacity in ((width+11, (46, 8, 85), .8),
                                      (width+5, (128, 28, 238), .9),
                                      (width, (193, 99, 255), 1),
                                      (2, LIGHT, 1)):
        canvas.line([start, head], fade*opacity, thickness, color)
    for strand in (-1, 1):
        points = []
        for index in range(41):
            t = index/40*travel
            curl = strand*(width+2)*math.sin(t*19-frame*.9)*math.sin(math.pi*t)
            points.append((start[0]+dx*t+nx*curl, start[1]+dy*t+ny*curl))
        canvas.line(points, fade*.7, 1, LIGHT)
    canvas.flash(12, fade, head)
