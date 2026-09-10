"""Seeded top-down fracture networks with progressive growth and luminous seams."""
from dataclasses import dataclass
import math

import numpy as np


@dataclass(frozen=True)
class Crack:
    points: tuple
    width: float
    start_distance: float = 0


def path_length(points):
    return sum(math.dist(a, b) for a, b in zip(points, points[1:]))


def fracture_network(seed=47, center=(256, 256), radius=190):
    """Connected trunks, forks and cross-fractures; positions never slide as they grow."""
    rng = np.random.default_rng(seed)
    trunks = []
    paths = []
    for index in range(7):
        angle = index*math.tau/7 + rng.uniform(-.18, .18)
        extent = radius*rng.uniform(.78, 1.05)
        points = [center]
        for step in range(1, 9):
            distance = extent*step/8
            bend = rng.uniform(-13, 13)
            points.append((center[0]+distance*math.cos(angle)-bend*math.sin(angle),
                           center[1]+distance*math.sin(angle)+bend*math.cos(angle)))
        trunks.append(points)
        paths.append(Crack(tuple(points), rng.uniform(7, 10)))
        for knot, side in [(3, -1), (5, 1)]:
            origin = points[knot]
            direction = angle + side*rng.uniform(.65, 1.1)
            branch = [origin]
            for step in range(1, 5):
                distance = step*rng.uniform(11, 16)
                bend = rng.uniform(-6, 6)
                branch.append((origin[0]+distance*math.cos(direction)-bend*math.sin(direction),
                               origin[1]+distance*math.sin(direction)+bend*math.cos(direction)))
            paths.append(Crack(tuple(branch), rng.uniform(3, 5), path_length(points[:knot+1])))
    for index in (0, 2, 4, 6):
        a, b = trunks[index][3], trunks[(index+1)%7][4]
        middle = [((1-t)*a[0]+t*b[0]+rng.uniform(-9, 9),
                   (1-t)*a[1]+t*b[1]+rng.uniform(-9, 9)) for t in (.33, .67)]
        paths.append(Crack(tuple([a, *middle, b]), 4, path_length(trunks[index][:4])))
    return tuple(paths)


def revealed_path(points, distance):
    visible = [points[0]]
    for a, b in zip(points, points[1:]):
        length = math.dist(a, b)
        if distance < length:
            fraction = max(0, distance)/length
            visible.append((a[0]+fraction*(b[0]-a[0]), a[1]+fraction*(b[1]-a[1])))
            break
        visible.append(b)
        distance -= length
    return visible


def draw_cracks(draw, network, growth, *, energy=1, phase=0, opacity=1, scale=2):
    reach = max(path.start_distance+path_length(path.points) for path in network)
    for index, path in enumerate(network):
        travel = growth*reach-path.start_distance
        if travel <= 0:
            continue
        points = revealed_path(path.points, travel)
        left, right = [], []
        for knot, (x, y) in enumerate(points):
            a, b = points[max(0, knot-1)], points[min(len(points)-1, knot+1)]
            angle = math.atan2(b[1]-a[1], b[0]-a[0]) + math.pi/2
            half_width = path.width/2 * (1-.78*knot/(len(points)-1))
            half_width *= .85 + .15*math.sin(knot*2.3+index)
            dx, dy = half_width*math.cos(angle), half_width*math.sin(angle)
            left.append(((x+dx)*scale, (y+dy)*scale))
            right.append(((x-dx)*scale, (y-dy)*scale))
        polygon = left + right[::-1]
        draw.polygon(polygon, fill=(3, 1, 7, round(240*opacity)))
        pulse = .55+.45*math.sin(phase-index*.7)**2
        draw.line(polygon+[polygon[0]], fill=(155, 39, 239, round(255*opacity*(.35+.65*energy)*pulse)), width=scale)
        for segment, (a, b) in enumerate(zip(points, points[1:])):
            hot = (.5+.5*math.sin(segment*1.8+index-phase))**4
            draw.line([(a[0]*scale, a[1]*scale), (b[0]*scale, b[1]*scale)],
                      fill=(round(3+222*energy*hot), round(1+169*energy*hot),
                            round(7+248*energy*hot), round(240*opacity)), width=scale)
