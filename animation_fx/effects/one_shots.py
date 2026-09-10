"""Finite effects assembled from shared drawing and transition primitives."""
import math

from animation_fx.primitives import cracks, runes, transitions
from animation_fx.primitives.canvas import Canvas, LIGHT, point
from animation_fx.primitives.geometry import compose
from animation_fx.primitives.timing import progress, smooth

SIZE = 512
FPS = 30
FRAMES = 60
GROUND_CRACKS = cracks.fracture_network()
GROUND_VENTS = tuple(path.points[3] for path in GROUND_CRACKS if path.start_distance == 0)[::2]


def teleport_departure(frame):
    t = progress(frame)
    canvas = Canvas()
    if t < .52:
        q = t/.52
        radius = (95 + 65*math.sin(math.pi*q)) * (1 - .85*smooth((q-.65)/.35))
        canvas.spiral(radius, -8*q, smooth(q/.18), arms=4)
        canvas.ring(radius+9, smooth(q/.2)*.45)
        canvas.flash(4 + 16*q**3, q**2)
    else:
        q = (t-.52)/.48
        canvas.ring(20+180*q, (1-q)**2, 3)
        canvas.sparks(q)
    canvas.flash(43, math.exp(-((t-.51)/.055)**2))
    return canvas.finish(smooth(t/.07)*(1-smooth((t-.82)/.18)))


def teleport_arrival(frame):
    t = progress(frame)
    canvas = Canvas()
    q = smooth(t/.32)
    canvas.flash(5+38*math.sin(math.pi*q), math.exp(-((t-.20)/.09)**2))
    canvas.ring(8+190*q, (1-t)**2, 4)
    canvas.ring(5+155*q, .55*(1-t)**2)
    canvas.spiral(25+155*smooth(t/.6), 5*t, math.sin(math.pi*t)**1.2*(1-t), arms=4)
    canvas.sparks(max(0, (t-.18)/.82))
    return canvas.finish(smooth(t/.045)*(1-smooth((t-.8)/.2)))


def impact_burst(frame):
    t = progress(frame)
    canvas = Canvas()
    # Use the teleport's compact moving trails, not persistent radial spokes.
    travel = t**.7
    canvas.ring(10+210*travel, (1-t)**3, 2)
    canvas.flash(45, math.exp(-((t-.12)/.06)**2))
    canvas.sparks(travel, radius=220)
    return canvas.finish(smooth(t/.04)*(1-smooth((t-.75)/.25)))


def ground_eruption(frame):
    t = progress(frame)
    growth = smooth(t/.36)
    fade = 1-smooth((t-.68)/.32)
    pulse = math.exp(-((t-.42)/.12)**2)
    surface = Canvas()
    cracks.draw_cracks(surface.draw, GROUND_CRACKS, growth, energy=.25+.75*pulse,
                       phase=math.tau*2*t, opacity=fade)
    accents = Canvas()
    for index, center in enumerate(GROUND_VENTS):
        age = (t-.32-index*.018)/.55
        accents.flash(18, pulse*.7, center)
        accents.sparks(age, radius=42, center=center, count=10)
    reveal = smooth(t/.05)
    return compose(surface.finish(reveal), accents.finish(.45*fade*reveal))


def casting_release(frame):
    t = progress(frame)
    canvas = Canvas()
    charge = smooth(t/.45)
    fade = 1-smooth((t-.56)/.40)
    radius = 110 + 25*(1-charge)
    canvas.ring(radius, charge*fade)
    canvas.ring(radius+12, charge*fade*.5)
    for i in range(12):
        angle = i*math.tau/12 + .6*t
        x, y = point(radius, angle)
        opacity = smooth((t-i*.018)/.15)*fade
        glyph = tuple(runes.GLYPHS)[i % len(runes.GLYPHS)]
        canvas.rune(glyph, (x, y), size=.8, rotation=angle+math.pi/2, opacity=opacity)
        canvas.line([point(28,angle), point(radius-20,angle)], opacity*.25)
    canvas.spiral(68, -7*t, charge*fade*.7)
    canvas.flash(48, math.exp(-((t-.56)/.055)**2))
    if t > .56:
        q = (t-.56)/.44
        canvas.ring(30+180*q, (1-q)**2, 3)
        canvas.sparks(q)
    return canvas.finish(smooth(t/.04)*(1-smooth((t-.87)/.13)))


def dispel(frame):
    t = progress(frame)
    canvas = Canvas()
    breakup = smooth((t-.32)/.65)
    for i in range(24):
        angle = i*math.tau/24
        radius = 115 + (45 + 35*math.sin(i*4)**2)*breakup
        rotation = angle + .5*breakup*math.sin(i*7)
        center = point(radius, rotation)
        glyph = tuple(runes.GLYPHS)[i % len(runes.GLYPHS)]
        canvas.rune(glyph, center, size=.8, rotation=rotation+math.pi/2,
                    opacity=(1-breakup)**1.5, fragmentation=breakup)
    if t < .36:
        canvas.ring(115, smooth(t/.1))
        canvas.ring(128, smooth(t/.1)*.5)
    canvas.flash(22, math.exp(-((t-.34)/.045)**2)*.7)
    canvas.sparks(max(0, (t-.34)/.66))
    return canvas.finish(smooth(t/.07)*(1-smooth((t-.85)/.15)))


def portal_open(frame):
    return transitions.render_transition(progress(frame), opening=True, variant='tall')


def portal_close(frame):
    return transitions.render_transition(progress(frame), opening=False, variant='tall')
