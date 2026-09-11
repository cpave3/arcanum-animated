"""Graphic flame study: independent bolt and blast, original fireball ground/timing."""
import math

from PIL import Image

from animation_fx.effects import fireball
from animation_fx.primitives import stylized_flames
from animation_fx.primitives.canvas import Canvas
from animation_fx.primitives.geometry import compose
from animation_fx.primitives.timing import smooth

SIZE = fireball.SIZE
FPS = fireball.FPS
FRAMES = fireball.SHOT_FRAMES


def projectile(frame):
    t = frame/fireball.IMPACT_FRAME
    head = -.94+.94*t**1.35
    opacity = smooth(t/.15)
    tail = stylized_flames.flame_mass(SIZE, .075, frame*.35,
        center=(head-.21, 0), opacity=opacity*.85, heat=.95, stretch=(3.6, .8))
    ball = stylized_flames.flame_mass(SIZE, .13, frame*.35,
        center=(head, 0), opacity=opacity, heat=1.15)
    return compose(tail, ball)


def explosion(frame):
    age = frame/FPS
    if age >= 2.5:
        return Image.new('RGBA', (SIZE, SIZE))
    radius = .10+.63*(1-math.exp(-age*7))
    fade = 1-smooth((age-1.1)/1.4)
    # Cooling breaks the broad hot shapes into separated lobes instead of fine smoke.
    heat = 1.1-.75*smooth((age-.6)/1.65)
    body = stylized_flames.flame_mass(SIZE, radius, age*5, opacity=fade, heat=heat)
    accents = Canvas(size=SIZE)
    accents.flash(54, math.exp(-((age-.05)/.085)**2))
    accents.sparks(age/1.8, radius=215, count=48)
    for index in range(7):
        travel = max(0, age-.22-index*.065)
        angle = index*2.399+.2
        distance = .16+.58*(1-math.exp(-travel*2.8))
        strength = smooth(travel/.12)*(1-smooth((travel-.4)/.7))
        puff = stylized_flames.flame_mass(SIZE, .08*(1+.5*travel), age*4+index,
            center=(distance*math.cos(angle), distance*math.sin(angle)), opacity=strength, heat=.9)
        body = compose(puff, body)
    return compose(body, accents.finish())


def render(frame):
    return fireball.one_shot(frame, projectile_layer=projectile, explosion_layer=explosion)
