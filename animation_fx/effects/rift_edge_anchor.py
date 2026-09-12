"""Handed force braces fitted to the actual left and right compact-rift banks."""
import math

import numpy as np
from PIL import Image, ImageDraw, ImageOps

from animation_fx.layers import bloom
from animation_fx.primitives import lightning, orbs, particles, rift, runes

SIZE = 320
SCALE = 2
FPS = 30
FRAMES = rift.COMPACT_FRAMES
MOUNT_SIZE = 32
MOUNT_SPACING = 8.75
PARENT_SCALE = rift.COMPACT_SIZE*MOUNT_SIZE/100/SIZE
PARENT_CENTER = (rift.COMPACT_SIZE*(.5-MOUNT_SPACING/100), rift.COMPACT_SIZE/2)
GLYPHS = {'left': ('spire', 'eye', 'branch'), 'right': ('gate', 'hourglass', 'fork')}
SPARKS = np.random.default_rng(748).random((24, 4))


def contacts(frame, side):
    """Contact positions in the delivered side's own native canvas coordinates."""
    phase = math.tau*(frame % FRAMES)/FRAMES
    contour = rift.compact_contour(phase)
    edge = contour[:len(contour)//2] if side == 'left' else contour[len(contour)//2:][::-1]
    center_x = PARENT_CENTER[0] if side == 'left' else rift.COMPACT_SIZE-PARENT_CENTER[0]
    ys, xs = [point[1] for point in edge], [point[0] for point in edge]
    return tuple(((np.interp(y, ys, xs)-center_x)/PARENT_SCALE+SIZE/2,
                  (y-PARENT_CENTER[1])/PARENT_SCALE+SIZE/2)
                 for y in (rift.COMPACT_SIZE/2-50, rift.COMPACT_SIZE/2, rift.COMPACT_SIZE/2+50))


def contact_sparks(draw, contact, time, index):
    for offset, direction, speed, brightness in SPARKS[:12]:
        age = (time*(2+int(speed*2))+offset+index*.27) % 1
        angle = math.pi+(direction-.5)*2.5
        distance = (16+31*speed)*age
        trail = (2+6*speed)*(1-age)
        head = (contact[0]+distance*math.cos(angle), contact[1]+distance*math.sin(angle))
        tail = (contact[0]+max(0, distance-trail)*math.cos(angle),
                contact[1]+max(0, distance-trail)*math.sin(angle))
        particles.draw_spark(draw, head, tail, color=(255, 231, 147),
            trail_color=(255, 145, 24), scale=SCALE, radius=.4+.35*brightness,
            alpha=round(235*math.sin(math.pi*age)**2*(.5+.5*brightness)),
            twinkle=brightness>.86)


def render(frame, *, side):
    time = (frame % FRAMES)/FRAMES
    phase = math.tau*time
    ink = Image.new('RGBA', (SIZE*SCALE, SIZE*SCALE))
    draw = ImageDraw.Draw(ink)
    runes.draw_brackets(draw, center=(203, 160), height=180, gap=25, bow=20,
                        scale=SCALE, sides=(-1,))
    nodes = []
    bank = contacts(frame, side)
    if side == 'right':
        bank = tuple((SIZE-x, y) for x, y in bank)
    for index, (contact, glyph) in enumerate(zip(bank, GLYPHS[side])):
        y = contact[1]
        bend = 20*math.sin(math.pi*(y-70)/180)
        node = (200-bend, y)
        pulse = .65+.35*math.sin(phase*2-index*.9)**2
        runes.draw_rune(draw, glyph, center=(150-bend, y), size=1.45,
                        opacity=.8+.2*pulse, scale=SCALE,
                        color=(255, 171, 26), highlight=(255, 239, 167))
        draw.line([((166-bend)*SCALE, y*SCALE), (node[0]*SCALE, y*SCALE)],
                  fill=(255, 185, 57, 185), width=SCALE)
        lightning.draw_tether(draw, node, contact, phase, seed=index*2, scale=SCALE,
                              opacity=.65+.3*pulse)
        contact_sparks(draw, contact, time, index*2)
        nodes.append((contact, 2.0+.6*pulse))
        nodes.append((node, 6.5+.6*math.sin(phase*2+index)))
    image = bloom(ink, [10, 3])
    for center, radius in nodes:
        image = Image.alpha_composite(image, orbs.orb_layer(SIZE, center, radius, scale=SCALE))
    if side == 'right':
        image = ImageOps.mirror(image)
    return image.resize((SIZE, SIZE), Image.Resampling.LANCZOS)
