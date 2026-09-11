"""Caster-centered sacred release: gathering seal, radiant echoes, dissolving light."""
import math

import numpy as np
from PIL import Image

from animation_fx.primitives import combustion, geometry, particles, runes
from animation_fx.primitives.canvas import Canvas, LIGHT, point
from animation_fx.primitives.timing import smooth

SIZE = 640
FPS = 30
FRAMES = 90
WINDUP_FRAMES = 5
BLAST_FRAME = 24
POSTER_FRAME = 48
# Start, lifetime, reach (logical units), strength, angular offset.
ECHOES = ((BLAST_FRAME, 43, 226, 1, 0), (BLAST_FRAME+7, 43, 213, .85, .19),
          (BLAST_FRAME+15, 42, 198, .72, .38))
X, Y = geometry.centered_grid(SIZE, SIZE / 512)
RADIUS = np.hypot(X, Y)
ANGLE = np.arctan2(Y, X)


def radiant_echo(frame, start, lifetime, reach, strength, rotation):
    """A thin luminous shell and fluted corona, never a filled fire/smoke volume."""
    age = (frame-start)/lifetime
    if not 0 < age < 1:
        return Image.new('RGBA', (SIZE, SIZE))
    radius = 22 + (reach-22)*(1-(1-age)**1.6)
    envelope = smooth(age/.09)*(1-smooth((age-.43)/.57))*strength
    noise = combustion.turbulence(X/120, Y/120, age*2+rotation)
    distance = RADIUS-radius-1.5*noise
    shell = np.exp(-(distance/(2.2+2*(1-age)))**2)
    halo = .23*np.exp(-(distance/13)**2)
    flutes = (.5+.5*np.cos(24*(ANGLE-rotation)))**14
    corona = .42*flutes*np.exp(-((RADIUS-radius+13)/24)**2)
    # Refracted light trails behind each bright edge, giving the echoes depth.
    filaments = (.5+.5*np.sin(46*ANGLE+RADIUS*.12+3*noise-rotation))**4
    wake = np.exp(-((distance+17)/22)**2)*np.clip(-distance/7, 0, 1)
    skirt = wake*(.22+.48*filaments)*(.65+.35*noise)
    density = (shell+halo+corona+skirt)*envelope
    heat = np.clip(.25+.74*shell+.12*filaments+.06*noise, 0, 1)
    return combustion.energy_field(density, heat)


def sacred_accents(frame):
    ink = Canvas(size=SIZE)
    formation = smooth(frame/WINDUP_FRAMES)
    charge_frames = max(0, min(frame, BLAST_FRAME)-WINDUP_FRAMES)
    # Preserve angular velocity as the inward spiral becomes an accelerating charge.
    spin = .22*min(frame, WINDUP_FRAMES) + .22*charge_frames + .011*charge_frames**2
    gather = formation*(1-smooth((frame-BLAST_FRAME)/15))
    flight = min(1, max(0, (frame-BLAST_FRAME)/42))
    glyph_alpha = formation if frame < BLAST_FRAME else (1-flight)**1.3
    for index, glyph in enumerate(runes.GLYPHS):
        angle = index*math.tau/len(runes.GLYPHS) + spin
        radius = 108-53*formation if frame < BLAST_FRAME else 55+165*(1-(1-flight)**1.6)
        ink.rune(glyph, point(radius, angle), size=.72, rotation=angle+math.pi/2,
                 opacity=glyph_alpha)
        ink.ring(92-20*formation, opacity=gather*.8, width=1,
                 angle=angle-.22, arc=.44)
        ink.ring(105-20*formation, opacity=gather*.4, width=1,
                 angle=angle-.15, arc=.30)
    flash_age = frame-BLAST_FRAME
    if flash_age >= 0:
        ink.flash(142+2*flash_age, math.exp(-flash_age/5))
        ink.flash(62+flash_age, math.exp(-flash_age/9))
    else:
        ink.flash(28+frame, gather*.45)
    for index in range(32):
        age = (frame-BLAST_FRAME-index%4)/35
        if not 0 < age < 1:
            continue
        angle = index*math.tau/32
        head = 32+185*age**.7
        tail = max(20, head-(18+24*(index%2))*(1-age))
        ink.line([point(tail, angle), point(head, angle)],
                 opacity=(1-age)**1.4*.65, width=1, color=LIGHT)
    ink.sparks((frame-BLAST_FRAME-6)/54, radius=225, count=80)
    # Paired glints keep the long dissolve centered while varying speed and onset.
    for index in range(24):
        age = (frame-BLAST_FRAME-10-index%7)/47
        if not 0 < age < 1:
            continue
        angle = index*math.tau/24+.17
        radius = 55+(120+20*(index%3))*age
        particles.draw_spark(ink.draw, point(radius, angle), point(radius-3, angle),
                             color=LIGHT, alpha=round(180*math.sin(math.pi*age)*(1-age)),
                             scale=2, radius=.6, twinkle=index%3 == 0)
    return ink.finish()


def render(frame):
    if frame <= 0 or frame >= FRAMES-1:
        return Image.new('RGBA', (SIZE, SIZE))
    image = geometry.compose(*(radiant_echo(frame, *echo) for echo in ECHOES),
                             sacred_accents(frame))
    fade = 1-smooth((frame-76)/12)
    image.putalpha(image.getchannel('A').point(lambda alpha: round(alpha*fade)))
    return image
