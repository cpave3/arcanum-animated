"""Compact, periodic status overlays; each animation has its own silhouette and motion."""
import math
from functools import lru_cache

import numpy as np
from PIL import Image

from animation_fx.primitives import combustion, geometry, particles, swirl
from animation_fx.primitives.canvas import Canvas, INK, LIGHT, point

SIZE = 640
FPS = 30
FRAMES = 90
X, Y = geometry.centered_grid(SIZE, SIZE/512)
EDGE = np.clip((244-np.maximum(np.abs(X), np.abs(Y)))/18, 0, 1)
SEEDS = np.random.default_rng(827).random((24, 4))
ZAPS = np.random.default_rng(912).random((40, 4))


def finish(ink):
    image = ink.finish()
    alpha = np.asarray(image.getchannel('A'), dtype=float)*EDGE
    image.putalpha(Image.fromarray(np.rint(alpha).astype(np.uint8)))
    return image


def electric(frame):
    t = (frame % FRAMES)/FRAMES
    ink = Canvas(size=SIZE)
    for index, (offset, direction, reach, size) in enumerate(ZAPS):
        age = (2*t+offset) % 1
        if age >= .16:
            continue
        # Each short zap exists for about 0.24 seconds, with no residual connecting web.
        pulse = math.sin(math.pi*age/.16)**.7
        theta = direction*math.tau
        center = point(105+53*reach, theta)
        angle = theta+math.pi/2+(size-.5)*1.5
        length = 22+24*size
        dx, dy = math.cos(angle), math.sin(angle)
        points = []
        for step in range(7):
            q = step/6
            bend = math.sin(math.pi*q)*7*math.sin(step*4.7+index+age*55)
            points.append((center[0]+dx*(q-.5)*length-dy*bend,
                           center[1]+dy*(q-.5)*length+dx*bend))
        ink.line(points, pulse*.65, width=3)
        ink.line(points, pulse, width=1, color=LIGHT)
        if index % 3 == 0:
            fork = point(12, angle-.9, points[3])
            ink.line([points[3], (fork[0]+3, fork[1]+2), fork], pulse*.7, width=1, color=LIGHT)
    return finish(ink)


def poison(frame):
    t = (frame % FRAMES)/FRAMES
    ink = Canvas(size=SIZE)
    for index, (offset, horizontal, speed, size) in enumerate(SEEDS[:18]):
        age = (t*(1+int(speed*2))+offset) % 1
        x = 256+(horizontal-.5)*255+8*math.sin(age*5+index)
        y = 256+130-age*(180+45*speed)
        radius = (6+12*size)*(.55+.45*math.sin(math.pi*min(age/.8, 1)/2))
        opacity = math.sin(math.pi*min(age/.12, 1)/2)*min(1, (1-age)/.17)
        if age < .82:
            ink.flash(radius*1.4, opacity*.16, (x, y))
            ink.ring(radius, opacity*.70, width=1, center=(x, y))
            ink.ring(radius*.72, opacity*.80, width=1, center=(x, y), angle=3.5, arc=1.1)
        else:
            pop = (age-.82)/.18
            for ray in range(5):
                angle = ray*math.tau/5+index
                head = point(radius*(1+pop*.85), angle, center=(x, y))
                tail = point(radius*(1+pop*.6), angle, center=(x, y))
                particles.draw_spark(ink.draw, head, tail, color=LIGHT,
                                     alpha=round(160*opacity*(1-pop)), scale=2, radius=.7)
    return finish(ink)


