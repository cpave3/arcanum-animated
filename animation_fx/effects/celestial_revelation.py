"""Pooling celestial light contracts into a core and releases a feathered corona."""
import math

import numpy as np
from PIL import Image

from animation_fx.layers import bloom
from animation_fx.primitives import combustion, geometry, particles
from animation_fx.primitives.canvas import Canvas, LIGHT, point
from animation_fx.primitives.timing import smooth

SIZE = 640
FPS = 30
FRAMES = 150
POOL_FRAME = 42
CORE_FRAME = 72
BLAST_FRAME = 81
POSTER_FRAME = 94
X, Y = geometry.centered_grid(SIZE, SIZE / 512)
RADIUS = np.hypot(X, Y)
ANGLE = np.arctan2(Y, X)


def gathering(frame):
    collapse = smooth((frame-POOL_FRAME)/(CORE_FRAME-POOL_FRAME))
    arrival = smooth(frame/POOL_FRAME)
    radius = 116*(1-collapse)+7
    width = 34*(1-collapse)+3
    phase = frame*.035
    noise = combustion.turbulence(X/100, Y/100, phase)
    folds = .5+.5*np.sin(5*ANGLE-RADIUS*.065-phase*2+noise*2)
    distance = RADIUS-radius-(1-collapse)*12*noise
    pool = np.exp(-(distance/width)**2)*(.25+.75*folds**2)
    wisps = np.exp(-(distance/(width*1.6))**2)*(.5+.5*noise)
    density = arrival*(pool*.75+wisps*.22)
    heat = .32+.38*folds+.23*collapse
    return bloom(combustion.energy_field(density, heat), [6, 2])


def release(frame):
    age = (frame-BLAST_FRAME)/(FRAMES-BLAST_FRAME-1)
    travel = 1-(1-age)**3
    radius = 10+208*travel
    noise = combustion.turbulence(X/110, Y/110, age*2)
    feather = (.5+.5*np.cos(18*ANGLE+1.5*noise))**8
    distance = RADIUS-radius-3*noise
    shell = np.exp(-(distance/(3+5*(1-age)))**2)
    wake = np.exp(-((distance+19)/26)**2)*np.clip(-distance/8, 0, 1)
    filaments = (.5+.5*np.sin(42*ANGLE+RADIUS*.16+2*noise))**6
    corona = np.exp(-((distance+8-16*feather)/19)**2)*feather
    envelope = (1-smooth((age-.12)/.82))
    density = (shell*.8+wake*(.22+.65*filaments)+corona*.65)*envelope
    heat = .42+.46*shell+.12*filaments
    return bloom(combustion.energy_field(density, heat), [5, 2])


def accents(frame):
    ink = Canvas(size=SIZE)
    collapse = smooth((frame-POOL_FRAME)/(CORE_FRAME-POOL_FRAME))
    arrival = smooth(frame/POOL_FRAME)
    if frame < BLAST_FRAME:
        # The same motes and curved streams contract with the pool, rather than teleporting to a core.
        for index in range(48):
            angle = index*math.tau/48+.18*math.sin(index*3)+frame*.008+collapse*.85
            radius = (78+65*(.5+.5*math.sin(index*7)))*(1-collapse)+7
            opacity = smooth((frame-index%12)/25)*(.5+.5*math.sin(index*4)**2)
            particles.draw_spark(ink.draw, point(radius, angle), point(radius+4*(1-collapse), angle-.025),
                                 color=LIGHT, alpha=round(210*opacity), scale=2,
                                 radius=.6, twinkle=index%6 == 0)
        for index in range(7):
            angle = index*math.tau/7+frame*.014+collapse*1.1
            points = [point((45+92*q/40)*(1-collapse)+7,
                            angle-q/40*.95) for q in range(41)]
            ink.line(points, arrival*(.15+.5*collapse)*(1-collapse), width=1, color=LIGHT)
        ink.flash(20+22*collapse, arrival*(.12+.88*collapse))
        if frame >= CORE_FRAME:
            ink.flash(36+8*smooth((frame-CORE_FRAME)/(BLAST_FRAME-CORE_FRAME)), 1)
    else:
        elapsed = frame-BLAST_FRAME
        ink.flash(96+elapsed*3, math.exp(-elapsed/5))
        ink.flash(38, math.exp(-elapsed/12))
        ink.sparks(elapsed/62, radius=224, count=100)
        for index in range(24):
            age = (elapsed-index%5)/49
            if not 0 < age < 1:
                continue
            angle = index*math.tau/24+.12*math.sin(index*5)
            radius = 16+(170+22*math.sin(index*4)**2)*(1-(1-age)**2)
            tail = radius-(12+18*math.sin(index*3)**2)*(1-age)
            ink.line([point(tail, angle), point(radius, angle)],
                     math.sin(math.pi*age)*(1-age)*.85, width=1, color=LIGHT)
    return ink.finish()


def render(frame):
    if frame <= 0 or frame >= FRAMES-1:
        return Image.new('RGBA', (SIZE, SIZE))
    field = gathering(frame) if frame < BLAST_FRAME else release(frame)
    image = geometry.compose(field, accents(frame))
    # Leave transparent padding even around the outermost bloom and drifting sparks.
    edge = np.clip((248-RADIUS)/18, 0, 1)
    fade = smooth(frame/9)*(1-smooth((frame-131)/17))
    alpha = np.asarray(image.getchannel('A'), dtype=float)*edge*fade
    image.putalpha(Image.fromarray(np.rint(alpha).astype(np.uint8)))
    return image
