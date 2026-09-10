"""Composable strokes, rings, flashes and glyphs in a 512-unit logical canvas."""
import math
from PIL import Image, ImageDraw
from animation_fx.layers import bloom
from animation_fx.primitives import particles, runes

INK = (169, 55, 255)
LIGHT = (236, 199, 255)

def point(radius, angle, center=(256, 256), aspect=1):
    return (center[0] + radius * math.cos(angle), center[1] + aspect * radius * math.sin(angle))


class Canvas:
    def __init__(self, size=512):
        self.size = size
        self.image = Image.new('RGBA', (1024, 1024))
        self.draw = ImageDraw.Draw(self.image)

    def line(self, points, opacity=1, width=2, color=INK):
        self.draw.line([(x*2, y*2) for x, y in points],
                       fill=(*color, round(255 * min(1, max(0, opacity)))), width=width*2, joint='curve')

    def ring(self, radius, opacity=1, width=2, center=(256, 256), aspect=1, angle=0, arc=math.tau):
        self.line([point(radius, angle + arc*i/128, center, aspect) for i in range(129)], opacity, width)

    def flash(self, radius, opacity=1, center=(256, 256)):
        x, y = center
        layer = Image.new('RGBA', self.image.size)
        draw = ImageDraw.Draw(layer)
        for step in range(40, 0, -1):
            fraction = step/40
            strength = math.exp(-6*fraction*fraction)
            color = (round(169+83*strength), round(55+188*strength), 255)
            r = radius * fraction
            draw.ellipse(((x-r)*2, (y-r)*2, (x+r)*2, (y+r)*2),
                         fill=(*color, round(255 * min(1, max(0, opacity)) * strength)))
        self.image = Image.alpha_composite(self.image, layer)
        self.draw = ImageDraw.Draw(self.image)

    def spiral(self, radius, rotation, opacity=1, arms=3):
        for arm in range(arms):
            points = [point(radius * (.12 + .88*i/80), rotation + arm*math.tau/arms + i/80*4.8)
                      for i in range(81)]
            self.line(points, opacity, 3)
            self.line(points, opacity*.75, 1, LIGHT)

    def sparks(self, age, radius=190, center=(256, 256), aspect=1):
        particles.draw_burst(self.draw, age, radius=radius, center=center, aspect=aspect, scale=2)

    def rune(self, glyph, center, *, size=1, rotation=0, opacity=1, fragmentation=0):
        runes.draw_rune(self.draw, glyph, center=center, size=size, rotation=rotation,
                        opacity=opacity, fragmentation=fragmentation, scale=2)

    def finish(self, opacity=1):
        image = bloom(self.image, [12, 4]).resize((self.size, self.size), Image.Resampling.LANCZOS)
        if opacity != 1:
            image.putalpha(image.getchannel('A').point(lambda a: round(a*min(1, max(0, opacity)))))
        return image