@lru_cache(maxsize=1)
def frost_texture():
    """Stationary ice facets: shimmer the frost, rather than sliding a noise sheet."""
    gx, gy = X/19, Y/19
    cell_x, cell_y = np.floor(gx), np.floor(gy)
    nearest = np.full_like(X, np.inf)
    second = np.full_like(X, np.inf)
    facets = np.zeros_like(X)
    for dx in (-1, 0, 1):
        for dy in (-1, 0, 1):
            cx, cy = cell_x+dx, cell_y+dy
            jitter = np.sin(cx*127.1+cy*311.7)
            px = cx+.5+.35*jitter
            py = cy+.5+.35*np.sin(cx*269.5+cy*183.3)
            distance = (gx-px)**2+(gy-py)**2
            facets = np.where(distance < nearest, .5+.5*jitter, facets)
            second = np.minimum(second, np.maximum(nearest, distance))
            nearest = np.minimum(nearest, distance)
    veins = np.exp(-((np.sqrt(second)-np.sqrt(nearest))/.055)**2)
    grain = combustion.value_noise(X/5, Y/5)
    return veins, facets, grain


def frost_surface(phase):
    radius, angle = np.hypot(X, Y), np.arctan2(Y, X)
    veins, facets, grain = frost_texture()
    feathers = (.5+.5*np.cos(38*angle+radius*.12+facets*5))**10
    inner = 131-22*feathers-8*facets
    coverage = np.clip((radius-inner)/19, 0, 1)*np.clip((182+4*facets-radius)/14, 0, 1)
    shimmer = .88+.12*np.sin(phase+3*angle+facets*math.tau)
    density = coverage*(.24+.30*veins+.12*grain)*shimmer
    heat = .59+.34*veins+.07*facets
    return combustion.energy_field(density, heat)


def frost_shards(phase):
    ink = Canvas(size=SIZE)
    for index in range(9):
        angle = index*math.tau/9+.15
        growth = .55+.45*(.5+.5*math.sin(phase+index*1.7))
        base = point(155, angle)
        tip = point(139-48*growth, angle)
        left = point(10*growth, angle+math.pi/2, base)
        right = point(10*growth, angle-math.pi/2, base)
        ink.draw.polygon([(x*2, y*2) for x, y in (left, tip, right)],
                         fill=(*INK, round(65*growth)))
        ink.line([left, tip, right], .45*growth, width=1)
        ink.line([base, tip], .65*growth, width=1, color=LIGHT)
    image = finish(ink)
    # Bury open-ended shard roots in the coating, retaining definition only at the inward tips.
    fade = np.clip((158-np.hypot(X, Y))/38, 0, 1)
    fade = fade*fade*(3-2*fade)
    image.putalpha(Image.fromarray(np.rint(np.asarray(image.getchannel('A'))*fade).astype(np.uint8)))
    return image


def frost(frame):
    phase = math.tau*(frame % FRAMES)/FRAMES
    ink = Canvas(size=SIZE)
    for index, (offset, horizontal, speed, size) in enumerate(SEEDS[:16]):
        age = ((frame % FRAMES)/FRAMES+offset) % 1
        x = 256+(horizontal-.5)*265+12*math.sin(math.tau*age+index)
        y = 256-140+260*age
        opacity = math.sin(math.pi*age)**2*.7
        radius = 2+3*size
        for arm in range(3):
            angle = arm*math.pi/3+phase*.5+index
            ink.line([point(radius, angle, (x, y)), point(radius, angle+math.pi, (x, y))],
                     opacity, width=1, color=LIGHT)
    return geometry.compose(frost_surface(phase), frost_shards(phase), finish(ink))


def necrotic(frame):
    # Reuse the vortex's layered currents, without its dark tear or full-size aura.
    image = geometry.scale_layer(swirl.render_swirl(frame, inward=True, particle_count=64), .78, .78)
    image.putalpha(image.getchannel('A').point(lambda alpha: round(alpha*.68)))
    return image


def charm_point(q, phase):
    angle = phase+q*math.tau*1.65
    return (256+140*math.cos(angle), 388-264*q+16*math.sin(angle)), math.sin(angle)


