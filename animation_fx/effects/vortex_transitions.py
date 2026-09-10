"""Vortex transition recipes built from the shared portal lifecycle."""


from animation_fx.primitives.timing import progress
from animation_fx.primitives.transitions import render_transition

SIZE = 640
FPS = 30
FRAMES = 60


def opening(frame):
    return render_transition(progress(frame, FRAMES), opening=True, variant='compact', with_swirl=True)


def closing(frame):
    return render_transition(progress(frame, FRAMES), opening=False, variant='compact', with_swirl=True)
