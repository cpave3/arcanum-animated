"""Matching caster/target ray recipes; Foundry decides which targets receive hits."""
import math

from PIL import Image

from animation_fx.primitives import beams, gas, particles, swirl
from animation_fx.primitives.geometry import compose, fade_horizontal_edges, scale_layer
from animation_fx.primitives.canvas import Canvas, LIGHT, point
from animation_fx.primitives.timing import smooth

SIZE = 640
FPS = 30
CHARGE_FRAMES = 12
BURST_SPACING = 10
HIT_FRAME = beams.TRAVEL_FRAMES
HIT_FRAMES = 42


def release_frames(count):
    return tuple(CHARGE_FRAMES+index*BURST_SPACING for index in range(count))


def caster_frames(count):
    return release_frames(count)[-1]+24


def charge(canvas, frame, last_release):
    gather = smooth(frame/CHARGE_FRAMES)
    fade = 1-smooth((frame-last_release)/18)
    swirl_alpha = smooth(frame/2)*(1-smooth((gather-.65)/.35))
    for direction, speed, brightness, offset in particles.BURST_SEEDS[:30]:
        theta = direction*math.tau-frame*.48
        distance = 5+(45+55*speed)*(1-gather)**.65
        particles.draw_spark(canvas.draw, point(distance, theta), point(distance+7*(1-gather), theta),
                             color=LIGHT, alpha=round(220*swirl_alpha*(.4+.6*brightness)),
                             scale=2, radius=.5)
    if swirl_alpha > 0:
        size = .04+.5*(1-gather)**.65
        twist = frame*9 + frame*frame*.45
        inward = swirl.render_swirl(-frame*6).rotate(twist, Image.Resampling.BICUBIC)
        vortex = scale_layer(inward, size, size)
        vortex.putalpha(vortex.getchannel('A').point(lambda a: round(a*swirl_alpha)))
        canvas.image = Image.alpha_composite(canvas.image, vortex.resize(canvas.image.size, Image.Resampling.LANCZOS))
    canvas.flash(8+29*gather, gather*fade)
    canvas.flash(5+13*gather, gather**2*fade)


def caster(frame, *, count):
    canvas = Canvas(size=SIZE)
    releases = release_frames(count)
    for onset in releases:
        local = frame-onset
        beams.draw_beam(canvas, local, (256, 256), (530, 256), origin_fade=24)
        if 0 <= local < 10:
            impulse = math.exp(-local/2.6)
            canvas.flash(38, impulse)
            canvas.ring(14+local*4, impulse*.6, 2)
            canvas.sparks(local/10, radius=52, count=20)
    charge(canvas, frame, releases[-1])
    return fade_horizontal_edges(canvas.finish(
        smooth(frame/3)*(1-smooth((frame-(caster_frames(count)-6))/5))))


def impact(frame):
    """Local impact component, reusable without the incoming half-beam."""
    if frame < 0:
        return Image.new('RGBA', (SIZE, SIZE))
    canvas = Canvas(size=SIZE)
    age = frame/(HIT_FRAMES-HIT_FRAME-1)
    canvas.flash(76, math.exp(-frame/4))
    canvas.ring(10+125*age**.7, (1-age)**3, 3)
    canvas.ring(8+95*age**.7, (1-age)**3*.45, 1)
    canvas.sparks(age, radius=165, count=72)
    for index in range(12):
        theta = index*math.tau/12+.2
        distance = 15+110*age**.65
        tail = max(0, distance-18*(1-age))
        canvas.line([point(tail, theta), point(distance, theta)], (1-age)**3*.6, 1, LIGHT)
    time = frame/FPS
    cloud = gas.billow(SIZE, (0, 0), .06+.16*(1-math.exp(-time*12)), time, seed=13)
    return compose(cloud, canvas.finish())


def target(frame):
    canvas = Canvas(size=SIZE)
    beams.draw_beam(canvas, frame, (-18, 256), (256, 256))
    image = compose(canvas.finish(), impact(frame-HIT_FRAME))
    opacity = smooth(frame/2)*(1-smooth((frame-(HIT_FRAMES-9))/8))
    image.putalpha(image.getchannel('A').point(lambda a: round(a*opacity)))
    return fade_horizontal_edges(image)