def charmed(frame):
    t = (frame % FRAMES)/FRAMES
    phase = math.tau*t
    ink = Canvas(size=SIZE)
    for index in range(160):
        q = index/160
        start, depth = charm_point(q, phase)
        end, _ = charm_point((index+1)/160, phase)
        taper = math.sin(math.pi*(q+.5/160))**.55
        opacity = taper*(.14+.76*((depth+1)/2)**2)
        # A soft ribbon and thin bright ridge suggest a near/far orbit without a solid cage.
        ink.line([start, end], opacity*.4, width=6)
        ink.line([start, end], opacity, width=2, color=LIGHT)
    for index in range(12):
        age = (t+index/12) % 1
        head, depth = charm_point(age, phase)
        tail, _ = charm_point(max(0, age-.012), phase)
        alpha = round(220*math.sin(math.pi*age)**2*(.25+.75*(depth+1)/2))
        particles.draw_spark(ink.draw, head, tail, color=LIGHT, alpha=alpha,
                             scale=2, radius=1, twinkle=index%3 == 0)
    return finish(ink)


ACID_PATCHES = ((-105, -75, 31, 26), (108, -39, 34, 29), (-117, 23, 29, 37),
                (82, 85, 39, 26), (-48, 99, 34, 27), (20, -107, 27, 24),
                (14, 16, 30, 24))


def acid_surface(phase):
    noise = combustion.value_noise(X/9+.25*math.cos(phase), Y/9+.25*math.sin(phase))
    grain = combustion.value_noise(X/3, Y/3)
    density, heat = np.zeros_like(X), np.zeros_like(X)
    for index, (cx, cy, width, height) in enumerate(ACID_PATCHES):
        dx, dy = (X-cx)/width, (Y-cy)/height
        angle = np.arctan2(dy, dx)
        distance = (np.hypot(dx, dy)+.07*np.sin(3*angle+index)
                    +.04*np.sin(11*angle+index*.7)+.36*(noise-.5))
        edge = 1+.07*math.sin(phase+index*1.8)
        body = np.clip((edge-distance)/.18, 0, 1)
        rim = np.exp(-((distance-edge+.16)/.065)**2)
        pits = (.5+.5*np.sin(dx*11+dy*8+2*phase+noise*4))**8
        density += body*(.30+.24*noise+.2*rim)*(1-.65*pits)
        heat = np.maximum(heat, body*(.28+.52*rim+.14*grain-.12*pits))
    return combustion.energy_field(density, heat)


def acid(frame):
    t = (frame % FRAMES)/FRAMES
    phase = math.tau*t
    ink = Canvas(size=SIZE)
    for index, (cx, cy, width, height) in enumerate(ACID_PATCHES):
        center = (256+cx, 256+cy)
        for bubble in range(2):
            age = (3*t+index*.137+bubble*.41) % 1
            origin = (center[0]+9*math.sin(index*4+bubble*2), center[1]+7*math.cos(index+bubble*3))
            if age < .72:
                opacity = math.sin(math.pi*age/.85)*.8
                ink.ring(2+6*age/.72, opacity, width=1, center=origin, aspect=.7)
                ink.flash(6, opacity*.25, origin)
            else:
                pop = (age-.72)/.28
                for ray in range(4):
                    angle = index+ray*math.tau/4
                    x = origin[0]+math.cos(angle)*(4+17*pop)
                    y = origin[1]+math.sin(angle)*9*pop-22*pop+12*pop*pop
                    particles.draw_spark(ink.draw, (x, y), (x-2*math.cos(angle), y+2),
                                         color=LIGHT, alpha=round(180*(1-pop)), scale=2, radius=.8)
        age = (t+index/7) % 1
        opacity = math.sin(math.pi*age)**2
        plume = [(center[0]+9*math.sin(q*4+index+age*3),
                  center[1]-12-45*age-q*22) for q in np.linspace(0, 1, 24)]
        ink.line(plume, opacity*.10, width=7)
        ink.line(plume, opacity*.12, width=2, color=LIGHT)
    return geometry.compose(acid_surface(phase), finish(ink))
