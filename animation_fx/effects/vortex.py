"""Original outward-flowing swirl with a compact central rift."""
from animation_fx.primitives.rift import render_rift
from animation_fx.primitives import swirl
from animation_fx.primitives.swirl import FPS, FRAMES, SIZE


def render(frame):
    return render_rift(frame, 'compact', background=swirl.render_swirl(frame))
