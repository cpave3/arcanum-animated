"""Live electrical tethers with fixed endpoints and periodic internal deflection."""
import math


def draw_tether(draw, start, end, phase, *, seed=0, scale=2, opacity=1):
    dx, dy = end[0]-start[0], end[1]-start[1]
    length = math.hypot(dx, dy)
    points = []
    for step in range(13):
        t = step/12
        bend = 4*math.sin(step*5.7+7*phase+seed)*math.sin(math.pi*t)
        points.append(((start[0]+dx*t-dy/length*bend)*scale,
                       (start[1]+dy*t+dx/length*bend)*scale))
    draw.line(points, fill=(255, 148, 20, round(220*opacity)), width=3*scale)
    draw.line(points, fill=(255, 240, 174, round(255*opacity)), width=scale)
