"""Shared spark appearance, with burst, anchor and swirl motion supplied separately."""
import math

import numpy as np
from PIL import ImageDraw

BURST_SEEDS = np.random.default_rng(906).random((96, 4))
ANCHOR_SEEDS = np.random.default_rng(128).random((150, 5))


def draw_spark(draw, head, tail, *, color, alpha, scale=1, radius=0,
               trail_color=None, trail_alpha=None, twinkle=False, glint_color=None):
    """One short trail, optional bright head and optional glint; all emitters use this."""
    ink = (*color, alpha)
    trail = (*(color if trail_color is None else trail_color), alpha if trail_alpha is None else trail_alpha)
    draw.line([(tail[0]*scale, tail[1]*scale), (head[0]*scale, head[1]*scale)],
              fill=trail, width=scale)
    x, y = head
    if radius:
        draw.ellipse(((x-radius)*scale, (y-radius)*scale, (x+radius)*scale, (y+radius)*scale), fill=ink)
    if twinkle:
        glint = (*(color if glint_color is None else glint_color), alpha)
        draw.line([((x-2)*scale, y*scale), ((x+2)*scale, y*scale)], fill=glint, width=scale)
        draw.line([(x*scale, (y-2)*scale), (x*scale, (y+2)*scale)], fill=glint, width=scale)


def draw_burst(draw, age, *, radius=190, center=(256, 256), aspect=1, scale=2, count=None):
    if not 0 < age < 1:
        return
    for angle, speed, brightness, offset in BURST_SEEDS[:count]:
        theta = angle * math.tau
        distance = 12 + radius * age * (.35 + .65*speed)
        tail_distance = max(0, distance - (3+12*speed)*(1-age))
        head = (center[0]+distance*math.cos(theta), center[1]+aspect*distance*math.sin(theta))
        tail = (center[0]+tail_distance*math.cos(theta), center[1]+aspect*tail_distance*math.sin(theta))
        draw_spark(draw, head, tail, color=(236, 199, 255), scale=scale,
                   alpha=round(255*(1-age)**1.6*(.4+.6*brightness)))


def draw_anchor_sparks(image, time, scale=2):
    draw = ImageDraw.Draw(image)
    for offset, direction, velocity, size, brightness in ANCHOR_SEEDS:
        cycles = 1 + int(velocity * 3)
        age = (time * cycles + offset) % 1
        theta = math.tau * direction
        radius = 7 + (65 + 55 * velocity) * age
        x = 160 + math.cos(theta) * radius * .75
        y = 160 + math.sin(theta) * radius + 15 * age * age
        opacity = int(255 * math.sin(math.pi * age)**1.3 * (.5 + .5 * brightness))
        trail = 3 + 9 * velocity
        tail = (x - math.cos(theta) * trail * .75, y - math.sin(theta) * trail)
        draw_spark(draw, (x, y), tail, alpha=opacity, scale=scale, radius=.45+.65*size,
                   color=(255, 211+int(35*brightness), 100+int(90*brightness)),
                   trail_color=(255, 161, 24), trail_alpha=opacity//2, twinkle=brightness>.93,
                   glint_color=(255, 237, 166))
